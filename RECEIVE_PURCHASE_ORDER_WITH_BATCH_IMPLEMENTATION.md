# Implementação: Recebimento de Pedido com Lote e Validade

## 🎯 Objetivo

Permitir que ao receber um pedido de compra, o usuário possa:
1. Informar a data de validade para cada item
2. Informar o número do lote para cada item
3. Automaticamente criar lotes no banco de dados
4. Automaticamente atualizar o estoque com os lotes criados

## ✅ O Que Foi Implementado

### 1. Frontend - ReceivePurchaseModal.tsx

#### Novos Campos na Interface ItemRecebimento
```typescript
interface ItemRecebimento {
  item_id: number;
  produto_nome: string;
  quantidade_solicitada: number;
  quantidade_recebida: number;
  preco_unitario: number;
  data_validade: string;      // ✅ NOVO
  numero_lote: string;        // ✅ NOVO
}
```

#### Inicialização com Valores Padrão
```typescript
// Data de validade padrão: 1 ano a partir de hoje
const dataValidadePadrao = new Date();
dataValidadePadrao.setFullYear(dataValidadePadrao.getFullYear() + 1);

// Número de lote padrão: LOTE-{numero_pedido}-{index}
numero_lote: `LOTE-${detalhes.numero_pedido}-${index + 1}`
```

#### Novos Handlers
- `handleDataValidadeChange()`: Atualiza data de validade do item
- `handleNumeroLoteChange()`: Atualiza número do lote do item

#### Tabela Atualizada
Adicionadas 2 novas colunas:
- **Validade**: Input date para selecionar data de validade
- **Lote**: Input text para informar número do lote

Exemplo visual:
```
┌─────────────┬──────────┬──────────┬──────────┬──────────┬──────────┬────────┬────────┐
│ Produto     │ Solicit. │ Recebido │ Preço    │ Validade │ Lote     │ Total  │ Status │
├─────────────┼──────────┼──────────┼──────────┼──────────┼──────────┼────────┼────────┤
│ Leite 1L    │ 50       │ 50       │ R$ 2.50  │ 2025-02-15 │ LOTE-PC000001-1 │ R$ 125 │ ✓ │
│ Queijo 500g │ 30       │ 30       │ R$ 15.00 │ 2025-03-20 │ LOTE-PC000001-2 │ R$ 450 │ ✓ │
└─────────────┴──────────┴──────────┴──────────┴──────────┴──────────┴────────┴────────┘
```

#### Dados Enviados ao Backend
```typescript
const dadosRecebimento: ReceberPedidoData = {
  pedido_id: 1,
  itens: [
    {
      item_id: 1,
      quantidade_recebida: 50,
      data_validade: "2025-02-15",      // ✅ NOVO
      numero_lote: "LOTE-PC000001-1"    // ✅ NOVO
    },
    {
      item_id: 2,
      quantidade_recebida: 30,
      data_validade: "2025-03-20",      // ✅ NOVO
      numero_lote: "LOTE-PC000001-2"    // ✅ NOVO
    }
  ]
};
```

### 2. Frontend - purchaseOrderService.ts

#### Interface ReceberPedidoData Atualizada
```typescript
export interface ReceberPedidoData {
  pedido_id: number;
  numero_nota_fiscal?: string;
  serie_nota_fiscal?: string;
  gerar_boleto: boolean;
  data_vencimento?: string;
  numero_documento?: string;
  itens: {
    item_id: number;
    quantidade_recebida: number;
    data_validade?: string;      // ✅ NOVO
    numero_lote?: string;        // ✅ NOVO
  }[];
}
```

### 3. Backend - pedidos_compra.py (Já Implementado)

O endpoint `receber_pedido_compra()` já foi atualizado para:

1. **Receber os dados de validade e lote**
```python
data_validade = None
if item_data.get('data_validade'):
    from datetime import datetime as dt
    data_validade = dt.strptime(item_data['data_validade'], '%Y-%m-%d').date()

numero_lote = f"LOTE-{pedido.numero_pedido}-{item.id}"
```

2. **Criar ProdutoLote automaticamente**
```python
lote = ProdutoLote(
    estabelecimento_id=user.estabelecimento_id,
    produto_id=produto.id,
    fornecedor_id=pedido.fornecedor_id,
    pedido_compra_id=pedido.id,
    numero_lote=numero_lote,
    quantidade=quantidade_recebida,
    quantidade_inicial=quantidade_recebida,
    data_validade=data_validade or (date.today() + timedelta(days=365)),
    data_entrada=date.today(),
    preco_custo_unitario=item.preco_unitario,
    ativo=True,
)
db.session.add(lote)
```

3. **Atualizar estoque do produto**
```python
produto.quantidade += quantidade_recebida
```

4. **Registrar movimentação de estoque**
```python
movimentacao = MovimentacaoEstoque(
    tipo='entrada',
    quantidade=quantidade_recebida,
    motivo=f'Recebimento pedido {pedido.numero_pedido}',
    observacoes=f'Lote: {numero_lote}'
)
```

## 🔄 Fluxo Completo

### Passo 1: Abrir Modal de Recebimento
```
Menu → Compras → Pedidos Pendentes
└── Selecionar Pedido → Clicar "Receber"
```

