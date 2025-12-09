from typing import Union

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from backend.src.rag.routing.models.search import BuscaSimples, BuscaComposta, Router
from backend.src.utils.logger import setup_logger

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
    
            Alerta!!! : Caso a pergunta tenha tom de continuidade/ seja uma pergunta complementar (aquela que 
            necessita de contexto anterior para responder) Coloque como BuscaSimples.
            
            Apenas diga qual rota usar.
            
            **Importante**: você deve responder **apenas em JSON** no seguinte formato:
            {{ "route": "<BuscaSimples | BuscaComposta>" }} e caso for BuscaComposta utilize o formato: 
            """,
        ),
        ("human", "{question}"),
    ]
)


def get_router_decision(question: str, llm_client) -> Union[BuscaSimples, BuscaComposta]:
    """
    Analisa a pergunta do usuário e decide qual rota de busca seguir.
    """

    logger = setup_logger(__name__)

    parser = PydanticOutputParser(pydantic_object=Router)
    chain = prompt_roteador | llm_client | parser

    logger.info("\n[INFO] Roteando a pergunta\n")

    # retorna uma instância de 'Router'
    router_result = chain.invoke({"question": question})

    return router_result.route

