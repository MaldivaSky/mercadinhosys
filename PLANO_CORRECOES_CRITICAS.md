# 🔧 PLANO DE CORREÇÕES CRÍTICAS
## Roadmap Detalhado para Entrega ao Cliente

---

## 🎯 OBJETIVO FINAL

Entregar um sistema **100% funcional** com:
- ✅ Dashboard com TODAS as métricas funcionando
- ✅ Vendas com múltiplas formas de pagamento
- ✅ Interface de delivery profissional
- ✅ Seed com dados realistas (múltiplos pagamentos)
- ✅ Novo cliente consegue usar o sistema do zero

---

## 📋 TAREFAS CRÍTICAS

### TAREFA 1: Dashboard - Renderização Completa
**Prioridade:** 🔴 CRÍTICA  
**Tempo Estimado:** 4-6 horas  
**Responsável:** Frontend Senior

#### 1.1 Diagnosticar Problema
```bash
# Verificar o que o backend retorna
curl -H "Authorization: Bearer <token>" \
  http://localhost:5000/api/dashboard/cientifico?days=30

# Comparar com o que o frontend espera
# Arquivo: frontend/mercadinhosys-frontend/src/features/dashboard/DashboardPage.tsx
# Linha: ~720 (onde começa o mapeamento de dados)
```

#### 1.2 Implementar Renderização
- [ ] Seção "Visão Geral" - KPIs principais
- [ ] Seção "Análise Detalhada" - Curva ABC, RFM
- [ ] Seção "Análise Temporal" - Gráficos de tendência
- [ ] Seção "Insights Científicos" - Anomalias e recomendações
- [ ] Seção "RH" - Métricas de funcionários
- [ ] Seção "Fiados" - Contas a receber

#### 1.3 Implementar Modais
- [ ] Modal de Produto Estrela (detalhes)
- [ ] Modal de Produto Lento (análise)
- [ ] Modal de Anomalia (causa e ação)
- [ ] Modal de Correlação (análise bivariada)
- [ ] Modal de Recomendação (impacto)

#### 1.4 Testar
- [ ] Carregar dashboard com 30 dias
- [ ] Carregar dashboard com 90 dias
- [ ] Filtrar por período personalizado
- [ ] Clicar em cada modal
- [ ] Verificar se dados estão corretos

---

### TAREFA 2: Múltiplos Pagamentos - Completar Backend
**Prioridade:** 🔴 CRÍTICA  
**Tempo Estimado:** 3-4 horas  
**Responsável:** Backend Senior

#### 2.1 Completar `finalizar_venda()` em pdv.py
**Arquivo:** `backend/app/routes/pdv.py` (linha ~747, incompleto)

```python
# O que falta:
# 1. Criar registros em Pagamento (um por forma de pagamento)
# 2. Validar que soma dos pagamentos = total da venda
# 3. Atualizar saldo de cliente se fiado
# 4. Registrar na SyncQueue se offline
# 5. Retornar venda criada

# Pseudocódigo:
def finalizar_venda():
    # ... código existente ...
    
    # 1. Criar registros de pagamento
    for pagamento_data in data.get("pagamentos", []):
        pagamento = Pagamento(
            venda_id=nova_venda.id,
            forma_pagamento=pagamento_data['forma'],
            valor=pagamento_data['valor'],
            referencia=pagamento_data.get('referencia'),
            data_pagamento=data_venda
        )
        db.session.add(pagamento)
    
    # 2. Se fiado, criar ContaReceber
    if any(p['forma'] == 'fiado' for p in data.get("pagamentos", [])):
        valor_fiado = sum(p['valor'] for p in data.get("pagamentos", []) if p['forma'] == 'fiado')
        data_vencimento = data.get("data_vencimento_fiado") or (data_venda + timedelta(days=30))
        
        conta = ContaReceber(
            cliente_id=cliente_id,
            venda_id=nova_venda.id,
            valor=valor_fiado,
            data_vencimento=data_vencimento,
            status="aberta"
        )
        db.session.add(conta)
    
    # 3. Atualizar estoque
    for item in items:
        produto = Produto.query.get(item['produto_id'])
        produto.quantidade -= item['quantidade']
        
        movimentacao = MovimentacaoEstoque(
            produto_id=item['produto_id'],
            tipo="saida",
            quantidade=item['quantidade'],
            venda_id=nova_venda.id
        )
        db.session.add(movimentacao)
    
    # 4. Commit atômico
    db.session.commit()
    
    return jsonify({
        "success": True,
        "venda": nova_venda.to_dict()
    }), 201
```