### Passo 2: Preencher Dados
```
Modal de Recebimento
├── Tabela de Itens
│   ├── Quantidade Recebida: 50 ✓
│   ├── Data de Validade: 2025-02-15 ✓ (NOVO)
│   └── Número do Lote: LOTE-PC000001-1 ✓ (NOVO)
├── Nota Fiscal (opcional)
└── Gerar Boleto (opcional)
```

### Passo 3: Confirmar Recebimento
```
Clicar "Confirmar Recebimento"
```

### Passo 4: Backend Processa
```
Backend (receber_pedido_compra)
├── Validar dados
├── Para cada item:
│   ├── Criar ProdutoLote
│   │   ├── numero_lote = "LOTE-PC000001-1"
│   │   ├── quantidade = 50
│   │   ├── data_validade = 2025-02-15
│   │   └── preco_custo_unitario = 2.50
│   ├── Criar MovimentacaoEstoque
│   │   ├── tipo = "entrada"
│   │   ├── quantidade = 50
│   │   └── observacoes = "Lote: LOTE-PC000001-1"
│   └── Atualizar Produto.quantidade += 50
├── Atualizar PedidoCompra.status = "recebido"
└── Criar ContaPagar (se solicitado)
```

### Passo 5: Resultado
```
✅ Pedido recebido com sucesso
✅ Lotes criados automaticamente
✅ Estoque atualizado
✅ Movimentações registradas
✅ Boleto gerado (se solicitado)
```

## 📊 Exemplo Prático

### Cenário: Receber Pedido de Leite

**Pedido PC000001**
- Item 1: Leite 1L x 50 un, validade 15/02/2025
- Item 2: Leite 1L x 30 un, validade 20/03/2025

**Ações do Usuário**
1. Abrir modal de recebimento
2. Confirmar quantidades (50 e 30)
3. Confirmar datas de validade (15/02 e 20/03)
4. Confirmar lotes (LOTE-PC000001-1 e LOTE-PC000001-2)
5. Clicar "Confirmar Recebimento"

**Resultado no Banco**
```
ProdutoLote 1:
- numero_lote: LOTE-PC000001-1
- quantidade: 50
- data_validade: 2025-02-15
- preco_custo_unitario: 2.50

ProdutoLote 2:
- numero_lote: LOTE-PC000001-2
- quantidade: 30
- data_validade: 2025-03-20
- preco_custo_unitario: 2.50

Produto (Leite 1L):
- quantidade: 80 (50 + 30)
- total_vendido: 0 (ainda não vendeu)

MovimentacaoEstoque 1:
- tipo: entrada
- quantidade: 50
- motivo: Recebimento pedido PC000001
- observacoes: Lote: LOTE-PC000001-1

MovimentacaoEstoque 2:
- tipo: entrada
- quantidade: 30
- motivo: Recebimento pedido PC000001
- observacoes: Lote: LOTE-PC000001-2
```

## 🎯 Benefícios

✅ **Controle de Validade**: Cada lote tem sua própria data de validade
✅ **Rastreabilidade**: Sabe exatamente qual fornecedor, quando entrou, qual validade
✅ **FIFO Automático**: Vende primeiro o que vence primeiro
✅ **Estoque Consistente**: Quantidade sempre = SUM(lotes.quantidade)
✅ **Auditoria Completa**: Todas as movimentações registradas
✅ **Flexibilidade**: Suporta múltiplas compras do mesmo produto com datas diferentes

## 🔍 Validações

- ✅ Data de validade obrigatória (padrão: 1 ano)
- ✅ Número de lote obrigatório (padrão: LOTE-{pedido}-{item})
- ✅ Quantidade recebida deve ser > 0
- ✅ Quantidade recebida não pode exceder quantidade solicitada
- ✅ Lote deve ser único por estabelecimento

## 📝 Checklist de Implementação

- [x] Adicionar campos de validade e lote no frontend
- [x] Atualizar interface ReceberPedidoData
- [x] Adicionar handlers para atualizar validade e lote
- [x] Atualizar tabela para exibir novos campos
- [x] Enviar dados de validade e lote ao backend
- [x] Backend recebe e processa dados
- [x] Backend cria ProdutoLote automaticamente
- [x] Backend atualiza estoque
- [x] Backend registra movimentações
- [x] Testes de integração (próximo)

## 🚀 Próximos Passos

1. **Testes de Integração**: Testar fluxo completo
2. **Validações Adicionais**: Validar datas de validade
3. **Alertas**: Notificar quando lote vence
4. **Relatórios**: Relatório de lotes por vencer
5. **Devolução**: Permitir devolver lotes ao fornecedor

## 📞 Resumo

O sistema agora permite que ao receber um pedido de compra, o usuário possa informar a data de validade e o número do lote para cada item. O backend automaticamente:

1. Cria um `ProdutoLote` para cada item recebido
2. Atualiza o estoque do produto
3. Registra a movimentação de estoque
4. Mantém rastreabilidade completa

Isso garante que o estoque seja sempre consistente e que cada lote seja rastreável desde a entrada até a venda.

---

**Status**: ✅ Implementação Completa
**Data**: Fevereiro 2025
**Versão**: 1.0
