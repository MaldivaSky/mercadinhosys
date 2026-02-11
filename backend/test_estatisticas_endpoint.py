#!/usr/bin/env python
"""
Script para testar o endpoint de estatísticas de produtos
e verificar se os dados estão corretos.
"""

import sys
import json
from decimal import Decimal
from datetime import datetime, date, timedelta

sys.path.insert(0, '.')

from app import create_app
from app.models import db, Produto, Estabelecimento, Venda, VendaItem
from flask_jwt_extended import create_access_token

app = create_app()

def test_estatisticas():
    """Testa o endpoint de estatísticas"""
    with app.app_context():
        # Obter estabelecimento
        est = Estabelecimento.query.first()
        if not est:
            print("❌ Nenhum estabelecimento encontrado")
            return
        
        print(f"\n{'='*80}")
        print(f"🏪 TESTE DE ESTATÍSTICAS - {est.nome_fantasia}")
        print(f"{'='*80}\n")
        
        # Verificar dados brutos
        produtos = Produto.query.filter_by(estabelecimento_id=est.id).all()
        print(f"📊 Total de produtos: {len(produtos)}")
        
        # Estatísticas básicas
        total_estoque = sum(p.quantidade for p in produtos)
        valor_total_estoque = sum(
            Decimal(str(p.preco_custo or 0)) * Decimal(str(p.quantidade or 0))
            for p in produtos
        )
        total_vendido = sum(Decimal(str(p.total_vendido or 0)) for p in produtos)
        
        print(f"\n📦 ESTOQUE:")
        print(f"   - Total de unidades: {total_estoque}")
        print(f"   - Valor total: R$ {float(valor_total_estoque):.2f}")
        print(f"   - Produtos com estoque negativo: {len([p for p in produtos if p.quantidade < 0])}")
        
        print(f"\n💰 VENDAS:")
        print(f"   - Total vendido (R$): R$ {float(total_vendido):.2f}")
        print(f"   - Produtos com vendas: {len([p for p in produtos if p.total_vendido and p.total_vendido > 0])}")
        print(f"   - Produtos sem vendas: {len([p for p in produtos if not p.total_vendido or p.total_vendido == 0])}")
        
        # Verificar margem
        margens = [Decimal(str(p.margem_lucro or 0)) for p in produtos if p.margem_lucro]
        margem_media = sum(margens) / len(margens) if margens else Decimal('0')
        print(f"\n📈 MARGEM:")
        print(f"   - Margem média: {float(margem_media):.2f}%")
        print(f"   - Margem mínima: {float(min(margens)):.2f}%" if margens else "   - Margem mínima: N/A")
        print(f"   - Margem máxima: {float(max(margens)):.2f}%" if margens else "   - Margem máxima: N/A")
        
        # Verificar ABC
        abc_counts = {"A": 0, "B": 0, "C": 0}
        for p in produtos:
            if p.classificacao_abc:
                abc_counts[p.classificacao_abc] += 1
        
        print(f"\n🎯 CLASSIFICAÇÃO ABC:")
        print(f"   - Classe A: {abc_counts['A']} produtos")
        print(f"   - Classe B: {abc_counts['B']} produtos")
        print(f"   - Classe C: {abc_counts['C']} produtos")
        
        # Verificar giro
        hoje = datetime.utcnow()
        giro_counts = {"rapido": 0, "normal": 0, "lento": 0}
        
        for p in produtos:
            if p.ultima_venda:
                dias = (hoje - p.ultima_venda).days
                if dias <= 7:
                    giro_counts["rapido"] += 1
                elif dias <= 30:
                    giro_counts["normal"] += 1
                else:
                    giro_counts["lento"] += 1
            else:
                giro_counts["lento"] += 1
        
        print(f"\n⚡ GIRO DE ESTOQUE:")
        print(f"   - Rápido (0-7 dias): {giro_counts['rapido']} produtos")
        print(f"   - Normal (8-30 dias): {giro_counts['normal']} produtos")
        print(f"   - Lento (30+ dias): {giro_counts['lento']} produtos")
        
        # Mostrar alguns produtos com problemas
        print(f"\n⚠️  PRODUTOS COM PROBLEMAS:")
        
        produtos_negativos = [p for p in produtos if p.quantidade < 0]
        if produtos_negativos:
            print(f"\n   Estoque Negativo ({len(produtos_negativos)}):")
            for p in produtos_negativos[:5]:
                print(f"   - {p.nome}: {p.quantidade} un (vendido: {p.total_vendido})")
        
        produtos_sem_venda = [p for p in produtos if not p.total_vendido or p.total_vendido == 0]
        if produtos_sem_venda:
            print(f"\n   Sem Vendas ({len(produtos_sem_venda)}):")
            for p in produtos_sem_venda[:5]:
                print(f"   - {p.nome}: {p.quantidade} un")
        
        # Testar endpoint
        print(f"\n{'='*80}")
        print(f"🔗 TESTANDO ENDPOINT /api/produtos/estatisticas")
        print(f"{'='*80}\n")
        
        with app.test_client() as client:
            # Criar token
            token = create_access_token(
                identity=1,
                additional_claims={"estabelecimento_id": est.id}
            )
            
            headers = {"Authorization": f"Bearer {token}"}
            
            # Testar sem filtros
            response = client.get('/api/produtos/estatisticas', headers=headers)
            
            if response.status_code == 200:
                data = response.get_json()
                stats = data.get('estatisticas', {})
                
                print(f"✅ Endpoint respondeu com sucesso (200)")
                print(f"\n📊 RESPOSTA DO ENDPOINT:")
                print(f"   - Total de produtos: {stats.get('total_produtos')}")
                print(f"   - Produtos normal: {stats.get('produtos_normal')}")
                print(f"   - Produtos baixo estoque: {stats.get('produtos_baixo_estoque')}")
                print(f"   - Produtos esgotados: {stats.get('produtos_esgotados')}")
                print(f"   - Valor total estoque: R$ {stats.get('valor_total_estoque'):.2f}")
                print(f"   - Margem média: {stats.get('margem_media'):.2f}%")
                
                abc = stats.get('classificacao_abc', {})
                print(f"\n   ABC:")
                print(f"   - Classe A: {abc.get('A', 0)}")
                print(f"   - Classe B: {abc.get('B', 0)}")
                print(f"   - Classe C: {abc.get('C', 0)}")
                
                giro = stats.get('giro_estoque', {})
                print(f"\n   Giro:")
                print(f"   - Rápido: {giro.get('rapido', 0)}")
                print(f"   - Normal: {giro.get('normal', 0)}")
                print(f"   - Lento: {giro.get('lento', 0)}")
                
                # Verificar se há inconsistências
                print(f"\n{'='*80}")
                print(f"🔍 VERIFICAÇÃO DE INCONSISTÊNCIAS")
                print(f"{'='*80}\n")
                
                total_status = (stats.get('produtos_normal', 0) + 
                               stats.get('produtos_baixo_estoque', 0) + 
                               stats.get('produtos_esgotados', 0))
                
                if total_status != stats.get('total_produtos'):
                    print(f"❌ ERRO: Total de status ({total_status}) != Total de produtos ({stats.get('total_produtos')})")
                else:
                    print(f"✅ Total de status está correto")
                
                total_abc = abc.get('A', 0) + abc.get('B', 0) + abc.get('C', 0)
                if total_abc != stats.get('total_produtos'):
                    print(f"❌ ERRO: Total ABC ({total_abc}) != Total de produtos ({stats.get('total_produtos')})")
                else:
                    print(f"✅ Total ABC está correto")
                
                total_giro = giro.get('rapido', 0) + giro.get('normal', 0) + giro.get('lento', 0)
                if total_giro != stats.get('total_produtos'):
                    print(f"❌ ERRO: Total Giro ({total_giro}) != Total de produtos ({stats.get('total_produtos')})")
                else:
                    print(f"✅ Total Giro está correto")
                
                # Verificar valor de estoque
                if stats.get('valor_total_estoque', 0) < 0:
                    print(f"❌ ERRO: Valor total de estoque é negativo: R$ {stats.get('valor_total_estoque')}")
                else:
                    print(f"✅ Valor total de estoque está positivo")
                
                # Verificar margem
                if stats.get('margem_media', 0) < 0:
                    print(f"❌ ERRO: Margem média é negativa: {stats.get('margem_media')}%")
                else:
                    print(f"✅ Margem média está positiva")
                
            else:
                print(f"❌ Erro na requisição: {response.status_code}")
                print(f"   Resposta: {response.get_json()}")

if __name__ == '__main__':
    test_estatisticas()
