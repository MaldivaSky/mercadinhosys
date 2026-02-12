from app import create_app, db
from app.models import Despesa, Estabelecimento
from datetime import datetime, timedelta
from sqlalchemy import func

def check_expenses():
    app = create_app()
    with app.app_context():
        # Get first establishment
        estab = db.session.query(Estabelecimento).first()
        if not estab:
            print("No establishment found.")
            return
        
        print(f"Checking expenses for establishment: {estab.id} - {estab.nome_fantasia}")
        
        total = db.session.query(func.count(Despesa.id)).filter(Despesa.estabelecimento_id == estab.id).scalar()
        print(f"Total expenses in DB: {total}")
        
        days = 30
        start_date = datetime.utcnow() - timedelta(days=days)
        print(f"Filter start_date (datetime): {start_date}")
        
        # Test query with datetime
        count_dt = db.session.query(func.count(Despesa.id)).filter(
            Despesa.estabelecimento_id == estab.id,
            Despesa.data_despesa >= start_date
        ).scalar()
        print(f"Expenses >= start_date (datetime): {count_dt}")
        
        # Test query with date
        start_date_only = start_date.date()
        print(f"Filter start_date (date only): {start_date_only}")
        count_d = db.session.query(func.count(Despesa.id)).filter(
            Despesa.estabelecimento_id == estab.id,
            Despesa.data_despesa >= start_date_only
        ).scalar()
        print(f"Expenses >= start_date (date only): {count_d}")
        
        # Check some samples
        samples = db.session.query(Despesa).filter(Despesa.estabelecimento_id == estab.id).limit(5).all()
        for s in samples:
            print(f"Sample: ID={s.id}, Data={s.data_despesa}, Valor={s.valor}, Categoria={s.categoria}, Tipo={s.tipo}")

if __name__ == "__main__":
    check_expenses()
