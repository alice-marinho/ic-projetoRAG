from data_manager import DocsHashChecker
from config.config import CHROMA_DIR
from ingestion import *
from ingestion.cleanner import TextCleaner
from llm import LLMClient
from rag import ConversationManager, RAGRetriever
from rag.agents import RetrievalDecisionAgent
#from rag.chat.conversation_history import MemoryManager
# from rag.generator import show_history, get_session_history
from rag.query_transformations.sub_query_decomposition import get_sub_queries
from rag.routing.router import get_router_decision
from rag.routing.models.search import BuscaSimples
from utils.data_processing import processing_data
from utils.logger import setup_logger
from vectorstore import VectorStoreManager
from vectorstore.mongo_db import MongoDocstore
from rag.chat.conversation_history import SessionManager  # <--- Adiciona isso



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
        # need_retrieval = self.decision_agent.needs_retrieval(question, session_id)

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

        try:
            final_context = self.retriever.retriever_final_context(question)
        except Exception as e:
            self.logger.error(f"Falha direta no retriever_final_context: {e}")
            final_context = []

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
            context=final_context_str,
            session_id=session_id,
            cache_context= cache_context_str)

    def generate_answer(self, question: str, context_chunks, session_id: str, user_id: str):
        """
        Gera uma resposta diretamente a partir de chunks fornecidos manualmente (sem retriever).
        Usado para o caso do formulário interdisciplinar.
        """
        user_sessions = self.session_history.list_sessions(user_id)
        if session_id not in user_sessions:
            self.logger.error(
                f"PERMISSÃO NEGADA: Usuário {user_id} tentou acessar sessão {session_id} que não lhe pertence."
            )
            return "Erro: Você não tem permissão para acessar esta sessão."

        if not context_chunks:
            self.logger.warning("Nenhum chunk fornecido manualmente para gerar resposta.")
            return "Desculpe, não há conteúdo disponível para gerar uma resposta."

        # Log e cache de contexto
        self.logger.info(f"Gerando resposta interdisciplinar com {len(context_chunks)} chunks fornecidos.")

        final_context_str = []
        self.context_cache = []

        # Primeiro, verifica se o que recebemos é uma lista
        if not isinstance(context_chunks, list):
            self.logger.warning("context_chunks não é uma lista. Tratando como string única.")
            final_context_str = [str(context_chunks)]
            self.context_cache = [{"page_content": str(context_chunks)}]

        elif context_chunks:  # Se a lista não estiver vazia

            if isinstance(context_chunks[0], str):
                # --- Caso 1: É uma lista de strings [str, str, ...] ---
                self.logger.info("context_chunks é uma lista de strings.")
                final_context_str = context_chunks
                self.context_cache = [{"page_content": chunk} for chunk in context_chunks]

            elif isinstance(context_chunks[0], dict):
                # --- Caso 2: É uma lista de dicionários [dict, dict, ...] ---
                self.logger.info("context_chunks é uma lista de dicionários.")
                self.context_cache = context_chunks  # O cache é a lista de dicts original

                # Constrói a lista de strings com segurança
                for chunk_dict in context_chunks:

                    # --- A CORREÇÃO PRINCIPAL ESTÁ AQUI ---
                    if "page_content" in chunk_dict:
                        final_context_str.append(chunk_dict["page_content"])
                    elif "content" in chunk_dict:  # Fallback
                        final_context_str.append(chunk_dict["content"])
                    else:
                        self.logger.warning(
                            f"Dicionário no chunk não tem 'page_content' ou 'content': {list(chunk_dict.keys())}")

            else:
                self.logger.error(f"Formato de context_chunks inesperado: {type(context_chunks[0])}")
        cache_context_str = []
        if isinstance(self.context_cache, list) and self.context_cache:
            for chunk_dict in self.context_cache:
                if "page_content" in chunk_dict:
                    cache_context_str.append(chunk_dict["page_content"])
                elif "content" in chunk_dict:
                    cache_context_str.append(chunk_dict["content"])
        if not final_context_str:
            self.logger.error("Falha ao processar context_chunks. Contexto final está vazio.")
            return "Erro: Não consegui processar os documentos selecionados."

        # Gera a resposta diretamente
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