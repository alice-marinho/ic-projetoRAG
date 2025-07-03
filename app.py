import streamlit as st
import sys
import os

# Adiciona o diretório 'src' ao sys.path para permitir os imports
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

# Importações do projeto
from main import processing_data, generate_adaptive_response
from rag import summarize_question, retrieve_context
from llm import LLMClient

# Configuração da página do Streamlit
st.set_page_config(page_title="Chatbot RAG Educacional", page_icon="🧠")
st.title("🧠 Chatbot RAG - Assistente Interdisciplinar")

# Inicialização do banco vetorial
if "initialized" not in st.session_state:
    with st.spinner("🔄 Processando documentos e carregando banco vetorial..."):
        processing_data()
    st.session_state.initialized = True
    st.success("✅ Banco vetorial pronto para uso!")

# Inicialização do histórico da conversa
if "history" not in st.session_state:
    st.session_state.history = []

# Entrada de pergunta pelo chat_input
user_question = st.chat_input("Digite sua pergunta...")

# Exibe histórico da conversa
for entry in st.session_state.history:
    with st.chat_message("user"):
        st.markdown(entry["pergunta"])
    with st.chat_message("ai"):
        st.markdown(entry["resposta"])

# Se o usuário fizer uma nova pergunta
if user_question:
    with st.chat_message("user"):
        st.markdown(user_question)

    # Reformulação e verificação de intenção
    summarized = summarize_question(user_question)
    final_question = user_question if summarized.upper() == "OK" else summarized

    # Recuperação de contexto com base na pergunta refinada
    context = retrieve_context(final_question)

    # Verificação de contexto encontrado
    if not context:
        response = "❌ Nenhum contexto relevante foi encontrado nos documentos."
    else:
        response = generate_adaptive_response(user_question, context, st.session_state.history)

    # Armazenar histórico e exibir resposta
    st.session_state.history.append({
        "pergunta": user_question,
        "resposta": response
    })

    with st.chat_message("ai"):
        st.markdown(response)
