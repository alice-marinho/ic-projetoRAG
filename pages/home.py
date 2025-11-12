# Home.py

import streamlit as st


st.set_page_config(
    page_title="RAG Interdisciplinar - Início",
    page_icon="🧠",
    layout="wide"
)


is_authenticated = st.session_state.get("authenticated", False)

if is_authenticated:
    st.title("Bem-vindo de volta!")
    st.info("Vá para a página de Chat para iniciar sua nova conversa.")


    st.page_link(
        "pages/1_Chat.py",
        label="Começar a Conversar Agora!",
        icon="💬",
        use_container_width=True
    )
else:
    st.title("Bem-vindo ao Sistema")
    st.write("Faça seu Login ou cadastro para iniciar a conversa!")

    col1, col2 = st.columns([0.8, 0.2])
    with col2:
        if st.button("Fazer Login", use_container_width=True):
            st.switch_page("pages/0_Login.py")

st.divider()

st.title("InterChat! 🧠")

st.markdown("""
Esta ferramenta foi desenvolvida para revolucionar a maneira como exploramos o conhecimento acadêmico. 
Utilizando técnicas avançadas de **RAG (Retrieval-Augmented Generation)**, nosso sistema analisa um banco de dados de planos de aula e documentos para fornecer respostas precisas e criar conteúdo educacional inovador.
""")

st.header("O que esta ferramenta faz? 🚀")
st.markdown("""
- **Respostas Baseadas em Contexto:** Faça perguntas sobre ementas, conteúdos programáticos e outros detalhes dos documentos, e receba respostas baseadas exclusivamente nos arquivos fornecidos.
- **Geração de Atividades Interdisciplinares:** Peça para criar projetos, provas e atividades que conectam diferentes disciplinas, promovendo uma visão unificada do conhecimento.
- **Chat Inteligente com Memória:** Cada conversa é uma sessão única. O sistema lembra o histórico do seu chat para fornecer respostas mais contextuais e relevantes.
""")



st.markdown("---")
st.write("Desenvolvido como uma ferramenta de auxílio acadêmico.")