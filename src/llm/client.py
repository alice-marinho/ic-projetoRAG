from together import Together
from config import llm_config

class LLMClient:
    def __init__(self):
        self.client = Together(api_key=llm_config.LLM_API_KEY)
        self.model = llm_config.LLM_MODEL
        self.temperature = llm_config.LLM_TEMPERATURE

    def chat(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
        )
        content = response.choices[0].message.content.strip()
        return content
