import streamlit as st
import sys
import os
from langchain.schema import HumanMessage, AIMessage

from main import ProcessQuestion
from rag.chat.conversation_history import SessionManager

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))


st.info("Aplicativo ainda está em fase de desenvolvimento!", icon="❗")
st.markdown("---")


# --- INICIALIZAÇÃO DO ESTADO DA APLICAÇÃO ---
if "session_manager" not in st.session_state:
    st.session_state.session_manager = SessionManager()
if "process_question_instance" not in st.session_state:
    st.session_state.process_question_instance = ProcessQuestion()
# Variável para rastrear a sessão ATUALMENTE exibida
if "active_session_id" not in st.session_state:
    st.session_state.active_session_id = None
# A lista de mensagens que será exibida na tela (nosso cache)
if "messages_to_display" not in st.session_state:
    st.session_state.messages_to_display = []

session_manager = st.session_state.session_manager
pq = st.session_state.process_question_instance

st.set_page_config(page_title="RAG Educacional", layout="wide")
st.title("🧠 Sistema RAG Interdisciplinar")

# --- SIDEBAR ---
with st.sidebar:
    st.header("Gerenciador de Sessões")

    new_name = st.text_input("Nome da nova sessão:")
    if st.button("Criar Sessão") and new_name.strip():
        new_session_id = session_manager.create_session(new_name)
        st.session_state.active_session_id = new_session_id
        st.session_state.messages_to_display = []  # Nova sessão começa vazia
        st.success(f"Sessão '{new_name}' criada e selecionada!")
        st.rerun()

    sessions = session_manager.list_sessions()
    if sessions:
        st.write("Selecione uma sessão:")  # Título opcional

        # Itera sobre cada sessão para criar um botão
        for session_id, session_name in sessions.items():

            # O 'key' é importante para que cada botão seja único para o Streamlit
            if st.button(session_name, key=session_id, use_container_width=True):
        # session_names = list(sessions.values())
        #
        # selected_name = st.radio("Selecione uma sessão:", session_names)
        # selected_id = next((k for k, v in sessions.items() if v == selected_name), None)

        # Carrega o histórico se o usuário selecionar
                if session_id != st.session_state.active_session_id:
                    st.session_state.active_session_id = session_id
                    session_obj = session_manager.get_session(session_id)
                    st.session_state.messages_to_display = session_obj.messages
                    st.rerun()  # Recarrega para garantir que o chat mostre o histórico certo

    else:
        st.info("Nenhuma sessão criada ainda.")

# --- CHAT PRINCIPAL ---

if not st.session_state.active_session_id:
    st.info("👈 Crie ou selecione uma sessão para começar.")
else:
    session_name = sessions.get(st.session_state.active_session_id, "Sessão")
    st.header(f"💬 {session_name}")

    # 1. O loop agora lê a lista do `session_state`, que é super rápido.
    # Ele não acessa o banco de dados aqui.
    for msg in st.session_state.messages_to_display:
        role = "user" if isinstance(msg, HumanMessage) else "assistant"
        with st.chat_message(role):
            st.markdown(msg.content)

    # 2. Processamento de nova pergunta
    if prompt := st.chat_input("Digite sua pergunta..."):
        # Exibe a pergunta do usuário imediatamente para feedback visual
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.spinner("Pensando..."):
            answer = pq.process_user_question(prompt, st.session_state.active_session_id)

            st.session_state.messages_to_display.append(HumanMessage(content=prompt))
            st.session_state.messages_to_display.append(AIMessage(content=answer))

            session_obj = session_manager.get_session(st.session_state.active_session_id)
            session_obj.add_message(HumanMessage(content=prompt))
            session_obj.add_message(AIMessage(content=answer))

        st.rerun()