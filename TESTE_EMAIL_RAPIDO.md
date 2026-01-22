# 🧪 Teste Rápido - Email de Nota Fiscal

## ⚡ Setup em 3 Passos

### 1. Configure o Email

Edite `backend/.env`:

```env
MAIL_USERNAME=seu-email@gmail.com
MAIL_PASSWORD=sua-senha-de-app-16-caracteres
MAIL_DEFAULT_SENDER=seu-email@gmail.com
```

### 2. Reinicie o Backend

```bash
cd backend
venv\Scripts\activate
python run.py
```

### 3. Teste o Envio

**Opção A: Via Frontend**

1. Acesse o PDV: http://localhost:5173
2. Login: `admin` / `admin123`
3. Adicione produtos ao carrinho
4. Selecione um cliente com email
5. Finalize a venda
6. ✅ Email será enviado automaticamente!

**Opção B: Via API (cURL)**

```bash
# 1. Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Copie o access_token da resposta

# 2. Finalizar venda com email
curl -X POST http://localhost:5000/api/pdv/finalizar \
  -H "Authorization: Bearer SEU_TOKEN_AQUI" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"id": 1, "quantity": 2, "discount": 0}
    ],
    "cliente_id": 1,
    "subtotal": 45.80,
    "desconto": 0,
    "total": 45.80,
    "paymentMethod": "dinheiro",
    "valor_recebido": 50,
    "troco": 4.20,
    "enviar_email": true
  }'
```

**Opção C: Reenviar Cupom Existente**

```bash
# Reenviar cupom da venda ID 1
curl -X POST http://localhost:5000/api/pdv/enviar-cupom/1 \
  -H "Authorization: Bearer SEU_TOKEN_AQUI" \
  -H "Content-Type: application/json" \
  -d '{"email": "cliente@email.com"}'
```

---

## ✅ Verificar se Funcionou

### 1. Logs do Backend

```bash
# Ver logs em tempo real
tail -f backend/logs/app.log

# Procure por:
# ✅ Cupom enviado para cliente@email.com - Venda V-20260121-1234
```

### 2. Resposta da API

```json
{
  "success": true,
  "message": "Venda finalizada com sucesso!",
  "email_enviado": true,
  "email_destinatario": "cliente@email.com",
  "venda": {
    "codigo": "V-20260121-1234",
    "total": 45.80
  }
}
```

### 3. Caixa de Email

- Verifique a caixa de entrada do cliente
- Se não aparecer, verifique **Spam**
- Assunto: "Cupom Fiscal - V-20260121-1234"

---

## 🐛 Problemas Comuns

### Email não enviado

**Erro nos logs:**
```
ERROR:app:❌ Erro ao enviar cupom: Authentication failed
```

**Solução:**
1. Verifique se a senha de app está correta
2. Remova espaços da senha: `ribpqcbfxhqrsgvz`
3. Gere nova senha de app: https://myaccount.google.com/apppasswords

### Cliente sem email

**Erro:**
```json
{
  "error": "Cliente não possui email cadastrado"
}
```

**Solução:**
1. Cadastre email do cliente
2. Ou informe email manualmente no reenvio

### Firewall bloqueando

**Erro:**
```
ERROR:app:❌ Erro ao enviar cupom: Connection refused
```

**Solução:**
1. Desabilite firewall temporariamente
2. Libere porta 587 (SMTP)
3. Teste: `telnet smtp.gmail.com 587`

---

## 📧 Exemplo de Email Recebido

![Cupom Fiscal](https://via.placeholder.com/400x600/ffffff/000000?text=Cupom+Fiscal)

```
╔════════════════════════════════════════╗
║         🛒 MERCADINHO SYS              ║
╚════════════════════════════════════════╝

CUPOM FISCAL NÃO FISCAL

Código: V-20260121-1234
Data/Hora: 21/01/2026 14:30:45
Operador: Admin Sistema
Cliente: Maria Santos

────────────────────────────────────────
PRODUTOS:

Arroz Tipo 1 5kg
  2 x R$ 22.90 = R$ 45.80

────────────────────────────────────────

Subtotal:           R$ 45.80
TOTAL:              R$ 45.80

Forma Pagamento:    Dinheiro
Valor Recebido:     R$ 50.00
Troco:              R$ 4.20

────────────────────────────────────────
Obrigado pela preferência!
```

---

## 🎯 Checklist de Teste

- [ ] Configurei `MAIL_USERNAME` no `.env`
- [ ] Configurei `MAIL_PASSWORD` no `.env`
- [ ] Reiniciei o backend
- [ ] Fiz login no sistema
- [ ] Selecionei cliente com email
- [ ] Finalizei venda com `enviar_email: true`
- [ ] Verifiquei logs do backend
- [ ] Recebi email na caixa de entrada
- [ ] Email está formatado corretamente
- [ ] Testei reenvio de cupom

---

## 💡 Dicas

1. **Use email de teste primeiro** - Teste com seu próprio email antes de enviar para clientes
2. **Verifique spam** - Primeiros emails podem cair no spam
3. **Adicione aos contatos** - Peça para clientes adicionarem seu email aos contatos
4. **Monitore logs** - Sempre verifique logs para debug
5. **Limite diário** - Gmail gratuito tem limite de 500 emails/dia

---

**✅ Pronto para testar!**

Qualquer dúvida, consulte `EMAIL_NOTA_FISCAL.md` para documentação completa.
