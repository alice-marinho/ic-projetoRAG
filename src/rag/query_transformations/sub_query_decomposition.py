from typing import List

from langchain_core.prompts import ChatPromptTemplate
from langchain_together import ChatTogether

from config.llm_config import LLM_MODEL
from rag.routing.routing_models import BuscaComposta

prompt_sub_query = ChatPromptTemplate.from_messages([
    (
        "system",
        """Você é um assistente de decomposição de perguntas complexas.
        Dada uma pergunta que envolve múltiplos temas, gere sub-queries independentes
        que possam ser buscadas separadamente.

        Exemplo:
        Pergunta: "Crie um projeto que una os temas de 'IA' e 'Ética'."
        Sub-queries:
        - "Qual é o conteúdo da disciplina de Inteligência Artificial?"
        - "Quais são as informações sobre o tema 'Ética'?"

        Gere as sub-queries como uma lista.
        """,
    ),
    ("human", "{question}"),
])

def get_sub_queries(question: str) -> List[str]:
    """
    :param question: Pergunta do usuário
    :return: Uma lista de mini perguntas
    """

    llm = ChatTogether(
        model=LLM_MODEL,
        temperature=0
    )

    structured_llm = llm.with_structured_output(BuscaComposta)
    chain = prompt_sub_query | structured_llm

    return chain.invoke({"question": question})