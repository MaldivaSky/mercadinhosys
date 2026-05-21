# 🎯 PROMPTS MINIMALISTAS PARA IA
## MercadinhoSys - Sprints Críticas (Tokens Otimizados)

**Versão:** 2.0 | **Atualizado:** 26/04/2026

---

## 📌 COMO USAR ESTE DOCUMENTO

1. Copie o prompt da sprint desejada
2. Cole no chat da IA (Claude, GPT-4, etc)
3. Aguarde a implementação
4. Teste conforme critérios de aceite
5. Marque como concluído ✅

---

## SPRINT 1: Dashboard Completo

**CONTEXTO:** Backend já retorna todas as métricas, mas frontend só renderiza 1 de 6 seções.

**PROMPT:**
```
Arquivo: frontend/mercadinhosys-frontend/src/features/dashboard/DashboardPage.tsx

OBJETIVO: Renderizar 6 seções do dashboard científico

STATUS ATUAL:
✅ Visão Geral (KPIs) - linha ~720
❌ Análise Detalhada (Curva ABC, RFM)
❌ Análise Temporal (gráficos tendência)
❌ Insights (anomalias, recomendações)
❌ RH (funcionários, horas, folha)
❌ Fiados (total, vencidas, clientes)

DADOS DISPONÍVEIS:
- Endpoint: GET /api/dashboard/cientifico?days=30
- Resposta: JSON com 6 seções completas
- Modais: src/features/dashboard/components/modals/

IMPLEMENTAR:
1. Curva ABC: 3 cards (A, B, C) com barras de progresso
2. RFM: 3 métricas (Recência, Frequência, Monetário)
3. Gráfico: LineChart com tendência de vendas (usar Recharts)
4. Anomalias: Cards vermelhos clicáveis
5. Recomendações: Cards azuis clicáveis
6. RH: 3 cards (funcionários, horas, folha)
7. Fiados: 3 cards (total, vencidas, clientes) com cores

CRITÉRIOS DE ACEITE:
✅ 6 seções renderizam corretamente
✅ Dados vêm do backend (não mock)
✅ Cliques abrem modais existentes
✅ Performance < 2s
✅ Sem erros no console
✅ Responsivo em mobile
```

**Tempo:** 4-6h | **Prioridade:** 🔴 CRÍTICA | **Dependências:** Nenhuma

---

## SPRINT 2: Múltiplos Pagamentos - Backend

**PROMPT:**
```
Arquivo: backend/app/routes/pdv.py (linha ~747)

Tarefa: Completar função finalizar_venda()

Falta implementar após criar nova_venda:

1. Criar registros Pagamento (um por forma)
   - Validar: soma pagamentos = total venda
   - Salvar: forma, valor, referência, data

2. Se fiado, criar ContaReceber
   - Valor fiado
   - Data vencimento (padrão +30 dias)
   - Atualizar saldo_devedor do cliente

3. Atualizar estoque
   - Lock pessimista (with_for_update)
   - Validar quantidade disponível
   - Criar MovimentacaoEstoque

4. Registrar MovimentacaoCaixa
   - Apenas formas != 'fiado'
   - Tipo: entrada

5. Commit atômico
   - Se erro: rollback
   - Retornar venda com pagamentos

Modelos necessários:
- Pagamento (venda_id, forma_pagamento, valor, referencia)
- ContaReceber (cliente_id, venda_id, valor, data_vencimento, status)
- MovimentacaoEstoque (produto_id, tipo, quantidade, venda_id)
- MovimentacaoCaixa (caixa_id, tipo, valor, venda_id)

Adicionar ao Cliente: saldo_devedor, limite_credito

Critério Aceite:
✅ Venda com 1 forma funciona
✅ Venda com 2+ formas funciona
✅ Fiado cria ContaReceber
✅ Estoque atualiza
✅ Caixa registra entrada
✅ Testes passam
```

**Tempo:** 3-4h | **Prioridade:** 🔴 CRÍTICA

---

## SPRINT 3: Seed - Múltiplos Pagamentos

