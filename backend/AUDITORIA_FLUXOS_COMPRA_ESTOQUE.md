# AUDITORIA DE FLUXOS - Compras, Contas a Pagar e Estoque

**Data:** 16/02/2026  
**Auditor:** Assistente IA Fullstack  
**Escopo:** Fluxo completo de pedido de compra, geração de boletos (contas a pagar), recebimento de mercadoria, controle de lotes/validade e venda via PDV  
**Arquivos auditados:**
- `backend/app/routes/pedidos_compra.py`
- `backend/app/routes/pdv.py`
- `backend/app/routes/despesas.py`
- `backend/app/models.py` (Produto, ProdutoLote, MovimentacaoEstoque, ContaPagar, PedidoCompra)
- `backend/seed_test.py`
- `frontend/.../BoletosAVencerPanel.tsx`
- `frontend/.../purchaseOrderService.ts`

---

## RESUMO EXECUTIVO

Foram identificadas **3 falhas** na lógica do sistema, sendo **1 crítica**, **1 moderada** e **1 de dados (seed)**. Todas foram corrigidas.

| # | Severidade | Falha | Status |
|---|---|---|---|
| 1 | **CRÍTICA** | PDV não consumia lotes FIFO ao vender | CORRIGIDA |
| 2 | **MODERADA** | Frontend misturava boletos de mercadoria com despesas fixas | CORRIGIDA |
| 3 | **DADOS** | Seed vinculava despesas fixas a fornecedores de mercadoria | CORRIGIDA |

---

## FALHA #1 — PDV NÃO CONSUMIA LOTES (FIFO) AO VENDER

### Severidade: CRÍTICA

### Descrição

O método `consumir_estoque_fifo()` existia no modelo `Produto` (models.py, linhas 1300-1333) e funcionava corretamente para consumir lotes pela data de validade mais próxima (FIFO). Porém, **a rota de venda do PDV (`pdv.py`, rota `/finalizar`) nunca chamava esse método**.

### Código com defeito (pdv.py, linhas 608-632)

```python
# ANTES — decrementava apenas o estoque geral, ignorando lotes
estoque_anterior = int(produto.quantidade) if produto.quantidade else 0
produto.quantidade = estoque_anterior - quantidade
produto.updated_at = datetime.now()

movimentacao = MovimentacaoEstoque(
    # ...
    motivo="Venda",
    observacoes=f"Venda {codigo_venda}"
)
```

### Impacto

1. **Lotes nunca diminuíam:** A quantidade individual de cada `ProdutoLote` permanecia intacta após vendas, causando divergência entre `produto.quantidade` e a soma dos lotes
2. **Controle de validade fictício:** O sistema registrava lotes com datas de validade mas nunca os consumia na venda, tornando o FIFO inoperante
3. **Rastreabilidade comprometida:** Não era possível saber de qual lote saiu a mercadoria vendida
4. **Relatórios de validade incorretos:** Produtos apareceriam como "em estoque" nos lotes mesmo quando já vendidos

### Correção aplicada

```python
# DEPOIS — consome lotes por FIFO quando disponíveis
estoque_anterior = int(produto.quantidade) if produto.quantidade else 0

lotes_consumidos = []
lotes_disponiveis = produto.get_lotes_disponiveis() if hasattr(produto, 'get_lotes_disponiveis') else []

if lotes_disponiveis:
    try:
        lotes_consumidos = produto.consumir_estoque_fifo(quantidade)
    except Exception as fifo_err:
        current_app.logger.warning(
            f"FIFO falhou para produto {produto.id}: {fifo_err}. "
            f"Decrementando estoque geral."
        )
        produto.quantidade = estoque_anterior - quantidade
else:
    # Produto sem lotes — decremento simples (compatibilidade retroativa)
    produto.quantidade = estoque_anterior - quantidade

# Movimentação registra quais lotes foram consumidos
lotes_info = ", ".join(
    f"Lote {lc['lote'].numero_lote}({lc['quantidade_consumida']}un)"
    for lc in lotes_consumidos
) if lotes_consumidos else "sem lote"

movimentacao = MovimentacaoEstoque(
    # ...
    motivo="Venda",
    observacoes=f"Venda {codigo_venda} | {lotes_info}"
)
```

