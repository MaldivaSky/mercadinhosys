# 🚀 SPRINTS ESTRUTURADAS PARA AGENTES DE IA
## MercadinhoSys - Correções Críticas
**Data:** 26 de Abril de 2026  
**Versão:** 2.2.0 Scientific  
**Objetivo:** Entregar sistema 100% funcional em 4-5 dias

---

## 📋 ÍNDICE DE SPRINTS

1. [SPRINT 1: Dashboard - Renderização Completa](#sprint-1-dashboard)
2. [SPRINT 2: Múltiplos Pagamentos - Backend](#sprint-2-multiplos-pagamentos-backend)
3. [SPRINT 3: Múltiplos Pagamentos - Seed](#sprint-3-multiplos-pagamentos-seed)
4. [SPRINT 4: Delivery - Interface](#sprint-4-delivery-interface)
5. [SPRINT 5: Novo Cliente - Onboarding](#sprint-5-novo-cliente-onboarding)
6. [SPRINT 6: Refatoração - Código Limpo](#sprint-6-refatoracao-codigo-limpo)
7. [SPRINT 7: Testes - Validação Completa](#sprint-7-testes-validacao)

---

# SPRINT 1: Dashboard - Renderização Completa

## 🎯 Objetivo
Implementar renderização completa do dashboard com todas as 6 seções funcionando e modais de análise avançada.

## 📊 Contexto
- **Arquivo Principal:** `frontend/mercadinhosys-frontend/src/features/dashboard/DashboardPage.tsx` (5094 linhas)
- **Backend:** `backend/app/routes/dashboard.py` (endpoints OK)
- **Módulo BI:** `backend/app/dashboard_cientifico/` (OK)
- **Problema:** Frontend não renderiza todas as métricas retornadas pelo backend
- **Impacto:** Cliente não consegue visualizar KPIs completos

## 🔍 Análise Técnica

### O que o Backend Retorna
```json
{
  "visao_geral": {
    "total_vendas": 1500.00,
    "ticket_medio": 75.00,
    "quantidade_vendas": 20,
    "margem_lucro": 35.5
  },
  "analise_detalhada": {
    "curva_abc": {...},
    "rfm": {...}
  },
  "analise_temporal": {
    "tendencia_vendas": [...],
    "sazonalidade": [...]
  },
  "insights_cientificos": {
    "anomalias": [...],
    "recomendacoes": [...]
  },
  "rh": {
    "funcionarios_ativos": 5,
    "horas_trabalhadas": 200,
    "folha_pagamento": 5000.00
  },
  "fiados": {
    "total_fiado": 500.00,
    "contas_vencidas": 100.00,
    "clientes_fiado": 3
  }
}
```

### O que o Frontend Renderiza Atualmente
- ✅ Visão Geral (KPIs)
- ❌ Análise Detalhada (Curva ABC, RFM)
- ❌ Análise Temporal (Gráficos)
- ❌ Insights Científicos (Anomalias)
- ❌ RH (Métricas)
- ❌ Fiados (Contas a receber)

## 📝 Tarefas

### Tarefa 1.1: Diagnosticar Problema
**Tempo:** 30 minutos

```bash
# 1. Verificar o que o backend retorna
curl -H "Authorization: Bearer <token>" \
  http://localhost:5000/api/dashboard/cientifico?days=30 | jq

# 2. Abrir DevTools (F12) e ir para Network
# 3. Ir para Dashboard
# 4. Verificar resposta da requisição
# 5. Comparar com o que o frontend espera
```

**Critério de Aceite:**
- [ ] Conseguiu fazer a requisição ao backend
- [ ] Viu a resposta JSON completa
- [ ] Identificou quais seções estão faltando no frontend

---

### Tarefa 1.2: Implementar Seção "Análise Detalhada"
**Tempo:** 1 hora

**Arquivo:** `frontend/mercadinhosys-frontend/src/features/dashboard/DashboardPage.tsx`

**Código a Adicionar:**

```typescript
// Adicionar após a seção de Visão Geral (procure por "Visão Geral")

{/* ==================== ANÁLISE DETALHADA ==================== */}
<div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
  {/* Curva ABC */}
  <Card className="p-6">
    <h3 className="text-lg font-semibold mb-4">Curva ABC</h3>
    {dashboardData?.analise_detalhada?.curva_abc ? (
      <div className="space-y-4">
        {Object.entries(dashboardData.analise_detalhada.curva_abc).map(([classe, dados]: any) => (
          <div key={classe} className="flex items-center justify-between">
            <span className="font-medium">{classe}</span>
            <div className="flex items-center gap-2">
              <div className="w-32 bg-gray-200 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full ${
                    classe === 'A' ? 'bg-green-500' : 
                    classe === 'B' ? 'bg-yellow-500' : 
                    'bg-red-500'
                  }`}
                  style={{ width: `${dados.percentual}%` }}
                />
              </div>
              <span className="text-sm text-gray-600">{dados.percentual}%</span>
            </div>
          </div>
        ))}
      </div>
    ) : (
      <p className="text-gray-500">Carregando...</p>
    )}
  </Card>

  {/* RFM */}
  <Card className="p-6">
    <h3 className="text-lg font-semibold mb-4">Análise RFM</h3>
    {dashboardData?.analise_detalhada?.rfm ? (
      <div className="space-y-4">
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center">
            <p className="text-2xl font-bold text-blue-600">
              {dashboardData.analise_detalhada.rfm.recencia_media}
            </p>
            <p className="text-sm text-gray-600">Dias (Recência)</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-green-600">
              {dashboardData.analise_detalhada.rfm.frequencia_media}
            </p>
            <p className="text-sm text-gray-600">Compras (Frequência)</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-purple-600">
              R$ {dashboardData.analise_detalhada.rfm.valor_medio}
            </p>
            <p className="text-sm text-gray-600">Valor (Monetário)</p>
          </div>
        </div>
      </div>
    ) : (
      <p className="text-gray-500">Carregando...</p>
    )}
  </Card>
</div>
```

**Critério de Aceite:**
- [ ] Seção "Análise Detalhada" aparece no dashboard
- [ ] Curva ABC renderiza com barras de progresso
- [ ] RFM mostra 3 métricas (Recência, Frequência, Monetário)
- [ ] Dados vêm do backend corretamente

---

### Tarefa 1.3: Implementar Seção "Análise Temporal"
**Tempo:** 1 hora

**Código a Adicionar:**

```typescript
{/* ==================== ANÁLISE TEMPORAL ==================== */}
<div className="mb-8">
  <Card className="p-6">
    <h3 className="text-lg font-semibold mb-4">Tendência de Vendas</h3>
    {dashboardData?.analise_temporal?.tendencia_vendas ? (
      <div className="h-64 bg-gray-50 rounded-lg p-4">
        {/* Usar biblioteca de gráficos (Recharts, Chart.js, etc) */}
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={dashboardData.analise_temporal.tendencia_vendas}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="data" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="total" 
              stroke="#8884d8" 
              name="Total de Vendas"
            />
            <Line 
              type="monotone" 
              dataKey="quantidade" 
              stroke="#82ca9d" 
              name="Quantidade"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    ) : (
      <p className="text-gray-500">Carregando...</p>
    )}
  </Card>
</div>
```

**Critério de Aceite:**
- [ ] Gráfico de tendência renderiza
- [ ] Mostra 2 linhas (Total e Quantidade)
- [ ] Eixos X e Y estão corretos
- [ ] Dados vêm do backend

---

### Tarefa 1.4: Implementar Seção "Insights Científicos"
**Tempo:** 1 hora

**Código a Adicionar:**

```typescript
{/* ==================== INSIGHTS CIENTÍFICOS ==================== */}
<div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
  {/* Anomalias */}
  <Card className="p-6">
    <h3 className="text-lg font-semibold mb-4">Anomalias Detectadas</h3>
    {dashboardData?.insights_cientificos?.anomalias?.length > 0 ? (
      <div className="space-y-3">
        {dashboardData.insights_cientificos.anomalias.map((anomalia: any, idx: number) => (
          <div 
            key={idx}
            className="p-3 bg-red-50 border border-red-200 rounded-lg cursor-pointer hover:bg-red-100"
            onClick={() => setAnomaliaModal(anomalia)}
          >
            <p className="font-medium text-red-900">{anomalia.tipo}</p>
            <p className="text-sm text-red-700">{anomalia.descricao}</p>
            <p className="text-xs text-red-600 mt-1">Confiança: {anomalia.confianca}%</p>
          </div>
        ))}
      </div>
    ) : (
      <p className="text-gray-500">Nenhuma anomalia detectada</p>
    )}
  </Card>

  {/* Recomendações */}
  <Card className="p-6">
    <h3 className="text-lg font-semibold mb-4">Recomendações</h3>
    {dashboardData?.insights_cientificos?.recomendacoes?.length > 0 ? (
      <div className="space-y-3">
        {dashboardData.insights_cientificos.recomendacoes.map((rec: any, idx: number) => (
          <div 
            key={idx}
            className="p-3 bg-blue-50 border border-blue-200 rounded-lg cursor-pointer hover:bg-blue-100"
            onClick={() => setRecomendacaoModal(rec)}
          >
            <p className="font-medium text-blue-900">{rec.titulo}</p>
            <p className="text-sm text-blue-700">{rec.descricao}</p>
            <p className="text-xs text-blue-600 mt-1">Impacto: {rec.impacto}</p>
          </div>
        ))}
      </div>
    ) : (
      <p className="text-gray-500">Nenhuma recomendação</p>
    )}
  </Card>
</div>
```

**Critério de Aceite:**
- [ ] Anomalias renderizam com estilo diferenciado
- [ ] Recomendações renderizam com estilo diferenciado
- [ ] Clique abre modal com detalhes
- [ ] Dados vêm do backend

---

### Tarefa 1.5: Implementar Seção "RH"
**Tempo:** 45 minutos

**Código a Adicionar:**

```typescript
{/* ==================== RH ==================== */}
<div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
  <Card className="p-6">
    <h3 className="text-sm font-medium text-gray-600">Funcionários Ativos</h3>
    <p className="text-3xl font-bold mt-2">
      {dashboardData?.rh?.funcionarios_ativos || 0}
    </p>
  </Card>
  <Card className="p-6">
    <h3 className="text-sm font-medium text-gray-600">Horas Trabalhadas</h3>
    <p className="text-3xl font-bold mt-2">
      {dashboardData?.rh?.horas_trabalhadas || 0}h
    </p>
  </Card>
  <Card className="p-6">
    <h3 className="text-sm font-medium text-gray-600">Folha de Pagamento</h3>
    <p className="text-3xl font-bold mt-2">
      R$ {dashboardData?.rh?.folha_pagamento?.toFixed(2) || '0.00'}
    </p>
  </Card>
</div>
```

**Critério de Aceite:**
- [ ] 3 cards renderizam com dados de RH
- [ ] Números estão corretos
- [ ] Formatação está correta

---

### Tarefa 1.6: Implementar Seção "Fiados"
**Tempo:** 45 minutos

**Código a Adicionar:**

```typescript
{/* ==================== FIADOS ==================== */}
<div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
  <Card className="p-6">
    <h3 className="text-sm font-medium text-gray-600">Total em Fiado</h3>
    <p className="text-3xl font-bold mt-2 text-orange-600">
      R$ {dashboardData?.fiados?.total_fiado?.toFixed(2) || '0.00'}
    </p>
  </Card>
  <Card className="p-6">
    <h3 className="text-sm font-medium text-gray-600">Contas Vencidas</h3>
    <p className="text-3xl font-bold mt-2 text-red-600">
      R$ {dashboardData?.fiados?.contas_vencidas?.toFixed(2) || '0.00'}
    </p>
  </Card>
  <Card className="p-6">
    <h3 className="text-sm font-medium text-gray-600">Clientes com Fiado</h3>
    <p className="text-3xl font-bold mt-2">
      {dashboardData?.fiados?.clientes_fiado || 0}
    </p>
  </Card>
</div>
```

**Critério de Aceite:**
- [ ] 3 cards renderizam com dados de fiados
- [ ] Cores diferenciadas (orange, red)
- [ ] Números estão corretos

---

### Tarefa 1.7: Implementar Modais de Análise
**Tempo:** 1.5 horas

**Criar arquivo:** `frontend/mercadinhosys-frontend/src/features/dashboard/components/modals/AnomalyDetailsModal.tsx`

```typescript
import React from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface AnomalyDetailsModalProps {
  anomalia: any;
  onClose: () => void;
}

export const AnomalyDetailsModal: React.FC<AnomalyDetailsModalProps> = ({ anomalia, onClose }) => {
  if (!anomalia) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <Card className="w-full max-w-2xl p-6">
        <h2 className="text-2xl font-bold mb-4">{anomalia.tipo}</h2>
        
        <div className="space-y-4 mb-6">
          <div>
            <h3 className="font-semibold text-gray-700">Descrição</h3>
            <p className="text-gray-600">{anomalia.descricao}</p>
          </div>
          
          <div>
            <h3 className="font-semibold text-gray-700">Causa Provável</h3>
            <p className="text-gray-600">{anomalia.causa}</p>
          </div>
          
          <div>
            <h3 className="font-semibold text-gray-700">Ação Recomendada</h3>
            <p className="text-gray-600">{anomalia.acao}</p>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-600">Confiança</p>
              <p className="text-2xl font-bold">{anomalia.confianca}%</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Impacto</p>
              <p className="text-2xl font-bold">{anomalia.impacto}</p>
            </div>
          </div>
        </div>
        
        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={onClose}>Fechar</Button>
          <Button onClick={() => {/* Ação */}}>Tomar Ação</Button>
        </div>
      </Card>
    </div>
  );
};
```

**Critério de Aceite:**
- [ ] Modal abre ao clicar em anomalia
- [ ] Mostra todos os detalhes
- [ ] Pode fechar modal
- [ ] Botão "Tomar Ação" funciona

---

### Tarefa 1.8: Testar Dashboard Completo
**Tempo:** 1 hora

**Teste Manual:**

```
1. Acessar http://localhost/dashboard
2. Verificar se todas as 6 seções aparecem:
   - [ ] Visão Geral (KPIs)
   - [ ] Análise Detalhada (Curva ABC, RFM)
   - [ ] Análise Temporal (Gráficos)
   - [ ] Insights Científicos (Anomalias, Recomendações)
   - [ ] RH (Funcionários, Horas, Folha)
   - [ ] Fiados (Total, Vencidas, Clientes)

