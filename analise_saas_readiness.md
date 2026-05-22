# 🏪 MercadinhoSys — Análise de Regras de Negócio & Plano de Ação SaaS

## Visão Geral do Sistema

O **MercadinhoSys** é um ERP completo para mercearias/mercadinhos no Brasil, construído com arquitetura **multi-tenant** (Flask + PostgreSQL/SQLite + React/Vite). O backend opera em modo **híbrido** (cloud-first com fallback local) e inclui um worker de sincronização offline-first.

---

## 1. Regras de Negócio Mapeadas

### 🏢 Multi-Tenancy & Isolamento de Dados

| Regra | Status | Detalhe |
|-------|--------|---------|
| Cada [Estabelecimento](file:///c:/Users/rafae/Dev/mercadinhosys/backend/app/models.py#154-208) é um tenant | ✅ Implementado | [TenantID()](file:///c:/Users/rafae/Dev/mercadinhosys/backend/app/models.py#140-144) + [TenantQuery](file:///c:/Users/rafae/Dev/mercadinhosys/backend/app/models.py#68-82) filtram automaticamente por `estabelecimento_id` |
| Soft-delete via [SoftDeleteMixin](file:///c:/Users/rafae/Dev/mercadinhosys/backend/app/models.py#87-93) | ✅ Implementado | `deleted_at` com filtro automático no [TenantQuery](file:///c:/Users/rafae/Dev/mercadinhosys/backend/app/models.py#68-82) |
| Audit trail com [AuditMixin](file:///c:/Users/rafae/Dev/mercadinhosys/backend/app/models.py#94-98) | ✅ Implementado | `created_at`, `updated_at`, `sync_uuid` em todos os modelos |
| Super Admin tem acesso global | ✅ Implementado | `is_super_admin` flag bypassa filtros de tenant |

### 💰 Planos & Cotas (SaaS)

| Plano | Produtos | Clientes | Fornecedores | Funcionários | Recursos |
|-------|----------|----------|--------------|--------------|----------|
| **Gratuito** | 100 | 200 | 50 | 1 | PDV, Clientes, Vendas |
| **Pro** | Ilimitado | Ilimitado | Ilimitado | 3 | + Ponto, Dashboard Científico |
| **Superadmin** | ∞ | ∞ | ∞ | ∞ | Acesso total |

### 🔐 RBAC (Controle de Acesso por Cargo)

| Cargo | Acesso (Gratuito) | Acesso (Pro) |
|-------|--------------------|--------------|
| **ADMIN/Proprietário** | Total | Total |
| **Gerente** | Total | Total |
| **Caixa** | PDV, Clientes, Vendas | + Ponto |
| **Estoquista** | Limitado | Completo |

### 🛒 PDV & Vendas

- **Multi-pagamento**: Suporte a split de pagamento (Dinheiro, Pix, Cartão Crédito/Débito, Fiado)
- **Validação de pagamento**: Soma dos pagamentos deve igualar o total da venda (tolerância ±R$0.01)
- **Estoque FIFO**: Consumo por lotes na ordem de entrada ([consumir_estoque_fifo](file:///c:/Users/rafae/Dev/mercadinhosys/backend/app/models.py#767-778))
- **Fiado**: Gera [ContaReceber](file:///c:/Users/rafae/Dev/mercadinhosys/backend/app/models.py#1029-1050) com saldo devedor atualizado no cliente
- **Movimentação de caixa**: Apenas pagamentos em dinheiro alteram o saldo do caixa
- **Métricas do cliente**: Atualiza `total_compras`, `valor_total_gasto`, `ultima_compra` a cada venda

### 📦 Estoque & Produtos

- **Classificação ABC dinâmica** por período (90 dias padrão)
- **Custo Médio Ponderado (CMP)** recalculado a cada entrada
- **Markup automático** com cálculos [calcular_preco_por_markup](file:///c:/Users/rafae/Dev/mercadinhosys/backend/app/models.py#678-684) e [calcular_markup_de_preco](file:///c:/Users/rafae/Dev/mercadinhosys/backend/app/models.py#685-691)
- **Giro de estoque**, **cobertura em dias**, e **ponto de ressuprimento**
- **Controle de lotes** com validade e alertas de vencimento
- **Histórico de preços** com rastro do funcionário responsável

### 👥 RH & Ponto (Pro)

- Controle de ponto (entrada/saída) com horário de Manaus (GMT-4)
- Banco de horas mensal por funcionário
- Justificativas de ponto com fluxo de aprovação
- Benefícios por funcionário com valores e datas
- Preferências individuais de funcionário

### 📊 Dashboard Científico

- Métricas diárias agregadas ([DashboardMetrica](file:///c:/Users/rafae/Dev/mercadinhosys/backend/app/models.py#1125-1162))
- Análise RFM de clientes (Recency, Frequency, Monetary)
- Relatórios agendados com destinatários por email

### 💳 Billing (Stripe)

- Checkout Session para assinatura mensal
- Public checkout (landing page → cria conta + checkout)
- Webhook handler: `checkout.session.completed`, `invoice.payment_succeeded`, `customer.subscription.deleted`
- Customer Portal para gestão de assinatura
- Preços: Basic R$49,90 | Advanced R$69,90 | Premium R$99,90

### 🔄 Sincronização Offline-First

- [SyncQueue](file:///c:/Users/rafae/Dev/mercadinhosys/backend/app/models.py#212-241) / `AuditoriaSincronia`: Fila de mutações pendentes
- [GuerrillaSyncWorker](file:///c:/Users/rafae/Dev/mercadinhosys/backend/app/services/sync_worker.py#12-107): Thread daemon que detecta internet e envia deltas para a nuvem
- Retry com máximo de 5 tentativas antes de marcar como erro
- [after_flush_listener](file:///c:/Users/rafae/Dev/mercadinhosys/backend/app/models.py#247-261) captura INSERT/UPDATE/DELETE automaticamente

---

## 2. Problemas Encontrados no Código

### 🔴 Críticos (Blockers para SaaS)

| # | Problema | Arquivo | Impacto |
|---|---------|---------|---------|
| 1 | **Webhook Pagar.me não implementado** | [saas.py](file:///c:/Users/rafae/Dev/mercadinhosys/backend/app/routes/saas.py#L386-L411) | Assinatura pelo Pagar.me nunca ativa — código tem apenas TODOs |
| 2 | **Exceção engolida no webhook** | [saas.py](file:///c:/Users/rafae/Dev/mercadinhosys/backend/app/routes/saas.py#L410-L412) | `except Exception as e: from flask import current_app` — código truncado, sem return |
| 3 | **[super_admin_required](file:///c:/Users/rafae/Dev/mercadinhosys/backend/app/decorators/decorator_jwt.py#155-192) duplicado** | [decorator_jwt.py](file:///c:/Users/rafae/Dev/mercadinhosys/backend/app/decorators/decorator_jwt.py#L155-L191) vs [rbac.py](file:///c:/Users/rafae/Dev/mercadinhosys/backend/app/decorators/rbac.py#L11-L71) | Dois decorators com lógicas diferentes para a mesma função — risco de bypass |
| 4 | **Senha retornada em plaintext no onboarding** | [saas.py](file:///c:/Users/rafae/Dev/mercadinhosys/backend/app/routes/saas.py#L282) | `"senha": data['senha_admin']` exposta no response JSON |
| 5 | **Secret keys com fallback hardcoded** | [config.py](file:///c:/Users/rafae/Dev/mercadinhosys/backend/config.py#L69-L70) | `SECRET_KEY = "dev-fallback-secret-key-12345"` pode ser usado em prod se env var ausente |
| 6 | **CNPJ placeholder `00.000.000/0001-00`** | [stripe_routes.py](file:///c:/Users/rafae/Dev/mercadinhosys/backend/app/routes/stripe_routes.py#L91) | Public checkout cria estabelecimento com dados inválidos |
| 7 | **SQL Injection potencial no multi-tenant** | [multi_tenant.py](file:///c:/Users/rafae/Dev/mercadinhosys/backend/app/middleware/multi_tenant.py#L116) | `cursor.execute(f"CREATE DATABASE {db_name}")` — sem sanitização |

### 🟡 Importantes (Devem ser resolvidos antes da distribuição)

| # | Problema | Arquivo | Impacto |
|---|---------|---------|---------|
| 8 | **Testes quase inexistentes** | `backend/tests/` | Apenas 3 test files; sem CI/CD real rodando |
| 9 | **Print statements em produção** | Diversos | `print()` usado extensivamente em vez de `logger` (sync_worker, plan_guards) |
| 10 | **Normalização de status inconsistente** | `decorator_jwt.py` vs `rbac.py` | `admin_required` usa normalização inline; `funcionario_required` usa `auth_utils` |
| 11 | **Hierarquia de planos inconsistente** | [plan_guards.py](file:///c:/Users/rafae/Dev/mercadinhosys/backend/app/decorators/plan_guards.py#L5-L9) vs [stripe_service.py](file:///c:/Users/rafae/Dev/mercadinhosys/backend/app/services/stripe_service.py#L18-L22) | Guards: `Gratuito/Pro/Superadmin`. Stripe: `Basic/Advanced/Premium`. Normalização mapeia ambos mas é confusa |
| 12 | **Sem rate limiting real** | [rate_limit.py](file:///c:/Users/rafae/Dev/mercadinhosys/backend/app/middleware/rate_limit.py) | Arquivo existe (1KB) mas provavelmente não aplicado globalmente |
| 13 | **Email com serviço duplicado** | `services/email_service.py` + `utils/email_service.py` | Dois módulos com lógicas potencialmente divergentes |
| 14 | **`datetime.fromtimestamp` sem timezone** | [stripe_service.py](file:///c:/Users/rafae/Dev/mercadinhosys/backend/app/services/stripe_service.py#L146) | `datetime.fromtimestamp(period_end)` é naive — pode causar bugs de fuso |

### 🟢 Melhorias Desejáveis

| # | Item | Detalhe |
|---|------|---------|
| 15 | Migração Alembic não testada | `flask db upgrade` no render.yaml pode falhar silenciosamente |
| 16 | Redis configurado mas não utilizado | Docker compose inclui Redis; backend usa `SimpleCache` |
| 17 | Falta landing page/frontend para onboarding self-service | SaaS route existe mas depende de Super Admin manual |
| 18 | Sem monitoramento (Sentry, APM) | Erros logados apenas no stdout |

---

## 3. Plano de Ação para Distribuição SaaS

### 📋 Fase 1 — Segurança & Correções Críticas (Prioridade Absoluta)

- [ ] **1.1** Remover fallback hardcoded de `SECRET_KEY` e `JWT_SECRET_KEY` — forçar crash se ausente em produção
- [ ] **1.2** Remover retorno de senha plaintext no endpoint de onboarding
- [ ] **1.3** Corrigir SQL injection no `create_tenant_database` — usar `psycopg2.sql.Identifier`
- [ ] **1.4** Corrigir webhook truncado em `saas.py` (linhas 410-412)
- [ ] **1.5** Unificar `super_admin_required` — remover duplicata e usar one-source-of-truth
- [ ] **1.6** Eliminar CNPJ/CPF placeholder no public checkout — exigir dados reais ou validar depois

### 📋 Fase 2 — Padronização & Qualidade de Código

- [ ] **2.1** Unificar normalização de status em TODOS os decorators (usar `auth_utils` centralizado)
- [ ] **2.2** Substituir todos os `print()` por `logger.info/warning/error`
- [ ] **2.3** Unificar nomenclatura de planos: definir enum único (`Gratuito`, `Pro`, `Enterprise`) e normalizar em um só lugar
- [ ] **2.4** Unificar módulos de email — mover para `services/email_service.py` e deletar `utils/email_service.py`
- [ ] **2.5** Adicionar `timezone.utc` ao `datetime.fromtimestamp` no Stripe webhook
- [ ] **2.6** Ativar e configurar rate limiting para endpoints públicos (`/leads/registrar`, `/public-checkout`, webhooks)

### 📋 Fase 3 — Testes & CI/CD

- [ ] **3.1** Expandir suite de testes: testes unitários para `VendaService`, `plan_guards`, `stripe_service`
- [ ] **3.2** Testes de integração para onboarding completo (cria tenant + admin + config + caixa)
- [ ] **3.3** Configurar GitHub Actions com: lint (flake8) → testes → build Docker → deploy staging
- [ ] **3.4** Adicionar `pytest-cov` com meta de cobertura mínima (ex: 60%)

### 📋 Fase 4 — Infraestrutura para Distribuição

- [ ] **4.1** Implementar webhook Pagar.me OU decidir usar exclusivamente Stripe
- [ ] **4.2** Configurar Sentry para monitoramento de erros em produção
- [ ] **4.3** Ativar Redis como cache (em vez de `SimpleCache`) para escala multi-instância
- [ ] **4.4** Implementar health check mais robusto (verificar DB connection + Redis + disk space)
- [ ] **4.5** Criar script de onboarding self-service: landing page → formulário → cria conta → redireciona para checkout Stripe

### 📋 Fase 5 — Documentação & Operações

- [ ] **5.1** Documentar API com Swagger/OpenAPI (estrutura `app/swagger/` já existe)
- [ ] **5.2** Criar docs de operação: Como criar tenant, como gerenciar planos, como fazer backup
- [ ] **5.3** Criar termos de uso e política de privacidade (LGPD)
- [ ] **5.4** Definir SLA e políticas de suporte

### 📋 Fase 6 — Go-to-Market

- [ ] **6.1** Landing page funcional com captura de leads e CTA para checkout
- [ ] **6.2** Email marketing para leads capturados (funil de onboarding)
- [ ] **6.3** Dashboard administrativo SaaS para o Super Admin (já existe parcialmente em `super_admin_dashboard.py`)
- [ ] **6.4** Métricas de negócio SaaS: MRR, churn, LTV, CAC

---

## 4. Resumo Executivo

```
┌─────────────────────────────────────────────────────┐
│              MATURIDADE SaaS: ~65%                  │
│                                                     │
│  ✅ Arquitetura multi-tenant          PRONTO        │
│  ✅ Planos com cotas                  PRONTO        │
│  ✅ RBAC com 5 níveis                 PRONTO        │
│  ✅ PDV com multi-pagamento           PRONTO        │
│  ✅ Stripe billing                    FUNCIONAL     │
│  ✅ Sync offline-first                FUNCIONAL     │
│  ⚠️  Segurança                        PRECISA FIXES │
│  ⚠️  Testes                           MÍNIMOS       │
│  ⚠️  Consistência de código           PRECISA FIXES │
│  ❌ Monitoring/APM                    AUSENTE       │
│  ❌ CI/CD automatizado                AUSENTE       │
│  ❌ Onboarding self-service           INCOMPLETO    │
│  ❌ Documentação API                  INCOMPLETO    │
│  ❌ LGPD/Termos de uso                AUSENTE       │
└─────────────────────────────────────────────────────┘
```

> [!IMPORTANT]
> As **Fases 1 e 2** são pré-requisitos absolutos antes de qualquer distribuição a clientes pagantes. As correções de segurança (1.1-1.6) devem ser implementadas **antes** do primeiro deploy público.

> [!TIP]
> O sistema já tem uma base sólida. Com as correções de segurança e padronização, pode estar pronto para **beta fechado** (clientes selecionados) em **2-3 semanas de trabalho focado**. Para distribuição **aberta**, estimar 4-6 semanas incluindo testes, CI/CD e documentação.
