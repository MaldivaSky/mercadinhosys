#!/usr/bin/env python
from app import create_app, db
from app.models import RegistroPonto
import json

app = create_app()
with app.app_context():
    registros = RegistroPonto.query.limit(5).all()
    print("📋 VERIFICANDO REGISTROS NO BANCO:")
    for r in registros:
        dict_r = r.to_dict()
        print(f"\n  ID: {r.id}")
        print(f"  foto_url no banco: {r.foto_url}")
        print(f"  foto_url no to_dict: {dict_r.get('foto_url')}")
        print(f"  Campos retornados: {list(dict_r.keys())}")
