# download_salesforce.py
from simple_salesforce import Salesforce
import pandas as pd
import requests
from datetime import datetime
import os

# Configurações
SF_USERNAME = "seu.email@dominio.com"
SF_PASSWORD = "sua_senha"
SF_SECURITY_TOKEN = "seu_token"  # Necessário se tiver restrição de IP
SF_DOMAIN = "login"  # ou "test" para sandbox
REPORT_ID = "00ON400000IiQkPMAV"

def download_relatorio_salesforce():
    print(f"📅 Iniciando download - {datetime.now()}")
    
    # 1. Conectar ao Salesforce
    sf = Salesforce(
        username=SF_USERNAME,
        password=SF_PASSWORD,
        security_token=SF_SECURITY_TOKEN,
        domain=SF_DOMAIN
    )
    print("✅ Conectado ao Salesforce")
    
    # 2. Fazer requisição para o relatório
    # Usando a Analytics API [citation:4][citation:7]
    headers = {
        'Authorization': f'Bearer {sf.session_id}',
        'Content-Type': 'application/json'
    }
    
    # Para relatórios tabulares, podemos baixar diretamente como CSV
    report_url = f"{sf.base_url}analytics/reports/{REPORT_ID}"
    
    response = requests.get(
        report_url,
        headers={'Authorization': f'Bearer {sf.session_id}'},
        params={
            'includeDetails': 'true',
            'exportFormat': 'csv'
        }
    )
    
    if response.status_code == 200:
        # Salvar CSV
        csv_path = r"C:\Users\dlucc\painel\base_atualizada.csv"
        with open(csv_path, 'wb') as f:
            f.write(response.content)
        print(f"✅ Relatório salvo em: {csv_path}")
        return csv_path
    else:
        print(f"❌ Erro: {response.status_code}")
        return None

if __name__ == "__main__":
    download_relatorio_salesforce()