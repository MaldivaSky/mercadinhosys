"""
Script para criar a tabela historico_precos no banco de dados
"""
import sys
sys.path.insert(0, '.')

from app import create_app
from app.models import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    # Criar a tabela historico_precos
    print("Criando tabela historico_precos...")
    
    with db.engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS historico_precos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                estabelecimento_id INTEGER NOT NULL,
                produto_id INTEGER NOT NULL,
                funcionario_id INTEGER NOT NULL,
                preco_custo_anterior NUMERIC(10, 2) NOT NULL,
                preco_venda_anterior NUMERIC(10, 2) NOT NULL,
                margem_anterior NUMERIC(5, 2) NOT NULL,
                preco_custo_novo NUMERIC(10, 2) NOT NULL,
                preco_venda_novo NUMERIC(10, 2) NOT NULL,
                margem_nova NUMERIC(5, 2) NOT NULL,
                motivo VARCHAR(100) NOT NULL,
                observacoes TEXT,
                data_alteracao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (estabelecimento_id) REFERENCES estabelecimentos(id) ON DELETE CASCADE,
                FOREIGN KEY (produto_id) REFERENCES produtos(id) ON DELETE CASCADE,
                FOREIGN KEY (funcionario_id) REFERENCES funcionarios(id)
            )
        """))
        
        # Criar índices
        print("Criando índices...")
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_historico_produto ON historico_precos(produto_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_historico_data ON historico_precos(data_alteracao)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_historico_estabelecimento ON historico_precos(estabelecimento_id)"))
        
        conn.commit()
    
    print("✓ Tabela historico_precos criada com sucesso!")
    
    # Verificar se a tabela foi criada
    with db.engine.connect() as conn:
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='historico_precos'"))
        if result.fetchone():
            print("✓ Tabela verificada no banco de dados")
        else:
            print("✗ Erro: Tabela não foi criada")
