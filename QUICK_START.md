# 🚀 Quick Start - MercadinhoSys

## 🎯 Setup Rápido (5 minutos)

### Opção 1: Docker (Recomendado)

```bash
# 1. Clone o repositório
git clone <seu-repo>
cd mercadinhosys

# 2. Configure variáveis de ambiente
cp .env.example .env

# 3. Inicie tudo com um comando
make install

# 4. Acesse o sistema
# Frontend: http://localhost
# Backend: http://localhost:5000
# Login: admin / admin123
```

### Opção 2: Manual (Desenvolvimento)

#### Backend

```bash
cd backend

# Criar ambiente virtual
python -m venv venv

# Ativar venv (Windows)
venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Criar banco e popular dados
python seed_cloud.py

# Iniciar servidor
python run.py
```

#### Frontend

```bash
cd frontend/mercadinhosys-frontend

# Instalar dependências
npm install

# Iniciar dev server
npm run dev
```

---

## 🔑 Credenciais de Teste

**Admin:**
- Username: `admin`
- Password: `admin123`
- Role: ADMIN (acesso total)

**Vendedor:**
- Username: `joao`
- Password: `joao123`
- Role: VENDEDOR (acesso limitado)

---

## 📦 Dados de Teste Incluídos

Após executar `seed_cloud.py`:

- ✅ 1 Estabelecimento (Mercado Souza Center)
- ✅ 2 Funcionários (admin, joao)
- ✅ 3 Clientes
- ✅ 2 Fornecedores
- ✅ 5 Categorias
- ✅ 10 Produtos com estoque
- ✅ 5 Vendas de exemplo (apenas local)

---

## 🧪 Testar Funcionalidades

### 1. Login
```bash
curl -X POST http://127.0.0.1:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

### 2. Health Check
```bash
curl http://127.0.0.1:5000/api/auth/health
```

### 3. Listar Produtos
```bash
# Primeiro faça login e copie o access_token
curl http://127.0.0.1:5000/api/produtos \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

### 4. Dashboard
```bash
curl http://127.0.0.1:5000/api/dashboard/cientifico \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

---

## 🛠️ Comandos Úteis

### Docker

```bash
# Iniciar serviços
make up

# Parar serviços
make down

# Ver logs
make logs

# Logs de um serviço específico
make logs-backend
make logs-frontend

# Rebuild
make rebuild

# Limpar tudo
make clean

# Backup do banco
make backup

# Restaurar backup
make restore

# Rodar testes
make test

# Migrations
make migrate
```

### Backend (Manual)

```bash
# Ativar venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Instalar dependências
pip install -r requirements.txt

# Criar/recriar banco
python seed_cloud.py

# Rodar testes
pytest

# Iniciar servidor
python run.py

# Migrations
flask db upgrade
flask db migrate -m "mensagem"
```

### Frontend (Manual)

```bash
# Instalar dependências
npm install

# Dev server
npm run dev

# Build
npm run build

# Preview build
npm run preview

# Lint
npm run lint

# Type check
npm run type-check
```

---

## 📁 Estrutura do Projeto

```
mercadinhosys/
├── backend/                    # API Flask
│   ├── app/
│   │   ├── routes/            # Endpoints da API
│   │   ├── models.py          # Modelos SQLAlchemy
│   │   ├── decorators/        # JWT, paginação
│   │   └── utils/             # Helpers
│   ├── config.py              # Configuração (detecta ambiente)
│   ├── run.py                 # Entry point
│   ├── seed_cloud.py          # Seed inteligente
│   └── requirements.txt       # Dependências Python
│
├── frontend/mercadinhosys-frontend/
│   ├── src/
│   │   ├── features/          # Páginas por feature
│   │   ├── api/               # Cliente API
│   │   ├── components/        # Componentes reutilizáveis
│   │   └── types/             # TypeScript types
│   └── package.json           # Dependências Node
│
├── docker-compose.yml         # Orquestração Docker
├── render.yaml                # Deploy Render.com
├── Makefile                   # Comandos automatizados
└── .env.example               # Template de variáveis
```

---

## 🔧 Configuração de Ambiente

### Desenvolvimento Local

```env
# .env
FLASK_ENV=development
SQLITE_DB=sqlite:///c:/temp/mercadinho_instance/mercadinho.db
SECRET_KEY=dev-secret-key-change-in-production
JWT_SECRET_KEY=dev-jwt-secret-key-change-in-production
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Produção (Render.com)

```env
# Configurar no Render Dashboard
FLASK_ENV=production
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
SECRET_KEY=[Generate Value]
JWT_SECRET_KEY=[Generate Value]
CORS_ORIGINS=https://seu-frontend.onrender.com
```

---

## 🐛 Problemas Comuns

### Backend não inicia

**Erro:** `ModuleNotFoundError: No module named 'flask'`

**Solução:**
```bash
# Ativar venv primeiro!
venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend não conecta no backend

**Erro:** `Network Error` ou `CORS policy`

**Solução:**
1. Verificar se backend está rodando: `http://127.0.0.1:5000/api/auth/health`
2. Verificar `VITE_API_URL` em `.env.development`
3. Verificar `CORS_ORIGINS` no backend

### Banco de dados vazio

**Erro:** Login falha com "Credenciais inválidas"

**Solução:**
```bash
cd backend
venv\Scripts\activate
python seed_cloud.py
```

### Porta já em uso

**Erro:** `Address already in use: 5000`

**Solução:**
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:5000 | xargs kill -9
```

---

## 📚 Documentação Adicional

- **Deploy:** `DEPLOY_RENDER.md` - Guia completo de deploy
- **Checklist:** `DEPLOY_CHECKLIST.md` - Checklist pré/pós deploy
- **DevOps:** `DEVOPS_COMPLETE.md` - Infraestrutura e CI/CD
- **Docker:** `README_DOCKER.md` - Uso do Docker
- **API:** Swagger UI em `http://localhost:5000/api/docs`

---

## 🎓 Próximos Passos

1. ✅ Explorar o sistema localmente
2. ✅ Testar todas as funcionalidades
3. ✅ Ler documentação de deploy
4. ✅ Configurar Render.com
5. ✅ Deploy em produção
6. ✅ Configurar monitoramento
7. ✅ Treinar usuários

---

## 💡 Dicas

- Use `make` para comandos Docker (mais rápido)
- Sempre ative o venv antes de rodar comandos Python
- Frontend hot-reload funciona automaticamente
- Backend precisa restart manual após mudanças
- Logs estão em `backend/logs/app.log`
- Use Postman/Insomnia para testar API
- Swagger UI disponível em `/api/docs`

---

**🎉 Pronto para começar!**

Qualquer dúvida, consulte a documentação ou abra uma issue no GitHub.
