from app import create_app, db
from app.models import Estabelecimento, Despesa, Venda, Funcionario
from sqlalchemy import func

def audit_data():
    app = create_app()
    with app.app_context():
        estabs = db.session.query(Estabelecimento).all()
        print(f"{'ID':<5} | {'Nome':<30} | {'Despesas':<10} | {'Vendas':<10} | {'Funcionários':<12}")
        print("-" * 75)
        for e in estabs:
            exp_count = db.session.query(func.count(Despesa.id)).filter(Despesa.estabelecimento_id == e.id).scalar()
            venda_count = db.session.query(func.count(Venda.id)).filter(Venda.estabelecimento_id == e.id).scalar()
            func_count = db.session.query(func.count(Funcionario.id)).filter(Funcionario.estabelecimento_id == e.id).scalar()
            print(f"{e.id:<5} | {e.nome_fantasia[:30]:<30} | {exp_count:<10} | {venda_count:<10} | {func_count:<12}")

if __name__ == "__main__":
    audit_data()
