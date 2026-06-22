# Cosmos Daily Harvest — Catálogo Mestre de Produtos

Coletor diário que usa o limite da API Cosmos (Bluesoft) para acumular produtos
com **EAN real** na tabela global `catalogo_mestre`. Quanto mais dias rodando,
mais rico fica o catálogo que acompanha o produto.

## O que faz

- Consulta até **24 EANs/dia** (configurável) que ainda não foram consultados.
- Grava os encontrados em `catalogo_mestre` (nome, marca, NCM, categoria, imagem).
- Marca os 404 como `nao_encontrado` para **nunca reconsultar** e desperdiçar quota.
- **Para imediatamente** se a Cosmos retornar `429` (limite atingido).
- Operação **100% aditiva** — nunca apaga nem reseta dados.

## Fontes de EANs candidatos

1. **Curados** — lista de EANs reais verificados (`cosmos_catalog.REAL_SKUS`).
2. **Gerador GS1 Brasil** — prefixos reais de fabricantes (Nestlé, Coca-Cola,
   Unilever, etc.); descobre produtos reais ao longo do tempo.

## Como rodar manualmente

```bash
cd backend
python scripts/cosmos_daily_harvest.py            # 24 EANs (padrão)
python scripts/cosmos_daily_harvest.py --limit 24
python scripts/cosmos_daily_harvest.py --no-generated   # só EANs curados
```

## Variáveis de ambiente

| Variável             | Default                     | Descrição                          |
|----------------------|-----------------------------|------------------------------------|
| `COSMOS_TOKEN`       | (token embutido p/ dev)     | Token da API Cosmos                |
| `COSMOS_DAILY_LIMIT` | `24`                        | Máximo de chamadas por execução    |
| `DATABASE_URL`       | (resolvido pelo `config.py`)| Banco onde o catálogo é gravado    |

## Automação via Cron Job no Render (recomendado)

A produção já roda no Render. Crie um **Cron Job** apontando para o mesmo repositório:

1. No painel do Render: **New → Cron Job**.
2. **Environment:** Python 3.
3. **Build Command:** `pip install -r backend/requirements.txt`
4. **Command:** `cd backend && python scripts/cosmos_daily_harvest.py`
5. **Schedule:** `0 9 * * *` (todo dia às 09:00 UTC).
6. **Environment Variables:** copie `DATABASE_URL` (Aiven), `COSMOS_TOKEN` e,
   se quiser, `COSMOS_DAILY_LIMIT` do serviço web principal.

O cron job compartilha o mesmo banco do app, então o catálogo cresce em produção
automaticamente, sem depender de nenhuma máquina local ligada.

## Como o lojista usa o catálogo

- **Cadastro rápido por EAN:** `GET /api/produtos/catalogo/buscar/<ean>`
  preenche nome, marca, NCM e imagem sem gastar quota Cosmos por loja.
- **Importação em massa:** `POST /api/produtos/catalogo/importar`
  com `{ "eans": [...], "fornecedor_id": opcional, "margem": opcional }`.
- **Listagem/pesquisa:** `GET /api/produtos/catalogo?busca=&categoria=&pagina=`.
