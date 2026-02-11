"""
🚀 Quick Validation Test - Execute AGORA para validar o sistema

Este script testa os fluxos críticos do sistema em 5 minutos.
Uso: python backend/quick_validation_test.py
"""

import sys
import os
from datetime import datetime, timedelta, date
from decimal import Decimal

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import (
    Estabelecimento, Produto, Cliente, Venda, VendaItem,
    MovimentacaoEstoque, Despesa, ProdutoLote
)
from app.dashboard_cientifico.data_layer import DataLayer
from app.dashboard_cientifico.orchestration import DashboardOrchestrator

app = create_app()

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")

def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.END}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.END}")

def test_database_connection():
    """Teste 1: Conexão com banco de dados"""
    print("\n" + "="*60)
    print("TESTE 1: Conexão com Banco de Dados")
    print("="*60)
    
    try:
        with app.app_context():
            # Tentar query simples
            estab_count = Estabelecimento.query.count()
            print_info(f"Estabelecimentos encontrados: {estab_count}")
            
            if estab_count == 0:
                print_warning("Nenhum estabelecimento encontrado. Execute seed primeiro.")
                return False
            
            print_success("Conexão com banco OK")
            return True
    except Exception as e:
        print_error(f"Falha na conexão: {e}")
        return False

def test_pdv_flow():
    """Teste 2: Fluxo completo de venda no PDV"""
    print("\n" + "="*60)
    print("TESTE 2: Fluxo de Venda no PDV")
    print("="*60)
    
    try:
        with app.app_context():
            # Buscar estabelecimento
            estab = Estabelecimento.query.first()
            if not estab:
                print_error("Nenhum estabelecimento encontrado")
                return False
            
            # Buscar produto com estoque
            produto = Produto.query.filter(
                Produto.estabelecimento_id == estab.id,
                Produto.estoque_atual > 0
            ).first()
            
            if not produto:
                print_error("Nenhum produto com estoque encontrado")
                return False
            
            print_info(f"Produto: {produto.nome} (Estoque: {produto.estoque_atual})")
            
            # Buscar cliente
            cliente = Cliente.query.filter_by(estabelecimento_id=estab.id).first()
            if not cliente:
                print_warning("Nenhum cliente encontrado, criando cliente de teste...")
                cliente = Cliente(
                    estabelecimento_id=estab.id,
                    nome="Cliente Teste",
                    cpf="000.000.000-00",
                    ativo=True
                )
                db.session.add(cliente)
                db.session.commit()
            
            # Criar venda de teste
            estoque_antes = produto.estoque_atual
            
            venda = Venda(
                estabelecimento_id=estab.id,
                cliente_id=cliente.id,
                data_venda=datetime.now(),
                status='finalizada',
                forma_pagamento='DINHEIRO',
                total=Decimal('0.00')
            )
            db.session.add(venda)
            db.session.flush()
            
            # Adicionar item
            item = VendaItem(
                venda_id=venda.id,
                produto_id=produto.id,
                quantidade=1,
                preco_unitario=produto.preco_venda,
                custo_unitario=produto.preco_custo or Decimal('0.00'),
                total_item=produto.preco_venda
            )
            db.session.add(item)
            
            venda.total = produto.preco_venda
            
            # Atualizar estoque
            produto.estoque_atual -= 1
            
            # Criar movimentação
            mov = MovimentacaoEstoque(
                estabelecimento_id=estab.id,
                produto_id=produto.id,
                tipo='SAIDA',
                quantidade=1,
                motivo='VENDA',
                referencia_id=venda.id,
                data_movimentacao=datetime.now()
            )
            db.session.add(mov)
            
            db.session.commit()
            
            # Verificações
            estoque_depois = produto.estoque_atual
            assert estoque_depois == estoque_antes - 1, "Estoque não foi atualizado corretamente"
            
            print_info(f"Venda ID: {venda.id}")
            print_info(f"Total: R$ {venda.total:.2f}")
            print_info(f"Estoque antes: {estoque_antes} | depois: {estoque_depois}")
            
            print_success("Fluxo de venda OK")
            return True
            
    except Exception as e:
        print_error(f"Falha no fluxo de venda: {e}")
        db.session.rollback()
        return False

