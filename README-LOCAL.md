# MercadinhoSys - Guia de Execução Local (Amazon Digital Twin)

## 🚀 Início Rápido (Ambiente de Alta Performance)

O MercadinhoSys foi arquitetado para rodar com perfeição localmente, utilizando um banco de dados SQLite de alta performance como Gêmeo Digital (Digital Twin) do ecossistema de produção (Aiven PostgreSQL). Este modelo "Local-First" previne problemas com pastas sincronizadas em nuvem (OneDrive) e garante estabilidade da simulação.

### Executar o Ecossistema Completo

```powershell
# Este script inicia tanto o Backend quanto o Frontend
.\start-local.ps1
```

Acessos automáticos nas portas padrão:
- **Painel Gerencial (Frontend)**: http://localhost:5173
- **API Core (Backend)**: http://localhost:5000

---

## 🔑 Credenciais Multi-Tenant (Simulação de 6 Meses)

A simulação mestre cria um universo hierárquico com **5 cenários corporativos reais**, desde mercados de elite até negócios em dificuldade.

| Tenant / Cenário | Plano de Assinatura | Owner (Dono) | Operador (Caixa) | Senha Padrão (Admin / Caixa) |
| :--- | :--- | :--- | :--- | :--- |
| **MercadinhoSys HQ** | Master SAAS | `admin_saas` | *N/A* | *(Acesso privado via .env)* |
| Mercado Maldivas Elite | **Pro** | `admin1` | `caixa1` | `admin123` / `caixa123` |
| Supermercado Estrela | **Pro** | `admin2` | `caixa2` | `admin123` / `caixa123` |
| Vendas do Bairro | Free | `admin3` | `caixa3` | `admin123` / `caixa123` |
| Mercado Popular | Free | `admin4` | `caixa4` | `admin123` / `caixa123` |
| Mini-Mercado Sucata | Free | `admin5` | `caixa5` | `admin123` / `caixa123` |

---

## 📊 O Motor Científico (Data Seeding)

Ao executar a inicialização pela primeira vez, o motor `seed_simulation_master.py` cria o ambiente:

*   Mais de **10.000 transações de venda** retroativas.
*   **Gestão Logística Complexa** (Funcionalidade Delivery Unificada).
*   Catálogo vivo com EANs reais e validação de Lote (Estoque FIFO e Classificação ABC).
*   **Eventos de RH** (Pontos, Férias, Benefícios).
*   Simulação profunda baseada em **DNA Organizacional** (Velocidade de giro, índice de inadimplência e margem de lucro).

---

## 🌍 Arquitetura Híbrida & Push-to-Cloud

Desenvolvido para resiliência no extremo norte do Brasil (Manaus/Amazonas), o sistema lida de forma autônoma com conectividade instável.

*   Todas as operações rodam localmente (SQLite).
*   Todas as tabelas possuem `sync_uuid` e rastreio de Timestamp (`updated_at`).
*   **Para sincronizar com a Nuvem (Aiven PostgreSQL):**
    ```powershell
    cd backend
    flask push-to-aiven
    ```

---

## 🔧 Ferramentas e Diagnósticos

Na pasta do Backend, você encontrará scripts utilitários focados em DevOps e administração de banco de dados:

*   `seed_simulation_master.py`: Orquestrador completo do Gêmeo Digital.
*   `compare_schemas.py`: Utilitário para auditoria de schemas (Local vs Nuvem).
*   `check_sales.py`: Profiling do motor de vendas e entregas.

## 🐛 Troubleshooting

Se precisar "resetar" a simulação completa para o dia zero:

```powershell
cd backend
Remove-Item .\instance\mercadinho.db -Force
python seed_simulation_master.py
```
Isso destruirá e recriará perfeitamente o universo simulado e o HQ SaaS.

---
*MercadinhoSys: ERP Industrial da Amazônia para o Mundo.*
