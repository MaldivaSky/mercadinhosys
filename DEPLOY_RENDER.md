# 🚀 Deploy no Render.com - Guia Completo

## 📋 Pré-requisitos

- Conta no [Render.com](https://render.com) (gratuita)
- Repositório Git (GitHub, GitLab ou Bitbucket)
- Credenciais do Neon PostgreSQL (já configuradas)

## 🎯 Opção 1: Deploy Automático com Blueprint (RECOMENDADO)

### Passo 1: Preparar o Repositório

```bash
# Commit e push do código
git add .
git commit -m "feat: add Render deployment configuration"
git push origin main
```

### Passo 2: Deploy via Blueprint

1. Acesse [Render Dashboard](https://dashboard.render.com)
2. Clique em **"New +"** → **"Blueprint"**
3. Conecte seu repositório Git
4. Render detectará automaticamente o `render.yaml`
5. Clique em **"Apply"**

✅ **Pronto!** Render criará automaticamente:
- Backend (Web Service)
- Frontend (Static Site)
- PostgreSQL Database

### Passo 3: Configurar Variáveis de Ambiente

Render auto-gerará `SECRET_KEY` e `JWT_SECRET_KEY`, mas você precisa configurar:

**Backend Service:**
- `DATABASE_URL`: Use suas credenciais Neon PostgreSQL (veja console.neon.tech)
  ```
  postgresql://[user]:[password]@[host]/neondb?sslmode=require
  ```
- `CORS_ORIGINS`: URL do frontend (ex: `https://mercadinhosys-frontend.onrender.com`)

**Frontend Service:**
- `VITE_API_URL`: URL do backend (ex: `https://mercadinhosys-backend.onrender.com`)

---

## 🎯 Opção 2: Deploy Manual

### Backend

1. **New Web Service**
   - Name: `mercadinhosys-backend`
   - Runtime: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn run:app --bind 0.0.0.0:$PORT --workers 2`
   - Root Directory: `backend`

2. **Environment Variables**
   ```
   FLASK_ENV=production
   DATABASE_URL=postgresql://[user]:[password]@[host]/neondb?sslmode=require
   SECRET_KEY=[Generate Value]
   JWT_SECRET_KEY=[Generate Value]
   CORS_ORIGINS=https://mercadinhosys-frontend.onrender.com
   ```
   
   **⚠️ DATABASE_URL:** Obtenha suas credenciais em https://console.neon.tech

3. **Health Check**
   - Path: `/api/auth/health`

### Frontend

1. **New Static Site**
   - Name: `mercadinhosys-frontend`
   - Build Command: `npm install && npm run build`
   - Publish Directory: `dist`
   - Root Directory: `frontend/mercadinhosys-frontend`

2. **Environment Variables**
   ```
   VITE_API_URL=https://mercadinhosys-backend.onrender.com/api
   ```

3. **Rewrite Rules** (para SPA)
   - Source: `/*`
   - Destination: `/index.html`

---

## 🗄️ Usando Neon PostgreSQL

**⚠️ IMPORTANTE: Suas credenciais reais estão protegidas em `backend/.env` (não vai para GitHub)**

### Como Obter Suas Credenciais

1. Acesse: https://console.neon.tech
2. Selecione seu projeto
3. Vá em "Connection Details"
4. Copie a "Connection string"

**Formato:**
```
postgresql://[user]:[password]@[host]/neondb?sslmode=require
```

### Seed Automático

O script `seed_cloud.py` roda automaticamente no primeiro deploy:
- Detecta ambiente Neon/Render
- Cria tabelas
- Popula dados iniciais (estabelecimento, admin, produtos)

**Credenciais de acesso:**
- Username: `admin`
- Password: `admin123`

---

## 🔍 Verificação Pós-Deploy

### 1. Backend Health Check

```bash
curl https://mercadinhosys-backend.onrender.com/api/auth/health
```

Resposta esperada:
```json
{
  "status": "healthy",
  "database": "connected",
  "environment": "production"
}
```

### 2. Teste de Login

```bash
curl -X POST https://mercadinhosys-backend.onrender.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

### 3. Frontend

Acesse: `https://mercadinhosys-frontend.onrender.com`

---

## 🐛 Troubleshooting

### Erro: "Application failed to respond"

**Causa:** Backend não iniciou corretamente

**Solução:**
1. Verifique logs no Render Dashboard
2. Confirme que `DATABASE_URL` está configurada
3. Verifique se `gunicorn` está em `requirements.txt`

### Erro: "CORS policy"

**Causa:** Frontend não autorizado no backend

**Solução:**
1. Adicione URL do frontend em `CORS_ORIGINS`
2. Formato: `https://seu-frontend.onrender.com` (sem barra final)
3. Redeploy do backend

### Erro: "Database connection failed"

**Causa:** Credenciais Neon incorretas ou SSL não configurado

**Solução:**
1. Verifique `DATABASE_URL` tem `?sslmode=require` no final
2. Teste conexão direta com Neon (use suas credenciais do console.neon.tech)
3. Verifique se Neon não está em sleep (plano free dorme após 5min)
4. Acesse Neon Console e acorde o database

### Frontend não carrega dados

**Causa:** `VITE_API_URL` incorreta ou não configurada

**Solução:**
1. Verifique variável de ambiente no frontend
2. Rebuild do frontend após alterar variáveis
3. Verifique console do navegador para erros de rede

---

## 📊 Monitoramento

### Logs em Tempo Real

**Backend:**
```bash
# Via Render CLI
render logs -s mercadinhosys-backend -f
```

**Frontend:**
```bash
render logs -s mercadinhosys-frontend -f
```

### Métricas

Render Dashboard mostra automaticamente:
- CPU Usage
- Memory Usage
- Request Count
- Response Time
- Error Rate

---

## 🔄 Atualizações

### Deploy Automático

Render faz deploy automático a cada push para `main`:

```bash
git add .
git commit -m "feat: nova funcionalidade"
git push origin main
```

### Deploy Manual

No Render Dashboard:
1. Selecione o serviço
2. Clique em **"Manual Deploy"**
3. Escolha a branch
4. Clique em **"Deploy"**

---

## 💰 Custos

### Plano Free (Atual)

**Incluído:**
- ✅ 750 horas/mês de Web Service
- ✅ 100 GB bandwidth/mês
- ✅ Static Sites ilimitados
- ⚠️ Serviços dormem após 15min de inatividade
- ⚠️ Cold start de ~30s

**Neon PostgreSQL Free:**
- ✅ 0.5 GB storage
- ✅ 1 projeto
- ⚠️ Dorme após 5min de inatividade

### Upgrade Recomendado (Produção)

**Render Starter ($7/mês por serviço):**
- ✅ Sem cold starts
- ✅ Sempre ativo
- ✅ 400 horas/mês

**Neon Pro ($19/mês):**
- ✅ 10 GB storage
- ✅ Sem sleep
- ✅ Backups automáticos

---

## 🎯 Próximos Passos

1. ✅ Deploy no Render
2. ✅ Configurar domínio customizado (opcional)
3. ✅ Configurar SSL (automático no Render)
4. ✅ Configurar backups do Neon
5. ✅ Configurar monitoramento (Sentry, LogRocket)
6. ✅ Configurar CI/CD com GitHub Actions

---

## 📞 Suporte

**Render:**
- Docs: https://render.com/docs
- Community: https://community.render.com
- Status: https://status.render.com

**Neon:**
- Docs: https://neon.tech/docs
- Discord: https://discord.gg/neon
- Status: https://neonstatus.com

---

## ✅ Checklist de Deploy

- [ ] Código commitado e pushed
- [ ] `render.yaml` configurado
- [ ] Variáveis de ambiente configuradas
- [ ] DATABASE_URL do Neon adicionada
- [ ] CORS_ORIGINS atualizado
- [ ] Health check funcionando
- [ ] Seed executado com sucesso
- [ ] Login testado
- [ ] Frontend carregando dados
- [ ] Logs sem erros críticos

---

**🎉 Parabéns! Seu MercadinhoSys está no ar!**

Acesse: `https://mercadinhosys-frontend.onrender.com`
