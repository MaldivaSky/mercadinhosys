#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de teste para verificar a API de vendas
"""

import requests
import json

def test_vendas_api():
    """Testa a API de vendas"""
    
    base_url = "http://localhost:5000/api"
    
    print("🧪 Testando API de Vendas...")
    print("=" * 60)
    
    # Teste 1: Listar vendas
    print("\n1️⃣ Testando GET /api/vendas")
    try:
        response = requests.get(f"{base_url}/vendas", params={
            "page": 1,
            "per_page": 5
        })
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Sucesso!")
            print(f"   Total de vendas: {data['paginacao']['total_itens']}")
            print(f"   Vendas retornadas: {len(data['vendas'])}")
            
            if data['vendas']:
                venda = data['vendas'][0]
                print(f"\n   Primeira venda:")
                print(f"   - Código: {venda['codigo']}")
                print(f"   - Total: R$ {venda['total']:.2f}")
                print(f"   - Status: {venda['status']}")
                print(f"   - Cliente: {venda['cliente']['nome']}")
                print(f"   - Funcionário: {venda['funcionario']['nome']}")
        else:
            print(f"❌ Erro: {response.status_code}")
            print(f"   Resposta: {response.text}")
            
    except Exception as e:
        print(f"❌ Erro na requisição: {str(e)}")
    
    # Teste 2: Estatísticas
    print("\n2️⃣ Testando estatísticas")
    try:
        response = requests.get(f"{base_url}/vendas", params={
            "page": 1,
            "per_page": 1
        })
        
        if response.status_code == 200:
            data = response.json()
            stats = data['paginacao']['estatisticas']
            print(f"✅ Estatísticas:")
            print(f"   - Total vendido: R$ {stats['total_vendas']:.2f}")
            print(f"   - Quantidade: {stats['quantidade_vendas']}")
            print(f"   - Ticket médio: R$ {stats['ticket_medio']:.2f}")
            print(f"   - Descontos: R$ {stats['total_descontos']:.2f}")
            
            if stats['formas_pagamento']:
                print(f"\n   Formas de pagamento:")
                for forma, dados in stats['formas_pagamento'].items():
                    total = float(dados['total']) if isinstance(dados['total'], (int, float, str)) else 0
                    print(f"   - {forma}: {dados['quantidade']} vendas, R$ {total:.2f}")
                    
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
    
    print("\n" + "=" * 60)
    print("✅ Testes concluídos!")

if __name__ == "__main__":
    test_vendas_api()
