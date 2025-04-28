from vectorstore import load_vectorstore


def retrieve_context(question):
    vectorstore = load_vectorstore()
    retriever = vectorstore.as_retriever(search_type="mmr", search_kwargs={"k": 10, "lambda_mult": 0.8})

    docs = retriever.invoke(question)

    print(f"\n[DEBUG] Contextos recuperados para a pergunta: '{question}'")

    relevant_docs = []
    for i, d in enumerate(docs):
        if any(keyword.lower() in d.page_content.lower() for keyword in question.split()):
            relevant_docs.append(d)

    return [doc.page_content for doc in relevant_docs] if relevant_docs else []
