#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Diagnóstico de fornecedores e classificação ABC"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models import Produto, Fornecedor

app = create_app()

with app.app_context():
    print("\n" + "="*80)
    print("DIAGNÓSTICO DE FORNECEDORES E CLASSIFICAÇÃO ABC")
    print("="*80 + "\n")
    
    # Total de produtos
    total = Produto.query.count()
    print(f"📊 Total de produtos: {total}")
    
    # Produtos sem fornecedor
    sem_fornecedor = Produto.query.filter_by(fornecedor_id=None).count()
    print(f"❌ Produtos SEM fornecedor: {sem_fornecedor}")
    
    # Produtos com fornecedor
    com_fornecedor = Produto.query.filter(Produto.fornecedor_id != None).count()
    print(f"✅ Produtos COM fornecedor: {com_fornecedor}")
    
    # Classificação ABC
    classe_a = Produto.query.filter_by(classificacao_abc='A').count()
    classe_b = Produto.query.filter_by(classificacao_abc='B').count()
    classe_c = Produto.query.filter_by(classificacao_abc='C').count()
    
    print(f"\n📈 Classificação ABC:")
    print(f"   Classe A: {classe_a} ({classe_a/total*100:.1f}%)")
    print(f"   Classe B: {classe_b} ({classe_b/total*100:.1f}%)")
    print(f"   Classe C: {classe_c} ({classe_c/total*100:.1f}%)")
    
    # Amostra de produtos sem fornecedor
    if sem_fornecedor > 0:
        print(f"\n🔍 Amostra de produtos SEM fornecedor:")
        produtos_sem = Produto.query.filter_by(fornecedor_id=None).limit(5).all()
        for p in produtos_sem:
            print(f"   - {p.nome} (ID: {p.id}, Marca: {p.marca}, Classe: {p.classificacao_abc})")
    
    # Amostra de produtos com fornecedor
    if com_fornecedor > 0:
        print(f"\n✅ Amostra de produtos COM fornecedor:")
        produtos_com = Produto.query.filter(Produto.fornecedor_id != None).limit(5).all()
        for p in produtos_com:
            fornecedor_nome = p.fornecedor.nome_fantasia if p.fornecedor else "N/A"
            print(f"   - {p.nome} (ID: {p.id}, Fornecedor: {fornecedor_nome}, Classe: {p.classificacao_abc})")
    
    # Total de fornecedores
    total_fornecedores = Fornecedor.query.count()
    print(f"\n🏭 Total de fornecedores: {total_fornecedores}")
    
    print("\n" + "="*80 + "\n")
