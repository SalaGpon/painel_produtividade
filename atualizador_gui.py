import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import psycopg2
from datetime import datetime
import threading

class AtualizadorBanco:
    def __init__(self, root):
        self.root = root
        self.root.title("Atualizador do Painel de Produtividade")
        self.root.geometry("500x300")
        
        # Frame principal
        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        ttk.Label(main_frame, text="📊 Atualizador de Banco de Dados", 
                 font=('Arial', 14, 'bold')).pack(pady=10)
        
        # Informações do arquivo
        self.file_label = ttk.Label(main_frame, text="Arquivo: base.xlsx")
        self.file_label.pack(pady=5)
        
        # Status
        self.status_label = ttk.Label(main_frame, text="Pronto para atualizar", 
                                      foreground="blue")
        self.status_label.pack(pady=10)
        
        # Barra de progresso
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=10)
        
        # Botões
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="🔍 Verificar Alterações", 
                  command=self.verificar).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="🚀 Atualizar Agora", 
                  command=self.atualizar).pack(side=tk.LEFT, padx=5)
        
        # Última atualização
        self.last_update_label = ttk.Label(main_frame, text="Última atualização: nunca")
        self.last_update_label.pack(pady=5)
        
    def verificar(self):
        self.status_label.config(text="Verificando...", foreground="orange")
        self.progress.start()
        
        def check():
            try:
                # Verificar se arquivo existe
                import os
                if os.path.exists(r"C:\Users\dlucc\painel\base.xlsx"):
                    self.root.after(0, lambda: self.status_label.config(
                        text="✅ Arquivo encontrado", foreground="green"))
                else:
                    self.root.after(0, lambda: self.status_label.config(
                        text="❌ Arquivo não encontrado", foreground="red"))
            finally:
                self.root.after(0, self.progress.stop)
        
        threading.Thread(target=check).start()
    
    def atualizar(self):
        self.status_label.config(text="Atualizando...", foreground="orange")
        self.progress.start()
        
        def update():
            try:
                # Conectar ao banco
                conn = psycopg2.connect(
                    "postgresql://postgres:#Lucasd15m10@db.bfamfgjjitrfcdyzuibd.supabase.co:5432/postgres"
                )
                cur = conn.cursor()
                
                # Ler Excel
                df = pd.read_excel(r"C:\Users\dlucc\painel\base.xlsx", header=11)
                df_filtrado = df[df['Estado'].isin(['Concluído com sucesso', 'Concluído sem sucesso'])]
                
                # Limpar e inserir
                cur.execute("TRUNCATE TABLE ordens_servico;")
                
                for _, row in df_filtrado.iterrows():
                    data = row['Início Execução']
                    if pd.notna(data) and isinstance(data, str):
                        try:
                            data = datetime.strptime(data, '%d/%m/%Y %H:%M')
                        except:
                            pass
                    
                    cur.execute("""
                        INSERT INTO ordens_servico 
                        (inicio_execucao, tecnico_atribuido, numero_sa, estado)
                        VALUES (%s, %s, %s, %s)
                    """, (data, row['Técnico Atribuído'], row['Número SA'], row['Estado']))
                
                conn.commit()
                cur.close()
                conn.close()
                
                self.root.after(0, lambda: self.status_label.config(
                    text=f"✅ Atualizado! {len(df_filtrado)} registros", foreground="green"))
                self.root.after(0, lambda: self.last_update_label.config(
                    text=f"Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M')}"))
                
            except Exception as e:
                self.root.after(0, lambda: self.status_label.config(
                    text=f"❌ Erro: {str(e)[:50]}...", foreground="red"))
            finally:
                self.root.after(0, self.progress.stop)
        
        threading.Thread(target=update).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = AtualizadorBanco(root)
    root.mainloop()