import logging
import os
import fitz # PyMuPDFLoader

from dotenv import load_dotenv
from together import Together
from langchain_chroma import Chroma

from langchain.schema import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# embedding e banco vetorial
from langchain_huggingface import HuggingFaceEmbeddings

# Para verificação do chromadb
import hashlib
import json




# OLLAMA_URL = "http://localhost:11434/api/generate"
# MODEL = "llama2"
load_dotenv()
client = Together() # os.environ.get("TOGETHER_API_KEY")
client.api_base = "https://api.together.xyz/v1"
FOLDER_PATH = "../data/docs"  # pasta
CHROMA_DIR = "chroma_db"

conversation_history = []
# Função que verifica arquivo pdf, le e retorna eles
def load_documents():
    # verifica se o arquivo existe antes de abrir
    if not os.path.exists(FOLDER_PATH):
        raise FileNotFoundError(f"Arquivo não encontrado: {FOLDER_PATH}")

    docs = []

    for document in os.listdir(FOLDER_PATH): # ele lista os arq as pasta
        if document.lower().endswith(".pdf"):
            document_path = os.path.join(FOLDER_PATH, document) # cria o caminho
            doc = fitz.open(document_path)

            for i, page in enumerate(doc):
                text = page.get_text()
                if text.strip():
                    documento = Document(
                        page_content=text,
                        metadata={
                            "source": document,
                            "page": i + 1
                        }
                    )
                    docs.append(documento)

    if not docs:
        raise ValueError("Nenhum documento válido foi encontrado ou todos estavam vazios.")

    return docs

def split_documents(documents: list[Document]):
    chunks = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=600,
        separators=["\n\n", "."]
    )
    return chunks.split_documents(documents)

def create_vectorstore(docs, persist_path=CHROMA_DIR):
    embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/multi-qa-mpnet-base-dot-v1")

    # Vamos fazer uma verificação para evitar documentos com conteúdo idêntico ou quase idêntico
    unique_docs = []
    seen_texts = set()

    for doc in docs:
        if doc.page_content not in seen_texts:
            unique_docs.append(doc)
            seen_texts.add(doc.page_content)  # Adiciona o conteúdo ao set para verificar duplicatas

    print(f"[DEBUG] {len(unique_docs)} documentos únicos foram adicionados ao banco vetorial.")

    # Criando o banco vetorial com os documentos únicos
    vectorstore = Chroma.from_documents(
        documents=unique_docs,
        embedding=embedding,
        persist_directory=persist_path
    )
    return vectorstore

# Carrega o banco já salvo no disco
def load_vectorstore(persist_path=CHROMA_DIR):
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/multi-qa-mpnet-base-dot-v1")
    return Chroma(persist_directory=persist_path, embedding_function=embeddings)


def retrieve_context(question):
    vectorstore = load_vectorstore()
    retriever = vectorstore.as_retriever(search_type="mmr", search_kwargs={"k": 30, "lambda_mult": 0.8})

    docs = retriever.invoke(question)

    print(f"\n[DEBUG] Contextos recuperados para a pergunta: '{question}'")
    # for i, doc in enumerate(docs):
    #     print(f"[Chunk {i + 1}] ---\n{doc.page_content}\n")
    # relevant_docs = []
    # for i, d in enumerate(docs):
    #     if any(keyword.lower() in d.page_content.lower() for keyword in question.split()):
    #         relevant_docs.append(d)
    #
    # return [doc.page_content for doc in relevant_docs] if relevant_docs else []
    return [doc.page_content for doc in docs]

def summarize_question(question):
   # prompt = (f"Forneça a melhor versão da minha pergunta. Verifique se eu elaborei a melhor versão dela, se não, sugira para mim a melhor versão."
   #           f"\n\n{question}")

    prompt = (
       "Reformule a pergunta abaixo apenas se ela estiver mal escrita, incompleta ou confusa. "
       "Caso já esteja clara e direta no contexto educacional, responda apenas com 'OK'\n\n"
       f"{question}"
    )


    response = client.chat.completions.create(
        model="mistralai/Mixtral-8x7B-Instruct-v0.1",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )

    content = response.choices[0].message.content.strip()


    # Se a IA respondeu apenas "OK", usamos a pergunta original
    if content.strip().upper() == "OK":
        return question
        # Se a resposta parece ser uma explicação (e não uma pergunta), usamos a original também
    elif "?" not in content or len(content.split()) > 20:
        return question
    else:
        return content


