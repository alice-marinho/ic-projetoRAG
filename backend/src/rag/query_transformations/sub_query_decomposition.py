from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

from backend.src.rag.routing.models.search import BuscaComposta

prompt_sub_query = ChatPromptTemplate.from_messages([
    (
        "system",
        """Você é um assistente de decomposição de perguntas complexas.
        Sua tarefa é transformar uma questão ampla em até 5 sub-queries objetivas e diretas.
        
        Regras importantes:
        - Cada sub-query deve explorar um aspecto / tópico da pergunta.
        - As sub-queries não podem ser redundantes e não podem reescrever a pergunta.
        - Evite generalidades: seja específico ao relacionar os conceitos.
        - Não é necessário pegar todas as informações que contém na pergunta, porém pegue aquilo que auxiliará na resposta

        Exemplo:
        Pergunta: "Crie uma prova de 'IA' e 'Ética' com 10 questões."
        Sub-queries:
        - "Qual é o conteúdo da disciplina de Inteligência Artificial?"
        - "Quais é o conteúdo da disciplina de 'Ética'?"

        Gere as sub-queries como uma lista.
        """,
    ),
    ("human", "{question}"),
])

def get_sub_queries(question: str, llm) -> dict | BaseModel:
    """
    :param llm: llm utilizada
    :param question: Pergunta do usuário
    :return: Uma lista de mini perguntas
    """

    structured_llm = llm.with_structured_output(BuscaComposta)
    chain = prompt_sub_query | structured_llm

    return chain.invoke({"question": question})