import shutil
import uuid
import logging

# from google.genai import client
from langchain.retrievers import ParentDocumentRetriever
from langchain_core.stores import InMemoryStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema import Document
from pathlib import Path

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from config.config import CHROMA_DIR
from config.llm_config import GEMINI_API_KEY
from config.vectorstore_config import EMBEDDING_PROVIDER, EMBEDDING_SENTENCE_MODEL, EMBEDDING_GEMINI_MODEL
from database.db_config import MONGO_DATABASE
from vectorstore.mongo_db import MongoDocstore

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
    def __init__(
            self,
            persist_path=CHROMA_DIR):
        self.persist_path = Path(persist_path)
        if EMBEDDING_PROVIDER == "gemini":
            self.model_name = EMBEDDING_GEMINI_MODEL
            self.embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_GEMINI_MODEL, google_api_key=GEMINI_API_KEY)
        else:
            self.model_name = EMBEDDING_SENTENCE_MODEL
            self.embeddings = HuggingFaceEmbeddings(model_name=self.model_name)

        self.vectorstore = Chroma(
                persist_directory=str(self.persist_path),
                embedding_function=self.embeddings
            )

        # self.retriever = None
        # self.vectorstore = None
        self.docstore = MongoDocstore(uri=MONGO_DATABASE, db_name="rag_db", collection_name="parents")
        self.child_splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50)

        self.retriever = ParentDocumentRetriever(
            vectorstore=self.vectorstore,
            docstore=self.docstore,
            child_splitter=self.child_splitter
        )
        logger.info(f"VectorStoreManager inicializado com modelo: {self.model_name}")


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
        return Chroma(
            persist_directory=str(self.persist_path),
            embedding_function=self.embeddings
        )

    def clean_storage(self):
        """
        Força a exclusão completa dos diretórios de armazenamento para garantir
        uma recriação limpa.
        """
        logger.info("Executando limpeza forçada dos diretórios de armazenamento...")

        # Converte os paths para objetos Path se ainda não forem
        # chroma_path = Path(self.persist_path)
        try:
            if hasattr(self.vectorstore, "_client"):
                del self.vectorstore  # Encerra o client interno
                logger.info("Conexão com ChromaDB encerrada.")
        except Exception as e:
            logger.warning(f"Erro ao encerrar conexão do ChromaDB: {e}")

        try:
            shutil.rmtree(self.persist_path, ignore_errors=True)
            logger.info(f"Diretório {self.persist_path} apagado com sucesso.")
        except Exception as e:
            logger.warning(f"Não foi possível apagar o ChromaDB: \n {e}")


    def search_parents_document(self, chunks: list[Document]) -> list[Document]:
        """
        Busca os documentos pais COMPLETOS a partir de uma lista de chunks filhos.
        """
        if not chunks:
            return []

        parent_ids = []
        for chunk in chunks:
            if hasattr(chunk, 'metadata') and 'parent_id' in chunk.metadata:
                parent_ids.append(chunk.metadata['parent_id'])

        if not parent_ids:
            logger.warning("Nenhum parent_id encontrado nos chunks fornecidos.")
            return []

        unique_parent_ids = list(set(parent_ids))

        parent_docs = self.docstore.mget(unique_parent_ids)

        documentos_encontrados = [doc for doc in parent_docs if doc is not None]

        logger.info(
            f"\n\nDe {len(unique_parent_ids)} IDs de pais únicos, {len(documentos_encontrados)} documentos completos "
            f"foram encontrados no docstore.\n\n")

        return documentos_encontrados

    def _create_parents_documents(self, clean_data: list[dict]) -> list[Document]:
        """Transforma o JSON limpo em documentos pais (sem alterações)."""
        parents_documents = []
        for item in clean_data:
            content_parts = [f"{field}: {value}" for field, value in item.items() if value and str(value).strip()]
            doc_content = "\n".join(content_parts)
            metadata = {
                "source": "dados_limpos.json",
                "curso": str(item.get("Curso", "")),
                "componente": str(item.get("Componente curricular", "")),
                "periodo": str(item.get("Periodo", "")),
                "codigo": str(item.get("Código", ""))
            }
            parents_documents.append(Document(page_content=doc_content, metadata=metadata))
        return parents_documents


    def organize_disciplines(self, clean_data: list[dict]):
        """
        Recebe os dados, cria os Parents com IDs explícitos
        e usa o retriever para salvar.
        """
        logger.info("Iniciando processo de indexação")
        parent_documents = self._create_parents_documents(clean_data)

        parent_docs_to_store = []
        child_chunks_to_index = []
        for parent_doc in parent_documents:
            # Gera um ID único para este pai
            parent_id = str(uuid.uuid4())

            # Adiciona o ID aos metadados do próprio documento pai
            parent_doc.metadata["parent_id"] = parent_id
            parent_docs_to_store.append((parent_id, parent_doc))

            # Quebra o documento pai em chunks filhos
            child_docs = self.child_splitter.split_documents([parent_doc])

            # Child recebe o ID do Parent, e mais os metadados
            for child in child_docs:
                child.metadata["parent_id"] = parent_id
                child.metadata["curso"] = parent_doc.metadata.get("curso", "")
                child.metadata["componente"] = parent_doc.metadata.get("componente", "")
                child.metadata["periodo"] = parent_doc.metadata.get("periodo", "")
                child.metadata["codigo"] = parent_doc.metadata.get("codigo", "")

            child_chunks_to_index.extend(child_docs)

            # Adiciona os pais ao docstore e os filhos ao vectorstore
        logger.info(f"Adicionando {len(parent_docs_to_store)} documentos pais ao docstore.")
        self.docstore.mset(parent_docs_to_store)

        logger.info(f"Adicionando {len(child_chunks_to_index)} chunks filhos ao ChromaDB.")
        self.vectorstore.add_documents(child_chunks_to_index)

        # Verificação final
        total_chunks = len(self.vectorstore.get(include=[])['ids'])
        chunks_data = self.vectorstore.get(include=["metadatas"])
        chunks_with_parent = sum(1 for m in chunks_data["metadatas"] if m and "parent_id" in m)

        logger.info(
            f"VERIFICAÇÃO DE VÍNCULO: {chunks_with_parent} de {total_chunks} chunks foram vinculados a um parent_id.")
        logger.info(f"Indexação concluída. {len(parent_documents)} disciplinas processadas.")

    def get_retriever(self):
        """Retorna a instância do retriever principal para ser usada nas buscas."""
        return self.retriever

    def load_or_create_components(self):
        """Carrega o ChromaDB do disco e (re)cria a instância do retriever."""
        logger.info(f"Carregando vectorstore de: {self.persist_path}")
        self.vectorstore = Chroma(
            persist_directory=str(self.persist_path),
            embedding_function=self.embeddings
        )

        self.retriever = ParentDocumentRetriever(
            vectorstore=self.vectorstore,
            docstore=self.docstore,
            child_splitter=self.child_splitter,
        )
        logger.info("Componentes de Vectorstore e Retriever (re)carregados.")

# def main():
#     VectorStoreManager().clean_storage()
#
# if __name__ == "__main__":
#     main()