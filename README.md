<div align="center">

# 🛒 MercadinhoSys

### ERP & PDV Multi-Tenant com Business Intelligence Científico

*Gestão comercial de nível profissional para mercados, lojas e atacarejos — varejo e atacado.*

<br/>

[![Version](https://img.shields.io/badge/version-2.2.0-2563eb?style=for-the-badge)](#)
[![Status](https://img.shields.io/badge/status-production-16a34a?style=for-the-badge)](#)
[![PWA](https://img.shields.io/badge/PWA-instalável-9333ea?style=for-the-badge&logo=pwa&logoColor=white)](#)
[![License](https://img.shields.io/badge/license-MIT-64748b?style=for-the-badge)](#-licença--autor)

<br/>

**Frontend**

![React](https://img.shields.io/badge/React_18-20232A?style=flat-square&logo=react&logoColor=61DAFB)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=flat-square&logo=typescript&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-646CFF?style=flat-square&logo=vite&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=flat-square&logo=tailwind-css&logoColor=white)
![React Router](https://img.shields.io/badge/React_Router-CA4245?style=flat-square&logo=react-router&logoColor=white)
![Axios](https://img.shields.io/badge/Axios-5A29E4?style=flat-square&logo=axios&logoColor=white)

**Backend**

![Python](https://img.shields.io/badge/Python_3.11+-3776AB?style=flat-square&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=flat-square&logo=flask&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy_2.0-D71F00?style=flat-square&logo=sqlalchemy&logoColor=white)
![JWT](https://img.shields.io/badge/JWT-000000?style=flat-square&logo=jsonwebtokens&logoColor=white)
![Gunicorn](https://img.shields.io/badge/Gunicorn-499848?style=flat-square&logo=gunicorn&logoColor=white)

**Dados & Infra**

![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=flat-square&logo=redis&logoColor=white)
![Render](https://img.shields.io/badge/Render-46E3B7?style=flat-square&logo=render&logoColor=white)
![Vercel](https://img.shields.io/badge/Vercel-000000?style=flat-square&logo=vercel&logoColor=white)

</div>

---

## ✨ Visão Geral

**MercadinhoSys** é um ecossistema completo de **ERP + Ponto de Venda (PDV)** com arquitetura **multi-tenant (SaaS)**, emissão fiscal (**NFC-e**), cadastro de produtos por **código de barras** e um **dashboard de Business Intelligence** com análises científicas (Curva ABC, RFM, previsão de ruptura). Tudo numa interface **PWA** instalável, responsiva e mobile-first.

> 📖 **Comece por aqui:** [`GUIA_DO_SISTEMA.md`](GUIA_DO_SISTEMA.md) — o documento-âncora com tudo que está construído, ligado e testado.

---

## 🚀 Quick Start

```bash
# Clone
git clone https://github.com/MaldivaSky/mercadinhosys.git
cd mercadinhosys

# Configure os segredos
cp .env.example .env

# Suba tudo com Docker (backend + frontend + banco)
make install
```

<div align="center">

| Serviço | URL | Acesso |
|---|---|---|
| 🖥️ Frontend | `http://localhost` | botão **Acesso Demo** |
| ⚙️ Backend API | `http://localhost:5000` | JWT |

</div>

> Setup manual (sem Docker): veja [`README-LOCAL.md`](README-LOCAL.md) · Guia Docker completo: [`README_DOCKER.md`](README_DOCKER.md)

---

## 🧩 Funcionalidades

### 📊 Business Intelligence & Analytics
- **Dashboards executivos** em tempo real: faturamento, margens, lucro líquido, ticket médio.
- **Curva ABC** automática (Pareto) e gestão científica de estoque/validade.
- **Análise RFM** de clientes: segmentação automática (Campeões, Fiéis, Em Risco, Perdidos).
- **DRE** e relatórios exportáveis em **PDF / Excel / CSV**.

### 🧾 Fiscal (NFC-e) & Catálogo Inteligente
- **Emissão de NFC-e** (modelo 65) via gateway **Focus NFe**, importação de **XML de entrada**, cancelamento e numeração por loja.
- **Travas de produção responsáveis:** não emite sem gateway real configurado nem com produto **sem NCM válido**.
- **Cadastro por código de barras:** leitura de EAN preenche nome, marca, **NCM** e imagem via catálogo local + **API Cosmos**, com cache que cresce sozinho (economiza quota).

### 🏢 Multi-Tenant & SaaS
- **Isolamento de dados por loja** garantido em nível de ORM (`TenantQuery`) com política **fail-closed** — um lojista jamais vê o dado de outro.
- **Onboarding self-service** com trial; super admin (dono do SaaS) ativa/inativa lojas.
- **Planos & permissões** por nível de acesso (Admin → Entregador).

### 🖥️ PDV & Operação de Loja
- Frente de caixa ultrarrápida com **atalhos de teclado** e **múltiplos pagamentos**.
- **Caixa blindado:** auditoria de quebra separando gaveta física (dinheiro) de fluxo digital (Pix/cartão).
- **Crédito (fiado)**, sangria/suprimento, **SFA** e **Delivery** com rotas e comissões.
- **PIN de segurança** para operações sensíveis (estorno, editar/descartar produto).

### 👥 RH & PWA
- **Ponto fotográfico** com geolocalização; holerites, escalas e banco de horas.
- **PWA instalável** (mobile/desktop) com cache offline e pull-to-refresh próprio.

---

## 🏗️ Arquitetura

```
┌─────────────────────────────┐        ┌──────────────────────────────┐
│   Frontend (PWA)            │  HTTPS │   Backend API (Flask)         │
│   React 18 · TS · Vite      │◄──────►│   REST · JWT · SQLAlchemy     │
│   Tailwind · Recharts       │  JSON  │   TenantQuery (multi-tenant)  │
└─────────────────────────────┘        └───────────────┬──────────────┘
                                                        │
                                  ┌─────────────────────┼─────────────────────┐
                                  │                      │                     │
                            PostgreSQL / SQLite     Focus NFe (fiscal)    API Cosmos (EAN)
```

- **Multi-tenant real:** toda consulta é escopada por estabelecimento automaticamente; rotas autenticadas sem tenant resolvido recebem `403` (fail-closed).
- **Detecção de ambiente:** SQLite em dev, PostgreSQL em produção, sem mudança de código.

---

## 📚 Documentação

| Documento | Conteúdo |
|---|---|
| [`GUIA_DO_SISTEMA.md`](GUIA_DO_SISTEMA.md) | **Âncora** — o que está construído, ligado e testado |
| [`CHECKLIST_FISCAL_GO_LIVE.md`](CHECKLIST_FISCAL_GO_LIVE.md) | Passo a passo para ativar a emissão fiscal de uma loja |
| [`README_DOCKER.md`](README_DOCKER.md) | Guia completo de Docker |
| [`README-LOCAL.md`](README-LOCAL.md) | Setup manual local |

---

## 🔐 Segurança

- ✅ **Autenticação JWT** com refresh tokens.
- ✅ **Isolamento multi-tenant ativo** (`TenantQuery` + `before_request` fail-closed).
- ✅ **PIN de segurança** (hash) para estorno, edição e descarte de produtos.
- ✅ **Rate limiting** e proteção contra brute-force nas rotas sensíveis.
- ✅ **Auditoria transacional** de caixa, vendas e acessos.
- ✅ Segredos fora do versionamento (env vars no servidor).

---

## 🧪 Qualidade

```bash
# Backend (pytest)
cd backend && venv/Scripts/python -m pytest tests/ -q     # 41 passed, 1 xfailed

# Frontend (type-check + build de produção)
cd frontend/mercadinhosys-frontend && npm run build
```

Cobertura de testes nos pontos críticos: isolamento multi-tenant, emissão fiscal (NFC-e), lookup de catálogo (Cosmos) e PIN de segurança.

---

## ☁️ Deploy

Trabalha-se em `main`; a branch **`master`** recebe o *fast-forward* de `main` e o `git push origin master` dispara o deploy (**Render** para o backend, **Vercel** para o frontend, **PostgreSQL** gerenciado).

> Variáveis sensíveis (`SECRET_KEY`, `JWT_SECRET_KEY`, `COSMOS_TOKEN`, credenciais fiscais) ficam nas *env vars* do servidor — nunca no git.

---

## 🗺️ Roadmap

- [ ] **Billing SaaS** — gateway de pagamento real (Asaas/Stripe/Efí) + webhook → ativação automática do tenant.
- [ ] **Fiscal em produção** — homologação real Focus NFe (certificado A1 + CSC do lojista).
- [ ] **PIX automático** via webhook (sem confirmação manual).
- [ ] **Impressoras fiscais** (WebUSB/Bluetooth) e **previsão de ruptura** com ML.

---

## 🤝 Contribuindo

1. Fork o projeto
2. Crie sua branch (`git checkout -b feature/MinhaFeature`)
3. Commit (`git commit -m 'feat: minha feature'`)
4. Push (`git push origin feature/MinhaFeature`)
5. Abra um Pull Request

---

## 📝 Licença & Autor

Distribuído sob a licença **MIT**.

<div align="center">

Desenvolvido com 💙 por **MaldivasTech** — feito com alma amazônica 🌳

**MercadinhoSys** · ERP Multi-Tenant · Production Ready

</div>
