import streamlit as st
from sqlalchemy import text

from backend.database.database import sqlal_engine
from backend.src.process_question import ProcessQuestion
from backend.src.rag.chat.conversation_history import SessionManager
from langchain.schema import HumanMessage, AIMessage
import time

# --- Configuração inicial ---
st.set_page_config(page_title="Formulário de Disciplinas", layout="wide")
st.title("📋 Formulário de Metadados de Disciplinas")

# --- Inicializa as classes ---
if "session_manager" not in st.session_state:
    st.session_state.session_manager = SessionManager()
if "process_question_instance" not in st.session_state:
    st.session_state.process_question_instance = ProcessQuestion()

session_manager = st.session_state.session_manager
pq = st.session_state.process_question_instance

# --- Busca registros do banco ---
with sqlal_engine.connect() as conn:
    result = conn.execute(text("SELECT id, content, metadata_json FROM parent_documents"))
    rows = result.fetchall()

dados = [
    {
        "id": row.id,
        "content": row.content,
        **row.metadata_json
    }
    for row in rows
]

# --- Seleção de curso ---
cursos = sorted(set(d["curso"] for d in dados if "curso" in d))
curso_escolhido = st.selectbox("🎓 Escolha o curso:", [""] + cursos)

if curso_escolhido:
    # --- Seleção de período ---
    periodos = sorted(set(
        d["periodo"] for d in dados if d.get("curso") == curso_escolhido
    ))
    periodo_escolhido = st.selectbox("📆 Escolha o período:", [""] + periodos)

    if periodo_escolhido:
        # --- Seleção de disciplinas ---
        qtd_disciplinas = st.number_input(
            "Quantas disciplinas você quer combinar?",
            min_value=2,
            max_value=10,
            value=2,
            step=1
        )

        componentes_filtrados = sorted(set(
            d["componente"] for d in dados
            if d.get("curso") == curso_escolhido and d.get("periodo") == periodo_escolhido
        ))

        st.markdown("### 📚 Escolha as disciplinas")
        componentes_escolhidos = st.multiselect(
            "Selecione as disciplinas (mínimo 2):",
            componentes_filtrados,
            max_selections=qtd_disciplinas
        )

        if len(componentes_escolhidos) >= qtd_disciplinas:
            st.success(f"✅ {len(componentes_escolhidos)} disciplinas selecionadas.")

            itens_selecionados = [
                d for d in dados if
                d.get("curso") == curso_escolhido and
                d.get("periodo") == periodo_escolhido and
                d.get("componente") in componentes_escolhidos
            ]

            for item in itens_selecionados:
                with st.expander(f"📘 {item['componente']}"):
                    st.json({
                        "curso": item["curso"],
                        "periodo": item["periodo"],
                        "componente": item["componente"],
                        "codigo": item.get("codigo"),
                        "source": item.get("source"),
                        "doc_id": item.get("doc_id")
                    })
                    st.write(item["content"])

            if st.button("🚀 Enviar todas ao Chat"):
                # Armazena todos os conteúdos e metadados na sessão
                session_manager = st.session_state.session_manager
                current_user_id = st.session_state["user_id"]

                new_session_id = session_manager.create_session(
                    user_id=current_user_id,
                    name="Chat Interdisciplinar",
                    fixed_context=itens_selecionados
                )

                st.session_state.transition_session_id = new_session_id
                if "from_form" in st.session_state:
                    del st.session_state["from_form"]
                if "selected_chunks" in st.session_state:
                    del st.session_state["selected_chunks"]

                st.success("Sessão criada! Iniciando o chat interdisciplinar...")
                time.sleep(1)

                st.switch_page("pages/1_Chat.py")