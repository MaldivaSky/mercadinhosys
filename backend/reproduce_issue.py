#!/usr/bin/env python3
"""
Script para reproduzir a lógica de listar_produtos_estoque e verificar se lote/validade estão sendo retornados.
"""
from app import create_app, db
from app.models import Produto, CategoriaProduto, Fornecedor
from sqlalchemy import text
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP

app = create_app()

def calcular_margem_lucro(venda, custo):
    if not custo or custo == 0:
        return 0
    return ((venda - custo) / custo) * 100

with app.app_context():
    print("=" * 80)
    print("TESTE LÓGICA ORM (Caminho Principal)")
    print("=" * 80)
    
    try:
        # Simular query base
        query = Produto.query
        paginacao = query.paginate(page=1, per_page=5, error_out=False)
        
        for produto in paginacao.items:
            print(f"ID: {produto.id} | Nome: {produto.nome}")
            print(f"   Lote ORM: '{produto.lote}'")
            print(f"   Validade ORM: {produto.data_validade}")
            
            # Simular construção do dict
            produto_dict = {
                "lote": produto.lote if hasattr(produto, 'lote') else None,
                "data_validade": produto.data_validade.isoformat() if hasattr(produto, 'data_validade') and produto.data_validade else None,
            }
            print(f"   Dict Final: {produto_dict}")
            
    except Exception as e:
        print(f"ERRO ORM: {e}")

    print("\n" + "=" * 80)
    print("TESTE LÓGICA SQL (Fallback)")
    print("=" * 80)
    
    try:
        # Simular query SQL fallback
        sql = text(
            f"SELECT id, nome, codigo_barras, codigo_interno, descricao, marca, unidade_medida, "
            f"preco_custo, preco_venda, quantidade, quantidade_minima, ativo, "
            f"quantidade_vendida, total_vendido, ultima_venda, classificacao_abc, fornecedor_id, "
            f"lote, data_validade, controlar_validade "  # Campos adicionados
            f"FROM produtos "
            f"LIMIT 5 OFFSET 0"
        )
        
        rows = db.session.execute(sql).fetchall()
        
        for r in rows:
            # Simular extração
            rid = r["id"] if isinstance(r, dict) or hasattr(r, "keys") else r[0]
            nome = r["nome"] if isinstance(r, dict) or hasattr(r, "keys") else r[1]
            
            # Índices ajustados conforme a query
            lote = r.get("lote", None) if hasattr(r, "get") else r[17]
            data_validade = r.get("data_validade", None) if hasattr(r, "get") else r[18]
            
            print(f"ID: {rid} | Nome: {nome}")
            print(f"   Lote SQL: '{lote}'")
            print(f"   Validade SQL: {data_validade}")
            
    except Exception as e:
        print(f"ERRO SQL: {e}")

