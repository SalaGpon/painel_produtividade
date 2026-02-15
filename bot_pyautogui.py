# bot_salesforce_final.py
import pyautogui
import time
import os
import subprocess
from datetime import datetime
import pygetwindow as gw

# Configurações de segurança
pyautogui.FAILSAFE = True  # Move mouse para canto superior esquerdo para parar
pyautogui.PAUSE = 0.5  # Pausa de 0.5 segundo entre comandos

# =========================================================
# CONFIGURAÇÕES - SUAS COORDENADAS (CALIBRADAS)
# =========================================================
# ✅ Coordenadas capturadas em 14/02/2026

BOTAO_EDITAR = (1880, 254)      # "Habilitar Edição em campo"
BOTAO_EXPORTAR_1 = (1820, 355)   # Primeiro botão "Exportar"
OPCAO_DETALHES = (761, 605)      # Opção "Detalhes apenas"
BOTAO_EXPORTAR_2 = (1219, 755)   # Botão "Exportar" final

# Coordenadas para a janela de download
BARRA_ENDERECO = (627, 49)       # Clique na barra de endereço do Explorer
BOTAO_SALVAR = (903, 734)        # Botão "Salvar"
BOTAO_SUBSTITUIR = (1013, 528)   # Botão "Substituir" (quando pergunta)

# URLs
URL_RELATORIO = "https://oimoveltrialorg2021.lightning.force.com/lightning/r/Report/00ON400000IiQkPMAV/view"

# Caminhos
PASTA_DESTINO = r"C:\Users\dlucc\painel"
NOME_ARQUIVO = "base.xlsx"

# Tempos de espera (ajuste se necessário)
TEMPO_CARREGAMENTO = 8
TEMPO_ESPERA_DOWNLOAD = 140  # 2 minutos e 20 segundos
TEMPO_PEQUENO = 2

# =========================================================
# FUNÇÕES
# =========================================================

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
    
    # Se não encontrar, abre uma nova
    os.system("start firefox")
    time.sleep(5)
    return True