### Comportamento após correção

1. Ao vender, o sistema verifica se o produto possui lotes disponíveis
2. Se sim, chama `consumir_estoque_fifo()` que:
   - Ordena lotes por `data_validade ASC` (primeiro a vencer = primeiro a sair)
   - Consome a quantidade necessária dos lotes na ordem
   - Atualiza `lote.quantidade` de cada lote consumido
   - Atualiza `produto.quantidade` (estoque total)
3. Se não há lotes (produto legado/sem controle de lote), faz o decremento simples
4. A movimentação de estoque agora registra quais lotes foram consumidos

### Arquivo modificado
- `backend/app/routes/pdv.py` — rota `POST /api/pdv/finalizar`

---

## FALHA #2 — FRONTEND MISTURAVA BOLETOS DE MERCADORIA COM DESPESAS FIXAS

### Severidade: MODERADA

### Descrição

O painel "Boletos a Vencer" na `ExpensesPage` tratava todos os registros de `ContaPagar` de forma idêntica, sem distinguir entre:
- **Boletos de mercadoria**: vinculados a `PedidoCompra` (compra de produtos de fornecedores como Ambev, Colgate)
- **Boletos de despesas fixas**: aluguel, energia, telefonia, contabilidade, etc.

### Impacto

1. Ao abrir detalhes de um boleto de despesa fixa (ex: telefonia), o modal exibia "Produtos do Pedido" vazio ou dados incorretos
2. O usuário não conseguia diferenciar rapidamente entre boletos de mercadoria e despesas operacionais
3. Experiência de usuário confusa e não profissional

### Correção aplicada

**Backend (`backend/app/routes/despesas.py`):**

Adicionados campos `origem` e `descricao` na resposta da rota `/boletos-a-vencer/`:

```python
tem_pedido = boleto.pedido_compra_id is not None and boleto.pedido_compra is not None
if tem_pedido:
    origem = "mercadoria"
    descricao = f"Pedido {boleto.pedido_compra.numero_pedido}"
else:
    origem = "despesa"
    descricao = boleto.observacoes or boleto.tipo_documento or "Despesa"
```

**Frontend (`BoletosAVencerPanel.tsx`):**

- Lista: tag visual colorida ("Mercadoria" em azul, "Despesa" em roxo)
- Modal de detalhes: conteúdo condicional baseado em `boleto.origem`
  - Mercadoria → exibe informações do pedido + tabela de produtos
  - Despesa → exibe descrição genérica (ex: "Ref. 02/2026 - Internet")

**Frontend (`purchaseOrderService.ts`):**

Atualizada interface `BoletoFornecedor` com novos campos:
```typescript
origem: 'mercadoria' | 'despesa';
descricao?: string;
tipo_documento?: string;
```

### Arquivos modificados
- `backend/app/routes/despesas.py`
- `frontend/.../components/BoletosAVencerPanel.tsx`
- `frontend/.../products/purchaseOrderService.ts`

---

## FALHA #3 — SEED VINCULAVA DESPESAS FIXAS A FORNECEDORES DE MERCADORIA

### Severidade: DADOS (seed/população do banco)

### Descrição

O script `seed_test.py` na função `seed_despesas()` usava `random.choice(fornecedores)` para vincular despesas fixas a fornecedores. Como a lista `fornecedores` continha apenas fornecedores de produtos (Ambev, Colgate, Nestlé, etc.), o resultado era:

| Despesa | Fornecedor atribuído |
|---|---|
| Aluguel | Ambev Distribuidora |
| Energia Elétrica | Colgate-Palmolive |
| Internet/Telefonia | Nestlé Brasil |
| Alvará/Licenças | P&G Brasil |
| Contabilidade | JBS Foods |

Isso é **absurdo do ponto de vista de negócio**.

### Código com defeito (seed_test.py, linha 2032)

```python
# ANTES — fornecedor aleatório de mercadoria para despesa fixa
forn = random.choice(fornecedores) if fornecedores else None
```

