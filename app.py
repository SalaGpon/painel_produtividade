# =========================================================
# TABELA POR TÉCNICO (SEM COLUNA STATUS)
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
        
        dados_tabela.append({
            "nome_exibicao": nome_exibicao,
            "tr": tr,
            "nome_completo": tecnico,
            "supervisor": supervisor,
            "dias": dias,
            "com_sucesso": total_sucesso_tecnico,
            "sem_sucesso": total_sem_sucesso_tecnico,
            "media": media_diaria_tecnico,
            "eficacia": eficacia_tecnico,
            "total": total_geral_tecnico
        })

dados_tabela.sort(key=lambda x: x["com_sucesso"], reverse=True)

# Criar HTML da tabela (SEM COLUNA STATUS)
html_tabela = '<div style="overflow-x: auto; border-radius: 8px; border: 1px solid #e2e8f0; max-height: 550px; overflow-y: auto;"><table style="width: 100%; border-collapse: collapse; font-size: 0.75rem;">'
html_tabela += "<thead><tr>"
html_tabela += "<th style='background: #f8fafc; padding: 8px 4px; position: sticky; top: 0;'>NOME</th>"
html_tabela += "<th style='background: #f8fafc; padding: 8px 4px; position: sticky; top: 0;'>TR</th>"
# LINHA DO STATUS REMOVIDA

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
    # LINHA DO STATUS REMOVIDA
    
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
        bg = "#10b98120"
        cor = "#065f46"
    elif tecnico["eficacia"] >= 60:
        bg = "#f59e0b20"
        cor = "#92400e"
    else:
        bg = "#ef444420"
        cor = "#991b1b"
    html_tabela += f'<td style="padding: 6px 4px;"><span style="background: {bg}; color: {cor}; padding: 2px 6px; border-radius: 20px; font-weight: 600;">{tecnico["eficacia"]:.0f}%</span></td>'
    
    html_tabela += f'<td style="padding: 6px 4px;"><strong>{tecnico["total"]}</strong></td>'
    html_tabela += "</tr>"

# Linha de TOTAL (para supervisor)
if dados_tabela and st.session_state.tipo_usuario == "supervisor":
    total_com_sucesso = sum(t["com_sucesso"] for t in dados_tabela)
    total_sem_sucesso = sum(t["sem_sucesso"] for t in dados_tabela)
    total_geral_geral = sum(t["total"] for t in dados_tabela)
    eficacia_geral = (total_com_sucesso / total_geral_geral * 100) if total_geral_geral > 0 else 0
    media_diaria_geral = total_com_sucesso / (len(dados_tabela) * dias_no_mes) if len(dados_tabela) > 0 else 0
    
    html_tabela += '<tr style="background: #f8fafc; font-weight: 700; border-top: 2px solid #2563eb;">'
    html_tabela += f'<td colspan="3" style="padding: 6px 4px; font-weight:700;">TOTAL</td>'  # Mudado de colspan="4" para "3"
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
# NOVA TABELA: ACOMPANHAMENTO POR HORA
# =========================================================

st.markdown("""
<div style="background: white; border-radius: 16px; padding: 20px; margin: 20px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.05); border: 1px solid #e2e8f0;">
    <div style="font-size: 1.2rem; font-weight: 700; color: #0f172a; margin-bottom: 15px; padding-bottom: 8px; border-bottom: 2px solid #2563eb;">
        ⏰ ACOMPANHAMENTO DIA - ATIVIDADES ENCERRADAS POR HORÁRIO
    </div>
""", unsafe_allow_html=True)

