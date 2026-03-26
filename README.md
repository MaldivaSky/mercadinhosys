<div align="center">
  <img src="https://via.placeholder.com/150x150.png?text=MercadinhoSys" alt="MercadinhoSys Logo" width="120" />

  <h1>🛒 MercadinhoSys</h1>
  <p><b>Industrial ERP & Digital Twin SaaS Platform</b></p>
  
  <p>
    <a href="#-sobre-o-projeto"><img alt="Status" src="https://img.shields.io/badge/Status-Production_Ready-success?style=flat-square" /></a>
    <a href="#-arquitetura-híbrida"><img alt="Architecture" src="https://img.shields.io/badge/Architecture-Hybrid_LocalFirst-blue?style=flat-square" /></a>
    <a href="#-tech-stack"><img alt="Python" src="https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white" /></a>
    <a href="#-tech-stack"><img alt="React" src="https://img.shields.io/badge/React-18+_TS-61DAFB?style=flat-square&logo=react&logoColor=black" /></a>
  </p>

  <p>
    <i>Desenvolvido com 💚 no coração da Amazônia (Manaus-AM, Brasil).</i>
  </p>
</div>

<br />

## 🌟 Sobre o Projeto

O **MercadinhoSys** evoluiu de um simples PDV para um **Ecossistema Completo de Gestão Comercial (ERP)** de nível corporativo. Mais do que gerenciar vendas, o sistema atua como um **Gêmeo Digital (Digital Twin)** do seu negócio, simulando, analisando e operando com alta fidelidade a realidade logística, financeira e de frente de caixa.

O grande diferencial desta versão é a **Engine de Simulação Mestre**, capaz de gerar 6 meses de histórico operacional hierárquico, permitindo testes de estresse em dashboards analíticos e validação de regras de negócio em 5 cenários simultâneos (do Plano *Free* ao *Premium*).

---

## 🚀 Principais Features & Módulos

### 🧠 Digital Twin & Master Seeder
O sistema acompanha um motor de simulação (`seed_simulation_master.py`) que povoa o banco de dados com **5 Tenants Distintos** simultaneamente. Cada tenant possui seu próprio DNA de vendas, margem de lucro e velocidade de giro, gerando:
*   Milhares de transações históricas (Frente de Caixa e Delivery).
*   Movimentações complexas de estoque (FIFO, Lotes, Validades).
*   Eventos de RH (Registro de ponto, admissões).
*   Gestão de Leads (Funil SaaS para captação de novos clientes).

### ⚡ Arquitetura "Local-First" Híbrida
Desenvolvido para resiliência extrema em ambientes com internet instável:
*   **Identidade Global:** Uso de `sync_uuid` (UUID v4) e `updated_at` em todas as tabelas.
*   **Operação Offline:** O PDV nunca para. Todas as operações rodam localmente (SQLite/Postgres).
*   **Bulk Sync Engine:** Um utilitário de sincronização em massa, idempotente e de alta performance, que transmite os dados locais para a nuvem (Aiven PostgreSQL) através de comandos CLI otimizados (`flask push-to-aiven`).

### 📦 Módulo Unificado de Delivery (Venda Entrega)
Transição do modelo teórico para a logística do mundo real. O ERP agora processa Vendas e Entregas em uma única transação atômica (`POST /venda-entrega`), alocando motoristas, separando produtos do estoque e gerando a rota, tudo integrado a uma interface de Frente de Caixa super fluída.

### 📊 Business Intelligence Científico
Um dashboard executivo que vai além do básico:
*   **Classificação ABC de Estoque** baseada no Princípio de Pareto.
*   **Análise RFM** (Recência, Frequência e Valor Monetário) para segmentar clientes.
*   **Previsão de Demanda** utilizando histórico de giro de mercadorias.

---

## 🛠️ Tech Stack

