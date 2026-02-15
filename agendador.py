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
        subprocess.run(["python", "bot_salesforce_final.py"], check=True)
        
        # Depois atualizar dados
        subprocess.run(["python", "atualizar_dados.py"], check=True)
        
        print(f"✅ Ciclo completo executado!")
        
    except Exception as e:
        print(f"❌ Erro: {e}")

# Agendar
schedule.every(1).hours.do(executar_robo)

print(f"🕐 AGENDADOR INICIADO")
print(f"📁 Monitorando: {BASE_PATH}")
print(f"⏰ Rodará a cada 1 hora")
print("="*60)

while True:
    schedule.run_pending()
    time.sleep(60)