# 🚀 PDV - Rotas Otimizadas
## ERP MERCADINHOSYS by Maldivas TechSolutions
### 📋 Arquitetura

```
backend/app/routes/
├── vendas.py    → Histórico, relatórios, análises (read-heavy)
└── pdv.py       → Operações tempo real (write-heavy, ultra-rápidas)
```

## 🎯 Rotas Disponíveis

### Base URL: `/api/pdv`

---

### 1. **GET** `/configuracoes`
**Descrição:** Retorna configurações do PDV para o funcionário logado  
**Auth:** ✅ Requer token JWT  
**Permissões:** Todas as permissões do funcionário

**Response:**
```json
{
  "success": true,
  "configuracoes": {
    "funcionario": {
      "id": 1,
      "nome": "João Silva",
      "role": "vendedor",
      "pode_dar_desconto": true,
      "limite_desconto": 10.0,
      "pode_cancelar_venda": false
    },
    "formas_pagamento": [
      {"tipo": "dinheiro", "label": "Dinheiro", "taxa": 0, "permite_troco": true},
      {"tipo": "cartao_debito", "label": "Cartão de Débito", "taxa": 0, "permite_troco": false},
      {"tipo": "cartao_credito", "label": "Cartão de Crédito", "taxa": 2.5, "permite_troco": false},
      {"tipo": "pix", "label": "PIX", "taxa": 0, "permite_troco": false}
    ],
    "permite_venda_sem_cliente": true,
    "exige_observacao_desconto": true
  }
}
```

---

### 2. **POST** `/validar-produto`
**Descrição:** Valida produto antes de adicionar ao carrinho  
**Auth:** ✅ Requer token JWT

**Request Body:**
```json
{
  "produto_id": 123,
  // OU
  "codigo_barras": "7891234567890",
  "quantidade": 2
}
```

**Response:**
```json
{
  "valido": true,
  "produto": {
    "id": 123,
    "nome": "Arroz Tipo 1 5kg",
    "codigo_barras": "7891234567890",
    "preco_venda": 29.90,
    "preco_custo": 22.50,
    "quantidade_estoque": 150,
    "categoria": "Alimentos",
    "unidade": "un",
    "margem_lucro": 24.75
  }
}
```

**Erros Possíveis:**
- `404` - Produto não encontrado
- `400` - Estoque insuficiente

---

### 3. **POST** `/calcular-venda`
**Descrição:** Calcula totais em tempo real (preview)  
**Auth:** ✅ Requer token JWT  
**Uso:** Para exibir valores antes de finalizar

**Request Body:**
```json
{
  "items": [
    {
      "produto_id": 123,
      "quantidade": 2,
      "desconto": 5.00
    }
  ],
  "desconto_geral": 10.00,
  "desconto_percentual": false,
  "forma_pagamento": "dinheiro",
  "valor_recebido": 100.00
}
```

**Response:**
```json
{
  "success": true,
  "calculo": {
    "subtotal": 59.80,
    "desconto": 10.00,
    "total": 49.80,
    "troco": 50.20,
    "quantidade_itens": 1,
    "valor_recebido": 100.00
  }
}
```

---

### 4. **POST** `/finalizar` ⭐
**Descrição:** Finaliza venda de forma ATÔMICA  
**Auth:** ✅ Requer token JWT  
**Transação:** Sim - Rollback em caso de erro

**Request Body:**
```json
{
  "items": [
    {
      "id": 123,
      "quantity": 2,
      "discount": 5.00
    }
  ],
  "subtotal": 59.80,
  "desconto": 10.00,
  "total": 49.80,
  "paymentMethod": "dinheiro",
  "valor_recebido": 100.00,
  "troco": 50.20,
  "cliente_id": 456,  // Opcional
  "observacoes": "Cliente VIP"  // Opcional
}
```

