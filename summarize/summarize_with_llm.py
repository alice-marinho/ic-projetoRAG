from main import client


def summarize_question(question):
    prompt = (f"reescreva a frase somente as palavras chaves de forma objetiva para facilitar uma pesquisa semântica."
              f"Exemplo: pergunta: Quais são matérias que ensinam biologia? || palavras: matérias ensine biologia "
              f"\n\n{question}")

    response = client.chat.completions.create(
        model="mistralai/Mixtral-8x7B-Instruct-v0.1",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )

    summarized_question = response.choices[0].message.content.strip()
    return summarized_question
