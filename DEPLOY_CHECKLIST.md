# ✅ Checklist de Deploy - MercadinhoSys

## 📋 Pré-Deploy

### Backend
- [ ] `backend/requirements.txt` atualizado com todas as dependências
- [ ] `backend/config.py` configurado para detectar ambiente automaticamente
- [ ] `backend/seed_cloud.py` testado localmente
- [ ] Health check endpoint `/api/auth/health` funcionando
- [ ] CORS configurado para aceitar domínio do frontend
- [ ] Variáveis de ambiente documentadas em `.env.example`

### Frontend
- [ ] `VITE_API_URL` configurada em `.env.production`
- [ ] Build local testado: `npm run build`
- [ ] API client configurado para detectar ambiente
- [ ] Rotas SPA configuradas no Nginx/Render

### Database
- [ ] Credenciais Neon PostgreSQL validadas
- [ ] Conexão SSL habilitada (`?sslmode=require`)
- [ ] Modelos SQLAlchemy compatíveis com PostgreSQL
- [ ] Migrations testadas (se aplicável)

---

## 🚀 Deploy no Render.com

### Opção 1: Blueprint (Automático) ⭐ RECOMENDADO

1. **Commit e Push**
   ```bash
   git add .
   git commit -m "feat: production deployment ready"
   git push origin main
   ```

2. **Criar Blueprint no Render**
   - Acesse: https://dashboard.render.com
   - Clique: **New +** → **Blueprint**
   - Conecte seu repositório Git
   - Render detecta `render.yaml` automaticamente
   - Clique: **Apply**

