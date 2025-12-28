from app import create_app
from app.models import db, Usuario, Produto, Cliente
from datetime import date, datetime, timedelta


def create_app(config_name="default"):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Configura CORS com origens permitidas
    cors_origins = app.config.get("CORS_ORIGINS", ["http://localhost:5173"])
    cors = CORS(app, origins=cors_origins)
    

def init_database():
    """Inicializa o banco de dados com dados de teste"""
    app = create_app()

    with app.app_context():
        # Cria todas as tabelas
        db.drop_all()  # Atenção: Isso APAGA todos os dados existentes!
        db.create_all()

        print("✅ Tabelas criadas com sucesso!")

        # Cria usuário admin
        admin = Usuario(
            nome="Administrador", usuario="admin", nivel_acesso="admin", ativo=True
        )
        admin.set_senha("admin123")
        db.session.add(admin)

        # Data de validade para produtos (7 dias a partir de hoje)
        data_validade = date.today() + timedelta(days=7)

        # Cria alguns produtos de exemplo
        produtos = [
            Produto(
                codigo_barras="7891000315507",
                nome="Arroz 5kg",
                descricao="Arroz tipo 1, pacote 5kg",
                preco_custo=15.90,
                preco_venda=25.90,
                quantidade=50,
                quantidade_minima=10,
                categoria="Mercearia",
            ),
            Produto(
                codigo_barras="7891000053508",
                nome="Feijão 1kg",
                descricao="Feijão carioca",
                preco_custo=4.50,
                preco_venda=8.50,
                quantidade=30,
                quantidade_minima=15,
                categoria="Mercearia",
            ),
            Produto(
                codigo_barras="7891000315508",
                nome="Café 500g",
                descricao="Café torrado e moído",
                preco_custo=6.90,
                preco_venda=12.90,
                quantidade=25,
                quantidade_minima=10,
                categoria="Mercearia",
            ),
            Produto(
                codigo_barras="7891000315509",
                nome="Açúcar 1kg",
                descricao="Açúcar refinado",
                preco_custo=2.40,
                preco_venda=4.90,
                quantidade=40,
                quantidade_minima=20,
                categoria="Mercearia",
            ),
            Produto(
                codigo_barras="7891000315510",
                nome="Óleo 900ml",
                descricao="Óleo de soja",
                preco_custo=5.90,
                preco_venda=9.90,
                quantidade=35,
                quantidade_minima=15,
                categoria="Mercearia",
            ),
            Produto(
                codigo_barras="7891000315511",
                nome="Leite 1L",
                descricao="Leite integral UHT",
                preco_custo=3.50,
                preco_venda=5.90,
                quantidade=60,
                quantidade_minima=30,
                categoria="Laticínios",
            ),
            Produto(
                codigo_barras="7891000315512",
                nome="Pão de Forma",
                descricao="Pão de forma integral",
                preco_custo=4.90,
                preco_venda=8.90,
                quantidade=20,
                quantidade_minima=10,
                categoria="Padaria",
                data_validade=data_validade,  # Usa a data calculada
            ),
            Produto(
                codigo_barras="7891000315513",
                nome="Refrigerante 2L",
                descricao="Refrigerante cola",
                preco_custo=4.90,
                preco_venda=7.90,
                quantidade=45,
                quantidade_minima=20,
                categoria="Bebidas",
            ),
        ]

        for produto in produtos:
            db.session.add(produto)

        # Cria alguns clientes de exemplo
        clientes = [
            Cliente(
                nome="João Silva",
                cpf="123.456.789-00",
                telefone="(11) 99999-8888",
                email="joao@email.com",
                endereco="Rua das Flores, 123 - Centro",
            ),
            Cliente(
                nome="Maria Santos",
                cpf="987.654.321-00",
                telefone="(11) 98888-7777",
                email="maria@email.com",
                endereco="Av. Principal, 456 - Jardim",
            ),
            Cliente(
                nome="Carlos Oliveira",
                telefone="(11) 97777-6666",
                email="carlos@email.com",
                endereco="Rua das Árvores, 789 - Vila Nova",
            ),
        ]

        for cliente in clientes:
            db.session.add(cliente)

        # Salva tudo no banco
        db.session.commit()

        print("✅ Usuário admin criado: admin / admin123")
        print(f"✅ {len(produtos)} produtos criados")
        print(f"✅ {len(clientes)} clientes criados")
        print("\n🎉 Banco de dados inicializado com sucesso!")


if __name__ == "__main__":
    init_database()
