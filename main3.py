import logging
import os
import fitz  # PyMuPDF

from dotenv import load_dotenv
from langchain_chroma import Chroma

from langchain.schema import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.prompts import ChatPromptTemplate

from langchain_huggingface import HuggingFaceEmbeddings
from together import Together

load_dotenv()
FOLDER_PATH = "data/docs"
CHROMA_DIR = "chroma_db"
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")

client = Together(api_key=TOGETHER_API_KEY)
conversation_history = []

def load_documents():
    if not os.path.exists(FOLDER_PATH):
        raise FileNotFoundError(f"Arquivo não encontrado: {FOLDER_PATH}")

    docs = []
    for document in os.listdir(FOLDER_PATH):
        if document.lower().endswith(".pdf"):
            document_path = os.path.join(FOLDER_PATH, document)
            doc = fitz.open(document_path)

            for i, page in enumerate(doc):
                text = page.get_text()
                if text.strip():
                    documento = Document(
                        page_content=text,
                        metadata={"source": document, "page": i + 1}
                    )
                    docs.append(documento)

    if not docs:
        raise ValueError("Nenhum documento válido foi encontrado ou todos estavam vazios.")

    return docs

def split_documents(documents: list[Document]):
    chunks = RecursiveCharacterTextSplitter(
        chunk_size=400,
        chunk_overlap=50,
        separators=["\n\n", "."]
    )
    return chunks.split_documents(documents)

def create_vectorstore(docs, persist_path=CHROMA_DIR):
    embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    unique_docs = []
    seen_texts = set()

    for doc in docs:
        if doc.page_content not in seen_texts:
            unique_docs.append(doc)
            seen_texts.add(doc.page_content)

    print(f"[DEBUG] {len(unique_docs)} documentos únicos foram adicionados ao banco vetorial.")

    vectorstore = Chroma.from_documents(
        documents=unique_docs,
        embedding=embedding,
        persist_directory=persist_path
    )
    return vectorstore

def load_vectorstore(persist_path=CHROMA_DIR):
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    return Chroma(persist_directory=persist_path, embedding_function=embeddings)

def retrieve_context(question):
    vectorstore = load_vectorstore()
    retriever = vectorstore.as_retriever(search_type="mmr", search_kwargs={"k": 10, "lambda_mult": 0.8})
    docs = retriever.invoke(question)
    print(f"\n[DEBUG] Contextos recuperados para a pergunta: '{question}'")
    return [doc.page_content for doc in docs]

def generate_response(question, context, history):
    final_context = "\n\n".join(context)

    conversation_log = ""
    for troca in history:
        conversation_log += f"Usuário: {troca['pergunta']}\nIA: {troca['resposta']}\n"

    prompt = f"""
    Você é uma inteligência artificial especializada em auxiliar no contexto educacional.

    Histórico da conversa até agora:
    {conversation_log}

    Sua base de dados principal será essa:
    {final_context}

    Sua função é:
    - Responder perguntas sobre conteúdos, disciplinas, materiais didáticos e temas educacionais.
    - Sugerir ideias, conteúdos e abordagens para projetos acadêmicos, se aplicável.

    Regras:
    - Use apenas o plano de aula como base principal de informações.
    - Só adicione informações externas se forem altamente relevantes para educação ou projetos.
    - Utilize linguagem clara, acessível e mantenha coerência no diálogo.
    - Nunca responda perguntas fora do contexto educacional.
    - Se a pergunta for confusa ou fora do escopo, responda: \"Pode explicar novamente?\"

    Pergunta: {question}
    Resposta:
    """

    response = client.chat.completions.create(
        model="openchat/openchat-3.5-1210",
        messages=[
            {"role": "system", "content": "Você responde com base apenas no contexto fornecido."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=1024,
        top_p=0.9
    )

    return response.choices[0].message.content.strip()

def main():
    docs = load_documents()
    print("Documentos carregados.")

    chunks = split_documents(docs)
    print("Documentos divididos em chunks.")

    if not os.path.exists(CHROMA_DIR):
        create_vectorstore(chunks)
        logging.basicConfig(level=logging.INFO)
        logging.info("Base vetorial criada.")

    while True:
        question = input("Pergunte sobre (ou sair): ")
        if question.lower() == "sair":
            break
        if not question.strip():
            print("Digite uma pergunta válida.")
            continue

        context = retrieve_context(question)

        if not context:
            print("Nenhum contexto encontrado.")
            continue

        answer = generate_response(question, context, conversation_history)
        conversation_history.append({"pergunta": question, "resposta": answer})

        print(f"\nResposta da IA:\n{answer}\n")

if __name__ == "__main__":
    main()
