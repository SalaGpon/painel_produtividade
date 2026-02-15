# config.py
import os

# Caminho base do projeto
BASE_PATH = r"C:\Users\dlucc\ABILITY\OneDrive - ABILITY TECNOLOGIA E SERVIÇOS S A\PY\painel"

# Caminhos importantes
EXCEL_PATH = os.path.join(BASE_PATH, "base.xlsx")
DOWNLOAD_PATH = os.path.join(BASE_PATH, "downloads")

# Criar pasta de downloads se não existir
if not os.path.exists(DOWNLOAD_PATH):
    os.makedirs(DOWNLOAD_PATH)

print(f"✅ Config carregada: {BASE_PATH}")
print(f"📁 Pasta de downloads: {DOWNLOAD_PATH}")