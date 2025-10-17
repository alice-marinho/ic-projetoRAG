# Home.py

import streamlit as st

# Configurações da página (deve ser o primeiro comando Streamlit)
st.set_page_config(
    page_title="RAG Interdisciplinar - Início",
    page_icon="🧠",
    layout="wide"
)

# --- Conteúdo da Página Inicial ---

st.title("Bem-vindo ao Sistema RAG Interdisciplinar! 🧠")

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

st.header("Como Começar? 🤔")
st.info("É simples! Vá para a página de Chat para iniciar sua primeira conversa com a IA.", icon="👇")

# Botão grande e chamativo para ir para a página de chat
st.page_link(
    "pages/chat.py",
    label="Começar a Conversar Agora!",
    icon="💬",
    use_container_width=True
)

st.markdown("---")
st.write("Desenvolvido como uma ferramenta de auxílio acadêmico.")