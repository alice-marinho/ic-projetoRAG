import logging
from pathlib import Path

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from config.config import CHROMA_DIR

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
    def __init__(self, persist_path=CHROMA_DIR, model_name="sentence-transformers/multi-qa-mpnet-base-dot-v1"):
        self.persist_path = Path(persist_path)
        self.model_name = model_name
        self.embeddings = HuggingFaceEmbeddings(model_name=self.model_name)
        logger.info(f"VectorStoreManager inicializado com modelo: {self.model_name}")

    def get_embeddings(self):
        logger.debug("Obtendo embeddings.")
        return self.embeddings

    @staticmethod
    def remove_duplicates(docs):
        unique_docs = []
        seen_texts = set()
        for doc in docs:
            if doc.page_content not in seen_texts:
                unique_docs.append(doc)
                seen_texts.add(doc.page_content)

        logger.info(f"{len(unique_docs)} documentos únicos foram adicionados ao banco vetorial.")
        return unique_docs

    def create_vectorstore(self, docs):
        logger.debug("Criando banco vetorial com documentos.")
        unique_docs = self.remove_duplicates(docs)
        return Chroma.from_documents(
            documents=unique_docs,
            embedding=self.embeddings,
            persist_directory=str(self.persist_path)
        )

    def load_vectorstore(self):
        logger.debug("Carregando banco vetorial persistido.")
        return Chroma(
            persist_directory=str(self.persist_path),
            embedding_function=self.embeddings
        )

    def buscar_chunks_por_metadados(self, curso: str, periodo: str, componente: str, k: int = 50):
        """
        Busca os chunks no vetor usando filtros de metadados exatos.
        """
        store = self.load_vectorstore()

        where_filter = {
            "Curso": curso,
            "Período Educacional": periodo,
            "Componente curricular": componente
        }

        try:
            docs = store.similarity_search(
                query=componente,
                k=k,
                filter=where_filter
            )
            return docs
        except Exception as e:
            logger.error(f"Erro ao buscar chunks de '{componente}': {e}")
            return []

    def buscar_chunks_por_texto(self, texto_busca: str, k: int = 10):
        """
        Busca chunks com base em conteúdo textual (ementa, objetivos, etc.), sem usar metadados.
        """
        store = self.load_vectorstore()

        try:
            docs = store.similarity_search(query=texto_busca, k=k)

            if not docs:
                logger.warning(f"Nenhum chunk encontrado para: {texto_busca}")
            return docs

        except Exception as e:
            logger.error(f"Erro ao buscar chunks de '{texto_busca}': {e}")
            return []


