import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import re
import os

# =========================================================
# CONFIGURAÇÃO DA PÁGINA
# =========================================================

st.set_page_config(
    layout="wide",
    page_title="Painel de Repetidas - SC",
    page_icon="🔄"
)

# =========================================================
# FUNÇÕES AUXILIARES
# =========================================================

def extrair_tr(nome_completo):
    """Extrai o TR/TT/TC do formato 'NOME (TR123456)'"""
    if pd.isna(nome_completo):
        return ""
    match = re.search(r'(TR\d+|TT\d+|TC\d+)', str(nome_completo))
    return match.group(1) if match else ""

# =========================================================
# CARREGAR DADOS
# =========================================================

@st.cache_data
def carregar_dados():
    """Carrega todas as bases"""
    
    bases_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "BASES")
    raiz = os.path.dirname(os.path.abspath(__file__))
    
    # Carregar base de repetidas
    df_repetidas = pd.read_csv(
        os.path.join(bases_path, "VIP_2026_02_ANL_FTTH_REPETIDA_30_DIAS000000000000.csv"),
        sep=';', 
        encoding='latin1'
    )
    
    # Carregar base de presença (com cidade na coluna T)
    df_presenca = pd.read_excel(
        os.path.join(raiz, "Presença.xlsx"),
        sheet_name='Técnicos'
    )
    
    return df_repetidas, df_presenca

