import pandas as pd
import psycopg2
from psycopg2 import sql
import os
from urllib.parse import quote_plus

# =========================================================
# CONFIGURAÇÕES
# =========================================================

# Caminho da planilha Presença
EXCEL_PATH = r"C:\Users\dlucc\painel\Presença.xlsx"

# String de conexão com o Supabase (a mesma do outro script)
DB_URL = "postgresql://postgres:#Lucasd15m10@db.bfamfgjjitrfcdyzuibd.supabase.co:5432/postgres"

# =========================================================
# FUNÇÃO PARA CRIAR TABELAS
# =========================================================

def criar_tabelas(conn, cur):
    """Cria as tabelas necessárias para supervisores e presença"""
    
    print("\n📦 Criando tabelas...")
    
    # Tabela de técnicos (com supervisores)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS tecnicos (
        id SERIAL PRIMARY KEY,
        tr VARCHAR(20) UNIQUE,
        tt VARCHAR(20),
        funcionario TEXT,
        funcao TEXT,
        operadora TEXT,
        supervisor TEXT,
        setor_origem TEXT,
        setor_atual TEXT,
        status TEXT,
        coordenador TEXT,
        cp TEXT,
        faz_os_2 TEXT,
        created_at TIMESTAMP DEFAULT NOW()
    );
    """)
    
    # Tabela de presença diária
    cur.execute("""
    CREATE TABLE IF NOT EXISTS presenca (
        id SERIAL PRIMARY KEY,
        tecnico_id INTEGER REFERENCES tecnicos(id),
        data DATE,
        status TEXT,
        observacao TEXT,
        created_at TIMESTAMP DEFAULT NOW(),
        UNIQUE(tecnico_id, data)
    );
    """)
    
    # Índices para consultas rápidas
    cur.execute("CREATE INDEX IF NOT EXISTS idx_tecnicos_tr ON tecnicos(tr);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_tecnicos_supervisor ON tecnicos(supervisor);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_presenca_data ON presenca(data);")
    
    conn.commit()
    print("✅ Tabelas criadas/verificadas!")

# =========================================================
# FUNÇÃO PARA MIGRAR DADOS DOS TÉCNICOS
# =========================================================

def migrar_tecnicos(conn, cur, df_tecnicos):
    """Migra os dados da aba Técnicos"""
    
    print("\n👥 Migrando dados dos técnicos...")
    
    # Verificar colunas disponíveis
    print(f"\n📋 Colunas encontradas na aba Técnicos:")
    for i, col in enumerate(df_tecnicos.columns):
        print(f"   {i}: {col}")
    
    # Mapeamento de colunas (ajuste conforme sua planilha)
    # Baseado na imagem que você mostrou, as colunas são:
    col_map = {
        'TR': None,
        'TT': None,
        'FUNCIONÁRIO': None,
        'FUNÇÃO': None,
        'OPERADORA': None,
        'SUPERVISOR': None,
        'SETOR ORIGEM': None,
        'SETOR ATUAL': None,
        'Status': None,
        'COORDENADOR': None,
        'CP': None,
        'Faz os 2?': None
    }
    
    # Mapear colunas reais
    for col in df_tecnicos.columns:
        col_upper = str(col).upper().strip()
        if 'TR' in col_upper and not 'TT' in col_upper:
            col_map['TR'] = col
        elif 'TT' in col_upper:
            col_map['TT'] = col
        elif 'FUNCIONÁRIO' in col_upper or 'NOME' in col_upper:
            col_map['FUNCIONÁRIO'] = col
        elif 'FUNÇÃO' in col_upper:
            col_map['FUNÇÃO'] = col
        elif 'OPERADORA' in col_upper:
            col_map['OPERADORA'] = col
        elif 'SUPERVISOR' in col_upper:
            col_map['SUPERVISOR'] = col
        elif 'SETOR ORIGEM' in col_upper:
            col_map['SETOR ORIGEM'] = col
        elif 'SETOR ATUAL' in col_upper:
            col_map['SETOR ATUAL'] = col
        elif 'STATUS' in col_upper:
            col_map['Status'] = col
        elif 'COORDENADOR' in col_upper:
            col_map['COORDENADOR'] = col
        elif 'CP' in col_upper:
            col_map['CP'] = col
        elif 'FAZ OS 2' in col_upper or 'FAZ OS 2?' in col_upper:
            col_map['Faz os 2?'] = col
    
    print("\n📊 Mapeamento de colunas:")
    for campo, coluna in col_map.items():
        if coluna:
            print(f"   ✅ {campo} -> {coluna}")
        else:
            print(f"   ⚠️ {campo} -> NÃO ENCONTRADO")
    
    # Limpar tabela existente
    cur.execute("TRUNCATE TABLE tecnicos CASCADE;")
    
    # Inserir dados
    inseridos = 0
    for _, row in df_tecnicos.iterrows():
        try:
            # Extrair valores com tratamento de nulos
            tr = str(row[col_map['TR']]).strip() if col_map['TR'] and pd.notna(row[col_map['TR']]) else ''
            tt = str(row[col_map['TT']]).strip() if col_map['TT'] and pd.notna(row[col_map['TT']]) else ''
            funcionario = str(row[col_map['FUNCIONÁRIO']]) if col_map['FUNCIONÁRIO'] and pd.notna(row[col_map['FUNCIONÁRIO']]) else ''
            funcao = str(row[col_map['FUNÇÃO']]) if col_map['FUNÇÃO'] and pd.notna(row[col_map['FUNÇÃO']]) else ''
            operadora = str(row[col_map['OPERADORA']]) if col_map['OPERADORA'] and pd.notna(row[col_map['OPERADORA']]) else ''
            supervisor = str(row[col_map['SUPERVISOR']]) if col_map['SUPERVISOR'] and pd.notna(row[col_map['SUPERVISOR']]) else 'Não alocado'
            setor_origem = str(row[col_map['SETOR ORIGEM']]) if col_map['SETOR ORIGEM'] and pd.notna(row[col_map['SETOR ORIGEM']]) else ''
            setor_atual = str(row[col_map['SETOR ATUAL']]) if col_map['SETOR ATUAL'] and pd.notna(row[col_map['SETOR ATUAL']]) else ''
            status = str(row[col_map['Status']]) if col_map['Status'] and pd.notna(row[col_map['Status']]) else 'Ativo'
            coordenador = str(row[col_map['COORDENADOR']]) if col_map['COORDENADOR'] and pd.notna(row[col_map['COORDENADOR']]) else ''
            cp = str(row[col_map['CP']]) if col_map['CP'] and pd.notna(row[col_map['CP']]) else ''
            faz_os_2 = str(row[col_map['Faz os 2?']]) if col_map['Faz os 2?'] and pd.notna(row[col_map['Faz os 2?']]) else ''
            
            # Inserir no banco
            cur.execute("""
                INSERT INTO tecnicos 
                (tr, tt, funcionario, funcao, operadora, supervisor, setor_origem, setor_atual, status, coordenador, cp, faz_os_2)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (tr) DO UPDATE SET
                    supervisor = EXCLUDED.supervisor,
                    status = EXCLUDED.status,
                    setor_atual = EXCLUDED.setor_atual
            """, (tr, tt, funcionario, funcao, operadora, supervisor, setor_origem, setor_atual, 
                  status, coordenador, cp, faz_os_2))
            
            inseridos += 1
            
        except Exception as e:
            print(f"   ⚠️ Erro ao inserir técnico: {e}")
    
    conn.commit()
    print(f"✅ {inseridos} técnicos migrados!")

# =========================================================
# FUNÇÃO PARA MIGRAR DADOS DE PRESENÇA
# =========================================================

def migrar_presenca(conn, cur, df_presenca):
    """Migra os dados da aba Presença"""
    
    print("\n📅 Migrando dados de presença...")
    
    # Esta parte é mais complexa porque a planilha de presença tem formato especial
    # Vamos pular por enquanto e focar nos supervisores
    print("⚠️ Migração de presença diária será implementada depois")
    
    # Placeholder para futura implementação
    pass

# =========================================================
# FUNÇÃO PRINCIPAL
# =========================================================

def migrar_tudo():
    print("="*60)
    print("🚀 MIGRAÇÃO DA PLANILHA PRESENÇA PARA SUPABASE")
    print("="*60)
    
    try:
        # 1. Ler a planilha Excel
        print("\n📖 Lendo arquivo Presença.xlsx...")
        xl = pd.ExcelFile(EXCEL_PATH)
        
        # Listar abas disponíveis
        print(f"\n📋 Abas encontradas: {xl.sheet_names}")
        
        # Carregar aba de Técnicos
        if 'Técnicos' in xl.sheet_names:
            df_tecnicos = pd.read_excel(EXCEL_PATH, sheet_name='Técnicos')
            print(f"✅ Aba 'Técnicos' carregada: {len(df_tecnicos)} linhas")
        else:
            # Tentar encontrar aba similar
            for sheet in xl.sheet_names:
                if 'tecnico' in sheet.lower():
                    df_tecnicos = pd.read_excel(EXCEL_PATH, sheet_name=sheet)
                    print(f"✅ Aba '{sheet}' carregada: {len(df_tecnicos)} linhas")
                    break
            else:
                df_tecnicos = None
                print("❌ Aba de técnicos não encontrada!")
        
        # Carregar aba de Presença
        if 'Presença' in xl.sheet_names:
            df_presenca = pd.read_excel(EXCEL_PATH, sheet_name='Presença')
            print(f"✅ Aba 'Presença' carregada: {len(df_presenca)} linhas")
        else:
            df_presenca = None
            print("⚠️ Aba de presença não encontrada (opcional)")
        
        # 2. Conectar ao Supabase
        print("\n🔌 Conectando ao Supabase...")
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        print("✅ Conectado!")
        
        # 3. Criar tabelas
        criar_tabelas(conn, cur)
        
        # 4. Migrar técnicos
        if df_tecnicos is not None:
            migrar_tecnicos(conn, cur, df_tecnicos)
        
        # 5. Migrar presença
        if df_presenca is not None:
            migrar_presenca(conn, cur, df_presenca)
        
        # 6. Verificar resultados
        cur.execute("SELECT COUNT(*) FROM tecnicos")
        total_tecnicos = cur.fetchone()[0]
        print(f"\n📊 Total de técnicos no banco: {total_tecnicos}")
        
        # Listar supervisores únicos
        cur.execute("SELECT DISTINCT supervisor FROM tecnicos ORDER BY supervisor")
        supervisores = cur.fetchall()
        print(f"\n👥 Supervisores encontrados ({len(supervisores)}):")
        for sup in supervisores[:10]:  # Mostrar apenas os 10 primeiros
            print(f"   • {sup[0]}")
        if len(supervisores) > 10:
            print(f"   ... e mais {len(supervisores) - 10}")
        
        cur.close()
        conn.close()
        print("\n🔒 Conexão fechada.")
        print("\n🎉 Migração concluída com sucesso!")
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    migrar_tudo()