
import sys
import os
from app import create_app
from app.models import db, Funcionario

# This script runs INSIDE the docker container
app = create_app()
with app.app_context():
    print(f"DEBUG: Using DB URI INSIDE DOCKER: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    # 1. Reset maldivas
    sa = Funcionario.query.filter((Funcionario.username == 'maldivas') | (Funcionario.email == 'rafaelmaldivas@gmail.com')).first()
    if sa:
        sa.set_senha("maldivas123")
        sa.status = "ativo"
        sa.ativo = True
        sa.role = "ADMIN"
        print(f"✅ User 'maldivas' updated in Postgres. Password: maldivas123")
    else:
        print("❌ User 'maldivas' NOT FOUND in Postgres!")

    # 2. Standardize ALL admins
    admins = Funcionario.query.filter_by(role="ADMIN").all()
    for a in admins:
        if a.username == "admin_1": a.set_senha("adminElite123")
        elif a.username == "admin_2": a.set_senha("adminBom123")
        elif a.username == "admin_3": a.set_senha("adminRazoavel123")
        elif a.username == "admin_4": a.set_senha("adminMal123")
        elif a.username == "admin_5": a.set_senha("adminPessimo123")
        # Don't overwrite maldivas if it's here
        elif a.username != "maldivas":
            a.set_senha("admin123")
        
        a.status = "ativo"
        a.ativo = True
    
    # 3. Standardize ALL workers
    workers = Funcionario.query.filter_by(role="FUNCIONARIO").all()
    for w in workers:
        w.set_senha("senha123")
        w.status = "ativo"
        w.ativo = True
    
    print(f"✅ Standardized all {len(admins)} admins and {len(workers)} workers in Postgres.")
    
    db.session.commit()
    print("--- DOCKER DB FIX COMPLETE ---")
