import os

from dotenv import load_dotenv

load_dotenv()

# Variáveis de configuração
LLM_API_KEY = os.getenv("TOGETHER_API_KEY")
# LLM_MODEL = os.getenv("LLM_MODEL", "mistralai/Mixtral-8x7B-Instruct-v0.1")
LLM_MODEL = os.getenv("LLM_MODEL", "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbometa-llama/Meta-Llama-3.1-8B-Instruct-Turbo")  # valor padrão opcional
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", 0.0))  # garante que seja float
