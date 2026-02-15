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
    page_title="Diagnóstico de Não Alocados",
    page_icon="🔍"
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

def extrair_apenas_codigo(texto):
    """Extrai apenas o código (TR, TT, TC) sem o nome"""
    if pd.isna(texto):
        return ""
    match = re.search(r'(TR\d+|TT\d+|TC\d+)', str(texto))
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
    
    # Carregar base de presença
    df_presenca = pd.read_excel(
        os.path.join(raiz, "Presença.xlsx"),
        sheet_name='Técnicos'
    )
    
    return df_repetidas, df_presenca

@st.cache_data
def criar_mapas_presenca(df_presenca):
    """Cria todos os mapas necessários da base presença"""
    
    # Dicionários para lookup
    codigo_para_funcionario = {}
    codigo_para_supervisor = {}
    codigo_para_coordenador = {}
    
    # Lista de todos os códigos válidos
    todos_codigos = []
    
    # Estatísticas
    total_tr = 0
    total_tt = 0
    
    for _, row in df_presenca.iterrows():
        tr = str(row['TR']).strip() if pd.notna(row['TR']) else ''
        tt = str(row['TT']).strip() if pd.notna(row['TT']) else ''
        funcionario = str(row['FUNCIONÁRIO']) if pd.notna(row['FUNCIONÁRIO']) else ''
        supervisor = str(row['SUPERVISOR']) if pd.notna(row['SUPERVISOR']) else 'Não alocado'
        coordenador = str(row['COORDENADOR']) if pd.notna(row['COORDENADOR']) else 'Não alocado'
        
        # Mapear por TR
        if tr and tr not in ['nan', 'None', '']:
            codigo_para_funcionario[tr] = funcionario
            codigo_para_supervisor[tr] = supervisor
            codigo_para_coordenador[tr] = coordenador
            todos_codigos.append(tr)
            total_tr += 1
        
        # Mapear por TT (se diferente de TR)
        if tt and tt not in ['nan', 'None', ''] and tt != tr:
            codigo_para_funcionario[tt] = funcionario
            codigo_para_supervisor[tt] = supervisor
            codigo_para_coordenador[tt] = coordenador
            todos_codigos.append(tt)
            total_tt += 1
    
    return {
        'mapa_funcionario': codigo_para_funcionario,
        'mapa_supervisor': codigo_para_supervisor,
        'mapa_coordenador': codigo_para_coordenador,
        'todos_codigos': set(todos_codigos),
        'total_tr': total_tr,
        'total_tt': total_tt,
        'total_codigos': len(set(todos_codigos))
    }

# =========================================================
# CARREGAR E PROCESSAR
# =========================================================

st.title("🔍 Diagnóstico de Registros Não Alocados")
st.markdown("---")

with st.spinner('Carregando dados...'):
    df_repetidas, df_presenca = carregar_dados()
    mapas = criar_mapas_presenca(df_presenca)
    
    # Filtrar dados de SC
    df_sc = df_repetidas[
        (df_repetidas['mes'] == '2026-02-01') & 
        (df_repetidas['uf'] == 'SC') &
        (df_repetidas['gpon'].notna()) & 
        (df_repetidas['gpon'] != '')
    ].copy()

# =========================================================
# ESTATÍSTICAS DA BASE PRESENÇA
# =========================================================

st.header("📊 Estatísticas da Base Presença")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Técnicos", len(df_presenca))
with col2:
    st.metric("Códigos TR", mapas['total_tr'])
with col3:
    st.metric("Códigos TT", mapas['total_tt'])
with col4:
    st.metric("Códigos Únicos", mapas['total_codigos'])

# =========================================================
# ANALISAR CÓDIGOS NOS DADOS
# =========================================================

st.header("🔎 Análise de Códigos nos Dados SC")

# Extrair todos os códigos possíveis
df_sc['cod_tecnico'] = df_sc['tecnico'].apply(extrair_apenas_codigo)
df_sc['cod_tecnico_anterior'] = df_sc['tecnico_anterior'].apply(extrair_apenas_codigo)
df_sc['cod_final'] = df_sc['cod_tecnico'].fillna(df_sc['cod_tecnico_anterior'])

# Identificar códigos que existem na presença
df_sc['codigo_existe'] = df_sc['cod_final'].isin(mapas['todos_codigos'])
df_sc['supervisor'] = df_sc['cod_final'].map(mapas['mapa_supervisor']).fillna('Não alocado')

# Separar alocados e não alocados
alocados = df_sc[df_sc['supervisor'] != 'Não alocado']
nao_alocados = df_sc[df_sc['supervisor'] == 'Não alocado']

st.subheader(f"📈 Resultados: {len(alocados)} alocados | {len(nao_alocados)} não alocados")

# =========================================================
# ANÁLISE DOS NÃO ALOÇADOS
# =========================================================

