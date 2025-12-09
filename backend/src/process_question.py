from backend.src.llm import LLMClient
from backend.src.rag import ConversationManager, RAGRetriever
from backend.src.rag.agents import RetrievalDecisionAgent
from backend.src.utils.data_processing import processing_data
from backend.src.utils.logger import setup_logger

from backend.src.rag.chat.conversation_history import SessionManager



class ProcessQuestion:
    # def __init__(self, session):
    def __init__(self):
        self.llm_client = LLMClient().llm
        self.context_cache = []

        # self.session_id = session
        # self.session_history = SessionManager().get_session(session_id=self.session_id)
        self.session_history = SessionManager()

        # self.response_manager = ConversationManager(self.session_id)
        self.retriever = RAGRetriever()
        self.response_manager = ConversationManager()
        self.decision_agent = RetrievalDecisionAgent()
        self.logger = setup_logger(__name__)
        # self.session_id = session_id
        pass


    # Recuperação
    def process_user_question(self, question: str, session_id, user_id):
        """
        Orquestra o fluxo completo, começando pela verificação/roteamento.
        :param session_id:
        :param question = Pergunta do usuário
        :param conversation_history = Histórico da conversa do usuário
        """
        user_sessions = self.session_history.list_sessions(user_id)
        if session_id not in user_sessions:
            self.logger.error(
                f"PERMISSÃO NEGADA: Usuário {user_id} tentou acessar sessão {session_id} que não lhe pertence.")
            return "Erro: Você não tem permissão para acessar esta sessão."
        final_context = []
        need_retrieval = self.decision_agent.needs_retrieval(question, session_id)

        # if need_retrieval:
        #     self.logger.info("Decisão: Recuperação de contexto é necessária.")
        #     decisao = get_router_decision(question,self.llm_client)
        #
        #
        #     # print(final_context)
        #
        #     if decisao == 'BuscaSimples':
        #         busca_obj = BuscaSimples(query=question) # Aqui ele verifica se está conforme o modelo PyDantic
        #         self.logger.info(f"Rota decidida: Busca Simples. Query: '{busca_obj.query}'")
        #         final_context = self.retriever.retriever_final_context(busca_obj.query)
        #
        #     elif decisao == 'BuscaComposta':
        #         busca_obj = get_sub_queries(question, self.llm_client)
        #         # print(f"Tipo retornado por get_sub_queries: {type(busca_obj)}")
        #         # print(f"Conteúdo retornado: {busca_obj}")
        #
        #         self.logger.info(f"\n\nRota decidida: Busca Composta. Sub-Queries: {busca_obj}\n\n")
        #         docs_combinados = {}
        #         for sub_query in busca_obj.sub_queries:
        #             individual_contexts = self.retriever.retriever_final_context(sub_query)
        #             print(f"\n\nSub-query: {sub_query} -> {len(individual_contexts)} chunks encontrados\n\n")
        #             for doc in individual_contexts:
        #                 docs_combinados[doc.page_content] = doc
        #
        #         final_context = list(docs_combinados.values())
        #     self.context_cache = final_context
        #             # time.sleep(20)
        #             # contextos = list({doc.page_content: doc for doc in final_context}.values())
        #             # print(contextos)
        # else:
        #     self.logger.info("Decisão: Recuperação não é necessária. Usando cache de contexto.")
        #     final_context = self.context_cache

        if need_retrieval:
            try:
                final_context = self.retriever.retriever_final_context(question)
            except Exception as e:
                self.logger.error(f"Falha direta no retriever_final_context: {e}")
                final_context = []
        else:
            self.logger.info("Decisão: Recuperação não é necessária. Usando cache de contexto.")
            final_context = self.context_cache

        self.context_cache = final_context

        if not final_context:
            self.logger.warning("Nenhum contexto encontrado para gerar a resposta")
            return "Desculpe, não encontrei contexto para responder."

        final_context_str = [doc.page_content for doc in final_context]
        cache_context_str= [doc.page_content for doc in self.context_cache] if self.context_cache else []
        #
        #
        return self.response_manager.generate_response(
            question,
            context=final_context,
            session_id=session_id,
            cache_context= cache_context_str)


    def generate_answer(self, question: str, context_chunks, session_id: str, user_id: str):
        """
        Gera uma resposta diretamente a partir de chunks fornecidos manualmente (do banco).
        """
        user_sessions = self.session_history.list_sessions(user_id)
        if session_id not in user_sessions:
            self.logger.error(
                f"PERMISSÃO NEGADA: Usuário {user_id} tentou acessar sessão {session_id} que não lhe pertence."
            )
            return "Erro: Você não tem permissão para acessar esta sessão."

        if not context_chunks:
            self.logger.warning("Nenhum chunk fixo encontrado para gerar resposta.")
            return "Desculpe, não há conteúdo disponível para gerar uma resposta."

        self.logger.info(f"Gerando resposta interdisciplinar com {len(context_chunks)} chunks fixos.")
        final_context_str = []
        try:
            for chunk in context_chunks:
                if "page_content" in chunk:
                    final_context_str.append(chunk["page_content"])
                elif "content" in chunk:
                    final_context_str.append(chunk["content"])
                else:
                    self.logger.warning(f"Chunk no modo formulário não tem 'page_content': {chunk.keys()}")

            cache_context_str = final_context_str

            if not final_context_str:
                self.logger.error("Falha ao processar context_chunks, lista de strings vazia.")
                return "Erro: Falha ao ler os documentos da sessão."

        except TypeError:
            self.logger.error("Erro de tipo no generate_answer. Esperava list[dict].")
            return "Erro: Formato de dados inesperado na sessão."

        response = self.response_manager.generate_response(
            question=question,
            context=final_context_str,
            session_id=session_id,
            cache_context=cache_context_str
        )

        return response

