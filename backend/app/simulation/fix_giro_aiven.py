"""
Script para corrigir o Giro de Estoque no banco de producao (Aiven).
Redistribui as datas de criacao dos produtos e quantidades vendidas
para gerar uma distribuicao realista de Giro Rapido/Normal/Lento.
"""
import os
import sys
import random
from decimal import Decimal
from datetime import datetime, timedelta, timezone

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, BASE_DIR)

# Carrega a URL do Aiven do ambiente (.env) — NUNCA hardcode credenciais no código
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BASE_DIR, ".env"))
except ImportError:
    pass

AIVEN_URL = os.environ.get("AIVEN_DATABASE_URL")
if not AIVEN_URL:
    raise SystemExit("AIVEN_DATABASE_URL nao configurada no .env. Abortando para nao rodar no banco errado.")

# Conectar direto no Aiven, ignorando o banco local
os.environ["DATABASE_URL"] = AIVEN_URL

from app import create_app, db
from app.models import Produto

# VMD realista por categoria (unidades/dia)
VMD_POR_CATEGORIA = {
    'Bebidas': (5, 30),
    'Laticinios': (8, 40),
    'Hortifruti': (10, 60),
    'Acougue': (3, 15),
    'Mercearia': (4, 25),
    'Padaria': (5, 35),
    'Limpeza': (2, 12),
    'Higiene': (2, 15),
    'Congelados': (2, 10),
    'Frios': (3, 20),
    'default': (2, 20),
}

# Distribuicao desejada: ~40% Rapido, ~40% Normal, ~20% Lento
GIRO_PESOS = ['rapido'] * 40 + ['normal'] * 40 + ['lento'] * 20


def fix_giro_aiven():
    app = create_app()
    with app.app_context():
        produtos = Produto.query.all()
        total = len(produtos)
        print(f"Conectado ao Aiven. Corrigindo {total} produtos...")

        hoje = datetime.now(timezone.utc)

        for p in produtos:
            # Redistribuir data de criacao nos ultimos 365 dias
            dias_atras = random.randint(30, 365)
            nova_data = hoje - timedelta(days=dias_atras)
            p.created_at = nova_data

            # VMD por categoria
            cat_nome = p.categoria.nome if p.categoria else 'default'
            vmd_min, vmd_max = VMD_POR_CATEGORIA.get(cat_nome, VMD_POR_CATEGORIA['default'])

            # Giro alvo
            giro_alvo = random.choice(GIRO_PESOS)
            qtd_atual = float(p.quantidade or 50)

            if giro_alvo == 'rapido':
                cobertura_alvo = random.uniform(2, 14)
            elif giro_alvo == 'normal':
                cobertura_alvo = random.uniform(16, 59)
            else:
                cobertura_alvo = random.uniform(61, 180)

            vmd = qtd_atual / cobertura_alvo if cobertura_alvo > 0 else 1
            qtd_vendida_nova = max(1, round(vmd * dias_atras))

            p.quantidade_vendida = qtd_vendida_nova
            preco = float(p.preco_venda or 10)
            p.total_vendido = Decimal(str(round(qtd_vendida_nova * preco, 2)))

            if p.preco_venda and p.preco_custo and float(p.preco_custo) > 0:
                p.margem_lucro = float(((p.preco_venda - p.preco_custo) / p.preco_custo) * 100)

        db.session.commit()
        print("[OK] Datas e VMDs corrigidos no Aiven!")

        # Recalcular ABC
        produtos = Produto.query.order_by(Produto.total_vendido.desc()).all()
        fat_total = sum(float(p.total_vendido or 0) for p in produtos)
        if fat_total > 0:
            acum = 0.0
            for p in produtos:
                fat = float(p.total_vendido or 0)
                acum += fat
                perc = acum / fat_total
                if perc <= 0.80:
                    p.classificacao_abc = 'A'
                elif perc <= 0.95:
                    p.classificacao_abc = 'B'
                else:
                    p.classificacao_abc = 'C'
            db.session.commit()
            print("[OK] Classificacao ABC recalculada!")

        # Verificar resultado
        print("\n=== Distribuicao resultante no Aiven ===")
        rapido = normal = lento = 0
        hoje_d = hoje.date()
        for p in produtos:
            dias_vida = max(1, (hoje_d - p.created_at.date()).days) if p.created_at else 365
            qtd_v = float(p.quantidade_vendida or 0)
            qtd_a = float(p.quantidade or 0)
            if qtd_v > 0:
                vmd = qtd_v / dias_vida
                cob = qtd_a / vmd if vmd > 0 else 9999
                if cob <= 15:
                    rapido += 1
                elif cob <= 60:
                    normal += 1
                else:
                    lento += 1
            else:
                lento += 1

        t = len(produtos)
        print(f"  Rapido (<= 15 dias): {rapido} ({rapido/t*100:.1f}%)")
        print(f"  Normal (16-60 dias): {normal} ({normal/t*100:.1f}%)")
        print(f"  Lento  (> 60 dias) : {lento}  ({lento/t*100:.1f}%)")
        print("\n[CONCLUIDO] Atualize a pagina no sistema de producao para ver os novos dados.")


if __name__ == '__main__':
    fix_giro_aiven()