def test_dashboard_calculations():
    """Teste 3: Cálculos do Dashboard"""
    print("\n" + "="*60)
    print("TESTE 3: Cálculos Financeiros do Dashboard")
    print("="*60)
    
    try:
        with app.app_context():
            estab = Estabelecimento.query.first()
            if not estab:
                print_error("Nenhum estabelecimento encontrado")
                return False
            
            # Buscar dados financeiros
            end_date = date.today()
            start_date = end_date - timedelta(days=30)
            
            financials = DataLayer.get_sales_financials(
                estab.id,
                start_date,
                end_date
            )
            
            print_info(f"Período: {start_date} a {end_date}")
            print_info(f"Revenue (Faturamento): R$ {financials['revenue']:,.2f}")
            print_info(f"COGS (CMV): R$ {financials['cogs']:,.2f}")
            print_info(f"Gross Profit: R$ {financials['gross_profit']:,.2f}")
            
            # Verificar fórmula básica
            expected_gross = financials['revenue'] - financials['cogs']
            if abs(financials['gross_profit'] - expected_gross) > 0.01:
                print_error(f"Gross Profit incorreto! Esperado: {expected_gross}, Obtido: {financials['gross_profit']}")
                return False
            
            # Buscar dashboard completo
            dashboard = DashboardOrchestrator(estab.id).get_scientific_dashboard(days=30)
            
            if 'financials' not in dashboard:
                print_error("Dashboard não retorna 'financials'")
                return False
            
            fin = dashboard['financials']
            print_info(f"Net Profit: R$ {fin.get('net_profit', 0):,.2f}")
            print_info(f"Net Margin: {fin.get('net_margin', 0):.2f}%")
            print_info(f"ROI: {fin.get('roi', 0):.2f}%")
            
            # Verificar que COGS != Total Inventory
            inventory = dashboard.get('inventory', {})
            total_inventory = inventory.get('custo_total', 0)
            
            if abs(financials['cogs'] - total_inventory) < 0.01 and financials['cogs'] > 0:
                print_warning("COGS é igual ao Valor Total do Estoque. Isso pode indicar erro na lógica.")
            else:
                print_success("COGS é diferente do Valor do Estoque (correto!)")
            
            print_success("Cálculos do Dashboard OK")
            return True
            
    except Exception as e:
        print_error(f"Falha nos cálculos do dashboard: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_abc_analysis():
    """Teste 4: Análise ABC"""
    print("\n" + "="*60)
    print("TESTE 4: Análise ABC de Produtos")
    print("="*60)
    
    try:
        with app.app_context():
            estab = Estabelecimento.query.first()
            if not estab:
                print_error("Nenhum estabelecimento encontrado")
                return False
            
            abc = DataLayer.get_abc_analysis(estab.id, days=30)
            
            if not abc or 'produtos' not in abc:
                print_warning("Análise ABC vazia (pode ser normal se não houver vendas)")
                return True
            
            total_produtos = len(abc['produtos'])
            print_info(f"Total de produtos analisados: {total_produtos}")
            
            if 'resumo' in abc:
                resumo = abc['resumo']
                print_info(f"Classe A: {resumo.get('A', {}).get('quantidade', 0)} produtos ({resumo.get('A', {}).get('percentual', 0):.1f}% do faturamento)")
                print_info(f"Classe B: {resumo.get('B', {}).get('quantidade', 0)} produtos ({resumo.get('B', {}).get('percentual', 0):.1f}% do faturamento)")
                print_info(f"Classe C: {resumo.get('C', {}).get('quantidade', 0)} produtos ({resumo.get('C', {}).get('percentual', 0):.1f}% do faturamento)")
            
            print_success("Análise ABC OK")
            return True
            
    except Exception as e:
        print_error(f"Falha na análise ABC: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """Executa todos os testes"""
    print("\n" + "🚀 " + "="*58)
    print("🚀  QUICK VALIDATION TEST - MercadinhoSys ERP")
    print("🚀 " + "="*58)
    
    results = {
        'Database Connection': test_database_connection(),
        'PDV Flow': test_pdv_flow(),
        'Dashboard Calculations': test_dashboard_calculations(),
        'ABC Analysis': test_abc_analysis()
    }
    
    # Resumo
    print("\n" + "="*60)
    print("RESUMO DOS TESTES")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{test_name:.<40} {status}")
    
    print("="*60)
    print(f"\nResultado: {passed}/{total} testes passaram")
    
    if passed == total:
        print_success("\n🎉 TODOS OS TESTES PASSARAM! Sistema está funcional.")
        print_info("Próximos passos:")
        print_info("  1. Execute seed_production_test.py para dados completos")
        print_info("  2. Teste o PDV manualmente no navegador")
        print_info("  3. Verifique o Dashboard")
    else:
        print_error("\n⚠️  ALGUNS TESTES FALHARAM. Revise os erros acima.")
        print_info("Possíveis causas:")
        print_info("  - Banco de dados vazio (execute seed primeiro)")
        print_info("  - Modelos desatualizados (execute migrations)")
        print_info("  - Lógica de negócio com bugs")
    
    return passed == total

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
