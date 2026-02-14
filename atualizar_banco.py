import pandas as pd
import psycopg2
from datetime import datetime

EXCEL_PATH = r"C:\Users\dlucc\painel\base.xlsx"
DB_URL = "postgresql://postgres:#Lucasd15m10@db.bfamfgjjitrfcdyzuibd.supabase.co:5432/postgres"

def atualizar_incremental():
    print("🚀 ATUALIZAÇÃO INCREMENTAL")
    
    # Pegar última data no banco
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("SELECT MAX(inicio_execucao) FROM ordens_servico")
    ultima_data = cur.fetchone()[0]
    
    # Ler Excel
    df = pd.read_excel(EXCEL_PATH, header=11)
    df_filtrado = df[df['Estado'].isin(['Concluído com sucesso', 'Concluído sem sucesso'])]
    
    # Converter datas
    df_filtrado['DATA_CONVERTIDA'] = pd.to_datetime(
        df_filtrado['Início Execução'], 
        format='%d/%m/%Y %H:%M', 
        errors='coerce'
    )
    
    # Filtrar apenas registros novos
    if ultima_data:
        df_novos = df_filtrado[df_filtrado['DATA_CONVERTIDA'] > ultima_data]
    else:
        df_novos = df_filtrado
    
    print(f"📊 Registros novos: {len(df_novos)}")
    
    # Inserir apenas os novos
    for _, row in df_novos.iterrows():
        cur.execute("""
            INSERT INTO ordens_servico 
            (inicio_execucao, tecnico_atribuido, numero_sa, estado)
            VALUES (%s, %s, %s, %s)
        """, (
            row['DATA_CONVERTIDA'],
            str(row['Técnico Atribuído'])[:255],
            str(row['Número SA'])[:100],
            str(row['Estado'])[:100]
        ))
    
    conn.commit()
    print("✅ Atualização concluída!")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    atualizar_incremental()