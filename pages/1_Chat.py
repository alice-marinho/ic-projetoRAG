import streamlit as st
import sys
import os
from langchain.schema import HumanMessage, AIMessage

# --- Configuração de Path ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from main import ProcessQuestion
from rag.chat.conversation_history import SessionManager

# --- Configuração da Página ---
st.set_page_config(page_title="RAG Educacional", layout="wide")
st.title("🧠 Sistema RAG Interdisciplinar")

# --- AUTENTICAÇÃO ---
if not st.session_state.get("authenticated", False):
    st.error("🔒 Acesso negado. Por favor, faça login pela página principal.")
    st.stop()

current_user_id = st.session_state["user_id"]
current_user_email = st.session_state["user_email"]
st.info(f"Logado como: {current_user_email}")

# --- INICIALIZAÇÃO DOS SERVIÇOS ---
if "session_manager" not in st.session_state:
    st.session_state.session_manager = SessionManager()
if "process_question_instance" not in st.session_state:
    st.session_state.process_question_instance = ProcessQuestion()

session_manager = st.session_state.session_manager
pq = st.session_state.process_question_instance

# --- INICIALIZAÇÃO DO ESTADO DO CHAT---
if "active_session_id" not in st.session_state:
    st.session_state.active_session_id = None
if "messages_to_display" not in st.session_state:
    st.session_state.messages_to_display = []
if "current_fixed_context" not in st.session_state:
    st.session_state.current_fixed_context = None

# --- LÓGICA DE TRANSIÇÃO DO FORMULÁRIO ---
if "transition_session_id" in st.session_state:
    new_session_id = st.session_state.transition_session_id
    del st.session_state.transition_session_id  # Limpa o flag

    st.session_state.active_session_id = new_session_id

    # Carrega os detalhes do banco
    session_details = session_manager.get_session_details(new_session_id)
    if session_details:
        st.session_state.current_fixed_context = session_details.fixed_context
    else:
        st.session_state.current_fixed_context = None

    st.session_state.messages_to_display = [
        AIMessage(content="Olá! 👋 Vamos criar uma atividade com base nos planos que você selecionou.")
    ]
    st.rerun()

# --- SIDEBAR: GERENCIADOR DE SESSÕES ---
with st.sidebar:
    st.header("Gerenciador de Sessões")

    if "editing_chat_id" not in st.session_state:
        st.session_state.editing_chat_id = None

    if st.sidebar.button("➕ Novo Chat", use_container_width=True):
        new_session_id = session_manager.create_session(
            user_id=current_user_id,
            fixed_context=None
        )
        st.session_state.active_session_id = new_session_id
        st.session_state.messages_to_display = []
        st.session_state.current_fixed_context = None
        st.session_state.editing_chat_id = None # modo edição
        st.success("Novo chat criado!")
        st.rerun()

    st.divider()

    sessions = session_manager.list_sessions(user_id=current_user_id)
    if sessions:
        st.write("Selecione uma sessão:")
        sorted_sessions = sessions.items()

        for session_id, session_name in sorted_sessions:
            if session_id == st.session_state.editing_chat_id:
                # MODO DE EDIÇÃO
                with st.container(border=True):
                    new_name = st.text_input(
                        "Novo nome:",
                        value=session_name,
                        key=f"input_{session_id}"
                    )

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Salvar", key=f"save_{session_id}", use_container_width=True):
                            if new_name.strip():
                                session_manager.update_session_title(session_id, new_name.strip())
                                st.session_state.editing_chat_id = None
                                st.rerun()
                            else:
                                st.error("O nome não pode ficar em branco.")
                    with col2:
                        if st.button("Cancelar", key=f"cancel_{session_id}", use_container_width=True):
                            st.session_state.editing_chat_id = None
                            st.rerun()

            else:
                col1, col2, col3 = st.columns([0.7, 0.15, 0.15])
                with col1:
                    if st.button(session_name, key=session_id, use_container_width=True):
                        if session_id != st.session_state.active_session_id:
                            st.session_state.active_session_id = session_id
                            session_obj = session_manager.get_session(session_id)
                            st.session_state.messages_to_display = session_obj.messages
                            session_details = session_manager.get_session_details(session_id)
                            if session_details:
                                st.session_state.current_fixed_context = session_details.fixed_context
                            else:
                                st.session_state.current_fixed_context = None

                            st.session_state.editing_chat_id = None # Sai do modo de edição
                            st.rerun()
                with col2:
                    if st.button("✏️", key=f"edit_{session_id}", use_container_width=True):
                        st.session_state.editing_chat_id = session_id
                        st.rerun()
                with col3:
                    if st.button("🗑️", key=f"delete_{session_id}", use_container_width=True):
                        session_manager.delete_session(session_id)

                        # recarrega
                        st.session_state.active_session_id = None
                        st.session_state.messages_to_display = []
                        st.session_state.current_fixed_context = None
                        st.session_state.editing_chat_id = None

                        st.rerun()
    else:
        st.info("Nenhuma sessão criada ainda.")

# --- CHAT PRINCIPAL ---
if not st.session_state.active_session_id:
    st.info("👈 Crie uma nova sessão ou use o Formulário de Disciplinas para começar.")
else:
    if st.session_state.current_fixed_context:
        st.success("🎯 Modo Interdisciplinar: Respondendo com base nos documentos salvos nesta sessão.")
    else:
        st.info("📚 Modo RAG Puro: Respondendo com base em todo o banco de dados.")

    # Histórico
    for msg in st.session_state.messages_to_display:
        role = "user" if isinstance(msg, HumanMessage) else "assistant"
        with st.chat_message(role):
            st.markdown(msg.content)

    # Titulo
    is_new_chat = False
    try:
        current_title = session_manager.get_session_title(st.session_state.active_session_id)
        if current_title == "Novo Chat":
            is_new_chat = True
    except Exception as e:
        st.warning(f"Não foi possível verificar o título do chat: {e}")

    # Entrada do usuário
    if prompt := st.chat_input("Digite sua pergunta..."):
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.spinner("Pensando..."):

            if st.session_state.current_fixed_context:
                answer = pq.generate_answer(
                    question=prompt,
                    context_chunks=st.session_state.current_fixed_context,  # <-- CORREÇÃO
                    session_id=st.session_state.active_session_id,
                    user_id=current_user_id,
                )
            else:
                answer = pq.process_user_question(
                    prompt,
                    st.session_state.active_session_id,
                    current_user_id
                )

        st.session_state.messages_to_display.append(HumanMessage(content=prompt))
        st.session_state.messages_to_display.append(AIMessage(content=answer))

        session_obj = session_manager.get_session(st.session_state.active_session_id)
        session_obj.add_message(HumanMessage(content=prompt))
        session_obj.add_message(AIMessage(content=answer))

        if is_new_chat:
            try:
                new_title = session_manager.generate_chat_title(prompt)
                session_manager.update_session_title(st.session_state.active_session_id, new_title)
            except Exception as e:
                st.error(f"Erro ao gerar título do chat: {e}")

        st.rerun()