# 🛒 MercadinhoSys - ERP & Scientific BI Dashboard

![Version](https://img.shields.io/badge/Version-2.2.0_Scientific-blue)
![Status](https://img.shields.io/badge/Status-Stable-green)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![React](https://img.shields.io/badge/React-18+_TS-blue)

**MercadinhoSys** é um ecossistema completo de gestão comercial (ERP) e Ponto de Venda (PDV) de nível industrial, agora potencializado com um **Dashboard de Business Intelligence Científico**. O sistema oferece análise preditiva, gestão de estoque via Classificação ABC e orquestração financeira avançada em uma interface premium e responsiva.

---

## 🚀 Quick Start

### Opção 1: Docker (Recomendado)

```bash
# Clone e configure
git clone https://github.com/MaldivaSky/mercadinhosys.git
cd mercadinhosys
cp .env.example .env

# Inicie tudo com um comando
make install

# Acesse: http://localhost (Frontend) | http://localhost:5000 (Backend)
# Login: demo / demo123
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
- **[DASHBOARD_RESUMO_FINAL.md](DASHBOARD_RESUMO_FINAL.md)** - Documentação do Dashboard
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

---

## 📋 Funcionalidades Principais Implementadas

### 📊 Business Intelligence & Analytics
*   **Dashboards Executivos:** KPIs em tempo real (Faturamento, Margens, Lucro Líquido, Ticket Médio).
*   **Gestão de Estoque Científica:** Classificação ABC automática (Curva de Pareto) e gestão de validades.
*   **Análise de Clientes (RFM):** Segmentação automática (Campeões, Fiéis, Risco, Perdidos).
*   **Relatórios Avançados:** Extratos exportáveis, análise de DRE, e relatórios de turnos consolidados.

### 🏢 Multi-Tenant & SaaS Pronta
*   **Arquitetura Multi-Estabelecimento:** Suporte nativo a matriz e múltiplas filiais.
*   **Onboarding Automático:** Criação de ambiente via acesso Demo e planos de assinatura (Gratuito, Pro, Enterprise).
*   **Gestão de Planos & Permissões (Guardiões):** Controle de rotas (PlanoGuard/SuperAdminRoute) e módulos habilitados por assinatura.

### 🖥️ PDV & Gestão de Loja (PWA Mobile-First)
*   **Frente de Caixa (PDV):** Interface ultra-rápida, atalhos de teclado, suporte a múltiplos pagamentos, sangrias, suprimentos.
*   **Gestão de Caixa Blindada:** Auditoria estrita de quebra de caixa, separando fluxo centralizado (Pix, Crédito) de gaveta física (Dinheiro).
*   **Gestão de Crédito (Fiado):** Controle de limites, pagamentos parciais e carteira de clientes devedores.
*   **SFA (Força de Vendas) & Delivery:** Módulos de gestão de pedidos, rotas de entrega e comissões.
*   **PWA Integrado:** Funciona como App Nativo (Mobile/Desktop) com instalação direta via navegador, cache offline e responsividade total.

### 👥 Gestão de RH & Operações
*   **Controle de Ponto Fotográfico:** Registro de ponto com captura de imagem e geolocalização.
*   **Painel do Colaborador:** Holerites, escalas e banco de horas.

---

## 🔧 Como Executar o Projeto

### Desenvolvimento Local

#### Opção 1: Docker (Recomendado)

```bash
# Clone o repositório
git clone https://github.com/MaldivaSky/mercadinhosys.git
cd mercadinhosys

# Configure variáveis de ambiente
cp .env.example .env

# Inicie tudo com um comando
make install

# Acesse:
# Frontend: http://localhost
# Backend: http://localhost:5000
# Login: demo / demo123 (Ou gere no botão Acesso Demo)
```

#### Opção 2: Manual

**Backend:**

```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate | Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
python seed_cloud.py
python run.py
```

**Frontend:**

```bash
cd frontend/mercadinhosys-frontend
npm install
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
```
**Documentação completa:** [DEPLOY_RENDER.md](DEPLOY_RENDER.md)

---

## 🗄️ Banco de Dados & Infraestrutura

Sistema detecta ambiente automaticamente:
- **Local:** SQLite (`c:/temp/mercadinho_instance/mercadinho.db`)
- **Produção:** PostgreSQL (Neon, Render, Railway, Heroku)

---

## 🔐 Segurança & Arquitetura

- ✅ **Autenticação JWT** blindada com refresh tokens e isolamento Multi-Tenant (`X-Tenant-ID`).
- ✅ **Rate Limiting** e proteção contra brute-force nas rotas sensíveis.
- ✅ **Auditoria Transacional:** Logs de caixa, vendas e histórico de acessos.
- ✅ **Frontend PWA:** React 18, Vite, TailwindCSS (glassmorphism premium).
- ✅ **Backend Rest API:** Flask, SQLAlchemy, Gunicorn.

---

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

---

## 📝 Licença & Autor

Este projeto está sob a licença MIT. 
Desenvolvido com 💙 por **MaldivasTech** - Feito com alma amazônica!

---

## 🎯 Roadmap Futuro

### v3.0 (Expansão de Ecossistema)
- [ ] Integração com PIX automatizado (MercadoPago/Stripe).
- [ ] Integração Direta com Impressoras Fiscais Bluetooth/Rede (via WebUSB/WebBluetooth).
- [ ] Módulo de Inteligência Artificial para Previsão de Ruptura de Estoque (Machine Learning).
- [ ] Integração com WhatsApp (Bot de Pedidos Automáticos).

---

**🎉 Sistema em produção e pronto para uso Comercial!**

Versão: 2.2.0 Scientific | Status: Production Ready | Multi-Tenant: Ativo