def chat_loop(session, question_process):

    while True:
        question = input("Pergunte sobre (ou sair): ")
        if question.lower() == "sair":
            break
        if not question.strip():
            print("Digite uma pergunta válida.")
            continue
        answer = question_process.process_user_question(question,session)
        print(f"\nResposta da IA:\n{answer}\n")


def main():
    question_process = ProcessQuestion()
    reload = input("Deseja refazer o banco de dados? s/n\n")
    processing_data(reload)
    # conversation_history = []
    session_manager = SessionManager()


    while True:
        print("\n=== Menu de Sessões ===")
        print("1. Criar nova sessão")
        print("2. Continuar sessão existente")
        print("3. Listar sessões")
        print("4. Sair")
        opcao = input("Escolha: ")

        if opcao == "1":
            name = input("Digite um nome para a nova sessão: ")
            session_id = session_manager.create_session(name)
            session = session_manager.get_session(session_id)
            print(f"Nova sessão criada: {name} (id={session_id})")
            chat_loop(session, question_process)


        elif opcao == "2":
            sessions = session_manager.list_sessions()
            if not sessions:
                print("Nenhuma sessão existente. Crie uma nova primeiro.")
                continue

            print("\nSessões disponíveis:")
            for sid, name in sessions.items():
                print(f"{sid}: {name}")

            session_id = input("Digite o ID da sessão que deseja continuar: ")
            if session_id not in sessions:
                print("ID inválido.")
                continue
            session = session_manager.get_session(session_id)
            chat_loop(session, question_process)


        elif opcao == "3":
            sessions = session_manager.list_sessions()
            if not sessions:
                print("Nenhuma sessão criada ainda.")
            else:
                print("\nSessões existentes:")
                for sid, name in sessions.items():
                    print(f"{sid}: {name}")
            continue

        elif opcao == "4":
            print("Saindo...")
            break

        else:
            print("Opção inválida.")
            continue


        # while True:
        #     question = input("Pergunte sobre (ou sair): ")
        #     if question.lower() == "sair":
        #         break
        #     if not question.strip():
        #         print("Digite uma pergunta válida.")
        #         continue
        #     # answer = orquestrar_resposta(question, conversation_history)
        #     # question = rewrite_query(question)
        #     answer = question_process.process_user_question(question, session)
        #
        #     # show_history()
        #
        #     print(f"\nResposta da IA:\n{answer}\n")

if __name__ == "__main__":
    main()