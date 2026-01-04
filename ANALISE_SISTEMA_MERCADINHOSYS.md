# 📊 ANÁLISE COMPLETA DO SISTEMA MERCADINHOSYS

**Data da Análise:** 04 de Janeiro de 2026  
**Versão do Sistema:** 1.0  
**Ambiente:** Desenvolvimento

---

## 🎯 RESUMO EXECUTIVO

O **MercadinhoSys** é um sistema completo de gestão para mercados/mercadinhos desenvolvido em:
- **Backend:** Python + Flask + SQLAlchemy + SQLite
- **Frontend:** React + TypeScript + Vite + Tailwind CSS
- **Autenticação:** JWT (JSON Web Tokens)
- **API:** RESTful com documentação Swagger

### Módulos Principais
1. **PDV (Ponto de Venda)** - Vendas em tempo real
2. **Dashboard** - Métricas e analytics avançados
3. **Produtos** - Gestão de estoque
4. **Clientes** - CRM e segmentação RFM
5. **Funcionários** - Gestão de equipe
6. **Fornecedores** - Gestão de parceiros
7. **Vendas** - Histórico e relatórios
8. **Despesas** - Controle financeiro
9. **Relatórios** - Business Intelligence

---

## 🗄️ ESTRUTURA DO BANCO DE DADOS

### Modelo de Dados (SQLite)

#### Tabela: `estabelecimentos`
```sql
- id (PK)
- nome
- cnpj
- telefone, email
- cep, endereco, cidade, estado
- data_cadastro
- ativo
```

#### Tabela: `funcionarios`
```sql
- id (PK)
- estabelecimento_id (FK)
- nome, username, cpf, telefone, email
- foto_url
- cargo (dono, gerente, caixa, vendedor)
- role (admin, gerente, funcionario)
- status (ativo, inativo, afastado)
- senha_hash
- comissao_percentual
- data_admissao, data_demissao
- ativo
- permissoes (JSON)
- created_at, updated_at
```

#### Tabela: `clientes`
```sql
- id (PK)
- estabelecimento_id (FK)
- nome, cpf_cnpj
- telefone, email, endereco
- data_cadastro, data_nascimento
- limite_credito
- observacoes
- total_compras
- frequencia_compras
- valor_medio_compra
- ultima_compra
- dias_ultima_compra
- segmento_rfm (ouro, prata, bronze, em_risco, perdido, novo)
```

#### Tabela: `fornecedores`
```sql
- id (PK)
- estabelecimento_id (FK)
- nome, cnpj
- telefone, email
- endereco, cidade, estado, cep
- contato_comercial, contato_nome, celular_comercial
- ativo
- prazo_entrega, forma_pagamento
- avaliacao
- tempo_medio_entrega
- taxa_atendimento
- observacoes
```

#### Tabela: `produtos`
```sql
- id (PK)
- estabelecimento_id (FK)
- fornecedor_id (FK)
- codigo_barras (UNIQUE)
- nome, descricao
- marca, fabricante
- categoria, subcategoria
- unidade_medida (UN, KG, LT, etc)
- quantidade
- quantidade_minima
- localizacao
- preco_custo, preco_venda
- margem_lucro
- data_validade
- lote
- ativo
- total_vendido
- quantidade_vendida
- frequencia_venda
- ultima_venda
- ncm, cest
- foto_url
```

#### Tabela: `vendas`
```sql
- id (PK)
- estabelecimento_id (FK)
- cliente_id (FK, nullable)
- funcionario_id (FK)
- codigo (UNIQUE)
- subtotal, desconto, total
- forma_pagamento (dinheiro, cartao_credito, cartao_debito, pix)
- valor_recebido, troco
- status (pendente, finalizada, cancelada)
- observacoes
- data_venda
- created_at, updated_at
- cancelada_em, cancelada_por, motivo_cancelamento
- quantidade_itens
- tipo_venda (normal, promocional, atacado)
```

