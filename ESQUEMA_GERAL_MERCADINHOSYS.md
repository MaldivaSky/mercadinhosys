# ESQUEMA GERAL DETALHADO — MERCADINHOSYS

## BACKEND (Flask)

### Estrutura principal
- backend/
  - app/
    - models.py — Modelos do banco (ORM SQLAlchemy)
    - routes/
      - clientes.py — Endpoints CRUD e analytics de clientes
    - ... (outros módulos: produtos, vendas, despesas, etc)
  - config.py — Configuração Flask
  - run.py — Inicialização do servidor
  - requirements.txt — Dependências Python
  - migrations/ — Migrações Alembic

### Arquivo: app/models.py
- **class Cliente(db.Model):**
  - id, nome, email, telefone, cpf, data_nascimento, dia_vencimento, limite_credito, status, etc.
  - def to_dict(self): retorna dict serializável do cliente
- Outras classes: Estabelecimento, Funcionario, Fornecedor, Produto, Venda, VendaItem, MovimentacaoEstoque, Despesa, LoginHistory, DashboardMetrica, RelatorioAgendado, AnalisePreditiva

### Arquivo: app/routes/clientes.py
- **Blueprint:** clientes_bp (prefixo /api/clientes)
- **Funções principais:**
  - curva_compras() — GET /curva_compras — Curva de compras dos clientes
  - listar_clientes() — GET / — Lista todos os clientes
  - detalhes_cliente(id) — GET /<id> — Detalhes de um cliente
  - atualizar_cliente(id) — PUT /<id> — Atualiza cliente
  - compras_cliente(id) — GET /<id>/compras — Compras do cliente
  - buscar_clientes() — GET /buscar — Busca avançada
  - estatisticas_clientes() — GET /estatisticas — Métricas/analytics
  - exportar_clientes() — GET /exportar — Exporta clientes (CSV/Excel)

#### Exemplo de fluxo CRUD:
- GET /api/clientes/ — lista clientes
- GET /api/clientes/<id> — detalhes
- POST /api/clientes — cria
- PUT /api/clientes/<id> — atualiza
- DELETE /api/clientes/<id> — remove

### Observações Backend
- Todos os endpoints usam SQLAlchemy e retornam JSON.
- Analytics e estatísticas disponíveis em endpoints extras.
- Modelos e campos devem estar sincronizados com frontend.

---

## FRONTEND (React + TS + MUI)

### Estrutura principal
- frontend/mercadinhosys-frontend/src/features/customers/
  - CustomersPage.tsx — Página principal de clientes
  - customerService.ts — Abstração de chamadas API
  - components/
    - CustomerTable.tsx — Tabela de clientes
    - CustomerForm.tsx — Formulário de cadastro/edição
    - CustomerDetailsModal.tsx — Modal de detalhes/ações
    - CustomerDashboard.tsx — Métricas/analytics
    - inputMasks.ts — Máscaras de input

### Arquivo: CustomersPage.tsx
- **Componente principal:** CustomersPage
- **Hooks:**
  - useState: clientes, loading, formOpen, editData, selectedCliente, clienteDetalhado, detalheLoading, snackbar, dashboard
  - useEffect: carrega clientes e dashboard
- **Funções:**
  - fetchDashboard — busca métricas
  - fetchClientes — busca lista
  - handleAdd, handleEdit, handleRowClick, handleDelete, handleSave — ações CRUD
- **Fluxo:**
  - Renderiza tabela, dashboard, modais de detalhes e formulário

### Arquivo: customerService.ts
- **Objeto:** customerService
  - list() — GET /clientes
  - create(cliente) — POST /clientes
  - update(id, cliente) — PUT /clientes/<id>
  - delete(id) — DELETE /clientes/<id>
- Usa apiClient (Axios) para requisições

### components/CustomerTable.tsx
- **Componente:** CustomerTable
  - Props: clientes, loading, onRowClick
  - Renderiza tabela de clientes

### components/CustomerForm.tsx
- **Componente:** CustomerForm
  - Props: open, onClose, onSave, initialData, loading
  - useState: form (dados do cliente)
  - handleChange, handleSubmit — manipulação de formulário

### components/CustomerDetailsModal.tsx
- **Componente:** CustomerDetailsModal
  - Props: open, cliente, loading, onClose, onEdit, onDelete
  - Exibe detalhes e ações do cliente

### Observações Frontend
- Integração direta com backend via customerService
- Tipos/props devem refletir campos do modelo Cliente
- Dashboard e analytics consomem endpoints específicos

---

## INTEGRAÇÃO E PONTOS CRÍTICOS
- Campos obrigatórios: nome, email, telefone, cpf, status, data_nascimento, dia_vencimento, limite_credito
- Sincronizar nomes/campos entre backend e frontend
- Tratar valores None/null para campos opcionais
- Testar todos os fluxos CRUD e analytics
- Para adicionar campos: alterar models.py, rodar migração, ajustar frontend

---

## RESUMO RÁPIDO PARA IA/DEV
- CRUD de clientes: backend/app/routes/clientes.py + frontend/src/features/customers/
- Modelos: backend/app/models.py
- API: /api/clientes/ (GET, POST, PUT, DELETE)
- Frontend: CustomersPage.tsx (página), CustomerTable.tsx (tabela), CustomerForm.tsx (form), CustomerDetailsModal.tsx (modal), customerService.ts (API)
- Analytics: endpoints extras + CustomerDashboard.tsx

Se precisar detalhamento de outros módulos (produtos, vendas, etc), ou exemplos de payloads, peça explicitamente.