def baixar_relatorio():
    print("="*60)
    print(f"🤖 INICIANDO ROBÔ - {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print("="*60)
    
    try:
        # 1. Focar no Firefox
        print("\n🔍 Ativando Firefox...")
        focar_firefox()
        
        # 2. Abrir nova aba (Ctrl+T)
        print("📂 Abrindo nova aba...")
        pyautogui.hotkey('ctrl', 't')
        time.sleep(1)
        
        # 3. Digitar a URL
        print("🔗 Navegando para o relatório...")
        pyautogui.write(URL_RELATORIO)
        pyautogui.press('enter')
        print(f"⏳ Aguardando {TEMPO_CARREGAMENTO} segundos...")
        time.sleep(TEMPO_CARREGAMENTO)
        
        # 4. Clicar em "Habilitar Edição em campo"
        print("\n✏️ Clicando em 'Habilitar Edição'...")
        pyautogui.click(*BOTAO_EDITAR)
        print(f"   ✅ Coordenadas: {BOTAO_EDITAR}")
        time.sleep(TEMPO_PEQUENO)
        
        # 5. Clicar no primeiro "Exportar"
        print("\n⬇️ Clicando em 'Exportar'...")
        pyautogui.click(*BOTAO_EXPORTAR_1)
        print(f"   ✅ Coordenadas: {BOTAO_EXPORTAR_1}")
        time.sleep(TEMPO_PEQUENO * 2)
        
        # 6. Selecionar "Detalhes apenas"
        print("\n📊 Selecionando 'Detalhes apenas'...")
        pyautogui.click(*OPCAO_DETALHES)
        print(f"   ✅ Coordenadas: {OPCAO_DETALHES}")
        time.sleep(TEMPO_PEQUENO)
        
        # 7. Clicar no botão final "Exportar"
        print("\n✅ Confirmando exportação...")
        pyautogui.click(*BOTAO_EXPORTAR_2)
        print(f"   ✅ Coordenadas: {BOTAO_EXPORTAR_2}")
        
        # =========================================================
        # ETAPA 8: AGUARDAR DOWNLOAD (2 MINUTOS E 20 SEGUNDOS)
        # =========================================================
        print(f"\n⏳ AGUARDANDO DOWNLOAD - {TEMPO_ESPERA_DOWNLOAD} segundos (2min20s)...")
        for i in range(TEMPO_ESPERA_DOWNLOAD):
            time.sleep(1)
            if i % 20 == 0:  # Mostra a cada 20 segundos
                minutos_restantes = (TEMPO_ESPERA_DOWNLOAD - i) // 60
                segundos_restantes = (TEMPO_ESPERA_DOWNLOAD - i) % 60
                print(f"   ⏱️  Restante: {minutos_restantes}min {segundos_restantes:02d}s")
        
        # =========================================================
        # ETAPA 9: SELECIONAR LOCAL E SALVAR ARQUIVO
        # =========================================================
        print("\n📁 Configurando local do arquivo...")
        
        # 9.1 Clicar na barra de endereço do Explorer
        time.sleep(TEMPO_PEQUENO)
        pyautogui.click(*BARRA_ENDERECO)
        print(f"   ✅ Clicou na barra de endereço: {BARRA_ENDERECO}")
        time.sleep(TEMPO_PEQUENO)
        
        # 9.2 Digitar o caminho da pasta
        pyautogui.write(PASTA_DESTINO)
        print(f"   ✅ Digitou caminho: {PASTA_DESTINO}")
        time.sleep(TEMPO_PEQUENO)
        pyautogui.press('enter')
        print(f"   ✅ Enter pressionado")
        time.sleep(TEMPO_PEQUENO * 2)
        
        # 9.3 Clicar no campo de nome do arquivo
        # Posição aproximada do campo de nome (ajuste se necessário)
        pyautogui.click(500, 500)
        print(f"   ✅ Clicou no campo de nome")
        time.sleep(TEMPO_PEQUENO)
        
        # 9.4 Digitar o nome do arquivo
        pyautogui.write(NOME_ARQUIVO)
        print(f"   ✅ Digitou nome: {NOME_ARQUIVO}")
        time.sleep(TEMPO_PEQUENO)
        
        # 9.5 Clicar em "Salvar"
        pyautogui.click(*BOTAO_SALVAR)
        print(f"   ✅ Clicou em Salvar: {BOTAO_SALVAR}")
        time.sleep(TEMPO_PEQUENO * 2)
        
        # =========================================================
        # ETAPA 10: CONFIRMAR SUBSTITUIÇÃO SE PERGUNTAR
        # =========================================================
        print("\n🔄 Verificando se precisa substituir...")
        time.sleep(TEMPO_PEQUENO)
        
        # Tenta clicar em "Substituir" (se aparecer a janela)
        pyautogui.click(*BOTAO_SUBSTITUIR)
        print(f"   ✅ Clicou em Substituir: {BOTAO_SUBSTITUIR}")
        time.sleep(TEMPO_PEQUENO)
        
        # 11. Fechar aba (Ctrl+W)
        print("\n📪 Fechando aba...")
        pyautogui.hotkey('ctrl', 'w')
        
        # =========================================================
        # ETAPA 12: EXECUTAR ATUALIZAÇÃO DO BANCO
        # =========================================================
        print("\n📤 Atualizando banco de dados...")
        try:
            subprocess.run(["python", "atualizar_dados.py"], check=True)
            print("✅ Banco atualizado!")
        except Exception as e:
            print(f"⚠️ Erro na atualização: {e}")
        
        print("\n" + "="*60)
        print("🎉 PROCESSO CONCLUÍDO COM SUCESSO!")
        print(f"🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ ERRO DURANTE EXECUÇÃO: {e}")
        print("🔍 Verifique se as coordenadas ainda estão corretas")

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
    
    input("\n6️⃣ Mova sobre o botão 'SALVAR' e pressione ENTER")
    x, y = pyautogui.position()
    coordenadas['SALVAR'] = (x, y)
    print(f"   ✅ Coordenadas: X={x}, Y={y}")
    
    input("\n7️⃣ Mova sobre o botão 'SUBSTITUIR' e pressione ENTER")
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
    print(f"BOTAO_SALVAR = {coordenadas['SALVAR']}")
    print(f"BOTAO_SUBSTITUIR = {coordenadas['SUBSTITUIR']}")
    print("="*50)

# =========================================================
# MENU PRINCIPAL
# =========================================================

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