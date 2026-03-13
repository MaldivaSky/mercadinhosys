# MercadinhoSys - Guia de Execução Local

## 🚀 Início Rápido

O MercadinhoSys está configurado para rodar localmente sem Docker, evitando problemas de caminho do OneDrive.

### Executar Sistema Local

```powershell
.\start-local.ps1
```

Isso iniciará:
- **Backend**: http://localhost:5000
- **Frontend**: http://localhost:5173

## 🔑 Credenciais de Acesso

| Usuário | Senha | Perfil |
|---------|--------|---------|
| maldivas | Mald1v@$ | Super Admin |
| rafael_owner | 123 | Owner |
| admin1 | 123 | Admin |
| caixa1 | 123 | Caixa |
| estoque1 | 123 | Estoquista |

## 📊 Dados do Sistema

O sistema foi populado com dados completos:

### Estabelecimentos
- **SUPERMERCADO ELITE CENTER** (próspero)
  - ~9.409 vendas (6 meses)
  - ~56.477 itens vendidos
  - Cenário: Crescimento 3%/mês

- **MERCADO ESTRELA DO NORTE** (dificuldade)
  - ~1.937 vendas (6 meses)
  - ~4.762 itens vendidos
  - Cenário: Declínio 5%/mês

### Produtos
- 128 produtos com EANs reais brasileiros
- 20 fornecedores reais brasileiros
- Categorias completas (Alimentos, Bebidas, Higiene, etc.)

## 🔧 Estrutura do Projeto

```
mercadinhosys/
├── backend/
│   ├── venv/                 # Ambiente virtual Python
│   ├── instance/             # Banco SQLite (33MB)
│   └── seed_main.py         # Script de dados
├── frontend/
│   └── mercadinhosys-frontend/
├── start-local.ps1          # Script de inicialização
└── README-LOCAL.md          # Este arquivo
```

## 🐛 Problemas Conhecidos

### Docker com OneDrive
O Docker ainda referencia caminhos antigos do OneDrive. Solução:
- Use o sistema local (recomendado)
- Ou limpe completamente o Docker e reconfigure

### Erros de Seed
Se precisar recriar o banco:
```powershell
cd backend
Remove-Item .\instance\mercadinho.db -Force
python seed_main.py
```

## 📝 Scripts Úteis

- `start-local.ps1` - Inicia backend e frontend
- `fix-docker-paths.ps1` - Limpa referências antigas do Docker

## 🌐 Acesso Web

Após iniciar, acesse:
- **Frontend**: http://localhost:5173
- **API Docs**: http://localhost:5000/api/health
- **Dashboard Científico**: http://localhost:5000/api/cientifico

## ✅ Status do Sistema

- ✅ Ambiente configurado
- ✅ Banco populado
- ✅ Backend Flask rodando
- ✅ Frontend Vite rodando
- ✅ Dados completos para demonstração
