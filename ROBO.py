# bot_salesforce_sessao_existente.py
from playwright.sync_api import sync_playwright
import time
import os
from datetime import datetime
import subprocess
import pygetwindow as gw
import pyautogui

def encontrar_janela_firefox():
    """Tenta encontrar e focar na janela do Firefox"""
    try:
        # Lista todas as janelas abertas
        janelas = gw.getWindowsWithTitle('Firefox')
        if janelas:
            # Pega a primeira janela do Firefox
            firefox = janelas[0]
            firefox.activate()  # Traz para frente
            time.sleep(1)
            return True
    except:
        pass
    return False

def baixar_relatorio_salesforce():
    print(f"🤖 INICIANDO ROBÔ - {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    
    # 1. Primeiro, tentar encontrar janela do Firefox já aberta
    if not encontrar_janela_firefox():
        print("⚠️ Janela do Firefox não encontrada!")
        print("👉 Por favor, abra o Firefox e faça login no Salesforce")
        input("Pressione ENTER quando estiver pronto...")
    
    with sync_playwright() as p:
        # Conectar a uma instância existente do Firefox
        # Isso requer que o Firefox esteja com debug remoto habilitado
        
        # Opção A: Conectar via CDP (mais avançado)
        browser = p.firefox.connect_over_cdp("http://localhost:9222")
        
        # Ou Opção B: Abrir novo contexto na mesma sessão
        context = browser.contexts[0]  # Pega o contexto existente
        page = context.new_page()  # Abre nova aba
        
        try:
            # 2. IR DIRETO PARA O RELATÓRIO (já está logado!)
            print("📊 Navegando para o relatório...")
            report_url = "https://oimoveltrialorg2021.lightning.force.com/lightning/r/Report/00ON400000IiQkPMAV/view"
            page.goto(report_url)
            page.wait_for_timeout(5000)
            
            # 3. PROCURAR BOTÃO DE EXPORTAR
            print("🔍 Procurando botão de exportar...")
            
            # Tenta encontrar por texto ou título
            try:
                # Clique no botão de engrenagem/seta
                page.click('button[title="Exportar"]')
            except:
                try:
                    # Alternativa: menu de ações
                    page.click('button[data-key="export"]')
                except:
                    print("⚠️ Botão não encontrado, tentando alternativa...")
                    page.click('button:has-text("Exportar")')
            
            page.wait_for_timeout(2000)
            
            # 4. ESCOLHER FORMATO
            print("📁 Selecionando formato Excel...")
            try:
                page.click('text="Exportar detalhes"')
            except:
                page.click('text="Detalhes"')
            page.wait_for_timeout(1000)
            
            # 5. INICIAR DOWNLOAD
            print("⬇️ Iniciando download...")
            
            # Configurar pasta de download
            download_path = r"C:\Users\dlucc\painel\downloads"
            if not os.path.exists(download_path):
                os.makedirs(download_path)
            
            # Escutar evento de download
            with page.expect_download() as download_info:
                page.click('button:text("Exportar")')
            
            download = download_info.value
            
            # Nome do arquivo com data
            data_atual = datetime.now().strftime("%Y%m%d_%H%M")
            caminho_final = rf"C:\Users\dlucc\painel\base_{data_atual}.xlsx"
            
            # Salvar arquivo
            download.save_as(caminho_final)
            print(f"✅ ARQUIVO BAIXADO: {caminho_final}")
            
            # 6. COPIAR PARA base.xlsx
            import shutil
            shutil.copy2(caminho_final, r"C:\Users\dlucc\painel\base.xlsx")
            print("✅ Arquivo copiado para base.xlsx")
            
            # 7. ATUALIZAR SUPABASE
            print("📤 Executando script de atualização...")
            subprocess.run(["python", "atualizar_dados.py"])
            
            # 8. FECHAR ABA (opcional)
            page.close()
            
            print("🎉 PROCESSO COMPLETO!")
            
        except Exception as e:
            print(f"❌ ERRO: {e}")
            page.screenshot(path="erro_salesforce.png")
            print("📸 Screenshot salvo como erro_salesforce.png")
        
        finally:
            # Não fechamos o browser, só a aba
            pass

if __name__ == "__main__":
    baixar_relatorio_salesforce()