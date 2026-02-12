# 🔧 APLICAR CORREÇÕES PRIORITÁRIAS

## Checklist de Correções

### ✅ 1. Logger do Dashboard - CORRIGIDO
- [x] Logger local criado em cada método
- [x] Removido uso de `current_app` sem import
- [x] Testado e funcionando

### 🔴 2. Criar Índices no Banco - EXECUTAR AGORA
```bash
cd backend
python otimizar_dashboard.py
```

### 🔴 3. Cache do Dashboard - JÁ CONFIGURADO
- TTL aumentado para 300s (5 minutos)
- Cache inteligente com validação de DB

### ⚠️ 4. Validação de Limite de Crédito - PENDENTE
**Arquivo:** `backend/app/routes/pdv.py`
**Linha:** ~490 (após validar cliente_id)

**Adicionar:**
```python
# Validar limite de crédito se cliente informado
if cliente_id:
    cliente = Cliente.query.get(cliente_id)
    if cliente and cliente.limite_credito:
        credito_disponivel = float(cliente.limite_credito) - float(cliente.saldo_devedor or 0)
        if total_venda > credito_disponivel:
            return jsonify({
                "error": f"Limite de crédito excedido. Disponível: R$ {credito_disponivel:.2f}",
                "tipo": "limite_credito_excedido"
            }), 400
```

### ⚠️ 5. Cliente Obrigatório - PENDENTE
**Arquivo:** `backend/app/routes/pdv.py`
**Linha:** ~485

**Substituir:**
```python
# ANTES:
if not cliente_id:
    current_app.logger.warning("⚠️ Venda sem cliente")

# DEPOIS:
if not cliente_id:
    # Criar ou buscar cliente "Consumidor Final"
    cliente_padrao = Cliente.query.filter_by(
        estabelecimento_id=estabelecimento_id,
        nome="Consumidor Final",
        cpf="00000000000"
    ).first()
    
    if not cliente_padrao:
        cliente_padrao = Cliente(
            estabelecimento_id=estabelecimento_id,
            nome="Consumidor Final",
            cpf="00000000000",
            email="consumidor@padrao.com",
            celular="00000000000",
            limite_credito=0,
            ativo=True
        )
        db.session.add(cliente_padrao)
        db.session.flush()
    
    cliente_id = cliente_padrao.id
```

---

## 🚀 Executar Correções

1. **Criar índices:**
   ```bash
   cd backend
   python otimizar_dashboard.py
   ```

2. **Testar dashboard:**
   - Acessar `/api/dashboard/cientifico?days=30`
   - Verificar tempo de resposta (<2s após cache)

3. **Aplicar validações de crédito** (código acima)

4. **Aplicar cliente obrigatório** (código acima)

---

## ✅ Status das Correções

- [x] Logger corrigido
- [ ] Índices criados (executar script)
- [x] Cache otimizado
- [ ] Validação de crédito (código pronto)
- [ ] Cliente obrigatório (código pronto)
