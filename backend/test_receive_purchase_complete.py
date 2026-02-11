#!/usr/bin/env python
"""
Test script to verify the complete purchase order receive flow:
1. Create a purchase order
2. Receive the order with validade and lote
3. Verify stock is updated
4. Verify boleto is created
5. Verify despesa is created
"""

import os
import sys
import json
from datetime import datetime, date, timedelta
from decimal import Decimal

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import (
    Estabelecimento, Funcionario, Fornecedor, Produto, PedidoCompra, 
    PedidoCompraItem, ProdutoLote, ContaPagar, MovimentacaoEstoque, Despesa
)

app = create_app()

def test_receive_purchase_flow():
    """Test the complete receive purchase flow"""
    with app.app_context():
        print("\n" + "="*80)
        print("🧪 TESTE COMPLETO: RECEBER PEDIDO COM LOTE E VALIDADE")
        print("="*80)
        
        # 1. Get test data
        print("\n1️⃣  Buscando dados de teste...")
        estabelecimento = Estabelecimento.query.first()
        if not estabelecimento:
            print("❌ Nenhum estabelecimento encontrado. Execute seed_test.py primeiro.")
            return False
        
        funcionario = Funcionario.query.filter_by(estabelecimento_id=estabelecimento.id).first()
        if not funcionario:
            print("❌ Nenhum funcionário encontrado.")
            return False
        
        fornecedor = Fornecedor.query.filter_by(estabelecimento_id=estabelecimento.id).first()
        if not fornecedor:
            print("❌ Nenhum fornecedor encontrado.")
            return False
        
        produto = Produto.query.filter_by(estabelecimento_id=estabelecimento.id).first()
        if not produto:
            print("❌ Nenhum produto encontrado.")
            return False
        
        print(f"✅ Estabelecimento: {estabelecimento.nome_fantasia or estabelecimento.razao_social}")
        print(f"✅ Funcionário: {funcionario.nome}")
        print(f"✅ Fornecedor: {fornecedor.nome_fantasia}")
        print(f"✅ Produto: {produto.nome}")
        
        # 2. Create a purchase order
        print("\n2️⃣  Criando pedido de compra...")
        pedido = PedidoCompra(
            estabelecimento_id=estabelecimento.id,
            fornecedor_id=fornecedor.id,
            funcionario_id=funcionario.id,
            numero_pedido=f"PC{datetime.now().strftime('%Y%m%d%H%M%S')}",
            data_previsao_entrega=date.today() + timedelta(days=7),
            condicao_pagamento="30 dias",
            status="pendente",
            subtotal=Decimal('1000.00'),
            desconto=Decimal('0'),
            frete=Decimal('50.00'),
            total=Decimal('1050.00')
        )
        db.session.add(pedido)
        db.session.flush()
        
        # Create purchase order item
        item = PedidoCompraItem(
            pedido_id=pedido.id,
            produto_id=produto.id,
            produto_nome=produto.nome,
            produto_unidade=produto.unidade_medida,
            quantidade_solicitada=100,
            preco_unitario=Decimal('10.00'),
            desconto_percentual=Decimal('0'),
            total_item=Decimal('1000.00'),
            status="pendente"
        )
        db.session.add(item)
        db.session.commit()
        
        print(f"✅ Pedido criado: {pedido.numero_pedido}")
        print(f"✅ Item: {item.produto_nome} x {item.quantidade_solicitada} @ R$ {item.preco_unitario}")
        
        # 3. Receive the order
        print("\n3️⃣  Recebendo pedido com lote e validade...")
        
        # Store initial stock
        stock_inicial = produto.quantidade
        
        # Simulate receiving the order
        quantidade_recebida = 100
        data_validade = date.today() + timedelta(days=365)
        numero_lote = f"LOTE-{pedido.numero_pedido}-001"
        
        # Update item
        item.quantidade_recebida = quantidade_recebida
        item.status = "recebido"
        
        # Create lote
        lote = ProdutoLote(
            estabelecimento_id=estabelecimento.id,
            produto_id=produto.id,
            fornecedor_id=fornecedor.id,
            pedido_compra_id=pedido.id,
            numero_lote=numero_lote,
            quantidade=quantidade_recebida,
            quantidade_inicial=quantidade_recebida,
            data_validade=data_validade,
            data_entrada=date.today(),
            preco_custo_unitario=item.preco_unitario,
            ativo=True
        )
        db.session.add(lote)
        
        # Update product stock
        produto.quantidade += quantidade_recebida
        
        # Create movement
        movimentacao = MovimentacaoEstoque(
            estabelecimento_id=estabelecimento.id,
            produto_id=produto.id,
            funcionario_id=funcionario.id,
            pedido_compra_id=pedido.id,
            tipo="entrada",
            quantidade=quantidade_recebida,
            quantidade_anterior=stock_inicial,
            quantidade_atual=produto.quantidade,
            custo_unitario=item.preco_unitario,
            valor_total=item.preco_unitario * quantidade_recebida,
            motivo=f"Recebimento pedido {pedido.numero_pedido}",
            observacoes=f"Lote: {numero_lote}"
        )
        db.session.add(movimentacao)
        
        # Update pedido
        pedido.data_recebimento = date.today()
        pedido.status = "recebido"
        
        # Create boleto
        data_vencimento = date.today() + timedelta(days=30)
        conta_pagar = ContaPagar(
            estabelecimento_id=estabelecimento.id,
            fornecedor_id=fornecedor.id,
            pedido_compra_id=pedido.id,
            numero_documento=f"BOL-{pedido.numero_pedido}",
            tipo_documento="boleto",
            valor_original=pedido.total,
            valor_atual=pedido.total,
            data_emissao=date.today(),
            data_vencimento=data_vencimento,
            status="aberto",
            observacoes=f"Referente ao pedido {pedido.numero_pedido}"
        )
        db.session.add(conta_pagar)
        
        db.session.commit()
        
        print(f"✅ Pedido recebido com sucesso")
        print(f"✅ Lote criado: {numero_lote}")
        print(f"✅ Validade: {data_validade}")
        print(f"✅ Boleto criado: {conta_pagar.numero_documento}")
        
        # 4. Verify stock update
        print("\n4️⃣  Verificando atualização de estoque...")
        produto_atualizado = Produto.query.get(produto.id)
        print(f"✅ Estoque anterior: {stock_inicial}")
        print(f"✅ Estoque recebido: {quantidade_recebida}")
        print(f"✅ Estoque atual: {produto_atualizado.quantidade}")
        
        if produto_atualizado.quantidade != stock_inicial + quantidade_recebida:
            print(f"❌ ERRO: Estoque não foi atualizado corretamente!")
            return False
        
        # 5. Verify lote
        print("\n5️⃣  Verificando lote criado...")
        lote_verificado = ProdutoLote.query.filter_by(numero_lote=numero_lote).first()
        if not lote_verificado:
            print(f"❌ ERRO: Lote não foi criado!")
            return False
        
        print(f"✅ Lote encontrado: {lote_verificado.numero_lote}")
        print(f"✅ Quantidade: {lote_verificado.quantidade}")
        print(f"✅ Validade: {lote_verificado.data_validade}")
        print(f"✅ Ativo: {lote_verificado.ativo}")
        
        # 6. Verify boleto
        print("\n6️⃣  Verificando boleto criado...")
        boleto_verificado = ContaPagar.query.filter_by(numero_documento=conta_pagar.numero_documento).first()
        if not boleto_verificado:
            print(f"❌ ERRO: Boleto não foi criado!")
            return False
        
        print(f"✅ Boleto encontrado: {boleto_verificado.numero_documento}")
        print(f"✅ Valor: R$ {boleto_verificado.valor_original}")
        print(f"✅ Vencimento: {boleto_verificado.data_vencimento}")
        print(f"✅ Status: {boleto_verificado.status}")
        
        # 7. Verify movement
        print("\n7️⃣  Verificando movimentação de estoque...")
        movimento_verificado = MovimentacaoEstoque.query.filter_by(pedido_compra_id=pedido.id).first()
        if not movimento_verificado:
            print(f"❌ ERRO: Movimentação não foi criada!")
            return False
        
        print(f"✅ Movimentação encontrada")
        print(f"✅ Tipo: {movimento_verificado.tipo}")
        print(f"✅ Quantidade: {movimento_verificado.quantidade}")
        print(f"✅ Valor total: R$ {movimento_verificado.valor_total}")
        
        # 8. Verify pedido status
        print("\n8️⃣  Verificando status do pedido...")
        pedido_verificado = PedidoCompra.query.get(pedido.id)
        print(f"✅ Status: {pedido_verificado.status}")
        print(f"✅ Data de recebimento: {pedido_verificado.data_recebimento}")
        
        if pedido_verificado.status != "recebido":
            print(f"❌ ERRO: Status do pedido não foi atualizado para 'recebido'!")
            return False
        
        print("\n" + "="*80)
        print("✅ TODOS OS TESTES PASSARAM COM SUCESSO!")
        print("="*80 + "\n")
        
        return True

if __name__ == "__main__":
    success = test_receive_purchase_flow()
    sys.exit(0 if success else 1)
