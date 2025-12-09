import streamlit as st
import sys
import os
from langchain.schema import HumanMessage, AIMessage

from pages.streamlit_configs import fetch_sessions_cached, fetch_chat_history_cached

# --- Configuração de Path ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# 🔥🔥 MUDANÇA 2: REMOVEMOS OS IMPORTS PESADOS DAQUI
# from backend.src.process_question import ProcessQuestion  <-- REMOVIDO
# from backend.src.rag.chat.conversation_history import SessionManager <-- REMOVIDO

# --- Configuração da Página ---
st.set_page_config(page_title="RAG Educacional", layout="wide")

# --- AUTENTICAÇÃO ---
if not st.session_state.get("authenticated", False):
    st.error("🔒 Acesso negado.")
    st.stop()

current_user_id = st.session_state["user_id"]
current_user_email = st.session_state["user_email"]

# 🔥🔥 MUDANÇA 3: BARRA SUPERIOR (TOP BAR) COM PERFIL
col_header, col_profile = st.columns([0.8, 0.2])
with col_header:
    st.title("🧠 Sistema RAG Interdisciplinar")
with col_profile:
    with st.popover(f"👤 {current_user_email.split('@')[0]}", use_container_width=True):
        st.caption(f"Logado como: {current_user_email}")
        st.divider()
        if st.button("🚪 Sair", type="primary", use_container_width=True):
            st.session_state["authenticated"] = False
            st.rerun()


# 🔥🔥 MUDANÇA 4: LAZY LOADING (CARREGAMENTO TARDIO)
# Isso faz a troca de abas ser instantânea
@st.cache_resource(show_spinner="Iniciando motores de IA...")
def get_rag_engine():
    # Os imports pesados acontecem SÓ AQUI DENTRO e SÓ UMA VEZ
    from backend.src.process_question import ProcessQuestion
    from backend.src.rag.chat.conversation_history import SessionManager
    return ProcessQuestion(), SessionManager()


# Carrega os serviços do cache (super rápido nas próximas vezes)
pq, session_manager = get_rag_engine()

# --- ESTADOS DO CHAT ---
if "active_session_id" not in st.session_state:
    st.session_state.active_session_id = None
# Não precisamos mais de messages_to_display no session_state para persistência,
# pois usaremos o cache, mas mantemos para compatibilidade do loop
if "messages_to_display" not in st.session_state:
    st.session_state.messages_to_display = []
if "current_fixed_context" not in st.session_state:
    st.session_state.current_fixed_context = None

# --- TRANSIÇÃO DO FORMULÁRIO ---
if "transition_session_id" in st.session_state:
    new_session_id = st.session_state.transition_session_id
    del st.session_state.transition_session_id

    st.session_state.active_session_id = new_session_id
    session_details = session_manager.get_session_details(new_session_id)
    st.session_state.current_fixed_context = session_details.fixed_context if session_details else None

    # Limpa cache para garantir que a nova sessão apareça
    fetch_chat_history_cached.clear()
    st.rerun()

