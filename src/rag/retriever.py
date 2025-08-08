import re

from rag.query_transformations.self_querying import create_self_query_retriever
from vectorstore import VectorStoreManager


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

        retriever = create_self_query_retriever(actual_vectorstore)
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