#### Tabela: `venda_itens`
```sql
- id (PK)
- venda_id (FK)
- produto_id (FK)
- produto_nome
- descricao
- produto_codigo
- produto_unidade
- quantidade
- preco_unitario
- desconto
- total_item
- custo_unitario
- margem_item
- created_at
```

#### Tabela: `movimentacoes_estoque`
```sql
- id (PK)
- estabelecimento_id (FK)
- produto_id (FK)
- venda_id (FK, nullable)
- funcionario_id (FK)
- tipo (entrada, saida, ajuste, perda, transferencia)
- quantidade
- quantidade_anterior
- quantidade_atual
- custo_unitario
- valor_total
- motivo
- documento
- created_at
```

#### Tabela: `despesas`
```sql
- id (PK)
- estabelecimento_id (FK)
- descricao
- categoria
- tipo (fixa, variavel)
- valor
- data_despesa
- forma_pagamento
- recorrente
- observacoes
- created_at, updated_at
```

#### Tabela: `configuracoes`
```sql
- id (PK)
- estabelecimento_id (FK, UNIQUE)
- logo_url
- cor_principal
- dias_alerta_validade
- estoque_minimo_padrao
- meta_vendas_diaria
- meta_vendas_mensal
- dashboard_analytics_avancado
- formas_pagamento (JSON)
```

#### Tabela: `dashboard_metricas`
```sql
- id (PK)
- estabelecimento_id (FK)
- data_referencia
- total_vendas_dia, quantidade_vendas_dia
- ticket_medio_dia
- clientes_atendidos_dia
- total_vendas_mes, quantidade_vendas_mes
- total_despesas_mes
- lucro_bruto_mes
- crescimento_vs_ontem
- crescimento_mensal
- top_produtos_json
- created_at, updated_at
```

---

## 🔌 MAPEAMENTO COMPLETO DE ENDPOINTS

### 🔐 Autenticação (`/api/auth`)

| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| POST | `/login` | Login com username/password | ❌ |
| POST | `/refresh` | Renovar token JWT | ✅ |
| GET | `/validate` | Validar token atual | ✅ |
| POST | `/logout` | Logout e blacklist token | ✅ |
| GET | `/profile` | Obter perfil do usuário | ✅ |
| PUT | `/profile` | Atualizar perfil | ✅ |
| GET | `/sessions` | Listar sessões ativas | ✅ |
| POST | `/password/reset-request` | Solicitar reset senha | ❌ |

