from app import create_app, db
from app.models import Produto, Estabelecimento, Fornecedor, Venda, VendaItem, CategoriaProduto, Despesa
from datetime import datetime, timedelta
import random
from decimal import Decimal

app = create_app()

with app.app_context():
    estab_id = 1 # Assumindo ID 1 (Mercadinho)
    
    print("=== INICIANDO CORREÇÃO DE DADOS V2 (DASHBOARD + DESPESAS) ===")
    
    produtos = Produto.query.filter_by(estabelecimento_id=estab_id).all()
    print(f"Encontrados {len(produtos)} produtos.")
    
    if not produtos:
        print("ERRO: NENHUM PRODUTO ENCONTRADO! Rode o seed primeiro.")
        exit()

    from app.models import Funcionario, Cliente
    
    funcionarios_list = Funcionario.query.filter_by(estabelecimento_id=estab_id).all()
    clientes_list = Cliente.query.filter_by(estabelecimento_id=estab_id).all()
    
    # 0. Limpeza Prévia (Evitar duplicação)
    print("Limpando dados antigos de Vendas e Despesas...")
    try:
        db.session.query(VendaItem).delete()
        db.session.query(Venda).delete()
        db.session.query(Despesa).delete()
        db.session.commit()
        print("Dados limpos com sucesso.")
    except Exception as e:
        db.session.rollback()
        print(f"Aviso ao limpar dados: {e}")

    # 1. Distribuir Fornecedores
    fornecedores = Fornecedor.query.filter_by(estabelecimento_id=estab_id).all()
    print(f"Fornecedores atuais: {len(fornecedores)}")
    
    if len(fornecedores) < 3:
        print("Criando fornecedores fictícios...")
        novos = [
            Fornecedor(nome_fantasia="Distribuidora Alpha", razao_social="Dist Alpha LTDA", cnpj="12345678000191", telefone="11999999991", email="a@teste.com", estabelecimento_id=estab_id, cep="01001000", logradouro="Rua A", numero="1", bairro="Centro", cidade="São Paulo", estado="SP"),
            Fornecedor(nome_fantasia="Atacadão Beta", razao_social="Atacado Beta SA", cnpj="98765432000182", telefone="11888888882", email="b@teste.com", estabelecimento_id=estab_id, cep="01001000", logradouro="Rua B", numero="2", bairro="Centro", cidade="São Paulo", estado="SP"),
            Fornecedor(nome_fantasia="Fornecedor Gamma", razao_social="Forn Gamma ME", cnpj="11223344000153", telefone="11777777773", email="c@teste.com", estabelecimento_id=estab_id, cep="01001000", logradouro="Rua C", numero="3", bairro="Centro", cidade="São Paulo", estado="SP")
        ]
        for f in novos:
            db.session.add(f)
        db.session.commit()
        fornecedores = Fornecedor.query.filter_by(estabelecimento_id=estab_id).all()
    
    print(f"Distribuindo produtos entre {len(fornecedores)} fornecedores...")
    for p in produtos:
        if fornecedores:
            p.fornecedor = random.choice(fornecedores)
    
    # 2. Criar Cenários de Estoque (Críticos)
    qtd_esgotados = int(len(produtos) * 0.1)
    qtd_baixo = int(len(produtos) * 0.2)
    
    random.shuffle(produtos)
    
    for i, p in enumerate(produtos):
        p.quantidade_minima = random.randint(5, 20)
        
        if i < qtd_esgotados:
            p.quantidade = 0
        elif i < qtd_esgotados + qtd_baixo:
            p.quantidade = random.randint(1, p.quantidade_minima)
        else:
            p.quantidade = random.randint(p.quantidade_minima + 1, 100)
            
        # Adicionar validade aleatória (alguns vencidos, alguns próximos, alguns longe)
        dias_validade = random.randint(-10, 365)
        p.data_validade = datetime.now().date() + timedelta(days=dias_validade)
        p.controlar_validade = True
            
        # Margem Lucro
        custo = round(random.uniform(5.0, 50.0), 2)
        margem = random.uniform(20.0, 150.0)
        venda = round(custo * (1 + margem/100), 2)
        
        p.preco_custo = Decimal(str(custo))
        p.preco_venda = Decimal(str(venda))
        p.margem_lucro = Decimal(str(round(margem, 2)))
        
    db.session.commit()
    print("Estoques e Preços atualizados.")
    
    # 3. Gerar Vendas (para ABC e Giro)
    # IMPORTANTE: Vendas antigas não deletadas para acumular histórico. Mas cuidado com duplicação excessiva.
    # Vou deletar vendas apenas deste teste (se possível identificar, mas aqui vou assumir que é seguro limpar TUDO de vendas se tiver poucas, ou adicionar novas)
    # Melhor adicionar novas para garantir volume.
    
    num_vendas = 150
    print(f"Gerando {num_vendas} vendas novas...")
    
    for _ in range(num_vendas):
        if _ < 20: # Garantir 20 vendas HOJE para o dashboard "Hoje" funcionar
            dias_atras = 0
        else:
            dias_atras = random.randint(0, 60)
        data_venda = datetime.now() - timedelta(days=dias_atras)
        valor_total = 0
        
        # Obter funcionário e cliente aleatórios
        funcionario = random.choice(funcionarios_list) if funcionarios_list else None
        cliente = random.choice(clientes_list) if clientes_list else None
        
        # Gerar código único
        codigo_venda = f"VND-{datetime.now().strftime('%Y%m%d')}-{random.randint(10000, 99999)}-{_}"
        
        venda = Venda(
            estabelecimento_id=estab_id,
            codigo=codigo_venda,
            data_venda=data_venda,
            status="finalizada",
            forma_pagamento="Dinheiro",
            funcionario_id=funcionario.id if funcionario else None, # Ajustado abaixo se None
            cliente_id=cliente.id if cliente else None,
            subtotal=0, # Será atualizado
            total=0     # Será atualizado
        )
        
        # Fallback se não tiver funcionário (não deveria acontecer se seed rodou)
        if not venda.funcionario_id:
             # Criar um dummy se precisar, mas melhor abortar ou assumir ID 1
             # Vamos assumir que existe ID 1
             venda.funcionario_id = 1
             
        db.session.add(venda)
        db.session.flush()
        
        num_itens = random.randint(1, 5)
        itens_venda = random.sample(produtos, num_itens)
        
        for prod in itens_venda:
            qtd = random.randint(1, 4)
            preco = float(prod.preco_venda)
            subtotal = qtd * preco
            
            item = VendaItem(
                venda_id=venda.id,
                produto_id=prod.id,
                quantidade=qtd,
                preco_unitario=preco,
                total_item=subtotal,
                custo_unitario=prod.preco_custo,
                produto_nome=prod.nome,
                produto_unidade=prod.unidade_medida or 'UN'
            )
            valor_total += subtotal
            
            # Atualizar stats
            prod.total_vendido = (float(prod.total_vendido) if prod.total_vendido else 0.0) + subtotal
            prod.quantidade_vendida = (int(prod.quantidade_vendida) if prod.quantidade_vendida else 0) + qtd
            
            if not prod.ultima_venda or prod.ultima_venda < data_venda:
                prod.ultima_venda = data_venda
                
            db.session.add(item)
        
        # Tentar setar total/valor_total
        if hasattr(venda, 'total'):
            venda.total = valor_total
        if hasattr(venda, 'valor_total'):
            venda.valor_total = valor_total
            
    db.session.commit()
    
    # 4. Atualizar Classificação ABC
    print("Atualizando Classificação ABC...")
    try:
        Produto.atualizar_classificacoes_abc(estab_id)
        db.session.commit()
        print("Classificação ABC OK.")
    except Exception as e:
        print(f"Erro ABC: {e}")

    # 5. Gerar Despesas
    print("Gerando Despesas Fictícias...")
    # Limpar despesas antigas para evitar poluição excessiva no teste repetitivo?
    # db.session.query(Despesa).filter_by(estabelecimento_id=estab_id).delete()
    
    despesas_fixas = [
        {"desc": "Aluguel Loja", "val": 2500.00, "cat": "Infraestrutura", "tipo": "fixa"},
        {"desc": "Internet Fibra", "val": 150.00, "cat": "Infraestrutura", "tipo": "fixa"},
        {"desc": "Energia Elétrica", "val": 650.00, "cat": "Infraestrutura", "tipo": "variavel"},
        {"desc": "Água e Esgoto", "val": 120.00, "cat": "Infraestrutura", "tipo": "variavel"},
        {"desc": "Marketing Digital", "val": 400.00, "cat": "Marketing", "tipo": "variavel"},
        {"desc": "Material de Limpeza", "val": 200.00, "cat": "Operacional", "tipo": "variavel"},
        {"desc": "Manutenção Computadores", "val": 350.00, "cat": "Manutenção", "tipo": "variavel"},
    ]
    
    # Gerar para últimos 3 meses
    for i in range(3): 
        # Mês referência
        data_base = datetime.now() - timedelta(days=30*i)
        
        for d in despesas_fixas:
            valor = d["val"] * random.uniform(0.9, 1.1)
            dia = random.randint(1, 28)
            
            # Garantir data válida
            try:
                data_despesa = data_base.replace(day=dia).date()
            except:
                data_despesa = data_base.date()
                
            nova_despesa = Despesa(
                estabelecimento_id=estab_id,
                descricao=f"{d['desc']}",
                categoria=d["cat"],
                tipo=d["tipo"],
                valor=Decimal(str(round(valor, 2))),
                data_despesa=data_despesa,
                recorrente=d["tipo"] == "fixa",
                forma_pagamento="Boleto" if valor > 500 else "Pix",
                observacoes="Gerado automaticamente"
            )
            db.session.add(nova_despesa)
            
    db.session.commit()
    print("Despesas geradas com sucesso.")
    
    print("=== FINALIZADO COM SUCESSO ===")
