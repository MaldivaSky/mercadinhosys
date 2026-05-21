# 🧪 GUIA DE TESTE RÁPIDO
## Como Validar o Sistema Antes da Entrega

---

## 🚀 SETUP INICIAL (5 minutos)

### 1. Iniciar Docker
```bash
cd mercadinhosys
docker-compose up -d
```

### 2. Aguardar Inicialização
```bash
# Verificar se backend está pronto
curl http://localhost:5000/api/dashboard/status

# Verificar se frontend está pronto
curl http://localhost
```

### 3. Acessar Sistema
- Frontend: http://localhost
- Backend: http://localhost:5000
- Banco de dados: localhost:5432

---

## 👤 LOGIN PADRÃO

```
Email: admin@mercadinho.com
Senha: admin123
```

Se não funcionar, executar seed:
```bash
docker exec mercadinhosys-backend python backend/seed_super_admin.py
```

---

## ✅ TESTE 1: NOVO CLIENTE (15 minutos)

### Objetivo
Validar que um novo cliente consegue usar o sistema do zero.

### Passos
1. Acessar http://localhost
2. Clicar em "Registrar"
3. Preencher:
   - Email: `teste@novo.com`
   - Senha: `Teste123!`
   - Nome Estabelecimento: `Mercado Teste`
   - CNPJ: `12.345.678/0001-90`
4. Confirmar email (se necessário)
5. Fazer login com novo usuário
6. Verificar se dashboard carrega

### Resultado Esperado
✅ Novo cliente consegue fazer login e ver dashboard

---

## ✅ TESTE 2: CRIAR CLIENTE (10 minutos)

### Objetivo
Validar fluxo de criação de cliente.

### Passos
1. Ir para "Clientes"
2. Clicar em "Novo Cliente"
3. Preencher:
   - Nome: `João Silva`
   - CPF: `123.456.789-00`
   - Email: `joao@email.com`
   - Telefone: `(92) 98765-4321`
   - Endereço: `Rua A, 123`
4. Salvar

### Resultado Esperado
✅ Cliente criado com sucesso e aparece na listagem

---

## ✅ TESTE 3: CRIAR PRODUTO (10 minutos)

### Objetivo
Validar fluxo de criação de produto.

### Passos
1. Ir para "Produtos"
2. Clicar em "Novo Produto"
3. Preencher:
   - Nome: `Arroz 5kg`
   - Código de Barras: `1234567890123`
   - Preço de Custo: `R$ 15,00`
   - Preço de Venda: `R$ 25,00`
   - Quantidade: `100`
   - Categoria: `Alimentos`
4. Salvar

### Resultado Esperado
✅ Produto criado e aparece na listagem

---

## ✅ TESTE 4: VENDA SIMPLES (15 minutos)

### Objetivo
Validar fluxo de venda com 1 forma de pagamento.

### Passos
1. Ir para "PDV"
2. Buscar produto: `Arroz`
3. Adicionar ao carrinho (quantidade: 2)
4. Clicar em "Pagar"
5. Selecionar cliente: `João Silva`
6. Selecionar forma de pagamento: `Dinheiro`
7. Valor recebido: `R$ 60,00`
8. Clicar em "Concluir Venda"

### Resultado Esperado
✅ Venda finalizada com sucesso
✅ Cupom fiscal gerado
✅ Estoque atualizado (100 → 98)

---

## ✅ TESTE 5: MÚLTIPLOS PAGAMENTOS (20 minutos)

### Objetivo
Validar fluxo de venda com 2+ formas de pagamento.

### Passos
1. Ir para "PDV"
2. Buscar produto: `Arroz`
3. Adicionar ao carrinho (quantidade: 3)
4. Clicar em "Pagar"
5. Selecionar cliente: `João Silva`
6. Adicionar forma de pagamento 1: `Dinheiro` - `R$ 30,00`
7. Adicionar forma de pagamento 2: `Cartão de Crédito` - `R$ 45,00`
8. Clicar em "Concluir Venda"

### Resultado Esperado
✅ Venda finalizada com múltiplos pagamentos
✅ Cupom mostra ambas as formas
✅ Estoque atualizado corretamente

---

## ✅ TESTE 6: FIADO (20 minutos)

### Objetivo
Validar fluxo de venda com fiado.

### Passos
1. Ir para "PDV"
2. Buscar produto: `Arroz`
3. Adicionar ao carrinho (quantidade: 2)
4. Clicar em "Pagar"
5. Selecionar cliente: `João Silva`
6. Adicionar forma de pagamento: `Fiado`
7. Valor: `R$ 50,00`
8. Data de vencimento: `30/05/2026`
9. Clicar em "Concluir Venda"

### Resultado Esperado
✅ Venda finalizada com fiado
✅ Conta a receber criada
✅ Saldo devedor do cliente atualizado

