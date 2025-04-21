import os
import re


import fitz # PyMuPDFLoader

import requests
from langchain_chroma import Chroma

from langchain.schema import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# embedding e banco vetorial
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from pathlib import Path


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama2"
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
        chunk_size=300,
        chunk_overlap=50
    )
    return chunks.split_documents(documents)

def create_vectorstore(docs, persist_path=CHROMA_DIR):
    #criando os embeddings dos splits
    embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    #criando o banco vetorial chromadb para armazenar os embeddings
    vectorstore =  Chroma.from_documents(
        documents=docs,
        embedding=embedding,
        persist_directory=persist_path # Guardar no disco para reutilizar depois
    )
    return vectorstore

# Carrega o banco já salvo no disco
def load_vectorstore(persist_path=CHROMA_DIR):
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    return Chroma(persist_directory=persist_path, embedding_function=embeddings)

def retrieve_context(question, k=3):
    vectorstore = load_vectorstore()
    retriever = vectorstore.as_retriever(search_kwargs={"k": k})
    docs = retriever.invoke(question)
    print(f"\n[DEBUG] Contextos recuperados para a pergunta: '{question}'")
    for i, d in enumerate(docs):
        print(f"\n--- Chunk {i+1} ---\n{d.page_content[:500]}")
    return [doc.page_content for doc in docs]



##  def create_prompt_template():

# #def search_content(chunks, question):
#     pergunta_palavras = set(re.findall(r'\w+', question.lower()))
#     trechos_com_peso = []
#
#     for chunk in chunks:
#         chunk_texto = chunk.page_content.lower()
#         chunk_palavras = set(re.findall(r'\w+', chunk_texto))
#         intersecao = pergunta_palavras.intersection(chunk_palavras)
#
#         # Só considera trechos com pelo menos 2 palavras em comum
#         if len(intersecao) >= 2:
#             score = len(intersecao)
#             trechos_com_peso.append((score, chunk.page_content))
#
#     # Ordena por score (mais relevante primeiro)
#     trechos_com_peso.sort(reverse=True, key=lambda x: x[0])
#
#     # Retorna só os textos dos 3 trechos mais relevantes
#     return [trecho for _, trecho in trechos_com_peso[:3]]


def generate_response(question, context):
    final_context = "\n\n".join(context)
    prompt = f"""
    Você é uma IA que responde com base apenas nas informações abaixo.
    
    Contexto:
    --------------------
    {final_context}
    --------------------
    
    Responda à pergunta abaixo de forma clara, objetiva e sem inventar nada. 
    Se a resposta não estiver no contexto, diga "Não sei responder com base nos documentos."
    
    Pergunta: {question}
    Resposta:
    """
    # dados que serão enviados na requisição HTTP
    payload = {
        "model": "llama2",
        "prompt": prompt,
        "temperature": 0.5, # Controla criatividade
        "stream": False # Envia respostas em partes
    }
    # aqui ele manda a url e o json do HTTP de cima para o ollama obter respostas
    response = requests.post(OLLAMA_URL, json=payload)

    if response.status_code == 200:
        content = response.json()
        return content.get("response", "").strip()
    else:
        return f"Erro: {response.status_code} - {response.text}"


def main():
    docs = load_documents()
    print("Documentos carregados.")

    chunks = split_documents(docs)
    print("Documentos divididos em chunks.")

    create_vectorstore(chunks)
    print("Base vetorial criada com sucesso.\n")

    while True:
        question = input("Pergunte sobre: ")
        if question.lower() == "sair":
            break

        context = retrieve_context(question)

        if not context:
            print("Nenhum contexto encontrado.")
            continue

        answer = generate_response(question, context)
        print(f"\nResposta da IA:\n{answer}\n")

if __name__ == "__main__":
    main()