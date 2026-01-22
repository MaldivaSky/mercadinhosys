# 🔧 FIX: Erro de Login no Vercel

## Problema
O frontend no Vercel não consegue fazer login porque não está conectando ao backend no Render.com.

## Causa
A variável de ambiente `VITE_API_URL` não está configurada no Vercel.

## ✅ URL Correta do Backend

```
Backend: https://mercadinhosys.onrender.com
API: https://mercadinhosys.onrender.com/api
```

## Solução Rápida

### Passo 1: Configurar Variável de Ambiente no Vercel

1. Acesse: https://vercel.com/dashboard
2. Selecione seu projeto: **mercadinhosys-frontend**
3. Vá em: **Settings** → **Environment Variables**
4. Clique em **Add New**
5. Configure:
   ```
   Name: VITE_API_URL
   Value: https://mercadinhosys.onrender.com/api
   Environment: Production ✅ (marque também Preview se quiser)
   ```
6. Clique em **Save**

### Passo 2: Redeploy

Após salvar a variável, você precisa fazer um novo deploy:

**Opção A: Via Dashboard**
1. Vá em **Deployments**
2. Clique nos 3 pontinhos do último deploy
3. Clique em **Redeploy**

**Opção B: Via Git (Recomendado)**
```bash
git add .
git commit -m "fix: configurar URL correta do backend"
git push
```

### Passo 3: Testar

Após o deploy:
1. Acesse seu site no Vercel
2. Tente fazer login com:
   - **Usuário:** admin
   - **Senha:** admin123

## Verificação

Para verificar se está funcionando, abra o Console do navegador (F12) e veja se aparece:

```
🔧 API Config: {
  BASE_URL: "https://mercadinhosys.onrender.com/api",
  ENVIRONMENT: "production"
}
```

## URLs Importantes

- **Backend (Render):** https://mercadinhosys.onrender.com
- **API Health Check:** https://mercadinhosys.onrender.com/api/auth/health

## Teste Rápido do Backend

Antes de testar o login, verifique se o backend está online:

**Abra no navegador:**
```
https://mercadinhosys.onrender.com/api/auth/health
```

Deve retornar:
```json
{
  "status": "healthy",
  "database": "connected",
  "environment": "production",
  "version": "2.0.0"
}
```

## Credenciais de Teste

- **Admin:**
  - Usuário: `admin`
  - Senha: `admin123`

- **Vendedor:**
  - Usuário: `joao`
  - Senha: `joao123`

## Troubleshooting

### Erro: "Network Error" ou "Failed to fetch"

**Causa:** Backend no Render.com pode estar dormindo (free tier)

**Solução:** 
1. Acesse diretamente: https://mercadinhosys.onrender.com/api/auth/health
2. Aguarde 30-60 segundos para o backend acordar
3. Tente fazer login novamente

### Erro: "CORS Error"

**Causa:** Backend não está aceitando requisições do domínio do Vercel

**Solução:** Adicionar domínio do Vercel na variável `CORS_ORIGINS` no Render.com:
```
https://seu-projeto.vercel.app
```

### Erro: "Invalid Credentials"

**Causa:** Banco de dados pode estar vazio ou senha incorreta

**Solução:** 
1. Verifique se o seed foi executado
2. Use as credenciais corretas: admin/admin123

## Observações

- O backend no Render.com (free tier) dorme após 15 minutos de inatividade
- O primeiro acesso pode demorar 30-60 segundos para acordar
- Após acordar, funciona normalmente
- O banco Neon PostgreSQL está sempre ativo

## Próximos Passos

Após configurar e fazer o redeploy:
1. ✅ Login deve funcionar
2. ✅ Dashboard deve carregar com dados
3. ✅ Todas as funcionalidades devem estar disponíveis
4. ✅ Pode testar no celular também
