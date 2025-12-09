import streamlit as st
import sys
import os
from langchain.schema import HumanMessage, AIMessage

from backend.src.process_question import ProcessQuestion

# Caminhos do projeto
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)


from backend.src.rag.chat.conversation_history import SessionManager

# --- CONFIG INICIAL ---
st.set_page_config(page_title="Chat Interdisciplinar", layout="wide")
st.title("🧠 Sistema RAG Interdisciplinar")
st.info("Chat iniciado a partir do formulário de seleção de componente.", icon="💬")

# --- AUTENTICAÇÃO ---
if not st.session_state.get("authenticated", False):
    st.error("🔒 Acesso negado. Faça login pela página principal.")
    st.stop()

# --- VARIÁVEIS DE CONTROLE ---
current_user_id = st.session_state["user_id"]
current_user_email = st.session_state["user_email"]

if "session_manager" not in st.session_state:
    st.session_state.session_manager = SessionManager()
if "process_question_instance" not in st.session_state:
    st.session_state.process_question_instance = ProcessQuestion()
if "active_session_id" not in st.session_state:
    st.session_state.active_session_id = None
if "messages_to_display" not in st.session_state:
    st.session_state.messages_to_display = []

session_manager = st.session_state.session_manager
pq = st.session_state.process_question_instance

# --- RECUPERA CHUNKS FIXOS VINDOS DO FORM ---
selected_chunk = st.session_state.get("selected_chunk", None)
from_form = st.session_state.get("from_form", False)

# Se veio do form e ainda não iniciou o chat, mostra saudação inicial
if from_form and not st.session_state.messages_to_display:
    greeting = "Olá! 👋 Qual é a ideia de hoje? Vamos criar uma atividade ou explorar o conteúdo juntos?"
    st.session_state.messages_to_display.append(AIMessage(content=greeting))

# --- SIDEBAR ---
with st.sidebar:
    st.header("Informações")
    st.info(f"Usuário: {current_user_email}")
    if from_form:
        st.success("🔖 Chat com base em conteúdo selecionado do formulário.")
    else:
        st.warning("⚠️ Chat comum (sem conteúdo fixo).")

# --- CHAT PRINCIPAL ---
if not st.session_state.active_session_id:
    st.info("👈 Volte ao formulário para iniciar uma nova sessão.")
else:
    for msg in st.session_state.messages_to_display:
        role = "user" if isinstance(msg, HumanMessage) else "assistant"
        with st.chat_message(role):
            st.markdown(msg.content)

    # Entrada do usuário
    if prompt := st.chat_input("Digite sua pergunta..."):
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.spinner("Pensando..."):
            if from_form and selected_chunk:
                # 🔒 Caminho especial: usa o chunk fixo
                fixed_prompt = f"""
                Você é um assistente interdisciplinar. Use APENAS o conteúdo abaixo para responder.

                --- CONTEXTO ---
                {selected_chunk}
                ----------------

                Pergunta: {prompt}
                """

                answer = pq.generate_answer(
                    question=fixed_prompt,
                    context_chunks=selected_chunk,
                    session_id=st.session_state.active_session_id,
                    user_id=current_user_id,
                )

            else:
                # 🔄 Caminho normal (roteamento completo)
                answer = pq.process_user_question(
                    prompt,
                    st.session_state.active_session_id,
                    current_user_id,
                )

        # Atualiza histórico e tela
        st.session_state.messages_to_display.append(HumanMessage(content=prompt))
        st.session_state.messages_to_display.append(AIMessage(content=answer))

        session_obj = session_manager.get_session(st.session_state.active_session_id)
        session_obj.add_message(HumanMessage(content=prompt))
        session_obj.add_message(AIMessage(content=answer))

        st.rerun()
