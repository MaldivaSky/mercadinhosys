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
            
            # Dropar tabelas em ordem (dependentes primeiro)
            tables_to_drop = [
                "sync_queue", "relatorios_agendados", "dashboard_metricas",
                "movimentacoes_caixa", "movimentacoes_estoque",
                "pagamentos", "venda_itens", "vendas", "caixas",
                "registros_ponto", "configuracoes_horario",
                "contas_pagar", "contas_receber", "pedidos_compra_itens", "pedidos_compra",
                "produtos", "categorias_produto", "fornecedores", "clientes",
                "login_history", "funcionarios", "configuracoes", "despesas", "estabelecimentos"
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
            {"nome": "Maria Santos", "cpf": "333.444.555-66", "email": "maria@email.com", "telefone": "(84) 93456-7890", "celular": "(84) 93456-7890", "bairro": "Centro"},
            {"nome": "Pedro Oliveira", "cpf": "444.555.666-77", "email": "pedro@email.com", "telefone": "(84) 94567-8901", "celular": "(84) 94567-8901", "bairro": "Tirol"},
            {"nome": "Ana Costa", "cpf": "555.666.777-88", "email": "ana@email.com", "telefone": "(84) 95678-9012", "celular": "(84) 95678-9012", "bairro": "Lagoa Nova"},
            {"nome": "Lucas Pereira", "cpf": "666.777.888-99", "email": "lucas@email.com", "telefone": "(84) 96789-0123", "celular": "(84) 96789-0123", "bairro": "Alecrim"},
            {"nome": "Juliana Lima", "cpf": "777.888.999-00", "email": "juliana@email.com", "telefone": "(84) 97890-1234", "celular": "(84) 97890-1234", "bairro": "Ponta Negra"},
            {"nome": "Roberto Souza", "cpf": "888.999.000-11", "email": "roberto@email.com", "telefone": "(84) 98901-2345", "celular": "(84) 98901-2345", "bairro": "Candelária"},
            {"nome": "Fernanda Alves", "cpf": "999.000.111-22", "email": "fernanda@email.com", "telefone": "(84) 99012-3456", "celular": "(84) 99012-3456", "bairro": "Petrópolis"},
            {"nome": "Carlos Silva", "cpf": "000.111.222-33", "email": "carlos@email.com", "telefone": "(84) 90123-4567", "celular": "(84) 90123-4567", "bairro": "Cidade Verde"},
            {"nome": "Patrícia Gomes", "cpf": "111.222.333-44", "email": "patricia@email.com", "telefone": "(84) 91234-5678", "celular": "(84) 91234-5678", "bairro": "Nova Parnamirim"},
            {"nome": "Ricardo Mendes", "cpf": "222.333.444-55", "email": "ricardo@email.com", "telefone": "(84) 92345-6789", "celular": "(84) 92345-6789", "bairro": "Emaús"},
            {"nome": "Camila Rocha", "cpf": "012.345.678-99", "email": "camila@email.com", "telefone": "(84) 93456-7890", "celular": "(84) 93456-7890", "bairro": "Cohabinal"},
            {"nome": "Felipe Martins", "cpf": "987.654.321-00", "email": "felipe@email.com", "telefone": "(84) 94567-8901", "celular": "(84) 94567-8901", "bairro": "Centro"},
        ]
        
        for i, c_data in enumerate(clientes_data):
            cliente = Cliente(
                estabelecimento_id=est.id,
                nome=c_data["nome"],
                cpf=c_data["cpf"],
                email=c_data["email"],
                telefone=c_data["telefone"],
                celular=c_data["celular"],
                cep=f"59000-{i:03d}",
                logradouro="Rua Exemplo",
                numero=str(10 + i),
                bairro=c_data["bairro"],
                cidade="Natal",
                estado="RN",
                ativo=True
            )
            db.session.add(cliente)
            print(f"  ✅ {cliente.nome}")
        
        db.session.flush()
        
        # 4. FORNECEDORES
        print()
        print("🚚 Criando fornecedores...")
        
        fornecedores_data = [
            {"nome": "Distribuidora ABC", "cnpj": "11.222.333/0001-44"},
            {"nome": "Atacado XYZ", "cnpj": "22.333.444/0001-55"},
            {"nome": "Logística Norte", "cnpj": "33.444.555/0001-66"},
            {"nome": "Alimentos Brasil", "cnpj": "44.555.666/0001-77"},
            {"nome": "Bebidas Premium", "cnpj": "55.666.777/0001-88"},
        ]
        
        fornecedores = []
        for i, f_data in enumerate(fornecedores_data):
            fornecedor = Fornecedor(
                estabelecimento_id=est.id,
                nome_fantasia=f_data["nome"],
                razao_social=f"{f_data['nome']} LTDA",
                cnpj=f_data["cnpj"],
                telefone=f"(84) 3000-{1000+i}",
                email=f"{f_data['nome'].lower().replace(' ', '')}@email.com",
                cep="59000-000",
                logradouro="Av Industrial",
                numero=str(500 + i * 10),
                bairro="Distrito Industrial",
                cidade="Natal",
                estado="RN",
                ativo=True
            )
            db.session.add(fornecedor)
            fornecedores.append(fornecedor)
            print(f"  ✅ {fornecedor.nome_fantasia}")
        
        db.session.flush()
        
        # 5. CATEGORIAS
        print()
        print("📁 Criando categorias...")
        
        categorias_data = ["Alimentos", "Bebidas", "Limpeza", "Higiene", "Padaria", "Hortifruti", "Carnes", "Laticínios"]
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
        
        # (nome, cat_idx, forn_idx, codigo_sufixo, custo, venda, qtd)
        # cat_idx: 0=Alim, 1=Beb, 2=Limp, 3=Hig, 4=Pad, 5=Horti, 6=Carnes, 7=Lat
        produtos_data = [
            # Alimentos
            ("Arroz Tipo 1 5kg", 0, 0, "01", 15.00, 22.90, 50),
            ("Feijão Preto 1kg", 0, 0, "02", 5.50, 8.90, 80),
            ("Açúcar Cristal 1kg", 0, 0, "03", 3.20, 4.99, 100),
            ("Café Torrado 500g", 0, 0, "04", 12.00, 18.50, 40),
            ("Macarrão Espaguete 500g", 0, 0, "05", 2.50, 4.20, 60),
            ("Óleo de Soja 900ml", 0, 0, "06", 5.80, 8.50, 70),
            ("Farinha de Trigo 1kg", 0, 0, "07", 3.50, 5.90, 50),
            ("Biscoito Recheado", 0, 0, "08", 1.80, 3.50, 120),
            
            # Bebidas
            ("Refrigerante 2L", 1, 1, "09", 5.50, 8.99, 60),
            ("Água Mineral 1.5L", 1, 1, "10", 1.20, 2.50, 120),
            ("Suco de Uva 1L", 1, 1, "11", 6.00, 10.90, 30),
            ("Cerveja Lata 350ml", 1, 1, "12", 2.50, 4.50, 200),
            ("Energético 473ml", 1, 1, "13", 7.00, 12.90, 40),
            
            # Limpeza
            ("Detergente Líquido", 2, 2, "14", 1.80, 2.99, 90),
            ("Sabão em Pó 1kg", 2, 2, "15", 8.50, 12.90, 40),
            ("Água Sanitária 1L", 2, 2, "16", 2.50, 4.50, 60),
            ("Amaciante 2L", 2, 2, "17", 10.00, 16.90, 30),
            ("Esponja de Aço", 2, 2, "18", 1.50, 2.80, 100),
            
            # Higiene
            ("Shampoo 400ml", 3, 2, "19", 8.00, 14.99, 35),
            ("Sabonete 90g", 3, 2, "20", 1.50, 2.49, 150),
            ("Papel Higiênico 4un", 3, 2, "21", 4.50, 7.90, 80),
            ("Creme Dental 90g", 3, 2, "22", 3.00, 5.50, 90),
            ("Desodorante Aerosol", 3, 2, "23", 9.00, 15.90, 40),
            
            # Padaria
            ("Pão Francês kg", 4, 3, "24", 8.00, 14.90, 20),
            ("Bolo de Chocolate", 4, 3, "25", 15.00, 25.00, 10),
            ("Pão de Queijo kg", 4, 3, "26", 18.00, 29.90, 15),
            
            # Hortifruti
            ("Tomate kg", 5, 3, "27", 4.00, 7.99, 30),
            ("Cebola kg", 5, 3, "28", 3.50, 6.90, 40),
            ("Batata kg", 5, 3, "29", 3.00, 5.90, 50),
            ("Banana Prata kg", 5, 3, "30", 2.50, 4.99, 45),
            ("Maçã Nacional kg", 5, 3, "31", 5.00, 9.90, 25),
            
            # Carnes
            ("Carne Moída kg", 6, 4, "32", 22.00, 34.90, 15),
            ("Frango Inteiro kg", 6, 4, "33", 9.00, 14.90, 20),
            ("Linguiça Toscana kg", 6, 4, "34", 14.00, 22.90, 18),
            
            # Laticínios
            ("Leite Integral 1L", 7, 4, "35", 3.80, 5.99, 80),
            ("Queijo Mussarela kg", 7, 4, "36", 28.00, 45.90, 10),
            ("Manteiga 200g", 7, 4, "37", 8.50, 13.90, 25),
            ("Iogurte 1L", 7, 4, "38", 9.00, 15.90, 20),

            # Mercearia / Enlatados
            ("Molho de Tomate 340g", 0, 0, "39", 2.50, 3.99, 60),
            ("Macarrão Inst. 85g", 0, 0, "40", 1.20, 2.50, 100),
            ("Sardinha Lata 125g", 0, 0, "41", 4.50, 7.90, 40),
            ("Atum Ralado 170g", 0, 0, "42", 6.50, 10.90, 30),
            ("Milho Verde Lata", 0, 0, "43", 3.00, 5.50, 50),
            ("Ervilha Lata", 0, 0, "44", 3.00, 5.50, 45),
            
            # Mais Bebidas
            ("Cerveja Garrafa 600ml", 1, 1, "45", 6.00, 10.00, 48),
            ("Vodka 1L", 1, 1, "46", 25.00, 45.00, 12),
            ("Whisky 1L", 1, 1, "47", 80.00, 149.90, 6),
            ("Suco Caixa 1L", 1, 1, "48", 5.50, 8.90, 40),
            ("Água de Coco 1L", 1, 1, "49", 7.00, 12.00, 24),

            # Bazar / Utilidades
            ("Isqueiro", 2, 2, "50", 3.00, 6.00, 50),
            ("Pilha AA (par)", 2, 2, "51", 5.00, 9.90, 30),
            ("Lâmpada LED 9W", 2, 2, "52", 8.00, 14.90, 20),
            ("Fósforos (maço)", 2, 2, "53", 0.50, 1.00, 100),
        ]
        
        for nome, cat_idx, forn_idx, sufixo, custo, venda, qtd in produtos_data:
            produto = Produto(
                estabelecimento_id=est.id,
                nome=nome,
                codigo_barras=f"7890000000{sufixo}",
                categoria_id=categorias[cat_idx].id,
                fornecedor_id=fornecedores[forn_idx].id,
                preco_custo=Decimal(str(custo)),
                preco_venda=Decimal(str(venda)),
                quantidade=qtd,
                unidade_medida="KG" if "kg" in nome.lower() else "UN",
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
        
        # Gerar despesas para os últimos 3 meses
        despesas_base = [
            {"descricao": "Salários Funcionários", "categoria": "salarios", "tipo": "fixa", "valor": Decimal("6000.00"), "forma_pagamento": "transferencia"},
            {"descricao": "Aluguel do Estabelecimento", "categoria": "aluguel", "tipo": "fixa", "valor": Decimal("3500.00"), "forma_pagamento": "transferencia"},
            {"descricao": "Conta de Energia", "categoria": "energia", "tipo": "variavel", "valor_min": 1100, "valor_max": 1300, "forma_pagamento": "boleto"},
            {"descricao": "Conta de Água", "categoria": "agua", "tipo": "variavel", "valor_min": 400, "valor_max": 500, "forma_pagamento": "boleto"},
            {"descricao": "Internet/Telefone", "categoria": "telefonia", "tipo": "fixa", "valor": Decimal("250.00"), "forma_pagamento": "boleto"},
            {"descricao": "Sistema de Gestão", "categoria": "software", "tipo": "fixa", "valor": Decimal("150.00"), "forma_pagamento": "cartao_credito"},
            {"descricao": "Marketing Digital", "categoria": "marketing", "tipo": "variavel", "valor_min": 500, "valor_max": 1000, "forma_pagamento": "cartao_credito"},
            {"descricao": "Material de Limpeza", "categoria": "limpeza", "tipo": "variavel", "valor_min": 200, "valor_max": 400, "forma_pagamento": "dinheiro"},
            {"descricao": "Manutenção Predial", "categoria": "manutencao", "tipo": "variavel", "valor_min": 100, "valor_max": 800, "forma_pagamento": "pix", "chance": 0.3},
        ]
        
        for mes_offset in range(3): # Mês atual, mês passado, mês retrasado
            data_base = hoje.replace(day=1) - timedelta(days=mes_offset * 30)
            data_base = data_base.replace(day=1) # Garantir dia 1
            
            for d in despesas_base:
                # Verificar chance (para despesas eventuais)
                if "chance" in d and random.random() > d["chance"]:
                    continue
                    
                # Calcular valor
                if "valor" in d:
                    valor = d["valor"]
                else:
                    valor = Decimal(str(random.randint(d["valor_min"], d["valor_max"])))
                
                # Calcular data (espalhar pelo mês)
                dia_pagto = random.randint(1, 28)
                data_despesa = data_base.replace(day=dia_pagto)
                
                # Se for futuro, ignorar
                if data_despesa > hoje:
                    continue
                    
                despesa = Despesa(
                    estabelecimento_id=est.id,
                    descricao=f"{d['descricao']} (Mês {data_base.month})",
                    categoria=d["categoria"],
                    tipo=d["tipo"],
                    valor=valor,
                    data_despesa=data_despesa,
                    forma_pagamento=d["forma_pagamento"],
                    recorrente=True,
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
        max_vendas = 150  # Mais vendas para enriquecer os dados (Aumentado para 150)
        
        for i in range(max_vendas):
            try:
                # Data da venda (últimos 60 dias para histórico maior)
                dias_atras = random.randint(0, 60)
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
        
        # 10. REPLICAÇÃO PARA NEON (apenas se estiver usando SQLite local e quiser replicar)
        is_sqlite_main = 'sqlite' in str(db.engine.url)
        
        if is_sqlite_main and target_url and target_url.startswith('postgresql://'):
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
