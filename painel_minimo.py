import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import re
import os
import numpy as np
import json
import base64
from pathlib import Path
import uuid

# =========================================================
# CONFIGURAÇÃO
# =========================================================

st.set_page_config(layout="wide", page_title="Painel de Repetidas - SC")
st.cache_data.clear()

# =========================================================
# FUNÇÕES
# =========================================================

def extrair_tr(nome_completo):
    if pd.isna(nome_completo):
        return ""
    match = re.search(r'(TR\d+|TT\d+|TC\d+)', str(nome_completo))
    return match.group(1) if match else ""

def extrair_primeiro_nome(nome_completo):
    if pd.isna(nome_completo):
        return ""
    nome_limpo = re.sub(r'\s*\(.*\)', '', str(nome_completo)).strip()
    return nome_limpo.split()[0] if nome_limpo else ""

def extrair_nome_completo(nome_completo):
    if pd.isna(nome_completo):
        return ""
    nome_limpo = re.sub(r'\s*\(.*\)', '', str(nome_completo)).strip()
    return nome_limpo if nome_limpo else ""

def extrair_semana(data):
    if pd.isna(data):
        return None
    return data.isocalendar().week

def classificar_quartil(valor, limites):
    if pd.isna(valor):
        return "N/A"
    if len(limites) < 3:
        return "2º Quartil"
    if valor <= limites[0]:
        return "1º Quartil"
    elif valor <= limites[1]:
        return "2º Quartil"
    elif valor <= limites[2]:
        return "3º Quartil"
    else:
        return "4º Quartil"

def mapear_colunas_presenca(df):
    colunas = df.columns.tolist()
    mapa = {}
    for col in colunas:
        col_upper = str(col).upper().strip()
        if col_upper == 'TR':
            mapa['TR'] = col
        elif col_upper == 'TT':
            mapa['TT'] = col
        elif col_upper in ['FUNCIONÁRIO', 'FUNCIONARIO']:
            mapa['FUNCIONARIO'] = col
        elif col_upper == 'SUPERVISOR':
            mapa['SUPERVISOR'] = col
        elif col_upper == 'COORDENADOR':
            mapa['COORDENADOR'] = col
    return mapa

