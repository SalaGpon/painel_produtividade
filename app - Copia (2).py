import streamlit as st
import pandas as pd
import os
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import calendar
import re
import hashlib

# =========================================================
# CONFIGURAÇÃO AUTOMÁTICA DO CAMINHO
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CAMINHO_ARQUIVO = os.path.join(BASE_DIR, "base.xlsx")
CAMINHO_PRESENCA = os.path.join(BASE_DIR, "Presença.xlsx")

# =========================================================
# CONFIGURAÇÃO DA PÁGINA
# =========================================================

st.set_page_config(
    layout="wide",
    page_title="Painel de Produtividade",
    page_icon="📊",
    initial_sidebar_state="collapsed"
)

# =========================================================
# FUNÇÕES DE AUTENTICAÇÃO
# =========================================================

def inicializar_sessao():
    """Inicializa as variáveis de sessão"""
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False
    if "usuario" not in st.session_state:
        st.session_state.usuario = None
    if "tipo_usuario" not in st.session_state:
        st.session_state.tipo_usuario = None
    if "tr_usuario" not in st.session_state:
        st.session_state.tr_usuario = None

def autenticar(login, senha):
    """
    Autentica o usuário baseado nas regras:
    - Técnico: login = TR, senha = TR
    - Supervisor: login = TR0000, senha = SUPMASTER
    """
    # Limpar login e senha
    login = login.strip().upper()
    senha = senha.strip().upper()
    
    # Verificar se é supervisor
    if login == "TR0000" and senha == "SUPMASTER":
        st.session_state.autenticado = True
        st.session_state.usuario = "SUPERVISOR"
        st.session_state.tipo_usuario = "supervisor"
        st.session_state.tr_usuario = None
        return True, "supervisor"
    
    # Verificar se é técnico (formato TRxxxxx)
    if re.match(r'^TR\d+$', login) and senha == login:
        st.session_state.autenticado = True
        st.session_state.usuario = login
        st.session_state.tipo_usuario = "tecnico"
        st.session_state.tr_usuario = login
        return True, "tecnico"
    
    return False, None

def logout():
    """Realiza logout do usuário"""
    st.session_state.autenticado = False
    st.session_state.usuario = None
    st.session_state.tipo_usuario = None
    st.session_state.tr_usuario = None

