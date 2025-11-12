# Seu novo arquivo: Chat.py
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

# --- INICIALIZAÇÃO DO ESTADO DO CHAT ---
if "active_session_id" not in st.session_state:
    st.session_state.active_session_id = None
if "messages_to_display" not in st.session_state:
    st.session_state.messages_to_display = []
if "current_session_is_form" not in st.session_state:
    st.session_state.current_session_is_form = False
if "current_session_chunks" not in st.session_state:
    st.session_state.current_session_chunks = None

# --- LÓGICA DE TRANSIÇÃO DO FORMULÁRIO ---
# Verifica se o usuário acabou de vir do formulário
if st.session_state.get("from_form", False):
    # Pega os chunks salvos pelo formulário (CORRIGIDO PARA "selected_chunks")
    form_chunks = st.session_state.get("selected_chunks")

    if form_chunks:
        # 1. Cria uma nova sessão para este chat de formulário
        new_session_id = session_manager.create_session(
            user_id=current_user_id,
            name="Chat Interdisciplinar"
        )
        st.session_state.active_session_id = new_session_id

        # 2. Configura o estado da sessão atual
        st.session_state.messages_to_display = [
            AIMessage(content="Olá! 👋 Vamos criar uma atividade com base nos planos que você selecionou.")
        ]
        st.session_state.current_session_is_form = True
        st.session_state.current_session_chunks = form_chunks

        # 3. Limpa os flags globais para não afetar outras sessões
        del st.session_state["from_form"]
        del st.session_state["selected_chunks"]
        if "metadata_list" in st.session_state:
            del st.session_state["metadata_list"]

        st.success("Sessão interdisciplinar iniciada!")
        st.rerun()  # Recarrega a página para refletir a nova sessão

# --- SIDEBAR: GERENCIADOR DE SESSÕES ---
with st.sidebar:
    st.header("Gerenciador de Sessões")

    new_name = st.text_input("Nome da nova sessão (RAG Puro):")
    if st.button("Criar Sessão") and new_name.strip():
        new_session_id = session_manager.create_session(
            user_id=current_user_id,
            name=new_name
        )
        st.session_state.active_session_id = new_session_id
        st.session_state.messages_to_display = []  # Nova sessão RAG puro
        st.session_state.current_session_is_form = False  # É RAG puro
        st.session_state.current_session_chunks = None  # É RAG puro
        st.success(f"Sessão '{new_name}' criada!")
        st.rerun()

    st.divider()

    sessions = session_manager.list_sessions(user_id=current_user_id)
    if sessions:
        st.write("Selecione uma sessão:")

        # Inverte o dicionário para ordenar por nome
        sorted_sessions = sorted(sessions.items(), key=lambda item: item[1])

        for session_id, session_name in sorted_sessions:
            if st.button(session_name, key=session_id, use_container_width=True):
                if session_id != st.session_state.active_session_id:
                    st.session_state.active_session_id = session_id

                    # Carrega histórico do banco
                    session_obj = session_manager.get_session(session_id)
                    st.session_state.messages_to_display = session_obj.messages

                    # ATENÇÃO: Esta lógica assume que SESSÕES DE FORMULÁRIO NÃO SÃO SALVAS
                    # Se você quiser que o modo "form" seja persistente,
                    # você precisará adicionar "is_form" e "chunks" ao seu
                    # SessionModel no banco de dados.
                    # Por enquanto, assumimos que qualquer sessão carregada é RAG Puro.
                    st.session_state.current_session_is_form = False
                    st.session_state.current_session_chunks = None

                    st.rerun()
    else:
        st.info("Nenhuma sessão criada ainda.")

# --- CHAT PRINCIPAL ---
if not st.session_state.active_session_id:
    st.info("👈 Crie uma nova sessão ou use o Formulário de Disciplinas para começar.")
else:
    # Exibe o status da sessão atual
    if st.session_state.current_session_is_form:
        st.success("🎯 Modo Interdisciplinar: Respondendo com base nos documentos selecionados.")
    else:
        st.info("📚 Modo RAG Puro: Respondendo com base em todo o banco de dados.")

    # Exibe histórico
    for msg in st.session_state.messages_to_display:
        role = "user" if isinstance(msg, HumanMessage) else "assistant"
        with st.chat_message(role):
            st.markdown(msg.content)

    # Entrada do usuário
    if prompt := st.chat_input("Digite sua pergunta..."):
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.spinner("Pensando..."):

            # Decide qual método da ProcessQuestion chamar
            if st.session_state.current_session_is_form and st.session_state.current_session_chunks:
                # --- Caminho 1: MODO FORMULÁRIO ---
                answer = pq.generate_answer(
                    question=prompt,  # Passa o prompt original
                    context_chunks=st.session_state.current_session_chunks,  # Passa os chunks
                    session_id=st.session_state.active_session_id,
                    user_id=current_user_id,
                )
            else:
                # --- Caminho 2: MODO RAG PURO ---
                answer = pq.process_user_question(
                    prompt,
                    st.session_state.active_session_id,
                    current_user_id
                )

        # Adiciona mensagens ao histórico local (para exibição)
        st.session_state.messages_to_display.append(HumanMessage(content=prompt))
        st.session_state.messages_to_display.append(AIMessage(content=answer))

        # Adiciona mensagens ao banco de dados
        session_obj = session_manager.get_session(st.session_state.active_session_id)
        session_obj.add_message(HumanMessage(content=prompt))
        session_obj.add_message(AIMessage(content=answer))

        st.rerun()