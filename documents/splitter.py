from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema import Document


def split_documents(documents: list[Document]):
    chunks = RecursiveCharacterTextSplitter(
        chunk_size=400,
        chunk_overlap=50,
        separators=["\n\n", "."]
    )
    return chunks.split_documents(documents)