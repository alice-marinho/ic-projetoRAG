from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from config import CHROMA_DIR


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