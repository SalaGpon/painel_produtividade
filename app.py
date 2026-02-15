import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import calendar
import re
import psycopg2
import os

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
    login = login.strip().upper()
    senha = senha.strip().upper()
    
    if login == "TR0000" and senha == "SUPMASTER":
        st.session_state.autenticado = True
        st.session_state.usuario = "SUPERVISOR"
        st.session_state.tipo_usuario = "supervisor"
        st.session_state.tr_usuario = None
        return True, "supervisor"
    
    if re.match(r'^TR\d+$', login) and senha == login:
        st.session_state.autenticado = True
        st.session_state.usuario = login
        st.session_state.tipo_usuario = "tecnico"
        st.session_state.tr_usuario = login
        return True, "tecnico"
    
    return False, None

def logout():
    st.session_state.autenticado = False
    st.session_state.usuario = None
    st.session_state.tipo_usuario = None
    st.session_state.tr_usuario = None

def tela_login():
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
        }
    </style>
    """, unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.markdown('<div class="login-title">PAINEL DE PRODUTIVIDADE</div>', unsafe_allow_html=True)
        
        with st.form("login_form"):
            login = st.text_input("Login", placeholder="Digite seu TR (ex: TR12345) ou TR0000")
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

def extrair_tr(nome_completo):
    """Extrai o TR do formato 'NOME (TR123456)'"""
    if pd.isna(nome_completo):
        return ""
    match = re.search(r'(TR\d+|TT\d+|TC\d+)', str(nome_completo))
    return match.group(1) if match else ""

def extrair_nome_limpo(nome_completo):
    """Extrai apenas o nome sem o TR do formato 'NOME (TR123456)'"""
    if pd.isna(nome_completo):
        return ""
    nome_limpo = re.sub(r'\s*\(.*\)', '', str(nome_completo)).strip()
    return nome_limpo

def extrair_primeiro_nome(nome_completo):
    """Extrai apenas o primeiro nome do técnico"""
    if pd.isna(nome_completo):
        return ""
    nome_limpo = extrair_nome_limpo(nome_completo)
    return nome_limpo.split()[0] if nome_limpo else ""

def extrair_ultimo_sobrenome(nome_completo):
    """Extrai o último sobrenome do técnico"""
    if pd.isna(nome_completo):
        return ""
    nome_limpo = extrair_nome_limpo(nome_completo)
    partes = nome_limpo.split()
    return partes[-1] if len(partes) > 1 else ""

def formatar_nome_exibicao(nome_completo):
    """Formata o nome como 'Primeiro Nome + Último Sobrenome'"""
    if pd.isna(nome_completo):
        return ""
    nome_limpo = extrair_nome_limpo(nome_completo)
    partes = nome_limpo.split()
    if len(partes) >= 2:
        return f"{partes[0]} {partes[-1]}"
    elif len(partes) == 1:
        return partes[0]
    return ""

def obter_dias_com_producao(df_tecnico):
    """Retorna o número de dias em que o técnico teve pelo menos uma atividade"""
    if df_tecnico.empty:
        return 0
    dias_com_atividade = set()
    for _, row in df_tecnico.iterrows():
        if pd.notna(row["DATA"]):
            dia = pd.to_datetime(row["DATA"]).day
            dias_com_atividade.add(dia)
    return len(dias_com_atividade)

def obter_meses_disponiveis(df):
    """Retorna lista de meses disponíveis no DataFrame"""
    if "DATA" in df.columns and not df["DATA"].isna().all():
        meses = df["DATA"].apply(lambda x: x.strftime("%Y-%m") if hasattr(x, 'strftime') else None)
        meses = meses.dropna().unique()
        return sorted(meses, reverse=True)
    return [datetime.now().strftime("%Y-%m")]

def obter_ultimo_dia_mes(ano_mes):
    """Retorna o último dia do mês (considerando data atual se for mês corrente)"""
    ano = int(ano_mes[:4])
    mes = int(ano_mes[5:7])
    
    hoje = date.today()
    
    if ano == hoje.year and mes == hoje.month:
        return hoje.day
    else:
        return calendar.monthrange(ano, mes)[1]

# =========================================================
# CONEXÃO COM SUPABASE (FUNCIONA LOCAL E CLOUD)
# =========================================================

def get_db_url():
    """
    Retorna a URL do banco de dados.
    Funciona nos dois ambientes sem precisar de python-dotenv
    """
    try:
        # Tenta pegar das secrets do Streamlit Cloud (funciona no deploy)
        return st.secrets["DB_URL"]
    except:
        # Se não encontrar, significa que está rodando local
        # Usa a string fixa (você pode comentar/descomentar conforme necessário)
        
        # OPÇÃO 1: String fixa (mais simples)
        DB_URL = "postgresql://postgres.bfamfgjjitrfcdyzuibd:#Lucasd15m10@aws-1-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require"
        
        # OPÇÃO 2: Variável de ambiente (se preferir)
        # DB_URL = os.environ.get("DB_URL")
        
        if DB_URL:
            return DB_URL
        else:
            st.error("""
            ❌ Configuração do banco não encontrada!
            
            Para executar localmente:
            - Use a string fixa no código
            
            Para executar no Streamlit Cloud:
            1. Vá em Settings > Secrets
            2. Adicione: DB_URL = "sua_string_de_conexao"
            """)
            return None

def obter_data_atualizacao():
    """Retorna a data da última atualização dos dados"""
    try:
        DB_URL = get_db_url()
        if not DB_URL:
            return None
        
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        # Buscar a data da última OS inserida
        cur.execute("SELECT MAX(inicio_execucao) FROM ordens_servico")
        ultima_os = cur.fetchone()[0]
        
        # Buscar a data da última atualização do banco (registro mais recente)
        cur.execute("SELECT created_at FROM ordens_servico ORDER BY created_at DESC LIMIT 1")
        ultima_atualizacao = cur.fetchone()[0]
        
        cur.close()
        conn.close()
        
        # Se tiver data da OS, usa ela, senão usa a data de criação
        if ultima_os:
            return ultima_os
        elif ultima_atualizacao:
            return ultima_atualizacao
        else:
            return datetime.now()
            
    except Exception as e:
        print(f"Erro ao buscar data de atualização: {e}")
        return datetime.now()

@st.cache_data(ttl=300)  # Cache de 5 minutos
def carregar_dados_os():
    """Carrega dados das ordens de serviço do Supabase"""
    try:
        DB_URL = get_db_url()
        if not DB_URL:
            return pd.DataFrame()
        
        conn = psycopg2.connect(DB_URL)
        
        query = """
        SELECT 
            inicio_execucao as "Início Execução",
            tecnico_atribuido as "Técnico Atribuído",
            numero_sa as "Número SA",
            estado as "Estado"
        FROM ordens_servico
        WHERE estado IN ('Concluído com sucesso', 'Concluído sem sucesso')
        ORDER BY inicio_execucao DESC
        """
        
        df = pd.read_sql(query, conn)
        conn.close()
        
        df["Início Execução"] = pd.to_datetime(df["Início Execução"])
        df["DATA"] = df["Início Execução"].dt.date
        
        return df
        
    except Exception as e:
        st.error(f"Erro ao carregar dados das OS: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=600)  # Cache de 10 minutos
def carregar_dados_tecnicos():
    """Carrega dados dos técnicos (supervisores e status) do Supabase"""
    try:
        DB_URL = get_db_url()
        if not DB_URL:
            return pd.DataFrame()
        
        conn = psycopg2.connect(DB_URL)
        
        query = """
        SELECT 
            tr,
            tt,
            funcionario,
            supervisor,
            status,
            setor_atual,
            faz_os_2
        FROM tecnicos
        """
        
        df = pd.read_sql(query, conn)
        conn.close()
        
        return df
        
    except Exception as e:
        st.warning(f"⚠️ Erro ao carregar dados dos técnicos: {e}")
        return pd.DataFrame()

# =========================================================
# INICIALIZAR SESSÃO
# =========================================================

inicializar_sessao()

if not st.session_state.autenticado:
    tela_login()
    st.stop()

# =========================================================
# CARREGAR DADOS
# =========================================================

# Carregar ordens de serviço
df_os = carregar_dados_os()

if df_os.empty:
    st.error("❌ Não foi possível carregar os dados. Verifique a conexão com o banco.")
    st.stop()

# Carregar dados dos técnicos (supervisores)
df_tecnicos = carregar_dados_tecnicos()

# Extrair informações das OS
df_os["TECNICO"] = df_os["Técnico Atribuído"].astype(str)
df_os["TR"] = df_os["TECNICO"].apply(extrair_tr)
df_os["NOME_COMPLETO"] = df_os["TECNICO"].apply(extrair_nome_limpo)
df_os["PRIMEIRO_NOME"] = df_os["TECNICO"].apply(extrair_primeiro_nome)
df_os["ULTIMO_SOBRENOME"] = df_os["TECNICO"].apply(extrair_ultimo_sobrenome)
df_os["NOME_EXIBICAO"] = df_os["TECNICO"].apply(formatar_nome_exibicao)

# Mapear supervisor e status a partir do TR
supervisor_map = {}
status_map = {}

if not df_tecnicos.empty:
    # Criar dicionários de mapeamento
    for _, row in df_tecnicos.iterrows():
        tr = str(row['tr']).strip() if pd.notna(row['tr']) else ''
        if tr:
            supervisor_map[tr] = str(row['supervisor']) if pd.notna(row['supervisor']) else 'Não alocado'
            status_map[tr] = str(row['status']) if pd.notna(row['status']) else 'Ativo'

# Aplicar mapeamento
df_os["SUPERVISOR"] = df_os["TR"].map(supervisor_map).fillna("Não alocado")
df_os["STATUS_TECNICO"] = df_os["TR"].map(status_map).fillna("Ativo")

# =========================================================
# HEADER COM DATA DA ÚLTIMA ATUALIZAÇÃO E BOTÃO
# =========================================================

hoje = date.today()
mes_atual = hoje.strftime("%B de %Y").capitalize()
data_atualizacao = obter_data_atualizacao()
data_formatada = data_atualizacao.strftime("%d/%m/%Y %H:%M") if data_atualizacao else "N/A"

col_header1, col_header2, col_header3 = st.columns([2, 1, 1])

with col_header1:
    st.markdown(f"""
    <div style="background: white; border-radius: 16px 16px 0 0; padding: 15px 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); border-bottom: 4px solid #3b82f6; margin-bottom: 15px;">
        <div style="font-size: 1.8rem; font-weight: 800; background: linear-gradient(135deg, #2563eb, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 5px;">📊 PAINEL DE PRODUTIVIDADE</div>
        <div style="color: #64748b; font-weight: 500; font-size: 0.95rem;">Atualização automática</div>
        <div style="display: inline-flex; align-items: center; gap: 6px; background: linear-gradient(135deg, #2563eb, #7c3aed); color: white; padding: 4px 14px; border-radius: 50px; font-weight: 600; margin-top: 8px; box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2); font-size: 0.8rem;">
            <span>📅 ÚLTIMA ATUALIZAÇÃO: {data_formatada}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_header2:
    st.markdown(f"""
    <div style="background: #f8fafc; padding: 8px 15px; border-radius: 50px; border: 1px solid #e2e8f0; text-align: center;">
        <span style="background: #2563eb; color: white; padding: 4px 12px; border-radius: 50px; font-weight: 600; font-size: 0.8rem;">
            {st.session_state.usuario if st.session_state.tipo_usuario == "supervisor" else f"Técnico {st.session_state.tr_usuario}"}
        </span>
    </div>
    """, unsafe_allow_html=True)

