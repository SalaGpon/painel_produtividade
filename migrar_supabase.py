import pandas as pd
import psycopg2
from psycopg2 import sql
import os
from urllib.parse import quote_plus
import time
from datetime import datetime

# =========================================================
# CONFIGURAÇÕES
# =========================================================

# Caminho do seu Excel
EXCEL_PATH = r"C:\Users\dlucc\painel\base.xlsx"
HEADER_ROW = 11  # Seus dados começam na linha 12

# NOVA SENHA
SENHA = "#Lucasd15m10"

# Codificar a senha para URL
SENHA_CODIFICADA = quote_plus(SENHA)

# STRING DE CONEXÃO
DB_URL = f"postgresql://postgres:{SENHA_CODIFICADA}@db.bfamfgjjitrfcdyzuibd.supabase.co:5432/postgres"

# =========================================================
# FUNÇÃO PARA CONVERTER DATA
# =========================================================

def converter_data(data_str):
    """Converte data do formato brasileiro (dd/mm/aaaa HH:MM) para ISO (aaaa-mm-dd HH:MM:SS)"""
    if pd.isna(data_str) or data_str is None:
        return None
    
    try:
        # Se já for datetime, converte direto
        if isinstance(data_str, datetime):
            return data_str
        
        # Se for string, tenta converter
        data_str = str(data_str).strip()
        
        # Tenta diferentes formatos
        formatos = [
            '%d/%m/%Y %H:%M',     # 16/12/2025 08:50
            '%d/%m/%Y %H:%M:%S',  # 16/12/2025 08:50:00
            '%Y-%m-%d %H:%M:%S',  # 2025-12-16 08:50:00 (ISO)
            '%Y-%m-%d %H:%M',     # 2025-12-16 08:50
        ]
        
        for fmt in formatos:
            try:
                data_obj = datetime.strptime(data_str, fmt)
                return data_obj.strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                continue
        
        # Se não conseguir converter, retorna None
        print(f"   ⚠️ Formato de data não reconhecido: {data_str}")
        return None
        
    except Exception as e:
        print(f"   ⚠️ Erro ao converter data '{data_str}': {e}")
        return None

# =========================================================
# FUNÇÃO PRINCIPAL
# =========================================================

def migrar_dados():
    print("="*50)
    print("🚀 INICIANDO MIGRAÇÃO PARA SUPABASE")
    print("="*50)
    
    conn = None
    cur = None
    
    try:
        # 1. Ler Excel
        print("\n📖 Lendo arquivo Excel...")
        df = pd.read_excel(EXCEL_PATH, header=HEADER_ROW)
        print(f"✅ Total de linhas no Excel: {len(df)}")
        
        # 2. Filtrar apenas status válidos
        print("\n🔍 Filtrando status válidos...")
        df_filtrado = df[df['Estado'].isin(['Concluído com sucesso', 'Concluído sem sucesso'])]
        print(f"✅ Linhas após filtro: {len(df_filtrado)}")
        
        if len(df_filtrado) == 0:
            print("❌ Nenhum dado válido encontrado!")
            return
        
        # 3. Conectar ao Supabase
        print("\n🔌 Conectando ao Supabase...")
        conn = psycopg2.connect(DB_URL)
        conn.set_session(autocommit=False)
        cur = conn.cursor()
        print("✅ Conectado!")
        
        # 4. Limpar tabela
        print("\n🧹 Limpando tabela existente...")
        try:
            cur.execute("TRUNCATE TABLE ordens_servico;")
            conn.commit()
            print("✅ Tabela limpa!")
        except Exception as e:
            conn.rollback()
            print(f"⚠️ Erro ao limpar tabela: {e}")
        
        # 5. Inserir dados em lote
        print("\n📤 Inserindo dados no Supabase...")
        batch_size = 100
        total = len(df_filtrado)
        inseridos = 0
        erros = 0
        erros_data = 0
        
        for i in range(0, total, batch_size):
            batch = df_filtrado.iloc[i:i+batch_size]
            batch_inseridos = 0
            
            for idx, (_, row) in enumerate(batch.iterrows()):
                try:
                    # CONVERTER A DATA para formato ISO
                    data_original = row['Início Execução']
                    data_convertida = converter_data(data_original)
                    
                    if data_convertida is None:
                        erros_data += 1
                        continue
                    
                    tecnico = str(row['Técnico Atribuído'])[:255] if pd.notna(row['Técnico Atribuído']) else ''
                    sa = str(row['Número SA'])[:100] if pd.notna(row['Número SA']) else ''
                    estado = str(row['Estado'])[:100] if pd.notna(row['Estado']) else ''
                    
                    cur.execute("""
                        INSERT INTO ordens_servico 
                        (inicio_execucao, tecnico_atribuido, numero_sa, estado)
                        VALUES (%s, %s, %s, %s)
                    """, (data_convertida, tecnico, sa, estado))
                    
                    batch_inseridos += 1
                    
                except Exception as e:
                    erros += 1
                    print(f"   ⚠️ Erro na linha {i+idx+1}: {e}")
                    conn.rollback()
                    continue
            
            # Commit do batch
            try:
                conn.commit()
                inseridos += batch_inseridos
                print(f"   ✅ {min(i+batch_size, total)}/{total} registros processados ({batch_inseridos} inseridos)")
            except Exception as e:
                print(f"   ❌ Erro no commit do lote: {e}")
                conn.rollback()
            
            time.sleep(0.5)
        
        print(f"\n📊 Resumo final:")
        print(f"   ✅ Inseridos: {inseridos}")
        print(f"   ⚠️ Erros gerais: {erros}")
        print(f"   📅 Erros de data: {erros_data}")
        print(f"   📁 Total processado: {total}")
        
        # 6. Verificar total no banco
        cur.execute("SELECT COUNT(*) FROM ordens_servico")
        count = cur.fetchone()[0]
        print(f"\n📊 Total no banco após migração: {count} registros")
        
        # Mostrar alguns exemplos
        cur.execute("SELECT * FROM ordens_servico LIMIT 5")
        amostra = cur.fetchall()
        print("\n📋 Amostra dos dados inseridos:")
        for row in amostra:
            print(f"   {row}")
        
    except Exception as e:
        print(f"\n❌ ERRO GERAL: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
            print("\n🔒 Conexão fechada.")

if __name__ == "__main__":
    migrar_dados()