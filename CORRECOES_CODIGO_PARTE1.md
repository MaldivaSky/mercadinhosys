# 🔧 CORREÇÕES DE CÓDIGO - PARTE 1
## Backend - Múltiplos Pagamentos

---

## ARQUIVO: backend/app/routes/pdv.py

### PROBLEMA: finalizar_venda() está incompleto (linha ~747)

### SOLUÇÃO: Completar a função

Adicionar após a criação de `nova_venda`:

```python
# ==================== CRIAR PAGAMENTOS ====================
# Validar que soma dos pagamentos = total da venda
pagamentos_data = data.get("pagamentos", [])
if not pagamentos_data:
    db.session.rollback()
    return jsonify({"error": "Nenhuma forma de pagamento informada"}), 400

total_pagamentos = sum(Decimal(str(p.get("valor", 0))) for p in pagamentos_data)
if abs(total_pagamentos - total) > Decimal('0.01'):
    db.session.rollback()
    return jsonify({
        "error": "Valor dos pagamentos não corresponde ao total",
        "total_esperado": float(total),
        "total_recebido": float(total_pagamentos)
    }), 400

# Criar registros de pagamento
for pagamento_data in pagamentos_data:
    forma = pagamento_data.get("forma", "dinheiro")
    valor = to_decimal(pagamento_data.get("valor", 0))
    
    pagamento = Pagamento(
        venda_id=nova_venda.id,
        forma_pagamento=forma,
        valor=valor,
        referencia=pagamento_data.get("referencia"),
        data_pagamento=data_venda,
        estabelecimento_id=estab_id
    )
    db.session.add(pagamento)

# ==================== CRIAR CONTA A RECEBER (FIADO) ====================
fiados = [p for p in pagamentos_data if p.get("forma") == "fiado"]
if fiados:
    valor_fiado = sum(Decimal(str(p.get("valor", 0))) for p in fiados)
    data_vencimento_fiado = data.get("data_vencimento_fiado")
    
    if data_vencimento_fiado:
        try:
            data_vencimento = datetime.fromisoformat(data_vencimento_fiado)
        except:
            data_vencimento = data_venda + timedelta(days=30)
    else:
        data_vencimento = data_venda + timedelta(days=30)
    
    conta_receber = ContaReceber(
        cliente_id=cliente_id,
        venda_id=nova_venda.id,
        valor=valor_fiado,
        data_vencimento=data_vencimento,
        status="aberta",
        estabelecimento_id=estab_id
    )
    db.session.add(conta_receber)
    
    # Atualizar saldo devedor do cliente
    if cliente_id:
        cliente = Cliente.query.get(cliente_id)
        if cliente:
            cliente.saldo_devedor = (cliente.saldo_devedor or Decimal('0')) + valor_fiado

# ==================== ATUALIZAR ESTOQUE ====================
for item in items:
    produto_id = item.get("produto_id")
    quantidade = Decimal(str(item.get("quantidade", 0)))
    
    # Lock pessimista para evitar race condition
    produto = Produto.query.with_for_update().get(produto_id)
    if not produto:
        db.session.rollback()
        return jsonify({"error": f"Produto {produto_id} não encontrado"}), 404
    
    if produto.quantidade < quantidade:
        db.session.rollback()
        return jsonify({
            "error": f"Estoque insuficiente para {produto.nome}",
            "disponivel": float(produto.quantidade),
            "solicitado": float(quantidade)
        }), 400
    
    produto.quantidade -= quantidade
    
    # Registrar movimentação
    movimentacao = MovimentacaoEstoque(
        produto_id=produto_id,
        tipo="saida",
        quantidade=quantidade,
        venda_id=nova_venda.id,
        estabelecimento_id=estab_id,
        motivo="venda_pdv"
    )
    db.session.add(movimentacao)

# ==================== REGISTRAR MOVIMENTAÇÃO DE CAIXA ====================
for pagamento_data in pagamentos_data:
    forma = pagamento_data.get("forma", "dinheiro")
    valor = to_decimal(pagamento_data.get("valor", 0))
    
    # Não registrar fiado como entrada de caixa
    if forma != "fiado":
        movimentacao_caixa = MovimentacaoCaixa(
            caixa_id=caixa_aberto.id,
            tipo="entrada",
            valor=valor,
            descricao=f"Venda {nova_venda.codigo} - {forma}",
            venda_id=nova_venda.id,
            estabelecimento_id=estab_id
        )
        db.session.add(movimentacao_caixa)

# ==================== COMMIT ATÔMICO ====================
try:
    db.session.commit()
    logger.info(f"Venda {nova_venda.codigo} finalizada com sucesso")
    
    return jsonify({
        "success": True,
        "venda": {
            "id": nova_venda.id,
            "codigo": nova_venda.codigo,
            "total": float(nova_venda.total),
            "pagamentos": [
                {
                    "forma": p.forma_pagamento,
                    "valor": float(p.valor)
                }
                for p in nova_venda.pagamentos
            ]
        }
    }), 201
    
except Exception as e:
    db.session.rollback()
    logger.error(f"Erro ao finalizar venda: {str(e)}", exc_info=True)
    return jsonify({
        "error": "Erro ao finalizar venda",
        "details": str(e) if current_app.debug else "Contate o suporte"
    }), 500
```

