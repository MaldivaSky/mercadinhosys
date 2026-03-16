import os
import sys

# Adicionar o diretório raiz ao path
sys.path.append(os.getcwd())

from app import create_app, db
from app.models import Produto, ProdutoLote, MovimentacaoEstoque
from decimal import Decimal, ROUND_HALF_UP

def round_qty(val):
    if val is None:
        return Decimal('0.000')
    d = Decimal(str(val))
    # Se estiver entre -0.01 e 0.01 e não for exatamente zero, zerar resíduo matemático
    if Decimal('-0.01') < d < Decimal('0.01'):
        return Decimal('0.000')
    return d.quantize(Decimal('0.000'), rounding=ROUND_HALF_UP)

app = create_app()
with app.app_context():
    print("🚀 [HEALER] Iniciando correção de precisão de estoque...")
    
    # 1. Corrigir Produtos
    produtos = Produto.query.all()
    count_prod = 0
    for p in produtos:
        old_val = p.quantidade
        new_val = round_qty(old_val)
        if old_val != new_val:
            p.quantidade = new_val
            count_prod += 1
    
    # 2. Corrigir Lotes
    lotes = ProdutoLote.query.all()
    count_lotes = 0
    for l in lotes:
        old_val = l.quantidade
        new_val = round_qty(old_val)
        if old_val != new_val:
            l.quantidade = new_val
            count_lotes += 1

    # 3. Corrigir Movimentações (opcional, mas bom para consistência)
    movs = MovimentacaoEstoque.query.all()
    count_movs = 0
    for m in movs:
        changed = False
        for attr in ['quantidade', 'quantidade_anterior', 'quantidade_atual']:
            old_val = getattr(m, attr)
            new_val = round_qty(old_val)
            if old_val != new_val:
                setattr(m, attr, new_val)
                changed = True
        if changed:
            count_movs += 1

    db.session.commit()
    print(f"✅ Sucesso!")
    print(f"   - Produtos corrigidos: {count_prod}")
    print(f"   - Lotes corrigidos: {count_lotes}")
    print(f"   - Movimentações corrigidas: {count_movs}")
