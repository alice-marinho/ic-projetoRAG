from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema import Document
from utils.logger import *

logger = setup_logger(__name__)

def split_json(clean_date):
    documents = []

    logger.info("Criando as chunks do json formatado")
    for item in clean_date:
        # chunk único por disciplina
        content_parts = []

        for field, value in item.items():
            if value and str(value).strip():
                content_parts.append(f"{field}: {value}")

        # um único documento por disciplina
        doc_content = "\n".join(content_parts)
        logger.debug("Chunks criadas e unificadas no documento")

        documents.append(Document(
            page_content=doc_content,
            metadata={
                "source": "dados_limpos.json",
                "curso": item.get("Curso", ""),
                "componente": item.get("Componente curricular", ""),
                "semestre": item.get("Semestre", ""),
                "codigo": item.get("Código", "")
            }
        ))

    return documents

def split_documents(documents: list[Document]):
    chunks = RecursiveCharacterTextSplitter(
        chunk_size=400,
        chunk_overlap=50,
        separators=["\n\n", "."]
    )
    return chunks.split_documents(documents)