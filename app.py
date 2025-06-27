import streamlit as st
import sys
import os

# Adiciona o diretório 'src' ao path para permitir os imports
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

# Importações do seu projeto
from main import processing_data
from rag import summarize_question, retrieve_context, generate_response, IntentDetector, ActivityGenerators
from llm import LLMClient

# Configuração da página do Streamlit
st.set_page_config(page_title="Chatbot RAG Educacional", page_icon="🧠")
st.title("🧠 Chatbot RAG - Assistente Acadêmico")

# Inicializa o banco vetorial se ainda não foi feito
if "initialized" not in st.session_state:
    with st.spinner("🔄 Processando documentos e carregando banco vetorial..."):
        processing_data()
    st.session_state.initialized = True
    st.success("✅ Banco vetorial pronto para uso!")

# Inicializa histórico da conversa
if "history" not in st.session_state:
    st.session_state.history = []

# Entrada de pergunta pelo chat_input
user_question = st.chat_input("Digite sua pergunta...")

# Função para gerar resposta com base no tipo de intenção
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

# Mostrar histórico da conversa
for entry in st.session_state.history:
    with st.chat_message("user"):
        st.markdown(entry["pergunta"])
    with st.chat_message("ai"):
        st.markdown(entry["resposta"])

# Se houver uma nova pergunta
if user_question:
    with st.chat_message("user"):
        st.markdown(user_question)

    summarized = summarize_question(user_question)
    final_question = user_question if summarized.upper() == "OK" else summarized

    context = retrieve_context(final_question)
    if not context:
        response = "❌ Nenhum contexto relevante foi encontrado nos documentos."
    else:
        response = generate_adaptive_response(user_question, context, st.session_state.history)

    # Salvar e exibir resposta
    st.session_state.history.append({"pergunta": user_question, "resposta": response})

    with st.chat_message("ai"):
        st.markdown(response)