# Processar dados por hora
if not df_filtrado.empty:
    # Extrair hora do encerramento
    df_filtrado["HORA"] = pd.to_datetime(df_filtrado["Início Execução"]).dt.hour
    
    # Definir faixas horárias
    faixas_horario = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]
    
    # Classificar cada atividade em uma faixa horária
    df_filtrado["FAIXA_HORA"] = df_filtrado["HORA"].apply(
        lambda x: f"{x:02d}H" if x in faixas_horario else ">19H"
    )
    
    # Agrupar por técnico e faixa horária
    pivot_hora = pd.crosstab(
        index=[df_filtrado["NOME_EXIBICAO"], df_filtrado["TR"]],
        columns=df_filtrado["FAIXA_HORA"],
        values=df_filtrado["Número SA"],
        aggfunc='count'
    ).fillna(0)
    
    # Garantir que todas as faixas existam
    for hora in [f"{h:02d}H" for h in faixas_horario] + [">19H"]:
        if hora not in pivot_hora.columns:
            pivot_hora[hora] = 0
    
    # Ordenar colunas
    colunas_ordenadas = [f"{h:02d}H" for h in faixas_horario] + [">19H"]
    pivot_hora = pivot_hora[colunas_ordenadas]
    
    # Reset index para ter NOME e TR como colunas
    pivot_hora = pivot_hora.reset_index()
    pivot_hora.columns.name = None
    
    # Adicionar coluna de total
    pivot_hora["TOTAL"] = pivot_hora.iloc[:, 2:].sum(axis=1)
    
    # Ordenar por total (decrescente)
    pivot_hora = pivot_hora.sort_values("TOTAL", ascending=False)
    
    # Criar HTML da tabela por hora
    html_hora = '<div style="overflow-x: auto; border-radius: 8px; border: 1px solid #e2e8f0; max-height: 400px; overflow-y: auto;"><table style="width: 100%; border-collapse: collapse; font-size: 0.75rem;">'
    html_hora += "<thead><tr>"
    html_hora += "<th style='background: #f8fafc; padding: 8px 4px; position: sticky; top: 0;'>NOME</th>"
    html_hora += "<th style='background: #f8fafc; padding: 8px 4px; position: sticky; top: 0;'>TR</th>"
    
    for hora in colunas_ordenadas:
        html_hora += f"<th style='background: #f8fafc; padding: 8px 4px; position: sticky; top: 0;'>{hora}</th>"
    
    html_hora += "<th style='background: #f8fafc; padding: 8px 4px; position: sticky; top: 0;'>TOTAL</th>"
    html_hora += "</tr></thead><tbody>"
    
    for _, row in pivot_hora.iterrows():
        html_hora += "<tr>"
        html_hora += f'<td style="padding: 6px 4px; font-weight: 500;">{row["NOME_EXIBICAO"]}</td>'
        html_hora += f'<td style="padding: 6px 4px;"><span style="background: #e2e8f0; color: #0f172a; padding: 2px 6px; border-radius: 12px; font-size: 0.65rem;">{row["TR"]}</span></td>'
        
        for hora in colunas_ordenadas:
            valor = int(row[hora])
            if valor >= 3:
                html_hora += f'<td style="padding: 6px 4px; background: #10b98120; color: #065f46; font-weight: 600; text-align: center;">{valor}</td>'
            elif valor >= 1:
                html_hora += f'<td style="padding: 6px 4px; background: #f59e0b20; color: #92400e; font-weight: 600; text-align: center;">{valor}</td>'
            else:
                html_hora += f'<td style="padding: 6px 4px; text-align: center;">{valor}</td>'
        
        html_hora += f'<td style="padding: 6px 4px; font-weight: 700; text-align: center;"><span style="background: #2563eb20; color: #1e40af; padding: 2px 6px; border-radius: 20px;">{int(row["TOTAL"])}</span></td>'
        html_hora += "</tr>"
    
    # Linha de total geral
    if st.session_state.tipo_usuario == "supervisor":
        totais_por_hora = {hora: pivot_hora[hora].sum() for hora in colunas_ordenadas}
        total_geral_horas = sum(totais_por_hora.values())
        
        html_hora += '<tr style="background: #f8fafc; font-weight: 700; border-top: 2px solid #2563eb;">'
        html_hora += '<td colspan="2" style="padding: 6px 4px;">TOTAL</td>'
        
        for hora in colunas_ordenadas:
            html_hora += f'<td style="padding: 6px 4px; text-align: center;"><strong>{int(totais_por_hora[hora])}</strong></td>'
        
        html_hora += f'<td style="padding: 6px 4px; text-align: center;"><strong>{int(total_geral_horas)}</strong></td>'
        html_hora += "</tr>"
    
    html_hora += "</tbody></table></div>"
    
    st.markdown(html_hora, unsafe_allow_html=True)
    
    # Métricas resumidas
    col_h1, col_h2, col_h3, col_h4 = st.columns(4)
    
    with col_h1:
        st.markdown(f"""
        <div style="background: #e8f4fc; padding: 10px; border-radius: 8px; border-left: 4px solid #2563eb; margin-top: 10px;">
            <div style="font-size: 0.7rem; color: #64748b;">HORÁRIO DE PICO</div>
            <div style="font-size: 1.2rem; font-weight: 700; color: #2563eb;">{max(totais_por_hora, key=totais_por_hora.get)}</div>
            <div style="font-size: 0.8rem;">{int(max(totais_por_hora.values()))} atividades</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_h2:
        # Calcular % após 18h
        apos_19 = totais_por_hora.get(">19H", 0)
        pct_apos_19 = (apos_19 / total_geral_horas * 100) if total_geral_horas > 0 else 0
        st.markdown(f"""
        <div style="background: #fef2f2; padding: 10px; border-radius: 8px; border-left: 4px solid #ef4444; margin-top: 10px;">
            <div style="font-size: 0.7rem; color: #64748b;">APÓS 19H</div>
            <div style="font-size: 1.2rem; font-weight: 700; color: #ef4444;">{int(apos_19)}</div>
            <div style="font-size: 0.8rem;">{pct_apos_19:.1f}% do total</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_h3:
        # Calcular média por hora (considerando apenas horas comerciais 8-18)
        horas_comerciais = sum(totais_por_hora[h] for h in [f"{h:02d}H" for h in range(8, 19)])
        media_por_hora = horas_comerciais / 11 if horas_comerciais > 0 else 0
        st.markdown(f"""
        <div style="background: #f0f4ff; padding: 10px; border-radius: 8px; border-left: 4px solid #8b5cf6; margin-top: 10px;">
            <div style="font-size: 0.7rem; color: #64748b;">MÉDIA/HORA (8-18H)</div>
            <div style="font-size: 1.2rem; font-weight: 700; color: #8b5cf6;">{media_por_hora:.1f}</div>
            <div style="font-size: 0.8rem;">atividades por hora</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_h4:
        # Horário com menor movimento
        horas_com_movimento = {h: v for h, v in totais_por_hora.items() if v > 0 and h != ">19H"}
        if horas_com_movimento:
            hora_min = min(horas_com_movimento, key=horas_com_movimento.get)
            valor_min = horas_com_movimento[hora_min]
            st.markdown(f"""
            <div style="background: #fff3cd; padding: 10px; border-radius: 8px; border-left: 4px solid #f59e0b; margin-top: 10px;">
                <div style="font-size: 0.7rem; color: #64748b;">MENOR MOVIMENTO</div>
                <div style="font-size: 1.2rem; font-weight: 700; color: #f59e0b;">{hora_min}</div>
                <div style="font-size: 0.8rem;">{int(valor_min)} atividades</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

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
