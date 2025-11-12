# Em pages/2_Admin.py
import streamlit as st
from auth import user_service
from database.database import SessionLocal
from database.models import UserRole  # Importe o Enum

# --- Portão de Autenticação (Obrigatório) ---
if not st.session_state.get("authenticated", False):
    st.error("🔒 Acesso negado. Faça login pela página principal.")
    st.stop()

# --- Portão de Autorização (Obrigatório) ---
role = st.session_state.get("user_role")
if role not in ["admin", "super_admin"]:
    st.error("🚫 Acesso negado. Você não tem permissão de Admin para ver esta página.")
    st.stop()


st.set_page_config(page_title="Gerenciar Usuários", layout="wide")
st.title("Painel de Gerenciamento de Usuários")

db = SessionLocal()
try:
    all_users = user_service.get_all_users(db)

    # Lista de nomes de roles para o selectbox
    role_options = [r.name for r in UserRole]

    # 1. Tabela de Usuários Pendentes
    st.header("Usuários Pendentes de Aprovação")
    pending_users = [user for user in all_users if not user.is_active]

    if not pending_users:
        st.info("Nenhum usuário pendente de aprovação.")
    else:
        for user in pending_users:
            with st.container(border=True):
                col1, col2, col3 = st.columns([2, 2, 1])
                col1.text(f"Nome: {user.name}")
                col2.text(f"Email: {user.email}")

                with col3:
                    # Chave única para o selectbox
                    key = f"role_select_{user.id}"
                    new_role_name = st.selectbox(
                        "Definir Nível:",
                        options=role_options,
                        index=role_options.index(user.role.name),  # Default
                        key=key
                    )

                if st.button("✅ Aprovar Usuário", key=f"approve_{user.id}"):
                    new_role = UserRole[new_role_name]  # Converte string (ex: "admin") para Enum
                    user_service.update_user_role_and_status(db, user.id, new_role, True)
                    st.success(f"Usuário {user.email} aprovado como {new_role_name}!")
                    st.rerun()  # Recarrega a página

    # 2. Tabela de Usuários Ativos (para gerenciar)
    st.header("Gerenciar Usuários Ativos")

    if st.session_state["user_role"] == UserRole.super_admin:
        active_users = [user for user in all_users if user.is_active and user.role != UserRole.super_admin]
    else:
        active_users = [user for user in all_users if
                        user.is_active and user.role not in [UserRole.super_admin, UserRole.admin]]

    if not active_users:
        st.info("Nenhum usuário ativo para gerenciar.")
    else:
        for user in active_users:
            with st.container(border=True):
                col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                col1.text(f"Nome: {user.name}")
                col2.text(f"Email: {user.email}")

                with col3:
                    key = f"role_active_select_{user.id}"
                    new_role_name = st.selectbox(
                        "Nível de Acesso:",
                        options=role_options,
                        index=role_options.index(user.role.name),
                        key=key
                    )

                with col4:
                    if st.button("Atualizar", key=f"update_{user.id}"):
                        new_role = UserRole[new_role_name]
                        user_service.update_user_role_and_status(db, user.id, new_role, True)
                        st.success(f"Usuário {user.email} atualizado para {new_role_name}!")
                        st.rerun()

                    if st.button("Bloquear", type="primary", key=f"deactivate_{user.id}"):
                        user_service.update_user_role_and_status(db, user.id, user.role,
                                                                 False)  # Mantém o role, mas desativa
                        st.warning(f"Usuário {user.email} foi bloqueado.")
                        st.rerun()
finally:
    db.close()