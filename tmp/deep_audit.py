
import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text
from datetime import datetime
from dotenv import load_dotenv

# Adjust path to import app correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load .env
load_dotenv(dotenv_path="backend/.env")

from app import create_app
from app.models import db, Estabelecimento, Venda, Despesa, ContaPagar, Cliente

def audit_database(uri, label):
    print(f"\n--- Auditing: {label} ---")
    print(f"URI: {uri}")
    
    os.environ["DATABASE_URL"] = uri
    os.environ["HYBRID_MODE"] = "offline" if "sqlite" in uri else "online"
    
    app = create_app()
    with app.app_context():
        try:
            # Check if tables exist
            db.Model.metadata.reflect(bind=db.engine)
            if not db.Model.metadata.tables:
                print("No tables found in this database.")
                return

            est_count = db.session.query(Estabelecimento).count()
            print(f"Establishments: {est_count}")
            
            ests = db.session.query(Estabelecimento).all()
            for est in ests:
                print(f"\n  Establishment ID: {est.id} ({est.nome_fantasia})")
                vendas = db.session.query(Venda).filter_by(estabelecimento_id=est.id).count()
                despesas = db.session.query(Despesa).filter_by(estabelecimento_id=est.id).count()
                contas = db.session.query(ContaPagar).filter_by(estabelecimento_id=est.id).count()
                clientes = db.session.query(Cliente).filter_by(estabelecimento_id=est.id).count()
                
                print(f"    Vendas: {vendas}")
                print(f"    Despesas: {despesas}")
                print(f"    Contas a Pagar: {contas}")
                print(f"    Clientes: {clientes}")
                
        except Exception as e:
            print(f"Error auditing {label}: {e}")

if __name__ == "__main__":
    # Check Postgres from .env
    pg_url = os.environ.get("DATABASE_URL")
    if pg_url:
        audit_database(pg_url, "PostgreSQL (.env)")
    
    # Check Aiven
    aiven_url = os.environ.get("AIVEN_DATABASE_URL")
    if aiven_url:
        audit_database(aiven_url.replace("postgres://", "postgresql://"), "Aiven Cloud")

    # Search for SQLite files
    print("\nSearching for SQLite files...")
    sqlite_files = list(Path(".").rglob("*.db")) + list(Path(".").rglob("*.sqlite"))
    for f in sqlite_files:
        path = str(f.absolute())
        audit_database(f"sqlite:///{path}", f"SQLite: {f.name} at {path}")
