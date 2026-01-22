# 🔍 Troubleshooting - Login não funciona no celular

## ✅ Status Atual (TUDO FUNCIONANDO):

- ✅ Backend Render: https://mercadinhosys.onrender.com - **ONLINE**
- ✅ Frontend Vercel: https://mercadinhosys.vercel.app - **ONLINE**
- ✅ Banco Neon PostgreSQL - **CONECTADO**
- ✅ Usuário admin existe (id=14)
- ✅ Variável VITE_API_URL configurada no Vercel
- ✅ Login funciona via API direta (testado com curl)

## 🔍 Diagnóstico por Tipo de Erro:

### 1. Erro: "Network Error" ou "Failed to fetch"

**Causa:** Frontend não consegue conectar ao backend

**Soluções:**
1. Verifique se o backend está acordado (Render free tier dorme):
   - Acesse: https://mercadinhosys.onrender.com/api/auth/health
   - Aguarde 30-60 segundos se estiver dormindo
   
2. Verifique CORS no backend:
   - O domínio do Vercel deve estar em CORS_ORIGINS
   - Adicione no Render: `https://mercadinhosys.vercel.app`

### 2. Erro: "Invalid Credentials"

**Causa:** Credenciais incorretas ou banco vazio

**Soluções:**
1. Confirme as credenciais:
   - Usuário: `admin`
   - Senha: `admin123`
   
2. Verifique se o banco tem dados:
   - Execute: `python backend/seed_neon_rapido.py`

### 3. Erro: Tela branca ou não carrega

**Causa:** Build do Vercel com problema

**Soluções:**
1. Limpe o cache e faça redeploy:
   - Vercel Dashboard → Deployments
   - Redeploy sem cache
   
2. Verifique erros no console do navegador (F12)

### 4. Erro: "CORS Error"

**Causa:** Backend bloqueando requisições do Vercel

**Solução:**
Adicione no Render (Environment Variables):
```
CORS_ORIGINS=https://mercadinhosys.vercel.app,https://mercadinhosys-frontend.vercel.app
```

## 🧪 Testes para Fazer:

### Teste 1: Backend está respondendo?
```bash
curl https://mercadinhosys.onrender.com/api/auth/health
```
Deve retornar: `{"status": "healthy"}`

### Teste 2: Login funciona via API?
```bash
curl -X POST https://mercadinhosys.onrender.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","senha":"admin123"}'
```
Deve retornar: `{"success": true, "data": {...}}`

### Teste 3: Frontend está usando a URL correta?
1. Abra: https://mercadinhosys.vercel.app
2. Abra Console (F12)
3. Procure por: `🔧 API Config`
4. Deve mostrar: `BASE_URL: "https://mercadinhosys.onrender.com/api"`

### Teste 4: Requisição de login está sendo enviada?
1. Abra: https://mercadinhosys.vercel.app
2. Abra Network tab (F12)
3. Tente fazer login
4. Veja se aparece requisição para `/api/auth/login`
5. Clique na requisição e veja:
   - Request URL: deve ser `https://mercadinhosys.onrender.com/api/auth/login`
   - Status: deve ser 200
   - Response: deve ter `success: true`

## 🔧 Soluções Rápidas:

### Solução 1: Acordar o backend
```bash
# Acesse esta URL no navegador:
https://mercadinhosys.onrender.com/api/auth/health

# Aguarde 30-60 segundos
# Tente fazer login novamente
```

### Solução 2: Adicionar domínio ao CORS
No Render Dashboard → Environment:
```
CORS_ORIGINS=https://mercadinhosys.vercel.app,http://localhost:5173
```

### Solução 3: Redeploy completo
```bash
# No terminal local:
git commit --allow-empty -m "chore: force redeploy"
git push

# Aguarde deploy do Vercel (2-3 min)
# Aguarde deploy do Render (2-3 min)
```

## 📱 Teste no Celular:

1. **Limpe o cache do navegador do celular**
2. **Feche e abra o navegador novamente**
3. **Acesse:** https://mercadinhosys.vercel.app
4. **Aguarde 30 segundos** (backend pode estar dormindo)
5. **Tente fazer login:** admin / admin123

## 🆘 Se nada funcionar:

1. Me envie print do erro que aparece no celular
2. Me envie os logs do Render (últimas 20 linhas)
3. Me envie print do Console do navegador (F12)
4. Me diga qual navegador está usando no celular

## 📞 Credenciais de Teste:

- **Admin:**
  - Usuário: `admin`
  - Senha: `admin123`
  - Role: ADMIN

- **Vendedor:**
  - Usuário: `joao`
  - Senha: `joao123`
  - Role: FUNCIONARIO

## 🔗 URLs Importantes:

- Frontend: https://mercadinhosys.vercel.app
- Backend: https://mercadinhosys.onrender.com
- Health Check: https://mercadinhosys.onrender.com/api/auth/health
- Vercel Dashboard: https://vercel.com/dashboard
- Render Dashboard: https://dashboard.render.com
