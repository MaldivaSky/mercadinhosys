"""
Script para corrigir as datas de criação dos produtos e tornar o
cálculo de Giro de Estoque (VMD / Cobertura) realista.

O problema: todos os produtos foram criados HOJE pela simulação,
então "dias de vida" = 1, e com milhares de vendas, o VMD explode.

Solução: redistribuir as datas de criação para os últimos 365 dias,
e ajustar as quantidades vendidas para valores diários realistas por categoria.
"""
import os
import sys
import random
from decimal import Decimal
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app import create_app, db
from app.models import Produto

# Faixa de VMD realista por categoria de produto de mercado
# (Venda Média Diária em unidades)
VMD_POR_CATEGORIA = {
    'Bebidas': (5, 30),
    'Laticínios': (8, 40),
    'Hortifrúti': (10, 60),
    'Açougue': (3, 15),
    'Mercearia': (4, 25),
    'Padaria': (5, 35),
    'Limpeza': (2, 12),
    'Higiene': (2, 15),
    'Congelados': (2, 10),
    'Frios': (3, 20),
    'default': (2, 20),
}

# Distribuição de giro desejada:
# ~40% Rápido (cobertura <= 15 dias)
# ~40% Normal (cobertura 16-60 dias)  
# ~20% Lento  (cobertura > 60 dias)
GIRO_PESOS = ['rapido'] * 40 + ['normal'] * 40 + ['lento'] * 20


def fix_giro():
    app = create_app()
    with app.app_context():
        produtos = Produto.query.all()
        print(f"Corrigindo {len(produtos)} produtos para giro realista...")

        hoje = datetime.now(timezone.utc)
        
        for p in produtos:
            # Distribuir data de criação aleatoriamente nos últimos 365 dias
            dias_atras = random.randint(30, 365)
            nova_data_criacao = hoje - timedelta(days=dias_atras)
            p.created_at = nova_data_criacao
            
            # Definir dias de vida
            dias_vida = dias_atras
            
            # Obter faixa VMD por categoria
            cat_nome = p.categoria.nome if p.categoria else 'default'
            vmd_min, vmd_max = VMD_POR_CATEGORIA.get(cat_nome, VMD_POR_CATEGORIA['default'])
            
            # Escolher giro aleatório seguindo distribuição desejada
            giro_alvo = random.choice(GIRO_PESOS)
            qtd_atual = float(p.quantidade or 50)
            
            # Calcular VMD necessário para atingir o giro alvo
            if giro_alvo == 'rapido':
                # Cobertura <= 15 dias → VMD >= qtd / 15
                cobertura_alvo = random.uniform(2, 14)
                vmd = qtd_atual / cobertura_alvo
            elif giro_alvo == 'normal':
                # Cobertura 16-60 dias
                cobertura_alvo = random.uniform(16, 59)
                vmd = qtd_atual / cobertura_alvo
            else:  # lento
                # Cobertura > 60 dias → VMD pequeno
                cobertura_alvo = random.uniform(61, 180)
                vmd = qtd_atual / cobertura_alvo if qtd_atual > 0 else 0.1
            
            # Calcular quantidade_vendida total baseada no VMD × dias de vida
            qtd_vendida_nova = max(1, round(vmd * dias_vida))
            
            # Atualizar os campos
            p.quantidade_vendida = qtd_vendida_nova
            
            # Recalcular total_vendido baseado no preço de venda
            preco = float(p.preco_venda or 10)
            p.total_vendido = Decimal(str(round(qtd_vendida_nova * preco, 2)))
            
            # Atualizar margem
            if p.preco_venda and p.preco_custo and p.preco_custo > 0:
                p.margem_lucro = float(
                    ((p.preco_venda - p.preco_custo) / p.preco_custo) * 100
                )

        db.session.commit()
        print("[OK] Datas e VMDs corrigidos!")
        
        # Recalcular classificação ABC
        produtos = Produto.query.order_by(Produto.total_vendido.desc()).all()
        faturamento_total = sum(float(p.total_vendido or 0) for p in produtos)
        
        if faturamento_total > 0:
            acumulado = 0.0
            for p in produtos:
                fat = float(p.total_vendido or 0)
                acumulado += fat
                percentual = acumulado / faturamento_total
                if percentual <= 0.80:
                    p.classificacao_abc = 'A'
                elif percentual <= 0.95:
                    p.classificacao_abc = 'B'
                else:
                    p.classificacao_abc = 'C'
            db.session.commit()
            print("[OK] Classificacao ABC recalculada!")

        # Verificar distribuição resultante
        print("\n=== Verificando distribuicao de Giro (simulada) ===")
        rapido = normal = lento = 0
        for p in produtos:
            dias_vida = max(1, (hoje.date() - p.created_at.date()).days if p.created_at else 365)
            qtd_vendida = float(p.quantidade_vendida or 0)
            if qtd_vendida > 0:
                vmd = qtd_vendida / dias_vida
                if vmd > 0:
                    cobertura = float(p.quantidade or 0) / vmd
                    if cobertura <= 15:
                        rapido += 1
                    elif cobertura <= 60:
                        normal += 1
                    else:
                        lento += 1
                else:
                    lento += 1
            else:
                lento += 1
        
        total = len(produtos)
        print(f"  Rápido (<=15 dias): {rapido} ({rapido/total*100:.1f}%)")
        print(f"  Normal (16-60 dias): {normal} ({normal/total*100:.1f}%)")
        print(f"  Lento (>60 dias): {lento} ({lento/total*100:.1f}%)")
        print("\n[CONCLUIDO] De um F5 no sistema para ver os novos dados.")


if __name__ == '__main__':
    fix_giro()
