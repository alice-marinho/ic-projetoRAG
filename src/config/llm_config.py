import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
load_dotenv()

# Variáveis de configuração
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
# LLM_MODEL = os.getenv("LLM_MODEL", "mistralai/Mixtral-8x7B-Instruct-v0.1")
LLM_MODEL = os.getenv("LLM_MODEL", "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbometa-llama/Meta-Llama-3.1-8B-Instruct-Turbo")  # valor padrão opcional
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", 0.0))  # garante que seja float
# RERANKER_API_KEY = os.getenv("JINA_API_KEY")
RERANKER_API_KEY = os.getenv("COHERE_API_KEY")
COHERE_MODEL = "rerank-multilingual-v3.0"

LLM_PROVIDER="gemini"
GEMINI_API_KEY= os.getenv("GEMINI_API_KEY")
GENAI_MODEL= 'gemini-2.0-flash'