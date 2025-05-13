from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from config import CHROMA_DIR


def load_vectorstore(persist_path=CHROMA_DIR):
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    return Chroma(persist_directory=persist_path, embedding_function=embeddings)
