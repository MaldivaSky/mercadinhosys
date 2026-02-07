"""
Seed Rápido para Neon PostgreSQL
Cria apenas dados essenciais para testar o sistema
"""
import os
import sys
import random
from datetime import datetime, date, timedelta
from decimal import Decimal
from dotenv import load_dotenv
from urllib.parse import urlparse
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Carregar .env
load_dotenv()

# Detectar URL do banco: Neon (prioridade) ou SQLite local
target_url = os.environ.get('NEON_DATABASE_URL') or os.environ.get('DATABASE_URL_ORIG') or os.environ.get('NEON_DB_URL') or os.environ.get('DB_PRIMARY') or os.environ.get('DATABASE_URL_TARGET')

# Se não tiver URL do Neon, usa SQLite local como fallback
if not target_url:
    fallback_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'mercadinhosys_seed.sqlite'))
    local_db_url = f"sqlite:///{fallback_path.replace('\\', '/')}"
    os.environ['DATABASE_URL'] = local_db_url
    print(f"[LOCAL SEED] Usando SQLite: {local_db_url}")
else:
    # Ajustar protocolo postgres:// para postgresql:// se necessário
    if target_url.startswith("postgres://"):
        target_url = target_url.replace("postgres://", "postgresql://", 1)
    
    # IMPORTANTE: Configurar DATABASE_URL para que o create_app() use o Neon
    os.environ['DATABASE_URL'] = target_url
    print(f"[NEON SEED] Usando PostgreSQL: {target_url.split('@')[1] if '@' in target_url else target_url}")

from app import create_app, db
from app.models import (
    Estabelecimento, Configuracao, Funcionario, LoginHistory, Cliente, Fornecedor,
    CategoriaProduto, Produto, Despesa, RegistroPonto, ConfiguracaoHorario,
    Caixa, Venda, VendaItem, Pagamento, MovimentacaoEstoque, MovimentacaoCaixa, DashboardMetrica
)
from werkzeug.security import generate_password_hash

print("=" * 60)
print("SEED NEON RAPIDO")
print("=" * 60)
print()

# Validação inicial do DESTINO Neon (se fornecido)
if target_url and target_url.startswith('postgresql://'):
    try:
        engine_test = create_engine(target_url)
        with engine_test.connect() as conn:
            conn.execute(text("SELECT 1"))
        parsed = urlparse(target_url)
        print(f"✅ Conexão com Neon verificada (host: {parsed.hostname})")
    except Exception as e:
        parsed = urlparse(target_url)
        host_info = parsed.hostname or "desconhecido"
        print(f"❌ Falha ao conectar no Neon ({host_info}).")
        print("   Verifique a URL de conexão do Neon (Dashboard > Connection string).")
        print("   Exemplo: postgresql://USUARIO:SENHA@SEU_HOST.neon.tech/SEU_DB?sslmode=require&channel_binding=require")
        print("   Dica: não use placeholders como 'host.neon.tech'; use o host real do seu projeto.")
        print(f"   Erro: {str(e)[:200]}")
        # Não aborta o seed local; apenas marcar que a replicação será pulada
        target_url = ""

app = create_app()

