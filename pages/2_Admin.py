import streamlit as st
from backend.auth import user_service
from backend.database import UserRole
from backend.database.database import SessionLocal
from backend.services.email_service import send_approval_email

# --- Configuração da Página (DEVE ser o primeiro comando Streamlit) ---
st.set_page_config(page_title="Gerenciar Usuários", layout="wide")

# --- CSS Personalizado para Alinhamento e Beleza ---
st.markdown("""
<style>
    /* Centraliza verticalmente o conteúdo das colunas dentro dos containers */
    div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"] {
        align-items: center;
    }
    /* Ajuste fino para cards */
    div[data-testid="stBlockContainer"] {
        padding-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# --- Portão de Autenticação ---
if not st.session_state.get("authenticated", False):
    st.error("🔒 Acesso negado. Faça login pela página principal.")
    st.stop()

# --- Portão de Autorização ---
role = st.session_state.get("user_role")
if role not in ["admin", "super_admin"]:
    st.error("🚫 Acesso negado. Você não tem permissão de Admin.")
    st.stop()

st.title("👥 Gerenciamento de Usuários")

# Conexão com Banco
db = SessionLocal()

try:
    # Busca todos os usuários uma vez
    all_users = user_service.get_all_users(db)
    role_options = [r.name for r in UserRole]

    # --- Filtros e Pesquisa ---
    col_search, _ = st.columns([1, 2])
    with col_search:
        search_query = st.text_input("🔍 Buscar usuário por nome ou email", placeholder="Digite para filtrar...").lower()

    # Filtra a lista baseada na busca
    filtered_users = [
        u for u in all_users
        if search_query in u.name.lower() or search_query in u.email.lower()
    ]

    # Separa em grupos
    pending_users = [u for u in filtered_users if not u.is_active]

    # Lógica de quem pode ver quem (Super Admin vê todos, Admin não vê Super Admin)
    if st.session_state["user_role"] == UserRole.super_admin.name:
        active_users = [u for u in filtered_users if u.is_active and u.role != UserRole.super_admin]
    else:
        active_users = [u for u in filtered_users if u.is_active and u.role.name not in ["super_admin", "admin"]]

    # --- LAYOUT EM ABAS ---
    tab_active, tab_pending = st.tabs(
        [f"✅ Usuários Ativos ({len(active_users)})", f"⏳ Pendentes ({len(pending_users)})"])

    # ------------------------------------------------------------------
    # ABA 1: USUÁRIOS ATIVOS
    # ------------------------------------------------------------------
    with tab_active:
        if not active_users:
            st.info("Nenhum usuário ativo encontrado.")
        else:
            for user in active_users:
                # Cria um container visual (Card)
                with st.container(border=True):
                    # Layout Responsivo:
                    # [Avatar/Info] [Role Select] [Ações]
                    c_info, c_role, c_actions = st.columns([0.45, 0.25, 0.3])

                    with c_info:
                        # UX: Nome em destaque, email discreto embaixo
                        st.markdown(f"**{user.name}**")
                        st.caption(f"📧 {user.email}")

                    with c_role:
                        # Selectbox sem label visível para economizar espaço vertical
                        key = f"role_act_{user.id}"
                        new_role_name = st.selectbox(
                            "Alterar Cargo",
                            options=role_options,
                            index=role_options.index(user.role.name),
                            key=key,
                            label_visibility="collapsed"  # Esconde o label "Alterar Cargo" visualmente
                        )

                    with c_actions:
                        # Colocamos os botões lado a lado para economizar altura
                        b_col1, b_col2 = st.columns(2)

                        with b_col1:
                            if st.button("💾 Salvar", key=f"upd_{user.id}", use_container_width=True):
                                new_role = UserRole[new_role_name]
                                user_service.update_user_role_and_status(db, user.id, new_role, True)
                                st.toast(f"Usuário {user.name} atualizado!", icon="✅")
                                st.rerun()

                        with b_col2:
                            # Botão de bloquear (Perigoso = vermelho)
                            if st.button("🚫 Bloquear", type="primary", key=f"blk_{user.id}", use_container_width=True):
                                user_service.update_user_role_and_status(db, user.id, user.role, False)
                                st.toast(f"Usuário {user.name} bloqueado!", icon="🔒")
                                st.rerun()

    # ------------------------------------------------------------------
    # ABA 2: PENDENTES
    # ------------------------------------------------------------------
    with tab_pending:
        if not pending_users:
            st.success("Tudo limpo! Nenhuma aprovação pendente.")
        else:
            for user in pending_users:
                with st.container(border=True):
                    c_info, c_role, c_btn = st.columns([0.5, 0.25, 0.25])

                    with c_info:
                        st.markdown(f"**{user.name}** *(Solicitado)*")
                        st.caption(f"📧 {user.email}")

                    with c_role:
                        key = f"role_pend_{user.id}"
                        new_role_name = st.selectbox(
                            "Definir Cargo",
                            options=role_options,
                            index=role_options.index(user.role.name),
                            key=key,
                            label_visibility="collapsed"
                        )

                    with c_btn:
                        # Botão de Aprovação
                        if st.button("✅ Aprovar", key=f"appr_{user.id}", type="primary", use_container_width=True):

                            # 1. Atualiza no Banco
                            new_role = UserRole[new_role_name]
                            user_service.update_user_role_and_status(db, user.id, new_role, True)

                            # 2. Envia o Email (Feedback visual)
                            with st.spinner("Enviando email de boas-vindas..."):
                                enviou = send_approval_email(user.email, user.name)

                            if enviou:
                                st.toast(f"Usuário aprovado e notificado por email!", icon="📧")
                            else:
                                st.warning("Usuário aprovado, mas houve erro ao enviar o email.")

                            st.balloons()
                            st.rerun()
finally:
    db.close()