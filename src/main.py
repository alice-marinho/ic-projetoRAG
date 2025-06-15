import json
import logging
import os
from data_manager import DocsHashChecker

from config.config import CHROMA_DIR
from ingestion import *
from ingestion.cleanner import TextCleaner
from rag import summarize_question, retrieve_context, generate_response
from utils.logger import setup_logger
from vectorstore import VectorStoreManager

def processing_data():

    logger = setup_logger(__name__)
    vs_manager = VectorStoreManager()
    hash_checker = DocsHashChecker()
    dt_extractor = DocsExtractor()

    # Vou verificar os dados do banco
    if not os.path.exists("dados_limpos.json") or hash_checker.has_docs_changed():
        logging.info("Processando documentos...")
        # Leio os pdf e armazeno em uma variável
        docs = load_documents()
        logging.info("Lendo documentos pdf")

        all_docs = ""
        for doc in docs:
            all_docs += doc.page_content + "\n"

        extracted_data = dt_extractor.extract_fields(all_docs)
        # print(type(extracted_data))
        logging.info("Extraindo documentos")
        clean_data = TextCleaner.clean_save_json(extracted_data)
        with open('dados_limpos.json', 'r', encoding='utf-8') as f:
            clean_data = json.load(f)

        print(f"Tipo de dados_limpos: {type(clean_data)}")
        json_documents = split_json(clean_data)


        print(f"Tipo de dados_limpos: {type(clean_data)}")
        # json_documents = split_json(clean_data)

        # Caso não existe o banco vetorial
        if not os.path.exists(CHROMA_DIR):
            vs_manager.create_vectorstore(json_documents)
            logger.info("Base vetorial criada a partir do JSON processado.")
        else:
            # Se já existir, apenas adiciona os novos chunks
            existing_store = vs_manager.load_vectorstore()
            existing_store.add_documents(json_documents)
            logger.info("Base vetorial atualizada com novos chunks do JSON.")
    else:
        print("Usando dados já processados...")
        with open('dados_limpos.json', 'r', encoding='utf-8') as f:
            dados_limpos = json.load(f)
        # split_json(dados_limpos)
        print(type(dados_limpos))
        json_documents = split_json(dados_limpos)
        # json_chunks = split_documents(json_documents)

        if not os.path.exists(CHROMA_DIR):
            vs_manager.create_vectorstore(json_documents)
        else:
            vs_manager.load_vectorstore()


def main():

    # Sistema de Q&A
    conversation_history = []
    processing_data()
    while True:
        question = input("Pergunte sobre (ou sair): ")
        if question.lower() == "sair":
            break
        if not question.strip():
            print("Digite uma pergunta válida.")
            continue

        quest = summarize_question(question)
        final_question = question if quest.upper() == "OK" else quest

        context = retrieve_context(final_question)
        if not context:
            print("Nenhum contexto encontrado.")
            continue

        answer = generate_response(question, context, conversation_history)
        conversation_history.append({"pergunta": question, "resposta": answer})

        print(f"\nResposta da IA:\n{answer}\n")

if __name__ == "__main__":
    main()