with col_header3:
    if st.button("🔄 Atualizar Agora", use_container_width=True, type="primary"):
        st.cache_data.clear()
        st.rerun()

# =========================================================
# FILTROS
# =========================================================

st.markdown('<div style="background: white; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); border: 1px solid #e2e8f0;">', unsafe_allow_html=True)

col_filtro1, col_filtro2, col_filtro3 = st.columns([2, 2, 2])

with col_filtro1:
    meses_disponiveis = obter_meses_disponiveis(df_os)
    mes_selecionado = st.selectbox(
        "📅 Selecione o Mês",
        options=meses_disponiveis,
        format_func=lambda x: datetime.strptime(x, "%Y-%m").strftime("%B/%Y").capitalize(),
        index=0,
        key="mes"
    )
    
    # Obter o último dia do mês selecionado
    ultimo_dia_mes = obter_ultimo_dia_mes(mes_selecionado)
    st.caption(f"📆 Mostrando dados de 01 a {ultimo_dia_mes}")

with col_filtro2:
    if st.session_state.tipo_usuario == "supervisor":
        # Lista de supervisores do banco de dados
        supervisores_list = ["TODOS"] + sorted(df_os["SUPERVISOR"].dropna().unique())
        supervisor_selecionado = st.selectbox(
            "👥 Selecione o Supervisor",
            options=supervisores_list,
            key="supervisor"
        )
    else:
        st.info("🔧 Visualizando seus dados")

