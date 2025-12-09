import time
import streamlit as st
import sys, os

# 1. Configuração
st.set_page_config(page_title="Meu Projeto", layout="wide")

# -----------------------------------------------------------
# LOGO DA EMPRESA (Novo recurso do Streamlit)
# -----------------------------------------------------------
# Se tiver uma imagem, use: st.logo("caminho/para/logo.png")
# Se não, ele usa um ícone padrão bonito.
st.logo("https://cdn-icons-png.flaticon.com/512/25/25231.png", link="https://streamlit.io", icon_image=None)

# -----------------------------------------------------------
# LOADING / SPLASH SCREEN (Mantivemos pois é essencial)
# -----------------------------------------------------------
if "backend_loaded" not in st.session_state:
    st.markdown("""<style>[data-testid="stSidebar"] {display: none;}</style>""", unsafe_allow_html=True)
    st.title("🚀 Iniciando Sistema...")

    with st.spinner("Carregando banco de dados..."):
        @st.cache_resource
        def load_backend():
            PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__)))
            if PROJECT_ROOT not in sys.path: sys.path.append(PROJECT_ROOT)
            from backend.database.models import UserRole
            return UserRole


        UserRole = load_backend()
        time.sleep(1)

    st.session_state["backend_loaded"] = True
    st.rerun()

# -----------------------------------------------------------
# APLICAÇÃO PRINCIPAL
# -----------------------------------------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path: sys.path.append(PROJECT_ROOT)

from backend.database.models import UserRole

# Definição das Páginas
all_pages = {
    "Acesso": [  # Mudei o nome para ficar mais curto
        st.Page("pages/home.py", title="Início", icon="🏠", default=True),
        st.Page("pages/0_Login.py", title="Entrar", icon="🔐"),
        st.Page("pages/1_Cadastro.py", title="Criar Conta", icon="✨"),
    ],
    "Ferramentas": [
        st.Page("pages/1_Chat.py", title="Assistente IA", icon="🤖"),
        st.Page("pages/3_Form.py", title="Formulário", icon="📝"),
    ],
    "Gestão": [
        st.Page("pages/2_Admin.py", title="Usuários", icon="👥"),
        st.Page("pages/banco.py", title="Dados", icon="🗄️"),
    ]
}


def logout():
    st.session_state["authenticated"] = False
    st.session_state["user_email"] = None
    st.session_state["user_role"] = None
    st.rerun()


is_authenticated = st.session_state.get("authenticated", False)
user_role_name = st.session_state.get("user_role", None)

# Lógica do Menu (Quem vê o quê)
if is_authenticated:
    # Usuário Logado vê Home + Ferramentas
    pages_to_show = {
        "Menu Principal": [all_pages["Acesso"][0]],  # Só a Home
        "Apps": all_pages["Ferramentas"]
    }

    # Admin vê tudo
    if user_role_name in [UserRole.admin.name, UserRole.super_admin.name]:
        pages_to_show["Painel Admin"] = all_pages["Gestão"]
else:
    # Deslogado vê Login/Cadastro
    pages_to_show = {
        "Bem-vindo": all_pages["Acesso"]
    }

# CRIA A NAVEGAÇÃO (Sem position="hidden", volta ao normal)
pg = st.navigation(pages_to_show)

# -----------------------------------------------------------
# SIDEBAR CUSTOMIZADA (INFO DO USUÁRIO)
# -----------------------------------------------------------
# Isso aparece EMBAIXO do menu de navegação
if is_authenticated:
    with st.sidebar:
        st.divider()  # Linha divisória elegante

        # Cria um container visual para o perfil
        with st.container(border=True):
            col1, col2 = st.columns([1, 4])
            with col1:
                st.write("👤")  # Ou use st.image("foto.png")
            with col2:
                # Trunca email longo para não quebrar layout
                email = st.session_state['user_email']
                st.caption("Conectado como:")
                st.text(email.split('@')[0])  # Mostra só antes do @ para ficar limpo

        # Botão de sair com cor primária (destaque) ou secundária
        st.button("Sair do Sistema", on_click=logout, use_container_width=True, type="secondary")

# Roda a página
pg.run()