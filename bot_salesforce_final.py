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
# CONFIGURAÇÕES - SUAS COORDENADAS ATUALIZADAS (15/02/2026)
# =========================================================
# Coordenadas calibradas manualmente
BOTAO_EDITAR = (1879, 257)        # ✅ Habilitar Edição
BOTAO_EXPORTAR_1 = (1821, 353)     # ✅ Primeiro Exportar
OPCAO_DETALHES = (795, 525)        # ✅ Detalhes apenas
BOTAO_EXPORTAR_2 = (1210, 756)     # ✅ Último Exportar
BARRA_ENDERECO = (783, 49)         # ✅ Barra de endereço
CAMPO_NOME = (482, 630)            # ✅ Campo nome do arquivo
BOTAO_SALVAR = (905, 730)          # ✅ Botão Salvar
BOTAO_SUBSTITUIR = (1005, 530)     # ✅ Botão Substituir

# URLs e nomes
URL_RELATORIO = "https://oimoveltrialorg2021.lightning.force.com/lightning/r/Report/00ON400000IiQkPMAV/view"
NOME_ARQUIVO = "base.xlsx"

# Tempos de espera
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
        print(f"   ✅ Coordenadas: {BOTAO_EDITAR}")
        time.sleep(TEMPO_PEQUENO)
        
        # 5. Primeiro Exportar
        print("\n⬇️ Clicando em 'Exportar'...")
        pyautogui.click(*BOTAO_EXPORTAR_1)
        print(f"   ✅ Coordenadas: {BOTAO_EXPORTAR_1}")
        time.sleep(TEMPO_PEQUENO * 2)
        
        # 6. Selecionar Detalhes
        print("\n📊 Selecionando 'Detalhes apenas'...")
        pyautogui.click(*OPCAO_DETALHES)
        print(f"   ✅ Coordenadas: {OPCAO_DETALHES}")
        time.sleep(TEMPO_PEQUENO)
        
        # 7. Exportar final
        print("\n✅ Confirmando...")
        pyautogui.click(*BOTAO_EXPORTAR_2)
        print(f"   ✅ Coordenadas: {BOTAO_EXPORTAR_2}")
        
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
        print("   📍 Clicando na barra de endereço...")
        pyautogui.click(*BARRA_ENDERECO)
        print(f"      ✅ Coordenadas: {BARRA_ENDERECO}")
        time.sleep(TEMPO_PEQUENO)
        
        # Digitar o caminho da pasta
        print(f"   📝 Digitando caminho: {BASE_PATH}")
        pyautogui.write(BASE_PATH)
        time.sleep(TEMPO_PEQUENO)
        pyautogui.press('enter')
        print("   ✅ Enter pressionado")
        time.sleep(TEMPO_PEQUENO * 2)
        
        # Clicar no campo de nome do arquivo
        print("   📝 Clicando no campo nome...")
        pyautogui.click(*CAMPO_NOME)
        print(f"      ✅ Coordenadas: {CAMPO_NOME}")
        time.sleep(TEMPO_PEQUENO)
        
        # Digitar nome do arquivo
        print(f"   📝 Digitando nome: {NOME_ARQUIVO}")
        pyautogui.write(NOME_ARQUIVO)
        time.sleep(TEMPO_PEQUENO)
        
        # Clicar em Salvar
        print("   💾 Clicando em Salvar...")
        pyautogui.click(*BOTAO_SALVAR)
        print(f"      ✅ Coordenadas: {BOTAO_SALVAR}")
        time.sleep(TEMPO_PEQUENO * 2)
        
        # Substituir se necessário
        print("\n🔄 Verificando substituição...")
        pyautogui.click(*BOTAO_SUBSTITUIR)
        print(f"   ✅ Coordenadas: {BOTAO_SUBSTITUIR}")
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
        import traceback
        traceback.print_exc()

# =========================================================
# MENU PRINCIPAL
# =========================================================

