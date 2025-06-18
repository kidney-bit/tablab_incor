import streamlit as st
import pandas as pd
import re

st.set_page_config(layout="wide")
st.title("📋 Extração de Exames via Colagem de PDFs (InCor)")

texto = st.text_area("Cole abaixo o conteúdo de múltiplos PDFs (Command+A, C, V):", height=1000, max_chars=None)

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

def limpar_texto(linha):
    return linha.replace("Resultado", "").replace(":", "").strip()

def padronizar_nome_exame(nome):
    nome = nome.strip().capitalize()
    return sinonimos.get(nome.upper(), nome)

def extrair_coletas(bloco, nome_paciente):
    padrao_data_hora = r"Liberado em \((\d{2}/\d{2}/\d{4}) (\d{2}:\d{2})\)"
    matches = re.findall(padrao_data_hora, bloco)
    if not matches:
        matches = [("", "")]

    exames = extrair_exames(bloco)
    coletas = []
    for data, hora in matches:
        coletas.append({
            "Paciente": nome_paciente,
            "Data": data,
            "Hora": hora,
            **exames
        })
    return coletas

def extrair_exames(texto):
    exames = {}

    def pegar_valor(label, linhas, idx):
        match = re.search(r"([\d\-,]+)", linhas[idx+1]) if idx+1 < len(linhas) else None
        return match.group(1).replace(",", ".") if match else None

    linhas = texto.splitlines()
    for i, linha in enumerate(linhas):
        linha = linha.strip()

        # Plaquetas fora do padrão
        if "CONTAGEM DE PLAQUETAS" in linha.upper():
            for j in range(i+1, min(i+5, len(linhas))):
                m = re.search(r"([\d]{4,})\s*/mm³", linhas[j])
                if m:
                    exames["Plaquetas"] = m.group(1)
                    break

        # Gasometria / BE / bicarbonato etc.
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

        # Regex geral
        match = re.search(r"([A-ZÁÉÍÓÚÃÕÂÊÎÔÛÇa-z0-9 \-/]{3,}?)\s*[:\-]?\s*([-\d,\.]+)", linha)
        if match:
            nome = padronizar_nome_exame(match.group(1))
            valor = match.group(2).replace(",", ".")
            if nome.lower() not in ["valor de referência", "referência", "resultado"]:
                exames[nome] = valor

    return exames

if st.button("🔍 Processar"):
    if not texto.strip():
        st.warning("Por favor, cole algum texto para continuar.")
    else:
        # Separar blocos por paciente
        blocos_pacientes = re.split(r"(?:Paciente\s*:?|Nome\s*:?|Paciente\s+-\s+)", texto, flags=re.IGNORECASE)[1:]
        blocos = [("Paciente " + blocos_pacientes[i] + blocos_pacientes[i+1]) for i in range(0, len(blocos_pacientes)-1, 2)]

        todas_coletas = []

        for bloco in blocos:
            nome_match = re.search(r"Paciente.*?:?\s*(.+)", bloco)
            nome = nome_match.group(1).strip().splitlines()[0] if nome_match else "Desconhecido"
            coletas = extrair_coletas(bloco, nome)
            todas_coletas.extend(coletas)

        df = pd.DataFrame(todas_coletas)

        colunas_fixas = ["Paciente", "Data", "Hora"]
        colunas_exames = [c for c in exames_prioritarios if c in df.columns]
        outras = sorted([c for c in df.columns if c not in colunas_fixas + colunas_exames])
        df = df[colunas_fixas + colunas_exames + outras]

        st.success(f"✅ {len(df)} coletas processadas.")
        st.dataframe(df, use_container_width=True)

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Baixar CSV", csv, file_name="exames_colados.csv", mime="text/csv")
