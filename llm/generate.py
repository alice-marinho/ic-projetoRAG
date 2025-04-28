from main import client


def generate_response(question, context):
    final_context = "\n\n".join(context)
    prompt = f"""
    Você é uma inteligência artificial especializada em auxiliar no contexto educacional.

    Sua base de dados principal será essa: {final_context}

    Sua função é:
    - Responder perguntas sobre conteúdos, disciplinas, materiais didáticos e temas educacionais.
    - Sugerir ideias, conteúdos e abordagens para projetos acadêmicos, se aplicável.

    Regras:
    - Use apenas o plano de aula como base principal de informações.
    - Só adicione informações externas se forem altamente relevantes para educação ou projetos.
    - Utilize linguagem clara, acessível e mantenha coerência no diálogo.
    - Nunca responda perguntas fora do contexto educacional.
    - Se a pergunta for confusa ou fora do escopo, responda: "Pode explicar novamente?"

    Pergunta: {question}
    Resposta:
    """

    response = client.chat.completions.create(
        model="mistralai/Mixtral-8x7B-Instruct-v0.1",
        messages=[
            {"role": "system", "content": "Você responde com base apenas no contexto fornecido."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
    )

    return response.choices[0].message.content.strip()