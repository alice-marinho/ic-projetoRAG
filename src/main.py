from data_manager import DocsHashChecker
from config.config import CHROMA_DIR
from ingestion import *
from ingestion.cleanner import TextCleaner
from llm import LLMClient
from rag import ConversationManager
from rag.agents import RetrievalDecisionAgent
#from rag.chat.conversation_history import MemoryManager
# from rag.generator import show_history, get_session_history
from rag.query_transformations.sub_query_decomposition import get_sub_queries
from rag.retriever import retrieve_final_context
from rag.routing.router import get_router_decision
from rag.routing.models.search import BuscaSimples
from utils.logger import setup_logger
from vectorstore import VectorStoreManager
from vectorstore.mongo_db import MongoDocstore
from rag.chat.conversation_history import SessionManager  # <--- Adiciona isso


def processing_data(reload):

    logger = setup_logger(__name__)

    # reload = input("Deseja refazer o banco de dados? s/n\n")
    if reload == "s":
        print("===")

    # Execute antes de reindexar
    #if not os.path.exists(CHROMA_DIR):
        logger.info(f"Diretório '{CHROMA_DIR}' não encontrado. Iniciando recriação total...")
        vs_manager = VectorStoreManager()
        mongo_manager = MongoDocstore()

        vs_manager.clean_storage()
        mongo_manager.clear()

        VectorStoreManager._instances = {}  # Limpa a instância Singleton
        vs_manager = VectorStoreManager()
        hash_checker = DocsHashChecker()
        dt_extractor = DocsExtractor()
        todos_os_docs = load_documents()
        if not todos_os_docs:
            logger.warning("Nenhum documento encontrado para processar. Encerrando.")
            return

        logger.info(f"Processando todos os {len(todos_os_docs)} documentos carregados...")

        docs_agrupados = {}
        for doc in todos_os_docs:
            source_file = doc.metadata["source"]
            if source_file not in docs_agrupados:
                docs_agrupados[source_file] = ""
            docs_agrupados[source_file] += doc.page_content + "\n"

        dados_extraidos_completos = []
        for source_file, full_text in docs_agrupados.items():
            try:
                extracted_data = dt_extractor.extract_fields(full_text)
                if isinstance(extracted_data, list):
                    for item in extracted_data:
                        item["original_source_pdf"] = source_file
                        dados_extraidos_completos.append(item)
            except Exception as e:
                logger.error(f"Falha na extração para {source_file} durante o rebuild: {e}")

        dados_limpos = TextCleaner.clean_save_json(dados_extraidos_completos)

        vs_manager.organize_disciplines(dados_limpos)

        # Salva o estado atual dos hashes para futuras comparações
        hash_checker.save_current_hashes()
        logger.info("Recriação total concluída. Banco vetorial e arquivo de hash criados.")

        ### Verificações do banco já existente ###
    else:
        logger.info("Banco vetorial encontrado. Verificando por mudanças nos documentos...")

        vs_manager = VectorStoreManager()
        hash_checker = DocsHashChecker()
        dt_extractor = DocsExtractor()
        changes = hash_checker.get_changes()

        if not any(changes.values()):
            logger.info("Nenhuma mudança detectada. O banco de dados está atualizado.")
            vs_manager.load_vectorstore()
            return

        logger.info(
            f"Mudanças detectadas: {len(changes['added'])} adicionados, {len(changes['removed'])} removidos, {len(changes['modified'])} modificados.")
        store = vs_manager.load_vectorstore()

        files_to_remove = changes['removed'] + changes['modified']
        if files_to_remove:
            logger.info(f"Removendo dados antigos de {len(files_to_remove)} arquivo(s)...")
            for filename in files_to_remove:
                store.delete(where={"source": filename})
            logger.info("Dados antigos removidos com sucesso.")

        files_to_process = changes['added'] + changes['modified']
        if files_to_process:
            logger.info(f"Processando {len(files_to_process)} arquivo(s) novos/modificados...")

            docs_a_processar = load_documents()

            if docs_a_processar:
                logger.info(f"Processando {len(docs_a_processar)} documentos novos/modificados...")

                docs_agrupados = {}
                for doc in docs_a_processar:
                    source_file = doc.metadata["source"]
                    if source_file not in docs_agrupados:
                        docs_agrupados[source_file] = ""
                    docs_agrupados[source_file] += doc.page_content + "\n"

                novos_dados_extraidos = []
                for source_file, full_text in docs_agrupados.items():
                    try:
                        extracted_data = dt_extractor.extract_fields(full_text)
                        if isinstance(extracted_data, list):
                            for item in extracted_data:
                                item["original_source_pdf"] = source_file
                                novos_dados_extraidos.append(item)
                    except Exception as e:
                        logger.error(f"Falha na extração para {source_file} durante o refresh: {e}")

                # c. Limpar dados
                novos_dados_limpos = TextCleaner.clean_save_json(novos_dados_extraidos)

                # d. Dividir em chunks
                novos_chunks = split_json(novos_dados_limpos)

                store.add_documents(novos_chunks)
                logger.info("Novos dados adicionados ao banco vetorial.")
            else:
                logger.warning("Nenhum conteúdo válido encontrado nos novos arquivos para processar.")

        # Atualiza o arquivo de hash para o novo estado
        hash_checker.save_current_hashes()
        logger.info("Refresh inteligente concluído. Arquivo de hash atualizado.")


