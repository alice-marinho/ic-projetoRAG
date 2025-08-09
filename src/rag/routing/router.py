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

            Sua tarefa é analisar cuidadosamente a pergunta e decidir qual tipo de busca usar:
            
            - Use **BuscaSimples** se a pergunta for sobre um único conceito, disciplina ou tema.  
              Exemplos:  
              - "Qual é a ementa da disciplina 'Algoritmos'?"  
              - "Qual é o conteúdo programático de 'História da Ciência e da Tecnologia' para o curso de ADS?"
            
            - Use **BuscaComposta** se a pergunta envolver a combinação, comparação, ou múltiplos conceitos ou disciplinas.  
              Exemplos:  
              - "Qual a diferença entre 'Língua Portuguesa 1' e 'Matemática 1'?"  
              - "Crie um projeto que una 'Programação' e 'Marketing'."  
              - "Quais são as competências de 'História' e 'Geografia' para o ensino médio?"
    
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

    # --- Heurística antes do LLM ---
    heuristicas_composta = [
        " e ",
        " e/ou ",
        "comparar",
        "diferença entre",
        "comparação",
        "vs",
        "versus"
    ]

    if any(h in question.lower() for h in heuristicas_composta):
        print("[INFO] Heurística detectou pergunta composta.")
        return BuscaComposta(sub_queries=[])

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