**Resposta de Login:**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "user": { "id": 1, "nome": "Admin", "role": "admin" },
    "session": { "login_time": "...", "expires_in": 3600 },
    "estabelecimento": { "id": 4, "nome": "Mercadinho ..." }
  }
}
```

---

### 📊 Dashboard (`/api/dashboard`)

| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| GET | `/resumo` | Métricas gerais do dashboard | ✅ |
| GET | `/painel-admin` | Painel administrativo avançado | ✅ Admin |
| GET | `/tendencia-mensal` | Tendências mensais | ✅ |
| GET | `/resumo-executivo` | Resumo executivo | ✅ Admin |
| GET | `/vendas-periodo` | Vendas por período customizado | ✅ |
| GET | `/analise-preditiva` | Análises preditivas ML | ✅ Admin |

**Resposta `/resumo`:**
```json
{
  "success": true,
  "usuario": {
    "nome": "Administrador",
    "role": "admin",
    "acesso_avancado": true
  },
  "data": {
    "hoje": {
      "data": "2026-01-04",
      "total_vendas": 0.0,
      "quantidade_vendas": 0,
      "ticket_medio": 0.0,
      "clientes_atendidos": 0,
      "crescimento_vs_ontem": 0.0
    },
    "mes": {
      "total_vendas": 0.0,
      "total_despesas": 0.0,
      "lucro_bruto": 0.0,
      "margem_lucro": null,
      "crescimento_mensal": 0.0
    },
    "alertas": {
      "estoque_baixo": [],
      "validade_proxima": []
    },
    "analise_temporal": {
      "vendas_por_hora": []
    },
    "ultimas_vendas": []
  }
}
```

---

### 📦 Produtos (`/api/produtos`)

| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| GET | `/search` | Buscar produtos | ✅ |
| GET | `/barcode/<codigo>` | Buscar por código de barras | ✅ |
| POST | `/quick-add` | Adicionar produto rápido (PDV) | ✅ |
| GET | `/estoque` | Listar todos produtos | ✅ |
| GET | `/estoque/<int:id>` | Obter produto específico | ✅ |
| POST | `/estoque` | Criar novo produto | ✅ |
| PUT | `/estoque/<int:id>` | Atualizar produto | ✅ |
| DELETE | `/estoque/<int:id>` | Deletar produto | ✅ Admin |
| PUT | `/estoque/<int:id>/estoque` | Ajustar estoque | ✅ |
| GET | `/categorias` | Listar categorias | ✅ |
| GET | `/relatorio/estoque` | Relatório de estoque | ✅ |
| GET | `/exportar/csv` | Exportar produtos CSV | ✅ |

---

### 👥 Clientes (`/api/clientes`)

| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| GET | `/` | Listar clientes | ✅ |
| GET | `/<int:id>` | Obter cliente específico | ✅ |
| POST | `/` | Criar novo cliente | ✅ |
| PUT | `/<int:id>` | Atualizar cliente | ✅ |
| DELETE | `/<int:id>` | Deletar cliente | ✅ Admin |
| GET | `/<int:id>/compras` | Histórico de compras | ✅ |
| GET | `/buscar` | Buscar clientes | ✅ |
| GET | `/estatisticas` | Estatísticas de clientes | ✅ |
| GET | `/exportar` | Exportar clientes | ✅ |

**Segmentação RFM:**
- **Ouro:** Compra frequente, alto valor, recente
- **Prata:** Compra regular, valor médio
- **Bronze:** Compra ocasional
- **Em Risco:** Não compra há tempo
- **Perdido:** Inativo há muito tempo
- **Novo:** Cadastrado recentemente

---

### 🏭 Fornecedores (`/api/fornecedores`)

| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| GET | `/` | Listar fornecedores | ✅ |
| GET | `/<int:id>` | Obter fornecedor específico | ✅ |
| GET | `/<int:id>/produtos` | Produtos do fornecedor | ✅ |
| POST | `/` | Criar fornecedor | ✅ |
| PUT | `/<int:id>` | Atualizar fornecedor | ✅ |
| DELETE | `/<int:id>` | Deletar fornecedor | ✅ Admin |
| GET | `/estatisticas` | Estatísticas fornecedores | ✅ |
| GET | `/relatorio` | Relatório de fornecedores | ✅ |

---

### 👷 Funcionários (`/api/funcionarios`)

| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| GET | `/` | Listar funcionários | ✅ |
| GET | `/<int:id>` | Obter funcionário específico | ✅ |
| POST | `/` | Criar funcionário | ✅ Admin |
| PUT | `/<int:id>` | Atualizar funcionário | ✅ Admin |
| DELETE | `/<int:id>` | Deletar funcionário | ✅ Admin |
| GET | `/estatisticas` | Estatísticas funcionários | ✅ |
| GET | `/relatorio-vendas` | Relatório vendas por funcionário | ✅ |
| POST | `/login` | Login de funcionário (PDV) | ❌ |
| POST | `/verificar-pin` | Verificar PIN | ❌ |

**Roles:**
- `admin` (dono) - Acesso total
- `gerente` - Acesso avançado ao dashboard
- `funcionario` (caixa) - Acesso básico PDV

---

### 🛒 Vendas (`/api/vendas`)

| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| GET | `/` | Listar vendas | ✅ |
| GET | `/<int:venda_id>` | Obter venda específica | ✅ |
| POST | `/` | Criar nova venda | ✅ |
| GET | `/dia` | Vendas do dia | ✅ |
| POST | `/<int:venda_id>/cancelar` | Cancelar venda | ✅ Admin |
| GET | `/estatisticas` | Estatísticas vendas | ✅ |
| GET | `/relatorio-diario` | Relatório diário | ✅ |
| GET | `/analise-tendencia` | Análise de tendências | ✅ |

**Formas de Pagamento:**
- `dinheiro` - Dinheiro (com troco)
- `cartao_credito` - Cartão de crédito (parcelas)
- `cartao_debito` - Cartão de débito
- `pix` - PIX

---

### 💸 Despesas (`/api/despesas`)

| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| GET | `/` | Listar despesas | ✅ |
| POST | `/` | Criar despesa | ✅ |
| PUT | `/<int:despesa_id>` | Atualizar despesa | ✅ |
| DELETE | `/<int:despesa_id>` | Deletar despesa | ✅ Admin |
| GET | `/estatisticas` | Estatísticas despesas | ✅ |

**Tipos de Despesas:**
- **Fixas:** Aluguel, Internet, Energia
- **Variáveis:** Insumos, Manutenção, Frete

---

### 📈 Relatórios (`/api/relatorios`)

| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| GET | `/vendas` | Relatório de vendas | ✅ |
| GET | `/estoque` | Relatório de estoque | ✅ |
| GET | `/analise-rotatividade` | Análise rotatividade produtos | ✅ |
| GET | `/comparativo-periodos` | Comparar períodos | ✅ |
| GET | `/dashboard` | Dashboard de relatórios | ✅ |

---

### ⚙️ Configurações (`/api/config`)

| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| GET | `/` | Obter configurações | ✅ |
| PUT | `/` | Atualizar configurações | ✅ Admin |
| POST | `/logo` | Upload logo | ✅ Admin |
| GET/PUT | `/estabelecimento` | Dados do estabelecimento | ✅ Admin |

---

## 🧮 CÁLCULOS E MÉTRICAS DO DASHBOARD

### Métricas Principais

#### 1. **Total Vendas Hoje**
```python
total_vendas_dia = sum(venda.total for venda in vendas_hoje)
```

#### 2. **Ticket Médio**
```python
ticket_medio = total_vendas / quantidade_vendas if quantidade_vendas > 0 else 0
```

#### 3. **Lucro Bruto Mês**
```python
lucro_bruto = total_vendas_mes - total_despesas_mes
```

#### 4. **Margem de Lucro**
```python
margem_lucro = (lucro_bruto / total_vendas_mes) * 100 if total_vendas_mes > 0 else 0
```

#### 5. **Crescimento vs Ontem**
```python
crescimento = ((vendas_hoje - vendas_ontem) / vendas_ontem) * 100 if vendas_ontem > 0 else 0
```

#### 6. **Produtos com Estoque Baixo**
```sql
SELECT * FROM produtos 
WHERE quantidade <= quantidade_minima 
  AND ativo = TRUE
