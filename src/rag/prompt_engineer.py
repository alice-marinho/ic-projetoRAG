from llm import LLMClient

def summarize_question(question):
    """
    Reformula a pergunta caso esteja mal escrita, incompleta ou confusa.
    Sempre oferece a versão original e a versão sugerida para escolha.

    Args:
        question (str): Pergunta original.

    Returns:
        str: Pergunta escolhida pelo usuário.
    """
    prompt = (
        "Haja como um especialista em processamento de linguagem natural. "
        "Para todas as minhas perguntas, dê a melhor versão delas e ao final me permita escolher entre a sua e a minha. "
        "Somente melhore, não me dê informações ou respostas das perguntas"
        "Responda apenas com a pergunta reformulada, sem explicações e tudo em Português - BR."
        "Aqui está a pergunta:\n\n"
        f"{question}"
    )

    llm_client = LLMClient()
    suggested_question = llm_client.chat(prompt)

    print(f"\nSugestão de reformulação: {suggested_question}")
    choice = input("Deseja usar a versão sugerida? (s/n): ").strip().lower()

    if choice == 's':
        return suggested_question
    else:
        return question


# from llm import LLMClient
#
#
# def summarize_question(question):
#     """
#     Reformula a pergunta caso esteja mal escrita, incompleta ou confusa.
#     Caso já esteja clara, retorna 'OK' e a função mantém a pergunta original.
#
#     Args:
#         question (str): Pergunta original.
#         client: Cliente da API para chamadas de chat completions.
#
#     Returns:
#         str: Pergunta reformulada ou original.
#     """
#     prompt = (
#         "Reformule a pergunta abaixo apenas se ela estiver mal escrita, incompleta ou confusa. "
#         "Caso já esteja clara e direta no contexto educacional, responda apenas com 'OK'\n\n"
#         f"{question}"
#     )
#
#     llm_client = LLMClient()
#     content = llm_client.chat(prompt)
#
#     # Se a IA respondeu apenas "OK", usamos a pergunta original
#     if content.upper() == "OK":
#         return question
#     # Se a resposta parece ser uma explicação (e não uma pergunta), usamos a original também
#     elif "?" not in content or len(content.split()) > 20:
#         return question
#     else:
#         return content
