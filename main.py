import os

from dotenv import load_dotenv
from together import Together

from llm import generate_response
from summarize.summarize_with_llm import summarize_question
from vectorstore import create_vectorstore, retrieve_context
from documents import load_documents, split_documents


# OLLAMA_URL = "http://localhost:11434/api/generate"
# MODEL = "llama2"
load_dotenv()
client = Together() # os.environ.get("TOGETHER_API_KEY")
client.api_base = "https://api.together.xyz/v1"
FOLDER_PATH = "data/docs" # pasta
CHROMA_DIR = "chroma_db"





def main():
    docs = load_documents()
    print("Documentos carregados.")

    chunks = split_documents(docs)
    print("Documentos divididos em chunks.")

    if not os.path.exists(CHROMA_DIR):
        create_vectorstore(chunks)
        print("Base vetorial criada com sucesso.\n")

    conversation_history = []

    while True:
        question = input("Pergunte sobre (ou sair): ")
        if question.lower() == "sair":
            break

        quest = summarize_question(question)
        # print(quest)
        context = retrieve_context(quest)

        if not context:
            print("Nenhum contexto encontrado.")
            continue

        answer = generate_response(question, context)

        print(f"\nResposta da IA:\n{answer}\n")
        conversation_history.append({"pergunta": question, "resposta": answer})

if __name__ == "__main__":
    main()