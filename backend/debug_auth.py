
import sys
import os
from app import create_app
from app.models import db, Funcionario
from werkzeug.security import check_password_hash

app = create_app()
with app.app_context():
    print(f"DEBUG: Using DB URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    identifier = "maldivas"
    password = "maldivas123"
    
    print(f"\n--- DIAGNOSTIC FOR '{identifier}' ---")
    
    # 1. Exact query used in auth.py
    funcionario = db.session.execute(
        db.select(Funcionario).filter(
            db.or_( 
                db.func.lower(Funcionario.username) == identifier.lower(),
                db.func.lower(Funcionario.email) == identifier.lower(),
            )
        )
    ).scalar_one_or_none()
    
    if funcionario:
        print(f"✅ User found: ID={funcionario.id}, Username='{funcionario.username}', Email='{funcionario.email}'")
        print(f"   Status: {funcionario.status}, Ativo: {funcionario.ativo}")
        
        # 2. Password check
        is_ok = funcionario.check_senha(password)
        print(f"   Password check for '{password}': {'✅ MATCH' if is_ok else '❌ FAIL'}")
        
        if not is_ok:
            print(f"   Current Hash: {funcionario.senha_hash}")
    else:
        print(f"❌ User NOT FOUND using the auth.py logic!")
        
        # 3. List all users to see if there's a typo
        print("\nAll usernames in DB:")
        all_users = Funcionario.query.all()
        for u in all_users:
            print(f" - '{u.username}' (len: {len(u.username)}) | email: '{u.email}'")

    print("\n--- DIAGNOSTIC COMPLETE ---")