@st.cache_data
def processar_dados(df_repetidas, df_presenca, mes_ano):
    """Processa os dados usando a base presença como referência principal"""
    
    # =========================================================
    # CRIAR MAPEAMENTO COMPLETO DA PRESENÇA
    # =========================================================
    
    # Dicionários para lookup (usando TR e TT como chaves)
    mapa_funcionario = {}
    mapa_supervisor = {}
    mapa_cidade = {}
    mapa_setor = {}
    
    # Também criar listas para análise
    todos_codigos = set()
    
    for _, row in df_presenca.iterrows():
        tr = str(row['TR']).strip() if pd.notna(row['TR']) else ''
        tt = str(row['TT']).strip() if pd.notna(row['TT']) else ''
        funcionario = str(row['FUNCIONÁRIO']) if pd.notna(row['FUNCIONÁRIO']) else ''
        supervisor = str(row['SUPERVISOR']) if pd.notna(row['SUPERVISOR']) else 'Não alocado'
        cidade = str(row['T']) if pd.notna(row['T']) else 'Não informada'  # Coluna T = cidade
        setor = str(row['SETOR ATUAL']) if pd.notna(row['SETOR ATUAL']) else ''
        
        # Mapear por TR
        if tr:
            mapa_funcionario[tr] = funcionario
            mapa_supervisor[tr] = supervisor
            mapa_cidade[tr] = cidade
            mapa_setor[tr] = setor
            todos_codigos.add(tr)
        
        # Mapear por TT (se diferente de TR)
        if tt and tt != tr:
            mapa_funcionario[tt] = funcionario
            mapa_supervisor[tt] = supervisor
            mapa_cidade[tt] = cidade
            mapa_setor[tt] = setor
            todos_codigos.add(tt)
    
    # =========================================================
    # FILTRAR DADOS
    # =========================================================
    
    df_filtrado = df_repetidas[
        (df_repetidas['mes'] == mes_ano) & 
        (df_repetidas['uf'] == 'SC') &
        (df_repetidas['gpon'].notna()) & 
        (df_repetidas['gpon'] != '')
    ].copy()
    
    # =========================================================
    # EXTRAIR CÓDIGOS
    # =========================================================
    
    df_filtrado['cod_tecnico'] = df_filtrado['tecnico'].apply(extrair_tr)
    df_filtrado['cod_tecnico_anterior'] = df_filtrado['tecnico_anterior'].apply(extrair_tr)
    
    # =========================================================
    # DEFINIR TÉCNICO FINAL (prioriza atual, depois anterior)
    # =========================================================
    
    df_filtrado['cod_final'] = df_filtrado['cod_tecnico'].fillna(df_filtrado['cod_tecnico_anterior'])
    
    # =========================================================
    # BUSCAR INFORMAÇÕES NA PRESENÇA
    # =========================================================
    
    df_filtrado['funcionario'] = df_filtrado['cod_final'].map(mapa_funcionario)
    df_filtrado['supervisor'] = df_filtrado['cod_final'].map(mapa_supervisor).fillna('Não alocado')
    df_filtrado['cidade'] = df_filtrado['cod_final'].map(mapa_cidade).fillna('Não informada')
    df_filtrado['setor'] = df_filtrado['cod_final'].map(mapa_setor).fillna('')
    
    # =========================================================
    # IDENTIFICAR REPETIDOS
    # =========================================================
    
    df_filtrado['is_repetido_geral'] = df_filtrado['in_flag_indicador'] == 'SIM'
    df_filtrado['tem_cod_anterior'] = df_filtrado['cod_tecnico_anterior'].notna() & (df_filtrado['cod_tecnico_anterior'] != '')
    df_filtrado['is_repetido_campo'] = df_filtrado['tem_cod_anterior'] & df_filtrado['is_repetido_geral']
    
    # =========================================================
    # ESTATÍSTICAS DE IDENTIFICAÇÃO
    # =========================================================
    
    estatisticas = {
        'total_registros': len(df_filtrado),
        'identificados_por_codigo': df_filtrado['cod_final'].notna().sum(),
        'com_supervisor': (df_filtrado['supervisor'] != 'Não alocado').sum(),
        'com_cidade': (df_filtrado['cidade'] != 'Não informada').sum(),
        'nao_identificados': (df_filtrado['supervisor'] == 'Não alocado').sum()
    }
    
    # =========================================================
    # AGRUPAMENTOS
    # =========================================================
    
    # 1. Por supervisor
    df_supervisor = df_filtrado.groupby('supervisor').agg(
        total_reparos=('gpon', 'count'),
        repetido_geral=('is_repetido_geral', 'sum'),
        repetido_campo=('is_repetido_campo', 'sum')
    ).reset_index()
    
    df_supervisor['%_repetido_geral'] = (df_supervisor['repetido_geral'] / df_supervisor['total_reparos'] * 100).round(2)
    df_supervisor['%_repetido_campo'] = (df_supervisor['repetido_campo'] / df_supervisor['total_reparos'] * 100).round(2)
    df_supervisor = df_supervisor.sort_values('repetido_campo', ascending=False)
    
    # 2. Por cidade
    df_cidade = df_filtrado.groupby('cidade').agg(
        total_reparos=('gpon', 'count'),
        repetido_geral=('is_repetido_geral', 'sum'),
        repetido_campo=('is_repetido_campo', 'sum')
    ).reset_index()
    
    df_cidade['%_repetido_campo'] = (df_cidade['repetido_campo'] / df_cidade['total_reparos'] * 100).round(2)
    df_cidade = df_cidade.sort_values('repetido_campo', ascending=False)
    
    # 3. Por setor
    df_setor = df_filtrado.groupby('setor').agg(
        total_reparos=('gpon', 'count'),
        repetido_geral=('is_repetido_geral', 'sum'),
        repetido_campo=('is_repetido_campo', 'sum')
    ).reset_index()
    
    df_setor['%_repetido_campo'] = (df_setor['repetido_campo'] / df_setor['total_reparos'] * 100).round(2)
    df_setor = df_setor[df_setor['setor'] != ''].sort_values('repetido_campo', ascending=False)
    
    # =========================================================
    # TOTAIS GERAIS
    # =========================================================
    
    totais = {
        'total_reparos': len(df_filtrado),
        'total_repetido_geral': df_filtrado['is_repetido_geral'].sum(),
        'total_repetido_campo': df_filtrado['is_repetido_campo'].sum(),
        'taxa_repetido_geral': (df_filtrado['is_repetido_geral'].sum() / len(df_filtrado) * 100) if len(df_filtrado) > 0 else 0,
        'taxa_repetido_campo': (df_filtrado['is_repetido_campo'].sum() / len(df_filtrado) * 100) if len(df_filtrado) > 0 else 0
    }
    
    return {
        'df_supervisor': df_supervisor,
        'df_cidade': df_cidade,
        'df_setor': df_setor,
        'df_filtrado': df_filtrado,
        'estatisticas': estatisticas,
        'totais': totais
    }

# =========================================================
# CARREGAR DADOS
# =========================================================

with st.spinner('Carregando dados...'):
    df_repetidas, df_presenca = carregar_dados()
    meses_disponiveis = sorted(df_repetidas['mes'].unique(), reverse=True)
    mes_selecionado = meses_disponiveis[0] if meses_disponiveis else None
    dados = processar_dados(df_repetidas, df_presenca, mes_selecionado)

# =========================================================
# HEADER
# =========================================================

