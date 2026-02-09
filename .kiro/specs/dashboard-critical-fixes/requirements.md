# Requirements Document

## Introduction

Este documento especifica os requisitos para correção de problemas críticos identificados no Dashboard Executivo do MercadinhoSys ERP. O sistema atual apresenta falhas graves que afetam qualidade, performance e experiência do usuário, incluindo dados vazios, arquivo monolítico de 2414 linhas, lógica de negócio no frontend, dados mockados e inconsistências. Esta correção é crítica para manter a qualidade enterprise do sistema em produção.

## Glossary

- **Dashboard_System**: O sistema completo de dashboard executivo do MercadinhoSys
- **Backend_API**: Camada de serviços Python/Flask que processa dados e expõe endpoints
- **Frontend_Component**: Componentes React TypeScript que renderizam a interface
- **DataLayer**: Camada de acesso a dados que executa queries no PostgreSQL
- **Analise_Temporal**: Módulo de análise de dados temporais (vendas por hora, tendências)
- **KPI_Modal**: Modal que exibe histórico detalhado de um indicador específico
- **Period_Filter**: Filtro global que define o período de análise (7, 30, 90 dias)
- **Vendas_Por_Hora**: Agregação de vendas por horário do dia (0-23h)
- **Produtos_Lentos**: Produtos com baixa rotatividade identificados por análise
- **Curva_ABC**: Classificação de produtos por importância (A: 80%, B: 15%, C: 5%)
- **Forecasting_Model**: Modelo estatístico para previsão de vendas futuras
- **Error_Boundary**: Componente React que captura erros e previne quebra total
- **Skeleton_Loader**: Componente de loading que mostra estrutura antes dos dados

## Requirements

### Requirement 1: Correção de Dados Vazios em Análise Temporal

**User Story:** Como gerente de projetos, eu quero que a análise de vendas por horário exiba dados reais do backend, para que eu possa tomar decisões baseadas em informações concretas sobre padrões de vendas ao longo do dia.

#### Acceptance Criteria

1. WHEN o Backend_API recebe requisição para análise temporal, THE DataLayer SHALL executar query agregando vendas por hora do dia (0-23h)
2. WHEN a query de vendas por hora é executada, THE DataLayer SHALL retornar total de vendas, quantidade de transações, lucro e margem para cada hora
3. WHEN o Frontend_Component renderiza a seção de análise temporal, THE Dashboard_System SHALL exibir dados reais de Vendas_Por_Hora sem mensagens de erro
4. IF o período filtrado não contém dados, THEN THE Dashboard_System SHALL exibir mensagem informativa ao invés de erro
5. WHEN dados de Vendas_Por_Hora são retornados, THE Backend_API SHALL incluir metadados sobre horários de pico e vale

### Requirement 2: Refatoração de Componente Monolítico

**User Story:** Como desenvolvedor, eu quero que o DashboardPage.tsx seja dividido em componentes menores e coesos, para que o código seja mais fácil de manter, testar e debugar.

#### Acceptance Criteria

1. THE Dashboard_System SHALL dividir DashboardPage.tsx em componentes com no máximo 500 linhas cada
2. WHEN componentes são criados, THE Frontend_Component SHALL seguir padrão de composição React com responsabilidade única
3. THE Dashboard_System SHALL criar componentes separados para KPICards, CurvaABCSection, AnaliseTemporalSection, ProdutosSection e RecomendacoesSection
4. WHEN componentes são refatorados, THE Frontend_Component SHALL manter toda funcionalidade existente sem regressões
5. THE Dashboard_System SHALL extrair hooks customizados para lógica de estado compartilhada

### Requirement 3: Migração de Lógica de Negócio para Backend

**User Story:** Como arquiteto de software, eu quero que toda lógica de negócio e cálculos complexos sejam executados no backend, para que o frontend seja apenas uma camada de apresentação e o sistema siga princípios de arquitetura limpa.

