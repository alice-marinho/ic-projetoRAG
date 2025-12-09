import streamlit as st
import sys, os
import threading
from streamlit.runtime.scriptrunner import add_script_run_ctx  # Importante!

from backend.auth import user_service, security
from backend.database.database import SessionLocal

# --- Configurações de Path (Mantenha as suas) ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path: sys.path.append(project_root)
src_root = os.path.join(project_root, 'src')
if src_root not in sys.path: sys.path.append(src_root)


# -----------------------------------------------------------
# 1. FUNÇÃO CACHEADA (O segredo está aqui)
# -----------------------------------------------------------
@st.cache_data(show_spinner=False, ttl=300)
def fetch_sessions_cached(user_id):
    """
    Busca as sessões no banco e guarda em cache.
    Importamos o SessionManager aqui dentro para evitar
    carregamento pesado no início do script de login.
    """
    try:
        # Import tardio para não travar o Login
        from backend.src.rag.chat.conversation_history import SessionManager
        manager = SessionManager()
        # Retorna o dicionário de sessões
        return manager.list_sessions(user_id=user_id)
    except Exception as e:
        print(f"Erro ao fazer cache warming: {e}")
        return {}


# Função wrapper para a thread
def background_loader(user_id):
    print(f"🔄 [Background] Carregando chats do user {user_id}...")
    fetch_sessions_cached(user_id)
    print("✅ [Background] Chats carregados!")


# -----------------------------------------------------------
# UI DO LOGIN
# -----------------------------------------------------------
st.markdown("""
    <style>
        section[data-testid="stAppViewBlockContainer"] {
            max-width: 40rem;
            margin: auto;
            padding-top: 5rem;
        }
    </style>
""", unsafe_allow_html=True)

st.title("Login no Sistema")

email = st.text_input("Email", key="login_email")
password = st.text_input("Senha", type="password", key="login_password")

if st.button("Login", use_container_width=True, key="login_button"):

    if len(password.encode('utf-8')) > 72:
        st.error("A senha é muito longa.")
    else:
        db = SessionLocal()
        try:
            user = user_service.get_user_by_email(email, db)

            if user and security.verify_password(password, user.password_hash):
                if not user.is_active:
                    st.warning("⚠️ Sua conta ainda está pendente de aprovação.")
                    st.markdown("""
                                    <small>Um administrador precisa ativar seu cadastro antes que você possa acessar. 
                                    Aguarde o e-mail de confirmação.</small>
                                """, unsafe_allow_html=True)
                    st.stop()
                else:
                    # SUCESSO NO LOGIN
                    st.session_state["authenticated"] = True
                    st.session_state["user_email"] = user.email
                    st.session_state["user_role"] = user.role.name
                    st.session_state["user_id"] = user.id

                    t = threading.Thread(target=background_loader, args=(user.id,))
                    add_script_run_ctx(t)  # Anexa o contexto do Streamlit
                    t.start()

                    st.success("Login realizado! Redirecionando...")
                    st.rerun()  # Vai para a Home (ou App)
            else:
                st.error("Email ou senha incorretos.")
        finally:
            db.close()
st.write("Não tem uma conta?")
st.page_link("pages/1_Cadastro.py", label="Cadastre-se")