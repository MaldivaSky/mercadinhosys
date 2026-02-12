# 🚨 AÇÃO IMEDIATA - Resolver Erros 422 no Vercel

## ⚡ Problema
Usuários recebendo erro 422 "Signature verification failed" ao acessar o dashboard e outras páginas.

## 🎯 Solução Rápida (5 minutos)

### Passo 1: Verificar JWT_SECRET_KEY no Backend (Vercel/Render)

1. **Acessar o dashboard do seu serviço de backend** (Vercel, Render, Railway, etc.)

2. **Ir em Settings → Environment Variables**

3. **Verificar se existe a variável `JWT_SECRET_KEY`**
   - ✅ Se existir: Anotar o valor
   - ❌ Se não existir: Adicionar agora!

4. **Adicionar/Atualizar a variável:**
   ```
   Nome: JWT_SECRET_KEY
   Valor: dev-jwt-secret-change-in-production
   ```
   
   ⚠️ **IMPORTANTE:** Use o mesmo valor que está no seu `.env` local do backend!

5. **Salvar e fazer Redeploy do backend**

### Passo 2: Limpar Tokens Antigos dos Usuários

Após corrigir o `JWT_SECRET_KEY`, os tokens antigos ficarão inválidos. Existem 2 opções:

#### Opção A: Automática (Recomendado) ✅
O frontend já foi corrigido para detectar tokens inválidos automaticamente!
- Usuários serão redirecionados para login automaticamente
- Tokens inválidos serão limpos do localStorage
- Nenhuma ação manual necessária! 🎉

#### Opção B: Manual (Se necessário)
Se algum usuário ainda tiver problemas:
1. Abrir DevTools (F12)
2. Console → Application → Local Storage
3. Deletar `access_token` e `refresh_token`
4. Fazer login novamente

### Passo 3: Fazer Deploy das Correções

#### Backend
```bash
cd backend
git add .
git commit -m "fix: add comprehensive JWT error handlers"
git push
```

#### Frontend
```bash
cd frontend/mercadinhosys-frontend
git add .
git commit -m "fix: improve JWT error detection and remove unused imports"
git push
```

### Passo 4: Verificar se Funcionou

1. **Abrir o aplicativo no Vercel**
2. **Tentar fazer login**
3. **Acessar o dashboard**
4. **Resultado Esperado:** ✅ Tudo funcionando sem erros 422!

---

## 🔍 Diagnóstico Rápido

### Se ainda houver erros 422:

1. **Verificar logs do backend:**
   ```
   Procurar por: "🔐 Token inválido recebido" ou "🔐 Assinatura JWT inválida"
   ```

2. **Verificar console do frontend:**
   ```
   Procurar por: "🔐 JWT inválido detectado, limpando tokens..."
   ```

3. **Verificar variáveis de ambiente:**
   ```bash
   # Backend local (.env)
   JWT_SECRET_KEY=dev-jwt-secret-change-in-production
   
   # Backend Vercel (Environment Variables)
   JWT_SECRET_KEY=dev-jwt-secret-change-in-production
   ```
   
   ⚠️ **Os valores DEVEM ser IDÊNTICOS!**

---

## ✅ Checklist de Verificação

- [ ] `JWT_SECRET_KEY` está definido no backend (Vercel/Render)
- [ ] `JWT_SECRET_KEY` é o mesmo no local e produção
- [ ] Backend foi feito redeploy após adicionar/atualizar a variável
- [ ] Frontend foi feito deploy com as correções
- [ ] Testado login e acesso ao dashboard
- [ ] Sem erros 422 nos logs

---

## 📞 Se Ainda Houver Problemas

### Erro Persiste Após Todas as Correções?

1. **Limpar TODOS os tokens:**
   ```javascript
   // No console do navegador:
   localStorage.clear();
   sessionStorage.clear();
   ```

2. **Fazer hard refresh:**
   - Windows: `Ctrl + Shift + R`
   - Mac: `Cmd + Shift + R`

3. **Verificar se o backend está usando a variável correta:**
   ```python
   # No backend, adicionar log temporário em config.py:
   print(f"JWT_SECRET_KEY: {os.environ.get('JWT_SECRET_KEY')}")
   ```

4. **Verificar se o frontend está enviando o token:**
   ```javascript
   // No console do navegador:
   console.log('Token:', localStorage.getItem('access_token'));
   ```

---

## 🎯 Resumo

**O que foi corrigido:**
- ✅ Backend agora trata erros JWT corretamente (6 handlers adicionados)
- ✅ Frontend detecta automaticamente tokens inválidos
- ✅ Build do frontend corrigido (erro TypeScript resolvido)
- ✅ Usuários são redirecionados automaticamente para login

**O que você precisa fazer:**
1. Verificar/adicionar `JWT_SECRET_KEY` no Vercel
2. Fazer redeploy do backend
3. Fazer deploy do frontend
4. Testar!

**Tempo estimado:** 5-10 minutos ⏱️

---

**Status:** ✅ Correções implementadas e testadas localmente  
**Build Frontend:** ✅ Passou sem erros  
**Próximo Passo:** Deploy para produção