---

## ARQUIVO: backend/app/models.py

### VERIFICAR: Modelo Pagamento existe?

Se não existir, adicionar:

```python
class Pagamento(db.Model, SerializableMixin, AuditMixin, MultiTenantMixin):
    """Registro de forma de pagamento de uma venda"""
    __tablename__ = "pagamentos"
    
    id = db.Column(db.Integer, primary_key=True)
    venda_id = db.Column(db.Integer, db.ForeignKey("vendas.id", ondelete="CASCADE"), nullable=False)
    forma_pagamento = db.Column(db.String(50), nullable=False)  # dinheiro, cartao_credito, pix, fiado
    valor = db.Column(db.Numeric(12, 2), nullable=False)
    referencia = db.Column(db.String(100))  # NSU, autorização, etc
    data_pagamento = db.Column(db.DateTime, default=utcnow)
    estabelecimento_id = TenantID()
    
    # Relacionamentos
    venda = db.relationship("Venda", backref="pagamentos")
    
    def __repr__(self):
        return f"<Pagamento {self.id}: {self.forma_pagamento} R${self.valor}>"
```

---

## ARQUIVO: backend/app/models.py

### VERIFICAR: Modelo ContaReceber existe?

Se não existir, adicionar:

```python
class ContaReceber(db.Model, SerializableMixin, AuditMixin, MultiTenantMixin):
    """Contas a receber (fiados)"""
    __tablename__ = "contas_receber"
    
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"), nullable=False)
    venda_id = db.Column(db.Integer, db.ForeignKey("vendas.id"), nullable=True)
    valor = db.Column(db.Numeric(12, 2), nullable=False)
    data_vencimento = db.Column(db.DateTime, nullable=False)
    data_pagamento = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default="aberta")  # aberta, paga, vencida
    estabelecimento_id = TenantID()
    
    # Relacionamentos
    cliente = db.relationship("Cliente", backref="contas_receber")
    venda = db.relationship("Venda", backref="contas_receber")
    
    def __repr__(self):
        return f"<ContaReceber {self.id}: {self.cliente.nome} R${self.valor}>"
```

---

## ARQUIVO: backend/app/models.py

### VERIFICAR: Modelo Venda tem campo saldo_devedor?

Se não tiver, adicionar ao Cliente:

```python
class Cliente(db.Model, SerializableMixin, AuditMixin, MultiTenantMixin, EnderecoMixin):
    # ... campos existentes ...
    
    saldo_devedor = db.Column(db.Numeric(12, 2), default=0)  # Total de fiados em aberto
    limite_credito = db.Column(db.Numeric(12, 2), default=0)  # Limite de crédito
    
    @property
    def pode_fazer_fiado(self):
        """Verifica se cliente pode fazer fiado"""
        return (self.saldo_devedor or 0) < (self.limite_credito or 0)
```

---

## PRÓXIMAS ETAPAS

1. Aplicar estas correções
2. Executar migrations: `flask db upgrade`
3. Testar fluxo de múltiplos pagamentos
4. Atualizar seed