def modo_calibracao():
    """Ajuda a encontrar as coordenadas dos botões"""
    print("\n🎯 MODO CALIBRAÇÃO")
    print("-" * 40)
    print("Mova o mouse sobre cada botão e pressione ENTER")
    print("(Pressione Ctrl+C para sair)")
    print("-" * 40)
    
    coordenadas = {}
    
    input("\n1️⃣ Mova sobre 'Habilitar Edição' e pressione ENTER")
    x, y = pyautogui.position()
    coordenadas['EDITAR'] = (x, y)
    print(f"   ✅ Coordenadas: X={x}, Y={y}")
    
    input("\n2️⃣ Mova sobre o primeiro 'Exportar' e pressione ENTER")
    x, y = pyautogui.position()
    coordenadas['EXPORTAR_1'] = (x, y)
    print(f"   ✅ Coordenadas: X={x}, Y={y}")
    
    input("\n3️⃣ Mova sobre 'Detalhes apenas' e pressione ENTER")
    x, y = pyautogui.position()
    coordenadas['DETALHES'] = (x, y)
    print(f"   ✅ Coordenadas: X={x}, Y={y}")
    
    input("\n4️⃣ Mova sobre o último 'Exportar' e pressione ENTER")
    x, y = pyautogui.position()
    coordenadas['EXPORTAR_2'] = (x, y)
    print(f"   ✅ Coordenadas: X={x}, Y={y}")
    
    input("\n5️⃣ Mova sobre a BARRA DE ENDEREÇO do Explorer e pressione ENTER")
    x, y = pyautogui.position()
    coordenadas['BARRA_ENDERECO'] = (x, y)
    print(f"   ✅ Coordenadas: X={x}, Y={y}")
    
    input("\n6️⃣ Mova sobre o campo NOME DO ARQUIVO e pressione ENTER")
    x, y = pyautogui.position()
    coordenadas['CAMPO_NOME'] = (x, y)
    print(f"   ✅ Coordenadas: X={x}, Y={y}")
    
    input("\n7️⃣ Mova sobre o botão 'SALVAR' e pressione ENTER")
    x, y = pyautogui.position()
    coordenadas['SALVAR'] = (x, y)
    print(f"   ✅ Coordenadas: X={x}, Y={y}")
    
    input("\n8️⃣ Mova sobre o botão 'SUBSTITUIR' e pressione ENTER")
    x, y = pyautogui.position()
    coordenadas['SUBSTITUIR'] = (x, y)
    print(f"   ✅ Coordenadas: X={x}, Y={y}")
    
    print("\n" + "="*50)
    print("📋 COPIE ESTAS COORDENADAS PARA O SCRIPT:")
    print("="*50)
    print(f"BOTAO_EDITAR = {coordenadas['EDITAR']}")
    print(f"BOTAO_EXPORTAR_1 = {coordenadas['EXPORTAR_1']}")
    print(f"OPCAO_DETALHES = {coordenadas['DETALHES']}")
    print(f"BOTAO_EXPORTAR_2 = {coordenadas['EXPORTAR_2']}")
    print(f"BARRA_ENDERECO = {coordenadas['BARRA_ENDERECO']}")
    print(f"CAMPO_NOME = {coordenadas['CAMPO_NOME']}")
    print(f"BOTAO_SALVAR = {coordenadas['SALVAR']}")
    print(f"BOTAO_SUBSTITUIR = {coordenadas['SUBSTITUIR']}")
    print("="*50)

if __name__ == "__main__":
    print("🤖 ROBÔ DE DOWNLOAD DO SALESFORCE")
    print("="*40)
    print("1️⃣  Executar robô")
    print("2️⃣  Modo calibração (descobrir coordenadas)")
    print("3️⃣  Sair")
    print("="*40)
    
    opcao = input("Escolha uma opção (1/2/3): ").strip()
    
    if opcao == '1':
        baixar_relatorio()
    elif opcao == '2':
        modo_calibracao()
    else:
        print("👋 Até mais!")