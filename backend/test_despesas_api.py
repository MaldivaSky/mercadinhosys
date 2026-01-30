#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Teste rápido da API de despesas"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models import Despesa, Funcionario, Estabelecimento
from datetime import datetime, date

app = create_app()

with app.app_context():
    print("🔍 Verificando despesas no banco...")
    
    # Verificar estabelecimentos
    estabelecimentos = Estabelecimento.query.all()
    print(f"📊 Estabelecimentos: {len(estabelecimentos)}")
    
    if estabelecimentos:
        estab = estabelecimentos[0]
        print(f"   - {estab.nome_fantasia} (ID: {estab.id})")
        
        # Verificar despesas
        despesas = Despesa.query.filter_by(estabelecimento_id=estab.id).all()
        print(f"💰 Despesas encontradas: {len(despesas)}")
        
        if despesas:
            for d in despesas[:3]:
                print(f"   - {d.descricao}: R$ {d.valor} ({d.categoria})")
        else:
            print("   ⚠️ Nenhuma despesa encontrada. Criando despesas de exemplo...")
            
            # Criar despesas de exemplo
            despesas_exemplo = [
                Despesa(
                    estabelecimento_id=estab.id,
                    descricao="Conta de Energia",
                    categoria="Energia",
                    tipo="fixa",
                    valor=450.00,
                    data_despesa=date.today(),
                    forma_pagamento="Boleto",
                    recorrente=True
                ),
                Despesa(
                    estabelecimento_id=estab.id,
                    descricao="Compra de Material de Limpeza",
                    categoria="Manutenção",
                    tipo="variavel",
                    valor=120.50,
                    data_despesa=date.today(),
                    forma_pagamento="Dinheiro",
                    recorrente=False
                ),
                Despesa(
                    estabelecimento_id=estab.id,
                    descricao="Aluguel do Estabelecimento",
                    categoria="Aluguel",
                    tipo="fixa",
                    valor=2500.00,
                    data_despesa=date.today(),
                    forma_pagamento="Transferência",
                    recorrente=True
                ),
            ]
            
            for despesa in despesas_exemplo:
                db.session.add(despesa)
            
            db.session.commit()
            print("   ✅ Despesas de exemplo criadas!")
            
            despesas = Despesa.query.filter_by(estabelecimento_id=estab.id).all()
            print(f"   📊 Total de despesas agora: {len(despesas)}")
    else:
        print("❌ Nenhum estabelecimento encontrado!")

print("\n✅ Teste concluído!")
