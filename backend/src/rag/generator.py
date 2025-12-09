from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.output_parsers.string import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts.chat import MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory


from backend.src.llm import LLMClient
from backend.src.rag.chat.conversation_history import SessionManager
from backend.src.utils.logger import setup_logger


class ConversationManager:
    """Gerencia o estado e a lógica da conversa, unindo LLM, prompt e histórico."""


    def __init__(self):
        self.logger = setup_logger(__name__)
        self.llm_client =  LLMClient(0.7).llm

        self.session_mng = SessionManager()
        _system_prompt = """Você é um assistente acadêmico especializado em interdisciplinaridade e integração de conhecimentos.
        Seu objetivo é criar respostas, explicações e materiais educacionais que conectem diferentes áreas do saber de forma clara,
        coerente e contextualizada.
       
        Todas as respostas devem ser baseadas estritamente no contexto fornecido, mantendo precisão conceitual e rigor acadêmico.

        Quando solicitado, você também pode responder diretamente sobre conteúdos específicos das disciplinas mencionadas no documento, 
        sempre buscando evidenciar suas relações com outras áreas quando possível.

        Use uma linguagem didática, acessível e organizada, adequada para professores e estudantes.

        Se o contexto não fornecer informação suficiente, explique isso explicitamente antes de tentar complementar com inferências baseadas em conhecimento geral.

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
                    Atividades e Interdisciplinaridade:
                    5.  Utilize a criatividade para geração das atividades solicitadas pelo usuário, para interligar 
                    os conteúdos que contenham nos planos de aula.
                    6. De sempre respostas estruturadas e completas, quando for solicitado atividade interdisciplinar faça algo robusto e completo, de atividade, prova ou o que for, já mastigada para que não seja necessário que o professor planeje e sim tenha em mão.
                    
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

        # final_context = "\n\n".join(context)
        # cache_context_str = "\n\n".join(cache_context)

        response = self.chain_with_history.invoke(
            {
                "final_context": context,
                "cache_context": cache_context,
                "question": question
                # "history": self.get_session()
            },
            config={"configurable": {"session_id": session_id}}
        )
        return response

