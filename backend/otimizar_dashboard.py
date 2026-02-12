"""
Script para otimizar performance do dashboard científico
Identifica e corrige problemas de lentidão
"""

import os
import sys
import time
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Venda, VendaItem, Produto, Cliente, Despesa
from sqlalchemy import text, Index
from app.dashboard_cientifico.orchestration import DashboardOrchestrator
from app.models import Funcionario

def criar_indices():
    """Cria índices para otimizar queries do dashboard"""
    print("=" * 70)
    print("🔧 CRIANDO ÍNDICES PARA OTIMIZAÇÃO")
    print("=" * 70)
    
    indices_criados = 0
    
    try:
        # Índice composto para vendas (usado em quase todas as queries)
        try:
            idx_vendas = Index(
                'idx_vendas_dashboard',
                Venda.estabelecimento_id,
                Venda.data_venda,
                Venda.status
            )
            idx_vendas.create(db.engine, checkfirst=True)
            print("✅ Índice idx_vendas_dashboard criado")
            indices_criados += 1
        except Exception as e:
            print(f"⚠️ Índice idx_vendas_dashboard já existe ou erro: {e}")
        
        # Índice para venda_itens (join com vendas)
        try:
            idx_venda_items = Index(
                'idx_venda_items_dashboard',
                VendaItem.venda_id,
                VendaItem.produto_id
            )
            idx_venda_items.create(db.engine, checkfirst=True)
            print("✅ Índice idx_venda_items_dashboard criado")
            indices_criados += 1
        except Exception as e:
            print(f"⚠️ Índice idx_venda_items_dashboard já existe ou erro: {e}")
        
        # Índice para produtos
        try:
            idx_produtos = Index(
                'idx_produtos_dashboard',
                Produto.estabelecimento_id,
                Produto.ativo
            )
            idx_produtos.create(db.engine, checkfirst=True)
            print("✅ Índice idx_produtos_dashboard criado")
            indices_criados += 1
        except Exception as e:
            print(f"⚠️ Índice idx_produtos_dashboard já existe ou erro: {e}")
        
        # Índice para despesas
        try:
            idx_despesas = Index(
                'idx_despesas_dashboard',
                Despesa.estabelecimento_id,
                Despesa.data_despesa
            )
            idx_despesas.create(db.engine, checkfirst=True)
            print("✅ Índice idx_despesas_dashboard criado")
            indices_criados += 1
        except Exception as e:
            print(f"⚠️ Índice idx_despesas_dashboard já existe ou erro: {e}")
        
        db.session.commit()
        print(f"\n✅ Total de índices criados/verificados: {indices_criados}")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro ao criar índices: {e}")
        import traceback
        traceback.print_exc()

def testar_performance():
    """Testa performance do dashboard"""
    print("\n" + "=" * 70)
    print("⚡ TESTE DE PERFORMANCE")
    print("=" * 70)
    
    app = create_app()
    
    with app.app_context():
        admin = Funcionario.query.filter_by(username="admin").first()
        if not admin:
            print("❌ Admin não encontrado!")
            return
        
        estabelecimento_id = admin.estabelecimento_id
        print(f"📊 Testando dashboard para estabelecimento ID: {estabelecimento_id}")
        
        orchestrator = DashboardOrchestrator(estabelecimento_id)
        
        # Primeira chamada (sem cache)
        print("\n🔥 Primeira chamada (sem cache)...")
        start = time.time()
        try:
            result = orchestrator.get_scientific_dashboard(days=30)
            elapsed = time.time() - start
            print(f"⏱️ Tempo: {elapsed:.2f}s")
            print(f"✅ Sucesso: {result.get('success', True)}")
        except Exception as e:
            elapsed = time.time() - start
            print(f"❌ Erro após {elapsed:.2f}s: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # Segunda chamada (com cache)
        print("\n🔥 Segunda chamada (com cache)...")
        start = time.time()
        try:
            result = orchestrator.get_scientific_dashboard(days=30)
            elapsed = time.time() - start
            print(f"⏱️ Tempo: {elapsed:.2f}s")
            print(f"✅ Sucesso: {result.get('success', True)}")
            if elapsed < 0.1:
                print("✅ Cache funcionando perfeitamente!")
        except Exception as e:
            elapsed = time.time() - start
            print(f"❌ Erro após {elapsed:.2f}s: {e}")

def analisar_queries():
    """Analisa queries lentas"""
    print("\n" + "=" * 70)
    print("🔍 ANÁLISE DE QUERIES")
    print("=" * 70)
    
    app = create_app()
    
    with app.app_context():
        # Contar registros
        total_vendas = db.session.query(Venda).count()
        total_items = db.session.query(VendaItem).count()
        total_produtos = db.session.query(Produto).count()
        
        print(f"📊 Estatísticas do banco:")
        print(f"   Vendas: {total_vendas:,}")
        print(f"   Itens de Venda: {total_items:,}")
        print(f"   Produtos: {total_produtos:,}")
        
        # Verificar índices existentes
        print("\n📋 Verificando índices...")
        try:
            if db.engine.name == 'postgresql':
                result = db.session.execute(text("""
                    SELECT indexname, indexdef 
                    FROM pg_indexes 
                    WHERE tablename IN ('vendas', 'venda_itens', 'produtos', 'despesas')
                    ORDER BY tablename, indexname
                """))
                indices = result.fetchall()
                if indices:
                    print(f"   Encontrados {len(indices)} índices:")
                    for idx_name, idx_def in indices:
                        print(f"   - {idx_name}")
                else:
                    print("   ⚠️ Nenhum índice encontrado!")
            elif db.engine.name == 'sqlite':
                result = db.session.execute(text("""
                    SELECT name, sql 
                    FROM sqlite_master 
                    WHERE type='index' 
                    AND tbl_name IN ('vendas', 'venda_itens', 'produtos', 'despesas')
                """))
                indices = result.fetchall()
                if indices:
                    print(f"   Encontrados {len(indices)} índices:")
                    for idx_name, idx_sql in indices:
                        if idx_name and not idx_name.startswith('sqlite_'):
                            print(f"   - {idx_name}")
                else:
                    print("   ⚠️ Nenhum índice encontrado!")
        except Exception as e:
            print(f"   ⚠️ Erro ao verificar índices: {e}")

def main():
    print("=" * 70)
    print("🚀 OTIMIZADOR DE PERFORMANCE DO DASHBOARD")
    print("=" * 70)
    
    app = create_app()
    
    with app.app_context():
        # 1. Analisar queries
        analisar_queries()
        
        # 2. Criar índices
        criar_indices()
        
        # 3. Testar performance
        testar_performance()
        
        print("\n" + "=" * 70)
        print("✅ OTIMIZAÇÃO CONCLUÍDA")
        print("=" * 70)

if __name__ == "__main__":
    main()