#### Acceptance Criteria

1. WHEN agrupamento mensal de timeseries é necessário, THE Backend_API SHALL processar e retornar dados já agregados
2. WHEN cálculo de insights de horários é necessário, THE Backend_API SHALL computar e retornar insights prontos
3. THE Frontend_Component SHALL NOT executar cálculos de negócio, apenas renderizar dados recebidos
4. WHEN identificação de Produtos_Lentos é necessária, THE Backend_API SHALL aplicar algoritmo de análise e retornar lista processada
5. THE DataLayer SHALL executar todas agregações e transformações de dados via SQL otimizado

### Requirement 4: Eliminação de Dados Mockados

**User Story:** Como gerente de projetos, eu quero que todas as recomendações e previsões sejam baseadas em modelos estatísticos reais, para que o sistema tenha credibilidade enterprise e forneça insights confiáveis.

#### Acceptance Criteria

1. THE Backend_API SHALL NOT retornar dados hardcoded ou fallbacks mockados em produção
2. WHEN previsões são solicitadas, THE Forecasting_Model SHALL usar biblioteca estatística (statsmodels ou prophet) para cálculos
3. WHEN recomendações de otimização são geradas, THE Backend_API SHALL basear em análise real de dados históricos
4. IF dados insuficientes para previsão, THEN THE Backend_API SHALL retornar indicador de confiança baixa ao invés de mock
5. THE Dashboard_System SHALL remover todos os cálculos simplistas (+10%) e substituir por modelos reais

### Requirement 5: Unificação de Fonte de Dados

**User Story:** Como desenvolvedor, eu quero que o backend seja a única fonte de verdade para todos os dados, para que não haja inconsistências entre cálculos duplicados no frontend e backend.

#### Acceptance Criteria

1. THE Backend_API SHALL ser a única fonte de verdade para identificação de Produtos_Lentos
2. THE Frontend_Component SHALL NOT duplicar lógica de cálculo que existe no backend
3. WHEN dados são requisitados, THE Dashboard_System SHALL buscar exclusivamente do Backend_API
4. THE DataLayer SHALL centralizar todas as queries e agregações de dados
5. WHEN lógica de negócio muda, THE Dashboard_System SHALL requerer alteração apenas no backend

### Requirement 6: Tratamento Robusto de Erros

**User Story:** Como usuário final, eu quero que o dashboard continue funcionando mesmo quando partes do backend falham, para que eu possa acessar informações disponíveis sem quebra total do sistema.

#### Acceptance Criteria

1. WHEN operações assíncronas são executadas, THE Frontend_Component SHALL envolver em try-catch com tratamento específico
2. WHEN erro ocorre em seção específica, THE Error_Boundary SHALL isolar falha e permitir funcionamento das demais seções
3. IF Backend_API está indisponível, THEN THE Dashboard_System SHALL exibir mensagem amigável e manter UI responsiva
4. WHEN erro de rede ocorre, THE Frontend_Component SHALL oferecer opção de retry ao usuário
5. THE Backend_API SHALL retornar códigos HTTP apropriados e mensagens de erro estruturadas

### Requirement 7: Modal de KPI Funcional

**User Story:** Como gerente, eu quero visualizar histórico detalhado de qualquer KPI ao clicar nele, para que eu possa analisar tendências e variações ao longo do tempo.

#### Acceptance Criteria

1. WHEN usuário clica em KPI, THE KPI_Modal SHALL abrir e iniciar carregamento de dados históricos
2. THE Backend_API SHALL fornecer endpoint específico para histórico de KPI com granularidade diária
3. WHEN dados históricos são carregados, THE KPI_Modal SHALL exibir gráfico de tendência e tabela de valores
4. WHILE dados estão sendo carregados, THE KPI_Modal SHALL exibir Skeleton_Loader
5. THE Dashboard_System SHALL implementar cache de dados históricos para evitar requisições repetidas