### Correção aplicada

O seed agora cria **fornecedores prestadores de serviço dedicados** para cada tipo de despesa fixa:

```python
# DEPOIS — cria prestadores de serviço específicos
prestadores_servico = {}
for desp_data in despesas_fixas:
    nome_prestador = desp_data["fornecedor_nome"]
    if nome_prestador not in prestadores_servico:
        existente = Fornecedor.query.filter_by(
            estabelecimento_id=estabelecimento_id,
            nome_fantasia=nome_prestador,
        ).first()
        if not existente:
            existente = Fornecedor(
                estabelecimento_id=estabelecimento_id,
                nome_fantasia=nome_prestador,
                razao_social=f"{nome_prestador} Serviços LTDA",
                cnpj=fake.cnpj(),
                # ... demais campos ...
            )
            db.session.add(existente)
            db.session.flush()
        prestadores_servico[nome_prestador] = existente

for desp_data in despesas_fixas:
    forn = prestadores_servico.get(desp_data["fornecedor_nome"], fornecedor_fallback)
```

### Resultado após correção

| Despesa | Fornecedor atribuído |
|---|---|
| Aluguel | **Imobiliária** Serviços LTDA |
| Energia Elétrica | **Concessionária** Serviços LTDA |
| Internet/Telefonia | **Telecom** Serviços LTDA |
| Alvará/Licenças | **Prefeitura** Serviços LTDA |
| Contabilidade | **Escritório Contábil** Serviços LTDA |
| Seguro do Imóvel | **Seguradora** Serviços LTDA |
| Sistema de Câmeras | **Segurança** Serviços LTDA |
| Manutenção Ar-Condicionado | **Climatização** Serviços LTDA |
| Software ERP | **TI** Serviços LTDA |

### Arquivo modificado
- `backend/seed_test.py` — função `seed_despesas()`

---

## FLUXOS VERIFICADOS E APROVADOS (SEM FALHAS)

### Fluxo 1: Criar Pedido de Compra → Gera Conta a Pagar

```
[Usuário cria pedido] → PedidoCompra(status=pendente)
                      → ContaPagar(status=aberto, tipo_documento=pedido_compra)
```

- Arquivo: `pedidos_compra.py`, rota `POST /pedidos-compra/`, linhas 187-203
- A `ContaPagar` é criada automaticamente na emissão do pedido
- Valor = total do pedido
- Vencimento = data de previsão de entrega

### Fluxo 2: Receber Pedido → Atualiza Estoque + Cria Lote

```
[Usuário confirma recebimento] → PedidoCompra(status=recebido)
                                → ProdutoLote(numero_lote, data_validade, quantidade)
                                → Produto.quantidade += quantidade_recebida
                                → MovimentacaoEstoque(tipo=entrada)
                                → Produto.preco_custo = CMP recalculado
                                → ContaPagar.valor_original = total realmente recebido
```

- Arquivo: `pedidos_compra.py`, rota `POST /pedidos-compra/receber`, linhas 251-403
- Cada item recebido gera um `ProdutoLote` com:
  - `numero_lote`: fornecido pelo usuário ou gerado automaticamente
  - `data_validade`: fornecida pelo usuário ou padrão 1 ano
  - `preco_custo_unitario`: preço unitário do item no pedido
  - `fornecedor_id` e `pedido_compra_id`: rastreabilidade completa
- O Custo Médio Ponderado (CMP) é recalculado via `recalcular_preco_custo_ponderado()`
- Se o total recebido difere do pedido original, a `ContaPagar` é atualizada

### Fluxo 3: Pagar Boleto → Gera Despesa

```
[Usuário paga boleto] → ContaPagar(status=pago, data_pagamento, valor_pago)
                      → Despesa(categoria=Fornecedores, valor=valor_pago)
```

- Arquivo: `pedidos_compra.py`, rota `POST /boletos/<id>/pagar`, linhas 546-603
- A `Despesa` é criada apenas no momento do pagamento (regime de caixa)
- O boleto pode ser pago parcialmente (status=parcial)

