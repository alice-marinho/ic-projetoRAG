# Função que verifica arquivo pdf e txt, le e retorna eles
import os
import fitz

from langchain.schema import Document
from config import FOLDER_PATH


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