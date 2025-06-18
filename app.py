# app.py - Interface unificada para o robô e o extrator

import streamlit as st
from robo_incor import executar_robo_incor
from extrator import executar_extrator_tabelado

st.set_page_config(page_title="tablab InCor", layout="wide")
st.title("🧪 tablab InCor")

# Menu lateral
aba = st.sidebar.radio("Escolha uma funcionalidade:", [
    "⬇️ Baixar PDFs dos pacientes",
    "📄 Extrair exames dos PDFs"
])

if aba == "⬇️ Baixar PDFs dos pacientes":
    executar_robo_incor()

elif aba == "📄 Extrair exames dos PDFs":
    executar_extrator_tabelado()
