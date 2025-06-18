import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import re
import tempfile
import os

st.set_page_config(layout="wide")
st.title("📎 Arraste PDFs do InCor para extração tabulada")

uploaded_files = st.file_uploader(
    "🧾 Arraste um ou mais PDFs de exames (InCor):",
    type=["pdf"],
    accept_multiple_files=True
)

exames_prioritarios = [
    "Hemoglobina", "Leucócitos", "Plaquetas",
    "Proteína C reativa", "Ureia", "Creatinina",
    "Sódio", "Potássio", "Fósforo", "Cálcio",
    "pH", "Bicarbonato", "Base Excess", "INR"
]

sinonimos = {
    "BE": "Base Excess",
    "BIC": "Bicarbonato",
    "HCO3": "Bicarbonato"
}

def padronizar_nome_exame(nome):
    nome = nome.strip().capitalize()
    return sinonimos.get(nome.upper(), nome)

def extrair_exames(texto):
    exames = {}
    linhas = texto.splitlines()
    for i, linha in enumerate(linhas):
        linha = linha.strip()

        if "CONTAGEM DE PLAQUETAS" in linha.upper():
            for j in range(i+1, min(i+5, len(linhas))):
                m = re.search(r"([\d]{4,})\s*/mm³", linhas[j])
                if m:
                    exames["Plaquetas"] = m.group(1)
                    break

        if re.match(r"^BE\s*[:\-]?\s*[-\d,\.]+", linha):
            exames["Base Excess"] = linha.split(":")[-1].strip().replace(",", ".")
        if "Bicarbonato" in linha:
            m = re.search(r"([\d,\.]+)", linha)
            if m:
                exames["Bicarbonato"] = m.group(1).replace(",", ".")
        if "pH" in linha:
            m = re.search(r"([\d,\.]+)", linha)
            if m:
                exames["pH"] = m.group(1).replace(",", ".")

        match = re.search(r"([A-ZÁÉÍÓÚÃÕÂÊÎÔÛÇa-z0-9 \-/]{3,}?)\s*[:\-]?\s*([-\d,\.]+)", linha)
        if match:
            nome = padronizar_nome_exame(match.group(1))
            valor = match.group(2).replace(",", ".")
            if nome.lower() not in ["valor de referência", "referência", "resultado"]:
                exames[nome] = valor
    return exames

def extrair_info(texto):
    nome_match = re.search(r"Paciente.*?:?\s*(.+)", texto)
    nome = nome_match.group(1).strip().splitlines()[0] if nome_match else "Desconhecido"
    data_hora_match = re.search(r"Liberado em \((\d{2}/\d{2}/\d{4}) (\d{2}:\d{2})\)", texto)
    data = data_hora_match.group(1) if data_hora_match else ""
    hora = data_hora_match.group(2) if data_hora_match else ""
    exames = extrair_exames(texto)
    return {
        "Paciente": nome,
        "Data": data,
        "Hora": hora,
        **exames
    }

if uploaded_files:
    resultados = []

    for file in uploaded_files:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
            tmpfile.write(file.read())
            tmpfile_path = tmpfile.name

        doc = fitz.open(tmpfile_path)
        texto = "\n".join(page.get_text() for page in doc)
        doc.close()
        os.remove(tmpfile_path)

        resultados.append(extrair_info(texto))

    df = pd.DataFrame(resultados)

    colunas_fixas = ["Paciente", "Data", "Hora"]
    colunas_exames = [c for c in exames_prioritarios if c in df.columns]
    outras = sorted([c for c in df.columns if c not in colunas_fixas + colunas_exames])
    df = df[colunas_fixas + colunas_exames + outras]

    st.success(f"✅ {len(df)} PDFs processados.")
    st.dataframe(df, use_container_width=True)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Baixar CSV", csv, file_name="exames_por_pdf.csv", mime="text/csv")
