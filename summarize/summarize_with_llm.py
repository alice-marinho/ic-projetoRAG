from llm import client
from together import Together

from llm.client import LLMClient

llm_client = LLMClient()

def summarize_question(question):
    prompt = (f"reescreva a frase somente as palavras chaves de forma objetiva para facilitar uma pesquisa semântica."
              f"Exemplo: pergunta: Quais são matérias que ensinam biologia? || palavras: matérias ensine biologia "
              f"\n\n{question}")

    messages = [{"role": "user", "content": prompt}]
    return llm_client.chat(messages)
