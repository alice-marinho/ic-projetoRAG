import os

from data_manager import DocsHashChecker

from config.config import CHROMA_DIR
from ingestion import *
from ingestion.cleanner import TextCleaner
from rag import retrieve_context, generate_response, IntentDetector, ActivityGenerators
from rag.prompt_engineer import *
from rag.routing.router import get_router_decision
from rag.routing.routing_models import BuscaComposta, BuscaSimples
from utils.logger import setup_logger
from vectorstore import VectorStoreManager


def processing_data():

    logger = setup_logger(__name__)
    vs_manager = VectorStoreManager()
    hash_checker = DocsHashChecker()
    dt_extractor = DocsExtractor()

    if not os.path.exists(CHROMA_DIR):
        logger.info(f"Diretório '{CHROMA_DIR}' não encontrado. Iniciando recriação total...")

        # Carrega os documentos da pasta
        todos_os_docs = load_documents()
        if not todos_os_docs:
            logger.warning("Nenhum documento encontrado para processar. Encerrando.")
            return

        # Bloco de Processamento (Extração, Limpeza, Split) ---
        logger.info(f"Processando todos os {len(todos_os_docs)} documentos carregados...")

        # a. Agrupar texto por arquivo de origem
        docs_agrupados = {}
        for doc in todos_os_docs:
            source_file = doc.metadata["source"]
            if source_file not in docs_agrupados:
                docs_agrupados[source_file] = ""
            docs_agrupados[source_file] += doc.page_content + "\n"

        # b. Extrair dados estruturados
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

        # c. Limpar dados
        dados_limpos = TextCleaner.clean_save_json(dados_extraidos_completos)

        # d. Dividir em chunks
        chunks_db = split_json(dados_limpos)
        # --- Fim do Bloco de Processamento ---

        # Cria o banco do zero com todos os chunks
        vs_manager.create_vectorstore(chunks_db)

        # Salva o estado atual dos hashes para futuras comparações
        hash_checker.save_current_hashes()
        logger.info("Recriação total concluída. Banco vetorial e arquivo de hash criados.")

        ### CENÁRIO 2 - Verificações do banco já existente ###
    else:
        logger.info("Banco vetorial encontrado. Verificando por mudanças nos documentos...")

        changes = hash_checker.get_changes()

        if not any(changes.values()):
            logger.info("Nenhuma mudança detectada. O banco de dados está atualizado.")
            return

        logger.info(
            f"Mudanças detectadas: {len(changes['added'])} adicionados, {len(changes['removed'])} removidos, {len(changes['modified'])} modificados.")
        store = vs_manager.load_vectorstore()

        ## Remover Dados Antigos ##
        files_to_remove = changes['removed'] + changes['modified']
        if files_to_remove:
            logger.info(f"Removendo dados antigos de {len(files_to_remove)} arquivo(s)...")
            for filename in files_to_remove:
                store.delete(where={"source": filename})
            logger.info("Dados antigos removidos com sucesso.")

        ## Processar e Adicionar Novos Dados ##
        files_to_process = changes['added'] + changes['modified']
        if files_to_process:
            logger.info(f"Processando {len(files_to_process)} arquivo(s) novos/modificados...")

            # Carrega apenas os documentos que mudaram
            docs_a_processar = load_documents()

            if docs_a_processar:
                # Bloco de Processamento
                logger.info(f"Processando {len(docs_a_processar)} documentos novos/modificados...")

                # a. Agrupar texto por arquivo de origem
                docs_agrupados = {}
                for doc in docs_a_processar:
                    source_file = doc.metadata["source"]
                    if source_file not in docs_agrupados:
                        docs_agrupados[source_file] = ""
                    docs_agrupados[source_file] += doc.page_content + "\n"

                # b. Extrair dados estruturados
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

def generate_adaptive_response(question, context, history):
    tipo = IntentDetector.detectar_tipo_de_atividade(question)

    if tipo == "geral":
        return generate_response(question, context, history)

    if tipo == "projeto":
        prompt = ActivityGenerators.montar_prompt_projeto(question, context, history)
    elif tipo == "prova":
        prompt = ActivityGenerators.montar_prompt_prova(question, context, history)
    elif tipo == "atividade":
        prompt = ActivityGenerators.montar_prompt_atividade(question, context, history)
    else:
        prompt = generate_response(question, context, history)

    llm = LLMClient()
    return llm.chat(prompt)


def process_user_question(question: str, conversation_history):
    """
    Orquestra o fluxo completo, começando pela verificação/roteamento.
    """
    decisao = get_router_decision(question)

    contextos = []

    if isinstance(decisao, BuscaSimples):
        print(f"[INFO] Rota decidida: Busca Simples. Query: '{decisao.query}'")
        # contextos = retrieve_context(decisao.query)

    elif isinstance(decisao, BuscaComposta):
        print(f"[INFO] Rota decidida: Busca Composta. Sub-Queries: {decisao.sub_queries}")
        contextos_combinados = []
        for sub_query in decisao.sub_queries:
            contextos_individuais = retrieve_context(sub_query)
            contextos_combinados.extend(contextos_individuais)
        # contextos = list(set(contextos_combinados))


def main():
    processing_data()
    conversation_history = []

    while True:
        question = input("Pergunte sobre (ou sair): ")
        if question.lower() == "sair":
            break
        if not question.strip():
            print("Digite uma pergunta válida.")
            continue
        # answer = orquestrar_resposta(question, conversation_history)
        answer = process_user_question(question, conversation_history)

        # reformulated = rewrite_query(question)

        ##### KEY WORDS ########
        # keywords = extract_keywords(reformulated)
        # print(f"\n[SPACY] Palavras-chave extraídas: {raw_keywords}")

        # Refinar com LLM
        # refined_keywords = refine_keywords_llm(reformulated, raw_keywords)
        # print(f"\n[LLM] Palavras-chave refinadas: {keywords}")

        # final_question = expand_question_with_keywords(reformulated, keywords)
        # final_question = question if quest.upper() == "OK" else quest

        ##### RETRIVER SEM O FLUXO NOVO ########
        # # context = retrieve_context(reformulated)
        # if not context:
        #     print("Nenhum contexto encontrado.")
        #     continue
        # else:
        #     for i, doc in context:
        #         print(f"\n--- Chunk {i + 1} ---")
        #         print(f"Conteúdo: {doc.page_content[:100]}...")  # Mostra os primeiros 100 caracteres
        #         print(f"Metadados: {doc.metadata}")
        #         print("-" * 20)
        # # Verificação mais detalhada. Só vai consultar a base de dados própria, caso tenha correlação na base de dados.
        #
        # #answer = generate_adaptive_response(question, context, conversation_history)
        # answer = generate_response(question, context, conversation_history)
        # conversation_history.append({"pergunta": question, "resposta": answer})

        print(f"\nResposta da IA:\n{answer}\n")

if __name__ == "__main__":
    main()