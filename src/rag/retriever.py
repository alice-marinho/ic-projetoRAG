import re
import cohere

from rerankers import Reranker
from sentence_transformers import SentenceTransformer, util
from config.llm_config import RERANKER_API_KEY, COHERE_MODEL
from config.vectorstore_config import EMBEDDING_SENTENCE_MODEL
from rag.query_transformations.self_querying import SelfQuery
from utils.logger import setup_logger
from langchain.schema import Document

from vectorstore import VectorStoreManager, manager


def clean_text(text):
    """Remove quebras de linha extras e espaços duplicados."""
    return re.sub(r'\s+', ' ', text.strip())


def retrieve_context(question: str, k : int = 5) -> list[str] | list[dict]:
    try:
        vectorstore = VectorStoreManager()

        # retriever = vectorstore.load_vectorstore().as_retriever(
        #     search_type="mmr", # Maximal Marginal Relevance
        #     search_kwargs={"k": k, "lambda_mult": 0.5}  # Ajuste para respostas mais precisas
        # )
        actual_vectorstore = vectorstore.load_vectorstore()

        self_query = SelfQuery()
        retriever = self_query.create_self_query_retriever(actual_vectorstore)
        docs = retriever.invoke(question)

        print(f"\n[DEBUG] Contextos recuperados para a pergunta: '{question}'")

        seen = set() # Remover duplicados
        context_chunks = []

        for doc in docs:
            cleaned = clean_text(doc.page_content)
            if cleaned not in seen and len(cleaned) > 50:  # Ignora textos muito curtos e duplicados
                seen.add(cleaned)
                context_chunks.append(cleaned)

        return context_chunks

    except Exception as e:
        print(f"Erro no retrieve_context: {str(e)}")
        return []

logger = setup_logger(__name__)
vectordb = VectorStoreManager()

def retrieve_final_context(question: str, k: int = 10) -> list[Document]:
    """
    Função de recuperação principal. Orquestra a busca usando a estratégia
    "Self-Query com Fallback" para encontrar o contexto mais relevante.

    Args:
        question: A pergunta feita pelo usuário final.
        k: O número de documentos a serem recuperados na busca direta (fallback).

    Returns:
        Uma lista de Documentos (os Parent Documents) contendo o contexto.
    """

   # logger = setup_logger(__name__)
    logger.info(f"===== Iniciando recuperação de contexto para a pergunta: ====\n '{question}'"+ ("-"*10))

    try:
        logger.info("Tentativa 1: Executando com Self-Query...")
        self_query_retriever = SelfQuery().create_self_query_retriever(vectordb.load_vectorstore())
        final_docs = self_query_retriever.invoke(question)

        #### Para visualizar o conteúdo do self-query
        # for i, doc in enumerate(final_docs, 1):
        #     logger.info(f"Documento {i}:")
        #     logger.info(f"  Metadata: {doc.metadata}{'-' * 80}")


        if not _metadata_verification(question, final_docs):
            logger.warning("Verificação de metadados falhou. Acionando fallback...")
            final_docs = _fallback_route(question, k)


    except Exception as e:
        logger.error(f"O Self-Query Retriever falhou com uma exceção:\n\n {e}.\n\n ==== Acionando fallback. ====")
        logger.debug("Tipo do EMBEDDING_SENTENCE_MODEL:", type(EMBEDDING_SENTENCE_MODEL))
        final_docs = []

    # --- Verificação e Fallback ---
    if not final_docs:
        logger.warning("Self-Query não retornou resultados. Acionando rota de Fallback.")
        final_docs = _fallback_route(question, k)

    return final_docs

def _fallback_route(question: str, k: int):
    logger.warning("Self-Query não retornou resultados. Acionando rota de Fallback.")

    # --- TENTATIVA 2: O Caminho de Fallback (Busca Direta)

    try:
        logger.info("Fallback: Executando busca de texto direta...")
        # child_chunks_fallback = vectordb.vectorstore.similarity_search_with_score(question, k=k)
        child_chunks_fallback = vectordb.load_vectorstore().as_retriever(
            search_type="mmr",  # Maximal Marginal Relevance
            search_kwargs={"k": k, "lambda_mult": 0.5}  # Ajuste para respostas mais precisas
        ).invoke(question)

        if child_chunks_fallback:
            logger.info(f"Fallback encontrou {len(child_chunks_fallback)} chunks. Buscando documentos pais...")
            # --- Reranking ---

            # reranker = Reranker("BAAI/bge-reranker-v2-m3", api_provider="huggingface")
            # reranker = Reranker("BAAI/bge-reranker-base", api_provider="huggingface")
            docs_text = [str(chunk.page_content) for chunk in child_chunks_fallback]


            co = cohere.Client(RERANKER_API_KEY)
            ranked_results = co.rerank(query=question, documents=docs_text, model=COHERE_MODEL)

            top_chunks = []
            for hit in ranked_results.results[:5]:
                # doc_text = hit.document['text']
                original_index = hit.index


                original_doc = child_chunks_fallback[original_index]
                top_chunks.append(original_doc)

                ### Para visualizar os conteúdos e o score ###
                # score = hit.relevance_score
                # print(f"Score: {score:.4f}\nConteúdo: {original_doc.page_content[:200]}...\n{'-' * 80}")

            # Agora 'top_chunks' contém os objetos Document corretos
            final_docs = vectordb.search_parents_document(top_chunks)

            return final_docs

            # docs = vectordb.search_parents_document(child_chunks_fallback)

            # print(docs)
        else:
            logger.warning("Busca por similaridade também não encontrou chunks.")
    except Exception as e:
                logger.error(f"A busca de fallback também falhou: {e}")
                return []  # Retorna vazio se tudo falhar


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
