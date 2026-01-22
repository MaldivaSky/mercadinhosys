# 🛒 MercadinhoSys - Sistema de Gestão para Pequenos Mercados

![Status do Projeto](https://img.shields.io/badge/Status-Production_Ready-green)
![License](https://img.shields.io/badge/License-MIT-blue)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![React](https://img.shields.io/badge/React-18+-blue)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Ready-blue)

**MercadinhoSys** é uma solução completa de ERP (Enterprise Resource Planning) e PDV (Ponto de Venda) desenvolvida para facilitar a gestão de pequenos comércios. O sistema integra controle de estoque, frente de caixa, gestão financeira e análise de dados em uma interface web moderna e responsiva.

**🎉 Novidade:** Sistema agora suporta PostgreSQL e está pronto para deploy em produção no Render.com!

---

## 🚀 Quick Start

### Opção 1: Docker (Recomendado)

```bash
# Clone e configure
git clone <seu-repo>
cd mercadinhosys
cp .env.example .env

# Inicie tudo com um comando
make install

# Acesse: http://localhost (Frontend) | http://localhost:5000 (Backend)
# Login: admin / admin123
```

### Opção 2: Manual

Ver [QUICK_START.md](QUICK_START.md) para instruções detalhadas.

---

## 📚 Documentação

### Para Desenvolvedores
- **[QUICK_START.md](QUICK_START.md)** - Setup rápido (5 minutos)
- **[README_DOCKER.md](README_DOCKER.md)** - Guia completo do Docker
- **[DEVOPS_COMPLETE.md](DEVOPS_COMPLETE.md)** - Infraestrutura e CI/CD

### Para Deploy em Produção
- **[DEPLOY_RENDER.md](DEPLOY_RENDER.md)** - Guia completo de deploy no Render.com
- **[DEPLOY_CHECKLIST.md](DEPLOY_CHECKLIST.md)** - Checklist pré/pós deploy
- **[DEPLOY_POSTGRESQL_COMPLETE.md](DEPLOY_POSTGRESQL_COMPLETE.md)** - Migração PostgreSQL

### Documentação Técnica
- **[ANALISE_SISTEMA_MERCADINHOSYS.md](ANALISE_SISTEMA_MERCADINHOSYS.md)** - Análise do sistema
- **[CORRECOES_CRITICAS_ARQUITETURA.md](CORRECOES_CRITICAS_ARQUITETURA.md)** - Correções arquiteturais
- **[DASHBOARD_*.md](DASHBOARD_RESUMO_FINAL.md)** - Documentação do Dashboard
- **[EMAIL_NOTA_FISCAL.md](EMAIL_NOTA_FISCAL.md)** - Sistema de envio de cupom por email

---

## 🚀 Tecnologias Utilizadas

### Frontend
* ![React](https://img.shields.io/badge/React-20232A?style=flat&logo=react&logoColor=61DAFB) **React 18** + **Vite** - Interface rápida e moderna
* ![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=flat&logo=typescript&logoColor=white) **TypeScript** - Tipagem estática
* ![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=flat&logo=tailwind-css&logoColor=white) **Tailwind CSS** - Estilização responsiva
* **Axios** - Cliente HTTP
* **Recharts** - Visualização de dados

### Backend
* ![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white) **Python 3.11+**
* ![Flask](https://img.shields.io/badge/Flask-000000?style=flat&logo=flask&logoColor=white) **Flask** - Framework web
* **SQLAlchemy** - ORM
* **Flask-JWT-Extended** - Autenticação JWT
* **PostgreSQL** / **SQLite** - Banco de dados (detecta ambiente automaticamente)

### DevOps
* ![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white) **Docker** + **Docker Compose**
* **Render.com** - Deploy em produção
* **Neon PostgreSQL** - Database serverless
* **GitHub Actions** - CI/CD
* **Gunicorn** - WSGI server

---

## 📋 Funcionalidades Principais

### 🖥️ PDV (Ponto de Venda)
* Frente de caixa ágil e intuitiva
* Leitura de código de barras
* Carrinho de compras em tempo real
* Múltiplos métodos de pagamento
* Autorização de gerente para descontos
* Busca rápida de produtos e clientes
* **📧 Envio de cupom fiscal por email**

### 📊 Dashboard Científico
* **3 Modos de Visualização:**
  - 📊 Visão Geral (KPIs essenciais)
  - 📈 Análise Detalhada (ABC + Temporal + Financeiro)
  - 🧬 Modo Científico (análise completa)
* Tooltips interativos com explicações
* Drill-down em métricas (ex: ROI por produto)
* Gráficos de evolução temporal
* Análise ABC de produtos
* Métricas financeiras avançadas

### 📦 Gestão de Estoque
* CRUD completo de produtos
* Controle de fornecedores
* Categorização de produtos
* Alertas de estoque baixo
* Precificação com margem de lucro
* Exportação para CSV

### 👥 Gestão Administrativa
* Controle de acesso por roles (ADMIN, GERENTE, VENDEDOR)
* Gestão de funcionários
* Cadastro de clientes
* Registro de despesas
* Relatórios gerenciais
* Histórico de vendas

---

## 🔧 Como Executar o Projeto

### Desenvolvimento Local

#### Opção 1: Docker (Recomendado)

```bash
# Clone o repositório
git clone <seu-repo>
cd mercadinhosys

# Configure variáveis de ambiente
cp .env.example .env

# Inicie tudo com um comando
make install

# Acesse:
# Frontend: http://localhost
# Backend: http://localhost:5000
# Login: admin / admin123
```

#### Opção 2: Manual

**Backend:**

```bash
# Acesse a pasta do backend
cd backend

# Crie um ambiente virtual
python -m venv venv

# Ative o ambiente virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instale as dependências
pip install -r requirements.txt

# Crie o banco e popule dados
python seed_cloud.py

# Execute o servidor
python run.py

**Frontend:**

```bash
# Acesse a pasta do frontend
cd frontend/mercadinhosys-frontend

# Instale as dependências
npm install

# Execute o servidor de desenvolvimento
npm run dev

# Acesse: http://localhost:5173
```

### Deploy em Produção

Sistema pronto para deploy no **Render.com** com **Neon PostgreSQL**.

```bash
# 1. Commit e push
git add .
git commit -m "feat: production deployment"
git push origin main

# 2. Criar Blueprint no Render
# - Acesse: https://dashboard.render.com
# - New + → Blueprint
# - Conecte seu repositório
# - Render detecta render.yaml automaticamente
# - Apply

# 3. Configurar DATABASE_URL
# - Backend → Environment → Add DATABASE_URL
# - Use suas credenciais Neon PostgreSQL

# 4. Atualizar CORS e API URLs
# - Backend: CORS_ORIGINS com URL do frontend
# - Frontend: VITE_API_URL com URL do backend
```

**Documentação completa:** [DEPLOY_RENDER.md](DEPLOY_RENDER.md)

---

## 🗄️ Banco de Dados

Sistema detecta ambiente automaticamente:
- **Local:** SQLite (`c:/temp/mercadinho_instance/mercadinho.db`)
- **Produção:** PostgreSQL (Neon, Render, Railway, Heroku)

**Seed automático** no primeiro deploy cria:
- 1 Estabelecimento
- 2 Funcionários (admin, joao)
- 3 Clientes
- 2 Fornecedores
- 5 Categorias
- 10 Produtos com estoque

**Credenciais de teste:**
- Username: `admin` / Password: `admin123` (ADMIN)
- Username: `joao` / Password: `joao123` (VENDEDOR)

---

## 🐳 Docker

```bash
# Comandos disponíveis
make install    # Setup completo (primeira vez)
make up         # Iniciar serviços
make down       # Parar serviços
make logs       # Ver logs
make test       # Rodar testes
make backup     # Backup do banco
make clean      # Limpar tudo
```

Ver [README_DOCKER.md](README_DOCKER.md) para mais detalhes.

---

## 🧪 Testes

```bash
# Backend
cd backend
venv\Scripts\activate  # Windows
pytest

# Frontend
cd frontend/mercadinhosys-frontend
npm run test
```

---

## 📊 Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                         USUÁRIO                              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Frontend (React + TypeScript)                   │
│  • Vite                                                      │
│  • Tailwind CSS                                              │
│  • Axios                                                     │
│  • Recharts                                                  │
└────────────────────────┬────────────────────────────────────┘
                         │ REST API (JWT)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Backend (Flask + Python)                        │
│  • Flask-JWT-Extended                                        │
│  • SQLAlchemy ORM                                            │
│  • Flask-CORS                                                │
│  • Gunicorn (Produção)                                       │
└────────────────────────┬────────────────────────────────────┘
                         │ SQL
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Database                                        │
│  • SQLite (Desenvolvimento)                                  │
│  • PostgreSQL (Produção)                                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔐 Segurança

- ✅ Autenticação JWT com refresh tokens
- ✅ Senhas hasheadas com Werkzeug
- ✅ CORS configurável por ambiente
- ✅ SSL obrigatório em produção
- ✅ Validação de entrada em todas as rotas
- ✅ Rate limiting (configurável)
- ✅ Auditoria de login com histórico

---

## 📈 Performance

- ✅ Connection pooling para PostgreSQL
- ✅ Cache de queries (configurável)
- ✅ Lazy loading de componentes React
- ✅ Code splitting automático (Vite)
- ✅ Gzip compression (Nginx)
- ✅ Multi-worker Gunicorn

---

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

---

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

## 👨‍💻 Autor

Desenvolvido com 💙 por [Seu Nome]

---

## 📞 Suporte

- 📧 Email: seu-email@exemplo.com
- 🐛 Issues: [GitHub Issues](https://github.com/seu-usuario/mercadinhosys/issues)
- 📚 Docs: Ver pasta de documentação

---

## 🎯 Roadmap

### v2.1 (Próximo)
- [ ] Integração com impressora fiscal
- [ ] App mobile (React Native)
- [ ] Relatórios avançados (PDF)
- [ ] Integração com WhatsApp
- [ ] Multi-estabelecimento

### v2.2 (Futuro)
- [ ] BI integrado
- [ ] Previsão de demanda (ML)
- [ ] Integração com marketplaces
- [ ] Sistema de fidelidade
- [ ] API pública

---

**🎉 Sistema em produção e pronto para uso!**

Versão: 2.0.0 | Status: Production Ready | Deploy: Render.com + Neon PostgreSQL
