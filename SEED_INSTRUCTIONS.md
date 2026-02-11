# Como Rodar o Seed Corretamente

## No Windows (CMD ou PowerShell)

### Opção 1: CMD
```cmd
cd backend
venv\Scripts\activate
python seed_test.py --reset --local
```

### Opção 2: PowerShell
```powershell
cd backend
.\venv\Scripts\Activate.ps1
python seed_test.py --reset --local
```

## O que o seed faz:

1. **Limpa o banco de dados** (--reset)
2. **Cria estabelecimento** com dados de teste
3. **Cria funcionários** (admin, gerente, caixa, estoque)
4. **Cria clientes** (50 clientes)
5. **Cria fornecedores** (20 fornecedores)
6. **Cria categorias de produtos** (Alimentos, Bebidas, Higiene, etc)
7. **Cria 200+ produtos** com preços realistas
8. **Cria 90 dias de vendas** com distribuição de Pareto (80/20)
9. **Cria pedidos de compra** com boletos
10. **Cria despesas** variadas
11. **Cria registros de ponto** para RH
12. **Cria métricas do dashboard**

## Credenciais de teste após seed:

- **Admin**: admin / admin123
- **Gerente**: gerente01 / 123456
- **Caixa**: caixa01 / 123456
- **Estoque**: estoque01 / 123456

## Verificar se funcionou:

Após rodar o seed, acesse:
- http://localhost:5000/api/produtos/estoque (lista produtos com margem_lucro calculada)
- Faça login com admin/admin123
- Vá para Products Page - deve mostrar produtos com vendas, margens e status críticos
