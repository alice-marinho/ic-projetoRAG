import os
from dotenv import load_dotenv
from together import Together

load_dotenv()  # Isso garante que TOGETHER_API_KEY seja carregada neste módulo

class LLMClient:
    def __init__(self, model="mistralai/Mixtral-8x7B-Instruct-v0.1"):
        self.client = Together(api_key=os.getenv("TOGETHER_API_KEY"))
        self.client.api_base = "https://api.together.xyz/v1"
        self.model = model

    def chat(self, prompt):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Você responde com base apenas no contexto fornecido."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()