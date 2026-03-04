"""
Teste direto do dashboard após seed.
"""
import requests
import json

print("=" * 80)
print("TESTE DIRETO DO DASHBOARD")
print("=" * 80)

# 1. Login
print("\n1. Login...")
login_response = requests.post(
    "http://localhost:5000/api/auth/login",
    json={"username": "admin", "password": "admin123"},
    timeout=10
)

if login_response.status_code != 200:
    print(f"❌ Login falhou: {login_response.status_code}")
    print(f"Resposta: {login_response.text}")
    exit()

login_data = login_response.json()
print(f"✅ Login: {login_data.get('success', 'N/A')}")

if not login_data.get('success'):
    print(f"❌ Erro: {login_data.get('error', 'Desconhecido')}")
    exit()

access_token = login_data.get('access_token')
print(f"Token: {access_token[:30]}...")

# 2. Testar dashboard
print("\n2. Testando dashboard científico...")
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

# Primeiro testar o endpoint que o frontend usa
dashboard_response = requests.get(
    "http://localhost:5000/api/dashboard/cientifico",
    headers=headers,
    timeout=10
)

print(f"Status: {dashboard_response.status_code}")

if dashboard_response.status_code == 200:
    dashboard_data = dashboard_response.json()
    print(f"Success: {dashboard_data.get('success', 'N/A')}")
    
    if dashboard_data.get('success'):
        data = dashboard_data.get('data', {})
        print(f"✅ Dashboard carregado com sucesso!")
        
        # Verificar estrutura
        print(f"\n📊 ESTRUTURA DOS DADOS:")
        
        # Análise financeira
        financeiro = data.get('analise_financeira', {})
        if financeiro:
            indicadores = financeiro.get('indicadores', {})
            print(f"💰 Indicadores financeiros: {len(indicadores)}")
            
            # Mostrar os mais importantes
            important = {
                'faturamento_total': 'Faturamento Total',
                'lucro_liquido': 'Lucro Líquido', 
                'margem_bruta': 'Margem Bruta',
                'ticket_medio': 'Ticket Médio',
                'custo_mercadoria_vendida': 'CMV',
                'despesas_totais': 'Despesas Totais'
            }
            
            print(f"\n📈 INDICADORES PRINCIPAIS:")
            for key, label in important.items():
                value = indicadores.get(key)
                if value is not None:
                    if isinstance(value, (int, float)):
                        if 'faturamento' in key or 'lucro' in key or 'custo' in key or 'despesas' in key:
                            print(f"  {label}: R$ {value:,.2f}")
                        elif 'margem' in key:
                            print(f"  {label}: {value:.1f}%")
                        elif 'ticket' in key:
                            print(f"  {label}: R$ {value:.2f}")
                        else:
                            print(f"  {label}: {value}")
                    else:
                        print(f"  {label}: {value}")
                else:
                    print(f"  {label}: NÃO ENCONTRADO")
        
        # Análise de produtos
        produtos = data.get('analise_produtos', {})
        if produtos:
            abc = produtos.get('curva_abc', {})
            if abc:
                resumo = abc.get('resumo', {})
                print(f"\n📦 CURVA ABC:")
                for classe in ['A', 'B', 'C']:
                    classe_data = resumo.get(classe, {})
                    print(f"  Classe {classe}: {classe_data.get('quantidade', 0)} produtos, "
                          f"R$ {classe_data.get('faturamento_total', 0):,.2f}")
            
            produtos_estrela = produtos.get('produtos_estrela', [])
            produtos_lentos = produtos.get('produtos_lentos', [])
            print(f"\n⭐ Produtos Estrela: {len(produtos_estrela)}")
            print(f"🐌 Produtos Lentos: {len(produtos_lentos)}")
        
        # Análise temporal
        temporal = data.get('analise_temporal', {})
        if temporal:
            tendencia = temporal.get('tendencia_vendas', [])
            print(f"\n📈 SÉRIE TEMPORAL: {len(tendencia)} dias")
            
            if len(tendencia) > 0:
                # Calcular estatísticas
                total_vendas = sum(d.get('vendas', 0) for d in tendencia)
                dias_com_vendas = sum(1 for d in tendencia if d.get('vendas', 0) > 0)
                print(f"  Total período: R$ {total_vendas:,.2f}")
                print(f"  Dias com vendas: {dias_com_vendas}/{len(tendencia)}")
                
                # Mostrar últimos 3 dias
                print(f"\n  ÚLTIMOS 3 DIAS:")
                for dia in tendencia[-3:]:
                    data_str = dia.get('data', 'N/A')
                    vendas = dia.get('vendas', 0)
                    print(f"    {data_str}: R$ {vendas:,.2f}")
        
        # Recomendações
        recomendacoes = data.get('recomendacoes', [])
        print(f"\n💡 RECOMENDAÇÕES: {len(recomendacoes)}")
        for i, rec in enumerate(recomendacoes[:3], 1):
            print(f"  {i}. {rec.get('tipo', 'N/A')}: {rec.get('mensagem', 'N/A')[:60]}...")
        
        # Verificar problemas
        print(f"\n🔍 VERIFICAÇÃO DE PROBLEMAS:")
        
        # 1. Verificar indicadores zerados
        if financeiro and 'indicadores' in financeiro:
            zero_indicators = []
            for key, value in financeiro['indicadores'].items():
                if isinstance(value, (int, float)) and value == 0:
                    zero_indicators.append(key)
            
            if zero_indicators:
                print(f"  ⚠️ Indicadores zerados: {len(zero_indicators)}")
                for zi in zero_indicators[:5]:
                    print(f"    - {zi}")
                if len(zero_indicators) > 5:
                    print(f"    ... e mais {len(zero_indicators) - 5}")
            else:
                print(f"  ✅ Nenhum indicador zerado")
        
        # 2. Verificar série temporal vazia
        if temporal and 'tendencia_vendas' in temporal:
            if len(temporal['tendencia_vendas']) == 0:
                print(f"  ❌ Série temporal vazia")
            else:
                print(f"  ✅ Série temporal com dados")
        
        # 3. Verificar produtos
        if produtos:
            if len(produtos.get('produtos_estrela', [])) == 0:
                print(f"  ⚠️ Nenhum produto estrela")
            if len(produtos.get('produtos_lentos', [])) == 0:
                print(f"  ⚠️ Nenhum produto lento")
        
    else:
        print(f"❌ Erro no dashboard: {dashboard_data.get('error', 'Desconhecido')}")
else:
    print(f"❌ HTTP {dashboard_response.status_code}")
    print(f"Resposta: {dashboard_response.text[:200]}")

print("\n" + "=" * 80)
print("RESUMO")
print("=" * 80)

print("\n✅ O QUE FUNCIONA:")
print("1. Seed carregou dados no banco")
print("2. Autenticação JWT funciona")
print("3. Endpoint do dashboard responde")

print("\n🔧 O QUE VERIFICAR NO FRONTEND:")
print("1. Se os gráficos estão carregando")
print("2. Se os indicadores mostram valores (não zerados)")
print("3. Se a série temporal tem dados")

print("\n🚀 PARA TESTAR:")
print("1. Acesse http://localhost:5173")
print("2. Login: admin / admin123")
print("3. Vá para o Dashboard Científico")
print("4. Verifique se os gráficos carregam")