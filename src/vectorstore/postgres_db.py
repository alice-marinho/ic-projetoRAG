from typing import Tuple, List

import unicodedata
from langchain_core.stores import BaseStore
from langchain.schema import Document
from sqlalchemy.orm import Session

from database.database import SessionLocal
from database.models import ParentDocument, ChildChunk
from utils.logger import setup_logger

logger = setup_logger(__name__)

class PostgresDocstore(BaseStore):
    def __init__(self, db_session= SessionLocal):
        self.db_session = db_session

    def set(self, key:str, document: Document):
        """Salva o ParentDocument"""
        with self.db_session() as session:
            try:
                parent = session.get(ParentDocument, key)
                if not parent:
                    parent = ParentDocument(id=key)
                normalized_metadata = {normalize_key(k): v for k, v in document.metadata.items()}
                parent.metadata_json = normalized_metadata
                parent.content = {"page_content": document.page_content}
                session.add(parent)


                session.commit()
            except Exception as e:
                logger.error(f"Falha ao salvar ParentDocument (ID: {key}) no docstore:\n\n {e}")
                session.rollback()
                raise e

    def get(self, key: str)-> Document | None:
        """Paga um ParentDocument"""
        with self.db_session() as session:
            parent = session.get(ParentDocument, key)
            if not parent:
                logger.warning("Não encontrado Parent")
                return None

            page_content_str = parent.content.get("page_content", "")

            return Document(page_content=page_content_str,
                            metadata=parent.metadata_json)

    def mset(self, items: List[Tuple[str, Document]]):
        logger.info(f"DOCSTORE MSET: Recebeu {len(items)} pais para salvar.")

        with self.db_session() as session:
            try:
                for key, doc in items:
                    # logger.info(f"DOCSTORE MSET: Processando pai com ID (key) = {key}")
                    parent = session.get(ParentDocument, key)
                    if not parent:
                        # logger.info(f"DOCSTORE MSET: Criando novo ParentDocument com ID = {key}")
                        parent = ParentDocument(id=key)
                    else:
                        logger.info(f"DOCSTORE MSET: Atualizando ParentDocument existente com ID = {key}")

                    parent.content = {"page_content": doc.page_content}
                    parent.metadata_json = doc.metadata

                    session.merge(parent)
                    logger.info(f"DOCSTORE MSET: 'session.merge(parent)' concluído para ID = {key}")

                logger.info("DOCSTORE MSET: Tentando session.commit() para todos os pais...")
                session.commit()
                logger.info(f"DOCSTORE MSET: COMMIT BEM-SUCEDIDO. {len(items)} pais salvos.")

            except Exception as e:
                # VAMOS EXPOR O ERRO REAL
                logger.error(f"DOCSTORE MSET: Falha no session.commit() ao salvar pais: {e}")
                session.rollback()
                raise e

    def mget(self, keys: List[str]):
        with self.db_session() as session:
            results = session.query(ParentDocument).filter(ParentDocument.id.in_(keys)).all()
            doc_map = {doc.id: doc for doc in results}

            final_docs = []
            for key in keys:
                parent = doc_map.get(key)
                if parent:
                    page_content_str = parent.content.get("page_content", "")
                    final_docs.append(Document(page_content=page_content_str,
                                               metadata=parent.metadata_json))
                else:
                    logger.warning(f"ParentDocument (ID: {key}) não encontrado no mget.")
                    final_docs.append(None)

            return final_docs

    def mdelete(self, keys: list[str]):
        with self.db_session() as session:
            session.query(ParentDocument).filter(ParentDocument.id.in_(keys)).delete(synchronize_session=False)
            session.commit()

    def yield_keys(self):
        pass

    def clear(self):
        """Limpa todas as tabelas de documentos e chunks."""
        with self.db_session() as session:
            session.query(ChildChunk).delete()
            session.query(ParentDocument).delete()
            session.commit()
            logger.info("Tabelas ParentDocument e ChildChunk limpas com sucesso.")


def normalize_key(key: str) -> str:
    key = key.lower()
    key = ''.join(c for c in unicodedata.normalize('NFD', key) if unicodedata.category(c) != 'Mn')
    return key.replace(" ", "_")