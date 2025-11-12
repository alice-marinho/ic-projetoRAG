import shutil
import uuid
import logging

# from google.genai import client
from langchain.retrievers import ParentDocumentRetriever
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_huggingface import HuggingFaceEmbeddings


from config.vectorstore_config import EMBEDDING_SENTENCE_MODEL
from database.database import SessionLocal, sqlal_engine  # , pg_engine
from database.db_config import DATABASE_URL
from langchain_postgres import PGVectorStore, PGVector

from vectorstore.postgres_db import PostgresDocstore

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class SingletonMeta(type):
    """Padrão Singleton para garantir uma única instância."""
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class VectorStoreManager(metaclass=SingletonMeta):
    def __init__(self):
        self.model_name = EMBEDDING_SENTENCE_MODEL
        self.embeddings = HuggingFaceEmbeddings(model_name=self.model_name)
        self.db_session = SessionLocal

        # self.vectorstore = PGVectorStore.create_sync(
        #     engine=pg_engine,
        #     embedding_service =self.embeddings,
        #     table_name="child_chunk"
        # )


        self.vectorstore = PGVector(
            connection=DATABASE_URL,
            embeddings=self.embeddings,
            collection_name="child_chunks",
            use_jsonb=True        )

        # self.vectorstore = SQLAlchemyVectorStore(
        #     session_factory=self.db_session,
        #     embedding_function=self.embeddings
        # )

        self.docstore = PostgresDocstore(db_session=self.db_session)
        self.child_splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50)

        self.retriever = ParentDocumentRetriever(
            vectorstore=self.vectorstore,
            docstore=self.docstore,
            child_splitter=self.child_splitter
        )
        logger.info(f"VectorStoreManager inicializado com modelo: {self.model_name}")


    def clear(self):
        self.vectorstore.delete()
        logger.info("Banco Vetorial PGVector deletado com sucesso")

    @staticmethod
    def _remove_duplicates(docs):
        unique_docs = []
        seen_texts = set()
        for doc in docs:
            if doc.page_content not in seen_texts:
                unique_docs.append(doc)
                seen_texts.add(doc.page_content)

        logger.info(f"{len(unique_docs)} documentos únicos foram adicionados ao banco vetorial.")
        return unique_docs


    def load_vectorstore(self):
        logger.debug("Carregando banco vetorial persistido.")
        return self.vectorstore


    def search_parents_document(self, chunks: list[Document]) -> list[Document]:
        """
        Busca os documentos pais COMPLETOS a partir de uma lista de chunks filhos.
        """
        if not chunks:
            return []

        parent_ids = [chunk.metadata.get('doc_id') for chunk in chunks if 'doc_id' in chunk.metadata]
        if not parent_ids:
            logger.warning("Nenhum doc_id encontrado nos chunks fornecidos.")
            return []

        unique_parent_ids = list(set(parent_ids))
        parent_docs = self.docstore.mget(unique_parent_ids)

        documentos_encontrados = [doc for doc in parent_docs if doc is not None]

        logger.info(
            f"\n\nDe {len(unique_parent_ids)} IDs de pais únicos, {len(documentos_encontrados)} documentos completos "
            f"foram encontrados no docstore.\n\n")

        return documentos_encontrados

    @staticmethod
    def _create_parents_documents(clean_data: list[dict]) -> list[Document]:
        """Transforma o JSON limpo em documentos pais (sem alterações)."""
        parents_documents = []
        for item in clean_data:
            content_parts = [f"{field}: {value}" for field, value in item.items() if value and str(value).strip()]
            doc_content = "\n".join(content_parts)
            metadata = {
                "source": "dados_limpos.json",
                "curso": str(item.get("Curso", "")),
                "componente": str(item.get("Componente curricular", "")),
                "periodo": str(item.get("Período Educacional", "")),
                "codigo": str(item.get("Código", ""))
            }
            parents_documents.append(Document(page_content=doc_content, metadata=metadata))
        return parents_documents

    def organize_disciplines(self, clean_data: list[dict]):
        """
        [VERSÃO MANUAL E À PROVA DE FALHAS]
        Salva os pais e os filhos separadamente, sem usar o retriever.
        """
        logger.info("Iniciando processo de indexação MANUAL...")
        parent_documents = self._create_parents_documents(clean_data)

        parents_save = []
        chunks_save = []
        chunk_id_save = []

        logger.info(f"Preparando {len(parent_documents)} pais e seus chunks...")
        for parent_doc in parent_documents:
            parent_id = str(uuid.uuid4())
            parent_doc.metadata["doc_id"] = parent_id

            parents_save.append((parent_id, parent_doc))

            chunks = self.child_splitter.split_documents([parent_doc])

            for chunk in chunks:
                chunk.metadata["doc_id"] = parent_id
                chunk_id_save.append(str(uuid.uuid4()))

            chunks_save.extend(chunks)

        logger.info(f"Total de pais para salvar: {len(parents_save)}")
        logger.info(f"Total de chunks para salvar: {len(chunks_save)}")

        try:
            logger.info("Passo 1/2: Salvando documentos pais no Docstore...")
            self.docstore.mset(parents_save)
            logger.info(">>> SUCESSO: Documentos pais salvos.")

            logger.info("Passo 2/2: Salvando chunks filhos no Vectorstore...")
            self.vectorstore.add_documents(chunks_save, ids=chunk_id_save)
            logger.info(">>> SUCESSO: Chunks filhos salvos.")

        except Exception as e:
            logger.error("!!!!!!!!!!!!!! ERRO REAL NA INGESTÃO MANUAL !!!!!!!!!!!!!!")
            logger.error(f"Falha durante o processo de salvamento manual: {e}")
            logger.error("O processo foi interrompido. Verifique o erro acima.")
            logger.error("!!!!!!!!!!!!!! ERRO REAL NA INGESTÃO MANUAL !!!!!!!!!!!!!!")

            try:
                logger.warning("Tentando reverter salvamento...")
                parent_keys = [key for key, doc in parents_save]
                self.docstore.mdelete(parent_keys)
                logger.warning("Documentos pais parciais removidos.")
            except Exception as cleanup_e:
                logger.error(f"Erro durante a limpeza de dados parciais: {cleanup_e}")
            raise e

    def get_retriever(self):
        """Retorna a instância do retriever principal para ser usada nas buscas."""
        return self.retriever


def get_vectorstore_sync(embeddings):
    return PGVectorStore.create_sync(
        engine=sqlal_engine,
        embedding_service=embeddings,
        table_name="child_chunk"
    )