```

#### 7. **Produtos Próximos da Validade**
```sql
SELECT * FROM produtos 
WHERE data_validade BETWEEN hoje AND (hoje + dias_alerta)
  AND quantidade > 0
```

### KPIs Avançados (Acesso Admin)

#### 8. **Customer Lifetime Value (CLV)**
```python
clv = media(cliente.total_compras) * media(cliente.frequencia_compras) * tempo_medio_cliente
```

#### 9. **Taxa de Churn**
```python
churn_rate = (clientes_perdidos / total_clientes) * 100
```

#### 10. **Taxa de Retenção**
```python
retention_rate = (clientes_recorrentes / total_clientes) * 100
```

#### 11. **Análise ABC de Estoque**
- **Classe A:** 20% produtos = 80% valor vendido
- **Classe B:** 30% produtos = 15% valor vendido
- **Classe C:** 50% produtos = 5% valor vendido

---

## 🔍 ANÁLISE DO PROBLEMA ATUAL

### 🐛 Problema Identificado: Dashboard Mostrando R$ 0.00

#### Causa Raiz
1. **Incompatibilidade de Formato**
   - Frontend espera: `{total_vendas_hoje: number, vendas_por_categoria: []}`
   - Backend retorna: `{data: {hoje: {...}, mes: {...}}}`

2. **Dados Não Mapeados**
   - O backend não está calculando `vendas_por_categoria`
   - O backend não está calculando `vendas_ultimos_7_dias`
   - O backend não está retornando `clientes_novos_mes`

#### Solução Implementada

**1. Criado Mapeador no Frontend** ([dashboardService.ts](c:\Users\rafae\OneDrive\Desktop\mercadinhosys\frontend\mercadinhosys-frontend\src\features\dashboard\dashboardService.ts))
```typescript
const mapBackendToDashboardMetrics = (backendData: any): DashboardMetrics => {
    return {
        total_vendas_hoje: backendData?.hoje?.total_vendas || 0,
        total_vendas_mes: backendData?.mes?.total_vendas || 0,
        ticket_medio: backendData?.hoje?.ticket_medio || 0,
        clientes_novos_mes: 0,
        produtos_baixo_estoque: backendData?.alertas?.estoque_baixo?.length || 0,
        despesas_mes: backendData?.mes?.total_despesas || 0,
        lucro_mes: backendData?.mes?.lucro_bruto || 0,
        vendas_por_categoria: [],
        vendas_ultimos_7_dias: [],
    };
};
```

**2. Corrigidos Erros de Serialização JSON** ([dashboard.py](c:\Users\rafae\OneDrive\Desktop\mercadinhosys\backend\app\routes\dashboard.py))
- Convertidos objetos `Produto` para dicionários
- Convertidos objetos `Cliente` para dicionários
- Convertidos objetos `Venda` para dicionários

**3. Ajustada SQL para SQLite**
- Mudado `DATE_SUB(NOW(), INTERVAL 30 DAY)` → `date('now', '-30 days')`
- Mudado `NOW()` → `date('now')`

---

## 📋 DADOS DE TESTE (seed_test.py)

### Dados Criados

| Entidade | Quantidade | Configuração |
|----------|------------|--------------|
| Estabelecimento | 1 | ID = 4 |
| Funcionários | 4 | admin, gerente, 2 caixas |
| Clientes | 40 | Com segmentação RFM |
| Fornecedores | 6 | Avaliação 3.5-5.0 |
| Produtos | 120 | 6 categorias |
| Vendas | ~740 | 180 dias + 20 hoje |
| Itens de Venda | ~3000 | 1-8 itens por venda |
| Despesas | ~50 | Fixas + variáveis |

### Credenciais de Teste

```
admin / admin123      (role: admin, cargo: dono)
gerente / 123456      (role: gerente, cargo: gerente)
caixa1 / 123456       (role: funcionario, cargo: caixa)
caixa2 / 123456       (role: funcionario, cargo: caixa)
```

### Distribuição de Vendas
- **Período:** Últimos 180 dias
- **Média:** 4 vendas/dia
- **Hoje:** 20 vendas garantidas
- **Horário Pico:** 10-12h e 17-19h
- **Formas Pagamento:** Distribuição realista

### Categorias de Produtos
1. Alimentos
2. Bebidas
3. Limpeza
4. Higiene
5. Padaria
6. Açougue

---

## ✅ PRÓXIMOS PASSOS NECESSÁRIOS

### 1. Implementar Dados Faltantes no Backend

#### A. Adicionar Vendas por Categoria
```python
# Em dashboard.py, função obter_dados_completos_dashboard()
vendas_por_categoria = (
    db.session.query(
        Produto.categoria,
        func.sum(VendaItem.total_item).label("total")
    )
    .join(VendaItem, Produto.id == VendaItem.produto_id)
    .join(Venda)
    .filter(
        Venda.estabelecimento_id == estabelecimento_id,
        Venda.data_venda >= inicio_mes,
        Venda.status == "finalizada"
    )
    .group_by(Produto.categoria)
    .all()
)