**PROMPT:**
```
Arquivo: backend/seed_simulation_master.py

Tarefa: Adicionar vendas com múltiplos pagamentos

Função nova: criar_vendas_com_multiplos_pagamentos()

Para cada mês:
- 10 vendas com 2-3 formas de pagamento
- Distribuir: dinheiro, cartão, pix, fiado
- Criar registros Pagamento (um por forma)
- Se fiado: criar ContaReceber
- Atualizar saldo_devedor cliente

Exemplo:
Venda R$100:
- Dinheiro: R$30
- Cartão: R$50
- Fiado: R$20 (cria ContaReceber)

Chamar em: MasterSeeder.seed()

Testar:
```bash
python backend/seed_simulation_master.py
sqlite3 backend/instance/mercadinho_local.db \
  "SELECT v.id, COUNT(p.id) FROM vendas v LEFT JOIN pagamentos p ON v.id=p.venda_id GROUP BY v.id HAVING COUNT(p.id)>1 LIMIT 5;"
```

Critério Aceite:
✅ 100+ vendas com múltiplos pagamentos
✅ Pagamentos somam corretamente
✅ ContaReceber criadas
✅ Saldo_devedor atualizado
```

**Tempo:** 2-3h | **Prioridade:** 🔴 CRÍTICA

---

## SPRINT 4: Delivery - Interface

**PROMPT:**
```
Arquivo: frontend/mercadinhosys-frontend/src/features/delivery/DeliveryPage.tsx

Tarefa: Implementar interface de delivery

Estrutura:
- DeliveryPage (principal)
- DeliveryList (listagem)
- DeliveryForm (criar/editar)
- DeliveryStatus (status badge)

Funcionalidades:
1. Listar entregas (GET /delivery/entregas)
   - Filtros: pendente, em_rota, entregue
   - Tabela com: ID, cliente, motorista, status, data

2. Criar entrega (POST /delivery/entregas)
   - Selecionar venda
   - Selecionar motorista
   - Selecionar veículo
   - Data entrega

3. Atualizar status (PUT /delivery/entregas/{id})
   - Botões: Pendente → Em Rota → Entregue
   - Registrar data/hora

4. Rastreamento (GET /delivery/rastreamento/{id})
   - Mostrar localização motorista
   - Timeline de status

Backend endpoints já existem em: backend/app/routes/delivery.py

Critério Aceite:
✅ Listar entregas funciona
✅ Criar entrega funciona
✅ Atualizar status funciona
✅ Rastreamento funciona
✅ Integração com backend OK
```

**Tempo:** 5-6h | **Prioridade:** 🟠 ALTA

---

## SPRINT 5: Novo Cliente - Onboarding

**PROMPT:**
```
Teste: Novo cliente consegue usar sistema do zero

Passos:
1. Registrar novo usuário
   - Email: teste@novo.com
   - Senha: Teste123!
   - Nome Estabelecimento: Mercado Teste
   - CNPJ: 12.345.678/0001-90

2. Fazer login

3. Criar primeiro cliente
   - Nome, CPF, email, telefone

4. Criar primeiro produto
   - Nome, código barras, preço, quantidade

5. Fazer primeira venda
   - Buscar produto
   - Adicionar ao carrinho
   - Pagar (dinheiro)

6. Visualizar dashboard
   - Deve mostrar a venda

7. Verificar relatórios
   - Deve mostrar dados

Critério Aceite:
✅ Registro funciona
✅ Login funciona
✅ Criar cliente funciona
✅ Criar produto funciona
✅ Fazer venda funciona
✅ Dashboard mostra dados
✅ Relatórios funcionam
```

**Tempo:** 2-3h | **Prioridade:** 🟠 ALTA

---

## SPRINT 6: Refatoração - Código Limpo

