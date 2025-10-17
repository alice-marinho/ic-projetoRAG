from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from llm import LLMClient
from utils.logger import setup_logger


class RetrievalDecisionAgent:
    """
    Decide se é necessário usar o retriever com base na pergunta atual e no histórico.
    """

    def __init__(self, temperature=0.0):
        self.llm = LLMClient(temperature).llm
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """
                Você é um agente de roteamento de perguntas em um sistema RAG.
                Sua função é decidir se é necessário buscar novos contextos no banco vetorial.

                Decida com base nas instruções abaixo:
                - Se caso for um simples comprimento, uma despedida, responda com "NO"
                - Se a pergunta for claramente uma continuação, como "refaça", "melhore", "explique melhor",
                  "dê mais exemplos" ou perguntas que façam referência à última resposta,
                  então responda apenas com "NO".
                - Se for uma nova pergunta ou um novo tema, responda "YES".
                - Responda APENAS com "YES" ou "NO".
            """),
            ("human", "Histórico: {history}\nPergunta: {question}")
        ])
        self.chain = self.prompt | self.llm | StrOutputParser()

    def needs_retrieval(self, question: str, history) -> bool:
        """Retorna True se for necessário buscar novos contextos."""
        decision = self.chain.invoke({"question": question, "history": history}).strip().upper()
        logger = setup_logger(__name__)
        logger.info(f"\n\nDecisão: {decision}\n\n")
        return decision == "YES"
