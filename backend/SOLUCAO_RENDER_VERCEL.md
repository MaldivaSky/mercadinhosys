# Solução para Erros 500 no Render/Vercel

## Problema
A aplicação funciona localmente (Docker) mas retorna 500 em produção nas rotas:
- `/api/produtos/` (carregar produtos)
- `/api/produtos/estatisticas`
- `/api/produtos/categorias`
- `/api/fornecedores/`

## Causa Raiz
O banco Postgres na nuvem (Aiven/Render) pode estar com schema desatualizado — faltam colunas que o código espera (ex: `margem_lucro_real`, `total_vendido`, etc.) ou o arquivo `seed_cloud.py` não existia, causando falha no deploy.

## Solução Implementada

### 1. `schema_sync.py` (novo)
Script que garante colunas críticas no Postgres:
- `venda_itens.margem_lucro_real`
- `produtos`: margem_lucro, tipo, classificacao_abc, total_vendido, quantidade_vendida, ultima_venda, fabricante
- `fornecedores`: valor_total_comprado, total_compras, classificacao, prazo_entrega

Executa `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` para cada uma. Não falha se a coluna já existir.

### 2. `start.sh` (atualizado)
Ordem de execução:
1. `flask db upgrade` — migrações
2. `db.create_all()` — criar tabelas
3. Seed (se DB vazio) via `seed_cloud.py`
4. **`schema_sync.py`** — garantir colunas críticas (novo)
5. Gunicorn

### 3. `seed_cloud.py` (criado)
Wrapper que redireciona para `seed_cloud_light.py` — o `start.sh` chamava `seed_cloud.py` que não existia.

### 4. Rotas mais resilientes
- **categorias**: fallback corrigido (usa `categorias_produto` + join) e fallback final retorna lista vazia em vez de 500.

## Deploy no Render

1. Faça push das alterações.
2. O Render fará redeploy automático.
3. No primeiro deploy ou se o banco estiver vazio, o seed rodará e populará os dados.
4. O `schema_sync` rodará antes do Gunicorn e adicionará colunas faltantes.
5. Verifique os logs do Render em **Dashboard → Serviço → Logs** para confirmar:
   - `✅ schema_sync: X/12 colunas verificadas`
   - `✅ Database already has data` ou `🌱 Seeding database...`

## Se ainda houver 500

1. **Logs do Render**: Dashboard → seu serviço → Logs. Procure por `[ERRO 500]` e o traceback.
2. **Verificar variáveis de ambiente**: `DATABASE_URL` deve apontar para o Postgres da Aiven.
3. **Rodar schema_sync manualmente** (em outro terminal com DATABASE_URL configurada):
   ```bash
   cd backend
   python schema_sync.py
   ```
