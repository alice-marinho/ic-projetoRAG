import time

import streamlit as st

from utils.data_processing import processing_data

# === Seção 1: Banco de Dados ===
st.header("📁 Banco de Dados")
st.write(f"A base de dados contém os seguintes PPCs completos:\n"
         f"- Ensino médio com técnico em Informática\n"
         f"- Ensino médio com técnico em Eventos\n"
         f"\nHá algumas matérias destes PPCs na base de dados, entretanto ainda não está com toda grade curricular "
         f"completa"
         f"de dados."
         f"\n- ADS\n- Automação\n- Turismo")
if st.button("Refazer banco de dados"):
    with st.spinner("Processando documentos e reconstruindo base..."):


        try:
            st.warning("Essa ação pode demorar um pouco...")
            processing_data(reload="s")
            # time.sleep(20)
            st.success("Banco vetorial recriado com sucesso!")


        except Exception as e:
            st.error(f"Erro durante o processamento: {e}")