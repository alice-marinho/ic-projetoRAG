from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_together import ChatTogether
from together import Together
from backend.src.config.llm_config import LLM_MODEL, LLM_TEMPERATURE, LLM_PROVIDER, TOGETHER_API_KEY, GEMINI_API_KEY, GENAI_MODEL


class LLMClient:
    def __init__(self, temp = None):

        temperature = temp if temp is not None else LLM_TEMPERATURE

        if LLM_PROVIDER== "together":
            self.llm = ChatTogether(
                api_key = TOGETHER_API_KEY,
                model = LLM_MODEL,
                temperature = temperature
            )
            # self.client = Together(api_key=llm_config.TOGETHER_API_KEY)
            # self.model = llm_config.LLM_MODEL
            # self.temperature = llm_config.LLM_TEMPERATURE

        elif LLM_PROVIDER== "gemini":
            self.llm = ChatGoogleGenerativeAI(
                google_api_key= GEMINI_API_KEY,
                model= GENAI_MODEL,
                temperature= temperature,
                max_tokens=None,
                timeout=None,
                max_retries=5,
                convert_system_message_to_human=True
            )
        else:
            raise ValueError("Provedor de LLM não suportado.")

    def chat(self, prompt: str) -> str:
        # response = self.client.chat.completions.create(
        #     model=self.model,
        #     messages=[{"role": "user", "content": prompt}],
        #     temperature=self.temperature
        # )
        # content = response.choices[0].message.content.strip()
        # return content
        response = self.llm.invoke(prompt)
        return response.content.strip()