return {
    "vendas_por_categoria": [
        {"categoria": cat, "total": float(total)}
        for cat, total in vendas_por_categoria
    ]
}
```

#### B. Adicionar Vendas Últimos 7 Dias
```python
vendas_ultimos_7_dias = []
for i in range(7):
    dia = hoje - timedelta(days=i)
    inicio = datetime.combine(dia, datetime.min.time())
    fim = datetime.combine(dia, datetime.max.time())
    
    total_dia = db.session.query(
        func.sum(Venda.total)
    ).filter(
        Venda.estabelecimento_id == estabelecimento_id,
        Venda.data_venda.between(inicio, fim),
        Venda.status == "finalizada"
    ).scalar() or 0
    
    vendas_ultimos_7_dias.append({
        "data": dia.isoformat(),
        "total": float(total_dia)
    })
```

#### C. Adicionar Clientes Novos do Mês
```python
clientes_novos_mes = Cliente.query.filter(
    Cliente.estabelecimento_id == estabelecimento_id,
    Cliente.data_cadastro >= inicio_mes
).count()
```

### 2. Atualizar Estrutura de Resposta do Backend

**Opção 1:** Manter estrutura atual + adicionar campos compatíveis
```python
response_data["data"]["metricas_frontend"] = {
    "total_vendas_hoje": metrica.total_vendas_dia,
    "total_vendas_mes": metrica.total_vendas_mes,
    "ticket_medio": metrica.ticket_medio_dia,
    "clientes_novos_mes": clientes_novos_mes,
    "produtos_baixo_estoque": len(dados_realtime["estoque_baixo"]),
    "despesas_mes": metrica.total_despesas_mes,
    "lucro_mes": metrica.lucro_bruto_mes,
    "vendas_por_categoria": vendas_por_categoria,
    "vendas_ultimos_7_dias": vendas_ultimos_7_dias
}
```

**Opção 2:** Criar endpoint separado `/dashboard/metricas-frontend`

### 3. Melhorar Frontend

#### A. Adicionar Tratamento de Erro Robusto
```typescript
const loadMetrics = async () => {
    try {
        setLoading(true);
        setError(null);
        const data = await dashboardService.getMetrics();
        setMetrics(data);
    } catch (error) {
        console.error('Erro ao carregar métricas:', error);
        setError('Erro ao carregar dashboard. Tente novamente.');
    } finally {
        setLoading(false);
    }
};
```

#### B. Adicionar Estado de Erro
```typescript
const [error, setError] = useState<string | null>(null);