#### 2.2 Testar Fluxo Completo
- [ ] Venda com 1 forma de pagamento (dinheiro)
- [ ] Venda com 2 formas (dinheiro + cartão)
- [ ] Venda com fiado
- [ ] Venda com múltiplos pagamentos + fiado
- [ ] Verificar se estoque foi atualizado
- [ ] Verificar se ContaReceber foi criada

---

### TAREFA 3: Múltiplos Pagamentos - Atualizar Seed
**Prioridade:** 🔴 CRÍTICA  
**Tempo Estimado:** 2-3 horas  
**Responsável:** Backend Senior

#### 3.1 Modificar `seed_simulation_master.py`
**Arquivo:** `backend/seed_simulation_master.py`

```python
# Adicionar ao MasterSeeder:

def criar_vendas_com_multiplos_pagamentos(self, estabelecimento_id, mes):
    """Cria vendas com múltiplas formas de pagamento"""
    
    # 30% das vendas: múltiplos pagamentos
    for i in range(10):  # 10 vendas por mês
        cliente = random.choice(self.clientes)
        funcionario = random.choice(self.funcionarios)
        
        # Selecionar 2-3 formas de pagamento
        formas = random.sample(['dinheiro', 'cartao_credito', 'pix', 'fiado'], k=random.randint(2, 3))
        
        # Criar venda
        venda = Venda(
            codigo=f"V-{mes}-{i:04d}",
            estabelecimento_id=estabelecimento_id,
            cliente_id=cliente.id,
            funcionario_id=funcionario.id,
            total=Decimal(random.uniform(100, 500)),
            status="finalizada",
            data_venda=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 30))
        )
        db.session.add(venda)
        db.session.flush()
        
        # Criar pagamentos
        total_restante = venda.total
        for forma in formas[:-1]:
            valor = Decimal(str(round(total_restante * random.uniform(0.3, 0.6), 2)))
            pagamento = Pagamento(
                venda_id=venda.id,
                forma_pagamento=forma,
                valor=valor
            )
            db.session.add(pagamento)
            total_restante -= valor
        
        # Último pagamento pega o restante
        pagamento = Pagamento(
            venda_id=venda.id,
            forma_pagamento=formas[-1],
            valor=total_restante
        )
        db.session.add(pagamento)
        
        # Se fiado, criar ContaReceber
        if 'fiado' in formas:
            valor_fiado = sum(p.valor for p in venda.pagamentos if p.forma_pagamento == 'fiado')
            conta = ContaReceber(
                cliente_id=cliente.id,
                venda_id=venda.id,
                valor=valor_fiado,
                data_vencimento=venda.data_venda + timedelta(days=30),
                status="aberta"
            )
            db.session.add(conta)
    
    db.session.commit()
```

#### 3.2 Testar Seed
```bash
# Executar seed
python backend/seed_simulation_master.py

# Verificar se vendas foram criadas com múltiplos pagamentos
sqlite3 backend/instance/mercadinho_local.db \
  "SELECT v.id, COUNT(p.id) as num_pagamentos FROM vendas v LEFT JOIN pagamentos p ON v.id = p.venda_id GROUP BY v.id HAVING COUNT(p.id) > 1 LIMIT 5;"
```

---

### TAREFA 4: Delivery - Interface Profissional
**Prioridade:** 🟠 ALTA  
**Tempo Estimado:** 5-6 horas  
**Responsável:** Frontend Senior

#### 4.1 Estrutura de Componentes
```
frontend/mercadinhosys-frontend/src/features/delivery/
├── DeliveryPage.tsx              # Página principal
├── components/
│   ├── DeliveryList.tsx          # Listagem de entregas
│   ├── DeliveryForm.tsx          # Criar/editar entrega
│   ├── DeliveryMap.tsx           # Mapa com rastreamento
│   ├── DriverManagement.tsx      # Gestão de motoristas
│   ├── VehicleManagement.tsx     # Gestão de veículos
│   ├── DeliveryStatus.tsx        # Status da entrega
│   └── DeliveryMetrics.tsx       # Métricas de delivery
└── deliveryService.ts            # API client
```

#### 4.2 Implementar DeliveryPage
```typescript
// Estrutura básica
const DeliveryPage: React.FC = () => {
  const [entregas, setEntregas] = useState([]);
  const [filtro, setFiltro] = useState('pendente');
  const [modalAberto, setModalAberto] = useState(false);
  
  useEffect(() => {
    carregarEntregas();
  }, [filtro]);
  
  const carregarEntregas = async () => {
    const resp = await apiClient.get('/delivery/entregas', {
      params: { status: filtro }
    });
    setEntregas(resp.data.entregas);
  };
  
  return (
    <div className="p-6">
      <h1>Gestão de Entregas</h1>
      
      {/* Filtros */}
      <div className="flex gap-4 mb-6">
        <button onClick={() => setFiltro('pendente')}>Pendentes</button>
        <button onClick={() => setFiltro('em_rota')}>Em Rota</button>
        <button onClick={() => setFiltro('entregue')}>Entregues</button>
      </div>
      
      {/* Listagem */}
      <DeliveryList entregas={entregas} />
      
      {/* Modal de Criar */}
      {modalAberto && <DeliveryForm onClose={() => setModalAberto(false)} />}
    </div>
  );
};
```