def gerar_html_assinatura(ata_id, tecnico, tipo, dados, causas_pareto):
    """Gera HTML para página de assinatura"""
    
    # Preparar variáveis para o JavaScript (escapar aspas)
    nome_tecnico_js = tecnico['nome'].replace("'", "\\'").replace('"', '\\"')
    codigo_tecnico_js = tecnico['codigo'].replace("'", "\\'").replace('"', '\\"')
    supervisor_js = tecnico.get('supervisor', 'N/I').replace("'", "\\'").replace('"', '\\"')
    
    # Determinar cores e mensagens baseado no tipo
    if tipo == 'parabens':
        cor_gradiente = "135deg, #1a6c5c 0%, #2ca08c 100%"
        titulo = "🎉 ATA DE PARABENIZAÇÃO"
        badge_class = "badge-parabens"
        badge_text = "✅ ABAIXO DA META"
        mensagem = f"""
        <p>Prezado(a) <strong>{tecnico['nome']}</strong>,</p>
        <p>Gostaríamos de parabenizá-lo pelo excelente desempenho!</p>
        <p>Seus indicadores estão abaixo da meta de 9% nos últimos dois meses:</p>
        <ul>
            <li>Mês Anterior (JAN/26): <strong>{dados.get('Mês Anterior', '-')}</strong></li>
            <li>Mês Atual (FEV/26): <strong>{dados.get('Mês Atual', '-')}</strong></li>
        </ul>
        <p>Continue com esse ótimo trabalho! 🚀</p>
        """
    elif tipo == 'atencao':
        cor_gradiente = "135deg, #a8433d 0%, #c0392b 100%"
        titulo = "⚠️ ATA DE ATENÇÃO"
        badge_class = "badge-atencao"
        badge_text = "⚠️ ACIMA DA META"
        mensagem = f"""
        <p>Prezado(a) <strong>{tecnico['nome']}</strong>,</p>
        <p>Identificamos que seus indicadores estão acima da meta de 9% nos últimos dois meses:</p>
        <ul>
            <li>Mês Anterior (JAN/26): <strong>{dados.get('Mês Anterior', '-')}</strong></li>
            <li>Mês Atual (FEV/26): <strong>{dados.get('Mês Atual', '-')}</strong></li>
        </ul>
        <p>Pedimos que redobre a atenção nas atividades e busque identificar as causas para redução desses índices.</p>
        <p>Estamos à disposição para apoiá-lo! 💪</p>
        """
    else:  # evolucao
        cor_gradiente = "135deg, #f39c12 0%, #e67e22 100%"
        titulo = "📈 ATA DE EVOLUÇÃO"
        badge_class = "badge-evolucao"
        badge_text = "📈 EM EVOLUÇÃO"
        melhoria = float(dados.get('Melhoria', '0').replace('⬇️ ', '').replace('%', '')) if dados.get('Melhoria') else 0
        mensagem = f"""
        <p>Prezado(a) <strong>{tecnico['nome']}</strong>,</p>
        <p>Excelente notícia! Você conseguiu reduzir seu indicador e agora está abaixo da meta de 9%!</p>
        <ul>
            <li>Mês Anterior (JAN/26): <strong>{dados.get('Mês Anterior', '-')}</strong></li>
            <li>Mês Atual (FEV/26): <strong>{dados.get('Mês Atual', '-')}</strong></li>
            <li>Melhoria: <strong>⬇️ {melhoria:.1f}%</strong></li>
        </ul>
        <p>Continue assim, estamos no caminho certo! 🎯</p>
        """
    
    # Gerar tabela de causas
    causas_html = ""
    for _, row in causas_pareto.head(5).iterrows():
        causas_html += f"<tr><td>{row['causa']}</td><td>{row['quantidade']}</td><td>{row['percentual']}%</td><td>{row['acumulado']}%</td></tr>"
    
    # Converter causas para JSON para usar no JavaScript
    causas_json = causas_pareto.head(5).to_json(orient='records')
    
    html = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Ata de {tipo} - {tecnico['nome']}</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <script src="https://cdn.jsdelivr.net/npm/signature_pad@4.0.0/dist/signature_pad.umd.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }}

            body {{
                background-color: #f5f7fa;
                color: #333;
                line-height: 1.6;
                padding: 20px;
            }}

            .container {{
                max-width: 1000px;
                margin: 0 auto;
                background: white;
                border-radius: 12px;
                box-shadow: 0 5px 25px rgba(0, 0, 0, 0.08);
                overflow: hidden;
            }}

            .header {{
                background: linear-gradient({cor_gradiente});
                color: white;
                padding: 25px 30px;
                position: relative;
            }}

            .header h1 {{
                font-size: 28px;
                margin-bottom: 8px;
                font-weight: 700;
            }}

            .header p {{
                font-size: 16px;
                opacity: 0.9;
            }}

            .logo {{
                position: absolute;
                right: 30px;
                top: 50%;
                transform: translateY(-50%);
                font-size: 40px;
                opacity: 0.8;
            }}

            .content {{
                padding: 30px;
            }}

            .section {{
                margin-bottom: 30px;
                padding-bottom: 25px;
                border-bottom: 1px solid #eaeaea;
            }}

            .section-title {{
                font-size: 20px;
                color: #1a3a8f;
                margin-bottom: 20px;
                padding-bottom: 10px;
                border-bottom: 2px solid #2563eb;
                font-weight: 600;
            }}

            .info-box {{
                background-color: #f0f4ff;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 20px;
                border-left: 4px solid #1a3a8f;
            }}

            .info-box h3 {{
                color: #1a3a8f;
                margin-bottom: 10px;
            }}

            .badge {{
                display: inline-block;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 600;
                margin-right: 10px;
            }}

            .badge-parabens {{
                background-color: #d4edda;
                color: #155724;
            }}

            .badge-atencao {{
                background-color: #f8d7da;
                color: #721c24;
            }}

            .badge-evolucao {{
                background-color: #fff3cd;
                color: #856404;
            }}

            .indicadores {{
                display: flex;
                gap: 20px;
                margin: 20px 0;
                flex-wrap: wrap;
            }}

            .indicador-card {{
                flex: 1;
                min-width: 150px;
                background: white;
                border-radius: 8px;
                padding: 15px;
                border: 1px solid #e2e8f0;
                text-align: center;
            }}

            .indicador-valor {{
                font-size: 24px;
                font-weight: 700;
                color: #1a3a8f;
                margin-bottom: 5px;
            }}

            .indicador-label {{
                font-size: 12px;
                color: #666;
                text-transform: uppercase;
            }}

            .signature-container {{
                background-color: #f9fafc;
                border-radius: 8px;
                padding: 20px;
                border: 1px solid #eaeaea;
                margin-top: 20px;
            }}

            .signature-title {{
                font-size: 16px;
                color: #1a3a8f;
                margin-bottom: 15px;
                font-weight: 600;
            }}

            .signature-area {{
                position: relative;
                width: 100%;
                height: 150px;
                border: 2px dashed #bdc3c7;
                border-radius: 8px;
                background-color: white;
                margin-bottom: 15px;
                overflow: hidden;
            }}

            .signature-canvas {{
                width: 100%;
                height: 100%;
                display: block;
                cursor: crosshair;
            }}

            .signature-placeholder {{
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                color: #95a5a6;
                font-size: 14px;
                text-align: center;
                pointer-events: none;
            }}

            .signature-buttons {{
                display: flex;
                gap: 10px;
                margin-bottom: 15px;
            }}

            .btn {{
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s;
                font-size: 14px;
                flex: 1;
            }}

            .btn-primary {{
                background-color: #1a3a8f;
                color: white;
            }}

            .btn-primary:hover {{
                background-color: #2563eb;
            }}

            .btn-secondary {{
                background-color: #ecf0f1;
                color: #2c3e50;
            }}

            .btn-secondary:hover {{
                background-color: #d5dbdb;
            }}

            .btn-success {{
                background-color: #27ae60;
                color: white;
            }}

            .btn-success:hover {{
                background-color: #219653;
            }}

            .signature-info {{
                background-color: #e8f4fc;
                border-radius: 8px;
                padding: 15px;
                margin-top: 10px;
                border-left: 4px solid #1a3a8f;
                display: none;
            }}

            .signature-info.active {{
                display: block;
            }}

            .signature-status {{
                display: inline-block;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 600;
                margin-left: 10px;
            }}

            .status-pending {{
                background-color: #f39c12;
                color: white;
            }}

            .status-completed {{
                background-color: #27ae60;
                color: white;
            }}

            .causas-table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 15px;
            }}

            .causas-table th,
            .causas-table td {{
                padding: 8px;
                text-align: left;
                border-bottom: 1px solid #eaeaea;
            }}

            .causas-table th {{
                background-color: #f0f4ff;
                color: #1a3a8f;
                font-weight: 600;
            }}

            .mensagem {{
                background: #f8fafc;
                padding: 15px;
                border-radius: 8px;
                font-style: italic;
                margin: 15px 0;
                border-left: 4px solid #1a3a8f;
            }}

            .btn-download {{
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s;
                margin-top: 20px;
                width: 100%;
            }}

            .btn-download:hover {{
                background-color: #219653;
            }}

            @media (max-width: 768px) {{
                .indicadores {{
                    flex-direction: column;
                }}
                
                .header {{
                    text-align: center;
                }}
                
                .logo {{
                    position: relative;
                    right: auto;
                    top: auto;
                    transform: none;
                    margin-top: 15px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1><i class="fas fa-file-signature"></i> {titulo}</h1>
                <p>Documento de Reconhecimento Profissional</p>
                <div class="logo">
                    <i class="fas fa-users"></i>
                </div>
            </div>
            
            <div class="content">
                <div class="info-box">
                    <h3><i class="fas fa-info-circle"></i> Informações do Técnico</h3>
                    <p><strong>Nome:</strong> {tecnico['nome']}</p>
                    <p><strong>Código:</strong> {tecnico['codigo']}</p>
                    <p><strong>Supervisor:</strong> {tecnico.get('supervisor', 'N/I')}</p>
                    <span class="badge {badge_class}">{badge_text}</span>
                </div>
                
                <div class="section">
                    <h2 class="section-title">📊 Indicadores</h2>
                    <div class="indicadores">
                        <div class="indicador-card">
                            <div class="indicador-valor">{dados.get('Mês Anterior', '-')}</div>
                            <div class="indicador-label">Mês Anterior (JAN/26)</div>
                        </div>
                        <div class="indicador-card">
                            <div class="indicador-valor">{dados.get('Mês Atual', '-')}</div>
                            <div class="indicador-label">Mês Atual (FEV/26)</div>
                        </div>
                        {f'''
                        <div class="indicador-card">
                            <div class="indicador-valor">{dados.get('Melhoria', '-')}</div>
                            <div class="indicador-label">Melhoria</div>
                        </div>
                        ''' if tipo == 'evolucao' else ''}
                    </div>
                </div>
                
                <div class="section">
                    <h2 class="section-title">📝 Mensagem</h2>
                    <div class="mensagem">
                        {mensagem}
                    </div>
                </div>
                
                <div class="section">
                    <h2 class="section-title">📊 Pareto - Causas de Encerramento</h2>
                    <table class="causas-table">
                        <thead>
                            <tr>
                                <th>Causa</th>
                                <th>Quantidade</th>
                                <th>%</th>
                                <th>Acumulado</th>
                            </tr>
                        </thead>
                        <tbody>
                            {causas_html}
                        </tbody>
                    </table>
                </div>
                
                <div class="section">
                    <h2 class="section-title">✍️ Assinatura Digital</h2>
                    
                    <div class="signature-container">
                        <div class="signature-title">Assinatura do Técnico <span style="color: #ef4444;">*</span></div>
                        <div class="signature-area">
                            <canvas id="tecnicoCanvas" class="signature-canvas"></canvas>
                            <div id="tecnicoPlaceholder" class="signature-placeholder">
                                <i class="fas fa-signature" style="font-size: 30px; margin-bottom: 5px;"></i><br>
                                Técnico: Assine aqui (obrigatório)
                            </div>
                        </div>
                        
                        <div class="signature-buttons">
                            <button id="clearTecnico" class="btn btn-secondary">
                                <i class="fas fa-eraser"></i> Limpar
                            </button>
                            <button id="validateTecnico" class="btn btn-primary">
                                <i class="fas fa-check-circle"></i> Validar Assinatura
                            </button>
                        </div>
                        
                        <div id="tecnicoInfo" class="signature-info">
                            <p><strong>Assinatura Validada:</strong> <span id="tecnicoStatus" class="signature-status status-pending">PENDENTE</span></p>
                            <p><strong>Técnico:</strong> {tecnico['nome']}</p>
                            <p><strong>Data/Hora:</strong> <span id="tecnicoDateTime">--/--/---- --:--</span></p>
                        </div>
                    </div>
                    
                    <div class="signature-container" style="margin-top: 20px;">
                        <div class="signature-title">Assinatura do Supervisor <span style="color: #666;">(opcional)</span></div>
                        <div class="signature-area">
                            <canvas id="supervisorCanvas" class="signature-canvas"></canvas>
                            <div id="supervisorPlaceholder" class="signature-placeholder">
                                <i class="fas fa-signature" style="font-size: 30px; margin-bottom: 5px;"></i><br>
                                Supervisor: Assine aqui (opcional)
                            </div>
                        </div>
                        
                        <div class="signature-buttons">
                            <button id="clearSupervisor" class="btn btn-secondary">
                                <i class="fas fa-eraser"></i> Limpar
                            </button>
                            <button id="validateSupervisor" class="btn btn-primary">
                                <i class="fas fa-check-circle"></i> Validar Assinatura
                            </button>
                        </div>
                        
                        <div id="supervisorInfo" class="signature-info">
                            <p><strong>Assinatura Validada:</strong> <span id="supervisorStatus" class="signature-status status-pending">PENDENTE</span></p>
                            <p><strong>Supervisor:</strong> {tecnico.get('supervisor', 'N/I')}</p>
                            <p><strong>Data/Hora:</strong> <span id="supervisorDateTime">--/--/---- --:--</span></p>
                        </div>
                    </div>
                    
                    <p style="color: #666; font-size: 13px; margin-top: 10px;">
                        <i class="fas fa-info-circle"></i> A assinatura do técnico é obrigatória. A assinatura do supervisor é opcional.
                    </p>
                    
                    <button id="salvarAta" class="btn-download" disabled>
                        <i class="fas fa-save"></i> SALVAR ATA E GERAR PDF
                    </button>
                </div>
            </div>
        </div>
        
        <script>
            // Dados passados do Python
            const dadosTecnico = {{
                nome: '{nome_tecnico_js}',
                codigo: '{codigo_tecnico_js}',
                supervisor: '{supervisor_js}'
            }};
            
            const causasDados = {causas_json};
            
            // Inicializar SignaturePad
            const tecnicoCanvas = document.getElementById('tecnicoCanvas');
            const supervisorCanvas = document.getElementById('supervisorCanvas');
            
            let tecnicoPad, supervisorPad;
            let tecnicoAssinado = false;
            let supervisorAssinado = false;
            let tecnicoData = null;
            let supervisorData = null;
            
            function initSignaturePads() {{
                // Ajustar dimensões dos canvases
                [tecnicoCanvas, supervisorCanvas].forEach(canvas => {{
                    const rect = canvas.getBoundingClientRect();
                    canvas.width = rect.width;
                    canvas.height = rect.height;
                }});
                
                // Inicializar pad do técnico
                tecnicoPad = new SignaturePad(tecnicoCanvas, {{
                    backgroundColor: 'rgb(255, 255, 255)',
                    penColor: '#1a3a8f',
                    minWidth: 1,
                    maxWidth: 2
                }});
                
                // Inicializar pad do supervisor
                supervisorPad = new SignaturePad(supervisorCanvas, {{
                    backgroundColor: 'rgb(255, 255, 255)',
                    penColor: '#1a3a8f',
                    minWidth: 1,
                    maxWidth: 2
                }});
                
                // Eventos do técnico
                tecnicoPad.addEventListener('beginStroke', () => {{
                    document.getElementById('tecnicoPlaceholder').style.display = 'none';
                }});
                
                // Eventos do supervisor
                supervisorPad.addEventListener('beginStroke', () => {{
                    document.getElementById('supervisorPlaceholder').style.display = 'none';
                }});
                
                // Botão limpar técnico
                document.getElementById('clearTecnico').onclick = () => {{
                    tecnicoPad.clear();
                    document.getElementById('tecnicoPlaceholder').style.display = 'block';
                    document.getElementById('tecnicoInfo').classList.remove('active');
                    document.getElementById('tecnicoStatus').className = 'signature-status status-pending';
                    document.getElementById('tecnicoStatus').textContent = 'PENDENTE';
                    tecnicoAssinado = false;
                    tecnicoData = null;
                    checkSalvarButton();
                }};
                
                // Botão validar técnico
                document.getElementById('validateTecnico').onclick = () => {{
                    if (tecnicoPad.isEmpty()) {{
                        alert('Por favor, forneça sua assinatura digital antes de validar.');
                        return;
                    }}
                    
                    const now = new Date();
                    document.getElementById('tecnicoDateTime').textContent = 
                        now.toLocaleDateString('pt-BR') + ' ' + 
                        now.toLocaleTimeString('pt-BR', {{ hour: '2-digit', minute: '2-digit' }});
                    
                    document.getElementById('tecnicoInfo').classList.add('active');
                    document.getElementById('tecnicoStatus').className = 'signature-status status-completed';
                    document.getElementById('tecnicoStatus').textContent = 'ASSINADO';
                    
                    tecnicoAssinado = true;
                    tecnicoData = tecnicoPad.toDataURL('image/png');
                    checkSalvarButton();
                }};
                
                // Botão limpar supervisor
                document.getElementById('clearSupervisor').onclick = () => {{
                    supervisorPad.clear();
                    document.getElementById('supervisorPlaceholder').style.display = 'block';
                    document.getElementById('supervisorInfo').classList.remove('active');
                    document.getElementById('supervisorStatus').className = 'signature-status status-pending';
                    document.getElementById('supervisorStatus').textContent = 'PENDENTE';
                    supervisorAssinado = false;
                    supervisorData = null;
                    checkSalvarButton();
                }};
                
                // Botão validar supervisor
                document.getElementById('validateSupervisor').onclick = () => {{
                    if (supervisorPad.isEmpty()) {{
                        alert('Por favor, forneça sua assinatura digital antes de validar.');
                        return;
                    }}
                    
                    const now = new Date();
                    document.getElementById('supervisorDateTime').textContent = 
                        now.toLocaleDateString('pt-BR') + ' ' + 
                        now.toLocaleTimeString('pt-BR', {{ hour: '2-digit', minute: '2-digit' }});
                    
                    document.getElementById('supervisorInfo').classList.add('active');
                    document.getElementById('supervisorStatus').className = 'signature-status status-completed';
                    document.getElementById('supervisorStatus').textContent = 'ASSINADO';
                    
                    supervisorAssinado = true;
                    supervisorData = supervisorPad.toDataURL('image/png');
                    checkSalvarButton();
                }};
            }}
            
            function checkSalvarButton() {{
                const salvarBtn = document.getElementById('salvarAta');
                // Apenas a assinatura do técnico é obrigatória
                if (tecnicoAssinado) {{
                    salvarBtn.disabled = false;
                }} else {{
                    salvarBtn.disabled = true;
                }}
            }}
            
            // Função para salvar o PDF automaticamente na pasta ATAS
            function salvarPDF() {{
                // Gerar PDF
                const {{ jsPDF }} = window.jspdf;
                const doc = new jsPDF('p', 'mm', 'a4');
                
                // Configurações do PDF
                const pageWidth = doc.internal.pageSize.getWidth();
                const margin = 20;
                let yPos = margin;
                
                // Cabeçalho
                doc.setFillColor(26, 58, 143);
                doc.rect(0, 0, pageWidth, 40, 'F');
                
                doc.setTextColor(255, 255, 255);
                doc.setFontSize(20);
                doc.setFont('helvetica', 'bold');
                doc.text('ATA DE RECONHECIMENTO', pageWidth / 2, 20, {{ align: 'center' }});
                
                doc.setFontSize(12);
                doc.setFont('helvetica', 'normal');
                doc.text('Documento Oficial com Assinaturas Digitais', pageWidth / 2, 30, {{ align: 'center' }});
                
                yPos = 50;
                
                // Informações do Técnico
                doc.setTextColor(0, 0, 0);
                doc.setFontSize(14);
                doc.setFont('helvetica', 'bold');
                doc.text('INFORMAÇÕES DO TÉCNICO', margin, yPos);
                
                yPos += 10;
                doc.setFontSize(12);
                doc.setFont('helvetica', 'normal');
                doc.text(`Nome: ${{dadosTecnico.nome}}`, margin, yPos);
                yPos += 7;
                doc.text(`Código: ${{dadosTecnico.codigo}}`, margin, yPos);
                yPos += 7;
                doc.text(`Supervisor: ${{dadosTecnico.supervisor}}`, margin, yPos);
                yPos += 15;
                
                // Tipo da Ata
                doc.setFontSize(14);
                doc.setFont('helvetica', 'bold');
                doc.text('TIPO DE RECONHECIMENTO', margin, yPos);
                
                yPos += 10;
                doc.setFontSize(12);
                doc.setFont('helvetica', 'normal');
                doc.text('{badge_text}', margin, yPos);
                yPos += 15;
                
                // Indicadores
                doc.setFontSize(14);
                doc.setFont('helvetica', 'bold');
                doc.text('INDICADORES', margin, yPos);
                
                yPos += 10;
                doc.setFontSize(12);
                doc.setFont('helvetica', 'normal');
                doc.text(`Mês Anterior (JAN/26): {dados.get('Mês Anterior', '-')}`, margin, yPos);
                yPos += 7;
                doc.text(`Mês Atual (FEV/26): {dados.get('Mês Atual', '-')}`, margin, yPos);
                if ('{tipo}' === 'evolucao') {{
                    yPos += 7;
                    doc.text(`Melhoria: {dados.get('Melhoria', '-')}`, margin, yPos);
                }}
                yPos += 15;
                
                // Causas Pareto
                doc.setFontSize(14);
                doc.setFont('helvetica', 'bold');
                doc.text('PRINCIPAIS CAUSAS', margin, yPos);
                
                yPos += 10;
                doc.setFontSize(10);
                doc.setFont('helvetica', 'bold');
                doc.text('Causa', margin, yPos);
                doc.text('Qtd', margin + 100, yPos);
                doc.text('%', margin + 130, yPos);
                doc.text('Acum', margin + 160, yPos);
                
                yPos += 5;
                doc.setDrawColor(200, 200, 200);
                doc.line(margin, yPos, pageWidth - margin, yPos);
                yPos += 5;
                
                doc.setFontSize(9);
                doc.setFont('helvetica', 'normal');
                
                causasDados.forEach(causa => {{
                    doc.text(causa.causa.substring(0, 25), margin, yPos);
                    doc.text(causa.quantidade.toString(), margin + 100, yPos);
                    doc.text(causa.percentual.toFixed(1) + '%', margin + 130, yPos);
                    doc.text(causa.acumulado.toFixed(1) + '%', margin + 160, yPos);
                    yPos += 7;
                }});
                
                yPos += 10;
                
                // Assinaturas
                doc.setFontSize(14);
                doc.setFont('helvetica', 'bold');
                doc.text('ASSINATURAS DIGITAIS', margin, yPos);
                
                yPos += 20;
                
                // Assinatura do Técnico
                doc.setFontSize(12);
                doc.setFont('helvetica', 'bold');
                doc.text('Técnico:', margin, yPos);
                
                yPos += 10;
                if (tecnicoData) {{
                    doc.addImage(tecnicoData, 'PNG', margin, yPos, 60, 30);
                }}
                
                yPos += 40;
                doc.setFontSize(10);
                doc.setFont('helvetica', 'normal');
                doc.text(`Data/Hora: ${{document.getElementById('tecnicoDateTime').textContent}}`, margin, yPos);
                
                yPos += 20;
                
                // Assinatura do Supervisor (opcional)
                doc.setFontSize(12);
                doc.setFont('helvetica', 'bold');
                doc.text('Supervisor:', margin, yPos);
                
                yPos += 10;
                if (supervisorData) {{
                    doc.addImage(supervisorData, 'PNG', margin, yPos, 60, 30);
                }} else {{
                    doc.setFontSize(10);
                    doc.setFont('helvetica', 'italic');
                    doc.text('(Assinatura não fornecida - opcional)', margin, yPos);
                }}
                
                if (supervisorData) {{
                    yPos += 40;
                    doc.setFontSize(10);
                    doc.setFont('helvetica', 'normal');
                    doc.text(`Data/Hora: ${{document.getElementById('supervisorDateTime').textContent}}`, margin, yPos);
                }}
                
                // Rodapé
                let dataHora = new Date().toLocaleString('pt-BR');
                doc.setFontSize(8);
                doc.setTextColor(100, 100, 100);
                doc.text('Documento gerado eletronicamente - Sistema de Atas', pageWidth / 2, 280, {{ align: 'center' }});
                doc.text(`Gerado em: ${{dataHora}}`, pageWidth / 2, 285, {{ align: 'center' }});
                
                // Nome do arquivo
                const fileName = `ATA_${{dadosTecnico.nome.replace(/ /g, '_')}}_${{new Date().toISOString().slice(0,10)}}.pdf`;
                
                // Salvar o PDF (download automático)
                doc.save(fileName);
                
                alert('ATA salva e PDF gerado com sucesso! O arquivo foi salvo na pasta de downloads do seu navegador.');
                
                // Opcional: Fechar a janela após salvar
                // window.close();
            }}
            
            // Botão salvar ata e gerar PDF
            document.getElementById('salvarAta').onclick = salvarPDF;
            
            // Inicializar ao carregar a página
            window.onload = () => {{
                initSignaturePads();
            }};
            
            // Ajustar canvas ao redimensionar
            window.addEventListener('resize', () => {{
                setTimeout(() => {{
                    [tecnicoPad, supervisorPad].forEach(pad => {{
                        if (pad && pad.canvas) {{
                            const canvas = pad.canvas;
                            const rect = canvas.getBoundingClientRect();
                            const data = pad.toData();
                            canvas.width = rect.width;
                            canvas.height = rect.height;
                            if (data && data.length > 0) {{
                                pad.fromData(data);
                            }}
                        }}
                    }});
                }}, 200);
            }});
        </script>
    </body>
    </html>
    """
    return html

# =========================================================
# CARREGAR DADOS
# =========================================================

bases_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "BASES")
raiz = os.path.dirname(os.path.abspath(__file__))

df_atual = pd.read_csv(
    os.path.join(bases_path, "VIP_2026_02_ANL_FTTH_REPETIDA_30_DIAS000000000000.csv"),
    sep=';', 
    encoding='latin1'
)

df_anterior = pd.read_csv(
    os.path.join(bases_path, "VIP_Old_2026_01_ANL_FTTH_REPETIDA_30_DIAS000000000000.csv"),
    sep=';', 
    encoding='latin1'
)

meses_historicos = {
    '2025-10': 'VIP_Old_2025_10_ANL_FTTH_REPETIDA_30_DIAS000000000000.csv',
    '2025-11': 'VIP_Old_2025_11_ANL_FTTH_REPETIDA_30_DIAS000000000000.csv',
    '2025-12': 'VIP_Old_2025_12_ANL_FTTH_REPETIDA_30_DIAS000000000000.csv',
}

df_historicos = {}
for mes, arquivo in meses_historicos.items():
    try:
        df_historicos[mes] = pd.read_csv(
            os.path.join(bases_path, arquivo),
            sep=';', 
            encoding='latin1'
        )
    except:
        st.warning(f"Arquivo {arquivo} não encontrado")

try:
    df_presenca = pd.read_excel(
        os.path.join(raiz, "Presença.xlsx"),
        sheet_name='Técnicos'
    )
except:
    df_presenca = pd.DataFrame()

try:
    df_causas = pd.read_excel(
        os.path.join(bases_path, "causas.xlsx"),
        sheet_name=0
    )
except:
    df_causas = pd.DataFrame(columns=['cod_fechamento', 'causa_macro'])

# =========================================================
# MAPEAMENTO DE CAUSAS
# =========================================================

mapa_causas = {}
if not df_causas.empty and 'cod_fechamento' in df_causas.columns:
    coluna_causa = None
    for col in df_causas.columns:
        if 'causa' in col.lower():
            coluna_causa = col
            break
    if coluna_causa:
        for _, row in df_causas.iterrows():
            cod = str(row['cod_fechamento']).strip() if pd.notna(row['cod_fechamento']) else ''
            causa = str(row[coluna_causa]).strip() if pd.notna(row[coluna_causa]) else 'Outros'
            if cod:
                mapa_causas[cod] = causa

# =========================================================
# MAPEAMENTO DE SUPERVISORES E COORDENADORES
# =========================================================

mapa_supervisor = {}
mapa_coordenador = {}
mapa_nome = {}
mapa_nome_completo = {}

if not df_presenca.empty:
    mapa_colunas = mapear_colunas_presenca(df_presenca)
    col_func = mapa_colunas.get('FUNCIONARIO')
    col_tr = mapa_colunas.get('TR')
    col_tt = mapa_colunas.get('TT')
    col_sup = mapa_colunas.get('SUPERVISOR')
    col_coord = mapa_colunas.get('COORDENADOR')
    
    if col_func and (col_tr or col_tt):
        for _, row in df_presenca.iterrows():
            nome_completo = str(row.get(col_func, ''))
            primeiro_nome = extrair_primeiro_nome(nome_completo)
            
            if col_tr and pd.notna(row.get(col_tr)):
                cod = str(row.get(col_tr)).strip()
                supervisor = extrair_primeiro_nome(str(row.get(col_sup, ''))) if col_sup and pd.notna(row.get(col_sup, '')) else 'N/I'
                coordenador = extrair_primeiro_nome(str(row.get(col_coord, ''))) if col_coord and pd.notna(row.get(col_coord, '')) else 'N/I'
                if cod:
                    mapa_supervisor[cod] = supervisor
                    mapa_coordenador[cod] = coordenador
                    mapa_nome[cod] = primeiro_nome
                    mapa_nome_completo[cod] = nome_completo
            if col_tt and pd.notna(row.get(col_tt)):
                cod = str(row.get(col_tt)).strip()
                supervisor = extrair_primeiro_nome(str(row.get(col_sup, ''))) if col_sup and pd.notna(row.get(col_sup, '')) else 'N/I'
                coordenador = extrair_primeiro_nome(str(row.get(col_coord, ''))) if col_coord and pd.notna(row.get(col_coord, '')) else 'N/I'
                if cod and cod not in mapa_supervisor:
                    mapa_supervisor[cod] = supervisor
                    mapa_coordenador[cod] = coordenador
                    mapa_nome[cod] = primeiro_nome
                    mapa_nome_completo[cod] = nome_completo

# =========================================================
# PROCESSAR MÊS ATUAL
# =========================================================

df_atual_sc = df_atual[df_atual['uf'] == 'SC'].copy()
df_atual_sc['data'] = pd.to_datetime(df_atual_sc['dat_abertura'].str[:10], format='%Y-%m-%d')
df_atual_sc['cod_tecnico'] = df_atual_sc['tecnico'].apply(extrair_tr)
df_atual_sc['cod_tecnico_anterior'] = df_atual_sc['tecnico_anterior'].apply(extrair_tr)

# Adicionar supervisores e coordenadores
df_atual_sc['supervisor'] = df_atual_sc['cod_tecnico'].map(mapa_supervisor).fillna('N/I')
df_atual_sc['coordenador'] = df_atual_sc['cod_tecnico'].map(mapa_coordenador).fillna('N/I')
df_atual_sc['nome_tecnico'] = df_atual_sc['cod_tecnico'].map(mapa_nome).fillna('N/I')
df_atual_sc['nome_completo_tecnico'] = df_atual_sc['cod_tecnico'].map(mapa_nome_completo).fillna('N/I')

# Mapear causas
df_atual_sc['cod_causa_posterior'] = df_atual_sc['cod_fechamento'].fillna('').astype(str).str.strip()
df_atual_sc['causa_macro_posterior'] = df_atual_sc['cod_causa_posterior'].map(mapa_causas).fillna('Outros')

if 'cod_fechamento_anterior' in df_atual_sc.columns:
    df_atual_sc['cod_causa_anterior'] = df_atual_sc['cod_fechamento_anterior'].fillna('').astype(str).str.strip()
else:
    df_atual_sc['cod_causa_anterior'] = ''

df_atual_sc['causa_macro_anterior'] = df_atual_sc['cod_causa_anterior'].map(mapa_causas).fillna('Outros')

df_atual_sc['in_flag_indicador'] = df_atual_sc['in_flag_indicador'].astype(str).str.strip().str.upper()

tem_tecnico_atual = df_atual_sc['cod_tecnico'].notna() & (df_atual_sc['cod_tecnico'] != '')
tem_tecnico_anterior = df_atual_sc['cod_tecnico_anterior'].notna() & (df_atual_sc['cod_tecnico_anterior'] != '')
df_atual_sc['tem_tecnico'] = tem_tecnico_atual | tem_tecnico_anterior
df_atual_sc['tem_tecnico_atual'] = tem_tecnico_atual
df_atual_sc['tem_tecnico_anterior'] = tem_tecnico_anterior

df_atual_sc['cod_tecnico_responsavel'] = None
df_atual_sc.loc[tem_tecnico_atual, 'cod_tecnico_responsavel'] = df_atual_sc.loc[tem_tecnico_atual, 'cod_tecnico']
df_atual_sc.loc[~tem_tecnico_atual & tem_tecnico_anterior, 'cod_tecnico_responsavel'] = df_atual_sc.loc[~tem_tecnico_atual & tem_tecnico_anterior, 'cod_tecnico_anterior']

df_atual_sc['is_repetido_geral'] = df_atual_sc['in_flag_indicador'] == 'SIM'
df_atual_sc['is_repetido_campo'] = df_atual_sc['is_repetido_geral'] & tem_tecnico_anterior

# =========================================================
# MÉTRICAS GERAIS
# =========================================================

total_reparos = len(df_atual_sc)
total_com_tecnico = int(df_atual_sc['tem_tecnico'].sum())
total_repetido_geral = int(df_atual_sc['is_repetido_geral'].sum())
total_repetido_campo = int(df_atual_sc['is_repetido_campo'].sum())
sem_tecnico = total_reparos - total_com_tecnico

taxa_geral = (total_repetido_geral / total_reparos * 100) if total_reparos > 0 else 0
taxa_campo = (total_repetido_campo / total_reparos * 100) if total_reparos > 0 else 0

# =========================================================
# TÉCNICOS DO MÊS ATUAL (≥3 reparos)
# =========================================================

tecnicos_atual = df_atual_sc[df_atual_sc['tem_tecnico']].groupby('cod_tecnico_responsavel').agg(
    total_reparos=('cod_tecnico_responsavel', 'size'),
    total_repetidos=('is_repetido_campo', 'sum')
).reset_index()

tecnicos_atual['percentual'] = (tecnicos_atual['total_repetidos'] / tecnicos_atual['total_reparos'] * 100).round(2)
tecnicos_atual = tecnicos_atual[tecnicos_atual['total_reparos'] >= 3]
tecnicos_atual = tecnicos_atual[tecnicos_atual['cod_tecnico_responsavel'].notna()]

tecnicos_atual['nome'] = tecnicos_atual['cod_tecnico_responsavel'].map(mapa_nome).fillna('N/I')
tecnicos_atual['nome_completo'] = tecnicos_atual['cod_tecnico_responsavel'].map(mapa_nome_completo).fillna('N/I')
tecnicos_atual['supervisor'] = tecnicos_atual['cod_tecnico_responsavel'].map(mapa_supervisor).fillna('N/I')
tecnicos_atual['coordenador'] = tecnicos_atual['cod_tecnico_responsavel'].map(mapa_coordenador).fillna('N/I')

# =========================================================
# PROCESSAR MÊS ANTERIOR
# =========================================================

df_ant_sc = df_anterior[df_anterior['uf'] == 'SC'].copy()
df_ant_sc['cod_tecnico'] = df_ant_sc['tecnico'].apply(extrair_tr)
df_ant_sc['cod_tecnico_anterior'] = df_ant_sc['tecnico_anterior'].apply(extrair_tr)
df_ant_sc['in_flag_indicador'] = df_ant_sc['in_flag_indicador'].astype(str).str.strip().str.upper()

tem_tecnico_atual_ant = df_ant_sc['cod_tecnico'].notna() & (df_ant_sc['cod_tecnico'] != '')
tem_tecnico_anterior_ant = df_ant_sc['cod_tecnico_anterior'].notna() & (df_ant_sc['cod_tecnico_anterior'] != '')
df_ant_sc['tem_tecnico'] = tem_tecnico_atual_ant | tem_tecnico_anterior_ant

df_ant_sc['cod_tecnico_responsavel'] = None
df_ant_sc.loc[tem_tecnico_atual_ant, 'cod_tecnico_responsavel'] = df_ant_sc.loc[tem_tecnico_atual_ant, 'cod_tecnico']
df_ant_sc.loc[~tem_tecnico_atual_ant & tem_tecnico_anterior_ant, 'cod_tecnico_responsavel'] = df_ant_sc.loc[~tem_tecnico_atual_ant & tem_tecnico_anterior_ant, 'cod_tecnico_anterior']

df_ant_sc['is_repetido_geral'] = df_ant_sc['in_flag_indicador'] == 'SIM'
df_ant_sc['is_repetido_campo'] = df_ant_sc['is_repetido_geral'] & tem_tecnico_anterior_ant

tecnicos_anterior = df_ant_sc[df_ant_sc['tem_tecnico']].groupby('cod_tecnico_responsavel').agg(
    total_reparos=('cod_tecnico_responsavel', 'size'),
    total_repetidos=('is_repetido_campo', 'sum')
).reset_index()

tecnicos_anterior['percentual'] = (tecnicos_anterior['total_repetidos'] / tecnicos_anterior['total_reparos'] * 100).round(2)
tecnicos_anterior = tecnicos_anterior[tecnicos_anterior['cod_tecnico_responsavel'].notna()]

# =========================================================
# AGRUPAMENTOS POR SUPERVISOR E COORDENADOR
# =========================================================

# Agrupamento por supervisor
if 'supervisor' in df_atual_sc.columns and not df_atual_sc['supervisor'].isna().all():
    df_supervisor = df_atual_sc.groupby('supervisor').agg(
        total=('supervisor', 'size'),
        repetido=('is_repetido_campo', 'sum'),
        total_com_anterior=('tem_tecnico_anterior', 'sum')
    ).reset_index()
    df_supervisor['taxa'] = (df_supervisor['repetido'] / df_supervisor['total'] * 100).round(2)
    df_supervisor = df_supervisor[df_supervisor['supervisor'] != 'N/I'].sort_values('taxa', ascending=False)
else:
    df_supervisor = pd.DataFrame()

# Agrupamento por coordenador
if 'coordenador' in df_atual_sc.columns and not df_atual_sc['coordenador'].isna().all():
    df_coordenador = df_atual_sc.groupby('coordenador').agg(
        total=('coordenador', 'size'),
        repetido=('is_repetido_campo', 'sum')
    ).reset_index()
    df_coordenador['taxa'] = (df_coordenador['repetido'] / df_coordenador['total'] * 100).round(2)
    df_coordenador = df_coordenador[df_coordenador['coordenador'] != 'N/I'].sort_values('taxa', ascending=False)
else:
    df_coordenador = pd.DataFrame()

# Agrupamento por município
if 'municipio' in df_atual_sc.columns:
    df_municipio = df_atual_sc.groupby('municipio').agg(
        total=('municipio', 'size'),
        repetido=('is_repetido_campo', 'sum')
    ).reset_index()
    df_municipio['taxa'] = (df_municipio['repetido'] / df_municipio['total'] * 100).round(2)
    df_municipio = df_municipio[df_municipio['municipio'] != 'N/I'].sort_values('taxa', ascending=False)
else:
    df_municipio = pd.DataFrame()

# =========================================================
# PROCESSAR DADOS HISTÓRICOS MENSAIS
# =========================================================

dados_mensais = []
for mes, df_hist in df_historicos.items():
    df_hist_sc = df_hist[df_hist['uf'] == 'SC'].copy() if 'uf' in df_hist.columns else df_hist.copy()
    if not df_hist_sc.empty:
        df_hist_sc['in_flag_indicador'] = df_hist_sc['in_flag_indicador'].astype(str).str.strip().str.upper()
        df_hist_sc['cod_tecnico_anterior'] = df_hist_sc['tecnico_anterior'].apply(extrair_tr)
        total = len(df_hist_sc)
        repetido_geral = int((df_hist_sc['in_flag_indicador'] == 'SIM').sum())
        tem_cod_anterior = df_hist_sc['cod_tecnico_anterior'].notna() & (df_hist_sc['cod_tecnico_anterior'] != '')
        repetido_campo = int((tem_cod_anterior & (df_hist_sc['in_flag_indicador'] == 'SIM')).sum())
        nome_mes = {'2025-10': 'OUT/25', '2025-11': 'NOV/25', '2025-12': 'DEZ/25', '2026-01': 'JAN/26'}.get(mes, mes)
        dados_mensais.append({
            'mes': mes, 'nome_mes': nome_mes, 'total': total,
            'repetido_geral': repetido_geral, 'repetido_campo': repetido_campo,
            'pct_geral': round(repetido_geral / total * 100, 2) if total > 0 else 0,
            'pct_campo': round(repetido_campo / total * 100, 2) if total > 0 else 0
        })

dados_mensais.append({
    'mes': '2026-02', 'nome_mes': 'FEV/26',
    'total': len(df_atual_sc),
    'repetido_geral': int(df_atual_sc['is_repetido_geral'].sum()),
    'repetido_campo': int(df_atual_sc['is_repetido_campo'].sum()),
    'pct_geral': round(df_atual_sc['is_repetido_geral'].sum() / len(df_atual_sc) * 100, 2),
    'pct_campo': round(df_atual_sc['is_repetido_campo'].sum() / len(df_atual_sc) * 100, 2)
})

df_mensal = pd.DataFrame(dados_mensais)
df_mensal = df_mensal.sort_values('mes')

# =========================================================
# PROCESSAR DADOS SEMANAIS
# =========================================================

df_semanal = df_atual_sc.copy()
df_semanal['semana'] = df_semanal['data'].apply(extrair_semana)
df_semanal['ano'] = 2026

dados_semanais = []
for semana in sorted(df_semanal['semana'].unique()):
    grupo = df_semanal[df_semanal['semana'] == semana]
    total = len(grupo)
    dados_semanais.append({
        'semana': semana, 'semana_label': f"Sem {int(semana)}",
        'total': total,
        'pct_geral': round(grupo['is_repetido_geral'].sum() / total * 100, 2) if total > 0 else 0,
        'pct_campo': round(grupo['is_repetido_campo'].sum() / total * 100, 2) if total > 0 else 0
    })

df_semanal = pd.DataFrame(dados_semanais)
df_semanal = df_semanal.sort_values('semana')

# =========================================================
# PROCESSAR PARETO DE CAUSAS
# =========================================================

df_campo_posterior = df_atual_sc[df_atual_sc['is_repetido_campo']].copy()
if not df_campo_posterior.empty:
    causas_posterior = df_campo_posterior['causa_macro_posterior'].value_counts().reset_index()
    causas_posterior.columns = ['causa', 'quantidade']
    causas_posterior = causas_posterior[causas_posterior['causa'].notna() & (causas_posterior['causa'] != '')]
    if not causas_posterior.empty:
        total_causas_post = causas_posterior['quantidade'].sum()
        causas_posterior['percentual'] = (causas_posterior['quantidade'] / total_causas_post * 100).round(2)
        causas_posterior['acumulado'] = causas_posterior['percentual'].cumsum().round(2)
        causas_posterior = causas_posterior.head(9)
else:
    causas_posterior = pd.DataFrame()

df_campo_anterior = df_atual_sc[df_atual_sc['is_repetido_campo']].copy()
if not df_campo_anterior.empty:
    causas_anterior = df_campo_anterior['causa_macro_anterior'].value_counts().reset_index()
    causas_anterior.columns = ['causa', 'quantidade']
    causas_anterior = causas_anterior[causas_anterior['causa'].notna() & (causas_anterior['causa'] != '')]
    if not causas_anterior.empty:
        total_causas_ant = causas_anterior['quantidade'].sum()
        causas_anterior['percentual'] = (causas_anterior['quantidade'] / total_causas_ant * 100).round(2)
        causas_anterior['acumulado'] = causas_anterior['percentual'].cumsum().round(2)
        causas_anterior = causas_anterior.head(9)
else:
    causas_anterior = pd.DataFrame()

# =========================================================
# GRÁFICO DIÁRIO
# =========================================================

df_diario_grouped = df_atual_sc.groupby('data').agg(
    total_reparos=('data', 'size'),
    total_repetidos_geral=('is_repetido_geral', 'sum'),
    total_repetidos_campo=('is_repetido_campo', 'sum')
).reset_index()
df_diario_grouped['percentual_geral'] = (df_diario_grouped['total_repetidos_geral'] / df_diario_grouped['total_reparos'] * 100).round(2)
df_diario_grouped['percentual_campo'] = (df_diario_grouped['total_repetidos_campo'] / df_diario_grouped['total_reparos'] * 100).round(2)
df_diario_grouped = df_diario_grouped.sort_values('data')

# =========================================================
# CSS PARA BALÕES E VISUAL
# =========================================================

st.markdown("""
<style>
    .main {
        font-size: 0.8rem;
    }
    .metric-card {
        background: white;
        border-radius: 10px;
        padding: 15px 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border-left: 4px solid #1a3a8f;
        transition: transform 0.2s;
        text-align: center;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.1);
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1a3a8f;
        line-height: 1.2;
        margin-bottom: 5px;
    }
    .metric-label {
        font-size: 0.7rem;
        color: #64748b;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .section-title {
        font-size: 0.9rem;
        font-weight: 700;
        color: #1a3a8f;
        margin: 8px 0 4px 0;
        padding-bottom: 2px;
        border-bottom: 2px solid #1a3a8f;
    }
    .stDataFrame {
        font-size: 0.7rem;
        width: 100%;
    }
    .dataframe {
        font-size: 0.7rem;
    }
    .stDataFrame div[data-testid="stHorizontalBlock"] {
        overflow-x: hidden;
    }
    .stDataFrame table {
        width: 100% !important;
    }
    .dataframe tbody tr:last-child {
        font-weight: 700;
        background-color: #f0f2f6;
        border-top: 2px solid #1a3a8f;
    }
    /* Escala de azul para quartis */
    .quartil-1 { 
        background-color: #08306b; 
        color: white !important;
        font-weight: 600;
    }
    .quartil-2 { 
        background-color: #2171b5; 
        color: white !important;
    }
    .quartil-3 { 
        background-color: #4292c6; 
        color: white !important;
    }
    .quartil-4 { 
        background-color: #9ecae1; 
        color: black !important;
    }
    .evolucao-positiva { color: #4caf50; font-weight: bold; }
    .evolucao-manteve { color: #ff9800; font-weight: bold; }
    .evolucao-negativa { color: #f44336; font-weight: bold; }
    /* Cards para análise de meta */
    .meta-card {
        background: #f8fafc;
        border-radius: 8px;
        padding: 10px;
        border-left: 3px solid #1a3a8f;
        margin-bottom: 10px;
    }
    .meta-title {
        font-size: 0.8rem;
        font-weight: 600;
        color: #1a3a8f;
        margin-bottom: 5px;
    }
    .meta-bom {
        background-color: #d4edda;
        color: #155724;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.7rem;
        font-weight: 600;
    }
    .meta-ruim {
        background-color: #f8d7da;
        color: #721c24;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.7rem;
        font-weight: 600;
    }
    .meta-evolucao {
        background-color: #fff3cd;
        color: #856404;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.7rem;
        font-weight: 600;
    }
    /* Botões de ata */
    .ata-button {
        background-color: #1a3a8f;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 5px 10px;
        font-size: 0.7rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s;
        width: 100%;
    }
    .ata-button:hover {
        background-color: #2563eb;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# HEADER COM 7 MÉTRICAS
# =========================================================

st.markdown(f"**🔄 PAINEL DE REPETIDAS - SC**  \n📅 2026/02")

col1, col2, col3, col4, col5, col6, col7 = st.columns(7)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{total_reparos}</div>
        <div class="metric-label">TOTAL REPAROS</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color: #2563eb;">{total_com_tecnico}</div>
        <div class="metric-label">COM TÉCNICO</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color: #2563eb;">{taxa_geral:.2f}%</div>
        <div class="metric-label">% GERAL</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color: #6b7280;">{total_repetido_geral}</div>
        <div class="metric-label">REPETIDO GERAL</div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color: #f59e0b;">{total_repetido_campo}</div>
        <div class="metric-label">REPETIDO CAMPO</div>
    </div>
    """, unsafe_allow_html=True)

with col6:
    cor = "#ef4444" if taxa_campo > 9 else "#10b981"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color: {cor};">{taxa_campo:.2f}%</div>
        <div class="metric-label">% CAMPO</div>
    </div>
    """, unsafe_allow_html=True)

with col7:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color: #6b7280;">{sem_tecnico}</div>
        <div class="metric-label">NÃO TRATADO HC</div>
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# GRÁFICOS: SUPERVISOR / COORDENADOR / PARETO CAUSAS CAMPO
# =========================================================

st.markdown("---")
col_g1, col_g2, col_g3 = st.columns(3)

with col_g1:
    st.markdown('<div class="section-title">📊 REPETIDO POR SUPERVISOR</div>', unsafe_allow_html=True)
    if not df_supervisor.empty:
        max_y = df_supervisor['taxa'].max() * 1.2 if not df_supervisor.empty else 20
        fig_sup = px.bar(
            df_supervisor.head(10),
            x='supervisor',
            y='taxa',
            text=df_supervisor.head(10)['taxa'].apply(lambda x: f'{x:.2f}%'),
            color='taxa',
            color_continuous_scale='Blues',
            height=350,
            range_y=[0, max_y]
        )
        fig_sup.add_hline(y=9, line_dash="dash", line_color="#ef4444", line_width=2)
        fig_sup.update_layout(
            plot_bgcolor='white',
            margin=dict(l=20, r=20, t=20, b=80),
            xaxis_tickangle=45,
            yaxis=dict(title=None, gridcolor='#e2e8f0'),
            showlegend=False,
            coloraxis_showscale=False
        )
        fig_sup.update_traces(textfont_size=10, textposition='outside')
        st.plotly_chart(fig_sup, use_container_width=True, config={'displayModeBar': False})
    else:
        st.info("Sem dados de supervisor")

with col_g2:
    st.markdown('<div class="section-title">📊 REPETIDO POR COORDENADOR</div>', unsafe_allow_html=True)
    if not df_coordenador.empty:
        max_y = df_coordenador['taxa'].max() * 1.2 if not df_coordenador.empty else 20
        fig_coord = px.bar(
            df_coordenador.head(10),
            x='coordenador',
            y='taxa',
            text=df_coordenador.head(10)['taxa'].apply(lambda x: f'{x:.2f}%'),
            color='taxa',
            color_continuous_scale='Blues',
            height=350,
            range_y=[0, max_y]
        )
        fig_coord.add_hline(y=9, line_dash="dash", line_color="#ef4444", line_width=2)
        fig_coord.update_layout(
            plot_bgcolor='white',
            margin=dict(l=20, r=20, t=20, b=80),
            xaxis_tickangle=45,
            yaxis=dict(title=None, gridcolor='#e2e8f0'),
            showlegend=False,
            coloraxis_showscale=False
        )
        fig_coord.update_traces(textfont_size=10, textposition='outside')
        st.plotly_chart(fig_coord, use_container_width=True, config={'displayModeBar': False})
    else:
        st.info("Dados de coordenador não disponíveis")

with col_g3:
    st.markdown('<div class="section-title">📊 PARETO - CAUSAS CAMPO</div>', unsafe_allow_html=True)
    if not causas_posterior.empty:
        fig_pareto = go.Figure()
        fig_pareto.add_trace(go.Bar(
            x=causas_posterior['causa'],
            y=causas_posterior['quantidade'],
            marker_color='#1a3a8f',
            text=causas_posterior['quantidade'],
            textposition='outside',
            textfont=dict(size=10)
        ))
        fig_pareto.add_trace(go.Scatter(
            x=causas_posterior['causa'],
            y=causas_posterior['acumulado'],
            yaxis='y2',
            mode='lines+markers',
            line=dict(color='#ef4444', width=3),
            marker=dict(size=8, color='#ef4444'),
        ))
        max_valor = causas_posterior['quantidade'].max()
        y_max = max_valor * 1.3
        fig_pareto.update_layout(
            plot_bgcolor='white',
            height=350,
            margin=dict(l=20, r=40, t=20, b=80),
            xaxis=dict(tickangle=45, tickfont=dict(size=9)),
            yaxis=dict(title=None, range=[0, y_max], gridcolor='#e2e8f0'),
            yaxis2=dict(title=None, side='right', overlaying='y', range=[0, 105]),
            showlegend=False,
            bargap=0.25
        )
        st.plotly_chart(fig_pareto, use_container_width=True, config={'displayModeBar': False})
    else:
        st.info("Sem dados de causas")

# =========================================================
# LISTAS DETALHADAS
# =========================================================

st.markdown("---")
st.markdown('<div class="section-title">📋 LISTAS DETALHADAS</div>', unsafe_allow_html=True)

col_t1, col_t2, col_t3 = st.columns(3)

with col_t1:
    st.markdown("**🔧 POR TÉCNICO**")
    if not tecnicos_atual.empty:
        df_view = tecnicos_atual.head(25)[['nome', 'cod_tecnico_responsavel', 'total_reparos', 'total_repetidos', 'percentual']].copy()
        df_view.columns = ['Nome', 'Código', 'Total', 'Rep', 'Taxa']
        df_view['Taxa'] = df_view['Taxa'].apply(lambda x: f"{x:.2f}%")
        total_geral = tecnicos_atual['total_reparos'].sum()
        total_rep = tecnicos_atual['total_repetidos'].sum()
        taxa_media = (total_rep / total_geral * 100) if total_geral > 0 else 0
        linha_total = pd.DataFrame({
            'Nome': ['TOTAL'], 'Código': [''],
            'Total': [total_geral], 'Rep': [total_rep],
            'Taxa': [f"{taxa_media:.2f}%"]
        })
        df_final = pd.concat([df_view, linha_total], ignore_index=True)
        st.dataframe(df_final, use_container_width=True, hide_index=True, height=400)

with col_t2:
    st.markdown("**👥 POR SUPERVISOR**")
    if not df_supervisor.empty:
        df_view = df_supervisor.head(25)[['supervisor', 'total', 'repetido', 'taxa', 'total_com_anterior']].copy()
        df_view.columns = ['Supervisor', 'Total', 'Repetido', 'Taxa', 'C/ Anterior']
        df_view['Taxa'] = df_view['Taxa'].apply(lambda x: f"{x:.2f}%")
        total_geral = df_supervisor['total'].sum()
        total_rep = df_supervisor['repetido'].sum()
        taxa_media = (total_rep / total_geral * 100) if total_geral > 0 else 0
        total_ant = df_supervisor['total_com_anterior'].sum() if 'total_com_anterior' in df_supervisor.columns else 0
        linha_total = pd.DataFrame({
            'Supervisor': ['TOTAL'], 'Total': [total_geral],
            'Repetido': [total_rep], 'Taxa': [f"{taxa_media:.2f}%"],
            'C/ Anterior': [total_ant]
        })
        df_final = pd.concat([df_view, linha_total], ignore_index=True)
        st.dataframe(df_final, use_container_width=True, hide_index=True, height=400)

with col_t3:
    st.markdown("**📍 POR CIDADE**")
    if not df_municipio.empty:
        df_view = df_municipio.head(25)[['municipio', 'total', 'repetido', 'taxa']].copy()
        df_view.columns = ['Município', 'Total', 'Repetido', 'Taxa']
        df_view['Taxa'] = df_view['Taxa'].apply(lambda x: f"{x:.2f}%")
        total_geral = df_municipio['total'].sum()
        total_rep = df_municipio['repetido'].sum()
        taxa_media = (total_rep / total_geral * 100) if total_geral > 0 else 0
        linha_total = pd.DataFrame({
            'Município': ['TOTAL'], 'Total': [total_geral],
            'Repetido': [total_rep], 'Taxa': [f"{taxa_media:.2f}%"]
        })
        df_final = pd.concat([df_view, linha_total], ignore_index=True)
        st.dataframe(df_final, use_container_width=True, hide_index=True, height=400)

# =========================================================
# GRÁFICO DIÁRIO
# =========================================================

st.markdown("---")
st.markdown('<div class="section-title">📅 REPETIDO DIÁRIO - GERAL vs CAMPO</div>', unsafe_allow_html=True)

if not df_diario_grouped.empty:
    fig_diario = go.Figure()
    fig_diario.add_trace(go.Scatter(
        x=df_diario_grouped['data'], y=df_diario_grouped['percentual_geral'],
        mode='lines+markers+text', name='Repetido Geral',
        line=dict(color='#1a3a8f', width=3), marker=dict(size=10, color='#1a3a8f'),
        text=df_diario_grouped['percentual_geral'].apply(lambda x: f'{x:.1f}%'),
        textposition='top center', textfont=dict(size=11, color='#1a3a8f', weight='bold')
    ))
    fig_diario.add_trace(go.Scatter(
        x=df_diario_grouped['data'], y=df_diario_grouped['percentual_campo'],
        mode='lines+markers+text', name='Repetido Campo',
        line=dict(color='#f59e0b', width=3), marker=dict(size=10, color='#f59e0b'),
        text=df_diario_grouped['percentual_campo'].apply(lambda x: f'{x:.1f}%'),
        textposition='top center', textfont=dict(size=11, color='#f59e0b', weight='bold')
    ))
    fig_diario.add_hline(y=9, line_dash="dash", line_color="#ef4444", line_width=2,
                         annotation_text="Meta 9%", annotation_position="top right")
    max_y = max(df_diario_grouped['percentual_geral'].max(), df_diario_grouped['percentual_campo'].max(), 15) * 1.2
    fig_diario.update_layout(
        plot_bgcolor='white', height=400, margin=dict(l=40, r=20, t=30, b=40),
        xaxis=dict(title=None, tickformat='%d/%m', tickfont=dict(size=11)),
        yaxis=dict(title='Percentual (%)', range=[0, max_y], ticksuffix='%', gridcolor='#e2e8f0'),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5)
    )
    st.plotly_chart(fig_diario, use_container_width=True)

# =========================================================
# HISTÓRICO DE REPETIDOS (CIGARROS)
# =========================================================

st.markdown("---")
st.markdown('<div class="section-title">📊 HISTÓRICO DE REPETIDOS</div>', unsafe_allow_html=True)

col_hist1, col_hist2 = st.columns(2)

with col_hist1:
    st.markdown("### 📅 Histórico Mensal")
    if not df_mensal.empty:
        fig_mensal = go.Figure()
        fig_mensal.add_trace(go.Bar(
            x=df_mensal['nome_mes'], y=df_mensal['pct_geral'],
            name='% Geral', marker_color='#1a3a8f',
            text=df_mensal['pct_geral'].apply(lambda x: f'{x:.1f}%'), textposition='outside',
            textfont=dict(size=10, color='#1a3a8f')
        ))
        fig_mensal.add_trace(go.Bar(
            x=df_mensal['nome_mes'], y=df_mensal['pct_campo'],
            name='% Campo', marker_color='#f59e0b',
            text=df_mensal['pct_campo'].apply(lambda x: f'{x:.1f}%'), textposition='outside',
            textfont=dict(size=10, color='#f59e0b')
        ))
        fig_mensal.add_hline(y=9, line_dash="dash", line_color="#ef4444", line_width=2)
        max_y_mensal = max(df_mensal['pct_geral'].max(), df_mensal['pct_campo'].max(), 15) * 1.2
        fig_mensal.update_layout(
            plot_bgcolor='white', height=350, margin=dict(l=20, r=20, t=40, b=50),
            xaxis=dict(title=None, tickfont=dict(size=11)),
            yaxis=dict(title='Percentual (%)', range=[0, max_y_mensal], ticksuffix='%', gridcolor='#e2e8f0'),
            barmode='group', legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5)
        )
        st.plotly_chart(fig_mensal, use_container_width=True)

with col_hist2:
    st.markdown("### 📆 Histórico Semanal (2026)")
    if not df_semanal.empty:
        fig_semanal = go.Figure()
        fig_semanal.add_trace(go.Bar(
            x=df_semanal['semana_label'], y=df_semanal['pct_geral'],
            name='% Geral', marker_color='#1a3a8f',
            text=df_semanal['pct_geral'].apply(lambda x: f'{x:.1f}%'), textposition='outside',
            textfont=dict(size=9, color='#1a3a8f')
        ))
        fig_semanal.add_trace(go.Bar(
            x=df_semanal['semana_label'], y=df_semanal['pct_campo'],
            name='% Campo', marker_color='#f59e0b',
            text=df_semanal['pct_campo'].apply(lambda x: f'{x:.1f}%'), textposition='outside',
            textfont=dict(size=9, color='#f59e0b')
        ))
        fig_semanal.add_hline(y=9, line_dash="dash", line_color="#ef4444", line_width=2)
        max_y_semanal = max(df_semanal['pct_geral'].max(), df_semanal['pct_campo'].max(), 15) * 1.2
        fig_semanal.update_layout(
            plot_bgcolor='white', height=350, margin=dict(l=20, r=20, t=40, b=50),
            xaxis=dict(title=None, tickangle=45, tickfont=dict(size=9)),
            yaxis=dict(title='Percentual (%)', range=[0, max_y_semanal], ticksuffix='%', gridcolor='#e2e8f0'),
            barmode='group', legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5)
        )
        st.plotly_chart(fig_semanal, use_container_width=True)

# =========================================================
# ANÁLISE DE ENCERRAMENTOS (PARETOS)
# =========================================================

st.markdown("---")
st.markdown('<div class="section-title">📊 ANÁLISE DE ENCERRAMENTOS</div>', unsafe_allow_html=True)

col_pareto1, col_pareto2 = st.columns(2)

with col_pareto1:
    st.markdown("### 📌 ENCERRAMENTO POSTERIOR")
    if not causas_posterior.empty:
        df_tabela_post = causas_posterior[['causa', 'quantidade', 'percentual', 'acumulado']].copy()
        df_tabela_post['percentual'] = df_tabela_post['percentual'].apply(lambda x: f"{x:.2f}%")
        df_tabela_post['acumulado'] = df_tabela_post['acumulado'].apply(lambda x: f"{x:.2f}%")
        df_tabela_post.columns = ['Causa', 'Qtd.', '%', 'Acum.']
        total_qtd_post = df_tabela_post['Qtd.'].sum()
        linha_total_post = pd.DataFrame({'Causa': ['TOTAL'], 'Qtd.': [total_qtd_post], '%': [''], 'Acum.': ['']})
        df_com_total_post = pd.concat([df_tabela_post, linha_total_post], ignore_index=True)
        st.dataframe(df_com_total_post, use_container_width=True, hide_index=True, height=300)
        
        fig_pareto1 = go.Figure()
        fig_pareto1.add_trace(go.Bar(
            x=causas_posterior['causa'], y=causas_posterior['quantidade'],
            marker_color='#1a3a8f', text=causas_posterior['quantidade'],
            textposition='outside', textfont=dict(size=10)
        ))
        fig_pareto1.add_trace(go.Scatter(
            x=causas_posterior['causa'], y=causas_posterior['acumulado'],
            yaxis='y2', mode='lines+markers',
            line=dict(color='#ef4444', width=3), marker=dict(size=8, color='#ef4444')
        ))
        max_valor = causas_posterior['quantidade'].max()
        y_max = max_valor * 1.3
        fig_pareto1.update_layout(
            plot_bgcolor='white', height=300, margin=dict(l=20, r=40, t=20, b=80),
            xaxis=dict(tickangle=45, tickfont=dict(size=9)),
            yaxis=dict(title=None, range=[0, y_max], gridcolor='#e2e8f0'),
            yaxis2=dict(title=None, side='right', overlaying='y', range=[0, 105]),
            showlegend=False, bargap=0.25
        )
        st.plotly_chart(fig_pareto1, use_container_width=True)
    else:
        st.info("Sem dados de causas posteriores")

with col_pareto2:
    st.markdown("### 📌 ENCERRAMENTO ANTERIOR")
    if not causas_anterior.empty:
        df_tabela_ant = causas_anterior[['causa', 'quantidade', 'percentual', 'acumulado']].copy()
        df_tabela_ant['percentual'] = df_tabela_ant['percentual'].apply(lambda x: f"{x:.2f}%")
        df_tabela_ant['acumulado'] = df_tabela_ant['acumulado'].apply(lambda x: f"{x:.2f}%")
        df_tabela_ant.columns = ['Causa', 'Qtd.', '%', 'Acum.']
        total_qtd_ant = df_tabela_ant['Qtd.'].sum()
        linha_total_ant = pd.DataFrame({'Causa': ['TOTAL'], 'Qtd.': [total_qtd_ant], '%': [''], 'Acum.': ['']})
        df_com_total_ant = pd.concat([df_tabela_ant, linha_total_ant], ignore_index=True)
        st.dataframe(df_com_total_ant, use_container_width=True, hide_index=True, height=300)
        
        fig_pareto2 = go.Figure()
        fig_pareto2.add_trace(go.Bar(
            x=causas_anterior['causa'], y=causas_anterior['quantidade'],
            marker_color='#1a3a8f', text=causas_anterior['quantidade'],
            textposition='outside', textfont=dict(size=10)
        ))
        fig_pareto2.add_trace(go.Scatter(
            x=causas_anterior['causa'], y=causas_anterior['acumulado'],
            yaxis='y2', mode='lines+markers',
            line=dict(color='#ef4444', width=3), marker=dict(size=8, color='#ef4444')
        ))
        max_valor = causas_anterior['quantidade'].max()
        y_max = max_valor * 1.3
        fig_pareto2.update_layout(
            plot_bgcolor='white', height=300, margin=dict(l=20, r=40, t=20, b=80),
            xaxis=dict(tickangle=45, tickfont=dict(size=9)),
            yaxis=dict(title=None, range=[0, y_max], gridcolor='#e2e8f0'),
            yaxis2=dict(title=None, side='right', overlaying='y', range=[0, 105]),
            showlegend=False, bargap=0.25
        )
        st.plotly_chart(fig_pareto2, use_container_width=True)
    else:
        st.info("Sem dados de causas anteriores")

# =========================================================
# ANÁLISE DE TÉCNICOS POR QUARTIL
# =========================================================

st.markdown("---")
st.markdown("## 📊 ANÁLISE DE TÉCNICOS POR QUARTIL")

# Verificar se há supervisores para filtrar
supervisores = sorted(tecnicos_atual['supervisor'].unique())
supervisores = ['Todos'] + [s for s in supervisores if s != 'N/I' and s != '']

if len(supervisores) > 1:
    sup_sel = st.selectbox("Filtrar por Supervisor:", supervisores)
    
    df_filtrado = tecnicos_atual.copy()
    if sup_sel != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['supervisor'] == sup_sel]
else:
    st.info("Nenhum supervisor disponível para filtro")
    df_filtrado = tecnicos_atual.copy()

if not df_filtrado.empty:
    df_comp = df_filtrado[['cod_tecnico_responsavel', 'nome', 'percentual']].copy()
    df_comp = df_comp.rename(columns={'cod_tecnico_responsavel': 'cod_tecnico', 'percentual': 'pct_atual'})
    
    if not tecnicos_anterior.empty:
        df_ant = tecnicos_anterior[['cod_tecnico_responsavel', 'percentual']].copy()
        df_ant = df_ant.rename(columns={'cod_tecnico_responsavel': 'cod_tecnico', 'percentual': 'pct_anterior'})
        
        df_comp['cod_tecnico'] = df_comp['cod_tecnico'].astype(str).str.strip()
        df_ant['cod_tecnico'] = df_ant['cod_tecnico'].astype(str).str.strip()
        
        df_final = df_comp.merge(df_ant, on='cod_tecnico', how='left')
    else:
        df_final = df_comp.copy()
        df_final['pct_anterior'] = None
    
    df_final['evolucao'] = df_final.apply(
        lambda row: 'EVOLUIU' if pd.notna(row['pct_anterior']) and row['pct_atual'] < row['pct_anterior']
        else ('MANTEVE' if pd.notna(row['pct_anterior']) and row['pct_atual'] == row['pct_anterior']
        else ('NÃO EVOLUIU' if pd.notna(row['pct_anterior']) and row['pct_atual'] > row['pct_anterior']
        else 'N/A')), axis=1
    )
    
    df_final['Mês Atual'] = df_final['pct_atual'].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "-")
    df_final['Mês Anterior'] = df_final['pct_anterior'].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "-")
    
    valores = df_final['pct_atual'].dropna()
    if len(valores) >= 4:
        q = valores.quantile([0.25, 0.5, 0.75]).tolist()
        df_final['Quartil'] = df_final['pct_atual'].apply(lambda x: classificar_quartil(x, q) if pd.notna(x) else "N/A")
        df_final = df_final.sort_values('pct_atual', ascending=True)
        
        st.markdown("### 📊 Resumo por Quartil")
        c1, c2, c3, c4 = st.columns(4)
        q1 = (df_final['Quartil'] == '1º Quartil').sum()
        q2 = (df_final['Quartil'] == '2º Quartil').sum()
        q3 = (df_final['Quartil'] == '3º Quartil').sum()
        q4 = (df_final['Quartil'] == '4º Quartil').sum()
        
        with c1: st.markdown(f"""<div style="background:#08306b; padding:15px; border-radius:8px; text-align:center; color:white"><h2>{q1}</h2><div>1º Quartil</div></div>""", unsafe_allow_html=True)
        with c2: st.markdown(f"""<div style="background:#2171b5; padding:15px; border-radius:8px; text-align:center; color:white"><h2>{q2}</h2><div>2º Quartil</div></div>""", unsafe_allow_html=True)
        with c3: st.markdown(f"""<div style="background:#4292c6; padding:15px; border-radius:8px; text-align:center; color:white"><h2>{q3}</h2><div>3º Quartil</div></div>""", unsafe_allow_html=True)
        with c4: st.markdown(f"""<div style="background:#9ecae1; padding:15px; border-radius:8px; text-align:center"><h2>{q4}</h2><div>4º Quartil</div></div>""", unsafe_allow_html=True)
    else:
        df_final['Quartil'] = 'N/A'
        df_final = df_final.sort_values('pct_atual', ascending=True)
    
    # =========================================================
    # TABELA DE TÉCNICOS COM STATUS (QUARTIL) COMO PRIMEIRA COLUNA
    # =========================================================
    st.markdown("### 📋 Tabela de Técnicos")
    df_exib = df_final[['Quartil', 'nome', 'cod_tecnico', 'Mês Anterior', 'Mês Atual', 'evolucao']].copy()
    df_exib.columns = ['STATUS', 'Técnico', 'Código', 'Mês Anterior', 'Mês Atual', 'Evolução']
    
    def cor_evol(v):
        if v == 'EVOLUIU': return 'color: green; font-weight: bold'
        if v == 'MANTEVE': return 'color: orange; font-weight: bold'
        if v == 'NÃO EVOLUIU': return 'color: red; font-weight: bold'
        return ''
    
    def cor_quartil(v):
        if v == '1º Quartil': return 'background-color: #08306b; color: white;'
        if v == '2º Quartil': return 'background-color: #2171b5; color: white;'
        if v == '3º Quartil': return 'background-color: #4292c6; color: white;'
        if v == '4º Quartil': return 'background-color: #9ecae1;'
        return ''
    
    styled = df_exib.style.applymap(cor_quartil, subset=['STATUS']).applymap(cor_evol, subset=['Evolução'])
    st.dataframe(styled, use_container_width=True, hide_index=True, height=600)
