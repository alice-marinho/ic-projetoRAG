from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

from rag.routing.models.search import BuscaComposta

prompt_sub_query = ChatPromptTemplate.from_messages([
    (
        "system",
        """Você é um assistente de decomposição de perguntas complexas.
        Sua tarefa é transformar uma questão ampla em 3 a 5 sub-queries independentes, 
        claras e objetivas, que possam ser buscadas separadamente e que juntas ajudem 
        a compor uma resposta completa à pergunta original.
        
        Regras importantes:
        - Cada sub-query deve explorar um aspecto / tópico da pergunta.
        - As sub-queries não podem ser redundantes e não podem reescrever a pergunta.
        - Cada sub-query deve ser autoexplicativa e poder ser entendida isoladamente.
        - Evite generalidades: seja específico ao relacionar os conceitos.
        - Não é necessário pegar todas as informações que contém na pergunta, porém pegue aquilo que auxiliará na resposta

        Exemplo:
        Pergunta: "Crie uma prova de 'IA' e 'Ética' com 10 questões."
        Sub-queries:
        - "Qual é o conteúdo da disciplina de Inteligência Artificial?"
        - "Quais são as informações sobre o tema 'Ética'?"
        - "Qual conteúdo da máteria de Ética?

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