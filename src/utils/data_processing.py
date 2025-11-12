from config.config import CHROMA_DIR
from data_manager import DocsHashChecker
from ingestion import DocsExtractor, load_documents, TextCleaner, split_json
from utils.logger import setup_logger
from vectorstore import VectorStoreManager
from vectorstore.mongo_db import MongoDocstore
from vectorstore.postgres_db import PostgresDocstore


def processing_data(reload):

    logger = setup_logger(__name__)

    # reload = input("Deseja refazer o banco de dados? s/n\n")


    # Execute antes de reindexar
    #if not os.path.exists(CHROMA_DIR):
    logger.info(f"Diretório '{CHROMA_DIR}' não encontrado. Iniciando recriação total...")
    vs_manager = VectorStoreManager()
    # mongo_manager = MongoDocstore()
    pg_manager = PostgresDocstore()

    hash_checker = DocsHashChecker()
    dt_extractor = DocsExtractor()

    if reload == "s":
        print("="*40)

        # vs_manager.clean_storage()

        # pg_manager.clear()
        vs_manager.clear()
        logger.info("Banco Vetorial ")

        # mongo_manager.clear()

        VectorStoreManager._instances = {}  # Limpa a instância Singleton
        vs_manager = VectorStoreManager()


        todos_os_docs = load_documents()
        if not todos_os_docs:
            logger.warning("Nenhum documento encontrado para processar. Encerrando.")
            return

        logger.info(f"Processando todos os {len(todos_os_docs)} documentos carregados...")

        docs_agrupados = {}
        for doc in todos_os_docs:
            source_file = doc.metadata["source"]
            docs_agrupados.setdefault(source_file, "")
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

        changes = hash_checker.get_changes()
        if not any(changes.values()):
            logger.info("Nenhuma mudança detectada. O banco de dados está atualizado.")
            vs_manager.load_vectorstore()
            return

        logger.info(
            f"Mudanças detectadas: {len(changes['added'])} adicionados, {len(changes['removed'])} removidos, {len(changes['modified'])} modificados.")
        # store = vs_manager.load_vectorstore()

        files_to_remove = changes['removed'] + changes['modified']
        if files_to_remove:
            logger.info(f"Removendo dados antigos de {len(files_to_remove)} arquivo(s)...")
            vs_manager.vectorstore.delete(
                where={"source": {"$in": changes['removed'] + changes['modified']}}
            )
            logger.info("Dados antigos removidos com sucesso.")

        files_to_process = changes['added'] + changes['modified']
        if files_to_process:
            logger.info(f"Processando {len(files_to_process)} arquivo(s) novos/modificados...")
            docs_a_processar = load_documents()

            if not docs_a_processar:
                logger.warning("Nenhum conteúdo válido encontrado nos novos arquivos para processar.")
                return

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

            novos_dados_limpos = TextCleaner.clean_save_json(novos_dados_extraidos)
            vs_manager.organize_disciplines(novos_dados_limpos)
            logger.info("Novos dados adicionados ao banco vetorial.")


        # Atualiza o arquivo de hash para o novo estado
        hash_checker.save_current_hashes()
        logger.info("Refresh inteligente concluído. Arquivo de hash atualizado.")