def tela_login():
    """Exibe a tela de login"""
    st.markdown("""
    <style>
        .login-container {
            max-width: 400px;
            margin: 100px auto;
            padding: 30px;
            background: white;
            border-radius: 16px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            border: 1px solid #e2e8f0;
        }
        .login-title {
            font-size: 2rem;
            font-weight: 800;
            background: linear-gradient(135deg, #2563eb, #8b5cf6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-align: center;
            margin-bottom: 30px;
        }
        .stTextInput > div > div > input {
            font-size: 1rem;
            padding: 10px;
        }
        .stButton > button {
            width: 100%;
            background: linear-gradient(135deg, #2563eb, #7c3aed);
            color: white;
            font-weight: 600;
            border: none;
            padding: 10px;
            font-size: 1rem;
            border-radius: 8px;
            transition: all 0.3s;
        }
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(37, 99, 235, 0.3);
        }
    </style>
    """, unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        
        st.markdown('<div class="login-title">PAINEL DE PRODUTIVIDADE</div>', unsafe_allow_html=True)
        
        with st.form("login_form"):
            login = st.text_input("Login", placeholder="Digite seu TR (ex: TR12345)")
            senha = st.text_input("Senha", type="password", placeholder="Digite sua senha")
            
            submitted = st.form_submit_button("Entrar", use_container_width=True)
            
            if submitted:
                if login and senha:
                    autenticado, tipo = autenticar(login, senha)
                    if autenticado:
                        st.success("✅ Login realizado com sucesso!")
                        st.rerun()
                    else:
                        st.error("❌ Login ou senha inválidos!")
                else:
                    st.warning("⚠️ Preencha todos os campos!")
        
        st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# FUNÇÕES AUXILIARES
# =========================================================

def obter_dias_com_producao(df_tecnico):
    """Retorna o número de dias em que o técnico teve pelo menos uma atividade (com ou sem sucesso)"""
    if df_tecnico.empty:
        return 0
    
    dias_com_atividade = set()
    for _, row in df_tecnico.iterrows():
        if pd.notna(row["DATA"]):
            dia = pd.to_datetime(row["DATA"]).day
            dias_com_atividade.add(dia)
    
    return len(dias_com_atividade)

def formatar_data_br(data):
    """Formata data para padrão brasileiro"""
    if pd.isna(data):
        return ""
    return data.strftime("%d/%m/%Y") if hasattr(data, 'strftime') else str(data)

def obter_meses_disponiveis(df):
    """Retorna lista de meses disponíveis no DataFrame"""
    if "DATA" in df.columns and not df["DATA"].isna().all():
        df_temp = df.dropna(subset=["DATA"])
        if not df_temp.empty:
            meses = df_temp["DATA"].apply(lambda x: x.strftime("%Y-%m") if hasattr(x, 'strftime') else None)
            meses = meses.dropna().unique()
            return sorted(meses, reverse=True)
    return [datetime.now().strftime("%Y-%m")]

def extrair_tr(nome_completo):
    """Extrai o TR do formato 'NOME (TR123456)'"""
    if pd.isna(nome_completo):
        return ""
    match = re.search(r'(TR\d+|TT\d+|TC\d+)', str(nome_completo))
    return match.group(1) if match else ""

def extrair_primeiro_nome(nome_completo):
    """Extrai apenas o primeiro nome do técnico"""
    if pd.isna(nome_completo):
        return ""
    nome_limpo = re.sub(r'\s*\(.*\)', '', str(nome_completo)).strip()
    primeiro_nome = nome_limpo.split()[0] if nome_limpo else ""
    return primeiro_nome

def carregar_dados_presenca():
    """Carrega os dados do arquivo Presença.xlsx e cria mapeamento por TR"""
    try:
        if not os.path.exists(CAMINHO_PRESENCA):
            return {}, {}
        
        xl = pd.ExcelFile(CAMINHO_PRESENCA)
        mapeamento_tr = {}
        df_tecnicos = None
        
        for sheet_name in xl.sheet_names:
            if "tecnicos" in sheet_name.lower():
                df_tecnicos = pd.read_excel(CAMINHO_PRESENCA, sheet_name=sheet_name)
                break
        
        if df_tecnicos is None:
            for sheet_name in xl.sheet_names:
                df_temp = pd.read_excel(CAMINHO_PRESENCA, sheet_name=sheet_name, nrows=5)
                if len(df_temp.columns) > 5:
                    df_tecnicos = pd.read_excel(CAMINHO_PRESENCA, sheet_name=sheet_name)
                    break
        
        if df_tecnicos is None:
            return {}, {}
        
        col_tr = None
        col_supervisor = None
        col_funcionario = None
        col_status = None
        
        for col in df_tecnicos.columns:
            col_str = str(col).upper().strip()
            if col_str in ['TR', 'TECNICO', 'TÉCNICO']:
                col_tr = col
            elif 'SUPERVISOR' in col_str:
                col_supervisor = col
            elif 'FUNCIONÁRIO' in col_str or 'NOME' in col_str:
                col_funcionario = col
            elif 'STATUS' in col_str or 'SITUAÇÃO' in col_str:
                col_status = col
        
        for _, row in df_tecnicos.iterrows():
            tr = str(row[col_tr]).strip() if pd.notna(row[col_tr]) else ""
            supervisor = str(row[col_supervisor]).strip() if pd.notna(row[col_supervisor]) else "Não alocado"
            funcionario = str(row[col_funcionario]).strip() if col_funcionario and pd.notna(row[col_funcionario]) else ""
            status = str(row[col_status]).strip() if col_status and pd.notna(row[col_status]) else "Ativo"
            
            if tr and tr not in ['nan', 'None', '']:
                tr_limpo = tr.upper().strip()
                mapeamento_tr[tr_limpo] = {
                    "supervisor": supervisor,
                    "funcionario": funcionario,
                    "status": status
                }
        
        return mapeamento_tr, df_tecnicos
        
    except Exception as e:
        return {}, {}

# =========================================================
# CSS PERSONALIZADO
# =========================================================

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    .stApp {
        background: white !important;
        font-family: 'Inter', sans-serif;
    }
    
    .main > div {
        background: white;
    }
    
    .header-card {
        background: white;
        border-radius: 16px 16px 0 0;
        padding: 15px 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        border-bottom: 4px solid #3b82f6;
        margin-bottom: 15px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .header-title {
        font-size: 1.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, #2563eb, #8b5cf6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 5px;
    }
    
    .header-subtitle {
        color: #64748b;
        font-weight: 500;
        font-size: 0.95rem;
    }
    
    .period-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: linear-gradient(135deg, #2563eb, #7c3aed);
        color: white;
        padding: 4px 14px;
        border-radius: 50px;
        font-weight: 600;
        margin-top: 8px;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
        font-size: 0.8rem;
    }
    
    .user-info {
        display: flex;
        align-items: center;
        gap: 15px;
        background: #f8fafc;
        padding: 8px 15px;
        border-radius: 50px;
        border: 1px solid #e2e8f0;
    }
    
    .user-badge {
        background: #2563eb;
        color: white;
        padding: 4px 12px;
        border-radius: 50px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    
    .logout-btn {
        background: #ef4444;
        color: white;
        border: none;
        padding: 4px 12px;
        border-radius: 50px;
        font-weight: 600;
        font-size: 0.8rem;
        cursor: pointer;
        transition: all 0.3s;
    }
    
    .logout-btn:hover {
        background: #dc2626;
    }
    
    .filtros-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        border: 1px solid #e2e8f0;
    }
    
    .kpi-card {
        background: white;
        border-radius: 14px;
        padding: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        transition: all 0.3s;
        border: 1px solid #e2e8f0;
        height: 100%;
    }
    
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 16px rgba(37, 99, 235, 0.1);
    }
    
    .kpi-label {
        font-size: 0.8rem;
        color: #64748b;
        margin-bottom: 4px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: 600;
    }
    
    .kpi-value {
        font-size: 2.2rem;
        font-weight: 800;
        line-height: 1;
        margin-bottom: 2px;
    }
    
    .kpi-sub {
        font-size: 0.75rem;
        color: #94a3b8;
    }
    
    .progress-bar {
        width: 100%;
        height: 6px;
        background: #e2e8f0;
        border-radius: 10px;
        margin-top: 8px;
        overflow: hidden;
    }
    
    .progress-fill {
        height: 100%;
        border-radius: 10px;
    }
    
    .section-card {
        background: white;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        border: 1px solid #e2e8f0;
    }
    
    .section-title {
        font-size: 1.2rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 15px;
        padding-bottom: 8px;
        border-bottom: 2px solid #2563eb;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .section-title span {
        background: #2563eb;
        color: white;
        padding: 2px 8px;
        border-radius: 50px;
        font-size: 0.8rem;
        font-weight: 500;
        margin-left: 10px;
    }
    
    .tabela-container {
        overflow-x: auto;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        max-height: 550px;
        overflow-y: auto;
        font-size: 0.8rem;
    }
    
    table {
        width: 100%;
        border-collapse: collapse;
        background: white;
        font-size: 0.75rem;
    }
    
    th {
        background: #f8fafc;
        color: #1e293b;
        font-weight: 600;
        padding: 8px 4px;
        white-space: nowrap;
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.3px;
        border-bottom: 2px solid #2563eb;
        position: sticky;
        top: 0;
        z-index: 10;
    }
    
    td {
        padding: 6px 4px;
        border-bottom: 1px solid #e2e8f0;
        text-align: center;
        font-size: 0.7rem;
    }
    
    .tecnico-nome {
        font-weight: 500;
        text-align: left;
        color: #0f172a;
        white-space: nowrap;
        font-size: 0.7rem;
    }
    
    .status-badge {
        display: inline-block;
        padding: 2px 6px;
        border-radius: 12px;
        font-size: 0.65rem;
        font-weight: 600;
        white-space: nowrap;
    }
    
    .status-ativo {
        background: #10b98120;
        color: #065f46;
    }
    
    .status-folga {
        background: #f59e0b20;
        color: #92400e;
    }
    
    .status-afastado {
        background: #94a3b820;
        color: #475569;
    }
    
    .badge-success {
        background: #10b98120;
        color: #065f46;
        padding: 2px 6px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.65rem;
        display: inline-block;
    }
    
    .badge-warning {
        background: #f59e0b20;
        color: #92400e;
        padding: 2px 6px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.65rem;
        display: inline-block;
    }
    
    .badge-danger {
        background: #ef444420;
        color: #991b1b;
        padding: 2px 6px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.65rem;
        display: inline-block;
    }
    
    .badge-blue {
        background: #2563eb20;
        color: #1e40af;
        padding: 2px 6px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.65rem;
        display: inline-block;
    }
    
    .total-row {
        background: #f8fafc;
        font-weight: 700;
        border-top: 2px solid #2563eb;
        position: sticky;
        bottom: 0;
        z-index: 10;
    }
    
    .total-row td {
        font-weight: 700;
        background: #f8fafc;
    }
    
    .footer {
        text-align: center;
        color: #64748b;
        margin-top: 20px;
        padding: 10px;
        background: #f8fafc;
        border-radius: 10px;
        font-size: 0.8rem;
        border: 1px solid #e2e8f0;
    }
    
    .footer strong {
        color: #0f172a;
    }
    
    div[data-testid="stMetricValue"] {
        font-size: 2.2rem;
        font-weight: 800;
    }
    
    div[data-testid="stMetricLabel"] {
        font-size: 0.8rem;
        text-transform: uppercase;
        color: #64748b;
    }
    
    .stPlotlyChart {
        background: white;
        border-radius: 10px;
        padding: 10px;
        border: 1px solid #e2e8f0;
        height: 300px;
    }
    
    .stSelectbox label {
        font-size: 0.8rem !important;
    }
    
    .graph-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 20px;
        margin-bottom: 20px;
    }
    
    .graph-full {
        margin-top: 20px;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# INICIALIZAR SESSÃO
# =========================================================

inicializar_sessao()

# =========================================================
# VERIFICAR AUTENTICAÇÃO
# =========================================================

if not st.session_state.autenticado:
    tela_login()
    st.stop()

# =========================================================
# CARREGAR DADOS (APENAS SE AUTENTICADO)
# =========================================================

try:
    df = pd.read_excel(CAMINHO_ARQUIVO, header=11)
except Exception as e:
    st.error(f"Erro ao carregar arquivo base.xlsx: {e}")
    st.stop()

mapeamento_tr, df_tecnicos = carregar_dados_presenca()

# =========================================================
# TRATAMENTO DAS COLUNAS
# =========================================================

try:
    df["DATA"] = pd.to_datetime(df["Início Execução"], errors="coerce").dt.date
    df["TECNICO"] = df["Técnico Atribuído"].astype(str)
    df["SA"] = df["Número SA"]
    df["STATUS"] = df["Estado"]
    df["TR"] = df["TECNICO"].apply(extrair_tr)
    df["PRIMEIRO_NOME"] = df["TECNICO"].apply(extrair_primeiro_nome)
    
    def get_info_by_tr(row):
        tr = row["TR"]
        if tr and tr in mapeamento_tr:
            return pd.Series([
                mapeamento_tr[tr]["supervisor"],
                mapeamento_tr[tr]["status"]
            ])
        else:
            return pd.Series(["Não alocado", "Não encontrado"])
    
    df[["SUPERVISOR", "STATUS_TECNICO"]] = df.apply(get_info_by_tr, axis=1)

except Exception as e:
    st.error(f"Erro ao processar dados: {e}")
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
# HEADER PERSONALIZADO COM INFORMAÇÕES DO USUÁRIO
# =========================================================

hoje = date.today()
mes_atual = hoje.strftime("%B de %Y").capitalize()

# Criar header com informações do usuário e botão de logout
col_header1, col_header2 = st.columns([3, 1])

with col_header1:
    st.markdown(f"""
    <div class="header-card">
        <div class="header-title">📊 PAINEL DE PRODUTIVIDADE</div>
        <div class="header-subtitle">01 a {hoje.day} de {mes_atual.lower()} • Atualização automática</div>
        <div class="period-badge">
            <span>📅 ATÉ {hoje.day}/{hoje.month:02d}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_header2:
    usuario_tipo = "👤 Supervisor" if st.session_state.tipo_usuario == "supervisor" else f"🔧 Técnico {st.session_state.usuario}"
    st.markdown(f"""
    <div style="background: white; border-radius: 16px; padding: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); border-bottom: 4px solid #3b82f6; height: 100%; display: flex; flex-direction: column; justify-content: center;">
        <div class="user-info">
            <span class="user-badge">{usuario_tipo}</span>
            <button class="logout-btn" onclick="document.querySelector('#logout').click();">Sair</button>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Botão invisível para logout (clicado via JavaScript)
    if st.button("Logout", key="logout", type="primary", use_container_width=True):
        logout()
        st.rerun()

# =========================================================
# FILTROS (APENAS PARA SUPERVISOR)
# =========================================================

st.markdown('<div class="filtros-card">', unsafe_allow_html=True)

if st.session_state.tipo_usuario == "supervisor":
    col_filtro1, col_filtro2, col_filtro3 = st.columns([2, 2, 2])
    
    with col_filtro1:
        meses_disponiveis = obter_meses_disponiveis(df)
        mes_selecionado = st.selectbox(
            "📅 Selecione o Mês",
            options=meses_disponiveis,
            format_func=lambda x: datetime.strptime(x, "%Y-%m").strftime("%B/%Y").capitalize(),
            index=0,
            key="mes"
        )
    
    with col_filtro2:
        supervisores_disponiveis = sorted(df["SUPERVISOR"].dropna().unique())
        supervisor_selecionado = st.selectbox(
            "👥 Selecione o Supervisor",
            options=["TODOS"] + supervisores_disponiveis,
            key="supervisor"
        )
    
    with col_filtro3:
        tecnicos_disponiveis = sorted(df["PRIMEIRO_NOME"].dropna().astype(str).unique())
        tecnico_selecionado = st.selectbox(
            "👤 Selecione o Técnico",
            options=["TODOS"] + tecnicos_disponiveis,
            key="tecnico"
        )
else:
    # Para técnico, mostrar apenas o mês (sem filtros de supervisor/técnico)
    col_filtro1, col_filtro2 = st.columns([2, 4])
    
    with col_filtro1:
        meses_disponiveis = obter_meses_disponiveis(df)
        mes_selecionado = st.selectbox(
            "📅 Selecione o Mês",
            options=meses_disponiveis,
            format_func=lambda x: datetime.strptime(x, "%Y-%m").strftime("%B/%Y").capitalize(),
            index=0,
            key="mes"
        )
    
    with col_filtro2:
        tr_usuario = st.session_state.tr_usuario
        # Buscar nome do técnico baseado no TR
        nome_tecnico = "Seu perfil"
        for tecnico in df["TECNICO"].unique():
            if tr_usuario in tecnico:
                partes = tecnico.split("(")
                if len(partes) > 1:
                    nome_tecnico = partes[0].strip()
                break
        
        st.markdown(f"""
        <div style="background: #f8fafc; padding: 10px 15px; border-radius: 8px; border: 1px solid #e2e8f0; margin-top: 25px;">
            <span style="color: #2563eb; font-weight: 600;">🔧 Visualizando dados de: {nome_tecnico} ({tr_usuario})</span>
        </div>
        """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# APLICAR FILTROS
# =========================================================

ano_mes_selecionado = mes_selecionado
df_filtrado = df.copy()
df_filtrado["ANO_MES"] = pd.to_datetime(df_filtrado["DATA"]).dt.strftime("%Y-%m")
df_filtrado = df_filtrado[df_filtrado["ANO_MES"] == ano_mes_selecionado]

# Aplicar filtros apenas para supervisor
if st.session_state.tipo_usuario == "supervisor":
    if supervisor_selecionado != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["SUPERVISOR"] == supervisor_selecionado]
    
    if tecnico_selecionado != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["PRIMEIRO_NOME"] == tecnico_selecionado]
else:
    # Para técnico, filtrar apenas pelo seu TR
    tr_usuario = st.session_state.tr_usuario
    df_filtrado = df_filtrado[df_filtrado["TR"] == tr_usuario]

# =========================================================
# KPIS GERAIS
# =========================================================

total_sucesso = df_filtrado[df_filtrado["STATUS"] == "Concluído com sucesso"].shape[0]
total_sem = df_filtrado[df_filtrado["STATUS"] == "Concluído sem sucesso"].shape[0]
total_geral = total_sucesso + total_sem
eficacia_media = (total_sucesso / total_geral * 100) if total_geral > 0 else 0
num_tecnicos = len(df_filtrado["TECNICO"].unique())

# Média diária considerando apenas dias com produção
media_diaria_geral = 0
if num_tecnicos > 0:
    total_dias_com_producao = 0
    for tecnico in df_filtrado["TECNICO"].unique():
        df_tecnico = df_filtrado[df_filtrado["TECNICO"] == tecnico]
        dias_com_producao = obter_dias_com_producao(df_tecnico)
        total_dias_com_producao += dias_com_producao
    
    media_diaria_geral = total_sucesso / total_dias_com_producao if total_dias_com_producao > 0 else 0

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">TOTAL GERAL</div>
        <div class="kpi-value" style="color: #2563eb;">{total_geral}</div>
        <div class="kpi-sub">{num_tecnicos} técnico(s)</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">COM SUCESSO</div>
        <div class="kpi-value" style="color: #10b981;">{total_sucesso}</div>
        <div class="kpi-sub">{eficacia_media:.1f}%</div>
        <div class="progress-bar">
            <div class="progress-fill" style="width: {eficacia_media}%; background: #10b981;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">SEM SUCESSO</div>
        <div class="kpi-value" style="color: #ef4444;">{total_sem}</div>
        <div class="kpi-sub">{100 - eficacia_media:.1f}%</div>
        <div class="progress-bar">
            <div class="progress-fill" style="width: {100 - eficacia_media}%; background: #ef4444;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">MÉDIA/DIA</div>
        <div class="kpi-value" style="color: #f59e0b;">{media_diaria_geral:.2f}</div>
        <div class="kpi-sub">sucesso/dia produtivo</div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">EFICÁCIA</div>
        <div class="kpi-value" style="color: #8b5cf6;">{eficacia_media:.1f}%</div>
        <div class="kpi-sub">Meta 80%</div>
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# TABELA POR TÉCNICO
# =========================================================

st.markdown(f"""
<div class="section-card">
    <div class="section-title">
        TÉCNICOS
        <span>{len(df_filtrado['TECNICO'].unique())} ativo(s)</span>
    </div>
""", unsafe_allow_html=True)

# Agrupar por técnico
tecnicos_unicos = df_filtrado["TECNICO"].unique()
dados_tabela = []

for tecnico in tecnicos_unicos:
    df_tecnico = df_filtrado[df_filtrado["TECNICO"] == tecnico]
    
    if not df_tecnico.empty:
        tr = df_tecnico["TR"].iloc[0] if not df_tecnico["TR"].isna().all() else ""
        primeiro_nome = df_tecnico["PRIMEIRO_NOME"].iloc[0] if not df_tecnico["PRIMEIRO_NOME"].isna().all() else ""
        supervisor = df_tecnico["SUPERVISOR"].iloc[0]
        status_tecnico = df_tecnico["STATUS_TECNICO"].iloc[0]
        
        # Calcular dias com produção para este técnico
        dias_com_producao = obter_dias_com_producao(df_tecnico)
        
        # Inicializar dicionário para dias (apenas sucesso)
        dias = {f"{dia:02d}": 0 for dia in range(1, hoje.day + 1)}
        
        # Preencher dias APENAS com sucesso
        for _, row in df_tecnico.iterrows():
            if pd.notna(row["DATA"]) and row["STATUS"] == "Concluído com sucesso":
                dia = pd.to_datetime(row["DATA"]).day
                if dia <= hoje.day:
                    dias[f"{dia:02d}"] += 1
        
        # Calcular totais
        total_sucesso_tecnico = sum(dias.values())
        total_sem_sucesso_tecnico = df_tecnico[df_tecnico["STATUS"] == "Concluído sem sucesso"].shape[0]
        total_geral_tecnico = total_sucesso_tecnico + total_sem_sucesso_tecnico
        eficacia_tecnico = (total_sucesso_tecnico / total_geral_tecnico * 100) if total_geral_tecnico > 0 else 0
        
        # Média considerando apenas dias com produção
        media_diaria_tecnico = total_sucesso_tecnico / dias_com_producao if dias_com_producao > 0 else 0
        
        # Status class
        status_class = "status-ativo"
        status_texto = str(status_tecnico).lower()
        if "folga" in status_texto:
            status_class = "status-folga"
        elif "afastado" in status_texto or "atestado" in status_texto:
            status_class = "status-afastado"
        
        nome_exibicao = f"{primeiro_nome} {tr}" if primeiro_nome and tr else tecnico[:20]
        
        dados_tabela.append({
            "nome": nome_exibicao,
            "nome_completo": tecnico,
            "status": status_tecnico,
            "status_class": status_class,
            "dias": dias,
            "com_sucesso": total_sucesso_tecnico,
            "sem_sucesso": total_sem_sucesso_tecnico,
            "media": media_diaria_tecnico,
            "eficacia": eficacia_tecnico,
            "total": total_geral_tecnico,
            "dias_produtivos": dias_com_producao
        })

# Ordenar por total de sucesso
dados_tabela.sort(key=lambda x: x["com_sucesso"], reverse=True)

# Criar HTML da tabela
html_tabela = '<div class="tabela-container"><table>'
html_tabela += "<thead><tr>"
html_tabela += "<th>TÉCNICO</th>"
html_tabela += "<th>STATUS</th>"

# Cabeçalhos dos dias
for dia in range(1, hoje.day + 1):
    html_tabela += f"<th>{dia:02d}</th>"

html_tabela += "<th>COM SUCESSO</th>"
html_tabela += "<th>SEM SUCESSO</th>"
html_tabela += "<th>MÉDIA</th>"
html_tabela += "<th>EFICÁCIA</th>"
html_tabela += "<th>TOTAL</th>"
html_tabela += "</tr></thead><tbody>"

# Linhas dos técnicos
for tecnico in dados_tabela:
    html_tabela += "<tr>"
    html_tabela += f'<td class="tecnico-nome" title="{tecnico["nome_completo"]}">{tecnico["nome"]}</td>'
    html_tabela += f'<td><span class="status-badge {tecnico["status_class"]}">{tecnico["status"]}</span></td>'
    
    # Dias (apenas sucesso)
    for dia in range(1, hoje.day + 1):
        valor = tecnico["dias"][f"{dia:02d}"]
        if valor >= 4:
            html_tabela += f'<td style="background: #10b98120; color: #065f46; font-weight: 600;">{valor}</td>'
        elif valor == 3:
            html_tabela += f'<td style="background: #f59e0b20; color: #92400e; font-weight: 600;">{valor}</td>'
        elif valor > 0:
            html_tabela += f'<td style="background: #ef444420; color: #991b1b; font-weight: 600;">{valor}</td>'
        else:
            html_tabela += f"<td>{valor}</td>"
    
    # Colunas finais
    html_tabela += f'<td><span class="badge-success">{tecnico["com_sucesso"]}</span></td>'
    html_tabela += f'<td><span class="badge-danger">{tecnico["sem_sucesso"]}</span></td>'
    html_tabela += f'<td><span class="badge-warning">{tecnico["media"]:.1f}</span></td>'
    
    # Eficácia
    if tecnico["eficacia"] >= 80:
        badge_class = "badge-success"
    elif tecnico["eficacia"] >= 60:
        badge_class = "badge-warning"
    else:
        badge_class = "badge-danger"
    html_tabela += f'<td><span class="{badge_class}">{tecnico["eficacia"]:.0f}%</span></td>'
    
    html_tabela += f'<td><strong>{tecnico["total"]}</strong></td>'
    html_tabela += "</tr>"

# Linha de total
if dados_tabela and st.session_state.tipo_usuario == "supervisor":
    total_com_sucesso = sum(t["com_sucesso"] for t in dados_tabela)
    total_sem_sucesso = sum(t["sem_sucesso"] for t in dados_tabela)
    total_geral_geral = sum(t["total"] for t in dados_tabela)
    eficacia_geral = (total_com_sucesso / total_geral_geral * 100) if total_geral_geral > 0 else 0
    
    # Média geral considerando dias produtivos
    total_dias_produtivos = sum(t["dias_produtivos"] for t in dados_tabela)
    media_diaria_geral_tabela = total_com_sucesso / total_dias_produtivos if total_dias_produtivos > 0 else 0
    
    html_tabela += '<tr class="total-row">'
    html_tabela += f'<td colspan="2" style="font-weight:700;">TOTAL</td>'
    for dia in range(1, hoje.day + 1):
        total_dia = sum(t["dias"][f"{dia:02d}"] for t in dados_tabela)
        html_tabela += f"<td><strong>{total_dia}</strong></td>"
    html_tabela += f'<td><strong>{total_com_sucesso}</strong></td>'
    html_tabela += f'<td><strong>{total_sem_sucesso}</strong></td>'
    html_tabela += f'<td><span class="badge-warning">{media_diaria_geral_tabela:.1f}</span></td>'
    html_tabela += f'<td><span class="badge-blue">{eficacia_geral:.0f}%</span></td>'
    html_tabela += f'<td><strong>{total_geral_geral}</strong></td>'
    html_tabela += "</tr>"

html_tabela += "</tbody></table></div>"

st.markdown(html_tabela, unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# GRÁFICOS (APENAS PARA SUPERVISOR OU SE TÉCNICO TIVER DADOS)
# =========================================================

if not df_filtrado.empty:
    # Preparar dados para os gráficos
    df_grafico = df_filtrado.copy()
    df_grafico["DIA"] = pd.to_datetime(df_grafico["DATA"]).dt.day
    df_grafico = df_grafico[df_grafico["DIA"] <= hoje.day]
    
    # Dados para gráfico de sucesso
    df_sucesso = df_grafico[df_grafico["STATUS"] == "Concluído com sucesso"].groupby("DIA").size().reset_index(name="COUNT")
    df_sucesso = df_sucesso.rename(columns={"COUNT": "SUCESSO"})
    
    # Dados para gráfico de pendências
    df_pendencias = df_grafico[df_grafico["STATUS"] == "Concluído sem sucesso"].groupby("DIA").size().reset_index(name="COUNT")
    df_pendencias = df_pendencias.rename(columns={"COUNT": "PENDENCIAS"})
    
    # Combinar dados
    df_combinado = pd.merge(df_sucesso, df_pendencias, on="DIA", how="outer").fillna(0)
    df_combinado = df_combinado.sort_values("DIA")
    
    if not df_combinado.empty:
        st.markdown("""
        <div class="section-card">
            <div class="section-title">
                EVOLUÇÃO DIÁRIA
            </div>
        """, unsafe_allow_html=True)
        
        # Criar grid de 2 colunas para os gráficos de barras
        st.markdown('<div class="graph-grid">', unsafe_allow_html=True)
        
        col_graph1, col_graph2 = st.columns(2)
        
        with col_graph1:
            fig1 = px.bar(
                df_combinado,
                x="DIA",
                y="SUCESSO",
                title="Atividades com Sucesso por Dia",
                color_discrete_sequence=["#10b981"]
            )
            
            fig1.update_traces(
                marker=dict(line=dict(width=1, color="white"))
            )
            
            fig1.update_layout(
                plot_bgcolor="white",
                paper_bgcolor="white",
                font_family="Inter",
                font_size=11,
                showlegend=False,
                height=300,
                margin=dict(l=20, r=20, t=40, b=20),
                xaxis=dict(
                    showgrid=True,
                    gridcolor="#e2e8f0",
                    title="Dia",
                    tickmode="linear",
                    tick0=1,
                    dtick=1
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor="#e2e8f0",
                    title="Quantidade",
                    tickmode="linear",
                    tick0=0,
                    dtick=5
                )
            )
            
            st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': False})
        
        with col_graph2:
            fig2 = px.bar(
                df_combinado,
                x="DIA",
                y="PENDENCIAS",
                title="Atividades sem Sucesso por Dia",
                color_discrete_sequence=["#ef4444"]
            )
            
            fig2.update_traces(
                marker=dict(line=dict(width=1, color="white"))
            )
            
            fig2.update_layout(
                plot_bgcolor="white",
                paper_bgcolor="white",
                font_family="Inter",
                font_size=11,
                showlegend=False,
                height=300,
                margin=dict(l=20, r=20, t=40, b=20),
                xaxis=dict(
                    showgrid=True,
                    gridcolor="#e2e8f0",
                    title="Dia",
                    tickmode="linear",
                    tick0=1,
                    dtick=1
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor="#e2e8f0",
                    title="Quantidade",
                    tickmode="linear",
                    tick0=0,
                    dtick=5
                )
            )
            
            st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Gráfico de linhas (com sucesso e sem sucesso)
        st.markdown('<div class="graph-full">', unsafe_allow_html=True)
        
        total_atividades = int(df_combinado["SUCESSO"].sum() + df_combinado["PENDENCIAS"].sum())
        
        fig3 = go.Figure()
        
        fig3.add_trace(go.Scatter(
            x=df_combinado["DIA"],
            y=df_combinado["SUCESSO"],
            mode='lines+markers',
            name='Com Sucesso',
            line=dict(color='#10b981', width=3),
            marker=dict(size=8, color='#10b981', line=dict(width=1, color='white'))
        ))
        
        fig3.add_trace(go.Scatter(
            x=df_combinado["DIA"],
            y=df_combinado["PENDENCIAS"],
            mode='lines+markers',
            name='Sem Sucesso',
            line=dict(color='#ef4444', width=3),
            marker=dict(size=8, color='#ef4444', line=dict(width=1, color='white'))
        ))
        
        fig3.update_layout(
            title=f"Evolução Diária - Total: {total_atividades} atividades",
            plot_bgcolor="white",
            paper_bgcolor="white",
            font_family="Inter",
            font_size=12,
            height=350,
            margin=dict(l=20, r=20, t=50, b=30),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            xaxis=dict(
                showgrid=True,
                gridcolor="#e2e8f0",
                title="Dia",
                tickmode="linear",
                tick0=1,
                dtick=1
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor="#e2e8f0",
                title="Quantidade",
                tickmode="linear",
                tick0=0,
                dtick=10
            ),
            hovermode="x unified"
        )
        
        st.plotly_chart(fig3, use_container_width=True, config={'displayModeBar': False})
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# FOOTER
# =========================================================

st.markdown(f"""
<div class="footer">
    <strong>PAINEL DE PRODUTIVIDADE</strong> • Dados até {hoje.day}/{hoje.month:02d}/{hoje.year} • Total: {total_geral} • Com Sucesso: {total_sucesso} ({eficacia_media:.0f}%) • Sem Sucesso: {total_sem} • Média: {media_diaria_geral:.1f}/dia produtivo
</div>
""", unsafe_allow_html=True)