### Fluxo 4: Venda PDV → Decrementa Estoque + FIFO (CORRIGIDO)

```
[Caixa finaliza venda] → Venda(status=finalizada)
                       → VendaItem (com margem_lucro_real calculada)
                       → consumir_estoque_fifo() → ProdutoLote.quantidade decrementada
                       → Produto.quantidade decrementada
                       → MovimentacaoEstoque(tipo=saida, observacoes=lotes consumidos)
```

- Arquivo: `pdv.py`, rota `POST /api/pdv/finalizar`, linhas 456-745
- Validação de estoque com lock pessimista (`with_for_update`)
- Rollback automático em caso de estoque insuficiente (retorna 400)
- Cálculo de margem de lucro real por item

---

## DIAGRAMA DE FLUXO COMPLETO

```
┌─────────────────────────────────────────────────────────────────┐
│                    CICLO DE VIDA - COMPRA                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. EMISSÃO DO PEDIDO                                          │
│     POST /pedidos-compra/                                       │
│     ┌──────────────┐    ┌──────────────┐                       │
│     │ PedidoCompra │───▶│  ContaPagar   │                       │
│     │ status=pend. │    │ status=aberto │                       │
│     └──────────────┘    └──────────────┘                       │
│           │                                                     │
│           ▼                                                     │
│  2. RECEBIMENTO DA MERCADORIA                                  │
│     POST /pedidos-compra/receber                                │
│     ┌──────────────┐    ┌──────────────┐                       │
│     │ PedidoCompra │    │ ProdutoLote  │ ← lote + validade     │
│     │ status=receb.│───▶│ qtd_inicial  │                       │
│     └──────────────┘    │ data_valid.  │                       │
│           │              │ preco_custo  │                       │
│           │              └──────────────┘                       │
│           ▼                     │                               │
│     ┌──────────────┐            ▼                               │
│     │   Produto    │    ┌──────────────┐                       │
│     │ qtd += receb.│    │ Movimentação │                       │
│     │ CMP recalc.  │    │ tipo=entrada │                       │
│     └──────────────┘    └──────────────┘                       │
│           │                                                     │
│           ▼                                                     │
│  3. PAGAMENTO DO BOLETO                                        │
│     POST /boletos/<id>/pagar                                    │
│     ┌──────────────┐    ┌──────────────┐                       │
│     │  ContaPagar   │───▶│   Despesa    │                       │
│     │ status=pago  │    │ cat=Fornec.  │                       │
│     └──────────────┘    └──────────────┘                       │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                    CICLO DE VIDA - VENDA                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  4. VENDA NO PDV                                               │
│     POST /api/pdv/finalizar                                     │
│     ┌──────────────┐    ┌──────────────┐                       │
│     │    Venda     │    │ ProdutoLote  │ ← FIFO por validade   │
│     │ status=final.│    │ qtd -= vend. │                       │
│     └──────────────┘    └──────────────┘                       │
│           │                     │                               │
│           ▼                     ▼                               │
│     ┌──────────────┐    ┌──────────────┐                       │
│     │  VendaItem   │    │   Produto    │                       │
│     │ margem_real  │    │ qtd -= vend. │                       │
│     └──────────────┘    └──────────────┘                       │
│           │                     │                               │
│           ▼                     ▼                               │
│     ┌──────────────┐    ┌──────────────┐                       │
│     │  Pagamento   │    │ Movimentação │                       │
│     │ forma_pgto   │    │ tipo=saida   │                       │
│     └──────────────┘    │ lotes info   │                       │
│                         └──────────────┘                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## CONCLUSÃO

A falha mais grave era o PDV não consumir lotes ao vender, o que invalidava todo o controle de validade FIFO. Com as 3 correções aplicadas, o fluxo completo — da compra à venda — está íntegro e auditável.

**Recomendações futuras:**
1. Criar teste automatizado que valide o decremento de lotes após venda PDV
2. Adicionar alerta quando um lote estiver prestes a zerar (`quantidade < 5`)
3. Implementar relatório de lotes consumidos por período para fiscalização
4. Considerar implementar controle de lote também no cancelamento de venda (devolver ao lote original)
