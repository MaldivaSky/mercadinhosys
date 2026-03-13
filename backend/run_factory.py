#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os

# Adiciona o diretório atual ao path para importar a app
sys.path.append(os.getcwd())

from app import create_app
from app.models import db, Estabelecimento, Funcionario, Cliente, Produto, Venda, VendaItem, Despesa, ContaReceber, Caixa, MovimentacaoCaixa, MovimentacaoEstoque, ProdutoLote, CategoriaProduto, HistoricoPrecos, Pagamento
from app.simulation.chronicle import ChronicleSimulator
from sqlalchemy import text

def run_reality_factory():
    """
    Script Mestre: Dispara a Fábrica de Realidade do MercadinhoSys.
    Injeta 5 empresas, 100+ produtos, 6 meses de história.
    """
    os.environ["FLASK_ENV"] = "simulation"
    app = create_app()
    
    with app.app_context():
        print("🚀 [FÁBRICA DE REALIDADE] Iniciando motor de simulação MASTER...")
        
        # 1. Garantir que o SCHEMA existe antes de qualquer operação
        print("🏗️  Garantindo integridade do Schema...")
        db.create_all()
        
        # 2. Limpeza Seletiva
        print("🧹 Limpando base de dados para injeção limpa...")
        db.session.execute(text("PRAGMA foreign_keys = OFF;"))
        
        tables = [
            "movimentacoes_caixa", "pagamentos", "contas_receber", 
            "venda_itens", "vendas", "estoque_movimentacoes", 
            "produtos_lotes", "produtos", "fornecedores", 
            "clientes", "caixas", "funcionarios", "estabelecimentos",
            "categorias_produto", "historico_precos", "despesas"
        ]
        
        for table in tables:
            try:
                # Usamos TRUNCATE artificial para SQLite
                db.session.execute(text(f"DELETE FROM {table};"))
            except Exception as e:
                # Silencia se a tabela não existir (embora create_all devesse ter criado)
                pass
        
        db.session.execute(text("PRAGMA foreign_keys = ON;"))
        db.session.commit()
        
        # Disparar o Simulador
        simulator = ChronicleSimulator(app)
        
        # Rodamos 6 meses de história (digital twin real)
        simulator.run_full_simulation(months=6)
        
        # --- RELATÓRIO DE ONBOARDING SÊNIOR ---
        print("\n" + "="*60)
        print("📊 RELATÓRIO MASTER DE ONBOARDING - GÊMEO DIGITAL".center(60))
        print("="*60)
        print(f"{'CENÁRIO':<15} | {'ESTABELECIMENTO':<25} | {'USUÁRIO' :<15} | {'SENHA'}")
        print("-"*80)
        
        from app.simulation.dna_factory import DNAFactory
        for scen_key, dna in DNAFactory.SCENARIOS.items():
            est = Estabelecimento.query.filter_by(nome_fantasia=dna.nome).first()
            if est:
                admin = Funcionario.query.filter_by(estabelecimento_id=est.id, cargo='Gerente').first()
                if admin:
                    # By injectors rule: password is admin{id}
                    senha_admin = f"admin{est.id}"
                    print(f"{scen_key:<15} | {est.nome_fantasia[:25]:<25} | {admin.username:<15} | {senha_admin}")
        
        print("="*80)
        print("🚀 Super-Admin Global para ver consolidado: maldivas / Mald1v@$")
        print("="*80)
        print("\n✅ [SUCESSO] Fábrica de Realidade concluída com dados industriais!")

if __name__ == "__main__":
    run_reality_factory()
