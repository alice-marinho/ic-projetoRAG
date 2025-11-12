import streamlit as st
import sys, os

project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)

src_root = os.path.join(project_root, 'src')
if src_root not in sys.path:
    sys.path.append(src_root)

from database.models import UserRole


st.set_page_config(page_title="Meu Projeto", layout="wide")

all_pages = {
    "Publica": [
        st.Page("pages/home.py", title="Home", icon="🏠", default=True),
        st.Page("pages/0_Login.py", title="Login", icon="🔒"),
        st.Page("pages/1_Cadastro.py", title="Cadastro", icon="📝"),
    ],
    "Aplicação": [
        st.Page("pages/1_Chat.py", title="ChatBot", icon="🤖"),
        st.Page("pages/3_Form.py", title="Formulário", icon="📝"),
    ],
    "Administração": [
        st.Page("pages/2_Admin.py", title="Gerenciar Usuários", icon="🛡️"),
        st.Page("pages/banco.py", title="Banco de Dados", icon="🗄️"),
    ]
}


def logout():
    st.session_state["authenticated"] = False
    st.session_state["user_email"] = None
    st.session_state["user_role"] = None
    st.session_state["user_id"] = None
    st.rerun()


is_authenticated = st.session_state.get("authenticated", False)
user_role_name = st.session_state.get("user_role", None)

pages_to_show = {
    "Navegação": all_pages["Publica"]
}

if is_authenticated:
    pages_to_show = {"Navegação": [all_pages["Publica"][0]], "Aplicação": all_pages["Aplicação"]}

    if user_role_name in [UserRole.admin.name, UserRole.super_admin.name]:
        pages_to_show["Administração"] = all_pages["Administração"]

    st.sidebar.write(f"Logado como: {st.session_state['user_email']}")
    st.sidebar.write(f"Nível de Acesso: {user_role_name}")
    st.sidebar.button("Logout", on_click=logout, use_container_width=True)


pg = st.navigation(pages_to_show)
pg.run()