st.markdown("""
<style>
    .header-card {
        background: white;
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        border-bottom: 4px solid #1a3a8f;
        margin-bottom: 20px;
    }
    .header-title {
        font-size: 1.8rem;
        font-weight: 900;
        color: #1a3a8f;
    }
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        border-left: 4px solid #1a3a8f;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 800;
        color: #1a3a8f;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #64748b;
    }
    .section-title {
        font-size: 1.4rem;
        font-weight: 800;
        color: #1a3a8f;
        margin: 20px 0;
        padding-bottom: 8px;
        border-bottom: 3px solid #1a3a8f;
    }
    .badge-success {
        background: #10b98120;
        color: #065f46;
        padding: 2px 8px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .badge-warning {
        background: #f59e0b20;
        color: #92400e;
        padding: 2px 8px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .badge-danger {
        background: #ef444420;
        color: #991b1b;
        padding: 2px 8px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .stats-box {
        background: #f8fafc;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown(f"""
<div class="header-card">
    <div class="header-title">🔄 PAINEL DE REPETIDAS - SC</div>
    <div>📅 Período: {mes_selecionado.replace('-', '/')}</div>
    <div style="margin-top: 10px; font-size: 0.9rem; color: #1a3a8f;">
        ✅ Base Presença como referência principal (incluindo cidades)
    </div>
</div>
""", unsafe_allow_html=True)

# =========================================================
# FILTRO DE MÊS
# =========================================================

mes_selecionado = st.selectbox(
    "📅 Selecione o Mês",
    options=meses_disponiveis,
    format_func=lambda x: x.replace('-', '/'),
    index=0
)

# Recarregar se mudar o mês
if mes_selecionado != list(df_repetidas[df_repetidas['uf'] == 'SC']['mes'].unique())[0]:
    dados = processar_dados(df_repetidas, df_presenca, mes_selecionado)

# =========================================================
# ESTATÍSTICAS DE IDENTIFICAÇÃO
# =========================================================

st.markdown('<div class="section-title">📊 COBERTURA DA BASE PRESENÇA</div>', unsafe_allow_html=True)

col_e1, col_e2, col_e3, col_e4 = st.columns(4)

with col_e1:
    st.markdown(f"""
    <div class="stats-box">
        <strong>Total Registros</strong><br>
        <span style="font-size: 1.5rem;">{dados['estatisticas']['total_registros']}</span>
    </div>
    """, unsafe_allow_html=True)

with col_e2:
    pct = (dados['estatisticas']['com_supervisor'] / dados['estatisticas']['total_registros'] * 100)
    st.markdown(f"""
    <div class="stats-box">
        <strong>Com Supervisor</strong><br>
        <span style="font-size: 1.5rem;">{dados['estatisticas']['com_supervisor']}</span><br>
        <small>{pct:.1f}%</small>
    </div>
    """, unsafe_allow_html=True)

with col_e3:
    pct_cidade = (dados['estatisticas']['com_cidade'] / dados['estatisticas']['total_registros'] * 100)
    st.markdown(f"""
    <div class="stats-box">
        <strong>Com Cidade</strong><br>
        <span style="font-size: 1.5rem;">{dados['estatisticas']['com_cidade']}</span><br>
        <small>{pct_cidade:.1f}%</small>
    </div>
    """, unsafe_allow_html=True)

with col_e4:
    st.markdown(f"""
    <div class="stats-box" style="border-left-color: {'#10b981' if dados['estatisticas']['nao_identificados'] == 0 else '#ef4444'};">
        <strong>Não Identificados</strong><br>
        <span style="font-size: 1.5rem; color: {'#10b981' if dados['estatisticas']['nao_identificados'] == 0 else '#ef4444'};">{dados['estatisticas']['nao_identificados']}</span>
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# MÉTRICAS PRINCIPAIS
# =========================================================

col_m1, col_m2, col_m3 = st.columns(3)

with col_m1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{dados['totais']['total_reparos']}</div>
        <div class="metric-label">Total Reparos SC</div>
    </div>
    """, unsafe_allow_html=True)

with col_m2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color: #ef4444;">{dados['totais']['total_repetido_campo']}</div>
        <div class="metric-label">Repetido Campo</div>
    </div>
    """, unsafe_allow_html=True)

with col_m3:
    cor = "#ef4444" if dados['totais']['taxa_repetido_campo'] > 9 else "#10b981"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color: {cor};">{dados['totais']['taxa_repetido_campo']:.2f}%</div>
        <div class="metric-label">% Repetido Campo</div>
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# GRÁFICO POR SUPERVISOR
# =========================================================

st.markdown('<div class="section-title">📊 REPETIDO CAMPO POR SUPERVISOR</div>', unsafe_allow_html=True)

