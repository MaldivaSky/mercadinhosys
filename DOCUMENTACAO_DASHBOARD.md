# DOCUMENTAÇÃO DETALHADA — DASHBOARD (backend/app/routes/dashboard.py)

## Visão Geral
O arquivo dashboard.py implementa os endpoints e funções de análise para o dashboard do sistema. Ele entrega métricas, KPIs, tendências, projeções, insights e alertas para o painel administrativo e executivo do mercadinho.

---

## Endpoints Principais

### 1. resumo_dashboard()
- **Função:** Gera o resumo geral do dashboard para o usuário logado.
- **Retorna:**
  - Faturamento total, vendas do mês, ticket médio, clientes ativos, produtos em destaque, etc.
  - Exemplo de resposta:
    ```json
    {
      "faturamento_total": 100000,
      "vendas_mes": 12000,
      "ticket_medio": 45.5,
      "clientes_ativos": 320,
      "produtos_destaque": [ ... ]
    }
    ```

### 2. painel_admin()
- **Função:** Painel detalhado para administradores.
- **Retorna:**
  - Métricas detalhadas por período, comparativos, evolução de vendas, ranking de produtos, etc.

### 3. tendencia_mensal_detalhada()
- **Função:** Traz a tendência de vendas/movimentação mês a mês.
- **Retorna:**
  - Lista de meses, valores de vendas, crescimento, sazonalidade.

### 4. resumo_executivo()
- **Função:** Resumo executivo para tomada de decisão rápida.
- **Retorna:**
  - KPIs principais, alertas críticos, insights automáticos.

---

## Funções de Apoio e Métricas Avançadas

### calcular_metricas_avancadas(estabelecimento_id, data_referencia)
- Calcula métricas como crescimento, churn, ticket médio, margem, etc.

### obter_dados_completos(estabelecimento_id, hoje)
- Busca todos os dados brutos necessários para análises e gráficos.

### calcular_tendencias_avancadas(estabelecimento_id, hoje)
- Analisa tendências de vendas, clientes, produtos, sazonalidade.

### calcular_projecoes_detalhadas(dados, tendencias, hoje)
- Projeta vendas, estoque, demanda futura com base em tendências.

### gerar_insights_inteligentes(dados, tendencias, projecoes)
- Gera insights automáticos (ex: "queda de vendas em X", "produto Y em alta").

### calcular_kpis_principais(dados, projecoes)
- Calcula KPIs essenciais para o negócio (faturamento, margem, crescimento, etc).

### gerar_alertas_prioritarios_detalhados(estabelecimento_id)
- Gera alertas automáticos de risco, oportunidade, anomalias.

### obter_dados_tempo_real(estabelecimento_id, hoje, acesso_avancado=False)
- Busca dados em tempo real para o dashboard (vendas do dia, estoque crítico, etc).

### calcular_top_produtos_avancado(estabelecimento_id, inicio, fim, limite=10)
- Retorna ranking dos produtos mais vendidos no período.

---

## Observações de Integração
- Todos os endpoints retornam JSON pronto para consumo no frontend.
- As funções de apoio podem ser usadas para criar novos gráficos, cards e alertas no dashboard.
- Para refazer as métricas, basta criar novos endpoints ou adaptar as funções de cálculo já existentes.
- O arquivo é altamente modular: cada métrica pode ser expandida ou customizada facilmente.

---

## Sugestões para Refatoração/Evolução
- Centralizar a lógica de KPIs e tendências em serviços reutilizáveis.
- Adicionar testes automatizados para cada métrica.
- Documentar exemplos de payloads de entrada/saída para cada endpoint.
- Permitir filtros dinâmicos (por período, categoria, etc) nos endpoints.

---

## Resumo Rápido para IA/Dev
- Endpoints principais: resumo_dashboard, painel_admin, tendencia_mensal_detalhada, resumo_executivo
- Funções de cálculo: calcular_metricas_avancadas, calcular_tendencias_avancadas, calcular_kpis_principais, gerar_insights_inteligentes, gerar_alertas_prioritarios_detalhados
- Retornos: sempre JSON, pronto para frontend
- Para criar novas métricas: siga o padrão das funções de cálculo e endpoints existentes

Se precisar de exemplos de resposta, payloads, ou detalhamento de cada função, peça explicitamente.