import pandas as pd
import psycopg2
from datetime import datetime, date

DB_URL = "postgresql://postgres:#Lucasd15m10@db.bfamfgjjitrfcdyzuibd.supabase.co:5432/postgres"
EXCEL_PATH = r"C:\Users\dlucc\painel\base.xlsx"

def atualizar_dados_novos():
    print(f"📅 Atualizando dados - {date.today()}")
    
    # Conectar ao banco
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    
    # Pegar última data no banco
    cur.execute("SELECT MAX(inicio_execucao) FROM ordens_servico")
    ultima_data = cur.fetchone()[0]
    
    # Ler Excel
    df = pd.read_excel(EXCEL_PATH, header=11)
    df_filtrado = df[df['Estado'].isin(['Concluído com sucesso', 'Concluído sem sucesso'])]
    
    # Converter datas
    df_filtrado['data_convertida'] = pd.to_datetime(
        df_filtrado['Início Execução'], 
        format='%d/%m/%Y %H:%M',
        errors='coerce'
    )
    
    # Filtrar apenas dados mais recentes que a última data no banco
    if ultima_data:
        df_novos = df_filtrado[df_filtrado['data_convertida'] > ultima_data]
    else:
        df_novos = df_filtrado
    
    print(f"📊 Registros novos encontrados: {len(df_novos)}")
    
    if len(df_novos) == 0:
        print("✅ Nenhum dado novo para inserir")
        return
    
    # Inserir dados novos
    for _, row in df_novos.iterrows():
        cur.execute("""
            INSERT INTO ordens_servico 
            (inicio_execucao, tecnico_atribuido, numero_sa, estado)
            VALUES (%s, %s, %s, %s)
        """, (
            row['data_convertida'],
            str(row['Técnico Atribuído'])[:255],
            str(row['Número SA'])[:100],
            str(row['Estado'])[:100]
        ))
    
    conn.commit()
    print(f"✅ {len(df_novos)} novos registros inseridos!")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    atualizar_dados_novos()
    input("\nPressione Enter para fechar...")