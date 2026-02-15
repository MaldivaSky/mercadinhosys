# Saúde do banco na nuvem (PostgreSQL / Neon)

## Problema

Se a aplicação online (Vercel frontend + Render backend) não funciona e o banco “não subiu” para o PostgreSQL, as causas mais comuns são:

1. **Migrações não aplicadas no Postgres**  
   O `start.sh` do Render só usava `db.create_all()`. Isso cria tabelas que não existem, mas **não** adiciona colunas ou tabelas novas definidas nas migrações Alembic (ex.: `margem_lucro_real` em `venda_itens`, tabela `historico_precos`). Ou seja, o schema do Neon fica atrás do código.

2. **Variável de ambiente errada**  
   O backend precisa usar a URL do Neon. No Render, a variável deve ser uma destas (em ordem de prioridade):  
   `NEON_DATABASE_URL`, `DATABASE_URL_TARGET`, `DATABASE_URL`, `POSTGRES_URL`.  
   O código já aceita `postgres://` e converte para `postgresql://` quando necessário.

## O que foi feito

1. **`start.sh` (Render)**  
   - Passa a rodar **`flask db upgrade`** antes de `db.create_all()`.  
   - Assim, todas as migrações Alembic são aplicadas no Postgres (Neon) a cada deploy, e o schema fica alinhado ao `models.py`.

2. **Script local `check_db_health.py`**  
   - Verifica conexão, tabela `alembic_version`, tabelas críticas e coluna `venda_itens.margem_lucro_real`.  
   - Uso (no `backend/`, com `.env` configurado):
     ```bash
     python check_db_health.py
     ```

3. **Endpoint de diagnóstico `GET /api/auth/db-schema`**  
   - Resposta JSON com: conexão, revisão Alembic e checagens de tabelas/colunas.  
   - Exemplo após deploy:
     ```text
     https://mercadinhosys.onrender.com/api/auth/db-schema
     ```

## O que você precisa fazer

### 1. Conferir variáveis no Render

- Serviço do **backend** no Render:
  - Garanta que existe uma variável apontando para o Neon, por exemplo:
    - **Nome:** `DATABASE_URL` (ou `NEON_DATABASE_URL`)  
    - **Valor:** a connection string do Neon (ex.: `postgresql://user:pass@host.neon.tech/neondb?sslmode=require`).

### 2. Fazer redeploy do backend

- Depois de commitar a alteração do `start.sh`, faça um **novo deploy** do serviço backend no Render.  
- Nos logs do deploy, confira se aparecem:
  - `Applying database migrations (flask db upgrade)...`
  - E que o comando termina sem erro (ou, em caso de falha, a mensagem indicada no log).

### 3. Verificar saúde do banco

- **Pela API (após o deploy):**
  - Abra no navegador ou via `curl`:
    ```text
    https://mercadinhosys.onrender.com/api/auth/db-schema
    ```
  - Se `schema_ok` for `true` e `database` for `connected`, o schema está alinhado e a aplicação pode usar o Postgres normalmente.

- **Localmente contra o Neon:**
  - No `backend/`, com o mesmo `.env` que você usaria em produção (por exemplo `DATABASE_URL` ou `NEON_DATABASE_URL`):
    ```bash
    python check_db_health.py
    ```
  - Se tudo estiver certo, o script termina com “SAÚDE DO BANCO: OK”.

### 4. Se ainda falhar

- Confira os **logs do Render** no momento do start (saída do `flask db upgrade` e do `create_all`).
- Se `flask db upgrade` falhar, a mensagem de erro costuma indicar conflito de revisões ou schema; nesse caso, pode ser necessário ajustar migrações ou rodar migrações manualmente uma vez (por exemplo via shell do Render, se disponível).
- Garanta que no Render o **Build Command** e o **Start Command** usem o `start.sh` (ou os mesmos passos: instalar deps, `flask db upgrade`, depois iniciar o app).

Com isso, o banco na nuvem (Neon) fica com o mesmo schema do código e a aplicação no Vercel (frontend) + Render (backend) pode funcionar de forma estável.