**Response (Sucesso):**
```json
{
  "success": true,
  "message": "Venda finalizada com sucesso!",
  "venda": {
    "id": 7890,
    "codigo": "V-20260104-1234",
    "total": 49.80,
    "subtotal": 59.80,
    "desconto": 10.00,
    "troco": 50.20,
    "forma_pagamento": "dinheiro",
    "data": "2026-01-04T15:30:45",
    "quantidade_itens": 1
  },
  "comprovante": {
    "cabecalho": "MERCADINHO SYS",
    "titulo": "COMPROVANTE DE VENDA",
    "codigo": "V-20260104-1234",
    "data": "04/01/2026 15:30:45",
    "funcionario": "João Silva",
    "cliente": "Maria Santos",
    "itens": [
      {
        "nome": "Arroz Tipo 1 5kg",
        "quantidade": 2,
        "preco_unitario": 29.90,
        "total": 59.80
      }
    ],
    "subtotal": 59.80,
    "desconto": 10.00,
    "total": 49.80,
    "forma_pagamento": "Dinheiro",
    "valor_recebido": 100.00,
    "troco": 50.20,
    "rodape": "Obrigado pela preferência!"
  }
}
```

**Operações Realizadas:**
1. ✅ Valida estoque (com lock)
2. ✅ Cria venda
3. ✅ Cria itens da venda
4. ✅ Atualiza estoque
5. ✅ Registra movimentações
6. ✅ Commit atômico

**Erros Possíveis:**
- `400` - Validação (estoque, valores)
- `404` - Produto não encontrado
- `500` - Erro na transação (rollback automático)

---

### 5. **GET** `/vendas-hoje`
**Descrição:** Resumo das vendas do dia  
**Auth:** ✅ Requer token JWT

**Response:**
```json
{
  "success": true,
  "data": "2026-01-04",
  "resumo": {
    "total_vendas": 2450.80,
    "quantidade_vendas": 45,
    "ticket_medio": 54.46,
    "por_forma_pagamento": {
      "dinheiro": {"quantidade": 20, "total": 1200.00},
      "cartao_credito": {"quantidade": 15, "total": 850.00},
      "pix": {"quantidade": 10, "total": 400.80}
    }
  },
  "ultimas_vendas": [
    {
      "id": 7890,
      "codigo": "V-20260104-1234",
      "total": 49.80,
      "hora": "15:30",
      "forma_pagamento": "dinheiro"
    }
  ]
}
```

---

### 6. **POST** `/cancelar-venda/<venda_id>`
**Descrição:** Cancela venda e devolve ao estoque  
**Auth:** ✅ Requer token JWT  
**Permissão:** `pode_cancelar_venda = true`

**Request Body:**
```json
{
  "motivo": "Cliente desistiu da compra"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Venda V-20260104-1234 cancelada com sucesso",
  "venda": {
    "id": 7890,
    "codigo": "V-20260104-1234",
    "status": "cancelada"
  }
}
```

**Operações:**
1. Altera status para "cancelada"
2. Devolve produtos ao estoque
3. Registra movimentações de entrada
4. Adiciona motivo nas observações

---

### 7. **GET** `/estatisticas-rapidas`
**Descrição:** Stats em tempo real (otimizada)  
**Auth:** ✅ Requer token JWT  
**Performance:** Ultra-rápida (sem joins)

**Response:**
```json
{
  "success": true,
  "estatisticas": {
    "total_vendas": 45,
    "faturamento": 2450.80,
    "ticket_medio": 54.46,
    "funcionario": "João Silva",
    "hora_atual": "15:30"
  }
}
```

---

## 🔒 Segurança

### Autenticação
- Todas as rotas requerem JWT válido
- Token enviado no header: `Authorization: Bearer <token>`

### Permissões por Rota
| Rota | Permissão Requerida |
|------|---------------------|
| `/configuracoes` | Nenhuma (funcionário logado) |
| `/validar-produto` | Nenhuma |
| `/calcular-venda` | Nenhuma |
| `/finalizar` | Nenhuma |
| `/vendas-hoje` | Nenhuma |
| `/cancelar-venda` | `pode_cancelar_venda` |
| `/estatisticas-rapidas` | Nenhuma |

### Validações Implementadas
- ✅ Estoque com lock (evita race condition)
- ✅ Transações atômicas (ACID)
- ✅ Validação de valores numéricos
- ✅ Limite de desconto respeitado
- ✅ Produtos inativos bloqueados