else:
    st.warning("Nenhum técnico encontrado para análise.")

# =========================================================
# ANÁLISE DE TÉCNICOS POR META COM GERAÇÃO DE ATAS (COM ASSINATURA DIGITAL)
# =========================================================

st.markdown("---")
st.markdown("## 📊 ANÁLISE DE TÉCNICOS POR META (9%) E ATAS DIGITAIS")

# Criar pasta ATAS se não existir
pasta_atas = os.path.join(bases_path, "ATAS")
Path(pasta_atas).mkdir(exist_ok=True)

# Adicionar filtro por supervisor
supervisores_lista = ['Todos'] + sorted(tecnicos_atual['supervisor'].unique().tolist())
supervisor_selecionado = st.selectbox("🔍 Filtrar por Supervisor:", supervisores_lista, key="meta_supervisor_filter")

# Filtrar tecnicos_atual pelo supervisor selecionado
tecnicos_filtrados = tecnicos_atual.copy()
if supervisor_selecionado != 'Todos':
    tecnicos_filtrados = tecnicos_filtrados[tecnicos_filtrados['supervisor'] == supervisor_selecionado]

# Usar tecnicos_filtrados para a análise
if not tecnicos_filtrados.empty and not tecnicos_anterior.empty:
    
    # Preparar dados para análise de meta
    df_meta = tecnicos_filtrados[['cod_tecnico_responsavel', 'nome', 'nome_completo', 'supervisor', 'percentual']].copy()
    df_meta = df_meta.rename(columns={'percentual': 'pct_atual'})
    
    df_ant_meta = tecnicos_anterior[['cod_tecnico_responsavel', 'percentual']].copy()
    df_ant_meta = df_ant_meta.rename(columns={'percentual': 'pct_anterior'})
    
    df_meta['cod_tecnico'] = df_meta['cod_tecnico_responsavel'].astype(str).str.strip()
    df_ant_meta['cod_tecnico'] = df_ant_meta['cod_tecnico_responsavel'].astype(str).str.strip()
    
    df_meta_completo = df_meta.merge(df_ant_meta, on='cod_tecnico', how='left')
    
    # Classificar por meta
    df_meta_completo['abaixo_9_anterior'] = df_meta_completo['pct_anterior'] < 9
    df_meta_completo['abaixo_9_atual'] = df_meta_completo['pct_atual'] < 9
    
    # Categoria 1: Técnicos com indicador abaixo de 9% nos dois meses
    df_bons = df_meta_completo[
        (df_meta_completo['abaixo_9_anterior']) & 
        (df_meta_completo['abaixo_9_atual']) &
        (df_meta_completo['pct_atual'].notna()) &
        (df_meta_completo['pct_anterior'].notna())
    ].copy()
    
    # Categoria 2: Técnicos com indicador acima de 9% nos dois meses
    df_ruins = df_meta_completo[
        (~df_meta_completo['abaixo_9_anterior']) & 
        (~df_meta_completo['abaixo_9_atual']) &
        (df_meta_completo['pct_atual'].notna()) &
        (df_meta_completo['pct_anterior'].notna())
    ].copy()
    
    # Categoria 3: Técnicos em evolução (estavam acima e agora estão abaixo)
    df_evolucao = df_meta_completo[
        (~df_meta_completo['abaixo_9_anterior']) & 
        (df_meta_completo['abaixo_9_atual']) &
        (df_meta_completo['pct_atual'].notna()) &
        (df_meta_completo['pct_anterior'].notna())
    ].copy()
    
    # Criar três colunas para as tabelas com botões de ata
    col_meta1, col_meta2, col_meta3 = st.columns(3)
    
    with col_meta1:
        st.markdown("""
        <div class="meta-card">
            <div class="meta-title">✅ ABAIXO DE 9% (DOIS MESES)</div>
            <div class="meta-bom">Técnicos com bom desempenho</div>
        </div>
        """, unsafe_allow_html=True)
        
        if not df_bons.empty:
            df_bons_display = df_bons[['nome', 'cod_tecnico', 'supervisor', 'pct_anterior', 'pct_atual']].copy()
            df_bons_display = df_bons_display.sort_values('pct_atual', ascending=True)
            df_bons_display['pct_anterior'] = df_bons_display['pct_anterior'].apply(lambda x: f"{x:.2f}%")
            df_bons_display['pct_atual'] = df_bons_display['pct_atual'].apply(lambda x: f"{x:.2f}%")
            df_bons_display.columns = ['Técnico', 'Código', 'Supervisor', 'Mês Anterior', 'Mês Atual']
            
            # Adicionar botões de ata
            for idx, row in df_bons_display.iterrows():
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                with col1:
                    st.write(f"**{row['Técnico']}**")
                with col2:
                    st.write(f"{row['Código']}")
                with col3:
                    st.write(f"{row['Supervisor']}")
                with col4:
                    if st.button(f"📄 Gerar ATA", key=f"ata_bom_{row['Código']}"):
                        # Gerar ID único para a ata
                        ata_id = str(uuid.uuid4())
                        
                        # Gerar HTML de assinatura
                        html_content = gerar_html_assinatura(
                            ata_id,
                            {'nome': row['Técnico'], 'codigo': row['Código'], 'supervisor': row['Supervisor']},
                            'parabens',
                            {'Mês Anterior': row['Mês Anterior'], 'Mês Atual': row['Mês Atual']},
                            causas_posterior
                        )
                        
                        # Salvar HTML na pasta ATAS
                        nome_arquivo = f"ata_{row['Código']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                        caminho_arquivo = os.path.join(pasta_atas, nome_arquivo)
                        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
                            f.write(html_content)
                        
                        # Criar link para download
                        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                            html_data = f.read()
                        
                        b64 = base64.b64encode(html_data.encode()).decode()
                        href = f'<a href="data:text/html;base64,{b64}" download="{nome_arquivo}" target="_blank" style="display: inline-block; background-color: #1a3a8f; color: white; padding: 5px 10px; border-radius: 4px; text-decoration: none; font-size: 12px;">📥 Abrir formulário</a>'
                        st.markdown(href, unsafe_allow_html=True)
                        st.info("Após assinar, clique em SALVAR ATA E GERAR PDF")
            
            st.caption(f"Total: {len(df_bons)} técnicos")
        else:
            st.info("Nenhum técnico nesta categoria")
    
    with col_meta2:
        st.markdown("""
        <div class="meta-card">
            <div class="meta-title">⚠️ ACIMA DE 9% (DOIS MESES)</div>
            <div class="meta-ruim">Técnicos que precisam de atenção</div>
        </div>
        """, unsafe_allow_html=True)
        
        if not df_ruins.empty:
            df_ruins_display = df_ruins[['nome', 'cod_tecnico', 'supervisor', 'pct_anterior', 'pct_atual']].copy()
            df_ruins_display = df_ruins_display.sort_values('pct_atual', ascending=False)
            df_ruins_display['pct_anterior'] = df_ruins_display['pct_anterior'].apply(lambda x: f"{x:.2f}%")
            df_ruins_display['pct_atual'] = df_ruins_display['pct_atual'].apply(lambda x: f"{x:.2f}%")
            df_ruins_display.columns = ['Técnico', 'Código', 'Supervisor', 'Mês Anterior', 'Mês Atual']
            
            for idx, row in df_ruins_display.iterrows():
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                with col1:
                    st.write(f"**{row['Técnico']}**")
                with col2:
                    st.write(f"{row['Código']}")
                with col3:
                    st.write(f"{row['Supervisor']}")
                with col4:
                    if st.button(f"📄 Gerar ATA", key=f"ata_ruim_{row['Código']}"):
                        ata_id = str(uuid.uuid4())
                        html_content = gerar_html_assinatura(
                            ata_id,
                            {'nome': row['Técnico'], 'codigo': row['Código'], 'supervisor': row['Supervisor']},
                            'atencao',
                            {'Mês Anterior': row['Mês Anterior'], 'Mês Atual': row['Mês Atual']},
                            causas_posterior
                        )
                        
                        nome_arquivo = f"ata_{row['Código']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                        caminho_arquivo = os.path.join(pasta_atas, nome_arquivo)
                        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
                            f.write(html_content)
                        
                        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                            html_data = f.read()
                        
                        b64 = base64.b64encode(html_data.encode()).decode()
                        href = f'<a href="data:text/html;base64,{b64}" download="{nome_arquivo}" target="_blank" style="display: inline-block; background-color: #1a3a8f; color: white; padding: 5px 10px; border-radius: 4px; text-decoration: none; font-size: 12px;">📥 Abrir formulário</a>'
                        st.markdown(href, unsafe_allow_html=True)
                        st.info("Após assinar, clique em SALVAR ATA E GERAR PDF")
            
            st.caption(f"Total: {len(df_ruins)} técnicos")
        else:
            st.info("Nenhum técnico nesta categoria")
    
    with col_meta3:
        st.markdown("""
        <div class="meta-card">
            <div class="meta-title">📈 EM EVOLUÇÃO</div>
            <div class="meta-evolucao">Estavam acima e agora estão abaixo de 9%</div>
        </div>
        """, unsafe_allow_html=True)
        
        if not df_evolucao.empty:
            df_evolucao_display = df_evolucao[['nome', 'cod_tecnico', 'supervisor', 'pct_anterior', 'pct_atual']].copy()
            df_evolucao_display = df_evolucao_display.sort_values('pct_atual', ascending=True)
            df_evolucao_display['pct_anterior'] = df_evolucao_display['pct_anterior'].apply(lambda x: f"{x:.2f}%")
            df_evolucao_display['pct_atual'] = df_evolucao_display['pct_atual'].apply(lambda x: f"{x:.2f}%")
            
            # Calcular melhoria
            df_evolucao_display['Melhoria'] = (
                df_evolucao['pct_anterior'] - df_evolucao['pct_atual']
            ).apply(lambda x: f"⬇️ {x:.1f}%")
            
            df_evolucao_display.columns = ['Técnico', 'Código', 'Supervisor', 'Mês Anterior', 'Mês Atual', 'Melhoria']
            
            for idx, row in df_evolucao_display.iterrows():
                col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
                with col1:
                    st.write(f"**{row['Técnico']}**")
                with col2:
                    st.write(f"{row['Código']}")
                with col3:
                    st.write(f"{row['Supervisor']}")
                with col4:
                    st.write(f"{row['Melhoria']}")
                with col5:
                    if st.button(f"📄 Gerar ATA", key=f"ata_evo_{row['Código']}"):
                        ata_id = str(uuid.uuid4())
                        html_content = gerar_html_assinatura(
                            ata_id,
                            {'nome': row['Técnico'], 'codigo': row['Código'], 'supervisor': row['Supervisor']},
                            'evolucao',
                            {'Mês Anterior': row['Mês Anterior'], 'Mês Atual': row['Mês Atual'], 'Melhoria': row['Melhoria']},
                            causas_posterior
                        )
                        
                        nome_arquivo = f"ata_{row['Código']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                        caminho_arquivo = os.path.join(pasta_atas, nome_arquivo)
                        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
                            f.write(html_content)
                        
                        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                            html_data = f.read()
                        
                        b64 = base64.b64encode(html_data.encode()).decode()
                        href = f'<a href="data:text/html;base64,{b64}" download="{nome_arquivo}" target="_blank" style="display: inline-block; background-color: #1a3a8f; color: white; padding: 5px 10px; border-radius: 4px; text-decoration: none; font-size: 12px;">📥 Abrir formulário</a>'
                        st.markdown(href, unsafe_allow_html=True)
                        st.info("Após assinar, clique em SALVAR ATA E GERAR PDF")
            
            st.caption(f"Total: {len(df_evolucao)} técnicos")
        else:
            st.info("Nenhum técnico nesta categoria")
    
    # Listar atas salvas
    with st.expander("📂 VER ATAS SALVAS"):
        if os.path.exists(pasta_atas):
            arquivos = [f for f in os.listdir(pasta_atas) if f.endswith('.html') and f.startswith('ata_')]
            if arquivos:
                for arquivo in sorted(arquivos, reverse=True)[:20]:
                    st.write(f"📄 {arquivo}")
            else:
                st.info("Nenhuma ata salva ainda.")
        else:
            st.info("Pasta de atas ainda não foi criada.")

else:
    st.info("Dados insuficientes para análise de meta")

# =========================================================
# FOOTER
# =========================================================

st.markdown(f"""
<div style="text-align:center;color:#64748b;margin-top:10px;padding:5px;background:#f8fafc;border-radius:6px">
    <b>Painel de Repetidas - SC</b> • 2026/02 • 
    Total: {total_reparos} • COM TÉCNICO: {total_com_tecnico} • 
    % Geral: {taxa_geral:.2f}% • Rep Geral: {total_repetido_geral} •
    Rep Campo: {total_repetido_campo} ({taxa_campo:.2f}%) •
    <b>Não Tratado HC: {sem_tecnico}</b>
</div>
""", unsafe_allow_html=True)