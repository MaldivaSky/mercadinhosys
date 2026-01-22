# 🌱 Guia: Semear Banco Neon PostgreSQL

## 🎯 Opção 1: Seed Local → Neon (RECOMENDADO - 2 minutos)

Execute o seed da sua máquina local, mas populando o Neon na nuvem.

### Passo 1: Ativar venv

```bash
cd backend
venv\Scripts\activate
```

### Passo 2: Executar Seed

```bash
python seed_neon.py
```

**O que vai acontecer:**
1. Script detecta que é Neon PostgreSQL
2. Conecta no banco na nuvem
3. Cria todas as tabelas
4. Popula com dados iniciais
5. Mostra resumo

**Dados criados:**
- ✅ 1 Estabelecimento (Mercado Souza Center)
- ✅ 2 Funcionários (admin/admin123, joao/joao123)
- ✅ 3 Clientes
- ✅ 2 Fornecedores
- ✅ 5 Categorias
- ✅ 10 Produtos com estoque
- ❌ Vendas (não cria em nuvem)

### Passo 3: Testar

```bash
# Testar login
curl -X POST https://seu-backend.onrender.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

---

## 🎯 Opção 2: Seed via Render Shell (Se Opção 1 falhar)

Execute o seed diretamente no servidor Render.

### Passo 1: Acessar Render Shell

1. Acesse: https://dashboard.render.com
2. Selecione: **mercadinhosys-backend**
3. Clique: **Shell** (no menu lateral)

### Passo 2: Executar Seed

```bash
# No shell do Render
python seed_cloud.py
```

### Passo 3: Confirmar

Digite `s` quando perguntar se deseja continuar.

---

## 🎯 Opção 3: Seed Automático no Deploy

O seed roda automaticamente no primeiro deploy se o banco estiver vazio.

### Como Funciona

O script `backend/start.sh` verifica:
1. Se banco tem dados?
2. Se não → Executa `seed_cloud.py` automaticamente
3. Se sim → Pula seed

### Forçar Seed no Próximo Deploy

1. Limpe o banco Neon (se necessário)
2. Faça um novo deploy no Render
3. Seed executará automaticamente

---

## 🧪 Verificar se Seed Funcionou

### Teste 1: Health Check

```bash
curl https://seu-backend.onrender.com/api/auth/health
```

**Resposta esperada:**
```json
{
  "status": "healthy",
  "database": "connected",
  "environment": "production"
}
```

### Teste 2: Login

```bash
curl -X POST https://seu-backend.onrender.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

**Resposta esperada:**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJ...",
    "user": {
      "username": "admin",
      "nome": "Administrador Sistema"
    }
  }
}
```

### Teste 3: Listar Produtos

```bash
# Use o token do login anterior
curl https://seu-backend.onrender.com/api/produtos \
  -H "Authorization: Bearer SEU_TOKEN"
```

**Resposta esperada:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "nome": "Arroz Tipo 1 5kg",
      "preco_venda": 22.90
    }
  ]
}
```

---

## 🐛 Troubleshooting

### Erro: "Connection refused"

**Causa:** Neon está em sleep (plano free dorme após 5min)

**Solução:**
1. Acesse: https://console.neon.tech
2. Selecione seu projeto
3. Clique em qualquer query para acordar o banco
4. Tente novamente

### Erro: "Authentication failed"

**Causa:** Credenciais incorretas

**Solução:**
1. Verifique `DATABASE_URL` no `.env`
2. Confirme credenciais em console.neon.tech
3. Verifique se tem `?sslmode=require` no final

### Erro: "Table already exists"

**Causa:** Banco já tem dados

**Solução:**
```bash
# Opção 1: Limpar e recriar
python seed_neon.py
# Digite 's' quando perguntar se deseja limpar

# Opção 2: Manter dados existentes
# Não precisa fazer nada, banco já está populado
```

### Erro: "SSL connection required"

**Causa:** Faltou `?sslmode=require` na URL

**Solução:**
```bash
# Verifique se a URL termina com:
?sslmode=require
```

---

## 📊 Logs do Seed

### Sucesso

```
========================================
🌱 SEED DATABASE - Ambiente: NEON
========================================

✅ Conexão com banco de dados OK
📊 Database: neondb
🔗 Host: ep-quiet-smoke-a8z521gd-pooler.eastus2.azure.neon.tech

📋 Criando tabelas...
✅ Tabelas criadas

🏢 Criando estabelecimento...
✅ Estabelecimento criado: Mercado Souza Center

👥 Criando funcionários...
  ✅ Administrador Sistema (ADMIN)
  ✅ João Silva (VENDEDOR)

🛒 Criando clientes...
  ✅ Maria Santos
  ✅ Pedro Oliveira
  ✅ Ana Costa

🚚 Criando fornecedores...
  ✅ Distribuidora ABC
  ✅ Atacado XYZ

📁 Criando categorias...
  ✅ Alimentos
  ✅ Bebidas
  ✅ Limpeza
  ✅ Higiene
  ✅ Padaria

📦 Criando produtos...
  ✅ Arroz Tipo 1 5kg - R$ 22.90
  ✅ Feijão Preto 1kg - R$ 8.90
  [...]

💾 Salvando no banco de dados...
✅ Dados salvos com sucesso!

========================================
📊 RESUMO DO SEED
========================================
  Estabelecimentos: 1
  Funcionários:     2
  Clientes:         3
  Fornecedores:     2
  Categorias:       5
  Produtos:         10
  Vendas:           0
========================================

🎉 SEED COMPLETO!

📝 Credenciais de acesso:
  Username: admin
  Password: admin123

🌐 Ambiente: NEON
========================================
```

---

## ✅ Checklist

- [ ] Ativei venv
- [ ] Executei `python seed_neon.py`
- [ ] Confirmei com 's'
- [ ] Seed completou sem erros
- [ ] Testei health check
- [ ] Testei login (admin/admin123)
- [ ] Testei listar produtos
- [ ] Backend funcionando na nuvem

---

## 🎯 Resumo Rápido

**Comando único:**
```bash
cd backend
venv\Scripts\activate
python seed_neon.py
```

**Credenciais criadas:**
- Username: `admin`
- Password: `admin123`

**Tempo estimado:** 2 minutos

---

## 📞 Suporte

Se tiver problemas:
1. Verifique logs do seed
2. Teste conexão com Neon
3. Verifique se Neon não está em sleep
4. Consulte troubleshooting acima

---

**🌱 Pronto para semear o Neon!**

Escolha a Opção 1 (mais rápida) e execute `python seed_neon.py`.
