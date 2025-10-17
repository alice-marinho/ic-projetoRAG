from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.output_parsers.string import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts.chat import MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory


from llm import LLMClient
from rag.chat.conversation_history import SessionManager


class ConversationManager:
    """Gerencia o estado e a lógica da conversa, unindo LLM, prompt e histórico."""


    def __init__(self):
        self.llm_client =  LLMClient(0.7).llm

        self.session_mng = SessionManager()
        _system_prompt = """Você é um assistente acadêmico especialista em interdisciplinaridade. 
                    Seu objetivo principal é criar respostas e materiais educacionais de uma forma interdisciplinar. 
                    O conteúdo será baseados estritamente no contexto fornecido.
                    Porém, você também responde as informações perguntadas diretamente sobre as matérias do documento.

                    ============= CONTEXTO NOVO =================
                    {final_context}
                    ===========================================
                    
                    ================ CONTEXTO ARMAZENADO =================
                    {cache_context}
                    ===========================================
                    
                    Sempre, na resposta, insira o código das máterias para o que foi usado para resposta.

                    REGRAS E DIRETRIZES:            

                    1.  **Fonte Única de Verdade:** Responda à pergunta usando EXCLUSIVAMENTE o conteúdo do CONTEXTO. Não adicione informações externas.
                    2.  **Tratamento de Informação Ausente:** Se a informação necessária para responder à pergunta NÃO estiver no CONTEXTO, responda de forma clara e direta: "A informação não está disponível nos arquivos analisados."
                    3.  **Linguagem:** Todas as respostas devem ser em Português do Brasil.
                    4.  **Estrutura e Formatação:** Utilize formatação Markdown para estruturar a resposta de maneira clara e visualmente agradável. Quando necessário, coloque enunciados mais elaborados, estruture de uma forma completa.
                    5.  **Análise Interdisciplinar:** Ao receber a pergunta, identifique os temas e associe-os ao conteúdo programático das disciplinas descritas no contexto, mesmo que o nome da disciplina não esteja explícito.
                        5.1 **Informações dos Planos de Aula **Além disso, você também responde perguntas relacionadas 
                        aos PPCs, como detalhes das ementas, horário, e entre outras informações contidas nos Planos de Aulas.
                    6.  Utilize a criatividade para geração das atividades solicitadas pelo usuário, para interligar 
                    os conteúdos que contenham nos planos de aula.
                    
                    O foco PRINCIPAL da ferramenta é gerar interdisciplinaridade entre os conteúdos, verifique quais 
                    conteúdos podem ser relacionados para entregar uma boa resposta interdisciplinar.
                    
                    
                    [Não passe isso para usuário] Sempre complemente com coisas a mais que o usuário pedir. Após a interação, 
                    pergunte se quer fazer algo a mais que esteja relacionado a conversa para ter um fluxo de conversa.                    
                    """

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", _system_prompt),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{question}")])


        self.chain = (
            self.prompt
            | self.llm_client
            | StrOutputParser() # Pega a resp final como str
        )

        # self.get_session = SessionManager().get_session(history)

        self.chain_with_history = RunnableWithMessageHistory(
            self.chain,
            get_session_history=self.session_mng.get_session,
            input_messages_key="question",
            history_messages_key="history",
            output_messages_key="output"
        )


    def generate_response(self, question, context, session_id, cache_context):
        final_context = "\n\n".join(context)
        cache_context_str = "\n\n".join(cache_context) if cache_context else ""


        response = self.chain_with_history.invoke(
            {
                "final_context": final_context,
                "cache_context": cache_context,
                "question": question
                # "history": self.get_session()
            },
            config={"configurable": {"session_id": session_id}}
        )

        # print(store)

        return response




# from langchain_community.chat_message_histories import ChatMessageHistory
#
# def get_session_history(session_id: str)-> BaseChatMessageHistory:
#     store = {}
#     if session_id not in store:
#         store[session_id] = ChatMessageHistory()
#     return store[session_id]


# def show_history(session_id):
#     if session_id not in store:
#         print("Nenhuma conversa para este session_id.")
#         return
#
#     history = store[session_id].messages
#     print(f"--- Histórico de conversa (session_id={session_id}) ---")
#     for i, msg in enumerate(history):
#         role = msg.type  # 'human' ou 'ai'
#         print(f"{i+1}. [{role}] {msg.content}")
#     print("---------------------------------------------")