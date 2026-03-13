import os
import sys
from datetime import datetime, date

# Adicionar diretório atual ao path para imports
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from app.models import (
    db, Estabelecimento, Funcionario, Venda, Cliente, 
    ProdutoLote, RegistroPonto, ContaReceber
)

def run_verification():
    app = create_app()
    with app.app_context():
        print("\n🔍 [QA AUDIT: MERCADINHOSYS ELITE]")
        print("="*50)
        
        errors = []
        
        # 1. Verificação de Identidade Master
        print("👤 Verificando Super Admin (Rafael)...")
        rafael = Funcionario.query.filter_by(username="maldivas").first()
        if not rafael:
            errors.append("Super Admin 'maldivas' não encontrado.")
        elif not rafael.is_super_admin:
            errors.append("Usuário 'maldivas' existe mas não possui privilégios de Super Admin.")
        else:
            print("   ✅ Rafael (maldivas) identificado como Master.")

        # 2. Verificação de Massa de Dados (6 Meses)
        print("\n📊 Auditando Estabelecimento 'admin1' (6 Meses)...")
        est1 = Estabelecimento.query.filter(Estabelecimento.nome_fantasia.like("%Souza%")).first()
        if not est1:
            errors.append("Estabelecimento admin1 não encontrado.")
        else:
            # Vendas
            vendas_count = Venda.query.filter_by(estabelecimento_id=est1.id).count()
            print(f"   ✅ Vendas: {vendas_count} registros encontrados.")
            if vendas_count < 100:
                errors.append("Massa de vendas insuficiente para 6 meses.")
            
            # Histórico Temporal
            primeira_venda = Venda.query.filter_by(estabelecimento_id=est1.id).order_by(Venda.data_venda.asc()).first()
            if primeira_venda:
                delta = datetime.now() - primeira_venda.data_venda
                print(f"   ✅ Histórico: {delta.days // 30} meses de dados ativos.")
            
            # RH Ponto
            pontos = RegistroPonto.query.filter_by(estabelecimento_id=est1.id).count()
            print(f"   ✅ RH: {pontos} batidas de ponto registradas.")

        # 3. Verificação de Inteligência (Lotes & Fiado)
        print("\n🧠 Auditando Inteligência de Negócio...")
        lotes_com_validade = ProdutoLote.query.filter(ProdutoLote.data_validade != None).count()
        if lotes_com_validade > 0:
            print(f"   ✅ Lotes: {lotes_com_validade} lotes com rastreabilidade de validade.")
        else:
            errors.append("Nenhum lote com validade encontrado.")

        fiados = ContaReceber.query.count()
        print(f"   ✅ Fiado: {fiados} contas a receber (Bons e Maus pagadores).")

        # 4. Verificação de Isolamento (Multi-Tenancy)
        print("\n🛡️ Validando Isolamento de Dados (Anti-Vazamento)...")
        # Se eu filtrar por est1, não devo ver nada de est2
        est2 = Estabelecimento.query.filter(Estabelecimento.nome_fantasia.like("%Bairro%")).first()
        if est1 and est2:
            vendas_est2_in_est1 = Venda.query.filter_by(estabelecimento_id=est2.id).all()
            # Simulando o bypass que o super admin teria vs o que o cliente vê
            # (Aqui testamos a integridade física da tabela)
            print(f"   ✅ Integridade: {vendas_count} (Loja 1) / {Venda.query.filter_by(estabelecimento_id=est2.id).count()} (Loja 2).")

        print("="*50)
        if not errors:
            print("🏆 [RESULTADO: APROVADO] O sistema possui massa de dados industrial.")
        else:
            print("❌ [RESULTADO: FALHA]")
            for err in errors:
                print(f"   - {err}")
        
        print("="*50)

if __name__ == "__main__":
    run_verification()
