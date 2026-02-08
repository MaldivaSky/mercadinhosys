# Dashboard Científico - Correlações e Anomalias IMPLEMENTADAS

## Data: 08/02/2026
## Status: ✅ ANÁLISES ESTATÍSTICAS AVANÇADAS COMPLETAS

---

## 🎓 ANÁLISES ESTATÍSTICAS IMPLEMENTADAS

### 1. CORRELAÇÕES ESTATÍSTICAS (Método de Pearson)

Implementei **3 correlações fundamentais** que revelam padrões ocultos no seu negócio:

#### 📊 Correlação 1: Vendas vs Dia da Semana
**O que analisa:**
- Identifica se há padrão semanal nas vendas
- Detecta quais dias da semana vendem mais/menos

**Insights gerados:**
- "Vendas aumentam significativamente no final da semana" (correlação > 0.5)
- "Vendas são maiores no início da semana" (correlação < -0.5)
- "Há tendência de aumento ao longo da semana" (correlação > 0.3)

**Ações recomendadas:**
- Ajustar estoque para dias de maior movimento
- Programar promoções nos dias de menor movimento
- Escalar equipe de acordo com o padrão semanal

#### 💰 Correlação 2: Ticket Médio vs Quantidade de Vendas
**O que analisa:**
- Relação entre volume de vendas e valor médio por compra
- Identifica se dias movimentados têm tickets maiores ou menores

**Insights gerados:**
- "Dias com mais vendas têm ticket médio maior" (correlação > 0.5)
- "Dias com mais vendas têm ticket médio menor - muitas compras pequenas" (correlação < -0.5)
- "Volume alto está associado a tickets menores" (correlação < -0.3)

**Ações recomendadas:**
- Incentivar vendas adicionais em dias de movimento
- Criar combos para aumentar ticket médio
- Treinar equipe em técnicas de upselling

#### 📈 Correlação 3: Vendas vs Tendência Temporal
**O que analisa:**
- Tendência geral das vendas ao longo do tempo
- Identifica se o negócio está crescendo ou declinando

**Insights gerados:**
- "Vendas em forte crescimento ao longo do período" (correlação > 0.5)
- "Vendas em queda consistente - atenção necessária" (correlação < -0.5)
- "Tendência de crescimento/queda moderado" (0.3 < |correlação| < 0.5)

**Ações recomendadas:**
- Manter estratégias que estão funcionando (se crescendo)
- Revisar estratégias urgentemente (se caindo)
- Analisar fatores externos (sazonalidade, concorrência)
- Ajustar metas baseado na tendência

---

### 2. DETECÇÃO DE ANOMALIAS (Método IQR - Interquartile Range)

Implementei **4 tipos de anomalias** usando estatística robusta:

#### 🔴 Anomalia 1: Vendas Anormalmente Baixas
**Método:** IQR (Interquartile Range)
- Calcula Q1 (quartil 25%) e Q3 (quartil 75%)
- Limite inferior = Q1 - 1.5 × IQR
- Identifica dias abaixo do limite

**Exemplo de detecção:**
```
"3 dia(s) com vendas anormalmente baixas detectados"
Impacto: 45.2% abaixo da média
Causa provável: feriado, problema operacional, falta de estoque
```

#### 🟢 Anomalia 2: Vendas Anormalmente Altas
**Método:** IQR (Interquartile Range)
- Limite superior = Q3 + 1.5 × IQR
- Identifica dias acima do limite

**Exemplo de detecção:**
```
"2 dia(s) com vendas excepcionalmente altas detectados"
Impacto: 78.5% acima da média
Causa provável: promoção bem-sucedida, evento especial
```

#### ⚠️ Anomalia 3: Alta Variabilidade
**Método:** Coeficiente de Variação (CV)
- CV = (Desvio Padrão / Média) × 100
- Alerta se CV > 50%

**Exemplo de detecção:**
```
"Vendas com alta variabilidade (CV: 62.3%)"
Impacto: 62.3%
Causa provável: Vendas inconsistentes - necessário estabilizar operação
```

#### 📉 Anomalia 4: Queda Súbita
**Método:** Comparação de médias móveis
- Compara últimos 3 dias vs 7 dias anteriores
- Alerta se queda > 30%

**Exemplo de detecção:**
```
"Queda súbita de 42.1% nas vendas nos últimos 3 dias"
Impacto: 42.1%
Causa provável: Investigar mudança de mercado, problema operacional
```

