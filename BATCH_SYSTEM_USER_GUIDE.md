# Guia de Uso - Sistema de Lotes/Batches com Validade

## 🎯 Introdução

O sistema de lotes permite que você gerencie produtos com múltiplas datas de validade. Quando você compra o mesmo produto em datas diferentes, cada compra cria um lote separado com sua própria data de validade.

## 📋 Cenário Prático

### Exemplo: Leite Integral 1L

**Situação Real**:
- Dia 15/01: Compra 50 unidades de Leite, validade 15/02
- Dia 20/01: Compra 30 unidades de Leite, validade 20/03

**Sem Sistema de Lotes** ❌
- Estoque: 80 unidades de Leite
- Problema: Não sabe qual vence primeiro
- Risco: Vende o que vence depois, deixa vencer o que vence antes

**Com Sistema de Lotes** ✅
- Lote 1: 50 unidades, vence 15/02
- Lote 2: 30 unidades, vence 20/03
- Automático: Vende primeiro o Lote 1 (FIFO)
- Seguro: Nunca deixa vencer

## 🔄 Passo a Passo

### 1️⃣ Criar Pedido de Compra

```
Menu → Compras → Novo Pedido
├── Fornecedor: Laticínios Silva
├── Item 1: Leite 1L
│   ├── Quantidade: 50
│   ├── Preço: R$ 2,50
│   └── Validade: 15/02/2025
├── Item 2: Leite 1L
│   ├── Quantidade: 30
│   ├── Preço: R$ 2,50
│   └── Validade: 20/03/2025
└── Salvar Pedido
```

### 2️⃣ Receber Pedido

```
Menu → Compras → Pedidos Pendentes
├── Selecionar: PC000001
├── Clicar: "Receber Pedido"
├── Confirmar Quantidades
│   ├── Item 1: 50 unidades ✓
│   └── Item 2: 30 unidades ✓
├── Confirmar Datas de Validade
│   ├── Item 1: 15/02/2025 ✓
│   └── Item 2: 20/03/2025 ✓
└── Clicar: "Confirmar Recebimento"
```

**O que acontece automaticamente**:
- ✅ Cria Lote 1: LOTE-PC000001-1 (50 un, vence 15/02)
- ✅ Cria Lote 2: LOTE-PC000001-2 (30 un, vence 20/03)
- ✅ Atualiza estoque: Leite = 80 unidades
- ✅ Registra movimentação de entrada

### 3️⃣ Consultar Lotes Disponíveis

```
Menu → Estoque → Produtos
├── Buscar: Leite Integral 1L
├── Clicar: "Ver Lotes"
└── Resultado:
    ├── Lote 1: LOTE-PC000001-1
    │   ├── Quantidade: 50 un
    │   ├── Validade: 15/02/2025
    │   ├── Dias para vencer: 5 dias ⚠️
    │   └── Status: Próximo de vencer
    ├── Lote 2: LOTE-PC000001-2
    │   ├── Quantidade: 30 un
    │   ├── Validade: 20/03/2025
    │   ├── Dias para vencer: 39 dias ✓
    │   └── Status: Normal
    └── Total: 80 unidades
```

### 4️⃣ Vender com FIFO Automático

```
Menu → PDV → Novo Carrinho
├── Adicionar: Leite 1L x 60 unidades
├── Sistema Automaticamente:
│   ├── Seleciona Lote 1 (vence 15/02): 50 unidades
│   ├── Seleciona Lote 2 (vence 20/03): 10 unidades
│   └── Mostra: "Usando FIFO - Lote 1 vence em 5 dias"
├── Finalizar Venda
└── Resultado:
    ├── Lote 1: 0 unidades (pode ser marcado como vendido)
    ├── Lote 2: 20 unidades (continua disponível)
    └── Estoque Total: 20 unidades
```

## 📊 Visualização de Lotes

### Tela de Detalhes do Produto

```
┌─────────────────────────────────────────┐
│ Leite Integral 1L                       │
├─────────────────────────────────────────┤
│ Estoque Total: 80 unidades              │
│ Quantidade Mínima: 10 unidades          │
│ Preço: R$ 2,50                          │
├─────────────────────────────────────────┤
│ LOTES DISPONÍVEIS (FIFO)                │
├─────────────────────────────────────────┤
│ 1. LOTE-PC000001-1                      │
│    Quantidade: 50 un                    │
│    Validade: 15/02/2025                 │
│    Dias para vencer: 5 ⚠️               │
│    Fornecedor: Laticínios Silva         │
│    Entrada: 15/01/2025                  │
│                                         │
│ 2. LOTE-PC000001-2                      │
│    Quantidade: 30 un                    │
│    Validade: 20/03/2025                 │
│    Dias para vencer: 39 ✓               │
│    Fornecedor: Laticínios Silva         │
│    Entrada: 20/01/2025                  │
└─────────────────────────────────────────┘
```

## 🎯 Casos de Uso

### Caso 1: Produto com Múltiplas Compras

**Situação**:
- Compra 1: 100 un, validade 01/03
- Compra 2: 50 un, validade 15/03
- Compra 3: 75 un, validade 01/04

**Resultado**:
- Estoque: 225 unidades
- Lotes: 3 (cada um com sua validade)
- Venda: Sempre começa pelo que vence primeiro

### Caso 2: Produto Próximo de Vencer

**Situação**:
- Lote 1: 30 un, vence em 2 dias ⚠️
- Lote 2: 50 un, vence em 30 dias ✓

**Ação Automática**:
- Sistema alerta: "Lote 1 vence em 2 dias"
- Sugestão: Aplicar desconto para vender rápido
- Venda: Sempre começa pelo Lote 1