if len(nao_alocados) > 0:
    st.header("❌ Análise dos Não Alocados")
    
    # 1. Quais códigos não foram encontrados?
    st.subheader("1. Códigos não encontrados na base Presença")
    codigos_faltantes = nao_alocados['cod_final'].value_counts().reset_index()
    codigos_faltantes.columns = ['Código', 'Quantidade']
    codigos_faltantes['%'] = (codigos_faltantes['Quantidade'] / len(nao_alocados) * 100).round(1)
    
    st.dataframe(codigos_faltantes, use_container_width=True)
    
    # 2. Amostra detalhada dos registros
    st.subheader("2. Amostra de registros não alocados")
    colunas_mostrar = ['tecnico', 'cod_tecnico', 'tecnico_anterior', 'cod_tecnico_anterior', 'cod_final']
    st.dataframe(nao_alocados[colunas_mostrar].head(50), use_container_width=True)
    
    # 3. Análise por tipo de código
    st.subheader("3. Análise por tipo de código")
    
    # Separar por tipo (TR, TT, TC, outros)
    def classificar_codigo(cod):
        if pd.isna(cod) or cod == '':
            return 'Vazio'
        if cod.startswith('TR'):
            return 'TR'
        if cod.startswith('TT'):
            return 'TT'
        if cod.startswith('TC'):
            return 'TC'
        return 'Outro'
    
    nao_alocados['tipo_codigo'] = nao_alocados['cod_final'].apply(classificar_codigo)
    tipo_counts = nao_alocados['tipo_codigo'].value_counts().reset_index()
    tipo_counts.columns = ['Tipo', 'Quantidade']
    
    st.dataframe(tipo_counts, use_container_width=True)
    
    # 4. Análise de padrões nos nomes
    st.subheader("4. Padrões nos nomes dos técnicos")
    
    # Extrair possíveis TRs dos nomes
    def extrair_tr_do_nome(nome):
        if pd.isna(nome):
            return ''
        match = re.search(r'(TR\d+|TT\d+|TC\d+)', str(nome))
        return match.group(1) if match else ''
    
    nao_alocados['tr_no_nome'] = nao_alocados['tecnico'].apply(extrair_tr_do_nome)
    nao_alocados['tr_anterior_no_nome'] = nao_alocados['tecnico_anterior'].apply(extrair_tr_do_nome)
    
    # Verificar se o código extraído corresponde ao que usamos
    nao_alocados['codigo_no_nome_corresponde'] = (
        (nao_alocados['tr_no_nome'] == nao_alocados['cod_tecnico']) | 
        (nao_alocados['tr_anterior_no_nome'] == nao_alocados['cod_tecnico_anterior'])
    )
    
    st.write(f"**Correspondência de código no nome:** {nao_alocados['codigo_no_nome_corresponde'].sum()} registros")
    
    # 5. Sugestões de correção
    st.subheader("5. Sugestões para correção")
    
    sugestoes = []
    
    # Verificar códigos que são TR mas não estão na base
    tr_faltantes = nao_alocados[nao_alocados['tipo_codigo'] == 'TR']['cod_final'].unique()
    if len(tr_faltantes) > 0:
        sugestoes.append(f"🔴 **{len(tr_faltantes)} códigos TR** não encontrados na base Presença")
    
    # Verificar códigos que são TT
    tt_faltantes = nao_alocados[nao_alocados['tipo_codigo'] == 'TT']['cod_final'].unique()
    if len(tt_faltantes) > 0:
        sugestoes.append(f"🟡 **{len(tt_faltantes)} códigos TT** não encontrados na base Presença")
    
    # Verificar registros sem código
    sem_codigo = nao_alocados[nao_alocados['tipo_codigo'] == 'Vazio'].shape[0]
    if sem_codigo > 0:
        sugestoes.append(f"⚪ **{sem_codigo} registros** sem código (tecnicos sem TR/TT/TC)")
    
    for sugestao in sugestoes:
        st.markdown(f"- {sugestao}")
    
    # 6. Exportar para análise
    st.subheader("6. Exportar dados para correção")
    
    if st.button("📥 Gerar CSV para correção"):
        csv = nao_alocados[['tecnico', 'tecnico_anterior', 'cod_final']].to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="nao_alocados_para_corrigir.csv",
            mime="text/csv"
        )

else:
    st.success("✅ Nenhum registro não alocado encontrado! Todos os técnicos foram identificados corretamente.")

# =========================================================
# VISÃO GERAL DOS SUPERVISORES
# =========================================================

if len(alocados) > 0:
    st.header("📋 Visão Geral dos Supervisores (Atual)")
    
    # Agrupar por supervisor
    df_sup = alocados.groupby('supervisor').agg(
        total_reparos=('gpon', 'count'),
        is_repetido=('in_flag_indicador', lambda x: (x == 'SIM').sum())
    ).reset_index()
    
    df_sup.columns = ['Supervisor', 'Total Reparos', 'Repetidos']
    df_sup['% Repetidos'] = (df_sup['Repetidos'] / df_sup['Total Reparos'] * 100).round(2)
    df_sup = df_sup.sort_values('Total Reparos', ascending=False)
    
    st.dataframe(df_sup, use_container_width=True)

# =========================================================
# FOOTER
# =========================================================

st.markdown("---")
st.caption(f"Total de registros analisados: {len(df_sc)} | Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}")