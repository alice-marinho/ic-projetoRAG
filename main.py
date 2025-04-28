import os
import re
import fitz # PyMuPDFLoader

import requests
from click import prompt
from dotenv import load_dotenv
from together import Together
from langchain_chroma import Chroma

from langchain.schema import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# embedding e banco vetorial
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from pathlib import Path



# OLLAMA_URL = "http://localhost:11434/api/generate"
# MODEL = "llama2"
load_dotenv()
client = Together() # os.environ.get("TOGETHER_API_KEY")
client.api_base = "https://api.together.xyz/v1"
FOLDER_PATH = "data/docs" # pasta
CHROMA_DIR = "chroma_db"


# Função que verifica arquivo pdf e txt, le e retorna eles
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
        chunk_size=400,
        chunk_overlap=50
    )
    return chunks.split_documents(documents)

# def create_vectorstore(docs, persist_path=CHROMA_DIR):
#     #criando os embeddings dos splits
#     embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
#     #criando o banco vetorial chromadb para armazenar os embeddings
#     vectorstore =  Chroma.from_documents(
#         documents=docs,
#         embedding=embedding,
#         persist_directory=persist_path # Guardar no disco para reutilizar depois
#     )
#     return vectorstore

def create_vectorstore(docs, persist_path=CHROMA_DIR):
    embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

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
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    return Chroma(persist_directory=persist_path, embedding_function=embeddings)

def retrieve_context(question):
    vectorstore = load_vectorstore()
    retriever = vectorstore.as_retriever(search_type="mmr", search_kwargs={"k": 10, "lambda_mult": 0.8})

    docs = retriever.invoke(question)

    print(f"\n[DEBUG] Contextos recuperados para a pergunta: '{question}'")

    relevant_docs = []
    for i, d in enumerate(docs):
        if any(keyword.lower() in d.page_content.lower() for keyword in question.split()):
            relevant_docs.append(d)

    if relevant_docs:
        for i, d in enumerate(relevant_docs):
            print(f"\n--- Chunk {i + 1} ---")
            print(f"Source: {d.metadata['source']}")
            print(f"Page: {d.metadata['page']}")
            print(f"Conteúdo do Chunk: {d.page_content[:500]}")  # Exibir os primeiros 500 caracteres do contexto

    else:
        print("Nenhum contexto relevante encontrado.")

    return [doc.page_content for doc in relevant_docs] if relevant_docs else []

def summarize_question(question):
    prompt = (f"reescreva a frase somente as palavras chaves de forma objetiva para facilitar uma pesquisa semântica."
              f"Exemplo: pergunta: Quais são matérias que ensinam biologia? || palavras: matérias ensine biologia "
              f"\n\n{question}")

    response = client.chat.completions.create(
        model="mistralai/Mixtral-8x7B-Instruct-v0.1",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )

    summarized_question = response.choices[0].message.content.strip()
    return summarized_question

def generate_response(question, context):
    final_context = "\n\n".join(context)
    # prompt = f"""
    #     Você é uma IA que responde perguntas com base apenas nas informações do contexto abaixo. Onde há pdf de planos de aulas, tendo o conteúdo do ano inteiro das turmas do ensino médio.
    #
    #     === CONTEXTO DOS DOCUMENTOS ===
    #     {final_context}
    #     === FIM DO CONTEXTO ===
    #
    #     Responda com base apenas nas informações fornecidas no contexto abaixo. Você pode identificar o nome da matéria, ano ou série com base no nome do documento, nas palavras-chave do conteúdo ou nas anotações do plano de aula, se disponíveis.
    #
    #     Se não houver informação suficiente, responda: "Não sei responder com base nos documentos. Pode perguntar de forma mais clara?"
    #
    #     Caso a pergunta seja vaga ou não tenha um conteúdo exato, você pode sugerir tópicos semelhantes ou relacionadas. Por exemplo: "Há algum conteúdo relacionado à história do Brasil Colônia?" Se não houver, sugira outra era ou contexto similar.
    #
    #     Pergunta: {question}
    #     Resposta:
    #     """
    prompt = f"""
    Você é uma inteligência artificial especializada em auxiliar no contexto educacional.

    Sua base de dados principal será essa: {final_context}

    Sua função é:
    - Responder perguntas sobre conteúdos, disciplinas, materiais didáticos e temas educacionais.
    - Sugerir ideias, conteúdos e abordagens para projetos acadêmicos, se aplicável.

    Regras:
    - Use apenas o plano de aula como base principal de informações.
    - Só adicione informações externas se forem altamente relevantes para educação ou projetos.
    - Utilize linguagem clara, acessível e mantenha coerência no diálogo.
    - Nunca responda perguntas fora do contexto educacional.
    - Se a pergunta for confusa ou fora do escopo, responda: "Pode explicar novamente?"

    Pergunta: {question}
    Resposta:
    """

    response = client.chat.completions.create(
        model="mistralai/Mixtral-8x7B-Instruct-v0.1",
        messages=[
            {"role": "system", "content": "Você responde com base apenas no contexto fornecido."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
    )

    return response.choices[0].message.content.strip()


def main():
    docs = load_documents()
    print("Documentos carregados.")

    chunks = split_documents(docs)
    print("Documentos divididos em chunks.")

    create_vectorstore(chunks)
    print("Base vetorial criada com sucesso.\n")

    conversation_history = []

    while True:
        question = input("Pergunte sobre (ou sair): ")
        if question.lower() == "sair":
            break

        quest = summarize_question(question)
        print(quest)
        context = retrieve_context(quest)

        if not context:
            print("Nenhum contexto encontrado.")
            continue

        answer = generate_response(question, context)

        print(f"\nResposta da IA:\n{answer}\n")
        conversation_history.append({"pergunta": question, "resposta": answer})

if __name__ == "__main__":
    main()