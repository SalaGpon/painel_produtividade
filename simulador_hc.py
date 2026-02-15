# simulador_hc.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from config_bases import BASES, get_base_path, listar_bases_disponiveis

st.set_page_config(
    layout="wide",
    page_title="Simulador HC - SC",
    page_icon="📊"
)

st.title("🎯 Simulador de Pontos HC - SC")

# Carregar bases disponíveis
bases = listar_bases_disponiveis()

if bases:
    st.sidebar.success(f"✅ {len(bases)} bases encontradas")
    
    # Menu de seleção
    opcao = st.sidebar.selectbox(
        "Selecione o Dashboard",
        ["Simulador HC", "Análise Detalhada", "Comparativo Mensal"]
    )
    
    if opcao == "Simulador HC":
        # Tabela de indicadores (igual à imagem)
        dados_hc = pd.DataFrame({
            'INDICADOR': [
                'Cumprimento 1a Agenda/ Antecipação Instalação',
                'Cumprimento 1a Agenda/ Antecipação Reparo',
                'Infância 30 Dias',
                'Instalação no Prazo 96h',
                'Reparo no Prazo 24h',
                'Reparo por Planta',
                'Repetida 30 dias'
            ],
            'LIMITE': ['85,00%', '85,00%', '4,50%', '85,00%', '85,00%', '2,50%', '10,00%'],
            'META': ['90,00%', '90,00%', '3,50%', '90,00%', '90,00%', '2,00%', '9,00%'],
            'REAL': ['91,69%', '87,23%', '10,18%', '94,25%', '70,33%', '1,76%', '21,54%'],
            'TOTAL': [15.0, 10.0, 20.0, 15.0, 10.0, 15.0, 15.0],
            'PTS': [15.0, 8.0, 0.0, 15.0, 0.0, 15.0, 0.0]
        })
        
        # Métricas principais
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total de Pontos", "53,0", "Meta: 100")
        with col2:
            st.metric("Indicadores Meta", "3/7", "42,9%")
        with col3:
            st.metric("Melhor Indicador", "Instalação 96h", "94,25%")
        with col4:
            st.metric("Pior Indicador", "Repetida 30d", "21,54%")
        
        # Tabela principal
        st.subheader("📋 Indicadores de Performance")
        
        # Formatação condicional
        def colorir_pts(val):
            if val == 0:
                return 'background: #ff4d4d; color: white'
            elif val >= 15:
                return 'background: #00cc66; color: white'
            return ''
        
        styled_df = dados_hc.style.applymap(colorir_pts, subset=['PTS'])
        
        st.dataframe(
            styled_df,
            use_container_width=True,
            height=400,
            column_config={
                "INDICADOR": "Indicador",
                "LIMITE": "Limite",
                "META": "Meta",
                "REAL": "Real",
                "TOTAL": st.column_config.NumberColumn("Total", format="%.1f"),
                "PTS": st.column_config.NumberColumn("Pontos", format="%.1f")
            }
        )
        
        # Gráfico de barras comparativo
        st.subheader("📊 Comparativo Real vs Meta")
        
        fig = go.Figure()
        
        # Remover % para converter em número
        dados_hc['REAL_NUM'] = dados_hc['REAL'].str.replace('%', '').astype(float)
        dados_hc['META_NUM'] = dados_hc['META'].str.replace('%', '').astype(float)
        
        fig.add_trace(go.Bar(
            name='Real',
            x=dados_hc['INDICADOR'],
            y=dados_hc['REAL_NUM'],
            marker_color='#2563eb'
        ))
        
        fig.add_trace(go.Bar(
            name='Meta',
            x=dados_hc['INDICADOR'],
            y=dados_hc['META_NUM'],
            marker_color='#94a3b8'
        ))
        
        fig.update_layout(
            barmode='group',
            plot_bgcolor='white',
            height=500,
            yaxis=dict(title='Percentual (%)', ticksuffix='%'),
            xaxis=dict(tickangle=45)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Análise de Gaps
        st.subheader("📈 Análise de Gaps")
        
        dados_hc['GAP'] = dados_hc['REAL_NUM'] - dados_hc['META_NUM']
        dados_hc['STATUS'] = dados_hc['GAP'].apply(
            lambda x: '✅ Acima da Meta' if x >= 0 else '⚠️ Abaixo da Meta'
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.dataframe(
                dados_hc[['INDICADOR', 'GAP', 'STATUS']],
                use_container_width=True
            )
        
        with col2:
            fig_pizza = px.pie(
                dados_hc,
                names='STATUS',
                title='Indicadores por Status',
                color='STATUS',
                color_discrete_map={
                    '✅ Acima da Meta': '#00cc66',
                    '⚠️ Abaixo da Meta': '#ff4d4d'
                }
            )
            st.plotly_chart(fig_pizza, use_container_width=True)
            
else:
    st.warning(f"""
    ⚠️ Nenhuma base encontrada em:
    {BASE_PATH}
    
    Certifique-se de que os arquivos estão na pasta correta.
    """)
    
    # Mostrar estrutura esperada
    with st.expander("📁 Estrutura esperada"):
        for key, base in BASES.items():
            st.write(f"- {base['descricao']}: `{base['nome']}`")