with col_filtro3:
    if st.session_state.tipo_usuario == "supervisor":
        # Lista de técnicos para filtro adicional (usando nome de exibição)
        tecnicos_list = ["TODOS"] + sorted(df_os["NOME_EXIBICAO"].dropna().astype(str).unique())
        tecnico_selecionado = st.selectbox(
            "👤 Selecione o Técnico",
            options=tecnicos_list,
            key="tecnico"
        )

# Mostrar estatísticas dos supervisores (opcional)
if st.session_state.tipo_usuario == "supervisor" and not df_tecnicos.empty:
    with st.expander("📊 Estatísticas dos Supervisores"):
        sup_counts = df_tecnicos['supervisor'].value_counts().reset_index()
        sup_counts.columns = ['Supervisor', 'Quantidade de Técnicos']
        st.dataframe(sup_counts, use_container_width=True, hide_index=True)

st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# APLICAR FILTROS
# =========================================================

df_filtrado = df_os[df_os["DATA"].apply(lambda x: x.strftime("%Y-%m")) == mes_selecionado]

if st.session_state.tipo_usuario == "supervisor":
    if 'supervisor_selecionado' in locals() and supervisor_selecionado != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["SUPERVISOR"] == supervisor_selecionado]
    if 'tecnico_selecionado' in locals() and tecnico_selecionado != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["NOME_EXIBICAO"] == tecnico_selecionado]