---

## ✅ TESTE 7: DASHBOARD (15 minutos)

### Objetivo
Validar que dashboard renderiza todas as métricas.

### Passos
1. Ir para "Dashboard"
2. Verificar seções:
   - [ ] Visão Geral (KPIs)
   - [ ] Análise Detalhada (Curva ABC)
   - [ ] Análise Temporal (Gráficos)
   - [ ] Insights Científicos (Anomalias)
   - [ ] RH (Métricas de funcionários)
   - [ ] Fiados (Contas a receber)
3. Clicar em cada modal para verificar detalhes

### Resultado Esperado
✅ Todas as 6 seções renderizam
✅ Gráficos carregam corretamente
✅ Modais abrem e mostram dados

---

## ✅ TESTE 8: DELIVERY (20 minutos)

### Objetivo
Validar fluxo básico de delivery.

### Passos
1. Ir para "Delivery"
2. Clicar em "Nova Entrega"
3. Selecionar venda anterior
4. Selecionar motorista
5. Selecionar veículo
6. Clicar em "Criar Entrega"
7. Atualizar status para "Em Rota"
8. Atualizar status para "Entregue"

### Resultado Esperado
✅ Entrega criada com sucesso
✅ Status atualizado corretamente
✅ Rastreamento funciona

---

## ✅ TESTE 9: RELATÓRIOS (15 minutos)

### Objetivo
Validar que relatórios carregam corretamente.

### Passos
1. Ir para "Relatórios"
2. Selecionar período: `Últimos 30 dias`
3. Clicar em "Gerar Relatório"
4. Verificar dados:
   - [ ] Total de vendas
   - [ ] Total de clientes
   - [ ] Produtos mais vendidos
   - [ ] Formas de pagamento

### Resultado Esperado
✅ Relatório gerado com dados corretos
✅ Pode exportar para PDF/Excel

---

## ✅ TESTE 10: PERFORMANCE (10 minutos)

### Objetivo
Validar que sistema responde rápido.

### Passos
1. Abrir DevTools (F12)
2. Ir para "Network"
3. Ir para "Dashboard"
4. Verificar tempo de carregamento

### Resultado Esperado
✅ Dashboard carrega em < 2 segundos
✅ Nenhuma requisição com erro
✅ Sem memory leaks

---

## 🐛 TESTE 11: TRATAMENTO DE ERROS (10 minutos)

### Objetivo
Validar que erros são tratados corretamente.

### Passos
1. Tentar criar venda sem cliente (se obrigatório)
2. Tentar criar venda sem produtos
3. Tentar criar venda com estoque insuficiente
4. Tentar fazer login com senha errada
5. Tentar acessar página sem permissão

### Resultado Esperado
✅ Mensagens de erro claras
✅ Usuário sabe o que fazer
✅ Sem crashes ou 500 errors

---

## 📊 CHECKLIST FINAL

### Funcionalidades
- [ ] Novo cliente consegue usar
- [ ] Criar cliente funciona
- [ ] Criar produto funciona
- [ ] Venda simples funciona
- [ ] Múltiplos pagamentos funciona
- [ ] Fiado funciona
- [ ] Dashboard completo
- [ ] Delivery funciona
- [ ] Relatórios funcionam
- [ ] Performance OK

### Qualidade
- [ ] Sem erros no console
- [ ] Sem memory leaks
- [ ] Sem crashes
- [ ] Mensagens de erro claras
- [ ] Responsivo em mobile

### Segurança
- [ ] Não consegue acessar sem login
- [ ] Não consegue acessar dados de outro tenant
- [ ] Senhas são hasheadas
- [ ] JWT funciona

---

## 🚨 PROBLEMAS COMUNS

### Dashboard não carrega
```bash
# Verificar se backend está respondendo
curl http://localhost:5000/api/dashboard/cientifico?days=30

# Se retornar erro, verificar logs
docker logs mercadinhosys-backend
```

### Múltiplos pagamentos não funciona
```bash
# Verificar se tabela Pagamento existe
docker exec mercadinhosys-db psql -U mercadinho_user -d mercadinhosys -c "\dt pagamentos"

# Se não existir, executar migration
docker exec mercadinhosys-backend flask db upgrade
```

### Delivery não aparece
```bash
# Verificar se rota existe
curl http://localhost:5000/api/delivery/entregas

# Se retornar 404, verificar se blueprint foi registrado
docker logs mercadinhosys-backend | grep delivery
```

---

## 📞 SUPORTE

Se encontrar problemas:
1. Verificar logs: `docker logs mercadinhosys-backend`
2. Verificar console do navegador (F12)
3. Abrir issue no GitHub
4. Contatar o time técnico

---

**Tempo Total de Testes:** ~2 horas  
**Status:** ✅ PRONTO PARA TESTAR
