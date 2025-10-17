from pydantic import BaseModel, Field
from typing import List, Union

class BuscaSimples(BaseModel):
    """ Rota para perguntas sobre um único tópico, disciplina ou conceito."""
    query: str = Field(description="A pergunta do usuário otimizada para uma única busca semântica.")

class BuscaComposta(BaseModel):
    """ Rota para perguntas que pedem para unir, comparar ou relacionar múltiplos tópicos."""
    sub_queries: List[str] = Field(
        description="Uma lista de perguntas autônomas, uma para cada tópico a ser buscado separadamente."
    )

class Router(BaseModel):
    """ Decide qual rota seguir (simples ou composta) com base na pergunta do usuário. O campo 'route' conterá a
    decisão final. """
    route: str = Field(..., description="A decisão de roteamento tomada com base na pergunta do usuário.")