#### 4.3 Integrar com Backend
- [ ] GET `/delivery/entregas` - Listar entregas
- [ ] POST `/delivery/entregas` - Criar entrega
- [ ] PUT `/delivery/entregas/{id}` - Atualizar status
- [ ] GET `/delivery/motoristas` - Listar motoristas
- [ ] POST `/delivery/motoristas` - Criar motorista
- [ ] GET `/delivery/rastreamento/{id}` - Rastreamento em tempo real

#### 4.4 Testar
- [ ] Criar entrega
- [ ] Atualizar status
- [ ] Visualizar rastreamento
- [ ] Listar motoristas
- [ ] Criar motorista

---

### TAREFA 5: Novo Cliente - Fluxo Completo
**Prioridade:** 🟠 ALTA  
**Tempo Estimado:** 2-3 horas  
**Responsável:** QA

#### 5.1 Teste de Onboarding
```
1. Acessar http://localhost
2. Clicar em "Registrar"
3. Preencher dados:
   - Email: novo@cliente.com
   - Senha: Senha123!
   - Nome Estabelecimento: Meu Mercado
   - CNPJ: 12.345.678/0001-90
4. Confirmar email (se necessário)
5. Fazer login
6. Criar primeiro cliente
7. Criar primeiro produto
8. Fazer primeira venda
9. Visualizar dashboard
```

#### 5.2 Checklist
- [ ] Registro funciona
- [ ] Login funciona
- [ ] Dashboard carrega
- [ ] PDV funciona
- [ ] Pode criar cliente
- [ ] Pode criar produto
- [ ] Pode fazer venda
- [ ] Pode visualizar relatórios

---

## 🔄 FLUXO DE TRABALHO

### Dia 1: Manhã
- [ ] Tarefa 1.1 - Diagnosticar dashboard
- [ ] Tarefa 2.1 - Completar finalizar_venda()

### Dia 1: Tarde
- [ ] Tarefa 1.2 - Implementar renderização
- [ ] Tarefa 2.2 - Testar múltiplos pagamentos

### Dia 2: Manhã
- [ ] Tarefa 1.3 - Implementar modais
- [ ] Tarefa 3.1 - Modificar seed

### Dia 2: Tarde
- [ ] Tarefa 1.4 - Testar dashboard
- [ ] Tarefa 3.2 - Testar seed

### Dia 3: Manhã
- [ ] Tarefa 4.1 - Estrutura delivery
- [ ] Tarefa 4.2 - Implementar DeliveryPage

### Dia 3: Tarde
- [ ] Tarefa 4.3 - Integrar com backend
- [ ] Tarefa 4.4 - Testar delivery

### Dia 4: Manhã
- [ ] Tarefa 5.1 - Teste de onboarding
- [ ] Correções finais

### Dia 4: Tarde
- [ ] Deploy em staging
- [ ] Testes finais
- [ ] Deploy em produção

---

## 📊 MÉTRICAS DE SUCESSO

| Métrica | Critério |
|---------|----------|
| Dashboard | Todas as 6 seções renderizando |
| Múltiplos Pagamentos | Venda com 3+ formas funciona |
| Delivery | Criar, atualizar, rastrear funciona |
| Seed | 100+ vendas com múltiplos pagamentos |
| Novo Cliente | Consegue fazer venda completa |
| Performance | Dashboard carrega em < 2s |
| Uptime | 99.9% em 24h |

---

## 🚨 RISCOS E MITIGAÇÕES

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|--------|-----------|
| Dashboard lento | Média | Alto | Adicionar índices, cache |
| Múltiplos pagamentos com bug | Média | Alto | Testes automatizados |
| Delivery não integra | Baixa | Alto | Testes E2E |
| Seed não funciona | Baixa | Médio | Testes unitários |
| Novo cliente não consegue usar | Baixa | Crítico | Teste de onboarding |

---

## 📞 ESCALAÇÃO

Se encontrar bloqueios:
1. Documentar o problema
2. Criar issue no GitHub
3. Notificar o CTO
4. Propor solução alternativa

---

**Status:** 🔴 PRONTO PARA INICIAR  
**Próximo Passo:** Começar Tarefa 1.1
