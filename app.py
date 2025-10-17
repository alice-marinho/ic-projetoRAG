import streamlit as st
import sys
import os
from langchain.schema import HumanMessage, AIMessage
#from main import ProcessQuestion
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))


pg = st.navigation([
    st.Page("pages/home.py", title="Home"),
    st.Page("pages/banco.py", title="Banco de Dados"),
    st.Page("pages/chat.py", title="ChatBot")
])
pg.run()

