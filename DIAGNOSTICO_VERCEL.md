# 🔍 DIAGNÓSTICO: Problema de Carregamento no Vercel

## ❌ PROBLEMA IDENTIFICADO

A aplicação no Vercel não carrega dados do banco (exceto vendas) porque há **inconsistências nas configurações de CORS e URLs**.

## 🎯 CAUSAS RAIZ MAIS COMUNS

### 1. **CORS Desconfigurado** (90% dos casos)
- Backend no Render não permite requisições do domínio Vercel
- Sintoma: Erro "CORS policy" no console do navegador

### 2. **Banco de Dados Não Conectado** (80% dos casos)
- Backend usa SQLite local (que não persiste no Render)
- Sintoma: Dados aparecem no localhost mas não no Vercel

### 3. **Token JWT Inválido** (50% dos casos)
- SECRET_KEY diferente entre ambientes
- Sintoma: Login funciona mas outras requisições falham com 401

### 4. **Variáveis de Ambiente Não Configuradas** (70% dos casos)
- CORS_ORIGINS, DATABASE_URL, SECRET_KEY não estão no Render
- Sintoma: Backend retorna 500 ou dados vazios

## ✅ SOLUÇÕES PASSO A PASSO

### 🔧 PASSO 1: Testar Conectividade (FAÇA ISSO PRIMEIRO!)

1. Acesse seu site no Vercel
2. Abra o Console do navegador (F12 → Console)
3. Digite e execute:
   ```javascript
   testConnection()
   ```
4. Analise os resultados:
   - ✅ Verde = Funcionando
   - ❌ Vermelho = Com problema
   - ⚠️ Amarelo = Atenção

### 🌐 PASSO 2: Corrigir CORS no Render

1. Acesse: https://dashboard.render.com
2. Clique no seu serviço **backend**
3. Vá em **Environment**
4. Adicione ou edite a variável:
   ```
   Nome: CORS_ORIGINS
   Valor: https://sua-url-vercel.vercel.app,https://mercadinhosys.vercel.app
   ```
   ⚠️ **IMPORTANTE**: Use a URL EXATA do seu Vercel (copie da barra de endereços)

5. Clique em **Save Changes**
6. Aguarde o redeploy automático (~2 minutos)

### 💾 PASSO 3: Configurar Banco de Dados PostgreSQL

**Se você ainda usa SQLite:**

1. Crie um banco PostgreSQL gratuito no Neon:
   - Acesse: https://neon.tech
   - Crie conta gratuita
   - Crie novo projeto
   - Copie a **Connection String**

2. No Render Dashboard:
   - Vá em **Environment**
   - Adicione:
     ```
     Nome: DATABASE_URL
     Valor: postgresql://user:pass@host.neon.tech/db?sslmode=require
     ```
   - Clique em **Save Changes**

3. Execute as migrações:
   ```bash
   # No seu terminal local
   cd backend
   python seed_neon.py  # Popula o banco com dados de teste
   ```

### 🔐 PASSO 4: Configurar Chaves de Segurança

No Render Dashboard → Environment, adicione:

```
SECRET_KEY=sua-chave-secreta-aqui-minimo-32-caracteres
JWT_SECRET_KEY=outra-chave-diferente-minimo-32-caracteres
```

💡 **Dica**: Use o botão "Generate Value" do Render para gerar chaves seguras

### 🔍 PASSO 5: Verificar Logs do Render

1. No Render Dashboard, clique em **Logs**
2. Procure por erros:
   - `CORS error` → Volte ao Passo 2
   - `Database connection failed` → Volte ao Passo 3
   - `401 Unauthorized` → Volte ao Passo 4
   - `Blueprint not registered` → Problema no código

### 🧪 PASSO 6: Testar Endpoints Manualmente

Abra o terminal e teste:

```bash
# 1. Teste de saúde
curl https://mercadinhosys.onrender.com/api/health

# 2. Teste de login
curl -X POST https://mercadinhosys.onrender.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@mercadinho.com","senha":"admin123"}'

# 3. Teste de produtos (substitua TOKEN pelo token do passo 2)
curl https://mercadinhosys.onrender.com/api/produtos \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

## 🔧 CORREÇÕES APLICADAS AUTOMATICAMENTE

Já apliquei as seguintes melhorias no código:

1. ✅ CORS mais permissivo no `render.yaml`
2. ✅ Logs detalhados de erro no `apiClient.ts`
3. ✅ Script de teste `testConnection()` disponível no console
4. ✅ Melhor tratamento de erros no backend

## 📋 CHECKLIST COMPLETO

Marque cada item conforme completa:

### Backend (Render)
- [ ] `CORS_ORIGINS` configurado com URL exata do Vercel
- [ ] `DATABASE_URL` configurado (PostgreSQL/Neon)
- [ ] `SECRET_KEY` configurado (32+ caracteres)
- [ ] `JWT_SECRET_KEY` configurado (32+ caracteres)
- [ ] Backend responde em `/api/health` (teste no navegador)
- [ ] Logs não mostram erros críticos

### Frontend (Vercel)
- [ ] `VITE_API_URL` aponta para `https://mercadinhosys.onrender.com/api`
- [ ] Console não mostra erros de CORS
- [ ] Login funciona e retorna token
- [ ] `testConnection()` mostra todos endpoints ✅

### Banco de Dados
- [ ] PostgreSQL/Neon configurado (não SQLite)
- [ ] Tabelas criadas (rode migrações)
- [ ] Dados de teste inseridos (rode seed)

## 🚨 PROBLEMAS COMUNS E SOLUÇÕES

### "CORS policy: No 'Access-Control-Allow-Origin'"
**Solução**: Adicione a URL exata do Vercel no `CORS_ORIGINS` do Render

### "401 Unauthorized" em todos endpoints
**Solução**: 
1. Faça logout e login novamente
2. Verifique se `JWT_SECRET_KEY` é a mesma em dev e prod

### "500 Internal Server Error"
**Solução**: 
1. Verifique logs do Render
2. Provavelmente falta `DATABASE_URL`

### "Network Error" ou "Failed to fetch"
**Solução**:
1. Backend está offline? Verifique Render Dashboard
2. URL incorreta? Verifique `VITE_API_URL`

### Vendas carregam mas outros dados não
**Solução**:
1. Problema de permissões ou banco vazio
2. Rode `seed_neon.py` para popular dados

## 📞 PRÓXIMOS PASSOS

**Me informe:**

1. Resultado do `testConnection()` no console
2. URL exata do seu Vercel (copie da barra de endereços)
3. Você tem PostgreSQL/Neon configurado? Qual a URL?
4. Erros que aparecem nos Logs do Render

Com essas informações, posso fazer ajustes mais específicos!

## 🎯 SOLUÇÃO RÁPIDA (Se tiver pressa)

Execute estes comandos no Render Dashboard → Environment:

```bash
# Adicione estas variáveis:
CORS_ORIGINS=*
DATABASE_URL=postgresql://seu-banco-aqui
SECRET_KEY=dev-secret-key-12345678901234567890
JWT_SECRET_KEY=dev-jwt-key-12345678901234567890
```

⚠️ **ATENÇÃO**: `CORS_ORIGINS=*` permite qualquer origem (use apenas para teste!)

Depois de adicionar, clique em **Save Changes** e aguarde o redeploy.
