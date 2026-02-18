"""
Script para aplicar índices de performance no banco de dados PostgreSQL.
Foco: Melhorar tempo de resposta do dashboard e listagens.
"""

import os
import sys
from sqlalchemy import text

# Adiciona o diretório 'backend' ao sys.path para que 'app' seja importável
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db

def apply_indexes():
    app = create_app()
    with app.app_context():
        print("🚀 Iniciando aplicação de índices de performance...")
        
        # Lista de índices a serem criados
        indexes = [
            # Vendas: Essencial para Dashboard e Relatórios
            "CREATE INDEX IF NOT EXISTS idx_vendas_perf ON vendas (estabelecimento_id, data_venda, status)",
            
            # Venda Itens: Essencial para cálculos financeiros (CMV, Lucro Bruto)
            "CREATE INDEX IF NOT EXISTS idx_venda_itens_perf ON venda_itens (venda_id, produto_id)",
            
            # Produtos: Melhora listagem e buscas
            "CREATE INDEX IF NOT EXISTS idx_produtos_perf ON produtos (estabelecimento_id, ativo, categoria_id)",
            "CREATE INDEX IF NOT EXISTS idx_produtos_busca ON produtos (estabelecimento_id, nome, codigo_barras)",
            
            # Lotes: Melhora monitor de validade
            "CREATE INDEX IF NOT EXISTS idx_lotes_validade ON produto_lotes (estabelecimento_id, data_validade, ativo, quantidade)",
            
            # Despesas: Melhora dashboard financeiro
            "CREATE INDEX IF NOT EXISTS idx_despesas_perf ON despesas (estabelecimento_id, data_despesa, tipo)",
            
            # Ponto: Melhora dashboard RH
            "CREATE INDEX IF NOT EXISTS idx_ponto_perf ON registro_ponto (estabelecimento_id, data, tipo_registro, funcionario_id)"
        ]
        
        for sql in indexes:
            try:
                print(f"Executing: {sql}")
                db.session.execute(text(sql))
                db.session.commit()
                print("✅ Sucesso!")
            except Exception as e:
                db.session.rollback()
                print(f"❌ Erro ao aplicar índice: {e}")
        
        print("\n✨ Aplicação de índices concluída.")

if __name__ == "__main__":
    apply_indexes()
