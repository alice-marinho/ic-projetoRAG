from llm import client, LLMClient


def generate_response(question, context, history):
    final_context = "\n\n".join(context)

    conversation_history = ""
    for troca in history:
        conversation_history += f"Usuário: {troca['pergunta']}\n"
        conversation_history += f"IA: {troca['resposta']}\n"

    prompt = f"""
    Você é uma inteligência artificial que responde perguntas estritamente com base no contexto abaixo.

    ================ CONTEXTO =================
    {final_context}
    ===========================================

    Instruções:
    - Responda sempre em Português - BR
    - Se o contexto incluir uma lista de tópicos ou conteúdos que claramente pertencem a uma disciplina (mesmo que o nome da disciplina não esteja explícito), associe-os ao nome da disciplina mencionada na pergunta.
    - Associe temas da pergunta ao conteúdo programático das disciplinas descritas.
    - Responda à pergunta abaixo usando somente o conteúdo do CONTEXTO.
    - Se o conteúdo da resposta estiver claramente no CONTEXTO, apresente a resposta diretamente.
    - Se a informação **não** estiver no CONTEXTO, diga: "A informação não está disponível nos arquivos analisados."
    - Sempre estruture a resposta da maneira mais visual possível.
    Histórico da conversa (para contexto):
    {conversation_history}

    Pergunta: {question}
"""

    llm_client = LLMClient()
    content = llm_client.chat(prompt)
    return content