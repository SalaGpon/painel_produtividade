# bot_salesforce_final.py
import pyautogui
import time
import os
import subprocess
from datetime import datetime
import pygetwindow as gw
from config import BASE_PATH, DOWNLOAD_PATH

# Configurações de segurança
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.5

# =========================================================
# CONFIGURAÇÕES - SUAS COORDENADAS
# =========================================================
BOTAO_EDITAR = (1880, 254)
BOTAO_EXPORTAR_1 = (1820, 355)
OPCAO_DETALHES = (761, 605)
BOTAO_EXPORTAR_2 = (1219, 755)
BARRA_ENDERECO = (627, 49)
BOTAO_SALVAR = (903, 734)
BOTAO_SUBSTITUIR = (1013, 528)

URL_RELATORIO = "https://oimoveltrialorg2021.lightning.force.com/lightning/r/Report/00ON400000IiQkPMAV/view"
NOME_ARQUIVO = "base.xlsx"

TEMPO_CARREGAMENTO = 8
TEMPO_ESPERA_DOWNLOAD = 140
TEMPO_PEQUENO = 2

def focar_firefox():
    """Traz a janela do Firefox para frente"""
    try:
        janelas = gw.getWindowsWithTitle('Firefox')
        if not janelas:
            janelas = gw.getWindowsWithTitle('Mozilla')
        if janelas:
            firefox = janelas[0]
            firefox.activate()
            time.sleep(2)
            print("✅ Janela do Firefox ativada")
            return True
    except Exception as e:
        print(f"⚠️ Erro: {e}")
    
    os.system("start firefox")
    time.sleep(5)
    return True

def baixar_relatorio():
    print("="*60)
    print(f"🤖 ROBÔ DE DOWNLOAD")
    print(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"📁 Pasta: {BASE_PATH}")
    print("="*60)
    
    try:
        # 1. Focar Firefox
        print("\n🔍 Ativando Firefox...")
        focar_firefox()
        
        # 2. Abrir nova aba
        print("📂 Abrindo nova aba...")
        pyautogui.hotkey('ctrl', 't')
        time.sleep(1)
        
        # 3. Digitar URL
        print("🔗 Navegando...")
        pyautogui.write(URL_RELATORIO)
        pyautogui.press('enter')
        print(f"⏳ Aguardando {TEMPO_CARREGAMENTO}s...")
        time.sleep(TEMPO_CARREGAMENTO)
        
        # 4. Clicar em Editar
        print("\n✏️ Clicando em 'Habilitar Edição'...")
        pyautogui.click(*BOTAO_EDITAR)
        time.sleep(TEMPO_PEQUENO)
        
        # 5. Primeiro Exportar
        print("\n⬇️ Clicando em 'Exportar'...")
        pyautogui.click(*BOTAO_EXPORTAR_1)
        time.sleep(TEMPO_PEQUENO * 2)
        
        # 6. Selecionar Detalhes
        print("\n📊 Selecionando 'Detalhes apenas'...")
        pyautogui.click(*OPCAO_DETALHES)
        time.sleep(TEMPO_PEQUENO)
        
        # 7. Exportar final
        print("\n✅ Confirmando...")
        pyautogui.click(*BOTAO_EXPORTAR_2)
        
        # 8. Aguardar download
        print(f"\n⏳ Aguardando {TEMPO_ESPERA_DOWNLOAD}s...")
        for i in range(TEMPO_ESPERA_DOWNLOAD):
            time.sleep(1)
            if i % 20 == 0:
                minutos = (TEMPO_ESPERA_DOWNLOAD - i) // 60
                segundos = (TEMPO_ESPERA_DOWNLOAD - i) % 60
                print(f"   ⏱️  Restante: {minutos}min {segundos:02d}s")
        
        # 9. Salvar na pasta correta
        print("\n📁 Salvando arquivo...")
        time.sleep(TEMPO_PEQUENO)
        
        # Clicar na barra de endereço
        pyautogui.click(*BARRA_ENDERECO)
        time.sleep(TEMPO_PEQUENO)
        
        # Digitar o caminho da pasta
        pyautogui.write(BASE_PATH)
        time.sleep(TEMPO_PEQUENO)
        pyautogui.press('enter')
        time.sleep(TEMPO_PEQUENO * 2)
        
        # Digitar nome do arquivo
        pyautogui.click(500, 500)
        time.sleep(TEMPO_PEQUENO)
        pyautogui.write(NOME_ARQUIVO)
        time.sleep(TEMPO_PEQUENO)
        
        # Clicar em Salvar
        pyautogui.click(*BOTAO_SALVAR)
        time.sleep(TEMPO_PEQUENO * 2)
        
        # Substituir se necessário
        print("\n🔄 Verificando substituição...")
        pyautogui.click(*BOTAO_SUBSTITUIR)
        time.sleep(TEMPO_PEQUENO)
        
        # 10. Fechar aba
        print("\n📪 Fechando aba...")
        pyautogui.hotkey('ctrl', 'w')
        
        # 11. Atualizar banco
        print("\n📤 Atualizando banco...")
        subprocess.run(["python", "atualizar_dados.py"], check=True)
        
        print("\n" + "="*60)
        print("🎉 PROCESSO CONCLUÍDO!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")

if __name__ == "__main__":
    baixar_relatorio()