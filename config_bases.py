# config_bases.py
import os
from datetime import datetime

# Caminho base das bases
BASE_PATH = r"C:\Users\dlucc\ABILITY\OneDrive - ABILITY TECNOLOGIA E SERVIÇOS S A\PY\painel\BASES"

# Dicionário com todas as bases
BASES = {
    'infancia': {
        'nome': 'VIP_2026_02_ANL_FTTH_INFANCIA_30_DIAS_INSTALACAO000000000000',
        'descricao': 'Numerador de Indicador Infância',
        'indicador': 'Infância 30 Dias'
    },
    'infancia_base': {
        'nome': 'VIP_2026_02_ANL_FTTH_INFANCIA_30_DIAS000000000000',
        'descricao': 'Base Infância',
        'indicador': 'Infância 30 Dias'
    },
    'instalacao_prazo': {
        'nome': 'VIP_2026_02_ANL_FTTH_INSTALACAO_NO_PRAZO000000000000',
        'descricao': 'Instalação no Prazo',
        'indicador': 'Instalação no Prazo 96h'
    },
    'planta': {
        'nome': 'VIP_2026_02_ANL_FTTH_PLANTA000000000000',
        'descricao': 'Reparo por Planta',
        'indicador': 'Reparo por Planta'
    },
    'reparo_prazo': {
        'nome': 'VIP_2026_02_ANL_FTTH_REPARO_NO_PRAZO000000000000',
        'descricao': 'Reparo no Prazo',
        'indicador': 'Reparo no Prazo 24h'
    },
    'repetida': {
        'nome': 'VIP_2026_02_ANL_FTTH_REPETIDA_30_DIAS000000000000',
        'descricao': 'Repetida 30 dias',
        'indicador': 'Repetida 30 dias'
    }
}

def get_base_path(nome_base):
    """Retorna o caminho completo da base"""
    return os.path.join(BASE_PATH, nome_base)

def listar_bases_disponiveis():
    """Lista todas as bases encontradas na pasta"""
    bases_encontradas = []
    if os.path.exists(BASE_PATH):
        for arquivo in os.listdir(BASE_PATH):
            for key, base in BASES.items():
                if base['nome'] in arquivo:
                    bases_encontradas.append({
                        'arquivo': arquivo,
                        'caminho': os.path.join(BASE_PATH, arquivo),
                        'descricao': base['descricao'],
                        'indicador': base['indicador']
                    })
    return bases_encontradas