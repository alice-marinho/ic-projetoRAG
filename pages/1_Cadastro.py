import streamlit as st
import sys, os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

# Adiciona 'src' ao path
src_root = os.path.join(project_root, 'src')
if src_root not in sys.path:
    sys.path.append(src_root)
from auth import user_service
from database.database import SessionLocal


st.set_page_config(page_title="Cadastro", layout="centered")
st.title("Página de Cadastro")
st.write("Crie sua conta. Ela precisará ser aprovada por um administrador.")

db = SessionLocal()
try:
    with st.form("signup_form"):
        name = st.text_input("Nome Completo")
        email = st.text_input("Email")
        password = st.text_input("Senha", type="password")
        password_confirm = st.text_input("Confirme a Senha", type="password")

        submitted = st.form_submit_button("Cadastrar")

        if submitted:
            if not name or not email or not password:
                st.error("Por favor, preencha todos os campos.")
            elif password != password_confirm:
                st.error("As senhas não coincidem.")
            elif user_service.get_user_by_email(email, db):
                st.error("Este email já está cadastrado.")
            else:
                # create_user por padrão salva como is_active=False
                user_service.create_user(db, name, email, password)
                st.success("Cadastro realizado com sucesso! Aguarde a aprovação do administrador.")
                st.info("Você será notificado por email (ou contate seu admin).")
finally:
    db.close()

# Adicione um link para a página de Login
st.page_link("pages/0_Login.py", label="Já tem uma conta? Faça login")