#### Frontend Layer
*   ![React](https://img.shields.io/badge/-React_18-61DAFB?logo=react&logoColor=black&style=flat-square) **React 18** (Vite)
*   ![TypeScript](https://img.shields.io/badge/-TypeScript_5-3178C6?logo=typescript&logoColor=white&style=flat-square) **TypeScript**
*   ![TailwindCSS](https://img.shields.io/badge/-Tailwind_CSS-38B2AC?logo=tailwindcss&logoColor=white&style=flat-square) **Tailwind CSS**
*   📈 **Recharts** (Dashboards) & **Lucide Icons**

#### Backend & Core Engine
*   ![Python](https://img.shields.io/badge/-Python_3.11-3776AB?logo=python&logoColor=white&style=flat-square) **Python 3.11+**
*   ![Flask](https://img.shields.io/badge/-Flask-000000?logo=flask&logoColor=white&style=flat-square) **Flask** (Patterns: Application Factory, Blueprints)
*   🐘 **SQLAlchemy** (ORM com Herança Polymorphic)
*   🔐 **Flask-JWT-Extended** (Autenticação Stateless)

#### Data & Infra
*   ![PostgreSQL](https://img.shields.io/badge/-PostgreSQL-4169E1?logo=postgresql&logoColor=white&style=flat-square) **PostgreSQL** (Aiven Cloud / Render Neon)
*   📦 **SQLite** (Local-First Fallback)
*   🐳 **Docker** & Docker Compose

---

## 🚦 Quick Start (Ambiente Simulado completo)

O ecossistema foi projetado para "subir" instantaneamente e demonstrar todo o seu potencial através de cenários reais pré-calculados.

### 1. Preparação (Clone e Instalação)
```bash
git clone https://github.com/MaldivaSky/mercadinhosys.git
cd mercadinhosys
```

### 2. Iniciando o Backend e a Simulação
```bash
# Entre na pasta backend
cd backend
python -m venv venv

# Ative o ambiente (Windows)
venv\Scripts\activate

# Instale as dependências
pip install -r requirements.txt

# Execute a MÁGICA: Gera 5 cenários, 6 meses de fluxo, +10.000 transações
python seed_simulation_master.py

# Inicie a API
python run.py
```

### 3. Iniciando o Frontend
Em outro terminal:
```bash
cd frontend/mercadinhosys-frontend
npm install
npm run dev
# Acesse: http://localhost:5173
```

---

## 🔑 Acesso aos Cenários (Digital Twin)

A simulação gera instantaneamente uma multi-empresa com os seguintes acessos:

| Tenant (Cenário) | Plano | Usuário Dono (Owner) | Usuário Caixa | Senha Padrão |
| :--- | :--- | :--- | :--- | :--- |
| **MercadinhoSys HQ** | Master | `admin_saas` | *N/A* | *(Acesso privado via .env)* |
| Mercado Maldivas Elite | Pro | `admin1` | `caixa1` | Admin: `admin123` / Caixa: `caixa123` |
| Supermercado Estrela | Pro | `admin2` | `caixa2` | Admin: `admin123` / Caixa: `caixa123` |
| Vendas do Bairro | Free | `admin3` | `caixa3` | Admin: `admin123` / Caixa: `caixa123` |
| Mercado Popular | Free | `admin4` | `caixa4` | Admin: `admin123` / Caixa: `caixa123` |
| Mini-Mercado Sucata | Free | `admin5` | `caixa5` | Admin: `admin123` / Caixa: `caixa123` |

---

## 🏗️ Arquitetura de Sincronização

A engine de sincronia funciona lendo uma `SyncQueue` local que rastreia os `sync_uuid` das tabelas alteradas. Um comando Flask (`flask push-to-aiven`) executa um script customizado (`scripts/force_sync_to_aiven.py`) que usa um UPSERT (`ON CONFLICT (id) DO UPDATE...`) ultra-rápido via Psycopg2 para empurrar as alterações em "Lotes" (Batch) para a nuvem.

---

## 👨‍💻 Autor

Criado e mantido com dedicação e muito código amazônico por **Rafael Maldivas**.  
📍 *Manaus, Amazonas, Brasil*

💼 **Conecte-se comigo:**  
*   [LinkedIn](https://www.linkedin.com/in/rafael-maldivas/) (Adicione seu link real aqui se desejar)
*   **Portfólio & Contato:** rafaelmaldivas@gmail.com

---
*Este projeto é uma demonstração de arquitetura de software de nível sênior, abordando desafios logísticos, concorrência de banco de dados, multi-tenancy e performance em edge-computing.*