else:
    df_filtrado = df_filtrado[df_filtrado["TR"] == st.session_state.tr_usuario]

# =========================================================
# KPIS GERAIS
# =========================================================

total_sucesso = df_filtrado[df_filtrado["Estado"] == "Concluído com sucesso"].shape[0]
total_sem = df_filtrado[df_filtrado["Estado"] == "Concluído sem sucesso"].shape[0]
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
    <div style="background: white; border-radius: 14px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); border: 1px solid #e2e8f0; height: 100%;">
        <div style="font-size: 0.8rem; color: #64748b; text-transform: uppercase; font-weight: 600;">TOTAL GERAL</div>
        <div style="font-size: 2.2rem; font-weight: 800; color: #2563eb;">{total_geral}</div>
        <div style="font-size: 0.75rem; color: #94a3b8;">{num_tecnicos} técnico(s)</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div style="background: white; border-radius: 14px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); border: 1px solid #e2e8f0; height: 100%;">
        <div style="font-size: 0.8rem; color: #64748b; text-transform: uppercase; font-weight: 600;">COM SUCESSO</div>
        <div style="font-size: 2.2rem; font-weight: 800; color: #10b981;">{total_sucesso}</div>
        <div style="font-size: 0.75rem; color: #94a3b8;">{eficacia_media:.1f}%</div>
        <div style="width: 100%; height: 6px; background: #e2e8f0; border-radius: 10px; margin-top: 8px; overflow: hidden;">
            <div style="height: 100%; width: {eficacia_media}%; background: #10b981;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div style="background: white; border-radius: 14px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); border: 1px solid #e2e8f0; height: 100%;">
        <div style="font-size: 0.8rem; color: #64748b; text-transform: uppercase; font-weight: 600;">SEM SUCESSO</div>
        <div style="font-size: 2.2rem; font-weight: 800; color: #ef4444;">{total_sem}</div>
        <div style="font-size: 0.75rem; color: #94a3b8;">{100 - eficacia_media:.1f}%</div>
        <div style="width: 100%; height: 6px; background: #e2e8f0; border-radius: 10px; margin-top: 8px; overflow: hidden;">
            <div style="height: 100%; width: {100 - eficacia_media}%; background: #ef4444;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div style="background: white; border-radius: 14px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); border: 1px solid #e2e8f0; height: 100%;">
        <div style="font-size: 0.8rem; color: #64748b; text-transform: uppercase; font-weight: 600;">MÉDIA/DIA</div>
        <div style="font-size: 2.2rem; font-weight: 800; color: #f59e0b;">{media_diaria_geral:.2f}</div>
        <div style="font-size: 0.75rem; color: #94a3b8;">sucesso/dia produtivo</div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    st.markdown(f"""
    <div style="background: white; border-radius: 14px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); border: 1px solid #e2e8f0; height: 100%;">
        <div style="font-size: 0.8rem; color: #64748b; text-transform: uppercase; font-weight: 600;">EFICÁCIA</div>
        <div style="font-size: 2.2rem; font-weight: 800; color: #8b5cf6;">{eficacia_media:.1f}%</div>
        <div style="font-size: 0.75rem; color: #94a3b8;">Meta 80%</div>
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# TABELA POR TÉCNICO
# =========================================================

st.markdown(f"""
<div style="background: white; border-radius: 16px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); border: 1px solid #e2e8f0;">
    <div style="font-size: 1.2rem; font-weight: 700; color: #0f172a; margin-bottom: 15px; padding-bottom: 8px; border-bottom: 2px solid #2563eb; display: flex; align-items: center;">
        TÉCNICOS - {datetime.strptime(mes_selecionado, "%Y-%m").strftime("%B/%Y").upper()}
        <span style="background: #2563eb; color: white; padding: 2px 8px; border-radius: 50px; font-size: 0.8rem; font-weight: 500; margin-left: 10px;">{len(df_filtrado['TECNICO'].unique())} ativo(s)</span>
    </div>
""", unsafe_allow_html=True)

# Agrupar por técnico
tecnicos_unicos = df_filtrado["TECNICO"].unique()
dados_tabela = []

# Usar o último dia do mês selecionado para a tabela
dias_no_mes = ultimo_dia_mes

for tecnico in tecnicos_unicos:
    df_tecnico = df_filtrado[df_filtrado["TECNICO"] == tecnico]
    
    if not df_tecnico.empty:
        tr = df_tecnico["TR"].iloc[0] if not df_tecnico["TR"].isna().all() else ""
        nome_exibicao = df_tecnico["NOME_EXIBICAO"].iloc[0] if not df_tecnico["NOME_EXIBICAO"].isna().all() else ""
        supervisor = df_tecnico["SUPERVISOR"].iloc[0]
        status_tecnico = df_tecnico["STATUS_TECNICO"].iloc[0]
        
        dias_com_producao = obter_dias_com_producao(df_tecnico)
        
        dias = {f"{dia:02d}": 0 for dia in range(1, dias_no_mes + 1)}
        
        for _, row in df_tecnico.iterrows():
            if pd.notna(row["DATA"]) and row["Estado"] == "Concluído com sucesso":
                dia = pd.to_datetime(row["DATA"]).day
                if dia <= dias_no_mes:
                    dias[f"{dia:02d}"] += 1
        
        total_sucesso_tecnico = sum(dias.values())
        total_sem_sucesso_tecnico = df_tecnico[df_tecnico["Estado"] == "Concluído sem sucesso"].shape[0]
        total_geral_tecnico = total_sucesso_tecnico + total_sem_sucesso_tecnico
        eficacia_tecnico = (total_sucesso_tecnico / total_geral_tecnico * 100) if total_geral_tecnico > 0 else 0
        media_diaria_tecnico = total_sucesso_tecnico / dias_com_producao if dias_com_producao > 0 else 0
        
        # Determinar classe do status
        status_class = "Ativo"
        status_lower = str(status_tecnico).lower()
        if "folga" in status_lower:
            status_class = "Folga"
        elif "afastado" in status_lower or "atestado" in status_lower:
            status_class = "Afastado"
        elif "veiculo" in status_lower or "avaria" in status_lower:
            status_class = "Problema Veículo"
        
        dados_tabela.append({
            "nome_exibicao": nome_exibicao,
            "tr": tr,
            "nome_completo": tecnico,
            "status": status_class,
            "status_original": status_tecnico,
            "supervisor": supervisor,
            "dias": dias,
            "com_sucesso": total_sucesso_tecnico,
            "sem_sucesso": total_sem_sucesso_tecnico,
            "media": media_diaria_tecnico,
            "eficacia": eficacia_tecnico,
            "total": total_geral_tecnico
        })

dados_tabela.sort(key=lambda x: x["com_sucesso"], reverse=True)

# Criar HTML da tabela
html_tabela = '<div style="overflow-x: auto; border-radius: 8px; border: 1px solid #e2e8f0; max-height: 550px; overflow-y: auto;"><table style="width: 100%; border-collapse: collapse; font-size: 0.75rem;">'
html_tabela += "<thead><tr>"
html_tabela += "<th style='background: #f8fafc; padding: 8px 4px; position: sticky; top: 0;'>NOME</th>"
html_tabela += "<th style='background: #f8fafc; padding: 8px 4px; position: sticky; top: 0;'>TR</th>"
html_tabela += "<th style='background: #f8fafc; padding: 8px 4px; position: sticky; top: 0;'>STATUS</th>"

for dia in range(1, dias_no_mes + 1):
    html_tabela += f"<th style='background: #f8fafc; padding: 8px 4px; position: sticky; top: 0;'>{dia:02d}</th>"

html_tabela += "<th style='background: #f8fafc; padding: 8px 4px; position: sticky; top: 0;'>COM SUCESSO</th>"
html_tabela += "<th style='background: #f8fafc; padding: 8px 4px; position: sticky; top: 0;'>SEM SUCESSO</th>"
html_tabela += "<th style='background: #f8fafc; padding: 8px 4px; position: sticky; top: 0;'>MÉDIA</th>"
html_tabela += "<th style='background: #f8fafc; padding: 8px 4px; position: sticky; top: 0;'>EFICÁCIA</th>"
html_tabela += "<th style='background: #f8fafc; padding: 8px 4px; position: sticky; top: 0;'>TOTAL</th>"
html_tabela += "</tr></thead><tbody>"

for tecnico in dados_tabela:
    html_tabela += "<tr>"
    html_tabela += f'<td style="padding: 6px 4px; text-align: left; font-weight: 500;" title="{tecnico["nome_completo"]}">{tecnico["nome_exibicao"]}</td>'
    html_tabela += f'<td style="padding: 6px 4px;"><span style="background: #e2e8f0; color: #0f172a; padding: 2px 6px; border-radius: 12px; font-size: 0.65rem;">{tecnico["tr"]}</span></td>'
    html_tabela += f'<td style="padding: 6px 4px;"><span style="background: #e2e8f0; color: #0f172a; padding: 2px 6px; border-radius: 12px; font-size: 0.65rem;">{tecnico["status"]}</span></td>'
    
    for dia in range(1, dias_no_mes + 1):
        valor = tecnico["dias"][f"{dia:02d}"]
        if valor >= 4:
            html_tabela += f'<td style="padding: 6px 4px; background: #10b98120; color: #065f46; font-weight: 600;">{valor}</td>'
        elif valor == 3:
            html_tabela += f'<td style="padding: 6px 4px; background: #f59e0b20; color: #92400e; font-weight: 600;">{valor}</td>'
        elif valor > 0:
            html_tabela += f'<td style="padding: 6px 4px; background: #ef444420; color: #991b1b; font-weight: 600;">{valor}</td>'
        else:
            html_tabela += f"<td style='padding: 6px 4px;'>{valor}</td>"
    
    html_tabela += f'<td style="padding: 6px 4px;"><span style="background: #10b98120; color: #065f46; padding: 2px 6px; border-radius: 20px; font-weight: 600;">{tecnico["com_sucesso"]}</span></td>'
    html_tabela += f'<td style="padding: 6px 4px;"><span style="background: #ef444420; color: #991b1b; padding: 2px 6px; border-radius: 20px; font-weight: 600;">{tecnico["sem_sucesso"]}</span></td>'
    html_tabela += f'<td style="padding: 6px 4px;"><span style="background: #f59e0b20; color: #92400e; padding: 2px 6px; border-radius: 20px; font-weight: 600;">{tecnico["media"]:.1f}</span></td>'
    
    if tecnico["eficacia"] >= 80:
        badge_class = "success"
        bg = "#10b98120"
        cor = "#065f46"
    elif tecnico["eficacia"] >= 60:
        badge_class = "warning"
        bg = "#f59e0b20"
        cor = "#92400e"
    else:
        badge_class = "danger"
        bg = "#ef444420"
        cor = "#991b1b"
    html_tabela += f'<td style="padding: 6px 4px;"><span style="background: {bg}; color: {cor}; padding: 2px 6px; border-radius: 20px; font-weight: 600;">{tecnico["eficacia"]:.0f}%</span></td>'
    
    html_tabela += f'<td style="padding: 6px 4px;"><strong>{tecnico["total"]}</strong></td>'
    html_tabela += "</tr>"

if dados_tabela and st.session_state.tipo_usuario == "supervisor":
    total_com_sucesso = sum(t["com_sucesso"] for t in dados_tabela)
    total_sem_sucesso = sum(t["sem_sucesso"] for t in dados_tabela)
    total_geral_geral = sum(t["total"] for t in dados_tabela)
    eficacia_geral = (total_com_sucesso / total_geral_geral * 100) if total_geral_geral > 0 else 0
    media_diaria_geral = total_com_sucesso / (len(dados_tabela) * dias_no_mes) if len(dados_tabela) > 0 else 0
    
    html_tabela += '<tr style="background: #f8fafc; font-weight: 700; border-top: 2px solid #2563eb;">'
    html_tabela += f'<td colspan="4" style="padding: 6px 4px; font-weight:700;">TOTAL</td>'
    for dia in range(1, dias_no_mes + 1):
        total_dia = sum(t["dias"][f"{dia:02d}"] for t in dados_tabela)
        html_tabela += f"<td style='padding: 6px 4px;'><strong>{total_dia}</strong></td>"
    html_tabela += f'<td style="padding: 6px 4px;"><strong>{total_com_sucesso}</strong></td>'
    html_tabela += f'<td style="padding: 6px 4px;"><strong>{total_sem_sucesso}</strong></td>'
    html_tabela += f'<td style="padding: 6px 4px;"><span style="background: #f59e0b20; color: #92400e; padding: 2px 6px; border-radius: 20px; font-weight: 600;">{media_diaria_geral:.1f}</span></td>'
    html_tabela += f'<td style="padding: 6px 4px;"><span style="background: #2563eb20; color: #1e40af; padding: 2px 6px; border-radius: 20px; font-weight: 600;">{eficacia_geral:.0f}%</span></td>'
    html_tabela += f'<td style="padding: 6px 4px;"><strong>{total_geral_geral}</strong></td>'
    html_tabela += "</tr>"

html_tabela += "</tbody></table></div>"

st.markdown(html_tabela, unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# GRÁFICOS
# =========================================================

if not df_filtrado.empty:
    df_grafico = df_filtrado.copy()
    df_grafico["DIA"] = pd.to_datetime(df_grafico["DATA"]).dt.day
    df_grafico = df_grafico[df_grafico["DIA"] <= dias_no_mes]
    
    df_sucesso = df_grafico[df_grafico["Estado"] == "Concluído com sucesso"].groupby("DIA").size().reset_index(name="SUCESSO")
    df_pendencias = df_grafico[df_grafico["Estado"] == "Concluído sem sucesso"].groupby("DIA").size().reset_index(name="PENDENCIAS")
    
    df_combinado = pd.merge(df_sucesso, df_pendencias, on="DIA", how="outer").fillna(0)
    df_combinado = df_combinado.sort_values("DIA")
    
    if not df_combinado.empty:
        st.markdown("""
        <div style="background: white; border-radius: 16px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); border: 1px solid #e2e8f0;">
            <div style="font-size: 1.2rem; font-weight: 700; color: #0f172a; margin-bottom: 15px; padding-bottom: 8px; border-bottom: 2px solid #2563eb;">
                EVOLUÇÃO DIÁRIA
            </div>
        """, unsafe_allow_html=True)
        
        # Grid de 2 colunas para os gráficos de barras
        col1, col2 = st.columns(2)
        
        with col1:
            fig1 = px.bar(
                df_combinado, 
                x="DIA", 
                y="SUCESSO", 
                title="Atividades com Sucesso por Dia",
                color_discrete_sequence=["#10b981"]
            )
            fig1.update_traces(marker=dict(line=dict(width=1, color="white")))
            fig1.update_layout(
                plot_bgcolor="white",
                paper_bgcolor="white",
                height=300,
                showlegend=False,
                xaxis=dict(tickmode="linear", tick0=1, dtick=1),
                yaxis=dict(tickmode="linear", tick0=0, dtick=5)
            )
            st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': False})
        
        with col2:
            fig2 = px.bar(
                df_combinado, 
                x="DIA", 
                y="PENDENCIAS", 
                title="Atividades sem Sucesso por Dia",
                color_discrete_sequence=["#ef4444"]
            )
            fig2.update_traces(marker=dict(line=dict(width=1, color="white")))
            fig2.update_layout(
                plot_bgcolor="white",
                paper_bgcolor="white",
                height=300,
                showlegend=False,
                xaxis=dict(tickmode="linear", tick0=1, dtick=1),
                yaxis=dict(tickmode="linear", tick0=0, dtick=5)
            )
            st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})
        
        # Gráfico de linhas comparativo
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
            title=f"Comparativo Diário - Total: {total_atividades} atividades",
            plot_bgcolor="white",
            paper_bgcolor="white",
            height=350,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis=dict(tickmode="linear", tick0=1, dtick=1),
            yaxis=dict(tickmode="linear", tick0=0, dtick=10),
            hovermode="x unified"
        )
        st.plotly_chart(fig3, use_container_width=True, config={'displayModeBar': False})
        
        st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# FOOTER
# =========================================================

st.markdown(f"""
<div style="text-align: center; color: #64748b; margin-top: 20px; padding: 10px; background: #f8fafc; border-radius: 10px; font-size: 0.8rem; border: 1px solid #e2e8f0;">
    <strong>PAINEL DE PRODUTIVIDADE</strong> • {datetime.strptime(mes_selecionado, "%Y-%m").strftime("%B/%Y")} • Total: {total_geral} • Com Sucesso: {total_sucesso} ({eficacia_media:.0f}%) • Média: {media_diaria_geral:.1f}/dia
</div>
""", unsafe_allow_html=True)