---

## 📐 FÓRMULAS ESTATÍSTICAS UTILIZADAS

### Correlação de Pearson
```
r = Σ[(xi - x̄)(yi - ȳ)] / √[Σ(xi - x̄)² × Σ(yi - ȳ)²]

Onde:
- r = coeficiente de correlação (-1 a 1)
- xi, yi = valores das variáveis
- x̄, ȳ = médias das variáveis
```

**Interpretação:**
- r > 0.7: Correlação forte positiva
- 0.5 < r < 0.7: Correlação moderada positiva
- 0.3 < r < 0.5: Correlação fraca positiva
- -0.3 < r < 0.3: Sem correlação
- r < -0.3: Correlação negativa (inversa)

### Método IQR (Interquartile Range)
```
IQR = Q3 - Q1

Limite Inferior = Q1 - 1.5 × IQR
Limite Superior = Q3 + 1.5 × IQR

Onde:
- Q1 = Quartil 25% (25% dos dados estão abaixo)
- Q3 = Quartil 75% (75% dos dados estão abaixo)
- IQR = Intervalo Interquartil
```

**Por que 1.5?**
- É o padrão estatístico de Tukey
- Identifica outliers moderados
- Balanceia sensibilidade vs falsos positivos

### Coeficiente de Variação
```
CV = (σ / μ) × 100

Onde:
- σ = Desvio padrão
- μ = Média
- CV = Coeficiente de variação (%)
```

**Interpretação:**
- CV < 15%: Baixa variabilidade (consistente)
- 15% < CV < 30%: Variabilidade moderada
- CV > 30%: Alta variabilidade (inconsistente)
- CV > 50%: Variabilidade excessiva (alerta!)

---

## 🔧 IMPLEMENTAÇÃO TÉCNICA

### Backend (Python)

**Arquivo:** `backend/app/dashboard_cientifico/models_layer.py`

**Novos métodos:**
1. `calculate_correlations()` - Calcula 3 correlações de Pearson
2. `_pearson_correlation()` - Implementação matemática da correlação
3. `detect_anomalies()` - Detecta 4 tipos de anomalias usando IQR

**Arquivo:** `backend/app/dashboard_cientifico/orchestration.py`

**Mudanças:**
```python
# Calcular correlações
correlations = _PM.calculate_correlations(sales_timeseries, expense_details)

# Detectar anomalias
anomalies = _PM.detect_anomalies(sales_timeseries, expense_details)

# Retornar no response
return {
    ...
    "correlations": correlations,
    "anomalies": anomalies
}
```

### Frontend (TypeScript/React)

**Arquivo:** `frontend/mercadinhosys-frontend/src/features/dashboard/DashboardPage.tsx`

**Mudanças:**
```typescript
// Extrair do backend
const { correlations = [], anomalies = [] } = data?.data || {};

// Mapear para insights_cientificos
const insights_cientificos = {
  correlações: correlations.map(...),
  anomalias: anomalies.map(...),
  previsoes: [...],
  recomendacoes_otimizacao: [...]
};
```

---

## 📊 EXEMPLO DE SAÍDA

### Correlações Detectadas:
```json
[
  {
    "variavel1": "Vendas Diárias",
    "variavel2": "Dia da Semana",
    "correlacao": 0.687,
    "significancia": 0.687,
    "insight": "Vendas aumentam significativamente no final da semana (sexta/sábado)",
    "explicacao": "Padrão semanal identificado nas vendas",
    "acoes": [
      "Ajuste o estoque para os dias de maior movimento",
      "Programe promoções nos dias de menor movimento",
      "Escale a equipe de acordo com o padrão semanal"
    ]
  },
  {
    "variavel1": "Ticket Médio",
    "variavel2": "Quantidade de Vendas",
    "correlacao": -0.542,
    "significancia": 0.542,
    "insight": "Dias com mais vendas têm ticket médio menor - muitas compras pequenas",
    "explicacao": "Relação entre volume de vendas e valor médio por compra",
    "acoes": [
      "Incentive vendas adicionais em dias de movimento",
      "Crie combos para aumentar ticket médio",
      "Treine equipe em técnicas de upselling"
    ]
  }
]
```

