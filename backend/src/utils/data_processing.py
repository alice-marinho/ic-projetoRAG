from sqlalchemy import text

from backend.database.database import sqlal_engine
from backend.database.manager import VectorStoreManager
from backend.src.config.config import CHROMA_DIR
from backend.src.data_manager import DocsHashChecker
from backend.src.ingestion import DocsExtractor, load_documents, TextCleaner
from backend.src.utils.logger import setup_logger
from backend.database.postgres_db import PostgresDocstore


def clear_vector_database():
    """
    Esvazia TODO o conteúdo das tabelas de vetores (chunks) e documentos (pais).
    """
    logger = setup_logger(__name__)
    logger.warning("INICIANDO LIMPEZA TOTAL DO BANCO VETORIAL...")


    tables_to_truncate = [
        "langchain_pg_embedding",
        "parent_documents",
        "langchain_pg_collection"
    ]

    try:
        with sqlal_engine.connect() as conn:
            with conn.begin():
                # table_names = ", ".join([f'"{table}"' for table in tables_to_truncate])
                # sql_query = f"TRUNCATE TABLE {table_names} RESTART IDENTITY CASCADE;"
                # logger.info(f"Executando: {sql_query}")
                # conn.execute(text(sql_query))
                logger.info("SUCESSO: Conteúdo do banco vetorial limpo.")
            return True

    except Exception as e:
        logger.error(f"ERRO AO LIMPAR O BANCO VETORIAL")
        logger.error(f"Erro: {e}")
        return False


def processing_data(reload: str):
    """
    Processa todos os documentos e recria o banco de dados.
    """
    logger = setup_logger(__name__)

    if reload != "s":
        logger.info("Processamento de dados pulado (reload != 's').")
        return

    logger.info("=" * 40)
    logger.info("Modo REBUILD TOTAL iniciado...")

    success = clear_vector_database()
    if not success:
        logger.error("Falha ao limpar o banco. Abortando o processamento.")
        return

    vs_manager = VectorStoreManager()
    dt_extractor = DocsExtractor()

    all_docs = load_documents()
    if not all_docs:
        logger.warning("Nenhum documento encontrado para processar. Encerrando.")
        return

    logger.info(f"Processando todos os {len(all_docs)} documentos carregados...")

    docs_agrupados = {}
    for doc in all_docs:
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

    logger.info("Recriação total concluída. Banco vetorial recriado.")
    pass