# agendador.py
import schedule
import time
import subprocess
from datetime import datetime
import os
from config import BASE_PATH

def executar_robo():
    """Executa o robô e registra no log"""
    print(f"\n{'='*60}")
    print(f"🤖 Executando robô - {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"📁 Pasta: {BASE_PATH}")
    print('='*60)
    
    # Mudar para a pasta correta
    os.chdir(BASE_PATH)
    
    try:
        # Executar o robô
        print("⏳ Baixando relatório do Salesforce...")
        subprocess.run(["python", "bot_salesforce_final.py"], check=True)
        
        # Depois atualizar dados
        print("⏳ Atualizando banco de dados...")
        subprocess.run(["python", "atualizar_dados.py"], check=True)
        
        print(f"✅ Ciclo completo executado com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro na execução: {e}")
        
        # Registrar erro em arquivo de log
        with open("erros_robo.txt", "a") as f:
            f.write(f"{datetime.now()} - ERRO: {e}\n")

# Agendar a cada 30 MINUTOS
schedule.every(30).minutes.do(executar_robo)

# Executar imediatamente ao iniciar
executar_robo()

print(f"🕐 AGENDADOR INICIADO")
print(f"📁 Monitorando: {BASE_PATH}")
print(f"⏰ Rodará a cada 30 MINUTOS")
print("="*60)
print("Pressione Ctrl+C para parar")
print("="*60)

while True:
    schedule.run_pending()
    time.sleep(60)