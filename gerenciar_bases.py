# gerenciar_bases.py
import os
import shutil
from pathlib import Path

# Configurações
BASE_ORIGEM = r"C:\Users\dlucc\Downloads"  # Ajuste para onde estão seus arquivos
BASE_DESTINO = r"C:\Users\dlucc\ABILITY\OneDrive - ABILITY TECNOLOGIA E SERVIÇOS S A\PY\painel\BASES"

# Lista de arquivos esperados
ARQUIVOS = [
    "VIP_2026_02_ANL_FTTH_INFANCIA_30_DIAS_INSTALACAO000000000000.xlsx",
    "VIP_2026_02_ANL_FTTH_INFANCIA_30_DIAS000000000000.xlsx",
    "VIP_2026_02_ANL_FTTH_INSTALACAO_NO_PRAZO000000000000.xlsx",
    "VIP_2026_02_ANL_FTTH_PLANTA000000000000.xlsx",
    "VIP_2026_02_ANL_FTTH_REPARO_NO_PRAZO000000000000.xlsx",
    "VIP_2026_02_ANL_FTTH_REPARO_POR_PLANTA000000000000.xlsx",
    "VIP_2026_02_ANL_FTTH_REPETIDA_30_DIAS000000000000.xlsx"
]

def copiar_bases():
    print("📂 Copiando bases...")
    
    # Criar pasta destino se não existir
    os.makedirs(BASE_DESTINO, exist_ok=True)
    
    for arquivo in ARQUIVOS:
        origem = os.path.join(BASE_ORIGEM, arquivo)
        destino = os.path.join(BASE_DESTINO, arquivo)
        
        if os.path.exists(origem):
            shutil.copy2(origem, destino)
            print(f"✅ Copiado: {arquivo}")
        else:
            print(f"⚠️ Arquivo não encontrado: {arquivo}")
    
    print("\n🎉 Processo concluído!")

def listar_bases():
    print("\n📋 Bases na pasta:")
    if os.path.exists(BASE_DESTINO):
        for arquivo in os.listdir(BASE_DESTINO):
            tamanho = os.path.getsize(os.path.join(BASE_DESTINO, arquivo)) / 1024
            print(f"   📄 {arquivo} ({tamanho:.1f} KB)")
    else:
        print("   Pasta não encontrada!")

if __name__ == "__main__":
    print("="*50)
    print("🚀 GERENCIADOR DE BASES")
    print("="*50)
    print("1️⃣  Copiar bases para pasta")
    print("2️⃣  Listar bases na pasta")
    print("3️⃣  Sair")
    
    opcao = input("\nEscolha: ")
    
    if opcao == "1":
        copiar_bases()
    elif opcao == "2":
        listar_bases()