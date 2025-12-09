import os
import sys
import time
import streamlit as st
from pathlib import Path
from sqlalchemy import text

# --- Configuração de Path ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from backend.src.config.config import DOCS_DIR
from backend.src.utils.data_processing import processing_data, clear_vector_database
from backend.database.database import sqlal_engine

# --- Configuração da Página ---
st.set_page_config(page_title="Admin", layout="wide")
st.title("🔑 Painel de Administração")

DOCS_PATH = DOCS_DIR
DOCS_PATH.mkdir(parents=True, exist_ok=True)


# ==============================================================================
# FUNÇÕES AUXILIARES (Busca dados para visualização e verificação)
# ==============================================================================
def get_database_status():
    """
    Busca metadados do banco para:
    1. Listar cursos e matérias.
    2. Listar arquivos PDF que já foram processados.
    """
    try:
        with sqlal_engine.connect() as conn:
            # Busca o JSON de metadados
            result = conn.execute(text("SELECT metadata_json FROM parent_documents"))
            rows = result.fetchall()

        processed_files = set()
        structure = {}  # { "Nome Curso": ["Matéria A", "Matéria B"] }

        for row in rows:
            meta = row[0]  # metadata_json
            if not meta: continue

            # 1. Coleta arquivo de origem
            if "original_source_pdf" in meta:
                # Normaliza pegando apenas o nome do arquivo (sem caminho completo)
                f_name = os.path.basename(meta["original_source_pdf"])
                processed_files.add(f_name)

            # 2. Monta estrutura Curso > Componente
            curso = meta.get("curso", "Sem Curso Definido")
            componente = meta.get("componente", "Sem Componente")

            if curso not in structure:
                structure[curso] = set()
            structure[curso].add(componente)

        return structure, processed_files
    except Exception as e:
        st.error(f"Erro ao conectar no banco para leitura: {e}")
        return {}, set()


# Carrega dados atuais
db_structure, db_files = get_database_status()

# Verifica arquivos na pasta física
folder_files = set(f.name for f in DOCS_PATH.glob("*.pdf"))

# Lógica de Aviso de Mudança
new_files = folder_files - db_files  # Arquivos na pasta mas não no banco
missing_files = db_files - folder_files  # Arquivos no banco mas não na pasta (deletados manualmente?)
needs_update = len(new_files) > 0 or len(missing_files) > 0

# ==============================================================================
# INTERFACE
# ==============================================================================

tab_db, tab_files = st.tabs(["🗄️ Banco de Dados", "📄 Gerenciar Arquivos PDF"])

# --- ABA 1: BANCO DE DADOS ---
with tab_db:
    # --- AVISO INTELIGENTE ---
    if needs_update:
        st.warning("⚠️ **Atenção: Mudanças detectadas!** O banco de dados está desatualizado em relação aos arquivos.",
                   icon="⚠️")
        col_warn1, col_warn2 = st.columns(2)
        with col_warn1:
            if new_files:
                st.write("**Novos arquivos encontrados:**")
                for f in new_files: st.caption(f"📄 {f}")
        with col_warn2:
            if missing_files:
                st.write("**Arquivos faltando (estão no banco mas não na pasta):**")
                for f in missing_files: st.caption(f"❌ {f}")
        st.markdown("---")
    else:
        st.success("✅ O banco de dados está sincronizado com a pasta de arquivos.", icon="✅")

    col_proc, col_viz = st.columns([0.4, 0.6])

    # Coluna Esquerda: Ações
    with col_proc:
        st.header("Ações")
        st.write("Processamento total dos documentos.")

        btn_label = "🔄 Atualizar Banco Agora" if needs_update else "Processar e Adicionar ao Banco"
        btn_type = "primary" if needs_update else "secondary"

        if st.button(btn_label, type=btn_type, use_container_width=True):
            with st.spinner("Lendo arquivos, extraindo metadados e vetorizando..."):
                try:
                    processing_data(reload="s")
                    st.success("Banco vetorial atualizado com sucesso!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")

        st.divider()

        with st.expander("🗑️ Zona de Perigo (Limpeza Total)"):
            st.warning("Isso apaga TUDO do banco vetorial.")
            if st.button("Deletar Todo o Conteúdo Vetorial", type="primary"):
                with st.spinner("Limpando..."):
                    if clear_vector_database():
                        st.success("Limpo!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Erro ao limpar.")

    # Coluna Direita: Visualização
    with col_viz:
        st.header("Conteúdo Salvo")
        st.caption("Cursos e disciplinas identificados no banco de dados.")

        if not db_structure:
            st.info("O banco de dados parece estar vazio.")
        else:
            # Mostra os cursos
            for curso, materias in sorted(db_structure.items()):
                with st.expander(f"🎓 {curso} ({len(materias)} disciplinas)"):
                    for mat in sorted(materias):
                        st.markdown(f"- 📘 {mat}")

# --- ABA 2: ARQUIVOS ---
with tab_files:
    st.header("Gerenciamento de Arquivos")

    # Upload
    with st.container(border=True):
        st.subheader("📤 Upload de Novos Documentos")
        uploaded_files = st.file_uploader("Arraste PDFs aqui", type="pdf", accept_multiple_files=True)

        if uploaded_files:
            saved_count = 0
            for uploaded_file in uploaded_files:
                file_path = DOCS_PATH / uploaded_file.name
                # Evita salvar se já existe para não gastar IO desnecessário, ou sobrescreve
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                saved_count += 1

            if saved_count > 0:
                st.success(f"{saved_count} arquivos salvos! Vá para a aba 'Banco de Dados' para processá-los.")
                time.sleep(1)
                st.rerun()

    st.divider()

    # Listagem e Exclusão Segura
    st.subheader(f"📂 Arquivos em `{DOCS_PATH.name}`")

    pdf_files = list(DOCS_PATH.glob("*.pdf"))

    if not pdf_files:
        st.info("A pasta está vazia.")
    else:
        # Cabeçalho da tabela
        col_h1, col_h2, col_h3 = st.columns([0.6, 0.2, 0.2])
        col_h1.markdown("**Nome do Arquivo**")
        col_h2.markdown("**Status**")
        col_h3.markdown("**Ação**")
        st.divider()

        for file_path in pdf_files:
            c1, c2, c3 = st.columns([0.6, 0.2, 0.2])

            with c1:
                st.text(file_path.name)

            with c2:
                # Verifica se este arquivo específico está no banco
                if file_path.name in db_files:
                    st.caption("✅ No Banco")
                else:
                    st.caption("⚠️ Não Processado")

            with c3:
                # --- DELETE SEGURO (POPOVER) ---
                # O botão de deletar fica escondido dentro do menu "🗑️"
                with st.popover("🗑️", use_container_width=True):
                    st.write(f"Tem certeza que deseja apagar **{file_path.name}**?")
                    st.caption("Isso não remove do banco automaticamente, você precisará reprocessar depois.")

                    if st.button("Sim, apagar", key=f"conf_del_{file_path.name}", type="primary"):
                        try:
                            os.remove(file_path)
                            st.toast(f"Arquivo deletado.")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro: {e}")