if not dados['df_supervisor'].empty:
    df_graf = dados['df_supervisor'][dados['df_supervisor']['supervisor'] != 'Não alocado']
    
    if not df_graf.empty:
        fig_sup = px.bar(
            df_graf,
            x='supervisor',
            y='%_repetido_campo',
            title='% Repetido Campo por Supervisor',
            color='%_repetido_campo',
            color_continuous_scale=['#10b981', '#f59e0b', '#ef4444'],
            text=df_graf['%_repetido_campo'].apply(lambda x: f'{x:.1f}%')
        )
        fig_sup.add_hline(y=9, line_dash="dash", line_color="#1a3a8f", annotation_text="Meta 9%")
        fig_sup.update_layout(plot_bgcolor='white', height=400, xaxis_tickangle=45)
        st.plotly_chart(fig_sup, use_container_width=True)

# =========================================================
# GRÁFICO POR CIDADE
# =========================================================

st.markdown('<div class="section-title">📍 REPETIDO CAMPO POR CIDADE</div>', unsafe_allow_html=True)

if not dados['df_cidade'].empty:
    df_cidade_graf = dados['df_cidade'][dados['df_cidade']['cidade'] != 'Não informada']
    
    if not df_cidade_graf.empty:
        fig_cidade = px.bar(
            df_cidade_graf,
            x='cidade',
            y='%_repetido_campo',
            title='% Repetido Campo por Cidade',
            color='%_repetido_campo',
            color_continuous_scale=['#10b981', '#f59e0b', '#ef4444'],
            text=df_cidade_graf['%_repetido_campo'].apply(lambda x: f'{x:.1f}%')
        )
        fig_cidade.add_hline(y=9, line_dash="dash", line_color="#1a3a8f", annotation_text="Meta 9%")
        fig_cidade.update_layout(plot_bgcolor='white', height=400, xaxis_tickangle=45)
        st.plotly_chart(fig_cidade, use_container_width=True)

# =========================================================
# TABELA DE SUPERVISORES
# =========================================================

st.markdown('<div class="section-title">📋 DETALHAMENTO POR SUPERVISOR</div>', unsafe_allow_html=True)

if not dados['df_supervisor'].empty:
    df_display = dados['df_supervisor'][dados['df_supervisor']['supervisor'] != 'Não alocado'].copy()
    
    if not df_display.empty:
        df_display['não_repetido'] = df_display['total_reparos'] - df_display['repetido_campo']
        df_display = df_display[['supervisor', 'total_reparos', 'repetido_campo', 'não_repetido', '%_repetido_campo']]
        df_display.columns = ['Supervisor', 'Total Reparos', 'Repetido Campo', 'Não Repetido', '% Repetido']
        df_display = df_display.sort_values('% Repetido', ascending=False)
        
        st.dataframe(df_display, use_container_width=True, hide_index=True)

# =========================================================
# TABELA POR CIDADE
# =========================================================

st.markdown('<div class="section-title">📍 DETALHAMENTO POR CIDADE</div>', unsafe_allow_html=True)

if not dados['df_cidade'].empty:
    df_cidade_display = dados['df_cidade'][dados['df_cidade']['cidade'] != 'Não informada'].copy()
    
    if not df_cidade_display.empty:
        df_cidade_display = df_cidade_display[['cidade', 'total_reparos', 'repetido_campo', '%_repetido_campo']]
        df_cidade_display.columns = ['Cidade', 'Total Reparos', 'Repetido Campo', '% Repetido']
        df_cidade_display = df_cidade_display.sort_values('% Repetido', ascending=False)
        
        st.dataframe(df_cidade_display, use_container_width=True, hide_index=True)

# =========================================================
# FOOTER
# =========================================================

st.markdown(f"""
<div style="text-align: center; color: #64748b; margin-top: 30px; padding: 10px; background: #f8fafc; border-radius: 10px;">
    <strong>Painel de Repetidas - SC</strong> • {mes_selecionado.replace('-', '/')} • 
    Total: {dados['totais']['total_reparos']} • Repetido Campo: {dados['totais']['total_repetido_campo']} ({dados['totais']['taxa_repetido_campo']:.2f}%) • Meta: 9% • 
    Cobertura: {dados['estatisticas']['com_supervisor']}/{dados['estatisticas']['total_registros']} ({dados['estatisticas']['com_supervisor']/dados['estatisticas']['total_registros']*100:.1f}%)
</div>
""", unsafe_allow_html=True)