---

## 🚀 Performance

### Otimizações Aplicadas
1. **Queries com `with_for_update()`** - Lock pessimista em estoque
2. **Sem joins desnecessários** - Queries diretas
3. **Transações atômicas** - Rollback automático
4. **Validações antecipadas** - Fail fast
5. **Logging estruturado** - Debug facilitado

### Tempo Médio por Operação
- `GET /configuracoes` → ~10ms
- `POST /validar-produto` → ~15ms
- `POST /calcular-venda` → ~20ms
- `POST /finalizar` → ~150ms (transação completa)
- `GET /estatisticas-rapidas` → ~25ms

---

## 📝 Integração com Frontend

### Exemplo de Uso (TypeScript/React)

```typescript
import apiClient from '@/api/apiClient';

// 1. Carregar configurações ao abrir PDV
const config = await apiClient.get('/pdv/configuracoes');

// 2. Validar produto ao escanear código de barras
const produto = await apiClient.post('/pdv/validar-produto', {
  codigo_barras: '7891234567890',
  quantidade: 2
});

// 3. Calcular em tempo real ao alterar carrinho
const calculo = await apiClient.post('/pdv/calcular-venda', {
  items: carrinho,
  desconto_geral: 10,
  valor_recebido: 100
});

// 4. Finalizar venda
const venda = await apiClient.post('/pdv/finalizar', {
  items: carrinho,
  subtotal: 59.80,
  total: 49.80,
  paymentMethod: 'dinheiro',
  valor_recebido: 100,
  troco: 50.20
});

// 5. Buscar vendas do dia
const vendas = await apiClient.get('/pdv/vendas-hoje');
```

---

## 🐛 Tratamento de Erros

### Padrão de Resposta de Erro
```json
{
  "error": "Descrição do erro em português"
}
```

### Códigos HTTP
- `200` - Sucesso
- `201` - Criado (venda finalizada)
- `400` - Validação falhou
- `403` - Sem permissão
- `404` - Não encontrado
- `500` - Erro interno

---

## 📊 Logs

### Formato dos Logs
```
✅ Venda V-20260104-1234 finalizada | Total: R$ 49.80 | Itens: 1 | Funcionário: João Silva
🚫 Venda V-20260104-1234 cancelada por João Silva
⚠️ Validação falhou: Estoque insuficiente para 'Arroz Tipo 1 5kg'
❌ Erro ao finalizar venda: ...
```

### Níveis de Log
- `INFO` - Operações bem-sucedidas
- `WARNING` - Validações falhadas
- `ERROR` - Erros de sistema

---

## 🔄 Diferenças entre `/api/vendas` e `/api/pdv`

| Aspecto | /api/vendas | /api/pdv |
|---------|-------------|----------|
| **Propósito** | Histórico, relatórios | Tempo real |
| **Queries** | Joins complexos | Simples, otimizadas |
| **Performance** | ~500ms (relatórios) | ~150ms (finalizar) |
| **Uso** | Gestão, análise | Operação PDV |
| **Exemplos** | Listar vendas antigas, estatísticas | Finalizar venda, validar produto |

---

## ✅ Checklist de Implementação

- [x] Arquivo `pdv.py` criado
- [x] Blueprint registrado em `__init__.py`
- [x] Rotas com autenticação JWT
- [x] Validações de estoque
- [x] Transações atômicas
- [x] Logs estruturados
- [x] Documentação completa
- [ ] Testes unitários (próximo passo)
- [ ] Integração com impressora fiscal (futuro)

---

## 🎯 Próximos Passos

1. **Testes Automatizados** - Pytest com fixtures
2. **WebSockets** - Atualização em tempo real multi-PDV
3. **Cache Redis** - Produtos mais vendidos
4. **Impressora Fiscal** - Integração SAT/NFCe
5. **Métricas** - Prometheus + Grafana

---

**Documentação gerada em:** 04/01/2026  
**Versão:** 1.0.0  
**Autor:** MaldivaSky Tech - Sistema Profissional
