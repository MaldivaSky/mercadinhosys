# 📧 Sistema de Envio de Nota Fiscal por Email

## ✅ Implementado e Funcionando

Sistema completo de envio de cupom fiscal por email usando Gmail SMTP.

---

## 🔐 Configuração Segura

### 1. Senha de App do Gmail

**⚠️ SUAS CREDENCIAIS ESTÃO PROTEGIDAS**

Suas credenciais reais estão apenas em:
- `backend/.env` (protegido pelo `.gitignore` - NÃO vai para GitHub)

**Para configurar:**
1. Gere senha de app em: https://myaccount.google.com/apppasswords
2. Adicione em `backend/.env`

**⚠️ IMPORTANTE:** Nunca exponha suas credenciais em documentação pública.

### 2. Arquivo `.env` Local (NÃO commitado)

```env
# backend/.env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=seu-email@gmail.com
MAIL_PASSWORD=sua-senha-de-app-16-caracteres
MAIL_DEFAULT_SENDER=seu-email@gmail.com
```

### 3. Produção (Render.com)

Configure as variáveis de ambiente no Render Dashboard:

```
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=seu-email@gmail.com
MAIL_PASSWORD=sua-senha-de-app-16-caracteres
MAIL_DEFAULT_SENDER=seu-email@gmail.com
```

---

## 🚀 Como Usar

### Opção 1: Enviar Automaticamente na Finalização

**Frontend (PDVPage.tsx):**

```typescript
const finalizarVenda = async () => {
  const payload = {
    items: carrinho,
    cliente_id: clienteSelecionado?.id,
    subtotal: subtotal,
    desconto: descontoTotal,
    total: total,
    paymentMethod: formaPagamento,
    valor_recebido: valorRecebido,
    troco: troco,
    enviar_email: true  // ← Adicione esta flag
  };
  
  const response = await api.post('/pdv/finalizar', payload);
  
  if (response.data.email_enviado) {
    toast.success(`Email enviado para ${response.data.email_destinatario}`);
  }
};
```

### Opção 2: Reenviar Cupom Posteriormente

**Endpoint:** `POST /api/pdv/enviar-cupom/<venda_id>`

```bash
curl -X POST http://localhost:5000/api/pdv/enviar-cupom/123 \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"email": "cliente@email.com"}'
```

**Resposta:**
```json
{
  "success": true,
  "message": "Cupom fiscal enviado para cliente@email.com",
  "email": "cliente@email.com"
}
```

---

## 📋 Funcionalidades

### 1. Envio Automático
- ✅ Envia cupom automaticamente ao finalizar venda
- ✅ Apenas se `enviar_email: true` no payload
- ✅ Apenas se cliente tiver email cadastrado
- ✅ Não bloqueia a venda se email falhar

### 2. Reenvio Manual
- ✅ Endpoint dedicado para reenviar cupom
- ✅ Pode especificar email diferente
- ✅ Busca dados da venda automaticamente
- ✅ Formata cupom com todos os detalhes

### 3. Template HTML Profissional
- ✅ Design de cupom fiscal realista
- ✅ Fonte monoespaçada (Courier New)
- ✅ Borda tracejada
- ✅ Informações completas da venda
- ✅ Responsivo para mobile
- ✅ Destaque para valores importantes

---

## 📧 Exemplo de Email Enviado

**Assunto:** Cupom Fiscal - V-20260121-1234

**Conteúdo:**

```
╔════════════════════════════════════════╗
║         🛒 MERCADINHO SYS              ║
║    CNPJ: 00.000.000/0001-00            ║
║    Av. Principal, 123 - Centro         ║
║    Tel: (00) 0000-0000                 ║
╚════════════════════════════════════════╝

CUPOM FISCAL NÃO FISCAL

Código: V-20260121-1234
Data/Hora: 21/01/2026 14:30:45
Operador: João Silva
Cliente: Maria Santos

────────────────────────────────────────
PRODUTOS:

Arroz Tipo 1 5kg
  2 x R$ 22.90 = R$ 45.80

Feijão Preto 1kg
  1 x R$ 8.90 = R$ 8.90

────────────────────────────────────────

Subtotal:           R$ 54.70
Desconto:          - R$ 4.70
TOTAL:              R$ 50.00

Forma Pagamento:    Dinheiro
Valor Recebido:     R$ 50.00
Troco:              R$ 0.00

────────────────────────────────────────
Obrigado pela preferência!

Este é um documento não fiscal.
Válido apenas para controle interno.

Email enviado automaticamente pelo sistema MercadinhoSys
```

---

## 🔧 Configuração do Gmail

### Passo 1: Habilitar Verificação em 2 Etapas

1. Acesse: https://myaccount.google.com/security
2. Ative "Verificação em duas etapas"

### Passo 2: Gerar Senha de App

