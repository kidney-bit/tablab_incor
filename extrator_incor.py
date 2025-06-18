import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import re
import os

st.set_page_config(layout="wide")
st.title("📄 Extrator de Exames - InCor HCFMUSP (Local e Automático)")

# Caminho base dos PDFs
PASTA_PDFS = r"D:\usuarios\enf51\Desktop\karol\pdfs"

# Dicionário de regex para cada exame
PADROES_EXAMES = {
    "pH": r"pH\s*:?\s*[\n ]*(\d{1,2}[.,]\d{1,2})",
    "pCO2": r"pCO2\s*:?\s*[\n ]*(\d{1,2}[.,]\d{1,2})",
    "pO2": r"pO2\s*:?\s*[\n ]*(\d{1,3}[.,]\d{1,2})",
    "Saturacao O2": r"Satur[açc][aã]o\s*O2\s*:?\s*[\n ]*(\d{1,3}[.,]\d{1,2})",
    "Bicarbonato": r"Bicarbonato\s*:?\s*(?:[\d,\.\sa-zA-Zàáéí]*)?(\d{1,2}[.,]\d{1,2})\s*mmol",
    "BE": r"BE\s*:?\s*([\+\-]?\d{1,2}[.,]\d{1,2})\s*mmol",
    "Hemoglobina": r"Hemoglobina\s*:?\s*(?:.*?\n){0,2}?([\d,\.]+)\s*g/dL",
    "Leucócitos": r"Leuc[oó]citos\s*:?\s*(?:.*?\n)?([\d\.]+)\s*/mm",
    "Plaquetas": r"(?:Plaquetas|CONTAGEM DE PLAQUETAS)[\s\S]*?(\d{2,6})\s*/mm",
    "Creatinina": r"CREATININA[\s\S]*?([\d,\.]+)\s*mg/dL",
    "Ureia": r"UREIA[\s\S]*?([\d,\.]+)\s*mg/dL",
    "Magnésio": r"MAGN[\u00c9E]SIO[\s\S]*?([\d,\.]+)\s*mg/dL",
    "Sódio": r"S[\u00d3O]DIO[\s\S]*?([\d,\.]+)\s*mEq",
    "Potássio": r"POT[\u00c1A]SSIO[\s\S]*?([\d,\.]+)\s*mEq",
    "Cálcio Iônico": r"C[\u00c1A]LCIO I[\u00d4O]NIZADO[\s\S]*?([\d,\.]+)\s*mMol",
    "Lactato": r"LACTATO[\s\S]*?([\d,\.]+)\s*mg/dL",
    "PCR": r"PROTE[\u00cdI]NA\s+C\s+REATIVA.*?([\d,\.]+)\s*mg/L",
}

def extrair_texto_pdf(caminho_pdf):
    with fitz.open(caminho_pdf) as doc:
        return "\n".join(p.get_text() for p in doc)

def extrair_nome(texto):
    match = re.search(r"Paciente\s*[:\.]{1,2}\s*(.+)", texto)
    return match.group(1).strip().title() if match else "Paciente Desconhecido"

def extrair_data_hora(texto):
    match = re.search(r"Coleta.*?:\s*(\d{2}/\d{2}/\d{4})\s*(\d{2}:\d{2})?", texto)
    if match:
        return match.group(1), match.group(2) if match.group(2) else ""
    return "", ""

def extrair_exames(texto):
    resultados = {}
    for exame, padrao in PADROES_EXAMES.items():
        match = re.search(padrao, texto, flags=re.IGNORECASE | re.DOTALL)
        resultados[exame] = match.group(1).replace(",", ".") if match else ""
    return resultados

# Listar subpastas com PDFs
subpastas = [p for p in os.listdir(PASTA_PDFS) if os.path.isdir(os.path.join(PASTA_PDFS, p))]
subpasta = st.selectbox("📁 Escolha a subpasta de PDFs:", subpastas if subpastas else ["(nenhuma encontrada)"])

if subpasta and subpasta != "(nenhuma encontrada)":
    caminho = os.path.join(PASTA_PDFS, subpasta)
    arquivos = [f for f in os.listdir(caminho) if f.lower().endswith(".pdf")]

    if arquivos:
        if st.button("🚀 Extrair Dados dos PDFs"):
            dados = []

            for nome_arquivo in arquivos:
                try:
                    caminho_arquivo = os.path.join(caminho, nome_arquivo)
                    texto = extrair_texto_pdf(caminho_arquivo)
                    paciente = extrair_nome(texto)
                    data, hora = extrair_data_hora(texto)
                    exames = extrair_exames(texto)
                    dados.append({"Paciente": paciente, "Data": data, "Hora": hora, **exames})
                except Exception as e:
                    st.error(f"Erro ao processar {nome_arquivo}: {e}")

            if dados:
                df = pd.DataFrame(dados)
                st.success("✅ Extração concluída com sucesso!")
                st.dataframe(df, use_container_width=True)
                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button("📥 Baixar CSV", csv, file_name="exames_incor.csv", mime="text/csv")
    else:
        st.warning("⚠️ Nenhum PDF encontrado na pasta selecionada.")