with app.app_context():
    try:
        print("🔧 Garantindo schema do banco...")
        db.create_all()
        print("✅ Tabelas criadas (se necessário)")
        
        print("⚠️  Este seed cria apenas dados essenciais (rápido)")
        print()
        proceed = False
        auto = os.environ.get('SEED_CONFIRM', '').lower()
        if auto in ('s', 'y', 'yes', 'true', '1'):
            proceed = True
        elif not sys.stdin.isatty():
            proceed = True
        else:
            try:
                resposta = input("Deseja continuar? (s/N): ").lower()
                proceed = (resposta == 's')
            except Exception:
                proceed = False
        if not proceed:
            print("❌ Cancelado")
            sys.exit(0)
        
        print()
        print("Limpando banco...")
        
        # Dropar todas as tabelas e recriar (mais seguro para PostgreSQL)
        try:
            from sqlalchemy import text
            
            # Detectar se é SQLite
            is_sqlite = 'sqlite' in str(db.engine.url)
            
            if not is_sqlite:
                # Desabilitar constraints apenas no Postgres
                db.session.execute(text("SET session_replication_role = 'replica'"))
            
            # Dropar tabelas em ordem
            tables_to_drop = [
                "movimentacoes_estoque", "registro_ponto", "configuracao_horario",
                "produtos", "categorias_produto", "fornecedores", "clientes",
                "funcionarios", "estabelecimentos", "despesas"
            ]
            
            for table in tables_to_drop:
                try:
                    if is_sqlite:
                        # SQLite não suporta CASCADE no DROP TABLE padrão, mas foreign_keys=OFF ajuda
                        db.session.execute(text(f"DROP TABLE IF EXISTS {table}"))
                    else:
                        db.session.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                except Exception as e:
                    print(f"Erro ao dropar {table}: {e}")

            if not is_sqlite:
                db.session.execute(text("SET session_replication_role = 'origin'"))
                
            db.session.commit()
            print("Tabelas removidas")
            
            # Recriar tabelas
            db.create_all()
            db.session.commit()
            print("Tabelas criadas")
        except Exception as e:
            print(f"Aviso na limpeza: {e}")
            db.create_all()
            db.session.commit()
        
        print()
        
        # 1. ESTABELECIMENTO
        print("🏢 Criando estabelecimento...")
        
        # Check if exists to avoid Unique Constraint Error if drop failed
        est = Estabelecimento.query.filter_by(cnpj="12.345.678/0001-90").first()
        
        if not est:
            est = Estabelecimento(
                nome_fantasia="Mercado Souza Center",
                razao_social="Mercado Souza Center LTDA",
                cnpj="12.345.678/0001-90",
                inscricao_estadual="ISENTO",
                telefone="(84) 3234-5678",
                email="contato@mercadosouza.com",
                cep="59000-000",
                logradouro="Rua Principal",
                numero="123",
                bairro="Centro",
                cidade="Natal",
                estado="RN",
                pais="Brasil",
                regime_tributario="SIMPLES NACIONAL",
                ativo=True,
                data_abertura=date.today() - timedelta(days=365),
                data_cadastro=datetime.now()
            )
            db.session.add(est)
            db.session.flush()
            print(f"✅ {est.nome_fantasia}")
        else:
            print(f"ℹ️ {est.nome_fantasia} já existe (pulando criação)")
        
        # 2. FUNCIONÁRIOS
        print()
        print("👥 Criando funcionários...")
        
        admin = Funcionario(
            estabelecimento_id=est.id,
            nome="Administrador Sistema",
            username="admin",
            senha_hash=generate_password_hash("admin123"),
            email="admin@empresa.com",
            cpf="111.222.333-44",
            rg="RN-12345678",
            data_nascimento=date(1985, 1, 1),
            telefone="(84) 91234-5678",
            celular="(84) 91234-5678",
            cargo="Gerente",
            role="ADMIN",
            ativo=True,
            status="ativo",
            data_admissao=date.today(),
            salario_base=Decimal("3500.00"),
            cep="59000-000",
            logradouro="Rua Principal",
            numero="100",
            bairro="Centro",
            cidade="Natal",
            estado="RN",
            pais="Brasil",
            permissoes_json='{"pdv":true,"estoque":true,"compras":true,"financeiro":true,"configuracoes":true,"relatorios":true}'
        )
        db.session.add(admin)
        print(f"  ✅ {admin.nome} (admin/admin123)")
        
        joao = Funcionario(
            estabelecimento_id=est.id,
            nome="João Silva",
            username="joao",
            senha_hash=generate_password_hash("joao123"),
            email="joao@empresa.com",
            cpf="222.333.444-55",
            rg="RN-87654321",
            data_nascimento=date(1990, 5, 15),
            telefone="(84) 92345-6789",
            celular="(84) 92345-6789",
            cargo="Vendedor",
            role="FUNCIONARIO",
            ativo=True,
            status="ativo",
            data_admissao=date.today(),
            salario_base=Decimal("1850.00"),
            cep="59000-000",
            logradouro="Rua Secundária",
            numero="200",
            bairro="Centro",
            cidade="Natal",
            estado="RN",
            pais="Brasil",
            permissoes_json='{"pdv":true,"estoque":false}'
        )
        db.session.add(joao)
        print(f"  ✅ {joao.nome} (joao/joao123)")
        
        db.session.flush()
        
        # 3. CLIENTES
        print()
        print("🛒 Criando clientes...")
        
        clientes_data = [
            {"nome": "Maria Santos", "cpf": "333.444.555-66", "email": "maria@email.com", "telefone": "(84) 93456-7890", "celular": "(84) 93456-7890",
             "cep": "59000-001", "logradouro": "Rua das Flores", "numero": "10", "bairro": "Centro", "cidade": "Natal", "estado": "RN"},
            {"nome": "Pedro Oliveira", "cpf": "444.555.666-77", "email": "pedro@email.com", "telefone": "(84) 94567-8901", "celular": "(84) 94567-8901",
             "cep": "59000-002", "logradouro": "Av. Brasil", "numero": "200", "bairro": "Tirol", "cidade": "Natal", "estado": "RN"},
            {"nome": "Ana Costa", "cpf": "555.666.777-88", "email": "ana@email.com", "telefone": "(84) 95678-9012", "celular": "(84) 95678-9012",
             "cep": "59000-003", "logradouro": "Rua Projetada", "numero": "300", "bairro": "Lagoa Nova", "cidade": "Natal", "estado": "RN"},
        ]
        
        for c_data in clientes_data:
            cliente = Cliente(
                estabelecimento_id=est.id,
                nome=c_data["nome"],
                cpf=c_data["cpf"],
                email=c_data["email"],
                telefone=c_data["telefone"],
                celular=c_data["celular"],
                cep=c_data["cep"],
                logradouro=c_data["logradouro"],
                numero=c_data["numero"],
                bairro=c_data["bairro"],
                cidade=c_data["cidade"],
                estado=c_data["estado"],
                ativo=True
            )
            db.session.add(cliente)
            print(f"  ✅ {cliente.nome}")
        
        db.session.flush()
        
        # 4. FORNECEDORES
        print()
        print("🚚 Criando fornecedores...")
        
        fornecedores_data = [
            {"nome": "Distribuidora ABC", "cnpj": "11.222.333/0001-44", "telefone": "(84) 3111-2222",
             "cep": "59010-000", "logradouro": "Rua dos Comerciantes", "numero": "50", "bairro": "Alecrim", "cidade": "Natal", "estado": "RN"},
            {"nome": "Atacado XYZ", "cnpj": "22.333.444/0001-55", "telefone": "(84) 3222-3333",
             "cep": "59020-000", "logradouro": "Av. Sete", "numero": "120", "bairro": "Cidade Alta", "cidade": "Natal", "estado": "RN"},
        ]
        
        fornecedores = []
        for f_data in fornecedores_data:
            fornecedor = Fornecedor(
                estabelecimento_id=est.id,
                nome_fantasia=f_data["nome"],
                razao_social=f"{f_data['nome']} LTDA",
                cnpj=f_data["cnpj"],
                telefone=f_data["telefone"],
                email=f"{f_data['nome'].lower().replace(' ', '')}@email.com",
                cep=f_data["cep"],
                logradouro=f_data["logradouro"],
                numero=f_data["numero"],
                bairro=f_data["bairro"],
                cidade=f_data["cidade"],
                estado=f_data["estado"],
                ativo=True
            )
            db.session.add(fornecedor)
            fornecedores.append(fornecedor)
            print(f"  ✅ {fornecedor.nome_fantasia}")
        
        db.session.flush()
        
        # 5. CATEGORIAS
        print()
        print("📁 Criando categorias...")
        
        categorias_data = ["Alimentos", "Bebidas", "Limpeza", "Higiene", "Padaria"]
        categorias = []
        
        for cat_nome in categorias_data:
            categoria = CategoriaProduto(
                estabelecimento_id=est.id,
                nome=cat_nome,
                ativo=True
            )
            db.session.add(categoria)
            categorias.append(categoria)
            print(f"  ✅ {categoria.nome}")
        
        db.session.flush()
        
        # 6. PRODUTOS
        print()
        print("📦 Criando produtos...")
        
        produtos_data = [
            ("Arroz Tipo 1 5kg", 0, 0, "7891234567890", 15.00, 22.90, 50),
            ("Feijão Preto 1kg", 0, 0, "7891234567891", 5.50, 8.90, 80),
            ("Açúcar Cristal 1kg", 0, 0, "7891234567892", 3.20, 4.99, 100),
            ("Refrigerante 2L", 1, 1, "7891234567893", 4.50, 7.99, 60),
            ("Água Mineral 1.5L", 1, 1, "7891234567894", 1.20, 2.50, 120),
            ("Detergente Líquido", 2, 0, "7891234567895", 1.80, 2.99, 90),
            ("Sabão em Pó 1kg", 2, 0, "7891234567896", 8.50, 12.90, 40),
            ("Shampoo 400ml", 3, 1, "7891234567897", 6.00, 9.99, 35),
            ("Sabonete 90g", 3, 1, "7891234567898", 1.50, 2.49, 150),
            ("Pão Francês kg", 4, 0, "7891234567899", 8.00, 12.00, 20),
        ]
        
        for nome, cat_idx, forn_idx, codigo, custo, venda, qtd in produtos_data:
            produto = Produto(
                estabelecimento_id=est.id,
                nome=nome,
                codigo_barras=codigo,
                categoria_id=categorias[cat_idx].id,
                fornecedor_id=fornecedores[forn_idx].id,
                preco_custo=Decimal(str(custo)),
                preco_venda=Decimal(str(venda)),
                quantidade=qtd,
                unidade_medida="UN",
                ativo=True
            )
            db.session.add(produto)
            print(f"  ✅ {produto.nome} - R$ {produto.preco_venda}")
        
        # COMMIT PRODUTOS
        print()
        print("💾 Salvando produtos...")
        db.session.commit()
        print("✅ Produtos salvos!")
        
        # 7. DESPESAS
        print()
        print("💸 Criando despesas...")
        hoje = date.today()
        primeiro_dia_mes = hoje.replace(day=1)
        despesas_data = [
            {"descricao": "Salários Funcionários", "categoria": "salarios", "tipo": "fixa", "valor": Decimal("6000.00"), "recorrente": True, "forma_pagamento": "transferencia"},
            {"descricao": "Aluguel do Estabelecimento", "categoria": "aluguel", "tipo": "fixa", "valor": Decimal("3500.00"), "recorrente": True, "forma_pagamento": "transferencia"},
            {"descricao": "Conta de Energia", "categoria": "energia", "tipo": "variavel", "valor": Decimal("1200.00"), "recorrente": True, "forma_pagamento": "boleto"},
            {"descricao": "Conta de Água", "categoria": "agua", "tipo": "variavel", "valor": Decimal("450.00"), "recorrente": True, "forma_pagamento": "boleto"},
            {"descricao": "Marketing Digital", "categoria": "marketing", "tipo": "variavel", "valor": Decimal("800.00"), "recorrente": True, "forma_pagamento": "cartao_credito"},
            {"descricao": "Manutenção de Equipamentos", "categoria": "manutencao", "tipo": "variavel", "valor": Decimal("650.00"), "recorrente": False, "forma_pagamento": "pix"},
            {"descricao": "Serviços de Limpeza", "categoria": "limpeza", "tipo": "variavel", "valor": Decimal("500.00"), "recorrente": True, "forma_pagamento": "dinheiro"},
        ]
        for idx, d in enumerate(despesas_data):
            data_despesa = primeiro_dia_mes + timedelta(days=min(idx * 3, 27))
            despesa = Despesa(
                estabelecimento_id=est.id,
                descricao=d["descricao"],
                categoria=d["categoria"],
                tipo=d["tipo"],
                valor=d["valor"],
                data_despesa=data_despesa,
                forma_pagamento=d["forma_pagamento"],
                recorrente=d["recorrente"],
                observacoes="Seed automático"
            )
            db.session.add(despesa)
            print(f"  ✅ {despesa.descricao} - R$ {despesa.valor}")
        db.session.commit()
        print("✅ Despesas salvas!")
        
        # 8. HISTÓRICO DE PONTO (sem fotos, realista)
        print()
        print("⏰ Criando histórico de ponto...")
        
        # Dados de configuração de horário padrão - criar ou atualizar
        config = db.session.query(ConfiguracaoHorario).filter_by(estabelecimento_id=est.id).first()
        if not config:
            config = ConfiguracaoHorario(
                estabelecimento_id=est.id,
                hora_entrada=datetime.strptime('08:00', '%H:%M').time(),
                hora_saida_almoco=datetime.strptime('12:00', '%H:%M').time(),
                hora_retorno_almoco=datetime.strptime('13:00', '%H:%M').time(),
                hora_saida=datetime.strptime('18:00', '%H:%M').time(),
                tolerancia_entrada=10,
                tolerancia_saida_almoco=5,
                tolerancia_retorno_almoco=10,
                tolerancia_saida=5,
                exigir_foto=True,
                exigir_localizacao=False,
                raio_permitido_metros=100
            )
            db.session.add(config)
            db.session.flush()
        
        # Criar registros de ponto para os últimos 30 dias
        # Apenas para funcionários (admin e joao)
        pontos_criados = 0
        funcionarios_para_ponto = [admin, joao]
        
        hoje = date.today()
        for dias_atras in range(30, 0, -1):
            data_registro = hoje - timedelta(days=dias_atras)
            
            # Pular fins de semana
            if data_registro.weekday() >= 5:  # 5=sábado, 6=domingo
                continue
            
            for funcionario in funcionarios_para_ponto:
                # Entrada (entre 07:50 e 08:15)
                hora_entrada = datetime.strptime('08:00', '%H:%M').time()
                minutos_variacao = random.randint(-10, 15)
                hora_entrada = (datetime.combine(data_registro, hora_entrada) + timedelta(minutes=minutos_variacao)).time()
                
                entrada = RegistroPonto(
                    funcionario_id=funcionario.id,
                    estabelecimento_id=est.id,
                    data=data_registro,
                    hora=hora_entrada,
                    tipo_registro='entrada',
                    status='normal' if minutos_variacao <= 10 else 'atrasado',
                    minutos_atraso=max(0, minutos_variacao - 10),
                    observacao='Entrada matinal'
                )
                db.session.add(entrada)
                pontos_criados += 1
                
                # Saída almoço (entre 11:55 e 12:10)
                hora_saida_alm = datetime.strptime('12:00', '%H:%M').time()
                minutos_var_alm = random.randint(-5, 10)
                hora_saida_alm = (datetime.combine(data_registro, hora_saida_alm) + timedelta(minutes=minutos_var_alm)).time()
                
                saida_almoco = RegistroPonto(
                    funcionario_id=funcionario.id,
                    estabelecimento_id=est.id,
                    data=data_registro,
                    hora=hora_saida_alm,
                    tipo_registro='saida_almoco',
                    status='normal',
                    minutos_atraso=0,
                    observacao='Saída para almoço'
                )
                db.session.add(saida_almoco)
                pontos_criados += 1
                
                # Retorno almoço (entre 12:55 e 13:15)
                hora_retorno_alm = datetime.strptime('13:00', '%H:%M').time()
                minutos_var_ret = random.randint(-5, 15)
                hora_retorno_alm = (datetime.combine(data_registro, hora_retorno_alm) + timedelta(minutes=minutos_var_ret)).time()
                
                retorno_almoco = RegistroPonto(
                    funcionario_id=funcionario.id,
                    estabelecimento_id=est.id,
                    data=data_registro,
                    hora=hora_retorno_alm,
                    tipo_registro='retorno_almoco',
                    status='normal' if minutos_var_ret <= 10 else 'atrasado',
                    minutos_atraso=max(0, minutos_var_ret - 10),
                    observacao='Retorno do almoço'
                )
                db.session.add(retorno_almoco)
                pontos_criados += 1
                
                # Saída (entre 17:50 e 18:15) - sem atraso (pode sair mais tarde)
                hora_saida_fim = datetime.strptime('18:00', '%H:%M').time()
                minutos_var_fim = random.randint(-10, 30)
                hora_saida_fim = (datetime.combine(data_registro, hora_saida_fim) + timedelta(minutes=minutos_var_fim)).time()
                
                saida = RegistroPonto(
                    funcionario_id=funcionario.id,
                    estabelecimento_id=est.id,
                    data=data_registro,
                    hora=hora_saida_fim,
                    tipo_registro='saida',
                    status='normal',
                    minutos_atraso=0,
                    observacao='Saída final'
                )
                db.session.add(saida)
                pontos_criados += 1
        
        db.session.commit()
        print(f"✅ {pontos_criados} registros de ponto criados!")
        
        # 9. VENDAS (em lotes pequenos para evitar timeout)
        print()
        print("🧾 Criando vendas...")
        
        from app.models import Venda, VendaItem, Pagamento, MovimentacaoEstoque
        import random
        
        # Buscar dados salvos
        produtos_salvos = Produto.query.filter_by(estabelecimento_id=est.id).all()
        clientes_salvos = Cliente.query.filter_by(estabelecimento_id=est.id).all()
        funcionarios_salvos = Funcionario.query.filter_by(estabelecimento_id=est.id).all()
        
        def gerar_codigo_venda_unico(estabelecimento_id: int, dt: datetime) -> str:
            base = f"V{dt.strftime('%Y%m%d')}"
            contador = (
                db.session.query(Venda.id)
                .filter(Venda.estabelecimento_id == estabelecimento_id)
                .filter(Venda.codigo.like(f"{base}%"))
                .count()
            )
            codigo = f"{base}{contador+1:03d}"
            while (
                db.session.query(Venda.id)
                .filter_by(estabelecimento_id=estabelecimento_id, codigo=codigo)
                .first()
                is not None
            ):
                codigo = f"{base}-{random.randint(100000, 999999)}"
            return codigo
        
        vendas_criadas = 0
        max_vendas = 60  # Mais vendas para enriquecer os dados
        
        for i in range(max_vendas):
            try:
                # Data da venda (últimos 30 dias)
                dias_atras = random.randint(0, 30)
                data_venda = datetime.now() - timedelta(days=dias_atras)
                
                # Criar venda
                forma = random.choices(
                    ["dinheiro", "pix", "cartao_debito", "cartao_credito"],
                    weights=[35, 25, 20, 20],
                    k=1
                )[0]
                venda = Venda(
                    estabelecimento_id=est.id,
                    cliente_id=random.choice(clientes_salvos).id if random.random() > 0.3 else None,
                    funcionario_id=random.choice(funcionarios_salvos).id,
                    codigo=gerar_codigo_venda_unico(est.id, data_venda),
                    subtotal=Decimal("0.00"),
                    desconto=Decimal("0.00"),
                    total=Decimal("0.00"),
                    forma_pagamento=forma,
                    valor_recebido=Decimal("0.00"),
                    troco=Decimal("0.00"),
                    status="finalizada" if random.random() > 0.05 else "cancelada",
                    quantidade_itens=0,
                    data_venda=data_venda
                )
                db.session.add(venda)
                db.session.flush()
                
                if venda.status == "finalizada":
                    # Criar itens (2-5 produtos por venda)
                    num_itens = random.randint(2, 5)
                    produtos_venda = random.sample(produtos_salvos, min(num_itens, len(produtos_salvos)))
                    
                    subtotal = Decimal("0.00")
                    
                    for produto in produtos_venda:
                        quantidade = random.randint(1, 4)
                        preco_unitario = produto.preco_venda
                        total_item = preco_unitario * Decimal(str(quantidade))
                        
                        # Margem percentual por item
                        if float(preco_unitario) > 0:
                            margem_pct = ((float(preco_unitario) - float(produto.preco_custo)) / float(preco_unitario)) * 100
                        else:
                            margem_pct = 0.0
                        
                        item = VendaItem(
                            venda_id=venda.id,
                            produto_id=produto.id,
                            produto_nome=produto.nome,
                            produto_codigo=produto.codigo_barras,
                            produto_unidade=produto.unidade_medida,
                            quantidade=quantidade,
                            preco_unitario=preco_unitario,
                            desconto=Decimal("0.00"),
                            total_item=total_item,
                            custo_unitario=produto.preco_custo,
                            margem_item=Decimal(str(round(margem_pct, 2)))
                        )
                        db.session.add(item)
                        
                        subtotal += total_item
                        
                        # Atualizar estoque
                        quantidade_anterior = produto.quantidade
                        produto.quantidade -= quantidade
                        produto.quantidade_vendida += quantidade
                        produto.total_vendido += float(total_item)
                        
                        # Movimentação de estoque
                        mov = MovimentacaoEstoque(
                            estabelecimento_id=est.id,
                            produto_id=produto.id,
                            tipo="saida",
                            quantidade=quantidade,
                            quantidade_anterior=quantidade_anterior,
                            quantidade_atual=produto.quantidade,
                            motivo="venda",
                            funcionario_id=venda.funcionario_id,
                            venda_id=venda.id,
                            created_at=data_venda,
                            observacoes=f"Venda {venda.codigo}"
                        )
                        db.session.add(mov)
                    
                    # Desconto aleatório (0%, 5% ou 10%)
                    desconto_pct = random.choice([0, 0, 5, 10])
                    desconto_valor = (subtotal * Decimal(str(desconto_pct))) / Decimal("100")
                    
                    # Atualizar totais da venda
                    venda.subtotal = subtotal
                    venda.desconto = desconto_valor
                    venda.total = max(Decimal("0.00"), subtotal - desconto_valor)
                    venda.quantidade_itens = num_itens
                    
                    # Valor recebido e troco
                    if venda.forma_pagamento == "dinheiro":
                        # pequeno troco
                        venda.valor_recebido = venda.total + Decimal(str(random.choice([0, 0, 2, 5])))
                        venda.troco = max(Decimal("0.00"), venda.valor_recebido - venda.total)
                    else:
                        venda.valor_recebido = venda.total
                        venda.troco = Decimal("0.00")
                    
                    # Criar pagamento
                    pagamento = Pagamento(
                        venda_id=venda.id,
                        estabelecimento_id=est.id,
                        forma_pagamento=venda.forma_pagamento,
                        valor=venda.total,
                        troco=venda.troco,
                        status="aprovado",
                        data_pagamento=data_venda
                    )
                    db.session.add(pagamento)
                else:
                    # Venda cancelada
                    venda.data_cancelamento = data_venda
                    venda.motivo_cancelamento = random.choice(["cliente desistiu", "erro de cobrança", "produto indisponível"])
                
                # Commit a cada 5 vendas para evitar timeout
                if (i + 1) % 5 == 0:
                    db.session.commit()
                    print(f"  ✅ {i+1} vendas criadas...")
                
                vendas_criadas += 1
                
            except Exception as e:
                print(f"  ⚠️  Erro na venda {i+1}: {str(e)[:50]}")
                db.session.rollback()
                break
        
        # Commit final
        db.session.commit()
        print(f"✅ {vendas_criadas} vendas criadas!")
        
        # 10. REPLICAÇÃO PARA NEON (usa target_url)
        if target_url and target_url.startswith('postgresql://'):
            print()
            print("🔄 Replicando dados para Neon (PostgreSQL)...")
            try:
                neon_engine = create_engine(target_url)
                # Testar conexão
                with neon_engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                NeonSession = sessionmaker(bind=neon_engine)
                neon_session = NeonSession()
                
                # Garantir que o schema existe
                db.metadata.create_all(neon_engine)
                
                # Limpar dados em ordem segura (respeitando FKs)
                for model in [
                    VendaItem, Pagamento, MovimentacaoEstoque, MovimentacaoCaixa, Venda, Caixa,
                    RegistroPonto, ConfiguracaoHorario,  # 🔥 ADICIONADO
                    Produto, CategoriaProduto, Fornecedor, Cliente, LoginHistory, Funcionario,
                    Configuracao, Despesa, DashboardMetrica, Estabelecimento
                ]:
                    try:
                        neon_session.query(model).delete()
                    except Exception as e:
                        print(f"  ⚠️  Erro ao limpar {model.__tablename__}: {str(e)[:80]}")
                neon_session.commit()
                print("  ✅ Banco Neon limpo")
                
                def _clone(instance):
                    """Clona uma instância de modelo para a sessão do Neon"""
                    data = {}
                    for col in instance.__table__.columns:
                        data[col.name] = getattr(instance, col.name)
                    return instance.__class__(**data)
                
                def _bulk_copy(model):
                    """Copia todos os registros de um modelo para o Neon"""
                    rows = db.session.query(model).all()
                    for r in rows:
                        neon_session.add(_clone(r))
                    neon_session.commit()
                    print(f"  ✅ {model.__tablename__}: {len(rows)} registros copiados")
                
                # Ordem de cópia respeitando FKs
                print("\n  📋 Copiando dados...")
                _bulk_copy(Estabelecimento)
                _bulk_copy(Configuracao)
                _bulk_copy(Funcionario)
                _bulk_copy(LoginHistory)
                _bulk_copy(Cliente)
                _bulk_copy(Fornecedor)
                _bulk_copy(CategoriaProduto)
                _bulk_copy(Produto)
                _bulk_copy(ConfiguracaoHorario)  # 🔥 ANTES de RegistroPonto
                _bulk_copy(RegistroPonto)        # 🔥 ADICIONADO
                _bulk_copy(Caixa)
                _bulk_copy(Venda)
                _bulk_copy(VendaItem)
                _bulk_copy(Pagamento)
                _bulk_copy(MovimentacaoEstoque)
                _bulk_copy(MovimentacaoCaixa)
                _bulk_copy(Despesa)
                _bulk_copy(DashboardMetrica)
                
                neon_session.close()
                print("\n✅ REPLICAÇÃO PARA NEON CONCLUÍDA COM SUCESSO!")
                
            except Exception as e:
                print(f"❌ ERRO NA REPLICAÇÃO: {str(e)}")
                import traceback
                traceback.print_exc()
        else:
            print()
            print("ℹ️ Neon não configurado. Configure NEON_DATABASE_URL para replicar.")

        
        # RESUMO
        print()
        print("=" * 60)
        print("📊 RESUMO")
        print("=" * 60)
        print(f"  Estabelecimentos: {Estabelecimento.query.count()}")
        print(f"  Funcionários:     {Funcionario.query.count()}")
        print(f"  Clientes:         {Cliente.query.count()}")
        print(f"  Fornecedores:     {Fornecedor.query.count()}")
        print(f"  Categorias:       {CategoriaProduto.query.count()}")
        print(f"  Produtos:         {Produto.query.count()}")
        print(f"  Vendas:           {Venda.query.count()}")
        print(f"  Itens Vendidos:   {VendaItem.query.count()}")
        print(f"  Movimentações:    {MovimentacaoEstoque.query.count()}")
        print("=" * 60)
        print()
        print("🎉 SEED COMPLETO!")
        print()
        print("📝 Credenciais:")
        print("  admin / admin123 (ADMIN)")
        print("  joao / joao123 (VENDEDOR)")
        print()
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        sys.exit(1)