1. Acesse: https://myaccount.google.com/apppasswords
2. Selecione "Email" e "Outro (nome personalizado)"
3. Digite: "MercadinhoSys"
4. Clique em "Gerar"
5. Copie a senha de 16 caracteres

### Passo 3: Configurar no Sistema

**Local:**
- Edite `backend/.env`
- Adicione `MAIL_USERNAME` e `MAIL_PASSWORD`

**Produção:**
- Render Dashboard → Backend → Environment
- Adicione as variáveis de email

---

## 🧪 Testar Localmente

### 1. Configurar `.env`

```bash
cd backend
# Edite .env com suas credenciais
```

### 2. Iniciar Backend

```bash
venv\Scripts\activate  # Windows
python run.py
```

### 3. Testar Envio

```bash
# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Copie o access_token

# Finalizar venda com email
curl -X POST http://localhost:5000/api/pdv/finalizar \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [{"id": 1, "quantity": 2, "discount": 0}],
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

### 4. Verificar Logs

```bash
# Logs do backend
tail -f backend/logs/app.log

# Procure por:
# ✅ Cupom enviado para cliente@email.com - Venda V-20260121-1234
```

---

## 🐛 Troubleshooting

### Erro: "Authentication failed"

**Causa:** Senha de app incorreta ou não configurada

**Solução:**
1. Verifique se a senha tem 16 caracteres (sem espaços)
2. Gere nova senha de app no Gmail
3. Atualize `MAIL_PASSWORD` no `.env`

### Erro: "SMTP connection failed"

**Causa:** Firewall bloqueando porta 587

**Solução:**
1. Verifique firewall/antivírus
2. Teste com `telnet smtp.gmail.com 587`
3. Use porta 465 com SSL se necessário

### Email não chega

**Causa:** Email na caixa de spam ou email inválido

**Solução:**
1. Verifique pasta de spam
2. Adicione remetente aos contatos
3. Verifique se email do cliente está correto

### Erro: "MAIL_USERNAME not configured"

**Causa:** Variáveis de ambiente não carregadas

**Solução:**
1. Verifique se `.env` existe em `backend/`
2. Reinicie o servidor Flask
3. Verifique logs de inicialização

---

## 📊 Logs e Monitoramento

### Logs de Sucesso

```
INFO:app:📧 Email enviado para cliente@email.com - Venda V-20260121-1234
INFO:app:✅ Cupom enviado para cliente@email.com - Venda V-20260121-1234
```

### Logs de Erro

```
ERROR:app:❌ Erro ao enviar cupom: Authentication failed
WARNING:app:⚠️ Falha ao enviar email para cliente@email.com
```

### Verificar Status

```bash
# Ver últimos logs
tail -n 50 backend/logs/app.log | grep -i email

# Ver apenas erros de email
tail -n 100 backend/logs/app.log | grep -i "erro.*email"
```

---

## 🔒 Segurança

### ✅ Implementado

- [x] Senha de app (não senha real do Gmail)
- [x] `.env` no `.gitignore` (não vai para GitHub)
- [x] TLS/SSL para conexão SMTP
- [x] Validação de email antes de enviar
- [x] Logs sem expor senha
- [x] Tratamento de erros sem expor credenciais

### ⚠️ Boas Práticas

1. **Nunca commite `.env`** - Já protegido pelo `.gitignore`
2. **Use senha de app** - Não use senha real do Gmail
3. **Rotacione senhas** - Gere nova senha de app periodicamente
4. **Monitore logs** - Verifique tentativas de envio
5. **Limite de envios** - Gmail tem limite de 500 emails/dia

---

## 💰 Custos

**Gmail Gratuito:**
- ✅ 500 emails/dia
- ✅ Sem custo adicional
- ✅ Suficiente para pequenos mercados

**Se precisar mais:**
- Google Workspace: $6/usuário/mês (2000 emails/dia)
- SendGrid: $15/mês (40.000 emails/mês)
- AWS SES: $0.10/1000 emails

---

## 🎯 Próximos Passos

### Melhorias Futuras

1. [ ] Adicionar logo do estabelecimento no email
2. [ ] QR Code para validação do cupom
3. [ ] Anexar PDF do cupom
4. [ ] Histórico de emails enviados
5. [ ] Retry automático em caso de falha
6. [ ] Template personalizável por estabelecimento
7. [ ] Envio de relatórios por email
8. [ ] Notificações de estoque baixo

---

## 📚 Referências

- **Flask-Mail:** https://pythonhosted.org/Flask-Mail/
- **Gmail SMTP:** https://support.google.com/mail/answer/7126229
- **Senhas de App:** https://myaccount.google.com/apppasswords

---

**✅ Sistema de Email Implementado e Funcionando!**

Configuração segura, template profissional, e pronto para uso em produção.

Data: 21 de Janeiro de 2026 | Versão: 2.0.0
