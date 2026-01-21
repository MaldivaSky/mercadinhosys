# 🛒 MercadinhoSys - Sistema de Gestão para Pequenos Mercados

![Status do Projeto](https://img.shields.io/badge/Status-Em_Desenvolvimento-yellow)
![License](https://img.shields.io/badge/License-MIT-blue)

**MercadinhoSys** é uma solução completa de ERP (Enterprise Resource Planning) e PDV (Ponto de Venda) desenvolvida para facilitar a gestão de pequenos comércios. O sistema integra controle de estoque, frente de caixa, gestão financeira e análise de dados em uma interface web moderna e responsiva.

---

## 🚀 Tecnologias Utilizadas

O projeto foi construído utilizando uma arquitetura robusta, separando Backend e Frontend:

### Frontend (Client-Side)
* ![React](https://img.shields.io/badge/React-20232A?style=flat&logo=react&logoColor=61DAFB) **React.js (Vite)**: Para uma interface rápida e SPA (Single Page Application).
* ![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=flat&logo=typescript&logoColor=white) **TypeScript**: Tipagem estática para maior segurança e manutenibilidade.
* ![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=flat&logo=tailwind-css&logoColor=white) **Tailwind CSS**: Estilização moderna e responsiva.
* **Axios**: Para comunicação com a API.
* **Recharts**: Para visualização de dados nos dashboards.

### Backend (Server-Side)
* ![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white) **Python 3.12+**: Linguagem base.
* ![Flask](https://img.shields.io/badge/Flask-000000?style=flat&logo=flask&logoColor=white) **Flask**: Framework web leve e escalável.
* **SQLAlchemy**: ORM para abstração e manipulação do banco de dados.
* **Flask-JWT-Extended**: Autenticação segura via JSON Web Tokens.
* **SQLite**: Banco de dados relacional (ambiente de desenvolvimento).

---

## 📋 Funcionalidades Principais

### 🖥️ PDV (Ponto de Venda)
* **Frente de Caixa Ágil**: Interface otimizada para registro rápido de vendas.
* **Leitura de Código de Barras**: Integração para busca automática de produtos.
* **Carrinho de Compras**: Adição, remoção e alteração de quantidade em tempo real.
* **Finalização Flexível**: Suporte a múltiplos métodos de pagamento.

### 📊 Dashboard & Analytics
* **Visão Geral**: Cards com métricas vitais (Faturamento Diário, Ticket Médio, Total de Vendas).
* **Gráficos Interativos**: Evolução de vendas e despesas.
* **Relatórios**: Exportação de dados para análise gerencial.

### 📦 Gestão de Estoque
* **CRUD Completo**: Cadastro de produtos, fornecedores e categorias.
* **Alertas**: Monitoramento de estoque baixo.
* **Precificação**: Controle de custo e preço de venda.

### 👥 Gestão Administrativa
* **Controle de Acesso**: Níveis de permissão para Gerentes e Operadores de Caixa.
* **Financeiro**: Registro de despesas e fluxo de caixa.
* **Clientes**: Cadastro e histórico de compras para fidelização.

---

## 🔧 Como Executar o Projeto

Pré-requisitos: Tenha o **Node.js**, **Python** e **Git** instalados em sua máquina.

### 1. Configuração do Backend

```bash
# Clone o repositório
git clone [https://github.com/seu-usuario/mercadinhosys.git](https://github.com/seu-usuario/mercadinhosys.git)

# Acesse a pasta do backend
cd mercadinhosys/backend

# Crie um ambiente virtual
python -m venv venv

# Ative o ambiente virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instale as dependências
pip install -r requirements.txt

# Inicialize o banco de dados
python init_db.py

# Execute o servidor
python run.py