### Requirement 8: Filtro de Período Global Consistente

**User Story:** Como analista, eu quero que o filtro de período afete todos os dados do dashboard uniformemente, para que eu tenha visão consistente do período selecionado em todas as análises.

#### Acceptance Criteria

1. WHEN Period_Filter é alterado, THE Dashboard_System SHALL aplicar período a todas as queries de dados
2. THE Backend_API SHALL receber parâmetro de período (days) em todos os endpoints de dashboard
3. WHEN Vendas_Por_Hora são consultadas, THE DataLayer SHALL filtrar dados pelo período selecionado
4. WHEN Produtos_Lentos são identificados, THE Backend_API SHALL considerar apenas período filtrado
5. WHEN Curva_ABC é calculada, THE DataLayer SHALL usar exclusivamente dados do período selecionado

### Requirement 9: Biblioteca de Utilitários Compartilhados

**User Story:** Como desenvolvedor, eu quero funções utilitárias centralizadas para operações comuns, para que não haja duplicação de código e manutenção seja simplificada.

#### Acceptance Criteria

1. THE Dashboard_System SHALL criar módulo de utils para formatação de datas, moeda e números
2. WHEN formatação de moeda é necessária, THE Frontend_Component SHALL usar função centralizada do módulo utils
3. WHEN cálculo de crescimento percentual é necessário, THE Dashboard_System SHALL usar função compartilhada
4. THE Dashboard_System SHALL eliminar todas as duplicações de lógica de formatação
5. THE Frontend_Component SHALL importar utils de módulo centralizado ao invés de reimplementar

### Requirement 10: Melhorias de UX e Acessibilidade

**User Story:** Como usuário final, eu quero feedback visual claro durante carregamentos e transições suaves, para que a experiência seja profissional e agradável.

#### Acceptance Criteria

1. WHEN seção está carregando dados, THE Frontend_Component SHALL exibir Skeleton_Loader específico para aquela seção
2. WHEN transição de estado ocorre, THE Dashboard_System SHALL aplicar animações suaves (fade, slide)
3. WHEN ação do usuário é processada, THE Frontend_Component SHALL fornecer feedback visual imediato
4. THE Dashboard_System SHALL garantir tempo de carregamento inicial menor que 2 segundos
5. WHEN erro ocorre, THE Frontend_Component SHALL exibir mensagem com ícone, cor e ação clara para o usuário

### Requirement 11: Otimização de Performance

**User Story:** Como usuário final, eu quero que o dashboard carregue rapidamente e responda de forma fluida, para que eu possa trabalhar com eficiência sem esperas desnecessárias.

#### Acceptance Criteria

1. THE Backend_API SHALL implementar cache de queries frequentes com TTL apropriado
2. WHEN múltiplas requisições são necessárias, THE Dashboard_System SHALL executar em paralelo usando Promise.all
3. THE DataLayer SHALL usar índices otimizados para queries de agregação temporal
4. WHEN componentes são renderizados, THE Frontend_Component SHALL usar React.memo para evitar re-renders desnecessários
5. THE Dashboard_System SHALL implementar lazy loading para seções abaixo da dobra

### Requirement 12: Qualidade e Testabilidade

**User Story:** Como desenvolvedor, eu quero código bem testado e seguindo padrões de qualidade, para que o sistema seja confiável e fácil de evoluir.

#### Acceptance Criteria

1. THE Dashboard_System SHALL ter cobertura de testes unitários maior que 80%
2. WHEN componentes são criados, THE Frontend_Component SHALL incluir testes de renderização e interação
3. WHEN endpoints são implementados, THE Backend_API SHALL incluir testes de integração
4. THE Dashboard_System SHALL seguir princípios SOLID em toda arquitetura
5. WHEN código é commitado, THE Dashboard_System SHALL passar por linting e validação de tipos TypeScript