def generate_response(question, context, history):
    final_context = "\n\n".join(context)

    conversation_history = ""
    for troca in history:
        conversation_history += f"Usuário: {troca['pergunta']}\n"
        conversation_history += f"IA: {troca['resposta']}\n"

    prompt = f"""
    Você é uma inteligência artificial que responde perguntas estritamente com base no contexto abaixo.

    ================ CONTEXTO =================
    {final_context}
    ===========================================

    Instruções:
    - Responda sempre em Português - BR
    - Se o contexto incluir uma lista de tópicos ou conteúdos que claramente pertencem a uma disciplina (mesmo que o nome da disciplina não esteja explícito), associe-os ao nome da disciplina mencionada na pergunta.
    - Associe temas da pergunta ao conteúdo programático das disciplinas descritas.
    - Responda à pergunta abaixo usando somente o conteúdo do CONTEXTO.
    - Se o conteúdo da resposta estiver claramente no CONTEXTO, apresente a resposta diretamente.
    - Se a informação **não** estiver no CONTEXTO, diga: "A informação não está disponível nos arquivos analisados."
    - **Não use conhecimento externo**.

    Histórico da conversa (para contexto):
    {conversation_history}

    Pergunta: {question}
    """
    #prompt
    # prompt = f"""
    # Você é uma inteligência artificial especializada em auxiliar no contexto educacional.
    #
    # Histórico da conversa até agora:
    # {conversation_history}
    #
    # Sua base de dados principal será essa: {final_context}
    #
    # Sua função é:
    # - Responder perguntas sobre conteúdos, disciplinas, materiais didáticos e temas educacionais.
    # - Sugerir ideias, conteúdos e abordagens para projetos acadêmicos, se aplicável.
    #
    # Regras:
    # - Use estritamente o plano de aula como base principal de informações.
    # - Só adicione informações externas se forem altamente relevantes para educação ou projetos.
    # - Utilize linguagem clara, acessível e mantenha coerência no diálogo.
    # - Nunca responda perguntas fora do contexto educacional.
    # - Se a pergunta for confusa ou fora do escopo, responda: "Pode explicar novamente?"
    #
    # Pergunta: {question}
    # Resposta:
    # """

    response = client.chat.completions.create(
        model="mistralai/Mixtral-8x7B-Instruct-v0.1",
        messages=[
            {"role": "system", "content": "Você responde com base apenas no contexto fornecido."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
    )

    return response.choices[0].message.content.strip()

HASH_FILE = "docs_hash.json"
def calculate_docs_hash(docs_dir):
    hash_md5 = hashlib.md5()
    for root, _, files in os.walk(docs_dir):
        for f in sorted(files):
            path = os.path.join(root,f)
            with open(path, "rb") as file:
                while chunk := file.read(4096):
                    hash_md5.update(chunk)
    return hash_md5.hexdigest()

def has_docs_changed():
    current_hash = calculate_docs_hash("../data/docs")
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, "r") as f:
            saved_hash = json.load(f).get("hash")
        if saved_hash == current_hash:
            return False
    # Save new hash
    with open(HASH_FILE, "w") as f:
        json.dump({"hash": current_hash}, f)
    return True




def main():
    docs = load_documents()
    print("Documentos carregados.")

    chunks = split_documents(docs)
    # print (chunks)
    print("Documentos divididos em chunks.")

    if not os.path.exists(CHROMA_DIR) or has_docs_changed():
        create_vectorstore(chunks)
        print("Base vetorial criada ou atualizada com sucesso.\n")

    # create_vectorstore(chunks)
    # print("Base vetorial criada ou atualizada com sucesso.\n")

    # if not os.path.exists(CHROMA_DIR):
    #     create_vectorstore(chunks)
    #     logging.basicConfig(level=logging.INFO)
    #     logging.info("Base vetorial criada.")



    while True:
        question = input("Pergunte sobre (ou sair): ")
        if question.lower() == "sair":
            break
        if not question.strip():
            print("Digite uma pergunta válida.")
            continue
        quest = summarize_question(question)
        print(quest)

        final_question = question if quest.upper() == "OK" else quest

        context = retrieve_context(final_question)
        # context = retrieve_context(question)

        if not context:
            print("Nenhum contexto encontrado.")
            continue

        answer = generate_response(question, context, conversation_history)
        conversation_history.append({"pergunta": question, "resposta": answer})

        print(f"\nResposta da IA:\n{answer}\n")
        conversation_history.append({"pergunta": question, "resposta": answer})

if __name__ == "__main__":
    main()