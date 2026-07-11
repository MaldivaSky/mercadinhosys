# Implementação do Módulo Consultor Inteligente (IA) - DNA IA Ubíqua

Este plano de implementação foi atualizado para acomodar a nova visão do sistema: a IA deve estar presente no DNA de todos os módulos. Além da interface de chat do Consultor, teremos **Cards de Insights Inteligentes** distribuídos pelo Dashboard, Vendas, Funcionários, Despesas, Produtos, RH, Compras & Doca e Fornecedores.

## Proposed Changes

### 1. Fundações e Integração de LLM (Backend)
- Inserção da `GEMINI_API_KEY=[CHAVE_GEMINI_REMOVIDA]` e modelo no `.env` e `.env.example`.
- Criação de `backend/app/utils/llm_client.py` com lógica multi-provedor (Gemini + Groq fallback).
- Refatoração de `backend/app/utils/ia_copiloto.py` utilizando o novo cliente.
- Criação do modelo `ConsultorInteracao` (`models.py`) e migração Alembic para auditoria e log.

### 2. Context Builders e Especialistas
A arquitetura extrairá métricas *anonimizadas* e *determinísticas* para o LLM. Serão implementados os contextos:
- **Financeiro / Despesas** (Alta prioridade)
- **Estoque / Produtos** (Alta prioridade)
- **Vendas**
- **RH / Funcionários**
- **Compras / Doca / Fornecedores**
- **Geral (Dashboard)**

Será configurado `backend/app/services/consultor/prompts.py` e `roteador.py`.

### 3. Nova Rota de Insights e Limite de Atualização
- `GET /api/consultor/insight?modulo=<nome_do_modulo>&refresh=<bool>`
  - Retorna uma dica proativa de até 100 palavras.
  - Possui um limite de **5 requisições manuais de refresh por dia** por estabelecimento (utilizando lógica central de quota e cache diário). 
  - Consultas sem `refresh=true` consumirão o último cache do dia sem gastar cota adicional, garantindo resposta ultra-rápida na navegação de abas.

### 4. Interface Central de Chat (Frontend)
- Criação do `ConsultorPage.tsx` e seus sub-componentes (`MensagemBubble`, `SugestoesChips`, `EspecialistaBadge`, `DadosReferencia`).
- Integração no menu lateral da aplicação para perfis de gerência e admin.

### 5. InsightCards nos Módulos (Frontend)
- **Componente Reutilizável**: `InsightCard.tsx`
  - Um card moderno, expansível e visualmente premium.
  - Botão de "Atualizar Insight" com contador informando as atualizações restantes (ex: "3/5 atualizações diárias").
  - Skeleton de loading elegante durante a comunicação com a API.
- **Implementação em Páginas**:
  - `DashboardPage` (Visão geral de saúde do negócio)
  - `DespesasPage` (Foco em onde cortar custos / alertas financeiros)
  - `ProdutosPage` (Foco em validade, itens parados e curva ABC)
  - `VendasPage` (Foco em pico de vendas, ticket médio e comissões)
  - `FuncionariosPage` / `RHPage` (Custo de folha, atestados)
  - `ComprasPage` / `FornecedoresPage` (Prazo médio e necessidade de reposição)

## Verification Plan

### Automated Tests
- Validação das rotas `/api/consultor/chat` e `/api/consultor/insight`.
- Teste rigoroso do bloqueio de quota para garantir que o 6º *refresh* no mesmo dia retorne HTTP 429 Too Many Requests (proteção contra abuso).
- Suíte `pytest backend/tests/` certificando ausência de regressões no backend atual.

### Manual Verification
- Iniciar o frontend localmente e navegar entre **todas as telas solicitadas**, verificando se o `InsightCard` aparece, carrega rapidamente o dado do cache, e se o botão "Atualizar" funciona até atingir o limite imposto.
- Validar se a resposta contém apenas as informações daquele domínio (ex: insights de Produtos não devem misturar dados de ponto eletrônico do RH).
- Testar a central do Consultor em paralelo, engajando no bate-papo de formato mais longo.
