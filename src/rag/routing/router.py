from typing import Union
from langchain_core.prompts import ChatPromptTemplate
from langchain_together import ChatTogether
from rag.routing.routing_models import BuscaSimples, BuscaComposta, Router

from config.llm_config import LLM_MODEL

prompt_roteador = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """Você é um assistente especialista em rotear perguntas de um usuário para um sistema de busca.
            Sua tarefa é analisar a pergunta e direcioná-la para a ferramenta correta: 'BuscaSimples' ou 'BuscaComposta'.

            - Use 'BuscaSimples' se a pergunta for sobre um único conceito ou disciplina.
            - Use 'BuscaComposta' se a pergunta pedir para unir, combinar ou comparar dois ou mais conceitos ou disciplinas.
    
            Apenas diga qual rota usar.
            """,
        ),
        ("human", "{question}"),
    ]
)

def get_router_decision(question: str) -> Union[BuscaSimples, BuscaComposta]:
    """
    Analisa a pergunta do usuário e decide qual rota de busca seguir.
    """
    llm = ChatTogether(
        model=LLM_MODEL,
        temperature=0
    )

    structured_llm = llm.with_structured_output(Router) # Modelo de retorno do Pydantic
    chain = prompt_roteador | structured_llm

    print(f"[INFO] Roteando a pergunta: '{question}'")

    # retorna uma instância de 'Router'
    router_result = chain.invoke({"question": question})

    return router_result.route

