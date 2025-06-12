import re
from vectorstore import VectorStoreManager


def clean_text(text):
    """Remove quebras de linha extras e espaços duplicados."""
    return re.sub(r'\s+', ' ', text.strip())


def retrieve_context(question):
    vectorstore = VectorStoreManager()

    retriever = vectorstore.load_vectorstore().as_retriever(
        search_type="mmr",
        search_kwargs={"k": 10, "lambda_mult": 0.7}  # Ajuste para respostas mais precisas
    )

    docs = retriever.invoke(question)

    print(f"\n[DEBUG] Contextos recuperados para a pergunta: '{question}'")

    seen = set()
    context_chunks = []

    for doc in docs:
        cleaned = clean_text(doc.page_content)
        if cleaned not in seen and len(cleaned) > 50:  # Ignora textos muito curtos e duplicados
            seen.add(cleaned)
            context_chunks.append(cleaned)

    return context_chunks