class ProcessQuestion:
    # def __init__(self, session):
    def __init__(self):
        self.llm_client = LLMClient().llm
        self.context_cache = []

        # self.session_id = session
        # self.session_history = SessionManager().get_session(session_id=self.session_id)
        self.session_history = SessionManager()

        # self.response_manager = ConversationManager(self.session_id)
        self.response_manager = ConversationManager()
        self.decision_agent = RetrievalDecisionAgent()
        # self.session_id = session_id
        pass


    # Recuperação
    def process_user_question(self, question: str, session_id):
        """
        Orquestra o fluxo completo, começando pela verificação/roteamento.
        :param question = Pergunta do usuário
        :param conversation_history = Histórico da conversa do usuário
        """

        final_context = []

        # history_text = "\n".join([msg.content for msg in self.session_history.messages])
        # need_retrieval = self.decision_agent.needs_retrieval(question, history_text)
        need_retrieval = self.decision_agent.needs_retrieval(question, session_id)

        if need_retrieval:
            decisao = get_router_decision(question,self.llm_client)


            # print(final_context)

            if decisao == 'BuscaSimples':
                busca_obj = BuscaSimples(query=question) # Aqui ele verifica se está conforme o modelo PyDantic
                print(f"[INFO] Rota decidida: Busca Simples. Query: '{busca_obj.query}'")
                final_context = retrieve_final_context(busca_obj.query)

            elif decisao == 'BuscaComposta':
                busca_obj = get_sub_queries(question, self.llm_client)
                # print(f"Tipo retornado por get_sub_queries: {type(busca_obj)}")
                # print(f"Conteúdo retornado: {busca_obj}")

                logger = setup_logger(__name__)
                logger.info(f"\n\nRota decidida: Busca Composta. Sub-Queries: {busca_obj}\n\n")
                docs_combinados = {}
                for sub_query in busca_obj.sub_queries:
                    individual_contexts = retrieve_final_context(sub_query)
                    print(f"\n\nSub-query: {sub_query} -> {len(individual_contexts)} chunks encontrados\n\n")
                    for doc in individual_contexts:
                        docs_combinados[doc.page_content] = doc

                    final_context = list(docs_combinados.values())
                    # time.sleep(20)
                    # contextos = list({doc.page_content: doc for doc in final_context}.values())
                    # print(contextos)
        else:
            final_context_str = [doc.page_content for doc in final_context]

            return self.response_manager.generate_response(
                question=question,
                context = [doc.page_content for doc in self.context_cache],
                session_id= session_id,
                cache_context=self.context_cache
                # session_id=self.session
            )
        self.context_cache = final_context

        if not final_context:
            return "Desculpe, não encontrei contexto para responder."

        final_context_str = [doc.page_content for doc in final_context]

        cache_context_str = [doc.page_content for doc in self.context_cache]
        return self.response_manager.generate_response(
            question=question,
            context=final_context_str,
            session_id=session_id,
            cache_context=cache_context_str)

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