**PROMPT:**
```
Tarefa: Refatorar backend/app/routes/pdv.py

Criar:
1. backend/app/services/venda_service.py
   - validar_estoque(produto_id, quantidade)
   - criar_pagamentos(venda_id, pagamentos_data)
   - criar_conta_receber(cliente_id, venda_id, valor, data_vencimento)
   - atualizar_estoque(produto_id, quantidade, venda_id)

2. backend/app/utils/errors.py
   - APIError (base)
   - EstoqueInsuficienteError
   - ClienteNaoEncontradoError
   - CaixaFechadoError

3. backend/app/utils/response.py
   - APIResponse.success(data, message, status_code)
   - APIResponse.error(code, message, details, status_code)
   - APIResponse.paginated(items, page, per_page, total)

4. backend/app/schemas/venda_schema.py
   - FinalizarVendaSchema (Pydantic)
   - PagamentoSchema
   - VendaItemSchema

Refatorar finalizar_venda():
- Usar VendaService
- Usar APIResponse
- Usar APIError
- Usar FinalizarVendaSchema

Resultado: 50 linhas ao invés de 150

Critério Aceite:
✅ Código mais limpo
✅ Sem duplicação
✅ Testes passam
✅ Performance igual
```

**Tempo:** 4-5h | **Prioridade:** 🟡 MÉDIA

---

## SPRINT 7: Testes - Validação

**PROMPT:**
```
Tarefa: Testes automatizados

Criar: backend/tests/test_vendas.py

Testes:
1. test_venda_simples()
   - Criar venda com 1 forma
   - Verificar estoque atualizado
   - Verificar caixa registrado

2. test_multiplos_pagamentos()
   - Criar venda com 2+ formas
   - Verificar soma = total
   - Verificar cada pagamento criado

3. test_fiado()
   - Criar venda com fiado
   - Verificar ContaReceber criada
   - Verificar saldo_devedor atualizado

4. test_estoque_insuficiente()
   - Tentar venda com estoque insuficiente
   - Verificar erro retornado
   - Verificar rollback

5. test_caixa_fechado()
   - Tentar venda com caixa fechado
   - Verificar erro retornado

6. test_dashboard_completo()
   - GET /api/dashboard/cientifico
   - Verificar 6 seções retornam
   - Verificar dados corretos

Executar:
```bash
pytest backend/tests/test_vendas.py -v
```

Critério Aceite:
✅ 6 testes passam
✅ Cobertura > 80%
✅ Sem warnings
```

**Tempo:** 3-4h | **Prioridade:** 🟡 MÉDIA

---

## 📊 RESUMO SPRINTS

| Sprint | Tarefa | Tempo | Prioridade | Status |
|--------|--------|-------|-----------|--------|
| 1 | Dashboard | 4-6h | 🔴 CRÍTICA | ⏳ |
| 2 | Múltiplos Pagamentos Backend | 3-4h | 🔴 CRÍTICA | ⏳ |
| 3 | Seed Múltiplos Pagamentos | 2-3h | 🔴 CRÍTICA | ⏳ |
| 4 | Delivery Interface | 5-6h | 🟠 ALTA | ⏳ |
| 5 | Novo Cliente Onboarding | 2-3h | 🟠 ALTA | ⏳ |
| 6 | Refatoração Código Limpo | 4-5h | 🟡 MÉDIA | ⏳ |
| 7 | Testes Automatizados | 3-4h | 🟡 MÉDIA | ⏳ |
| **TOTAL** | - | **24-31h** | - | - |

---

## 🚀 FLUXO EXECUÇÃO

**Dia 1:**
- Sprint 1 (Dashboard) - 4-6h
- Sprint 2 (Múltiplos Pagamentos Backend) - 3-4h

**Dia 2:**
- Sprint 3 (Seed) - 2-3h
- Sprint 4 (Delivery) - 5-6h

**Dia 3:**
- Sprint 5 (Onboarding) - 2-3h
- Sprint 6 (Refatoração) - 4-5h

**Dia 4:**
- Sprint 7 (Testes) - 3-4h
- Correções finais

---

## 💡 DICAS PARA IA

1. **Copiar contexto:** Abra arquivo mencionado antes de pedir mudanças
2. **Ser específico:** Cite linhas exatas onde adicionar código
3. **Testar:** Execute testes após cada sprint
4. **Commit:** Faça commit após cada sprint
5. **Documentar:** Atualize docstrings

---

**Gerado:** 26 de Abril de 2026  
**Versão:** 2.2.0 Scientific  
**Status:** ✅ PRONTO PARA USAR
