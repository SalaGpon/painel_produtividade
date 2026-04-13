#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BERTA — Painel Operacional do Supervisor v3.0
Telas: Producao Diaria | Repetidos | Infancia
Tema: Branco / Azul Marinho — CSS injetado no topo, keys fixas, sem bugs de tema
"""

import os
import re
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime
import streamlit as st

# =============================================================================
# 1. CONFIGURACAO DA PAGINA — primeira chamada obrigatoria
# =============================================================================

st.set_page_config(
    layout="wide",
    page_title="BERTA - Painel Operacional",
    page_icon="📡",
    initial_sidebar_state="expanded",
)

# =============================================================================
# 2. CSS GLOBAL — injetado UMA unica vez, antes de qualquer widget
#    Isso garante que o tema nao reseta ao mudar filtro ou tela
# =============================================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

/* Reset global */
html, body { margin: 0; padding: 0; }
* { font-family: 'Inter', sans-serif !important; box-sizing: border-box; }

/* Fundo branco em TODOS os containers do Streamlit */
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="block-container"],
.main, .block-container,
section.main > div,
div[data-testid="stVerticalBlock"] {
    background-color: #f5f7fa !important;
    color: #1a2332 !important;
}

/* Sidebar branca */
[data-testid="stSidebar"] {
    background-color: #ffffff !important;
    border-right: 1px solid #dde3ed !important;
}
[data-testid="stSidebar"] * { color: #1a2332 !important; }
[data-testid="stSidebar"] hr { border-color: #dde3ed !important; }

/* Inputs e selects */
[data-baseweb="select"] > div,
[data-baseweb="input"] > div {
    background-color: #ffffff !important;
    border-color: #dde3ed !important;
    color: #1a2332 !important;
}
[data-baseweb="select"] span,
[data-baseweb="select"] div { color: #1a2332 !important; }
[data-baseweb="popover"] { background: #ffffff !important; }
[role="listbox"] { background: #ffffff !important; }
[role="option"] { color: #1a2332 !important; }

/* Tabs */
[data-baseweb="tab-list"] {
    background-color: #ffffff !important;
    border-bottom: 2px solid #dde3ed !important;
}
[data-baseweb="tab"] {
    color: #64748b !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    padding: 10px 20px !important;
    background: transparent !important;
}
[aria-selected="true"] {
    color: #1e3a5f !important;
    border-bottom: 2px solid #1e3a5f !important;
    background: transparent !important;
}
[data-baseweb="tab-panel"] {
    background-color: transparent !important;
}
[data-baseweb="tab-border"] { background-color: #dde3ed !important; }

/* DataFrames */
.stDataFrame,
[data-testid="stDataFrameResizable"],
[data-testid="stDataFrameContainer"] {
    background-color: #ffffff !important;
    border: 1px solid #dde3ed !important;
    border-radius: 8px !important;
}

/* Botoes */
.stButton > button {
    background-color: #1e3a5f !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
}
.stButton > button:hover { background-color: #163050 !important; }

/* Multiselect tags */
[data-baseweb="tag"] {
    background-color: #e8f0fa !important;
    color: #1e3a5f !important;
}

/* Radio buttons */
.stRadio label { color: #1a2332 !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #f5f7fa; }
::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 3px; }

/* KPI Cards */
.kpi-card {
    background: #ffffff;
    border: 1px solid #dde3ed;
    border-radius: 10px;
    padding: 16px 14px;
    text-align: center;
    position: relative;
    overflow: hidden;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
    min-height: 100px;
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: var(--accent, #1e3a5f);
}
.kpi-label {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.1px;
    text-transform: uppercase;
    color: #64748b;
    margin-bottom: 6px;
}
.kpi-value {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 26px;
    font-weight: 700;
    color: #1a2332;
    line-height: 1;
}
.kpi-sub { font-size: 10px; color: #94a3b8; margin-top: 5px; }
.kpi-blue   { --accent: #1e3a5f; }
.kpi-green  { --accent: #16a34a; }
.kpi-yellow { --accent: #d97706; }
.kpi-red    { --accent: #dc2626; }
.kpi-purple { --accent: #7c3aed; }

/* Secao titulo */
.sec {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1.4px;
    text-transform: uppercase;
    color: #1e3a5f;
    border-left: 3px solid #1e3a5f;
    padding-left: 10px;
    margin: 22px 0 10px 0;
}

/* Header de tela */
.ph {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px 0 18px 0;
    border-bottom: 1px solid #dde3ed;
    margin-bottom: 18px;
}
.ph h1 { font-size: 20px; font-weight: 700; color: #1a2332; margin: 0; }
.badge {
    background: #e8f0fa;
    border: 1px solid #bdd0ea;
    color: #1e3a5f;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
    padding: 3px 10px;
    border-radius: 20px;
    text-transform: uppercase;
    white-space: nowrap;
}
.badge-sup { background: #f0f4f8; border-color: #cbd5e1; color: #475569; }

/* Banner supervisor */
.banner-sup {
    background: #e8f0fa;
    border: 1px solid #bdd0ea;
    border-radius: 6px;
    padding: 8px 14px;
    margin-bottom: 16px;
    font-size: 12px;
    color: #1e3a5f;
}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 3. CONSTANTES
# =============================================================================

SUPABASE_URL = "https://bfamfgjjitrfcdyzuibd.supabase.co"
SUPABASE_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJmYW1mZ2pqaXRyZmNkeXp1aWJkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzEwODA1NjksImV4cCI6MjA4NjY1NjU2OX0."
    "BUWI_spoZoF-XC7DDaexsj2aNVO_sA7gODVEtcBRck0"
)
SUPABASE_HDR = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
}

# ==========================================================
# SUPABASE STORAGE — fonte do BASEBOT.csv
# ==========================================================
SUPABASE_STORAGE_URL = (
    f"{SUPABASE_URL}/storage/v1/object/public/berta/BASEBOT.csv"
)
# Fallback local (desenvolvimento)
_DIR = os.path.dirname(os.path.abspath(__file__))
CAMINHO_BASE_LOCAL = next(
    (p for p in [
        os.path.join(_DIR, "BASEBOT.csv"),
        os.path.join(_DIR, "bases", "BASEBOT.csv"),
    ] if os.path.exists(p)),
    None,
)

# Cores para graficos — tema branco
C = {
    "bg":     "#ffffff",
    "paper":  "#ffffff",
    "grid":   "#e8edf3",
    "txt":    "#475569",
    "navy":   "#1e3a5f",
    "navy2":  "#2d5a8e",
    "navy3":  "#4a7db5",
    "green":  "#16a34a",
    "yellow": "#d97706",
    "red":    "#dc2626",
    "purple": "#7c3aed",
}

_LYT = dict(
    paper_bgcolor=C["paper"],
    plot_bgcolor=C["bg"],
    font=dict(family="Inter, sans-serif", color=C["txt"], size=12),
    margin=dict(l=40, r=20, t=44, b=36),
    xaxis=dict(gridcolor=C["grid"], linecolor=C["grid"], zeroline=False, tickfont_color=C["txt"]),
    yaxis=dict(gridcolor=C["grid"], linecolor=C["grid"], zeroline=False, tickfont_color=C["txt"]),
    legend=dict(bgcolor="rgba(255,255,255,.9)", bordercolor=C["grid"], borderwidth=1, font_color=C["txt"]),
)

# =============================================================================
# 4. DADOS
# =============================================================================

@st.cache_data(ttl=300)
def carregar_base(_dummy=None):
    """
    Carrega BASEBOT.csv do Supabase Storage (producao).
    Fallback automatico para arquivo local (desenvolvimento).
    TTL de 5 minutos — atualiza quando o robo fizer novo upload.
    """
    import io

    # Tentativa 1 — Supabase Storage
    try:
        r = requests.get(SUPABASE_STORAGE_URL, timeout=90)
        if r.status_code == 200:
            # Decodificar com utf-8-sig (remove BOM se houver)
            texto = r.content.decode("utf-8-sig", errors="replace")
            df = pd.read_csv(io.StringIO(texto), sep=";", dtype=str, low_memory=False)
            if len(df) > 0:
                return _processar_df(df)
            st.warning("Base do Supabase veio vazia — tentando arquivo local...")
        else:
            st.warning(f"Supabase Storage: HTTP {r.status_code} — tentando arquivo local...")
    except requests.exceptions.Timeout:
        st.warning("Timeout ao baixar base do Supabase — tentando arquivo local...")
    except Exception as e:
        st.warning(f"Erro Supabase Storage: {e} — tentando arquivo local...")

    # Tentativa 2 — arquivo local (desenvolvimento)
    if CAMINHO_BASE_LOCAL:
        try:
            df = pd.read_csv(CAMINHO_BASE_LOCAL, sep=";", encoding="utf-8-sig",
                             dtype=str, low_memory=False)
            return _processar_df(df)
        except Exception as e:
            st.error(f"Erro ao carregar arquivo local: {e}")

    return None


def _processar_df(df):
    """Normaliza e cria colunas derivadas no DataFrame carregado."""
    df.columns = df.columns.str.strip()
    df["FIM_DT"] = pd.to_datetime(df["Fim Execução"],    dayfirst=True, errors="coerce")
    df["AB_DT"]  = pd.to_datetime(df["Data de criação"], dayfirst=True, errors="coerce")
    df["Estado"]          = df["Estado"].str.strip().str.upper()
    df["Macro Atividade"] = df["Macro Atividade"].str.strip().str.upper()
    df["NOME_TEC"] = df["Técnico Atribuído"].apply(
        lambda v: str(v).split(" - ")[0].strip().title() if pd.notna(v) else "")
    df["DIA_FIM"] = df["FIM_DT"].dt.date
    df["MES_FIM"] = df["FIM_DT"].dt.to_period("M")
    df["SEM_FIM"] = df["FIM_DT"].dt.isocalendar().week.astype("Int64")
    df["ANO_FIM"] = df["FIM_DT"].dt.year.astype("Int64")
    df["DIA_AB"]  = df["AB_DT"].dt.date
    df["MES_AB"]  = df["AB_DT"].dt.to_period("M")
    df["SEM_AB"]  = df["AB_DT"].dt.isocalendar().week.astype("Int64")
    return df


@st.cache_data(ttl=300)
def carregar_equipes():
    try:
        r = requests.get(
            f"{SUPABASE_URL}/rest/v1/tecnicos?select=tr,tt,tc,supervisor,funcionario",
            headers=SUPABASE_HDR, timeout=10)
        if r.status_code != 200:
            return {}
        pat = re.compile(r"^(TR|TT|TC)\d+$", re.I)
        eq = {}
        for row in r.json():
            sup = str(row.get("supervisor") or "").strip()
            if not sup or sup.upper() in ("", "NAN", "NONE"):
                continue
            sup = sup.title()
            cod = None
            func = str(row.get("funcionario") or "")
            m = re.search(r"(TR|TT|TC)\d+", func, re.I)
            if m:
                cod = m.group(0).upper()
            else:
                for campo in ("tc", "tr", "tt"):
                    v = str(row.get(campo) or "").strip().upper()
                    if v and pat.match(v):
                        cod = v
                        break
            if cod:
                eq.setdefault(sup, [])
                if cod not in eq[sup]:
                    eq[sup].append(cod)
        return eq
    except Exception:
        return {}

# =============================================================================
# 5. HELPERS
# =============================================================================

def _kpi(label, valor, sub="", cls="kpi-blue"):
    s = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    return (f'<div class="kpi-card {cls}">'
            f'<div class="kpi-label">{label}</div>'
            f'<div class="kpi-value">{valor}</div>'
            f'{s}</div>')


def _sec(txt):
    st.markdown(f'<div class="sec">{txt}</div>', unsafe_allow_html=True)


def _header(icone, titulo, f):
    mes = f.get("mes", "")
    sup = f.get("supervisor", "")
    sup_b = f'<span class="badge badge-sup">👑 {sup}</span>' if sup else ""
    st.markdown(
        f'<div class="ph"><h1>{icone} {titulo}</h1>'
        f'<span class="badge">{mes}</span>{sup_b}</div>',
        unsafe_allow_html=True)


def _lyt(titulo="", h=360):
    return {**_LYT, "height": h,
            "title": dict(text=titulo, font=dict(size=13, color="#1a2332"), x=0.01)}


def _bar_h(y, x, color, titulo="", h=340, labels=None):
    fig = go.Figure(go.Bar(
        x=x, y=y, orientation="h", marker_color=color,
        text=labels, textposition="inside", textfont_color="white"))
    fig.update_layout(**_lyt(titulo, h))
    fig.update_layout(yaxis_autorange="reversed")
    return fig


def _ev_dual(x, bars, line, bcolor, titulo, h=300, meta=None):
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_bar(x=x, y=bars, name="Qtd", marker_color=bcolor)
    fig.add_scatter(x=x, y=line, name="Taxa%", mode="lines+markers",
                    line=dict(color=C["yellow"], width=2), marker_size=6, secondary_y=True)
    if meta is not None:
        fig.add_hline(y=meta, line_dash="dash", line_color=C["red"],
                      annotation_text=f"Meta {meta}%", secondary_y=True)
    fig.update_layout(**_lyt(titulo, h))
    fig.update_yaxes(showgrid=False, secondary_y=True)
    return fig

# =============================================================================
# 6. SIDEBAR — keys fixas para nao resetar ao trocar tela
# =============================================================================

def sidebar(df):
    with st.sidebar:
        st.markdown(
            '<div style="text-align:center;padding:18px 0 10px">'
            '<div style="font-size:22px;font-weight:800;color:#1e3a5f;letter-spacing:2px">📡 BERTA</div>'
            '<div style="font-size:10px;color:#64748b;font-weight:600;letter-spacing:1px;margin-top:3px">PAINEL OPERACIONAL</div>'
            '</div>', unsafe_allow_html=True)
        st.divider()

        tela = st.radio("Tela",
            ["📅 Diario", "📊 Producao Diaria", "🔁 Repetidos", "👶 Infancia", "📆 Calendario"],
            label_visibility="collapsed", key="nav")
        st.divider()

        st.markdown("**Filtros**")

        meses = sorted(df["MES_FIM"].dropna().astype(str).unique(), reverse=True)
        mes   = st.selectbox("📅 Mes", meses, key="f_mes")

        eq   = carregar_equipes()
        sups = sorted(eq.keys())
        if sups:
            sup = st.selectbox("👑 Supervisor", ["— Todos —"] + sups, key="f_sup")
            tecs_sup = eq.get(sup, []) if sup != "— Todos —" else []
            if tecs_sup:
                st.caption(f"Equipe: {len(tecs_sup)} tecnico(s)")
        else:
            sup, tecs_sup = "— Todos —", []
            st.caption("Supervisores nao carregados")

        terrs = sorted(df["Território de serviço: Nome"].dropna().unique())
        terr  = st.multiselect("📍 Territorio", terrs, key="f_terr")

        pool = ([t for t in tecs_sup if t in df["CODIGO_TECNICO_EXTRAIDO"].values]
                if tecs_sup else sorted(df["CODIGO_TECNICO_EXTRAIDO"].dropna().unique()))
        tec  = st.multiselect("👤 Tecnico", pool, key="f_tec")

        st.divider()
        if st.button("🔄 Recarregar base", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    return {
        "tela": tela, "mes": mes,
        "supervisor": "" if sup == "— Todos —" else sup,
        "tecs_sup": tecs_sup,
        "territorios": terr,
        "tecnicos": tec,
    }


def _filtrar(df, f):
    r = df[df["MES_FIM"].astype(str) == f["mes"]].copy()
    if f["tecs_sup"]:    r = r[r["CODIGO_TECNICO_EXTRAIDO"].isin(f["tecs_sup"])]
    if f["territorios"]: r = r[r["Território de serviço: Nome"].isin(f["territorios"])]
    if f["tecnicos"]:    r = r[r["CODIGO_TECNICO_EXTRAIDO"].isin(f["tecnicos"])]
    return r


def _escopo(df, f):
    if f["tecs_sup"]:
        return df[df["CODIGO_TECNICO_EXTRAIDO"].isin(f["tecs_sup"])].copy()
    return df

# =============================================================================
# 7. TELA — PRODUCAO DIARIA
# =============================================================================

def tela_producao(dm, ds, f):
    _header("📊", "Producao Diaria", f)

    suc  = dm[dm["FLAG_CONCLUIDO_SUCESSO"] == "SIM"]
    conc = dm[dm["Estado"].isin(["CONCLUÍDO COM SUCESSO", "CONCLUÍDO SEM SUCESSO"])]
    inst = suc[suc["Macro Atividade"] == "INST-FTTH"]
    rep  = suc[suc["Macro Atividade"] == "REP-FTTH"]
    dias = suc["DIA_FIM"].nunique()
    efic = round(len(suc) / len(conc) * 100, 1) if len(conc) > 0 else 0
    med  = round(len(suc) / dias, 1) if dias > 0 else 0

    cols = st.columns(6)
    for col, (lb, vl, sb, cl) in zip(cols, [
        ("Concluidos",  f"{len(suc):,}",  "c/ sucesso",       "kpi-blue"),
        ("Eficacia",    f"{efic}%",        "suc / total",      "kpi-green" if efic>=85 else "kpi-yellow" if efic>=70 else "kpi-red"),
        ("Instalacoes", f"{len(inst):,}",  "INST-FTTH",        "kpi-blue"),
        ("Reparos",     f"{len(rep):,}",   "REP-FTTH",         "kpi-purple"),
        ("Dias Trab.",  f"{dias}",         "c/ encerramento",  "kpi-blue"),
        ("Media/Dia",   f"{med}",          "atividades/dia",   "kpi-blue"),
    ]):
        col.markdown(_kpi(lb, vl, sb, cl), unsafe_allow_html=True)
    st.write("")

    _sec("Producao por Dia")
    prod = suc.groupby("DIA_FIM").agg(
        Total=("Número SA", "count"),
        Inst =("Macro Atividade", lambda x: (x=="INST-FTTH").sum()),
        Rep  =("Macro Atividade", lambda x: (x=="REP-FTTH").sum()),
    ).reset_index()
    ss = dm[dm["FLAG_CONCLUIDO_SEM_SUCESSO"]=="SIM"].groupby("DIA_FIM").size().reset_index(name="SS")
    prod = prod.merge(ss, on="DIA_FIM", how="left")
    prod["SS"]    = prod["SS"].fillna(0).astype(int)
    prod["Efic%"] = (prod["Total"]/(prod["Total"]+prod["SS"])*100).round(1)
    prod["Dia"]   = pd.to_datetime(prod["DIA_FIM"]).dt.strftime("%d/%m")

    fig = go.Figure()
    fig.add_bar(x=prod["Dia"], y=prod["Inst"], name="INST", marker_color=C["navy"])
    fig.add_bar(x=prod["Dia"], y=prod["Rep"],  name="REP",  marker_color=C["purple"])
    fig.update_layout(barmode="stack", showlegend=True, **_lyt("Producao Diaria - INST + REP", 320))
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        prod[["Dia","Total","Inst","Rep","SS","Efic%"]].rename(
            columns={"Inst":"INST","Rep":"REP","SS":"Sem Suc.","Efic%":"Eficacia%"}),
        use_container_width=True, hide_index=True,
        column_config={"Eficacia%": st.column_config.ProgressColumn(
            "Eficacia%", format="%.1f%%", min_value=0, max_value=100)})

    _sec("Pareto de Tecnicos")
    pt = suc.groupby(["CODIGO_TECNICO_EXTRAIDO","NOME_TEC"]).size().reset_index(name="Prod")
    pt = pt.sort_values("Prod", ascending=False).reset_index(drop=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Top 5 — Maior Producao**")
        t5 = pt.head(5)
        st.plotly_chart(
            _bar_h(t5["NOME_TEC"], t5["Prod"], C["green"],
                   labels=t5["CODIGO_TECNICO_EXTRAIDO"], h=260),
            use_container_width=True)
    with c2:
        st.markdown("**Top 5 — Menor Producao**")
        b5 = pt.tail(5).sort_values("Prod")
        st.plotly_chart(
            _bar_h(b5["NOME_TEC"], b5["Prod"], C["yellow"],
                   labels=b5["CODIGO_TECNICO_EXTRAIDO"], h=260),
            use_container_width=True)

    _sec("Ranking Completo")
    pt["#"] = range(1, len(pt)+1)
    st.dataframe(
        pt[["#","NOME_TEC","CODIGO_TECNICO_EXTRAIDO","Prod"]].rename(
            columns={"NOME_TEC":"Nome","CODIGO_TECNICO_EXTRAIDO":"TR","Prod":"Producao"}),
        use_container_width=True, hide_index=True,
        column_config={"Producao": st.column_config.ProgressColumn(
            "Producao", format="%d", min_value=0, max_value=int(pt["Prod"].max()))})

    _sec("Evolucoes")
    tab1, tab2 = st.tabs(["📅 Semanal","📆 Mensal"])
    suc_sc = ds[ds["FLAG_CONCLUIDO_SUCESSO"]=="SIM"].copy()
    with tab1:
        suc_sc["AW"] = suc_sc["ANO_FIM"].astype(str)+"-S"+suc_sc["SEM_FIM"].astype(str).str.zfill(2)
        ev = suc_sc.groupby("AW").size().reset_index(name="T").sort_values("AW").tail(12)
        fig2 = go.Figure(go.Scatter(x=ev["AW"],y=ev["T"],mode="lines+markers",
                                    line=dict(color=C["navy"],width=2),marker_size=7))
        fig2.update_layout(**_lyt("Producao Semanal - ultimas 12 semanas",300))
        st.plotly_chart(fig2, use_container_width=True)
    with tab2:
        ev2 = suc_sc.groupby("MES_FIM").size().reset_index(name="T")
        ev2["MES_FIM"] = ev2["MES_FIM"].astype(str)
        ev2 = ev2.sort_values("MES_FIM").tail(12)
        fig3 = go.Figure(go.Bar(x=ev2["MES_FIM"],y=ev2["T"],marker_color=C["navy"]))
        fig3.update_layout(**_lyt("Producao Mensal",300))
        st.plotly_chart(fig3, use_container_width=True)

# =============================================================================
# 8. TELA — REPETIDOS
# =============================================================================

def _calcular_repetidos_gpon(ds, mes_str):
    """
    Mesma logica do bot Telegram:
    - Identifica GPONs com 2+ reparos conclusos c/ sucesso
    - Delta <= 30 dias entre Fim Execucao do PAI e Fim Execucao do filho
    - Denominador: reparos validos com Data de criacao no mes
    - Numerador: GPONs unicos com repeticao cujo filho foi aberto no mes
    Retorna: (gpons_repetidos dict, den_total, den_tec_df)
    """
    from datetime import datetime as _dt
    import re as _re

    try:
        per = pd.Period(mes_str, freq="M")
        ano, mes = per.year, per.month
    except Exception:
        return {}, 0, pd.DataFrame()

    primeiro_dia = pd.Timestamp(ano, mes, 1)
    if mes == 12:
        ultimo_dia = pd.Timestamp(ano+1, 1, 1) - pd.Timedelta(days=1)
    else:
        ultimo_dia = pd.Timestamp(ano, mes+1, 1) - pd.Timedelta(days=1)

    df = ds.copy()

    # Garantir colunas de data
    if "FIM_DT" not in df.columns:
        df["FIM_DT"] = pd.to_datetime(df["Fim Execução"], dayfirst=True, errors="coerce")
    if "AB_DT" not in df.columns:
        df["AB_DT"] = pd.to_datetime(df["Data de criação"], dayfirst=True, errors="coerce")

    # Normalizar GPON
    df["_GPON"] = df["FSLOI_GPONAccess"].astype(str).str.strip().str.upper()

    # Reparos validos concluidos com sucesso (igual ao bot)
    df_rep = df[
        (df["Macro Atividade"] == "REP-FTTH") &
        (df["Estado"] == "CONCLUÍDO COM SUCESSO") &
        (df["FIM_DT"].notna()) &
        (df["_GPON"].notna()) &
        (~df["_GPON"].isin(["", "NAN"]))
    ].copy()

    # Identificar GPONs repetidos (delta Fim→Fim <= 30 dias)
    gpons_repetidos = {}
    for gpon, grupo in df_rep.groupby("_GPON"):
        grupo = grupo.sort_values("FIM_DT").reset_index(drop=True)
        if len(grupo) < 2:
            continue
        for i in range(len(grupo) - 1):
            pai  = grupo.iloc[i]
            filho = grupo.iloc[i+1]
            delta = (filho["FIM_DT"] - pai["FIM_DT"]).days
            # Filho aberto no mes de referencia
            ab_filho = filho.get("AB_DT") if "AB_DT" in filho.index else None
            if pd.notna(ab_filho):
                if ab_filho < primeiro_dia or ab_filho > ultimo_dia:
                    continue
            if delta <= 30:
                if gpon not in gpons_repetidos:
                    gpons_repetidos[gpon] = {
                        "pai_tr"   : pai.get("CODIGO_TECNICO_EXTRAIDO", ""),
                        "pai_nome" : pai.get("NOME_TEC", ""),
                        "pai_sa"   : pai.get("Número SA", ""),
                        "pai_fim"  : pai["FIM_DT"],
                        "filho_tr" : filho.get("CODIGO_TECNICO_EXTRAIDO", ""),
                        "filho_sa" : filho.get("Número SA", ""),
                        "delta"    : delta,
                    }
                break

    # Denominador: reparos validos abertos no mes (Data de criacao)
    den_df = df[
        (df["Macro Atividade"] == "REP-FTTH") &
        (df["Estado"] == "CONCLUÍDO COM SUCESSO") &
        (df["AB_DT"].notna()) &
        (df["AB_DT"] >= primeiro_dia) &
        (df["AB_DT"] <= ultimo_dia)
    ]

    return gpons_repetidos, len(den_df), den_df


def tela_repetidos(dm, ds, f):
    _header("🔁", "Repetidos", f)

    # Calcular com mesma logica do bot
    gpons_rep, den_total, den_df = _calcular_repetidos_gpon(ds, f["mes"])
    num_gpons = len(gpons_rep)
    taxa  = round(num_gpons / den_total * 100, 2) if den_total > 0 else 0
    rep_ab   = ds[ds["FLAG_REPETIDO_ABERTO"] == "SIM"]
    rep_alrm = pd.DataFrame([v for v in gpons_rep.values() if ds[ds["FSLOI_GPONAccess"].str.upper()==k]["ALARMADO"].eq("SIM").any() for k in [v.get("pai_sa","")]][:0])  # placeholder
    # Alarmados: GPONs repetidos que estao alarmados
    gpons_rep_set = set(gpons_rep.keys())
    rep_alrm_count = ds[
        (ds["_GPON"].isin(gpons_rep_set) if "_GPON" in ds.columns else
         ds["FSLOI_GPONAccess"].astype(str).str.upper().isin(gpons_rep_set)) &
        (ds["ALARMADO"] == "SIM")
    ].shape[0] if "ALARMADO" in ds.columns else 0

    cols = st.columns(5)
    for col, (lb,vl,sb,cl) in zip(cols,[
        ("Total Reparos", f"{den_total:,}",   "abertos no mes",  "kpi-blue"),
        ("Repetidos",     f"{num_gpons:,}",   "GPONs unicos",    "kpi-red" if taxa>9 else "kpi-yellow"),
        ("Taxa %",        f"{taxa}%",          "meta: <= 9%",     "kpi-red" if taxa>9 else "kpi-green"),
        ("Em Garantia",   f"{len(rep_ab):,}", "abertos 30d",     "kpi-yellow"),
        ("Alarmados",     f"{rep_alrm_count}", "GPON alarmado",  "kpi-red" if rep_alrm_count>0 else "kpi-green"),
    ]):
        col.markdown(_kpi(lb,vl,sb,cl), unsafe_allow_html=True)
    st.write("")

    _sec("Indicador por Tecnico — GPONs unicos (mesma logica do bot)")
    def _n(v): return str(v).split(" - ")[0].strip().title() if pd.notna(v) else ""

    # Denominador por tecnico (reparos abertos no mes)
    den_tec = den_df.groupby("CODIGO_TECNICO_EXTRAIDO").agg(
        Total=("Número SA","count"),
        Nome=("Técnico Atribuído", lambda x: _n(x.iloc[0]) if len(x) else "")
    ).reset_index() if not den_df.empty else pd.DataFrame(columns=["CODIGO_TECNICO_EXTRAIDO","Total","Nome"])

    # Numerador por tecnico (GPONs únicos onde é PAI)
    rep_por_tec = {}
    for gpon, info in gpons_rep.items():
        tr = info.get("pai_tr","")
        if tr:
            rep_por_tec[tr] = rep_por_tec.get(tr, 0) + 1

    rep_tec_df = pd.DataFrame(
        [(k, v) for k,v in rep_por_tec.items()],
        columns=["CODIGO_TECNICO_EXTRAIDO","Repetidos"]
    ) if rep_por_tec else pd.DataFrame(columns=["CODIGO_TECNICO_EXTRAIDO","Repetidos"])

    tb = den_tec.merge(rep_tec_df, on="CODIGO_TECNICO_EXTRAIDO", how="left")
    tb["Repetidos"] = tb["Repetidos"].fillna(0).astype(int)
    tb["Taxa%"] = (tb["Repetidos"]/tb["Total"].replace(0,1)*100).round(2)
    tb = tb.sort_values("Taxa%", ascending=False).reset_index(drop=True)
    tb.columns = ["TR","Total","Nome","Repetidos","Taxa%"]
    tb["Status"] = tb["Taxa%"].apply(lambda t: "🔴" if t>12 else "🟡" if t>9 else "🟢" if t>0 else "⚪")
    st.dataframe(tb[["Status","Nome","TR","Repetidos","Total","Taxa%"]], use_container_width=True, hide_index=True,
                 column_config={"Taxa%": st.column_config.ProgressColumn(
                     "Taxa%", format="%.1f%%", min_value=0,
                     max_value=max(float(tb["Taxa%"].max()) if not tb.empty else 1, 1))})

    c1, c2 = st.columns(2)
    with c1:
        _sec("Pareto - Causas")
        if "Descrição" in num.columns and num["Descrição"].notna().any():
            caus = num["Descrição"].value_counts().head(10).reset_index()
            caus.columns = ["Causa","Qtd"]
            caus["L"] = caus["Causa"].str[:50]+"..."
            st.plotly_chart(_bar_h(caus["L"],caus["Qtd"],C["red"],"Top 10 Causas",h=380),
                            use_container_width=True)
        else:
            st.info("Sem dados de causa.")
    with c2:
        _sec("Pareto - Tecnicos")
        top = tb[tb["Repetidos"]>0].sort_values("Repetidos",ascending=False).head(15)
        if not top.empty:
            st.plotly_chart(_bar_h(top["Nome"],top["Repetidos"],C["red"],
                                   "Tecnicos c/ mais Repetidos",h=380,labels=top["TR"]),
                            use_container_width=True)
        else:
            st.success("Nenhum tecnico com repetidos.")

    _sec("Evolucoes")
    tab1, tab2 = st.tabs(["📅 Semanal","📆 Mensal"])
    rep_sc = ds[ds["FLAG_REPETIDO_30D"]=="SIM"].copy()
    den_sc = ds[ds["FLAG_REPARO_VALIDO"]=="SIM"].copy()
    with tab1:
        rs = rep_sc.groupby("SEM_AB").size().reset_index(name="Rep")
        dss = den_sc.groupby("SEM_AB").size().reset_index(name="Den")
        ev = rs.merge(dss,on="SEM_AB",how="outer").fillna(0)
        ev["Taxa"] = (ev["Rep"]/ev["Den"].replace(0,1)*100).round(2)
        ev = ev[ev["SEM_AB"].notna()].sort_values("SEM_AB").tail(12)
        ev["SEM_AB"] = "S"+ev["SEM_AB"].astype(str).str.zfill(2)
        st.plotly_chart(_ev_dual(ev["SEM_AB"],ev["Rep"],ev["Taxa"],
                                  C["red"],"Evolucao Semanal",meta=9), use_container_width=True)
    with tab2:
        rm = rep_sc.groupby("MES_AB").size().reset_index(name="Rep")
        dm2 = den_sc.groupby("MES_AB").size().reset_index(name="Den")
        ev2 = rm.merge(dm2,on="MES_AB",how="outer").fillna(0)
        ev2["Taxa"]   = (ev2["Rep"]/ev2["Den"].replace(0,1)*100).round(2)
        ev2["MES_AB"] = ev2["MES_AB"].astype(str)
        ev2 = ev2.sort_values("MES_AB").tail(12)
        st.plotly_chart(_ev_dual(ev2["MES_AB"],ev2["Rep"],ev2["Taxa"],
                                  C["red"],"Evolucao Mensal",meta=9), use_container_width=True)

    ta, tb2 = st.tabs(["📂 Em Garantia","🚨 Alarmados"])
    with ta:
        _sec("Reparos em Garantia (Abertos)")
        if rep_ab.empty:
            st.success("Nenhum reparo em garantia.")
        else:
            ok = [c for c in ["Número SA","FSLOI_GPONAccess","CODIGO_TECNICO_EXTRAIDO",
                               "NOME_TEC","Estado","DIA_AB","ALARMADO"] if c in rep_ab.columns]
            st.dataframe(rep_ab[ok].rename(columns={
                "Número SA":"SA","FSLOI_GPONAccess":"GPON",
                "CODIGO_TECNICO_EXTRAIDO":"TR","NOME_TEC":"Tecnico","DIA_AB":"Abertura"}),
                use_container_width=True, hide_index=True)
    with tb2:
        _sec("Repetidos com GPON Alarmado")
        if rep_alrm.empty:
            st.success("Nenhum repetido alarmado.")
        else:
            ok = [c for c in ["Número SA","FSLOI_GPONAccess","CODIGO_TECNICO_EXTRAIDO",
                               "NOME_TEC","Estado","Alarm ID"] if c in rep_alrm.columns]
            st.dataframe(rep_alrm[ok].rename(columns={
                "Número SA":"SA","FSLOI_GPONAccess":"GPON",
                "CODIGO_TECNICO_EXTRAIDO":"TR","NOME_TEC":"Tecnico","Alarm ID":"Alarme"}),
                use_container_width=True, hide_index=True)

# =============================================================================
# 9. TELA — INFANCIA
# =============================================================================

def tela_infancia(dm, ds, f):
    _header("👶", "Infancia", f)

    inst = dm[dm["FLAG_INSTALACAO_VALIDA"]=="SIM"]
    inf  = inst[inst["FLAG_INFANCIA_30D"]=="SIM"]
    taxa = round(len(inf)/len(inst)*100,2) if len(inst)>0 else 0
    estados_ab = ["ATRIBUÍDO","NÃO ATRIBUÍDO","RECEBIDO","EM EXECUÇÃO","EM DESLOCAMENTO"]
    gpons = set(inf["FSLOI_GPONAccess"].dropna().str.upper())
    rep_ab = ds[(ds["Macro Atividade"]=="REP-FTTH") &
                (ds["Estado"].isin(estados_ab)) &
                (ds["FSLOI_GPONAccess"].str.upper().isin(gpons))]
    inf_alrm = inf[inf["ALARMADO"]=="SIM"] if "ALARMADO" in inf.columns else pd.DataFrame()

    cols = st.columns(5)
    for col,(lb,vl,sb,cl) in zip(cols,[
        ("Total Inst.",  f"{len(inst):,}", "INST concluidas",  "kpi-blue"),
        ("Infancia",     f"{len(inf):,}",  "reparo em 30d",    "kpi-red" if taxa>5 else "kpi-yellow"),
        ("Taxa %",       f"{taxa}%",       "meta: <= 5%",      "kpi-red" if taxa>5 else "kpi-green"),
        ("Inf. Aberta",  f"{len(rep_ab):,}","reparo aberto",   "kpi-yellow"),
        ("Alarmados",    f"{len(inf_alrm):,}","GPON alarmado", "kpi-red" if len(inf_alrm)>0 else "kpi-green"),
    ]):
        col.markdown(_kpi(lb,vl,sb,cl), unsafe_allow_html=True)
    st.write("")

    _sec("Indicador por Tecnico")
    def _n(v): return str(v).split(" - ")[0].strip().title() if pd.notna(v) else ""
    di = inst.groupby("CODIGO_TECNICO_EXTRAIDO").agg(
        Total=("Número SA","count"),
        Nome=("Técnico Atribuído", lambda x: _n(x.iloc[0]) if len(x) else "")).reset_index()
    ni = inf.groupby("CODIGO_TECNICO_EXTRAIDO").size().reset_index(name="Inf")
    tb = di.merge(ni,on="CODIGO_TECNICO_EXTRAIDO",how="left")
    tb["Inf"]   = tb["Inf"].fillna(0).astype(int)
    tb["Taxa%"] = (tb["Inf"]/tb["Total"]*100).round(2)
    tb = tb.sort_values("Taxa%",ascending=False).reset_index(drop=True)
    tb.columns = ["TR","Total","Nome","Infancia","Taxa%"]
    tb["Status"] = tb["Taxa%"].apply(lambda t: "🔴" if t>8 else "🟡" if t>5 else "🟢" if t>0 else "⚪")
    st.dataframe(tb[["Status","Nome","TR","Infancia","Total","Taxa%"]], use_container_width=True, hide_index=True,
                 column_config={"Taxa%": st.column_config.ProgressColumn(
                     "Taxa%", format="%.1f%%", min_value=0, max_value=max(float(tb["Taxa%"].max()),1))})

    c1, c2 = st.columns(2)
    with c1:
        _sec("Pareto - Causas")
        sas = inf["SA_REPARO_INFANCIA"].dropna().unique() if "SA_REPARO_INFANCIA" in inf.columns else []
        rows = ds[ds["Número SA"].isin(sas)] if len(sas) else pd.DataFrame()
        if not rows.empty and "Descrição" in rows.columns:
            caus = rows["Descrição"].value_counts().head(10).reset_index()
            caus.columns = ["Causa","Qtd"]
            caus["L"] = caus["Causa"].str[:50]+"..."
            st.plotly_chart(_bar_h(caus["L"],caus["Qtd"],C["purple"],"Top 10 Causas Infancia",h=380),
                            use_container_width=True)
        else:
            st.info("Sem dados de causa.")
    with c2:
        _sec("Pareto - Tecnicos")
        top = tb[tb["Infancia"]>0].sort_values("Infancia",ascending=False).head(15)
        if not top.empty:
            st.plotly_chart(_bar_h(top["Nome"],top["Infancia"],C["purple"],
                                   "Tecnicos c/ mais Infancia",h=380,labels=top["TR"]),
                            use_container_width=True)
        else:
            st.success("Nenhum tecnico com infancia.")

    _sec("Evolucoes")
    tab1, tab2 = st.tabs(["📅 Semanal","📆 Mensal"])
    inst_sc = ds[ds["FLAG_INSTALACAO_VALIDA"]=="SIM"].copy()
    inf_sc  = ds[ds["FLAG_INFANCIA_30D"]=="SIM"].copy()
    with tab1:
        is_ = inf_sc.groupby("SEM_FIM").size().reset_index(name="Inf")
        ds2 = inst_sc.groupby("SEM_FIM").size().reset_index(name="Den")
        ev  = is_.merge(ds2,on="SEM_FIM",how="outer").fillna(0)
        ev["Taxa"] = (ev["Inf"]/ev["Den"].replace(0,1)*100).round(2)
        ev = ev[ev["SEM_FIM"].notna()].sort_values("SEM_FIM").tail(12)
        ev["SEM_FIM"] = "S"+ev["SEM_FIM"].astype(str).str.zfill(2)
        st.plotly_chart(_ev_dual(ev["SEM_FIM"],ev["Inf"],ev["Taxa"],
                                  C["purple"],"Evolucao Semanal"), use_container_width=True)
    with tab2:
        im = inf_sc.groupby("MES_FIM").size().reset_index(name="Inf")
        dm2 = inst_sc.groupby("MES_FIM").size().reset_index(name="Den")
        ev2 = im.merge(dm2,on="MES_FIM",how="outer").fillna(0)
        ev2["Taxa"]   = (ev2["Inf"]/ev2["Den"].replace(0,1)*100).round(2)
        ev2["MES_FIM"] = ev2["MES_FIM"].astype(str)
        ev2 = ev2.sort_values("MES_FIM").tail(12)
        st.plotly_chart(_ev_dual(ev2["MES_FIM"],ev2["Inf"],ev2["Taxa"],
                                  C["purple"],"Evolucao Mensal"), use_container_width=True)

    ta, tb2 = st.tabs(["📂 Infancia Aberta","🚨 Infancia Alarmada"])
    with ta:
        _sec("Instalacoes com Reparo em Andamento")
        if rep_ab.empty:
            st.success("Nenhuma instalacao com reparo aberto.")
        else:
            ok = [c for c in ["Número SA","FSLOI_GPONAccess","CODIGO_TECNICO_EXTRAIDO",
                               "NOME_TEC","Estado","DIA_AB","ALARMADO"] if c in rep_ab.columns]
            st.dataframe(rep_ab[ok].rename(columns={
                "Número SA":"SA","FSLOI_GPONAccess":"GPON",
                "CODIGO_TECNICO_EXTRAIDO":"TR","NOME_TEC":"Tecnico","DIA_AB":"Abertura"}),
                use_container_width=True, hide_index=True)
    with tb2:
        _sec("Instalacoes com GPON Alarmado")
        if inf_alrm.empty:
            st.success("Nenhuma infancia alarmada.")
        else:
            ok = [c for c in ["Número SA","FSLOI_GPONAccess","CODIGO_TECNICO_EXTRAIDO",
                               "NOME_TEC","SA_REPARO_INFANCIA","Alarm ID"] if c in inf_alrm.columns]
            st.dataframe(inf_alrm[ok].rename(columns={
                "Número SA":"SA Inst.","FSLOI_GPONAccess":"GPON",
                "CODIGO_TECNICO_EXTRAIDO":"TR","NOME_TEC":"Tecnico",
                "SA_REPARO_INFANCIA":"SA Reparo","Alarm ID":"Alarme"}),
                use_container_width=True, hide_index=True)

# =============================================================================
# TELA — DIARIO
# =============================================================================

def tela_diario(df, ds, f):
    _header("📅", "Controle do Dia", f)

    # Seletor de data — usa a data mais recente da base como padrao
    datas_disp = sorted(ds["FIM_DT"].dropna().dt.date.unique(), reverse=True)
    if not datas_disp:
        st.warning("Nenhuma data disponivel.")
        return

    c_pick, c_info = st.columns([2, 5])
    with c_pick:
        dia_sel = st.date_input("Data de referencia",
            value=datas_disp[0],
            min_value=datas_disp[-1],
            max_value=datas_disp[0],
            key="dia_ref")

    dm  = ds[ds["FIM_DT"].dt.date == dia_sel].copy()
    dm_ab = ds[ds["AB_DT"].dt.date == dia_sel].copy()

    suc     = dm[dm["FLAG_CONCLUIDO_SUCESSO"]    == "SIM"]
    sem_suc = dm[dm["FLAG_CONCLUIDO_SEM_SUCESSO"] == "SIM"]
    inst_d  = suc[suc["Macro Atividade"] == "INST-FTTH"]
    rep_d   = suc[suc["Macro Atividade"] == "REP-FTTH"]
    tecs_atv = suc["CODIGO_TECNICO_EXTRAIDO"].nunique()
    efic    = round(len(suc)/(len(suc)+len(sem_suc))*100,1) if (len(suc)+len(sem_suc))>0 else 0

    with c_info:
        st.markdown(
            f"<div style='margin-top:28px;font-size:12px;color:#64748b;'>"
            f"<b>{dia_sel.strftime('%d/%m/%Y')}</b> — "
            f"{tecs_atv} tecnicos ativos | {len(suc)+len(sem_suc)} atividades concluidas</div>",
            unsafe_allow_html=True)

    rep_dia_ab = dm_ab[dm_ab["FLAG_REPETIDO_30D"]  == "SIM"]
    rep_ab_tot = ds[ds["FLAG_REPETIDO_ABERTO"]      == "SIM"]
    inf_dia    = suc[suc["FLAG_INFANCIA_30D"]        == "SIM"]
    p0_10 = ds[(ds["FIM_DT"].dt.date == dia_sel) & (ds["FLAG_P0_10_DIA"] == "SIM")]
    p0_15 = ds[(ds["FIM_DT"].dt.date == dia_sel) & (ds["FLAG_P0_15_DIA"] == "SIM")]

    # KPIs
    cols = st.columns(7)
    for col, (lb,vl,sb,cl) in zip(cols, [
        ("Concluidos",    f"{len(suc):,}",  f"INST:{len(inst_d)} REP:{len(rep_d)}", "kpi-blue"),
        ("Eficacia",      f"{efic}%",        "suc/total",   "kpi-green" if efic>=85 else "kpi-yellow" if efic>=70 else "kpi-red"),
        ("Sem Sucesso",   f"{len(sem_suc):,}","pendencias",  "kpi-red" if len(sem_suc)>0 else "kpi-green"),
        ("Rep. Dia",      f"{len(rep_dia_ab):,}","abertos hoje","kpi-red" if len(rep_dia_ab)>0 else "kpi-green"),
        ("Rep. Abertos",  f"{len(rep_ab_tot):,}","em garantia","kpi-yellow" if len(rep_ab_tot)>0 else "kpi-green"),
        ("P0 10h",        f"{p0_10['CODIGO_TECNICO_EXTRAIDO'].nunique()}","tecnicos","kpi-red" if not p0_10.empty else "kpi-green"),
        ("P0 15h",        f"{p0_15['CODIGO_TECNICO_EXTRAIDO'].nunique()}","tecnicos","kpi-red" if not p0_15.empty else "kpi-green"),
    ]):
        col.markdown(_kpi(lb,vl,sb,cl), unsafe_allow_html=True)
    st.write("")

    # Produtividade por tecnico
    _sec("Produtividade por Tecnico")
    def _n(v): return str(v).split(" - ")[0].strip().title() if pd.notna(v) else ""
    if suc.empty:
        st.info("Nenhuma atividade concluida neste dia.")
    else:
        pt = suc.groupby("CODIGO_TECNICO_EXTRAIDO").agg(
            Nome  =("Técnico Atribuído", lambda x: _n(x.iloc[0])),
            Total =("Número SA","count"),
            INST  =("Macro Atividade", lambda x: (x=="INST-FTTH").sum()),
            REP   =("Macro Atividade", lambda x: (x=="REP-FTTH").sum()),
        ).reset_index()
        ss_tec = sem_suc.groupby("CODIGO_TECNICO_EXTRAIDO").size().reset_index(name="SemSuc")
        pt = pt.merge(ss_tec, on="CODIGO_TECNICO_EXTRAIDO", how="left")
        pt["SemSuc"] = pt["SemSuc"].fillna(0).astype(int)
        pt["Efic%"]  = (pt["Total"]/(pt["Total"]+pt["SemSuc"]).replace(0,1)*100).round(1)
        pt = pt.sort_values("Total", ascending=False).reset_index(drop=True)
        pt.columns = ["TR","Nome","Total","INST","REP","Sem Suc.","Eficacia%"]
        st.dataframe(pt, use_container_width=True, hide_index=True,
            column_config={
                "Total":    st.column_config.ProgressColumn("Total", format="%d", min_value=0,
                            max_value=int(pt["Total"].max()) if not pt.empty else 1),
                "Eficacia%":st.column_config.ProgressColumn("Eficacia%", format="%.1f%%", min_value=0, max_value=100),
            })

    # Sem sucesso / pendencias
    _sec("Sem Sucesso — Pendencias do Dia")
    if sem_suc.empty:
        st.success("Nenhuma pendencia no dia.")
    else:
        ok = [c for c in ["Número SA","CODIGO_TECNICO_EXTRAIDO","NOME_TEC",
                           "Macro Atividade","Descrição","Observação",
                           "Código de encerramento"] if c in sem_suc.columns]
        st.dataframe(sem_suc[ok].rename(columns={
            "Número SA":"SA","CODIGO_TECNICO_EXTRAIDO":"TR","NOME_TEC":"Tecnico",
            "Macro Atividade":"Tipo","Código de encerramento":"Cod. Enc."}),
            use_container_width=True, hide_index=True)

    # Repetidos
    c1, c2 = st.columns(2)
    with c1:
        _sec("Repetidos Abertos no Dia")
        if rep_dia_ab.empty:
            st.success("Nenhum repetido aberto hoje.")
        else:
            ok = [c for c in ["Número SA","CODIGO_TECNICO_EXTRAIDO","NOME_TEC",
                               "FSLOI_GPONAccess","ALARMADO"] if c in rep_dia_ab.columns]
            st.dataframe(rep_dia_ab[ok].rename(columns={
                "Número SA":"SA","CODIGO_TECNICO_EXTRAIDO":"TR",
                "NOME_TEC":"Tecnico","FSLOI_GPONAccess":"GPON"}),
                use_container_width=True, hide_index=True)
    with c2:
        _sec("Repetidos em Garantia (Abertos)")
        if rep_ab_tot.empty:
            st.success("Nenhum reparo em garantia.")
        else:
            ok = [c for c in ["Número SA","CODIGO_TECNICO_EXTRAIDO","NOME_TEC",
                               "FSLOI_GPONAccess","DIA_AB","ALARMADO"] if c in rep_ab_tot.columns]
            st.dataframe(rep_ab_tot[ok].rename(columns={
                "Número SA":"SA","CODIGO_TECNICO_EXTRAIDO":"TR",
                "NOME_TEC":"Tecnico","FSLOI_GPONAccess":"GPON","DIA_AB":"Abertura"}),
                use_container_width=True, hide_index=True)

    # Infancia
    c3, c4 = st.columns(2)
    with c3:
        _sec("Infancia — Instalacoes do Dia")
        if inf_dia.empty:
            st.success("Nenhuma infancia hoje.")
        else:
            ok = [c for c in ["Número SA","CODIGO_TECNICO_EXTRAIDO","NOME_TEC",
                               "FSLOI_GPONAccess","SA_REPARO_INFANCIA"] if c in inf_dia.columns]
            st.dataframe(inf_dia[ok].rename(columns={
                "Número SA":"SA Inst.","CODIGO_TECNICO_EXTRAIDO":"TR",
                "NOME_TEC":"Tecnico","FSLOI_GPONAccess":"GPON",
                "SA_REPARO_INFANCIA":"SA Reparo"}),
                use_container_width=True, hide_index=True)
    with c4:
        _sec("Infancia Aberta (Reparo em Andamento)")
        estados_ab = ["ATRIBUÍDO","NÃO ATRIBUÍDO","RECEBIDO","EM EXECUÇÃO","EM DESLOCAMENTO"]
        gpons_suc = set(suc["FSLOI_GPONAccess"].dropna().str.upper())
        inf_ab_dia = ds[
            (ds["Macro Atividade"] == "REP-FTTH") &
            (ds["Estado"].isin(estados_ab)) &
            (ds["FLAG_INFANCIA_30D"] == "SIM") &
            (ds["FSLOI_GPONAccess"].str.upper().isin(gpons_suc))
        ]
        if inf_ab_dia.empty:
            st.success("Nenhuma infancia aberta.")
        else:
            ok = [c for c in ["Número SA","CODIGO_TECNICO_EXTRAIDO","NOME_TEC",
                               "FSLOI_GPONAccess","Estado"] if c in inf_ab_dia.columns]
            st.dataframe(inf_ab_dia[ok].rename(columns={
                "Número SA":"SA","CODIGO_TECNICO_EXTRAIDO":"TR",
                "NOME_TEC":"Tecnico","FSLOI_GPONAccess":"GPON"}),
                use_container_width=True, hide_index=True)

    # P0
    _sec("P0 — Controle de Encerramento")
    cp1, cp2 = st.columns(2)
    with cp1:
        st.markdown("**P0 10h — Nao encerraram ate as 10h**")
        if p0_10.empty:
            st.success("Todos encerraram ate 10h.")
        else:
            t10 = p0_10.groupby("CODIGO_TECNICO_EXTRAIDO").agg(
                Nome=("Técnico Atribuído", lambda x: _n(x.iloc[0])),
                Qtd =("Número SA","count")).reset_index()
            t10.columns = ["TR","Nome","Qtd"]
            st.dataframe(t10, use_container_width=True, hide_index=True)
    with cp2:
        st.markdown("**P0 15h — Nao encerraram ate as 15h**")
        if p0_15.empty:
            st.success("Todos encerraram ate 15h.")
        else:
            t15 = p0_15.groupby("CODIGO_TECNICO_EXTRAIDO").agg(
                Nome=("Técnico Atribuído", lambda x: _n(x.iloc[0])),
                Qtd =("Número SA","count")).reset_index()
            t15.columns = ["TR","Nome","Qtd"]
            st.dataframe(t15, use_container_width=True, hide_index=True)


# =============================================================================
# TELA — CALENDARIO MENSAL
# =============================================================================

def tela_calendario(df, ds, f):
    import calendar as _cal
    _header("📆", "Calendario Mensal", f)

    mes_str = f["mes"]
    try:
        per = pd.Period(mes_str, freq="M")
        ano, mes = per.year, per.month
    except Exception:
        st.error("Mes invalido."); return

    hoje      = datetime.now()
    dias_mes  = _cal.monthrange(ano, mes)[1]
    # Se for o mes atual, mostrar apenas ate hoje
    dia_max   = hoje.day if (ano == hoje.year and mes == hoje.month) else dias_mes
    dias_range = list(range(1, dia_max + 1))
    meses_pt  = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]
    lbl_mes   = f"{meses_pt[mes-1]}/{ano}"

    df_m = ds[(ds["FIM_DT"].dt.year==ano) & (ds["FIM_DT"].dt.month==mes)].copy()
    df_m["DIA"] = df_m["FIM_DT"].dt.day.astype(int)
    suc_m    = df_m[df_m["FLAG_CONCLUIDO_SUCESSO"]    == "SIM"]
    semsuc_m = df_m[df_m["FLAG_CONCLUIDO_SEM_SUCESSO"] == "SIM"]

    if suc_m.empty:
        st.warning("Sem dados de producao para o mes selecionado.")
        return

    # KPIs
    tecs = suc_m["CODIGO_TECNICO_EXTRAIDO"].nunique()
    efic = round(len(suc_m)/(len(suc_m)+len(semsuc_m))*100,1) if (len(suc_m)+len(semsuc_m))>0 else 0
    cols = st.columns(5)
    for col,(lb,vl,sb,cl) in zip(cols,[
        ("Tecnicos Ativos", f"{tecs}",           lbl_mes,       "kpi-blue"),
        ("Concluidos",      f"{len(suc_m):,}",   "c/ sucesso",  "kpi-blue"),
        ("INST",            f"{(suc_m['Macro Atividade']=='INST-FTTH').sum():,}", "", "kpi-blue"),
        ("REP",             f"{(suc_m['Macro Atividade']=='REP-FTTH').sum():,}",  "", "kpi-purple"),
        ("Eficacia",        f"{efic}%",           "suc/total",   "kpi-green" if efic>=85 else "kpi-yellow"),
    ]):
        col.markdown(_kpi(lb,vl,sb,cl), unsafe_allow_html=True)
    st.write("")

    # Legenda de cores
    st.markdown("""
    <div style="display:flex;gap:10px;margin-bottom:10px;font-size:11px;align-items:center;">
        <span style="background:#1e3a5f;color:white;padding:2px 8px;border-radius:4px;">≥5</span>
        <span style="background:#d4edda;color:#155724;padding:2px 8px;border-radius:4px;">=4</span>
        <span style="background:#fff3cd;color:#856404;padding:2px 8px;border-radius:4px;">=3</span>
        <span style="background:#ffcccc;color:#721c24;padding:2px 8px;border-radius:4px;">1-2</span>
        <span style="background:#f0f0f0;color:#6c757d;padding:2px 8px;border-radius:4px;">0</span>
        <span style="color:#64748b;margin-left:4px;">= atividades no dia</span>
    </div>
    """, unsafe_allow_html=True)

    _sec(f"Producao por Tecnico — {lbl_mes}")

    def _n(v): return str(v).split(" - ")[0].strip().title() if pd.notna(v) else ""

    # Pivot: tecnico x dia (apenas dias_range)
    suc_range = suc_m[suc_m["DIA"].isin(dias_range)]
    pivot = suc_range.groupby(["CODIGO_TECNICO_EXTRAIDO","DIA"]).size().unstack(fill_value=0)
    for d in dias_range:
        if d not in pivot.columns:
            pivot[d] = 0
    pivot = pivot[dias_range]

    nomes     = suc_m.groupby("CODIGO_TECNICO_EXTRAIDO")["Técnico Atribuído"].first().apply(_n)
    ss_tec    = semsuc_m.groupby("CODIGO_TECNICO_EXTRAIDO").size()
    dias_trab = suc_range.groupby("CODIGO_TECNICO_EXTRAIDO")["DIA"].nunique()

    pivot.insert(0, "Nome", nomes)
    pivot["Total"]     = pivot[dias_range].sum(axis=1)
    pivot["Sem Suc."]  = ss_tec.reindex(pivot.index).fillna(0).astype(int)
    pivot["Dias"]      = dias_trab.reindex(pivot.index).fillna(0).astype(int)
    pivot["Media"]     = (pivot["Total"] / pivot["Dias"].replace(0,1)).round(1)
    pivot["Eficacia%"] = (pivot["Total"]/(pivot["Total"]+pivot["Sem Suc."]).replace(0,1)*100).round(1)
    pivot = pivot.sort_values("Total", ascending=False).reset_index()
    pivot = pivot.rename(columns={"CODIGO_TECNICO_EXTRAIDO":"TR"})

    # Renomear colunas de dia para string
    cols_dia  = [str(d) for d in dias_range]
    # Nome primeiro, TR segundo
    cols_order = ["Nome","TR"] + dias_range + ["Dias","Total","Sem Suc.","Media","Eficacia%"]
    pivot = pivot[cols_order]
    pivot.columns = ["Nome","TR"] + cols_dia + ["Dias","Total","Sem Suc.","Media","Eficacia%"]

    def _cor_cel(v):
        try:
            v = int(v)
        except Exception:
            return ""
        if v >= 5: return "background-color:#1e3a5f;color:white;font-weight:700;text-align:center"
        if v == 4: return "background-color:#d4edda;color:#155724;font-weight:600;text-align:center"
        if v == 3: return "background-color:#fff3cd;color:#856404;font-weight:600;text-align:center"
        if v in (1,2): return "background-color:#ffcccc;color:#721c24;text-align:center"
        return "background-color:#f0f0f0;color:#adb5bd;text-align:center"

    try:
        styled = pivot.style.map(_cor_cel, subset=cols_dia)
    except AttributeError:
        styled = pivot.style.applymap(_cor_cel, subset=cols_dia)

    max_p = int(pivot["Total"].max()) if not pivot.empty else 1
    # 38px cabecalho + 35px por linha — mostra todos sem scroll vertical
    altura_total = 38 + (len(pivot) * 35)

    st.dataframe(styled, use_container_width=True, hide_index=True,
        column_config={
            "Nome"     : st.column_config.TextColumn("Nome", width="medium"),
            "TR"       : st.column_config.TextColumn("TR", width="small"),
            "Total"    : st.column_config.ProgressColumn("Total", format="%d", min_value=0, max_value=max_p),
            "Eficacia%": st.column_config.ProgressColumn("Eficacia%", format="%.1f%%", min_value=0, max_value=100),
            "Media"    : st.column_config.NumberColumn("Media", format="%.1f"),
        }, height=altura_total)

    # Grafico eficacia diaria — apenas dias do range
    _sec("Eficacia Diaria do Mes")
    ef_list = []
    for d in dias_range:
        rows = df_m[df_m["DIA"] == d]
        s = (rows["FLAG_CONCLUIDO_SUCESSO"]=="SIM").sum()
        ss = (rows["FLAG_CONCLUIDO_SEM_SUCESSO"]=="SIM").sum()
        ef_list.append({
            "DIA": d,
            "Concluidos": s,
            "Eficacia%": round(s / max(s+ss, 1) * 100, 1),
        })
    ef_dia = pd.DataFrame(ef_list)

    fig = go.Figure()
    fig.add_bar(x=ef_dia["DIA"].astype(str), y=ef_dia["Concluidos"],
                name="Concluidos", marker_color=C["navy"], yaxis="y")
    fig.add_scatter(x=ef_dia["DIA"].astype(str), y=ef_dia["Eficacia%"],
                    name="Eficacia%", mode="lines+markers",
                    line=dict(color=C["green"],width=2), marker_size=6, yaxis="y2")
    fig.add_hline(y=85, line_dash="dash", line_color=C["yellow"],
                  annotation_text="Meta 85%", yref="y2")
    fig.update_layout(
        **_lyt(f"Producao e Eficacia — {lbl_mes}", 320),
        yaxis2=dict(overlaying="y", side="right", showgrid=False,
                    tickfont_color=C["green"], range=[0,110]),
        showlegend=True)
    st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# 10. MAIN
# =============================================================================

def main():
    # Verificacao local apenas para desenvolvimento
    # Em producao os dados vem do Supabase Storage
    try:
        df = carregar_base()
        if df is None:
            st.error("Nao foi possivel carregar a base. Verifique o Supabase Storage.")
            return
    except Exception as e:
        st.error(f"Erro ao carregar base: {e}")
        return

    f    = sidebar(df)
    tela = f["tela"]
    dm   = _filtrar(df, f)
    ds   = _escopo(df, f)

    if f["supervisor"]:
        st.markdown(
            f'<div class="banner-sup">👑 Equipe de <strong>{f["supervisor"]}</strong>'
            f' — {len(f["tecs_sup"])} tecnico(s) | {f["mes"]}</div>',
            unsafe_allow_html=True)

    if dm.empty and tela not in ("📅 Diario", "📆 Calendario"):
        st.warning("Nenhum dado encontrado para os filtros selecionados.")
        return

    if tela == "📅 Diario":
        tela_diario(df, ds, f)
    elif tela == "📊 Producao Diaria":
        tela_producao(dm, ds, f)
    elif tela == "🔁 Repetidos":
        tela_repetidos(dm, ds, f)
    elif tela == "👶 Infancia":
        tela_infancia(dm, ds, f)
    elif tela == "📆 Calendario":
        tela_calendario(df, ds, f)


if __name__ == "__main__":
    main()
