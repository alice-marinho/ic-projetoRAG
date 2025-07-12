import json
import logging
import os

from data_manager import DocsHashChecker

from config.config import CHROMA_DIR
from ingestion import *
from ingestion.cleanner import TextCleaner
from rag import summarize_question, retrieve_context, generate_response, IntentDetector, ActivityGenerators
from rag.prompt_engineer import *
from searcher.course_loader import AppController
from searcher.interdisciplinaridade import Interdisciplina
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


def main():
    # 1. Processar dados e atualizar vetor
    processing_data()

    # 2. Iniciar o controller para escolher curso, semestre e matérias
    # controller = AppController()
    # controller.executar()
    # curso = controller.curso
    # semestre = controller.semestre
    # componentes = controller.componentes
    # # componente2 = controller.componente2
    #
    # print(f"[DEBUG] curso: {curso}, semestre: {semestre}, disciplina 1: {componentes}")
    #
    # inter = Interdisciplina(
    #     curso= curso,
    #     periodo= semestre,
    #     disciplinas = componentes
    # )
    #
    # resposta = inter.interdisciplinaridade_filtros()
    #
    # print(resposta)


    # 3. Recuperar matérias selecionadas e gerar sugestões de projetos


    # 4. Criar pergunta automática para gerar sugestões de projetos
    #materia_str = ", ".join(componentes)
    #print(materia_str)
    #pergunta_projetos = f"Quais são boas ideias de projetos para as seguintes matérias: {materia_str}?"

    # 5. Buscar contexto e gerar resposta da IA
    #contexto = retrieve_context(componentes)
    #sugestoes = generate_adaptive_response(pergunta_projetos, contexto, [])

    # print("\nSugestões de projetos com base nas matérias escolhidas:")
    #print(sugestoes)

    # 6. Iniciar o chat normal
    conversation_history = []

    while True:
        question = input("Pergunte sobre (ou sair): ")
        if question.lower() == "sair":
            break
        if not question.strip():
            print("Digite uma pergunta válida.")
            continue

        reformulated = summarize_question(question)
        #raw_keywords = extract_keywords(reformulated)
        keywords = extract_keywords(reformulated)
        # print(f"\n[SPACY] Palavras-chave extraídas: {raw_keywords}")

        # Refinar com LLM
        # refined_keywords = refine_keywords_llm(reformulated, raw_keywords)
        print(f"\n[LLM] Palavras-chave refinadas: {keywords}")

        final_question = expand_question_with_keywords(reformulated, keywords)
        # final_question = question if quest.upper() == "OK" else quest

        context = retrieve_context(final_question)
        if not context:
            print("Nenhum contexto encontrado.")
            continue
        # Verificação mais detalhada. Só vai consultar a base de dados própria, caso tenha correlação na base de dados.

        answer = generate_adaptive_response(question, context, conversation_history)
        # answer = generate_response(question, context, conversation_history)
        conversation_history.append({"pergunta": question, "resposta": answer})

        print(f"\nResposta da IA:\n{answer}\n")

if __name__ == "__main__":
    main()