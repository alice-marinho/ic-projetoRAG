import streamlit as st
import sys, os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

src_root = os.path.join(project_root, 'src')
if src_root not in sys.path:
    sys.path.append(src_root)

from database.database import SessionLocal
from auth import security, user_service

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

# Damos chaves únicas para garantir
email = st.text_input("Email", key="login_email")
password = st.text_input("Senha", type="password", key="login_password")

if st.button("Login", use_container_width=True, key="login_button"):

    if len(password.encode('utf-8')) > 72:
        st.error("A senha é muito longa (limite de 72 bytes/caracteres).")
    else:
        db = SessionLocal()
        try:
            user = user_service.get_user_by_email(email, db)

            if user and security.verify_password(password, user.password_hash):
                if not user.is_active:
                    st.error("Sua conta está pendente de aprovação por um administrador.")
                else:
                    # SUCESSO NO LOGIN
                    st.session_state["authenticated"] = True
                    st.session_state["user_email"] = user.email
                    st.session_state["user_role"] = user.role.name
                    st.session_state["user_id"] = user.id
                    st.rerun()
            else:
                st.error("Email ou senha incorretos.")
        finally:
            db.close()

st.page_link("pages/1_Cadastro.py", label="Não tem uma conta? Cadastre-se")