if (error) {
    return (
        <div className="p-4 bg-red-100 text-red-700 rounded">
            {error}
        </div>
    );
}
```

### 4. Adicionar Gráficos Reais

Instalar biblioteca de gráficos:
```bash
npm install recharts
```

Implementar gráficos:
```tsx
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

<LineChart data={metrics.vendas_ultimos_7_dias}>
    <CartesianGrid strokeDasharray="3 3" />
    <XAxis dataKey="data" />
    <YAxis />
    <Tooltip />
    <Legend />
    <Line type="monotone" dataKey="total" stroke="#8884d8" />
</LineChart>
```

### 5. Otimizações de Performance

#### A. Cache de Métricas
```python
# Usar Redis ou cache em memória
from flask_caching import Cache

cache = Cache(config={'CACHE_TYPE': 'simple'})

@cache.memoize(timeout=300)  # 5 minutos
def get_dashboard_metrics(estabelecimento_id, hoje):
    # ... cálculos
    return metrics
```

#### B. Índices no Banco
```sql
CREATE INDEX idx_vendas_data_est ON vendas(data_venda, estabelecimento_id);
CREATE INDEX idx_vendas_status ON vendas(status);
CREATE INDEX idx_produtos_est_cat ON produtos(estabelecimento_id, categoria);
CREATE INDEX idx_clientes_data ON clientes(data_cadastro);
```

---

## 🔐 SEGURANÇA

### Implementações Atuais
- ✅ JWT Authentication
- ✅ Password Hashing (werkzeug.security)
- ✅ CORS Configurado
- ✅ Decoradores de Permissão (@token_required)
- ✅ Validação de Roles

### Melhorias Recomendadas
- ⚠️ Rate Limiting (implementado mas não ativo)
- ⚠️ HTTPS em produção
- ⚠️ Validação de inputs com schemas
- ⚠️ SQL Injection protection (SQLAlchemy já protege)
- ⚠️ XSS Protection (React já protege)

---

## 📊 ESTRUTURA DE PERMISSÕES

```python
{
    "acesso_pdv": True,
    "acesso_estoque": True,
    "acesso_relatorios": True,
    "acesso_configuracoes": role == "admin",
    "acesso_financeiro": role in ["admin", "gerente"],
    "pode_dar_desconto": True,
    "limite_desconto": 10.0,
    "pode_cancelar_venda": role in ["admin", "gerente"],
    "acesso_dashboard_avancado": role in ["admin", "gerente"]
}
```

---

## 🎨 FRONTEND - ESTRUTURA

```
src/
├── api/
│   ├── apiClient.ts          # Axios configurado
│   └── apiConfig.ts          # Configs de API
├── components/
│   ├── dashboard/            # Componentes do dashboard
│   ├── layout/               # Layout geral
│   └── shared/               # Componentes compartilhados
├── features/
│   ├── auth/                 # Autenticação
│   ├── customers/            # Clientes
│   ├── dashboard/            # Dashboard
│   ├── employees/            # Funcionários
│   ├── expenses/             # Despesas
│   ├── pdv/                  # PDV
│   ├── products/             # Produtos
│   ├── reports/              # Relatórios
│   ├── sales/                # Vendas
│   └── settings/             # Configurações
├── hooks/                    # Custom hooks
├── routes/                   # Rotas
├── stores/                   # State management
├── types/                    # TypeScript types
└── utils/                    # Utilitários
```

---

## 🚀 COMANDOS ÚTEIS

### Backend
```bash
# Ativar ambiente virtual
.\venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Criar banco de dados
python init_db.py

