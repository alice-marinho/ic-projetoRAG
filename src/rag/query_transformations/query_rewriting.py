from langchain.prompts import PromptTemplate
from config import llm_config
from llm import LLMClient  # certifique-se que o caminho está correto

# Instanciar seu cliente
llm_client = LLMClient()

# Template da reformulação de consulta
query_rewrite_template = """Você é um assistente de IA encarregado de reformular as consultas dos usuários para melhorar a recuperação em um sistema RAG.
Dada a consulta original, reescreva-a para que seja mais específica, detalhada e com maior probabilidade de recuperar informações relevantes.

- Retorne apenas a pergunta reescrita

Pergunta Original: "{original_query}"
Pergunta Expandida e Otimizada:"""

# Criar prompt com LangChain
query_rewrite_prompt = PromptTemplate(
    input_variables=["original_query"],
    template=query_rewrite_template
)

def rewrite_query(original_query: str) -> str:
    # Preencher o prompt com o texto original
    prompt = query_rewrite_prompt.format(original_query=original_query)
    # Usar o LLM para obter a resposta
    response = llm_client.chat(prompt)
    return response
