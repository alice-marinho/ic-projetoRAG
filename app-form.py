import streamlit as st
import pandas as pd

from src.llm import LLMClient
from src.rag import retrieve_context
from searcher.course_service import DataService
from config.config import CLEAN_CSV


class StreamlitApp:
    def __init__(self, caminho_csv=CLEAN_CSV):
        self.service = DataService(caminho_csv)
        self._setup_page_config()

    def _setup_page_config(self):
        st.set_page_config(
            page_title="Sistema de Consulta Acadêmica",
            page_icon="🎓",
            layout="wide"
        )
        st.title("📚 Sistema de Consulta de Componentes Curriculares")

    def run(self):
        self._show_course_selection()

        if hasattr(st.session_state, 'curso'):
            self._show_semester_selection()

        if hasattr(st.session_state, 'semestre'):
            self._show_component_selection()

        if hasattr(st.session_state, 'componentes'):
            self._show_results()

    def _show_course_selection(self):
        st.header("1. Selecione o Curso")
        cursos = self.service.listar_cursos()
        curso = st.selectbox(
            "Escolha um curso:",
            cursos,
            index=None,
            placeholder="Selecione um curso..."
        )
        if curso:
            st.session_state.curso = curso

    def _show_semester_selection(self):
        st.header("2. Selecione o Semestre/Ano")
        semestres = self.service.listar_periodo(st.session_state.curso)
        semestre = st.selectbox(
            f"Semestres disponíveis para {st.session_state.curso}:",
            semestres,
            index=None,
            placeholder="Selecione um período..."
        )
        if semestre:
            st.session_state.semestre = semestre

    def _show_component_selection(self):
        st.header("3. Selecione os Componentes")
        componentes = self.service.listar_componentes_por_curso_e_periodo(
            st.session_state.curso,
            st.session_state.semestre
        )

        selecionados = st.multiselect(
            f"Componentes disponíveis em {st.session_state.semestre}:",
            componentes,
            placeholder="Selecione um ou mais componentes..."
        )

        if selecionados:
            st.session_state.componentes = selecionados
            if st.button("Consultar Informações"):
                st.session_state.consultar = True

    def _show_results(self):
        if getattr(st.session_state, 'consultar', False):
            st.header("📝 Resultados da Consulta")

            with st.spinner("Processando sua consulta..."):
                resultados = self._enviar_llm(
                    st.session_state.curso,
                    st.session_state.semestre,
                    st.session_state.componentes
                )

            if isinstance(resultados, str):
                st.warning(resultados)
            elif resultados:
                self._display_results(resultados)

    def _display_results(self, resultados):
        st.success("Consulta realizada com sucesso!")

        # Mostra os resultados em abas
        tabs = st.tabs([f"Componente {i + 1}" for i in range(len(resultados))])

        for i, (tab, doc) in enumerate(zip(tabs, resultados)):
            with tab:
                if hasattr(doc, 'page_content'):
                    content = doc.page_content
                    metadata = doc.metadata
                else:
                    content = str(doc)
                    metadata = {}

                st.subheader(st.session_state.componentes[i])
                st.markdown("### Conteúdo Principal")
                st.text_area("", value=content, height=200, key=f"content_{i}")

                if metadata:
                    with st.expander("Metadados"):
                        st.json(metadata)

                # Botão para gerar resumo com LLM
                if st.button(f"Gerar Resumo com IA", key=f"btn_{i}"):
                    with st.spinner("Gerando resumo..."):
                        prompt = f"""
                        Resuma o seguinte componente curricular de forma didática:
                        Curso: {st.session_state.curso}
                        Período: {st.session_state.semestre}
                        Componente: {st.session_state.componentes[i]}

                        Conteúdo:
                        {content}
                        """
                        resumo = LLMClient().chat(prompt)
                        st.info(resumo)

    def _enviar_llm(self, curso: str, semestre: str, componentes: list) -> str | list[dict]:
        """Adaptação do seu método original para Streamlit"""
        dados_filtrados = self.service.df[
            (self.service.df["Curso"] == curso) &
            (self.service.df["Período Educacional"] == semestre) &
            (self.service.df["Componente curricular"].isin(componentes))
            ]

        if dados_filtrados.empty:
            return "Nenhum dado encontrado para os critérios selecionados."

        contexto = self._formatar_para_retriever(dados_filtrados)
        return retrieve_context(contexto, len(componentes))

    def _formatar_para_retriever(self, dados: pd.DataFrame) -> str:
        textos = []
        for _, row in dados.iterrows():
            texto = f"""
            Curso: {row['Curso']}
            Período: {row['Período Educacional']}
            Componente: {row['Componente curricular']}
            Descrição: {row.get('Descrição', 'Não informado')}
            """
            textos.append(texto)
        return "\n".join(textos)


# Para executar a aplicação
if __name__ == "__main__":
    app = StreamlitApp()
    app.run()