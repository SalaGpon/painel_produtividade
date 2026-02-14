import streamlit as st
import pandas as pd
import os

# =========================================================
# CONFIGURAÇÃO AUTOMÁTICA DO CAMINHO (SEMPRE PEGA DA PASTA DO APP)
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CAMINHO_ARQUIVO = os.path.join(BASE_DIR, "base.xlsx")

# =========================================================
# FUNÇÃO PARA CARREGAR DADOS
# =========================================================

@st.cache_data
def carregar_dados():

    if not os.path.exists(CAMINHO_ARQUIVO):
        st.error(f"Arquivo não encontrado em: {CAMINHO_ARQUIVO}")
        st.stop()

    # Cabeçalho começa na linha 12
    df = pd.read_excel(CAMINHO_ARQUIVO, header=11)

    return df


# =========================================================
# INÍCIO DO APP
# =========================================================

st.set_page_config(layout="wide")
st.title("📊 Painel de Produtividade JVE.11")

df = carregar_dados()

# =========================================================
# TRATAMENTO DAS COLUNAS
# =========================================================

try:
    df["DATA"] = pd.to_datetime(df["Início Execução"], errors="coerce").dt.date
    df["TECNICO"] = df["Técnico Atribuído"]
    df["SA"] = df["Número SA"]
    df["STATUS"] = df["Estado"]

except Exception:
    st.error("Erro ao localizar colunas. Verifique os nomes no Excel.")
    st.write("Colunas encontradas no arquivo:")
    st.write(df.columns)
    st.stop()

# =========================================================
# FILTRAR APENAS STATUS VÁLIDOS
# =========================================================

df = df[
    df["STATUS"].isin([
        "Concluído com sucesso",
        "Concluído sem sucesso"
    ])
]

# =========================================================
# AGRUPAMENTO
# =========================================================

resumo = (
    df.groupby(["TECNICO", "DATA", "STATUS"])
    .size()
    .reset_index(name="TOTAL")
)

pivot = resumo.pivot_table(
    index=["TECNICO", "DATA"],
    columns="STATUS",
    values="TOTAL",
    fill_value=0
).reset_index()

pivot["TOTAL_GERAL"] = (
    pivot.get("Concluído com sucesso", 0)
    + pivot.get("Concluído sem sucesso", 0)
)

pivot["EFICACIA_%"] = (
    pivot.get("Concluído com sucesso", 0)
    / pivot["TOTAL_GERAL"]
    * 100
).round(1)

# =========================================================
# KPIs GERAIS
# =========================================================

col1, col2, col3 = st.columns(3)

total_sucesso = df[df["STATUS"] == "Concluído com sucesso"].shape[0]
total_sem = df[df["STATUS"] == "Concluído sem sucesso"].shape[0]
total_geral = total_sucesso + total_sem

col1.metric("Total Geral", total_geral)
col2.metric("Sucesso", total_sucesso)
col3.metric("Sem Sucesso", total_sem)

# =========================================================
# TABELA FINAL
# =========================================================

st.subheader("📋 Resultado por Técnico / Dia")

st.dataframe(pivot, use_container_width=True)