3. Clicar em cada modal:
   - [ ] Modal de Anomalia abre
   - [ ] Modal de Recomendação abre
   - [ ] Modal de Produto Estrela abre
   - [ ] Modal de Produto Lento abre

4. Verificar performance:
   - [ ] Dashboard carrega em < 2s
   - [ ] Sem erros no console
   - [ ] Sem memory leaks

5. Testar com diferentes períodos:
   - [ ] 7 dias
   - [ ] 30 dias
   - [ ] 90 dias
   - [ ] Período customizado
```

**Critério de Aceite:**
- [ ] Todas as 6 seções renderizam
- [ ] Todos os modais funcionam
- [ ] Performance < 2s
- [ ] Sem erros no console

---

## ✅ Critérios de Aceite Gerais (Sprint 1)

- [ ] Dashboard renderiza todas as 6 seções
- [ ] Todos os gráficos carregam corretamente
- [ ] Todos os modais funcionam
- [ ] Dados vêm do backend corretamente
- [ ] Performance < 2 segundos
- [ ] Sem erros no console
- [ ] Responsivo em mobile
- [ ] Teste manual passou 100%

## 🧪 Testes Automatizados

```typescript
// Adicionar em backend/tests/test_dashboard.py
def test_dashboard_cientifico_completo():
    """Testa se dashboard retorna todas as seções"""
    response = client.get('/api/dashboard/cientifico?days=30')
    assert response.status_code == 200
    
    data = response.get_json()
    assert 'visao_geral' in data
    assert 'analise_detalhada' in data
    assert 'analise_temporal' in data
    assert 'insights_cientificos' in data
    assert 'rh' in data
    assert 'fiados' in data
```

---

