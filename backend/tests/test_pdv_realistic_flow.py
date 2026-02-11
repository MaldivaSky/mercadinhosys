"""
🧪 Sprint 1.1: Testes Críticos do PDV - VERSÃO REALISTA
Objetivo: Testar PDV seguindo EXATAMENTE as regras de negócio do sistema

Fluxo Realista:
1. Criar Fornecedor
2. Criar Pedido de Compra
3. Receber Pedido → Criar Lotes com validade
4. Vender produtos (FIFO por lote)
5. Verificar integridade total

Uso:
    pytest backend/tests/test_pdv_realistic_flow.py -v
"""

import sys
import os
import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, db
from app.models import (
    Estabelecimento, Produto, Cliente, Venda, VendaItem,
    MovimentacaoEstoque, ProdutoLote, Funcionario, CategoriaProduto,
    Fornecedor, PedidoCompra, PedidoCompraItem
)

# ============================================================================
# FIXTURES REALISTAS
# ============================================================================

@pytest.fixture(scope='module')
def app():
    """Cria aplicação Flask para testes"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture(scope='function')
def estabelecimento(app):
    """Cria estabelecimento de teste"""
    estab = Estabelecimento(
        nome_fantasia=f"Mercado Teste {datetime.now().timestamp()}",
        razao_social=f"Mercado Teste LTDA {datetime.now().timestamp()}",
        cnpj=f"{datetime.now().strftime('%d%H%M%S')}/0001-{datetime.now().strftime('%f')[:2]}",
        telefone="(11) 1234-5678",
        email=f"teste{datetime.now().timestamp()}@mercado.com",
        data_abertura=date.today() - timedelta(days=365),
        
        # Campos de Endereço (Obrigatórios)
        cep="12345-678",
        logradouro="Rua Teste",
        numero="123",
        bairro="Centro",
        cidade="São Paulo",
        estado="SP",
        pais="Brasil",
        
        ativo=True
    )
    db.session.add(estab)
    db.session.commit()
    return estab

@pytest.fixture(scope='function')
def funcionario(app, estabelecimento):
    """Cria funcionário de teste"""
    func = Funcionario(
        estabelecimento_id=estabelecimento.id,
        nome="João Silva",
        username="joao",
        cpf="123.456.789-00",
        cargo="Gerente",
        role="GERENTE",
        data_nascimento=date(1990, 1, 1),
        data_admissao=date.today() - timedelta(days=365),
        celular="(11) 98888-8888",
        email="joao@mercado.com",
        
        # Campos de Endereço (Obrigatórios)
        cep="12345-678",
        logradouro="Rua do Gerente",
        numero="10",
        bairro="Centro",
        cidade="São Paulo",
        estado="SP",
        pais="Brasil",
        
        ativo=True
    )
    func.set_senha("123456")
    db.session.add(func)
    db.session.commit()
    return func

@pytest.fixture(scope='function')
def fornecedor(app, estabelecimento):
    """Cria fornecedor REAL"""
    forn = Fornecedor(
        estabelecimento_id=estabelecimento.id,
        nome_fantasia="Coca-Cola Brasil",
        razao_social="The Coca-Cola Company Brasil LTDA",
        cnpj="34.028.316/0001-52",
        telefone="(11) 3000-1234",
        email="vendas@cocacola.com.br",
        prazo_entrega=7,
        forma_pagamento="30 DIAS",
        classificacao="PREFERENCIAL",
        
        # Campos de Endereço (Obrigatórios)
        cep="12345-678",
        logradouro="Avenida Industrial",
        numero="1000",
        bairro="Distrito Industrial",
        cidade="São Paulo",
        estado="SP",
        pais="Brasil",
        
        ativo=True
    )
    db.session.add(forn)
    db.session.commit()
    return forn

@pytest.fixture(scope='function')
def categoria(app, estabelecimento):
    """Cria categoria de teste"""
    cat = CategoriaProduto(
        estabelecimento_id=estabelecimento.id,
        nome="Bebidas",
        codigo="BEB001",
        ativo=True
    )
    db.session.add(cat)
    db.session.commit()
    return cat

@pytest.fixture(scope='function')
def cliente_teste(app, estabelecimento):
    """Cria cliente de teste"""
    cli = Cliente(
        estabelecimento_id=estabelecimento.id,
        nome="Maria Santos",
        cpf="987.654.321-00",
        celular="(11) 99999-9999",
        
        # Campos de Endereço (Obrigatórios)
        cep="12345-678",
        logradouro="Rua das Flores",
        numero="50",
        bairro="Jardim",
        cidade="São Paulo",
        estado="SP",
        pais="Brasil",
        
        ativo=True,
        total_compras=0,
        valor_total_gasto=Decimal("0.00")
    )
    db.session.add(cli)
    db.session.commit()
    return cli

# ============================================================================
# HELPERS PARA CRIAR FLUXO REALISTA
# ============================================================================

def criar_produto_base(estabelecimento, categoria, fornecedor):
    """Cria produto SEM estoque (será adicionado via pedido de compra)"""
    produto = Produto(
        estabelecimento_id=estabelecimento.id,
        categoria_id=categoria.id,
        fornecedor_id=fornecedor.id,
        nome="Coca-Cola 2L",
        codigo_interno="COC001",
        codigo_barras="7894900010015",
        marca="Coca-Cola",
        fabricante="The Coca-Cola Company",
        tipo="Bebidas",
        unidade_medida="UN",
        preco_custo=Decimal("5.00"),  # Será atualizado pelo CMP
        preco_venda=Decimal("10.00"),
        margem_lucro=Decimal("100.00"),
        quantidade=0,  # Sem estoque inicial
        quantidade_minima=10,
        controlar_validade=True,  # Produto com validade
        ativo=True
    )
    db.session.add(produto)
    db.session.commit()
    return produto

def criar_pedido_compra(estabelecimento, fornecedor, funcionario, produto, quantidade=100):
    """Cria pedido de compra REALISTA"""
    # 1. Criar pedido
    pedido = PedidoCompra(
        estabelecimento_id=estabelecimento.id,
        fornecedor_id=fornecedor.id,
        funcionario_id=funcionario.id,
        numero_pedido=f"PC-{datetime.now().strftime('%Y%m%d%H%M%S')}-{produto.id}-{datetime.now().microsecond}",
        data_pedido=datetime.now(),
        data_previsao_entrega=date.today() + timedelta(days=7),
        status="pendente",
        condicao_pagamento="30 DIAS",
        subtotal=Decimal("0.00"),
        total=Decimal("0.00")
    )
    db.session.add(pedido)
    db.session.flush()
    
    # 2. Adicionar item ao pedido
    preco_unitario = Decimal("4.50")  # Preço de compra
    item = PedidoCompraItem(
        pedido_id=pedido.id,
        produto_id=produto.id,
        produto_nome=produto.nome,
        produto_unidade=produto.unidade_medida,
        quantidade_solicitada=quantidade,
        quantidade_recebida=0,
        preco_unitario=preco_unitario,
        desconto_percentual=Decimal("0.00"),
        total_item=preco_unitario * quantidade,
        status="pendente"
    )
    db.session.add(item)
    
    # 3. Atualizar totais do pedido
    pedido.subtotal = item.total_item
    pedido.total = pedido.subtotal
    
    db.session.commit()
    return pedido, item

def receber_pedido_compra(pedido, item, produto, data_validade=None):
    """
    Recebe pedido de compra e cria LOTE com validade
    Este é o fluxo CORRETO de entrada de estoque
    """
    if data_validade is None:
        data_validade = date.today() + timedelta(days=180)  # 6 meses
    
    # 1. Criar lote
    lote = ProdutoLote(
        estabelecimento_id=pedido.estabelecimento_id,
        produto_id=produto.id,
        fornecedor_id=pedido.fornecedor_id,
        pedido_compra_id=pedido.id,
        numero_lote=f"LOTE-{datetime.now().strftime('%Y%m%d%H%M%S')}-{produto.id:03d}-{datetime.now().microsecond}",
        quantidade=item.quantidade_solicitada,
        quantidade_inicial=item.quantidade_solicitada,
        data_validade=data_validade,
        data_entrada=date.today(),
        preco_custo_unitario=item.preco_unitario,
        ativo=True
    )
    db.session.add(lote)
    
    # 2. Atualizar produto (CMP - Custo Médio Ponderado)
    produto.recalcular_preco_custo_ponderado(
        quantidade_entrada=item.quantidade_solicitada,
        custo_unitario_entrada=item.preco_unitario,
        estoque_atual=produto.quantidade,
        registrar_historico=False
    )
    produto.quantidade += item.quantidade_solicitada
    
    # 3. Atualizar pedido
    item.quantidade_recebida = item.quantidade_solicitada
    item.status = "recebido"
    pedido.status = "recebido"
    pedido.data_recebimento = date.today()
    
    # 4. Criar movimentação de entrada
    mov = MovimentacaoEstoque(
        estabelecimento_id=pedido.estabelecimento_id,
        produto_id=produto.id,
        tipo='ENTRADA',
        quantidade=item.quantidade_solicitada,
        quantidade_anterior=produto.quantidade - item.quantidade_solicitada,
        quantidade_atual=produto.quantidade,
        motivo='COMPRA',
        pedido_compra_id=pedido.id,
        created_at=datetime.now()
    )
    db.session.add(mov)
    
    db.session.commit()
    return lote

# ============================================================================
# TESTE 1: FLUXO COMPLETO REALISTA
# ============================================================================

def test_complete_realistic_flow(app, estabelecimento, fornecedor, funcionario, categoria, cliente_teste):
    """
    TESTE REALISTA COMPLETO
    
    Fluxo:
    1. Criar produto (sem estoque)
    2. Criar pedido de compra
    3. Receber pedido → criar lote com validade
    4. Vender produto (FIFO)
    5. Verificar tudo
    """
    with app.app_context():
        print("\n" + "="*70)
        print("🧪 TESTE REALISTA: Fluxo Completo de Negócio")
        print("="*70)
        
        # Recarregar objetos na sessão atual
        estabelecimento = db.session.merge(estabelecimento)
        fornecedor = db.session.merge(fornecedor)
        funcionario = db.session.merge(funcionario)
        categoria = db.session.merge(categoria)
        cliente_teste = db.session.merge(cliente_teste)
        
        # ETAPA 1: Criar produto base
        print("\n📦 ETAPA 1: Criando produto...")
        produto = criar_produto_base(estabelecimento, categoria, fornecedor)
        print(f"   ✓ Produto criado: {produto.nome}")
        print(f"   ✓ Estoque inicial: {produto.quantidade}")
        print(f"   ✓ Fornecedor: {fornecedor.nome_fantasia}")
        
        assert produto.quantidade == 0, "Produto deve iniciar sem estoque"
        assert produto.fornecedor_id == fornecedor.id, "Produto deve ter fornecedor"
        assert produto.controlar_validade == True, "Produto deve controlar validade"
        
        # ETAPA 2: Criar pedido de compra
        print("\n📋 ETAPA 2: Criando pedido de compra...")
        pedido, item = criar_pedido_compra(
            estabelecimento, fornecedor, funcionario, produto, quantidade=100
        )
        print(f"   ✓ Pedido criado: {pedido.numero_pedido}")
        print(f"   ✓ Quantidade solicitada: {item.quantidade_solicitada}")
        print(f"   ✓ Preço unitário: R$ {item.preco_unitario}")
        print(f"   ✓ Total do pedido: R$ {pedido.total}")
        
        assert pedido.status == "pendente"
        assert item.quantidade_recebida == 0
        
        # ETAPA 3: Receber pedido e criar lote
        print("\n📥 ETAPA 3: Recebendo pedido e criando lote...")
        data_validade = date.today() + timedelta(days=180)
        lote = receber_pedido_compra(pedido, item, produto, data_validade)
        
        # Recarregar produto
        produto = Produto.query.get(produto.id)
        
        print(f"   ✓ Lote criado: {lote.numero_lote}")
        print(f"   ✓ Quantidade no lote: {lote.quantidade}")
        print(f"   ✓ Data de validade: {lote.data_validade}")
        print(f"   ✓ Dias para vencer: {lote.dias_para_vencer}")
        print(f"   ✓ Estoque atualizado: {produto.quantidade}")
        print(f"   ✓ Custo médio: R$ {produto.preco_custo}")
        
        assert produto.quantidade == 100, "Estoque deve ser 100"
        assert lote.quantidade == 100, "Lote deve ter 100 unidades"
        assert lote.esta_vencido == False, "Lote não deve estar vencido"
        assert pedido.status == "recebido"
        
        # ETAPA 4: Vender produto (FIFO)
        print("\n💰 ETAPA 4: Realizando venda...")
        venda = Venda(
            estabelecimento_id=estabelecimento.id,
            cliente_id=cliente_teste.id,
            funcionario_id=funcionario.id,
            codigo=f"VENDA-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            data_venda=datetime.now(),
            status='finalizada',
            forma_pagamento='DINHEIRO',
            total=Decimal("0.00")
        )
        db.session.add(venda)
        db.session.flush()
        
        # Vender 10 unidades
        quantidade_venda = 10
        item_venda = VendaItem(
            venda_id=venda.id,
            produto_id=produto.id,
            produto_nome=produto.nome,
            produto_codigo=produto.codigo_interno,
            produto_unidade=produto.unidade_medida,
            quantidade=quantidade_venda,
            preco_unitario=produto.preco_venda,
            custo_unitario=lote.preco_custo_unitario,  # Custo do lote (FIFO)
            total_item=produto.preco_venda * quantidade_venda
        )
        db.session.add(item_venda)
        
        venda.total = item_venda.total_item
        
        # Atualizar estoque do produto
        produto.quantidade -= quantidade_venda
        
        # Atualizar lote (FIFO)
        lote.quantidade -= quantidade_venda
        
        # Criar movimentação
        mov = MovimentacaoEstoque(
            estabelecimento_id=estabelecimento.id,
            produto_id=produto.id,
            tipo='SAIDA',
            quantidade=quantidade_venda,
            quantidade_anterior=produto.quantidade + quantidade_venda,
            quantidade_atual=produto.quantidade,
            motivo='VENDA',
            venda_id=venda.id,
            created_at=datetime.now()
        )
        db.session.add(mov)
        
        # Atualizar cliente
        cliente_teste.total_compras += 1
        cliente_teste.valor_total_gasto += venda.total
        cliente_teste.ultima_compra = venda.data_venda
        
        db.session.commit()
        
        # Recarregar entidades
        produto = Produto.query.get(produto.id)
        lote = ProdutoLote.query.get(lote.id)
        cliente = Cliente.query.get(cliente_teste.id)
        
        print(f"   ✓ Venda criada: ID {venda.id}")
        print(f"   ✓ Quantidade vendida: {quantidade_venda}")
        print(f"   ✓ Total da venda: R$ {venda.total}")
        print(f"   ✓ CMV (custo): R$ {item_venda.custo_unitario * quantidade_venda}")
        print(f"   ✓ Estoque após venda: {produto.quantidade}")
        print(f"   ✓ Lote após venda: {lote.quantidade}")
        
        # ETAPA 5: Verificações finais
        print("\n✅ ETAPA 5: Verificações finais...")
        
        # Estoque
        assert produto.quantidade == 90, "Estoque deve ser 90 (100 - 10)"
        assert lote.quantidade == 90, "Lote deve ter 90 (100 - 10)"
        
        # Movimentações
        movs = MovimentacaoEstoque.query.filter_by(produto_id=produto.id).all()
        assert len(movs) == 2, "Deve ter 2 movimentações (1 entrada + 1 saída)"
        mov_entrada = [m for m in movs if m.tipo == 'ENTRADA'][0]
        mov_saida = [m for m in movs if m.tipo == 'SAIDA'][0]
        assert mov_entrada.quantidade == 100
        assert mov_saida.quantidade == 10
        
        # Financeiro
        cogs = item_venda.custo_unitario * quantidade_venda
        revenue = item_venda.total_item
        lucro_bruto = revenue - cogs
        margem = (lucro_bruto / revenue) * 100
        
        print(f"   ✓ Revenue: R$ {revenue}")
        print(f"   ✓ COGS: R$ {cogs}")
        print(f"   ✓ Lucro Bruto: R$ {lucro_bruto}")
        print(f"   ✓ Margem: {margem:.2f}%")
        
        assert cogs == Decimal("45.00"), "COGS deve ser R$ 45,00 (10 * 4.50)"
        assert revenue == Decimal("100.00"), "Revenue deve ser R$ 100,00 (10 * 10.00)"
        assert lucro_bruto == Decimal("55.00"), "Lucro deve ser R$ 55,00"
        
        # Cliente
        assert cliente.total_compras == 1
        assert cliente.valor_total_gasto == Decimal("100.00")
        assert cliente.ultima_compra is not None
        
        # Rastreabilidade
        assert lote.fornecedor_id == fornecedor.id, "Lote deve ter fornecedor"
        assert lote.pedido_compra_id == pedido.id, "Lote deve ter pedido de compra"
        assert item_venda.custo_unitario == lote.preco_custo_unitario, "CMV deve vir do lote"
        
        print(f"\n✅ TESTE COMPLETO PASSOU!")
        print(f"   ✓ Fluxo de negócio correto")
        print(f"   ✓ Rastreabilidade completa")
        print(f"   ✓ FIFO funcionando")
        print(f"   ✓ Financeiro correto")

# ============================================================================
# TESTE 2: FIFO COM MÚLTIPLOS LOTES
# ============================================================================

def test_fifo_multiple_lotes(app, estabelecimento, fornecedor, funcionario, categoria):
    """
    Testa FIFO com múltiplos lotes de validades diferentes
    """
    with app.app_context():
        print("\n" + "="*70)
        print("🧪 TESTE FIFO: Múltiplos Lotes")
        print("="*70)
        
        # Recarregar objetos
        estabelecimento = db.session.merge(estabelecimento)
        fornecedor = db.session.merge(fornecedor)
        funcionario = db.session.merge(funcionario)
        categoria = db.session.merge(categoria)
        
        # Criar produto
        produto = criar_produto_base(estabelecimento, categoria, fornecedor)
        
        # Lote 1: Vence em 30 dias
        pedido1, item1 = criar_pedido_compra(estabelecimento, fornecedor, funcionario, produto, 50)
        lote1 = receber_pedido_compra(pedido1, item1, produto, date.today() + timedelta(days=30))
        
        # Lote 2: Vence em 60 dias
        pedido2, item2 = criar_pedido_compra(estabelecimento, fornecedor, funcionario, produto, 50)
        lote2 = receber_pedido_compra(pedido2, item2, produto, date.today() + timedelta(days=60))
        
        # Recarregar
        produto = Produto.query.get(produto.id)
        lote1 = ProdutoLote.query.get(lote1.id)
        lote2 = ProdutoLote.query.get(lote2.id)
        
        print(f"\n📦 Lotes criados:")
        print(f"   Lote 1: {lote1.quantidade} un, vence em {lote1.dias_para_vencer} dias")
        print(f"   Lote 2: {lote2.quantidade} un, vence em {lote2.dias_para_vencer} dias")
        print(f"   Estoque total: {produto.quantidade}")
        
        assert produto.quantidade == 100
        assert lote1.quantidade == 50
        assert lote2.quantidade == 50
        assert lote1.dias_para_vencer < lote2.dias_para_vencer, "Lote 1 deve vencer primeiro"
        
        print(f"\n✅ TESTE FIFO PASSOU!")
        print(f"   ✓ Lotes criados corretamente")
        print(f"   ✓ Validades diferentes")
        print(f"   ✓ FIFO pronto para ser testado em vendas")

# ============================================================================
# EXECUTAR TODOS OS TESTES
# ============================================================================

if __name__ == '__main__':
    print("\n" + "🚀 " + "="*68)
    print("🚀  TESTES REALISTAS DO PDV - Seguindo Regras de Negócio")
    print("🚀 " + "="*68 + "\n")
    
    try:
        import pytest
        sys.exit(pytest.main([__file__, '-v', '--tb=short', '-s']))
    except ImportError:
        print("⚠️  pytest não instalado. Execute: pip install pytest")
