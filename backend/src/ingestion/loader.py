# Função que verifica arquivo pdf e txt, le e retorna eles
import os
import fitz

from langchain.schema import Document
from backend.src.config.config import DATA_DIR, DOCS_DIR


def load_documents():
    # verifica se o arquivo existe antes de abrir
    if not os.path.exists(DOCS_DIR):
        raise FileNotFoundError(f"Arquivo não encontrado: {DOCS_DIR}")

    docs = []

    for document in os.listdir(DOCS_DIR): # ele lista os arq as pasta
        if document.lower().endswith(".pdf"):
            document_path = os.path.join(DOCS_DIR, document) # cria o caminho
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