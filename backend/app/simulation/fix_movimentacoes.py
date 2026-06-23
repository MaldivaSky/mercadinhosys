import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app
from app.models import db, Produto, ProdutoLote, MovimentacaoEstoque
from datetime import datetime, timedelta

def fix_entradas_estoque():
    app = create_app()
    with app.app_context():
        # Busca produtos com quantidade > 0
        produtos = Produto.query.filter(Produto.quantidade > 0).all()
        for p in produtos:
            # Verifica se já existe uma movimentação de entrada para este produto
            tem_entrada = MovimentacaoEstoque.query.filter_by(
                produto_id=p.id, tipo='entrada'
            ).first()
            
            if not tem_entrada:
                # Usa a data de cadastro do produto, ou do lote mais antigo
                lotes = ProdutoLote.query.filter_by(produto_id=p.id).order_by(ProdutoLote.data_entrada.asc()).all()
                data_entrada = p.created_at
                if lotes:
                    data_entrada = lotes[0].created_at or p.created_at
                
                # Criar MovimentacaoEstoque inicial
                mov = MovimentacaoEstoque(
                    estabelecimento_id=p.estabelecimento_id,
                    produto_id=p.id,
                    tipo='entrada',
                    quantidade=p.quantidade,
                    quantidade_anterior=0,
                    quantidade_atual=p.quantidade,
                    custo_unitario=p.preco_custo,
                    valor_total=p.quantidade * p.preco_custo,
                    motivo='Entrada Inicial (Sistema/Simulação)',
                    observacoes='Ajuste automático para garantir histórico de entrada',
                    created_at=data_entrada
                )
                db.session.add(mov)
                print(f"Gerada Entrada Inicial para Produto ID {p.id}: {p.nome} - Qtd: {p.quantidade}")
        
        db.session.commit()
        print("Finalizado ajuste de entradas!")

if __name__ == '__main__':
    fix_entradas_estoque()