# Popular com dados de teste
python seed_test.py --reset

# Executar backend
python run.py
```

### Frontend
```bash
# Instalar dependências
npm install

# Executar desenvolvimento
npm run dev

# Build produção
npm run build
```

---

## 📝 NOTAS IMPORTANTES

1. **Estabelecimento Padrão:** ID = 4 (usado em testes)
2. **SQLite:** Sintaxe diferente de MySQL (cuidado com DATE functions)
3. **CORS:** Configurado para permitir todas origens (*) em DEV
4. **Tokens JWT:** Expiram em 1 hora
5. **Dashboard:** Recalcula métricas automaticamente se não existir para o dia

---

## 🎯 CONCLUSÃO

O MercadinhoSys é um sistema robusto e bem estruturado com:
- ✅ Arquitetura RESTful bem definida
- ✅ Separação clara de responsabilidades
- ✅ Autenticação e autorização implementadas
- ✅ Métricas avançadas e analytics
- ✅ Dados de teste realistas

**Problema Atual:** Incompatibilidade entre estrutura de dados backend/frontend no dashboard.

**Solução:** Mapeador temporário implementado. Necessário adicionar campos faltantes no backend para dados completos.

---

**Documento gerado em:** 04/01/2026  
**Autor:** GitHub Copilot (Claude Sonnet 4.5)  
**Versão:** 1.0
