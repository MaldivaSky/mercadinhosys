# 🔐 Segurança de Credenciais - MercadinhoSys

## ✅ Proteção Implementada

Todas as credenciais sensíveis estão protegidas e **NÃO vão para o GitHub**.

---

## 🛡️ Credenciais Protegidas

### 1. Email (Gmail)
- **Localização:** `backend/.env` (protegido pelo `.gitignore`)
- **Como obter:** https://myaccount.google.com/apppasswords

### 2. Neon PostgreSQL
- **Localização:** `backend/.env` (protegido pelo `.gitignore`)
- **Como obter:** https://console.neon.tech

### 3. Secrets do Flask
- **SECRET_KEY:** Gerado automaticamente em produção
- **JWT_SECRET_KEY:** Gerado automaticamente em produção
- **Localização:** `backend/.env` (local) e Render Dashboard (produção)

---

## 📁 Arquivos Protegidos pelo .gitignore

```
# Nunca vão para o GitHub:
backend/.env                    ✅ Suas credenciais reais
backend/.env.local              ✅ Backup local
backend/.env.local.example      ✅ Template com suas credenciais
.env                            ✅ Qualquer .env na raiz
*.secret                        ✅ Arquivos de segredo
credentials.json                ✅ Credenciais JSON
database.ini                    ✅ Config de banco
```

---

## 📝 Arquivos Seguros para Commitar

```
# Podem ir para o GitHub (sem credenciais reais):
.env.example                    ✅ Template genérico
backend/.env.render             ✅ Template Render.com
SEGURANCA_CREDENCIAIS.md        ✅ Este documento
```

---

## 🔧 Como Usar Localmente

### Opção 1: Usar o .env Existente (Já Configurado)

```bash
cd backend
# O arquivo .env já está configurado com suas credenciais
python run.py
```

### Opção 2: Copiar do Template

```bash
cd backend
cp .env.local.example .env
# Edite .env se necessário
python run.py
```

---

## 🚀 Como Configurar em Produção (Render.com)

### 1. Acesse Render Dashboard

https://dashboard.render.com

### 2. Configure Backend

**mercadinhosys-backend** → **Environment** → Adicione:

```
DATABASE_URL=[Suas credenciais Neon - veja console.neon.tech]
MAIL_USERNAME=seu-email@gmail.com
MAIL_PASSWORD=sua-senha-de-app
MAIL_DEFAULT_SENDER=seu-email@gmail.com
SECRET_KEY=[Generate Value]
JWT_SECRET_KEY=[Generate Value]
CORS_ORIGINS=https://seu-frontend.onrender.com
```

### 3. Configure Frontend

**mercadinhosys-frontend** → **Environment** → Adicione:

```
VITE_API_URL=https://seu-backend.onrender.com/api
```

---

## 🔍 Verificar Proteção

### Teste 1: Verificar .gitignore

```bash
# Ver o que será commitado
git status

# .env NÃO deve aparecer na lista
# Se aparecer, PARE e verifique .gitignore
```

### Teste 2: Verificar Histórico Git

```bash
# Procurar por credenciais no histórico
git log --all --full-history --source -- backend/.env

# Deve retornar vazio (arquivo nunca foi commitado)
```

### Teste 3: Buscar Credenciais no Código

```bash
# Procurar senha de email (não deve retornar nada em arquivos públicos)
git grep "sua-senha"

# Deve retornar apenas:
# - backend/.env (não commitado)
# - Arquivos de documentação com placeholders
```

---

## ⚠️ O Que NUNCA Fazer

### ❌ NUNCA commite .env

```bash
# ERRADO:
git add backend/.env
git commit -m "add config"

# CERTO:
# .env já está no .gitignore, não precisa fazer nada
```

### ❌ NUNCA coloque credenciais em código

```python
# ERRADO: nunca hardcode credenciais no código
# MAIL_PASS = "..."  ← NUNCA FAÇA ISSO

# CERTO: use variáveis de ambiente
MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
```

### ❌ NUNCA compartilhe .env publicamente

- Não envie por email
- Não poste em fóruns
- Não compartilhe em chat público
- Use apenas canais seguros (1-a-1)

---

## 🔄 Rotação de Credenciais

### Quando Rotacionar

- ✅ A cada 90 dias (recomendado)
- ✅ Se suspeitar de vazamento
- ✅ Ao remover membro da equipe
- ✅ Após incidente de segurança

### Como Rotacionar Gmail

1. Acesse: https://myaccount.google.com/apppasswords
2. Revogue senha antiga
3. Gere nova senha de app
4. Atualize `backend/.env` local
5. Atualize Render Dashboard
6. Teste envio de email

### Como Rotacionar Neon PostgreSQL

1. Acesse: https://console.neon.tech
2. Vá em "Settings" → "Reset Password"
3. Copie nova connection string
4. Atualize `backend/.env` local
5. Atualize Render Dashboard
6. Teste conexão

---

## 📊 Níveis de Segurança

### Desenvolvimento Local
- ✅ `.env` com credenciais reais
- ✅ Protegido pelo `.gitignore`
- ✅ Apenas na sua máquina

### Produção (Render.com)
- ✅ Environment variables no dashboard
- ✅ Criptografadas em repouso
- ✅ Transmitidas via HTTPS
- ✅ Não aparecem em logs

### Repositório Git
- ✅ Apenas templates sem credenciais
- ✅ `.env.example` com placeholders
- ✅ Documentação sem senhas reais

---

## 🚨 Em Caso de Vazamento

### Se .env foi commitado acidentalmente:

```bash
# 1. Remover do histórico (CUIDADO!)
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch backend/.env" \
  --prune-empty --tag-name-filter cat -- --all

# 2. Force push (se repositório privado)
git push origin --force --all

# 3. ROTACIONAR TODAS AS CREDENCIAIS IMEDIATAMENTE
# - Gmail: Revogar senha de app
# - Neon: Reset password
# - Render: Regenerar secrets
```

### Se credenciais foram expostas:

1. **Imediato:** Rotacionar todas as credenciais
2. **Verificar:** Logs de acesso suspeito
3. **Monitorar:** Atividade incomum
4. **Documentar:** Incidente para aprendizado

---

## ✅ Checklist de Segurança

- [x] `.env` no `.gitignore`
- [x] Credenciais apenas em variáveis de ambiente
- [x] Senha de app (não senha real do Gmail)
- [x] SSL/TLS habilitado (PostgreSQL e SMTP)
- [x] Secrets gerados automaticamente em produção
- [x] Documentação sem credenciais reais
- [x] Templates com placeholders
- [x] Verificação de proteção implementada

---

## 📚 Referências

- **OWASP Secrets Management:** https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html
- **GitHub .gitignore:** https://git-scm.com/docs/gitignore
- **Render Environment Variables:** https://render.com/docs/environment-variables
- **Gmail App Passwords:** https://support.google.com/accounts/answer/185833

---

## 🎯 Resumo

**✅ Suas credenciais estão seguras!**

- Email e senha de app protegidos
- Credenciais Neon PostgreSQL protegidas
- `.gitignore` configurado corretamente
- Documentação sem expor segredos
- Pronto para produção

**Localização das credenciais:**
- **Local:** `backend/.env` (não commitado)
- **Produção:** Render Dashboard (criptografado)
- **Backup:** `backend/.env.local.example` (não commitado)

---

**🔐 Segurança Implementada e Verificada!**

Data: 21 de Janeiro de 2026 | Versão: 2.0.0
