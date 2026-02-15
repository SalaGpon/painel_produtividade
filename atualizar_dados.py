# atualizar_dados.py
import pandas as pd
import psycopg2
from datetime import datetime
import os
from config import BASE_PATH, EXCEL_PATH

# String de conexão com o Supabase
DB_URL = "postgresql://postgres.bfamfgjjitrfcdyzuibd:#Lucasd15m10@aws-1-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require"

# Cabeçalho do Excel
HEADER_ROW = 11

def converter_data(data_str):
    """Converte data do formato brasileiro para datetime"""
    if pd.isna(data_str):
        return None
    try:
        if isinstance(data_str, datetime):
            return data_str
        return datetime.strptime(str(data_str), '%d/%m/%Y %H:%M')
    except:
        try:
            return datetime.strptime(str(data_str), '%Y-%m-%d %H:%M:%S')
        except:
            print(f"   ⚠️ Data inválida: {data_str}")
            return None

def atualizar_dados():
    print("="*60)
    print(f"🚀 ATUALIZADOR DE DADOS - PAINEL DE PRODUTIVIDADE")
    print(f"📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"📁 Pasta: {BASE_PATH}")
    print("="*60)
    
    try:
        # 1. Verificar arquivo Excel
        print("\n📁 Verificando arquivo Excel...")
        if not os.path.exists(EXCEL_PATH):
            print(f"❌ ERRO: Arquivo não encontrado em: {EXCEL_PATH}")
            return
        print(f"✅ Arquivo encontrado: {EXCEL_PATH}")
        
        # 2. Conectar ao Supabase
        print("\n🔌 Conectando ao Supabase...")
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        print("✅ Conectado!")
        
        # 3. Pegar última data no banco
        print("\n📊 Verificando última data no banco...")
        cur.execute("SELECT MAX(inicio_execucao) FROM ordens_servico")
        ultima_data = cur.fetchone()[0]
        if ultima_data:
            print(f"✅ Última data no banco: {ultima_data.strftime('%d/%m/%Y %H:%M')}")
        else:
            print("⚠️ Nenhum dado encontrado no banco")
        
        # 4. Ler Excel
        print("\n📖 Lendo arquivo Excel...")
        df = pd.read_excel(EXCEL_PATH, header=HEADER_ROW)
        print(f"✅ Total de linhas no Excel: {len(df)}")
        
        # 5. Filtrar status válidos
        print("\n🔍 Filtrando status válidos...")
        df_filtrado = df[df['Estado'].isin(['Concluído com sucesso', 'Concluído sem sucesso'])]
        print(f"✅ Linhas com status válidos: {len(df_filtrado)}")
        
        if len(df_filtrado) == 0:
            print("❌ Nenhum dado válido encontrado!")
            return
        
        # 6. Converter datas
        print("\n🔄 Convertendo datas...")
        df_filtrado.loc[:, 'data_convertida'] = df_filtrado['Início Execução'].apply(converter_data)
        df_filtrado = df_filtrado.dropna(subset=['data_convertida'])
        print(f"✅ Datas convertidas: {len(df_filtrado)} linhas")
        
        # 7. Filtrar dados novos
        print("\n📈 Verificando dados novos...")
        if ultima_data:
            if hasattr(ultima_data, 'tzinfo') and ultima_data.tzinfo is not None:
                ultima_data = ultima_data.replace(tzinfo=None)
            df_novos = df_filtrado[df_filtrado['data_convertida'] > ultima_data]
        else:
            df_novos = df_filtrado
        
        print(f"✅ Registros novos encontrados: {len(df_novos)}")
        
        if len(df_novos) == 0:
            print("\n✨ Banco já está atualizado! Nenhum dado novo para inserir.")
            return
        
        # 8. Inserir dados novos
        print(f"\n📤 Inserindo {len(df_novos)} novos registros...")
        inseridos = 0
        batch_size = 100
        
        for i in range(0, len(df_novos), batch_size):
            batch = df_novos.iloc[i:i+batch_size]
            for _, row in batch.iterrows():
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
                inseridos += 1
            conn.commit()
            print(f"   ✅ {min(i+batch_size, len(df_novos))}/{len(df_novos)}...")
        
        print(f"\n🎉 SUCESSO! {inseridos} novos registros inseridos!")
        
        # 9. Verificar total
        cur.execute("SELECT COUNT(*) FROM ordens_servico")
        total = cur.fetchone()[0]
        print(f"📊 Total no banco: {total}")
        
        cur.close()
        conn.close()
        print("\n🔒 Conexão fechada.")
        print("\n" + "="*60)
        print("✅ ATUALIZAÇÃO CONCLUÍDA!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n")
    input("Pressione Enter para fechar...")

if __name__ == "__main__":
    atualizar_dados()