3. **Configurar DATABASE_URL**
   - Vá em: **mercadinhosys-backend** → **Environment**
   - Adicione suas credenciais Neon:
     ```
     DATABASE_URL=postgresql://[user]:[password]@[host]/neondb?sslmode=require
     ```
     (Obtenha em: https://console.neon.tech)
   - Salve e aguarde redeploy automático

4. **Atualizar CORS no Backend**
   - Após deploy do frontend, copie a URL (ex: `https://mercadinhosys-frontend.onrender.com`)
   - Vá em: **mercadinhosys-backend** → **Environment**
   - Atualize `CORS_ORIGINS` com a URL real do frontend
   - Salve e aguarde redeploy

5. **Atualizar VITE_API_URL no Frontend**
   - Após deploy do backend, copie a URL (ex: `https://mercadinhosys-backend.onrender.com`)
   - Vá em: **mercadinhosys-frontend** → **Environment**
   - Atualize `VITE_API_URL` para: `https://mercadinhosys-backend.onrender.com/api`
   - Clique: **Manual Deploy** → **Clear build cache & deploy**

### Opção 2: Manual

Ver `DEPLOY_RENDER.md` para instruções detalhadas.

---

## 🧪 Testes Pós-Deploy

### 1. Backend Health Check
```bash
curl https://mercadinhosys-backend.onrender.com/api/auth/health
```

**Resposta esperada:**
```json
{
  "status": "healthy",
  "database": "connected",
  "environment": "production",
  "timestamp": "2026-01-21T...",
  "version": "2.0.0"
}
```

### 2. Teste de Login
```bash
curl -X POST https://mercadinhosys-backend.onrender.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

**Resposta esperada:**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJ...",
    "user": { ... }
  }
}
```

### 3. Frontend
- Acesse: `https://mercadinhosys-frontend.onrender.com`
- Faça login com: `admin` / `admin123`
- Verifique se Dashboard carrega dados
- Teste PDV, Produtos, Fornecedores

### 4. Logs
```bash
# Backend
render logs -s mercadinhosys-backend -f

# Frontend
render logs -s mercadinhosys-frontend -f
```

---

## 🐛 Troubleshooting

### ❌ Backend não inicia

**Sintomas:**
- "Application failed to respond"
- Health check falha

**Soluções:**
1. Verificar logs: `render logs -s mercadinhosys-backend`
2. Confirmar `DATABASE_URL` está configurada
3. Verificar se `gunicorn` está em `requirements.txt`
4. Testar conexão Neon diretamente (use suas credenciais do console.neon.tech)

### ❌ CORS Error

**Sintomas:**
- Console do navegador: "CORS policy: No 'Access-Control-Allow-Origin'"

**Soluções:**
1. Verificar `CORS_ORIGINS` no backend tem URL correta do frontend
2. URL deve ser EXATA (sem barra final): `https://mercadinhosys-frontend.onrender.com`
3. Redeploy do backend após alterar

### ❌ Frontend não carrega dados

**Sintomas:**
- Tela branca ou erro 404 nas chamadas API
- Console: "Failed to fetch"

**Soluções:**
1. Verificar `VITE_API_URL` no frontend
2. Deve incluir `/api`: `https://mercadinhosys-backend.onrender.com/api`
3. Rebuild do frontend: **Clear build cache & deploy**
4. Verificar console do navegador para URL exata sendo chamada

### ❌ Database connection failed

**Sintomas:**
- Health check retorna `"database": "disconnected"`
- Logs: "could not connect to server"

**Soluções:**
1. Verificar `DATABASE_URL` tem `?sslmode=require` no final
2. Testar credenciais Neon diretamente
3. Verificar se Neon não está em sleep (plano free dorme após 5min)
4. Acessar Neon Console e acordar o database

### ❌ Seed não executou

**Sintomas:**
- Login falha com "Credenciais inválidas"
- Banco vazio

**Soluções:**
1. Executar seed manualmente via Render Shell:
   ```bash
   # No Render Dashboard: mercadinhosys-backend → Shell
   python seed_cloud.py
   ```
2. Verificar logs do primeiro deploy (seed roda automaticamente)

---

## 📊 Monitoramento

### Métricas no Render Dashboard

**Backend:**
- CPU Usage (deve ficar < 50%)
- Memory Usage (deve ficar < 512MB)
- Response Time (deve ficar < 500ms)
- Error Rate (deve ficar < 1%)

**Frontend:**
- Build Time (deve ficar < 3min)
- Deploy Time (deve ficar < 1min)

### Alertas Recomendados

1. **Health Check Failure**
   - Configurar em: Render Dashboard → Service → Settings → Health Check
   - Notificar via email/Slack

2. **High Error Rate**
   - Integrar Sentry para tracking de erros
   - Configurar alertas para > 5% error rate

3. **Database Sleep (Neon Free)**
   - Neon dorme após 5min de inatividade
   - Considerar upgrade para Pro ($19/mês) em produção

---

## 🔄 Atualizações Futuras

### Deploy Automático (CI/CD)

Já configurado em `.github/workflows/ci-cd.yml`:
- Push para `main` → Deploy automático
- Testes rodam antes do deploy
- Build Docker e push para Docker Hub
- Security scan com Trivy

### Rollback

Se algo der errado:
1. Render Dashboard → Service → **Deploys**
2. Encontre o deploy anterior que funcionava
3. Clique: **Rollback to this version**

### Domínio Customizado

1. Render Dashboard → Service → **Settings** → **Custom Domain**
2. Adicione: `app.mercadinhosys.com.br`
3. Configure DNS:
   ```
   CNAME app mercadinhosys-frontend.onrender.com
   ```
4. SSL automático via Let's Encrypt

---

## 💰 Custos Estimados

### Plano Atual (Free)
- Backend: $0/mês (750h incluídas)
- Frontend: $0/mês (ilimitado)
- Neon DB: $0/mês (0.5GB)
- **Total: $0/mês**

**Limitações:**
- ⚠️ Cold starts (~30s)
- ⚠️ Sleep após 15min inatividade
- ⚠️ Database sleep após 5min

### Produção Recomendada
- Backend Starter: $7/mês
- Frontend: $0/mês
- Neon Pro: $19/mês
- **Total: $26/mês**

**Benefícios:**
- ✅ Sem cold starts
- ✅ Sempre ativo
- ✅ Backups automáticos
- ✅ 10GB storage

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

**MercadinhoSys:**
- Issues: GitHub Issues
- Docs: `README.md`, `DEPLOY_RENDER.md`

---

## ✅ Checklist Final

- [ ] Backend deployado e health check OK
- [ ] Frontend deployado e acessível
- [ ] Login funcionando
- [ ] Dashboard carregando dados
- [ ] PDV funcionando
- [ ] Produtos listando
- [ ] Fornecedores listando
- [ ] Logs sem erros críticos
- [ ] CORS configurado corretamente
- [ ] Seed executado com sucesso
- [ ] Credenciais de teste funcionando
- [ ] Monitoramento configurado
- [ ] Backups configurados (Neon)
- [ ] Domínio customizado (opcional)
- [ ] SSL ativo (automático)

---

**🎉 Deploy Completo! Sistema em produção!**

Próximos passos:
1. Testar todas as funcionalidades
2. Configurar monitoramento (Sentry, LogRocket)
3. Configurar backups automáticos
4. Documentar para equipe
5. Treinar usuários
