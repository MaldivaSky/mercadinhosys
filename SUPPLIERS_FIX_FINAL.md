# SUPPLIERS PAGE - FIX COMPLETO

## PROBLEMA IDENTIFICADO
CORS error bloqueando chamadas da API `/api/fornecedores` porque:
1. Backend usava `@login_required` (Flask-Login session-based) ao invés de JWT
2. Frontend envia JWT tokens mas backend esperava session cookies
3. CORS não estava configurado corretamente para aceitar headers Authorization

## CORREÇÕES APLICADAS

### 1. Backend - `backend/app/routes/fornecedores.py`
✅ Mudado de `@login_required` para `@funcionario_required` (JWT)
✅ Mudado de `current_user` para `get_jwt()` para pegar dados do token
✅ Removido prefixo duplicado `/api/fornecedores` das rotas (já está no blueprint)
✅ Adicionado `estabelecimento_id` via JWT em todas as rotas
✅ Atualizado validação para aceitar `estabelecimento_id` como parâmetro

**Rotas corrigidas:**
- `GET /api/fornecedores` - Listar fornecedores
- `GET /api/fornecedores/<id>` - Obter fornecedor específico
- `POST /api/fornecedores` - Criar fornecedor
- `PUT /api/fornecedores/<id>` - Atualizar fornecedor
- `PATCH /api/fornecedores/<id>/status` - Ativar/desativar
- `DELETE /api/fornecedores/<id>` - Excluir fornecedor
- `GET /api/fornecedores/busca` - Busca rápida
- `GET /api/fornecedores/estatisticas` - Estatísticas
- `GET /api/fornecedores/<id>/pedidos` - Pedidos do fornecedor
- `GET /api/fornecedores/exportar` - Exportar CSV/Excel
- `POST /api/fornecedores/importar` - Importar CSV
- `GET /api/fornecedores/relatorio/analitico` - Relatório analítico

### 2. Backend - `backend/app/__init__.py`
✅ Configurado CORS para aceitar todos os origins em desenvolvimento
✅ Adicionado suporte para headers Authorization
✅ Habilitado métodos GET, POST, PUT, PATCH, DELETE, OPTIONS

```python
CORS(app, 
     resources={r"/api/*": {"origins": "*"}},
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
)
```

### 3. Frontend - `frontend/mercadinhosys-frontend/src/features/suppliers/SuppliersPage.tsx`
✅ Removido parâmetro `ativo: 'true'` para carregar todos os fornecedores
✅ Adicionado console.log para debug da resposta da API
✅ Mapeamento correto dos campos do backend:
  - `nome_fantasia` → `nome`
  - `produtos_ativos` → `total_produtos`

## FORMATO DE RESPOSTA DO BACKEND

```json
{
  "success": true,
  "fornecedores": [
    {
      "id": 1,
      "nome_fantasia": "Distribuidora ABC",
      "razao_social": "ABC Distribuidora LTDA",
      "cnpj": "12.345.678/0001-90",
      "telefone": "(11) 98765-4321",
      "email": "contato@abc.com",
      "cidade": "São Paulo",
      "estado": "SP",
      "ativo": true,
      "produtos_ativos": 15,
      "classificacao": "A",
      "total_compras": 50,
      "valor_total_comprado": 125000.00
    }
  ],
  "total": 1,
  "pagina": 1,
  "por_pagina": 50,
  "total_paginas": 1
}
```

## PRÓXIMOS PASSOS

1. **REINICIAR O BACKEND** para aplicar as mudanças
2. Verificar se o backend está rodando em `http://127.0.0.1:5000`
3. Testar a rota diretamente: `curl http://127.0.0.1:5000/api/fornecedores -H "Authorization: Bearer <token>"`
4. Verificar no console do navegador se o CORS error desapareceu
5. Verificar se os cards do dashboard mostram os números corretos

## COMANDOS PARA REINICIAR

```bash
cd backend
# Ativar venv
venv\Scripts\activate
# Reiniciar servidor
python run.py
```

## TESTE RÁPIDO

Após reiniciar o backend, abra o console do navegador (F12) e verifique:
1. ✅ Sem erros CORS
2. ✅ Resposta 200 OK da API `/api/fornecedores`
3. ✅ Console mostra: `📦 Resposta da API fornecedores: { success: true, fornecedores: [...] }`
4. ✅ Cards do dashboard mostram números corretos
5. ✅ Tabela de fornecedores carrega corretamente