# --- SIDEBAR: GERENCIADOR DE SESSÕES ---
with st.sidebar:
    st.header("Gerenciador")

    if st.button("➕ Nova Conversa", type="primary", use_container_width=True):
        fetch_sessions_cached.clear()
        new_session_id = session_manager.create_session(user_id=current_user_id)
        st.session_state.active_session_id = new_session_id
        fetch_chat_history_cached.clear()  # Limpa msg antiga
        st.session_state.current_fixed_context = None
        st.rerun()

    st.divider()

    # 🔥🔥 MUDANÇA 5: SPINNER REMOVIDO E CSS OTIMIZADO
    # Carrega a lista do cache
    sessions = fetch_sessions_cached(current_user_id)

    with st.expander("🕒 Histórico", expanded=True):
        if sessions:
            # O CSS fica FORA do loop para não ser renderizado 50 vezes
            st.markdown("""
                <style>
                    div[data-testid="stSidebar"] .stButton button div p {
                        white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
                        max-width: 100%; font-size: 14px;
                    }
                    div[data-testid="stSidebar"] .stButton button {
                        height: 40px !important; padding: 0 !important;
                        border: 1px solid #333; justify-content: start;
                    }
                    section[data-testid="stSidebar"] div[data-testid="stPopover"] button svg { display: none !important; }
                    section[data-testid="stSidebar"] div[data-testid="stPopover"] button {
                        padding: 0 !important; justify-content: center !important;
                        height: 40px !important; width: 100% !important;
                        border: 1px solid #333 !important; background: transparent;
                    }
                    div[data-testid="stHorizontalBlock"] { align-items: center; gap: 0.5rem; }
                </style>
            """, unsafe_allow_html=True)

            for session_item in sessions:
                session_id = session_item['id']
                session_name = session_item['name']

                col_chat, col_menu = st.columns([0.82, 0.18])

                with col_chat:
                    tipo_botao = "primary" if session_id == st.session_state.active_session_id else "secondary"
                    if st.button(f"💬 {session_name}", key=f"btn_{session_id}", use_container_width=True,
                                 type=tipo_botao, help=session_name):
                        st.session_state.active_session_id = session_id
                        st.rerun()

                with col_menu:
                    with st.popover("⋮", use_container_width=True):
                        new_name = st.text_input("Renomear", value=session_name, key=f"in_{session_id}")

                        if st.button("Salvar", key=f"sv_{session_id}", use_container_width=True):
                            if new_name.strip():
                                session_manager.update_session_title(session_id, new_name.strip())
                                fetch_sessions_cached.clear()  # Limpa só a lista
                                st.rerun()

                        st.divider()
                        if st.button("Excluir", key=f"del_{session_id}", type="primary", use_container_width=True):
                            session_manager.delete_session(session_id)
                            fetch_sessions_cached.clear()
                            fetch_chat_history_cached.clear()
                            if st.session_state.active_session_id == session_id:
                                st.session_state.active_session_id = None
                            st.rerun()
        else:
            st.caption("Sem histórico.")

# --- CHAT PRINCIPAL ---
if not st.session_state.active_session_id:
    st.info("👈 Selecione uma conversa no histórico.")
else:
    if st.session_state.current_fixed_context:
        st.success("🎯 Modo Interdisciplinar Ativo")

    # 🔥🔥 MUDANÇA 6: CARREGAMENTO DE MENSAGENS VIA CACHE
    # Isso faz o clique no chat ser instantâneo
    current_messages = fetch_chat_history_cached(st.session_state.active_session_id)

    # Exibe as mensagens do cache
    for msg in current_messages:
        role = "user" if isinstance(msg, HumanMessage) else "assistant"
        with st.chat_message(role):
            st.markdown(msg.content)

    # Input do usuário
    if prompt := st.chat_input("Digite sua pergunta..."):
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.spinner("Pensando..."):
            if st.session_state.current_fixed_context:
                answer = pq.generate_answer(
                    question=prompt,
                    context_chunks=st.session_state.current_fixed_context,
                    session_id=st.session_state.active_session_id,
                    user_id=current_user_id,
                )
            else:
                answer = pq.process_user_question(
                    prompt,
                    st.session_state.active_session_id,
                    current_user_id
                )

        # Atualiza banco
        session_obj = session_manager.get_session(st.session_state.active_session_id)
        session_obj.add_message(HumanMessage(content=prompt))
        session_obj.add_message(AIMessage(content=answer))

        # 🔥🔥 MUDANÇA 7: LIMPA O CACHE DE MENSAGENS PARA ATUALIZAR
        fetch_chat_history_cached.clear()

        # Gera título se for novo
        try:
            current_title = session_manager.get_session_title(st.session_state.active_session_id)
            if current_title == "Novo Chat":
                new_title = session_manager.generate_chat_title(prompt)
                session_manager.update_session_title(st.session_state.active_session_id, new_title)
                fetch_sessions_cached.clear()  # Atualiza sidebar
        except:
            pass

        st.rerun()