### Caso 3: Devolução de Lote

**Situação**:
- Lote recebido com defeito
- Precisa devolver ao fornecedor

**Processo**:
1. Menu → Compras → Devoluções
2. Selecionar: Lote-PC000001-1
3. Motivo: "Produto com defeito"
4. Quantidade: 50 unidades
5. Sistema marca lote como inativo
6. Estoque atualizado automaticamente

## ⚠️ Alertas e Notificações

### Alertas Automáticos

1. **Lote Próximo de Vencer** (7 dias)
   - Notificação: "Lote X vence em 7 dias"
   - Ação: Considerar desconto

2. **Lote Vencido**
   - Notificação: "Lote X venceu"
   - Ação: Não pode vender, deve descartar

3. **Estoque Baixo**
   - Notificação: "Estoque de Leite abaixo do mínimo"
   - Ação: Criar novo pedido de compra

## 🔍 Relatórios

### Relatório de Lotes por Vencer

```
Menu → Relatórios → Lotes por Vencer

Período: Próximos 30 dias

┌──────────────────────────────────────────────┐
│ Produto          │ Lote      │ Qtd │ Vence  │
├──────────────────────────────────────────────┤
│ Leite 1L         │ LOTE-001  │ 50  │ 15/02  │
│ Iogurte 500ml    │ LOTE-002  │ 30  │ 18/02  │
│ Queijo 500g      │ LOTE-003  │ 20  │ 22/02  │
│ Manteiga 200g    │ LOTE-004  │ 15  │ 25/02  │
└──────────────────────────────────────────────┘

Total: 4 lotes vencendo em 30 dias
Ação Recomendada: Aplicar desconto ou promover
```

### Relatório de Rotatividade por Lote

```
Menu → Relatórios → Rotatividade

┌──────────────────────────────────────────────┐
│ Lote      │ Entrada │ Saída  │ Dias │ Giro  │
├──────────────────────────────────────────────┤
│ LOTE-001  │ 15/01   │ 20/01  │ 5    │ Rápido│
│ LOTE-002  │ 10/01   │ 25/01  │ 15   │ Normal│
│ LOTE-003  │ 05/01   │ Aberto │ 36   │ Lento │
└──────────────────────────────────────────────┘
```

## 🛠️ Configurações

### Ativar/Desativar Controle de Validade

```
Menu → Configurações → Estoque
├── Controlar Validade: ✓ Ativado
├── Dias de Alerta: 7 dias
├── Permitir Venda de Vencidos: ✗ Desativado
└── Salvar
```

### Padrão de Data de Validade

```
Menu → Configurações → Estoque
├── Se não informar validade:
│   └── Padrão: 1 ano (365 dias)
└── Salvar
```

## 📱 API para Desenvolvedores

### Consultar Lotes Disponíveis

```bash
GET /produtos/5/lotes-disponiveis

Response:
{
  "produto_id": 5,
  "produto_nome": "Leite Integral 1L",
  "total_quantidade": 80,
  "lotes": [
    {
      "id": 1,
      "numero_lote": "LOTE-PC000001-1",
      "quantidade": 50,
      "data_validade": "2025-02-15",
      "dias_para_vencer": 5,
      "esta_vencido": false,
      "preco_custo_unitario": 2.50
    }
  ]
}
```

### Receber Pedido com Lotes

```bash
POST /pedidos-compra/receber

Request:
{
  "pedido_id": 1,
  "itens": [
    {
      "item_id": 1,
      "quantidade_recebida": 50,
      "data_validade": "2025-02-15"
    }
  ]
}

Response:
{
  "message": "Pedido recebido com sucesso",
  "pedido": { ... }
}
```

## ✅ Checklist de Implementação

- [x] Criar modelo ProdutoLote
- [x] Recebimento automático de lotes
- [x] FIFO automático na venda
- [x] Consulta de lotes disponíveis
- [x] Alertas de validade
- [ ] Relatórios de lotes (próximo)
- [ ] Devolução de lotes (próximo)
- [ ] Desconto automático para lotes próximos de vencer (próximo)

## 🎓 Dúvidas Frequentes

**P: O que acontece se não informar a data de validade?**
R: O sistema usa padrão de 1 ano (365 dias) a partir da data de entrada.

**P: Posso vender um lote vencido?**
R: Não. O sistema impede venda de lotes vencidos automaticamente.

**P: Como devolver um lote?**
R: Menu → Compras → Devoluções. Selecione o lote e o motivo.

**P: O FIFO é automático?**
R: Sim. O sistema sempre vende primeiro o lote que vence primeiro.

**P: Posso ver o histórico de um lote?**
R: Sim. Clique em "Ver Detalhes" do lote para ver entrada, saídas e movimentações.

**P: Como saber qual fornecedor forneceu cada lote?**
R: Cada lote registra o fornecedor. Veja em "Detalhes do Lote".

## 🚀 Próximas Funcionalidades

1. **Desconto Automático**: Aplicar desconto para lotes próximos de vencer
2. **Alertas por Email**: Notificação quando lote vence em 7 dias
3. **Rastreabilidade**: Ver todas as vendas de um lote específico
4. **Devolução**: Devolver lotes ao fornecedor
5. **Relatórios Avançados**: Análise de rotatividade por lote

## 📞 Suporte

Para dúvidas ou problemas com o sistema de lotes:
1. Consulte este guia
2. Verifique os alertas do sistema
3. Contate o suporte técnico

---

**Versão**: 1.0
**Data**: Fevereiro 2025
**Status**: ✅ Pronto para Produção
