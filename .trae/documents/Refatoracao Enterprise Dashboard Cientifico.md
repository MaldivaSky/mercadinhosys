## Objetivo
Reconciliar o visual Enterprise (grid 12 colunas + dark mode + skeletons) com 100% das funcionalidades do dashboard científico (despesas, previsões, insights, modais e análises), sem regressões.

## Diagnóstico Rápido (por que perdeu utilidade)
- O DashboardPage atual foi reescrito como “MVP visual”: renderiza apenas KPIs, 1 gráfico principal simplificado, ABC resumido e um painel RFM reduzido.
- O dashboardService ficou com responsabilidades misturadas (endpoints legados vs científico) e parte do fluxo de dados/normalização que existia antes deixou de alimentar os componentes.
- O backend científico já entrega `timeseries`, `forecast`, `expenses`, `abc`, `rfm`, `recomendacoes` — mas a UI não está usando isso por completo.

## Plano de Implementação (Sênior / Enterprise + Funcional)

## 1) Normalização de dados no serviço (fonte única)
- Reestruturar o dashboardService para expor um único método `getEnterpriseDashboard(filters)`.
- Esse método vai:
  - Buscar `/dashboard/cientifico?dias=...` (principal).
  - Opcionalmente buscar endpoints legados só quando necessário para filtros (ex.: lista de categorias) sem quebrar o modo científico.
  - Normalizar tudo para um modelo único:
    - `kpis[]` com `sparkline[]` vindo de `timeseries`.
    - `trendSeries[]` combinando `timeseries` (real) + `forecast` (previsto) no mesmo array, pronto para o ComposedChart.
    - `expenses[]` (despesas detalhadas) + agregações (top categorias, %).
    - `abc` (produtos + resumo + insights) em formato pronto para gráfico e tabela.
    - `rfm` (segments + janela + lista quando existir).
    - `insights` (recomendacoes, correlações, previsões/intervalos).
- Remover código placeholder e duplicações atuais do serviço para evitar erros e regressões.

## 2) Recuperar funcionalidades perdidas no DashboardPage mantendo o design
- Manter:
  - Fundo `bg-gray-50 dark:bg-slate-950`.
  - Cards `bg-white dark:bg-slate-900 border-gray-100 dark:border-slate-800`.
  - Tipografia e paleta (Indigo/Emerald/Rose), `rounded-2xl`, `shadow-sm`.
- Reintroduzir (em layout enterprise):
  - **Despesas**: gráfico (barra/donut) + lista com percentuais.
  - **Previsões**: linha/área “Previsto” + intervalos/confiabilidade quando disponível.
  - **Insights Científicos**: cards/sections para correlações, anomalias, previsões e recomendações.
  - **Curva ABC interativa**: toggle Classe A/B/C/All + tabela detalhada (top produtos) + insights pareto.
  - **RFM**: visual mais informativo (ex.: barras/donut por segmento) e CTA para listas (quando houver).

## 3) Restaurar os Modais (sem quebrar o novo layout)
- Reacoplar:
  - RecommendationDetailsModal (ações/CTA, listas de clientes/produtos).
  - CorrelationDetailsModal (correlações, significância, ações sugeridas).
  - (Se existir no projeto) modal de anomalias/previsões.
- Garantir tipagem e mapeamento de campos para não haver crashes ao clicar.

## 4) Filtros retráteis realmente funcionais
- FilterBar vai disparar `getEnterpriseDashboard(filters)`.
- Implementar filtros:
  - Período (7/15/30/90): impacta `dias` do endpoint científico e recalcula sparklines.
  - Comparar período anterior: calcula no service (ex.: compara soma últimos N dias vs N dias anteriores) e devolve `trend%` nos KPIs.
  - Categoria de produto: 
    - Opção A (sem backend): filtrar apenas o que tiver categoria disponível (se vier do endpoint legado).
    - Opção B (melhor): estender backend para retornar categoria nos produtos do ABC/top_products; assim o filtro funciona 100% no modo científico.

## 5) Gráficos “Dark-aware” (Recharts)
- Centralizar `themeColors` e aplicar em TODOS os gráficos:
  - CartesianGrid `#1e293b` no dark.
  - ticks/eixos `#94a3b8` no dark.
  - tooltip `bg-slate-950`/bordas `#1e293b`.

## 6) Tooltips ricos: “Custo Médio Ponderado” e “Margem Real”
- Situação atual do backend:
  - A análise ABC calcula margem usando `preco_custo`, mas esse custo não é retornado no payload do ABC.
- Plano:
  - **Frontend imediato**: exibir “Margem (%)” (já vem no ABC) e, onde houver custo, mostrar “Custo Base”.
  - **Melhoria correta (recomendada)**: ajustar o backend científico para incluir no ABC por produto:
    - `preco_custo` (ou custo unitário base) e, quando disponível, `custo_medio_ponderado` (WAC).
  - Com isso, o tooltip do ABC e tabelas mostram:
    - Custo Médio Ponderado (WAC)
    - Margem Real (calculada com WAC)

## 7) Skeleton loading por seção (percepção de performance)
- Manter `loading` global só para primeira carga.
- Em mudanças de filtro:
  - Skeleton nos KPIs.
  - Skeleton no gráfico principal.
  - Skeleton nos cards ABC/RFM/Despesas.

## 8) Validação (sem achismo)
- Conferir no frontend:
  - Troca de tema (claro/escuro) e legibilidade dos gráficos.
  - Filtros realmente mudando os números e séries.
  - Clique em recomendações/correlações abrindo modais sem erros.
  - Despesas e previsões aparecendo com dados do seed local (90 dias).
- Conferir payload do backend científico:
  - `timeseries` com histórico.
  - `forecast` presente.
  - `expenses` presente.
  - `abc` com resumo e produtos.
  - `rfm` com segments.

## Entregáveis
- DashboardPage.tsx funcional + enterprise.
- dashboardService.ts limpo, tipado e com normalização.
- Modais restaurados.
- Filtros funcionando.
- (Opcional/recomendado) pequena extensão no backend científico para WAC/custos no ABC.

Se você confirmar, eu começo pela normalização do dashboardService (fonte única), e em seguida restauro as seções perdidas no DashboardPage mantendo o layout e o dark mode.