### Anomalias Detectadas:
```json
[
  {
    "tipo": "vendas_baixas",
    "descricao": "2 dia(s) com vendas anormalmente baixas detectados",
    "impacto": 38.5,
    "causa_provavel": "Possíveis causas: feriado, problema operacional, falta de estoque ou evento externo"
  },
  {
    "tipo": "queda_subita",
    "descricao": "Queda súbita de 31.2% nas vendas nos últimos 3 dias",
    "impacto": 31.2,
    "causa_provavel": "Investigar: mudança de mercado, problema operacional ou ação da concorrência"
  }
]
```

---

## 🎯 COMO USAR NO DASHBOARD

### Seção "Insights Científicos"

**Correlações Estatísticas:**
- Exibe cada correlação encontrada
- Mostra força da correlação (valor de -1 a 1)
- Apresenta insight em linguagem clara
- Lista ações práticas recomendadas
- Permite clicar para ver detalhes

**Anomalias:**
- Lista todas as anomalias detectadas
- Mostra tipo e descrição
- Indica impacto percentual
- Sugere causas prováveis
- Destaca anomalias críticas em vermelho

**Previsões:**
- Mantém as 7 previsões de vendas
- Mostra intervalo de confiança
- Indica tendência (crescimento/queda)

**Recomendações:**
- Lista ações prioritárias
- Indica complexidade (baixa/média/alta)
- Mostra impacto esperado

---

## ✅ VALIDAÇÃO

### Requisitos Mínimos:
- ✅ Mínimo 7 dias de dados para correlações
- ✅ Mínimo 7 dias de dados para anomalias
- ✅ Tratamento de erros robusto
- ✅ Valores padrão quando dados insuficientes

### Testes Realizados:
- ✅ Correlação de Pearson com dados reais
- ✅ Detecção IQR de outliers
- ✅ Cálculo de coeficiente de variação
- ✅ Detecção de quedas súbitas
- ✅ Integração frontend-backend

---

## 🚀 PRÓXIMAS MELHORIAS POSSÍVEIS

### Correlações Adicionais:
1. **Vendas vs Despesas** - Identificar se gastos impactam vendas
2. **Vendas vs Estoque** - Correlação entre nível de estoque e vendas
3. **Ticket Médio vs Dia da Semana** - Padrão de gastos por dia
4. **Vendas vs Clima** - Se integrar API de clima

### Anomalias Adicionais:
1. **Padrão de Horário** - Detectar horários anormais
2. **Produtos Específicos** - Anomalias por produto
3. **Clientes** - Comportamento anormal de clientes
4. **Sazonalidade** - Desvios do padrão sazonal

### Modelos Avançados:
1. **ARIMA** - Previsão de séries temporais
2. **Prophet** - Modelo do Facebook para sazonalidade
3. **Regressão Linear** - Prever vendas baseado em múltiplas variáveis
4. **Clustering** - Agrupar dias/produtos similares

---

## 📚 REFERÊNCIAS ESTATÍSTICAS

1. **Correlação de Pearson:**
   - Pearson, K. (1895). "Notes on regression and inheritance in the case of two parents"
   - Interpretação: Cohen, J. (1988). "Statistical Power Analysis"

2. **Método IQR:**
   - Tukey, J. W. (1977). "Exploratory Data Analysis"
   - Padrão: 1.5 × IQR para outliers moderados

3. **Coeficiente de Variação:**
   - Abdi, H. (2010). "Coefficient of variation"
   - Threshold: CV > 50% indica alta variabilidade

---

## 🎉 CONCLUSÃO

Implementei um sistema completo de análise estatística avançada que:

✅ **Calcula 3 correlações de Pearson** revelando padrões ocultos
✅ **Detecta 4 tipos de anomalias** usando método IQR robusto
✅ **Gera insights acionáveis** em linguagem clara
✅ **Recomenda ações práticas** baseadas em dados
✅ **Integra perfeitamente** com o dashboard existente

**Agora o dashboard é um verdadeiro sistema de Business Intelligence com análises estatísticas de nível profissional!** 🚀📊

---

## 📝 COMO TESTAR

1. Reinicie o backend: `python backend/run.py`
2. Acesse o dashboard no modo "Científico"
3. Vá até a seção "Insights Científicos"
4. Veja as correlações e anomalias detectadas
5. Clique em cada item para ver detalhes

**Os dados são calculados em tempo real baseado nos seus 90 dias de vendas!**
