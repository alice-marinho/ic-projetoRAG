import cohere

from sentence_transformers import SentenceTransformer, util

from backend.database.manager import VectorStoreManager
from backend.src.config.llm_config import RERANKER_API_KEY, COHERE_MODEL
from backend.src.config.vectorstore_config import EMBEDDING_SENTENCE_MODEL
from backend.src.llm import LLMClient
from backend.src.rag.query_transformations.self_querying import SelfQuery
from backend.src.utils.logger import setup_logger
from langchain.schema import Document

logger = setup_logger(__name__)

class RAGRetriever:
    """Self-Query, Fallback e Reranking."""
    def __init__(self):
        try:
            logger.info("Inicializando RAGRetriever...")
            self.vectordb_manager = VectorStoreManager()
            self.vectorstore = self.vectordb_manager.load_vectorstore()

            self.llm = LLMClient().llm
            self.self_query_retriever = SelfQuery().create_self_query_retriever(
                vectorstore=self.vectorstore,
                llm=self.llm
            )
            self.fallback_retriever = self.vectorstore.as_retriever(
                search_type="mmr",
                search_kwargs={"k": 10, "lambda_mult": 0.5}
            )
            self.cohere_client = cohere.Client(RERANKER_API_KEY)

            logger.info("RAGRetriever inicializado com sucesso.")

        except Exception as e:
            logger.error(f"Erro fatal ao inicializar o RAGRetriever: {e}")
            self.self_query_retriever = None
            self.fallback_retriever = None
            self.cohere_client = None


    def _fallback_route(self, question: str, k: int):
        logger.warning("Self-Query não retornou resultados. Acionando rota de Fallback.")
        if not self.fallback_retriever or not self.cohere_client:
            logger.error("Fallback Retriever ou Cohere Client não inicializados.")
            return []

        try:
            logger.info("Fallback: Executando busca de texto direta...")
            # child_chunks_fallback = vectordb.vectorstore.similarity_search_with_score(question, k=k)
            child_chunks_fallback = self.fallback_retriever.invoke(question)
            if not child_chunks_fallback:
                logger.warning("Busca Fallback (MMR) também não encontrou chunks.")
                return []

            logger.info(f"Fallback encontrou {len(child_chunks_fallback)} chunks. Buscando documentos pais...")

            docs_text = [str(chunk.page_content) for chunk in child_chunks_fallback]
            ranked_results = self.cohere_client.rerank(query=question, documents=docs_text, model=COHERE_MODEL, top_n=3)

            top_chunks = []
            for hit in ranked_results.results:
                original_doc = child_chunks_fallback[hit.index]
                top_chunks.append(original_doc)

                ### Para visualizar os conteúdos e o score ###
                # score = hit.relevance_score
                # print(f"Score: {score:.4f}\nConteúdo: {original_doc.page_content[:200]}...\n{'-' * 80}")

            logger.info(f"Rerank selecionou {len(top_chunks)} chunks. Buscando pais...")
            final_docs = self.vectordb_manager.search_parents_document(top_chunks)

            return final_docs

        except Exception as e:
            logger.error(f"A busca de fallback também falhou: {e}")
            return []  # Retorna vazio se tudo falhar

    def retriever_final_context(self, question: str, k: int = 10) -> list[Document]:
        """
        Função de recuperação principal. Orquestra a busca usando a estratégia
        "Self-Query com Fallback" para encontrar o contexto mais relevante.

        Args:
            question: A pergunta feita pelo usuário final.
            k: O número de documentos a serem recuperados na busca direta (fallback).

        Returns:
            Uma lista de Documentos (os Parent Documents) contendo o contexto.
        """

        logger.info(f"===== Iniciando recuperação de contexto para a pergunta: ====\n '{question}'"+ ("-"*10))
        if not self.self_query_retriever:
            logger.error("SelfQueryRetriever não foi inicializado corretamente.")
            return []
        final_docs = []

        try:
            logger.info("Tentativa 1: Executando com Self-Query...")
            child_chunks = self.self_query_retriever.invoke(question)

            #### Para visualizar o conteúdo do self-query
            # for i, doc in enumerate(final_docs, 1):
            #     logger.info(f"Documento {i}:")
            #     logger.info(f"  Metadata: {doc.metadata}{'-' * 80}")

            if child_chunks:
                logger.info(f"Self-Query encontrou {len(child_chunks)} chunks. Buscando pais...")
                final_docs = self.vectordb_manager.search_parents_document(child_chunks)
            else:
                final_docs = []


        except Exception as e:
            logger.error(f"O Self-Query Retriever falhou com uma exceção:\n\n {e}.\n\n ==== Acionando fallback. ====")
            logger.debug("Tipo do EMBEDDING_SENTENCE_MODEL:", type(EMBEDDING_SENTENCE_MODEL))
            final_docs = []

        # --- Verificação e Fallback ---
        if not final_docs:
            logger.warning("Self-Query não retornou resultados. Acionando rota de Fallback.")
            final_docs = self._fallback_route(question, k)

        return final_docs


    def _metadata_verification(question: str, docs: list, threshold: float =0.55) -> bool:
        if not docs: return False

        model = SentenceTransformer(EMBEDDING_SENTENCE_MODEL)

        meta_text = []
        for doc in docs:
            comp = str(doc.metadata.get("componente", ""))
            curso = str(doc.metadata.get("curso", ""))
            periodo = str(doc.metadata.get("periodo", ""))
            codigo = str(doc.metadata.get("codigo", ""))
            meta_text.append(f"{comp} - {curso} - {periodo} - {codigo}")

        quest_emb = model.encode(question)
        meta_embs = model.encode(meta_text)

        similaridade = util.cos_sim(quest_emb, meta_embs)[0]
        max_similaridade = float(similaridade.max().item())

        return max_similaridade >= threshold
