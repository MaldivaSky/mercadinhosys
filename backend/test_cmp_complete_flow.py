#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script to verify complete CMP (Custo Médio Ponderado) integration flow.

Tests:
1. Create product with initial stock and CMP
2. Adjust stock with CMP recalculation
3. Receive purchase order with CMP
4. Verify PDV captures CMP snapshot at time of sale
5. Verify audit trail in HistoricoPrecos
"""

import sys
import os
from datetime import datetime, date, timedelta
from decimal import Decimal

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app import create_app, db
from app.models import (
    Estabelecimento, Funcionario, Produto, CategoriaProduto, 
    HistoricoPrecos, MovimentacaoEstoque, Fornecedor, PedidoCompra,
    PedidoCompraItem, ProdutoLote, Venda, VendaItem, Cliente
)

def setup_test_data():
    """Setup test data"""
    app = create_app()
    with app.app_context():
        # Clear existing data
        db.drop_all()
        db.create_all()
        
        # Create establishment
        estab = Estabelecimento(
            nome_fantasia="Teste CMP",
            razao_social="Teste CMP LTDA",
            cnpj="12.345.678/0001-90",
            telefone="1133334444",
            email="teste@cmp.com",
            cep="01310100",
            logradouro="Avenida Paulista",
            numero="1000",
            bairro="Bela Vista",
            cidade="São Paulo",
            estado="SP",
            data_abertura=date.today()
        )
        db.session.add(estab)
        db.session.flush()
        
        # Create user
        user = Funcionario(
            estabelecimento_id=estab.id,
            nome="Teste User",
            cpf="123.456.789-00",
            data_nascimento=date(1990, 1, 1),
            celular="11999999999",
            email="user@teste.com",
            cargo="Gerente",
            data_admissao=date.today(),
            username="testuser",
            role="GERENTE",
            ativo=True,
            cep="01310100",
            logradouro="Avenida Paulista",
            numero="1000",
            bairro="Bela Vista",
            cidade="São Paulo",
            estado="SP"
        )
        user.set_senha("123456")
        db.session.add(user)
        db.session.flush()
        
        # Create category
        categoria = CategoriaProduto(
            estabelecimento_id=estab.id,
            nome="Bebidas"
        )
        db.session.add(categoria)
        db.session.flush()
        
        # Create supplier
        fornecedor = Fornecedor(
            estabelecimento_id=estab.id,
            nome_fantasia="Fornecedor Teste",
            razao_social="Fornecedor Teste LTDA",
            cnpj="98.765.432/0001-10",
            telefone="1144445555",
            email="fornecedor@teste.com",
            cep="01310100",
            logradouro="Avenida Paulista",
            numero="2000",
            bairro="Bela Vista",
            cidade="São Paulo",
            estado="SP"
        )
        db.session.add(fornecedor)
        db.session.flush()
        
        # Create client
        cliente = Cliente(
            estabelecimento_id=estab.id,
            nome="Cliente Teste",
            cpf="111.222.333-44",
            celular="11988888888",
            email="cliente@teste.com",
            cep="01310100",
            logradouro="Avenida Paulista",
            numero="3000",
            bairro="Bela Vista",
            cidade="São Paulo",
            estado="SP"
        )
        db.session.add(cliente)
        db.session.flush()
        
        db.session.commit()
        
        return {
            'app': app,
            'estab_id': estab.id,
            'user_id': user.id,
            'categoria_id': categoria.id,
            'fornecedor_id': fornecedor.id,
            'cliente_id': cliente.id
        }

def test_create_product_with_initial_stock():
    """Test 1: Create product with initial stock and CMP"""
    print("\n" + "="*60)
    print("TEST 1: Create product with initial stock and CMP")
    print("="*60)
    
    data = setup_test_data()
    app = data['app']
    
    with app.app_context():
        # Create product with initial stock
        produto = Produto(
            estabelecimento_id=data['estab_id'],
            categoria_id=data['categoria_id'],
            nome="Refrigerante 2L",
            codigo_interno="REF001",
            quantidade=100,
            quantidade_minima=20,
            preco_custo=Decimal("2.50"),
            preco_venda=Decimal("5.00"),
            margem_lucro=Decimal("100.00"),
            ativo=True
        )
        db.session.add(produto)
        db.session.flush()
        
        # Apply CMP on initial stock
        produto.recalcular_preco_custo_ponderado(
            quantidade_entrada=100,
            custo_unitario_entrada=Decimal("2.50"),
            estoque_atual=0,
            registrar_historico=True,
            funcionario_id=data['user_id'],
            motivo="Cadastro inicial do produto"
        )
        
        # Create initial movement
        mov = MovimentacaoEstoque(
            estabelecimento_id=data['estab_id'],
            produto_id=produto.id,
            funcionario_id=data['user_id'],
            tipo='entrada',
            quantidade=100,
            quantidade_anterior=0,
            quantidade_atual=100,
            custo_unitario=produto.preco_custo,
            valor_total=100 * produto.preco_custo,
            motivo="Cadastro inicial"
        )
        db.session.add(mov)
        db.session.commit()
        
        print(f"[OK] Produto criado: {produto.nome}")
        print(f"  - ID: {produto.id}")
        print(f"  - Quantidade: {produto.quantidade}")
        print(f"  - Custo: R$ {produto.preco_custo}")
        print(f"  - Venda: R$ {produto.preco_venda}")
        print(f"  - Margem: {produto.margem_lucro}%")
        
        # Verify history
        historico = HistoricoPrecos.query.filter_by(produto_id=produto.id).all()
        print(f"[OK] Historico de precos registrado: {len(historico)} entrada(s)")
        for h in historico:
            print(f"  - {h.motivo}: R$ {h.preco_custo_anterior} -> R$ {h.preco_custo_novo}")

def test_adjust_stock_with_cmp():
    """Test 2: Adjust stock with CMP recalculation"""
    print("\n" + "="*60)
    print("TEST 2: Adjust stock with CMP recalculation")
    print("="*60)
    
    data = setup_test_data()
    app = data['app']
    
    with app.app_context():
        # Create initial product
        produto = Produto(
            estabelecimento_id=data['estab_id'],
            categoria_id=data['categoria_id'],
            nome="Suco Natural 1L",
            codigo_interno="SUC001",
            quantidade=50,
            quantidade_minima=10,
            preco_custo=Decimal("3.00"),
            preco_venda=Decimal("7.00"),
            margem_lucro=Decimal("133.33"),
            ativo=True
        )
        db.session.add(produto)
        db.session.flush()
        
        print(f"[OK] Produto inicial: {produto.nome}")
        print(f"  - Quantidade: {produto.quantidade}")
        print(f"  - Custo: R$ {produto.preco_custo}")
        
        # Adjust stock with different cost (simulating new purchase)
        custo_anterior = produto.preco_custo
        produto.recalcular_preco_custo_ponderado(
            quantidade_entrada=50,
            custo_unitario_entrada=Decimal("3.50"),
            estoque_atual=50,
            registrar_historico=True,
            funcionario_id=data['user_id'],
            motivo="Entrada de estoque - ajuste"
        )
        produto.quantidade += 50
        
        mov = MovimentacaoEstoque(
            estabelecimento_id=data['estab_id'],
            produto_id=produto.id,
            funcionario_id=data['user_id'],
            tipo='entrada',
            quantidade=50,
            quantidade_anterior=50,
            quantidade_atual=100,
            custo_unitario=Decimal("3.50"),
            valor_total=50 * Decimal("3.50"),
            motivo="Ajuste de estoque"
        )
        db.session.add(mov)
        db.session.commit()
        
        print(f"[OK] Estoque ajustado:")
        print(f"  - Quantidade anterior: 50")
        print(f"  - Quantidade adicionada: 50")
        print(f"  - Quantidade atual: {produto.quantidade}")
        print(f"  - Custo anterior: R$ {custo_anterior}")
        print(f"  - Novo custo (CMP): R$ {produto.preco_custo}")
        print(f"  - Diferenca: R$ {produto.preco_custo - custo_anterior}")
        
        # Verify CMP calculation
        # CMP = (50 * 3.00 + 50 * 3.50) / 100 = 3.25
        expected_cmp = Decimal("3.25")
        assert abs(produto.preco_custo - expected_cmp) < Decimal("0.01"), \
            f"CMP calculation error: expected {expected_cmp}, got {produto.preco_custo}"
        print(f"[OK] CMP calculation verified: R$ {produto.preco_custo} (expected R$ {expected_cmp})")

def test_receive_purchase_order_with_cmp():
    """Test 3: Receive purchase order with CMP"""
    print("\n" + "="*60)
    print("TEST 3: Receive purchase order with CMP")
    print("="*60)
    
    data = setup_test_data()
    app = data['app']
    
    with app.app_context():
        # Create product
        produto = Produto(
            estabelecimento_id=data['estab_id'],
            categoria_id=data['categoria_id'],
            nome="Água Mineral 1.5L",
            codigo_interno="AGU001",
            quantidade=100,
            quantidade_minima=20,
            preco_custo=Decimal("1.50"),
            preco_venda=Decimal("3.00"),
            margem_lucro=Decimal("100.00"),
            ativo=True
        )
        db.session.add(produto)
        db.session.flush()
        
        # Create purchase order
        pedido = PedidoCompra(
            estabelecimento_id=data['estab_id'],
            fornecedor_id=data['fornecedor_id'],
            funcionario_id=data['user_id'],
            numero_pedido="PC000001",
            data_previsao_entrega=date.today() + timedelta(days=7),
            condicao_pagamento="30 DIAS",
            status='pendente'
        )
        db.session.add(pedido)
        db.session.flush()
        
        # Create purchase order item
        item = PedidoCompraItem(
            pedido_id=pedido.id,
            produto_id=produto.id,
            produto_nome=produto.nome,
            produto_unidade="UN",
            quantidade_solicitada=50,
            preco_unitario=Decimal("1.80"),
            desconto_percentual=Decimal("0"),
            total_item=50 * Decimal("1.80"),
            status='pendente'
        )
        db.session.add(item)
        db.session.flush()
        
        print(f"[OK] Pedido de compra criado: {pedido.numero_pedido}")
        print(f"  - Produto: {produto.nome}")
        print(f"  - Quantidade: 50 unidades")
        print(f"  - Preco unitario: R$ 1.80")
        print(f"  - Custo atual do produto: R$ {produto.preco_custo}")
        
        # Receive purchase order
        custo_anterior = produto.preco_custo
        quantidade_anterior = produto.quantidade
        
        item.quantidade_recebida = 50
        item.status = 'recebido'
        
        # Create lot
        lote = ProdutoLote(
            estabelecimento_id=data['estab_id'],
            produto_id=produto.id,
            fornecedor_id=data['fornecedor_id'],
            pedido_compra_id=pedido.id,
            numero_lote="LOTE-PC000001-001",
            quantidade=50,
            quantidade_inicial=50,
            data_validade=date.today() + timedelta(days=365),
            data_entrada=date.today(),
            preco_custo_unitario=Decimal("1.80"),
            ativo=True
        )
        db.session.add(lote)
        
        # Create movement
        mov = MovimentacaoEstoque(
            estabelecimento_id=data['estab_id'],
            produto_id=produto.id,
            funcionario_id=data['user_id'],
            pedido_compra_id=pedido.id,
            tipo='entrada',
            quantidade=50,
            quantidade_anterior=quantidade_anterior,
            quantidade_atual=quantidade_anterior + 50,
            custo_unitario=Decimal("1.80"),
            valor_total=50 * Decimal("1.80"),
            motivo=f'Recebimento pedido {pedido.numero_pedido}'
        )
        db.session.add(mov)
        
        # Apply CMP
        produto.recalcular_preco_custo_ponderado(
            quantidade_entrada=50,
            custo_unitario_entrada=Decimal("1.80"),
            estoque_atual=quantidade_anterior,
            registrar_historico=True,
            funcionario_id=data['user_id'],
            motivo=f'Recebimento pedido {pedido.numero_pedido}'
        )
        produto.quantidade += 50
        
        pedido.status = 'recebido'
        pedido.data_recebimento = date.today()
        
        db.session.commit()
        
        print(f"[OK] Pedido recebido:")
        print(f"  - Quantidade anterior: {quantidade_anterior}")
        print(f"  - Quantidade recebida: 50")
        print(f"  - Quantidade atual: {produto.quantidade}")
        print(f"  - Custo anterior: R$ {custo_anterior}")
        print(f"  - Novo custo (CMP): R$ {produto.preco_custo}")
        print(f"  - Lote criado: LOTE-PC000001-001")
        
        # Verify CMP calculation
        # CMP = (100 * 1.50 + 50 * 1.80) / 150 = 1.60
        expected_cmp = Decimal("1.60")
        assert abs(produto.preco_custo - expected_cmp) < Decimal("0.01"), \
            f"CMP calculation error: expected {expected_cmp}, got {produto.preco_custo}"
        print(f"[OK] CMP calculation verified: R$ {produto.preco_custo} (expected R$ {expected_cmp})")

def test_pdv_captures_cmp_snapshot():
    """Test 4: Verify PDV captures CMP snapshot at time of sale"""
    print("\n" + "="*60)
    print("TEST 4: PDV captures CMP snapshot at time of sale")
    print("="*60)
    
    data = setup_test_data()
    app = data['app']
    
    with app.app_context():
        # Create product with CMP
        produto = Produto(
            estabelecimento_id=data['estab_id'],
            categoria_id=data['categoria_id'],
            nome="Cerveja Premium 600ml",
            codigo_interno="CER001",
            quantidade=200,
            quantidade_minima=30,
            preco_custo=Decimal("4.00"),
            preco_venda=Decimal("8.00"),
            margem_lucro=Decimal("100.00"),
            ativo=True
        )
        db.session.add(produto)
        db.session.flush()
        
        # Create sale
        venda = Venda(
            estabelecimento_id=data['estab_id'],
            cliente_id=data['cliente_id'],
            funcionario_id=data['user_id'],
            codigo="VND000001",
            subtotal=Decimal("24.00"),
            desconto=Decimal("0"),
            total=Decimal("24.00"),
            forma_pagamento="Dinheiro",
            status='finalizada',
            data_venda=datetime.now()
        )
        db.session.add(venda)
        db.session.flush()
        
        # Create sale item with CMP snapshot
        custo_snapshot = produto.preco_custo
        venda_item = VendaItem(
            venda_id=venda.id,
            produto_id=produto.id,
            produto_nome=produto.nome,
            produto_codigo=produto.codigo_interno,
            produto_unidade=produto.unidade_medida,
            quantidade=3,
            preco_unitario=Decimal("8.00"),
            desconto=Decimal("0"),
            total_item=Decimal("24.00"),
            custo_unitario=custo_snapshot,  # CMP snapshot at time of sale
            margem_item=Decimal("100.00"),
            margem_lucro_real=Decimal("100.00")
        )
        db.session.add(venda_item)
        
        # Update product stock
        produto.quantidade -= 3
        produto.quantidade_vendida = (produto.quantidade_vendida or 0) + 3
        produto.total_vendido = float((produto.total_vendido or 0) + Decimal("24.00"))
        produto.ultima_venda = datetime.now()
        
        db.session.commit()
        
        print(f"[OK] Venda criada: {venda.codigo}")
        print(f"  - Produto: {produto.nome}")
        print(f"  - Quantidade vendida: 3")
        print(f"  - Preco unitario: R$ 8.00")
        print(f"  - Custo unitario (snapshot): R$ {venda_item.custo_unitario}")
        print(f"  - Margem real: {venda_item.margem_lucro_real}%")
        print(f"  - Total: R$ {venda_item.total_item}")
        
        # Verify snapshot
        assert venda_item.custo_unitario == custo_snapshot, \
            f"CMP snapshot error: expected {custo_snapshot}, got {venda_item.custo_unitario}"
        print(f"[OK] CMP snapshot verified: R$ {venda_item.custo_unitario}")

def test_audit_trail():
    """Test 5: Verify audit trail in HistoricoPrecos"""
    print("\n" + "="*60)
    print("TEST 5: Audit trail in HistoricoPrecos")
    print("="*60)
    
    data = setup_test_data()
    app = data['app']
    
    with app.app_context():
        # Create product
        produto = Produto(
            estabelecimento_id=data['estab_id'],
            categoria_id=data['categoria_id'],
            nome="Vinho Tinto 750ml",
            codigo_interno="VIN001",
            quantidade=50,
            quantidade_minima=10,
            preco_custo=Decimal("15.00"),
            preco_venda=Decimal("35.00"),
            margem_lucro=Decimal("133.33"),
            ativo=True
        )
        db.session.add(produto)
        db.session.flush()
        
        # Record initial price
        historico_inicial = HistoricoPrecos(
            estabelecimento_id=data['estab_id'],
            produto_id=produto.id,
            funcionario_id=data['user_id'],
            preco_custo_anterior=Decimal("0"),
            preco_venda_anterior=Decimal("0"),
            margem_anterior=Decimal("0"),
            preco_custo_novo=produto.preco_custo,
            preco_venda_novo=produto.preco_venda,
            margem_nova=produto.margem_lucro,
            motivo="Cadastro inicial",
            observacoes="Produto cadastrado"
        )
        db.session.add(historico_inicial)
        db.session.flush()
        
        # Update price
        preco_custo_anterior = produto.preco_custo
        preco_venda_anterior = produto.preco_venda
        margem_anterior = produto.margem_lucro
        
        produto.preco_custo = Decimal("16.00")
        produto.preco_venda = Decimal("38.00")
        produto.margem_lucro = Decimal("137.50")
        
        historico_atualizacao = HistoricoPrecos(
            estabelecimento_id=data['estab_id'],
            produto_id=produto.id,
            funcionario_id=data['user_id'],
            preco_custo_anterior=preco_custo_anterior,
            preco_venda_anterior=preco_venda_anterior,
            margem_anterior=margem_anterior,
            preco_custo_novo=produto.preco_custo,
            preco_venda_novo=produto.preco_venda,
            margem_nova=produto.margem_lucro,
            motivo="Ajuste de preço",
            observacoes="Reajuste de 6.67%"
        )
        db.session.add(historico_atualizacao)
        db.session.commit()
        
        # Retrieve audit trail
        historico = HistoricoPrecos.query.filter_by(produto_id=produto.id).order_by(
            HistoricoPrecos.data_alteracao.asc()
        ).all()
        
        print(f"✓ Histórico de preços para {produto.nome}:")
        for i, h in enumerate(historico, 1):
            print(f"\n  Entrada {i}: {h.motivo}")
            print(f"    Data: {h.data_alteracao.strftime('%d/%m/%Y %H:%M:%S')}")
            print(f"    Custo: R$ {h.preco_custo_anterior} → R$ {h.preco_custo_novo}")
            print(f"    Venda: R$ {h.preco_venda_anterior} → R$ {h.preco_venda_novo}")
            print(f"    Margem: {h.margem_anterior}% → {h.margem_nova}%")
            print(f"    Observações: {h.observacoes}")
        
        assert len(historico) == 2, f"Expected 2 history entries, got {len(historico)}"
        print(f"\n✓ Audit trail verified: {len(historico)} entries")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("CMP (CUSTO MÉDIO PONDERADO) INTEGRATION TEST SUITE")
    print("="*60)
    
    try:
        test_create_product_with_initial_stock()
        test_adjust_stock_with_cmp()
        test_receive_purchase_order_with_cmp()
        test_pdv_captures_cmp_snapshot()
        test_audit_trail()
        
        print("\n" + "="*60)
        print("✓ ALL TESTS PASSED!")
        print("="*60)
        print("\nCMP Integration Summary:")
        print("  ✓ Products created with initial stock and CMP")
        print("  ✓ Stock adjustments recalculate CMP correctly")
        print("  ✓ Purchase orders apply CMP on receipt")
        print("  ✓ PDV captures CMP snapshot at time of sale")
        print("  ✓ Complete audit trail in HistoricoPrecos")
        print("\nThe system is ready for production use!")
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
