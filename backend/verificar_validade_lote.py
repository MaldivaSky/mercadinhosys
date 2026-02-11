#!/usr/bin/env python3
"""
Script para verificar dados de validade e lote dos produtos
"""
from app import create_app, db
from app.models import Produto

app = create_app()

with app.app_context():
    with open('verification_result.txt', 'w', encoding='utf-8') as f:
        def log(msg):
            print(msg)
            f.write(msg + '\n')
            
        log("=" * 80)
        log("VERIFICAÇÃO DE VALIDADE E LOTE")
        log("=" * 80)
        
        # Total de produtos
        total = Produto.query.count()
        log(f"\n📦 Total de produtos: {total}")
        
        # Produtos com validade
        com_validade = Produto.query.filter(Produto.data_validade.isnot(None)).count()
        log(f"📅 Produtos com data_validade: {com_validade}")
        
        # Produtos com lote
        com_lote = Produto.query.filter(Produto.lote.isnot(None), Produto.lote != '').count()
        log(f"🏷️ Produtos com lote: {com_lote}")
        
        # Produtos controlando validade
        controla_validade = Produto.query.filter(Produto.controlar_validade == True).count()
        log(f"✅ Produtos com controlar_validade=True: {controla_validade}")
        
        log("\n" + "=" * 80)
        log("AMOSTRA DE PRODUTOS (Primeiros 10)")
        log("=" * 80)
        
        produtos = Produto.query.limit(10).all()
        
        for p in produtos:
            log(f"\nID: {p.id} | Nome: {p.nome}")
            log(f"   Controla Validade: {p.controlar_validade}")
            log(f"   Data Validade: {p.data_validade}")
            log(f"   Lote: '{p.lote}'")
        
        log("\n" + "=" * 80)
        log("PRODUTOS COM VALIDADE DEFINIDA (Primeiros 5)")
        log("=" * 80)
        
        produtos_validade = Produto.query.filter(Produto.data_validade.isnot(None)).limit(5).all()
        if not produtos_validade:
            log("Nenhum produto com data de validade encontrada.")
        else:
            for p in produtos_validade:
                log(f"ID: {p.id} | Nome: {p.nome} | Validade: {p.data_validade} | Lote: {p.lote}")


