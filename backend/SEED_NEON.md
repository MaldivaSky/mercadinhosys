# Semear o banco Neon (PostgreSQL) com seed_test.py

Os erros **500** e **UndefinedColumn** (ex.: `column produtos...`) no Vercel/Render acontecem quando o schema do Neon está desatualizado em relação ao `models.py` (ex.: falta a coluna `tipo` na tabela `produtos`).

O seed com **--reset --cloud** agora **recria todas as tabelas** no Postgres (DROP + CREATE), alinhando o schema ao código e em seguida populando os dados.

## Semear LOCAL + NUVEM juntos

Para popular **ambos** os bancos (SQLite local e Neon) com o mesmo conjunto de dados:

```bash
python seed_test.py --reset --both
```

Isso executa o seed sequencialmente: primeiro o banco local, depois o Neon. Ideal para manter os dois ambientes sincronizados.

## Neon Free Tier – Rate limiting

No modo **--cloud** (PostgreSQL/Neon), o seed usa automaticamente:
- Batches menores (10 vendas por commit) para evitar timeouts
- Intervalo de **10 segundos** entre batches para não sobrecarregar o plano free
- Ordenação de locks por ID para evitar deadlocks

## Passos

### 1. Configurar a URL do Neon

No **backend**, crie ou edite o arquivo `.env` e defina a **mesma** connection string que o Render usa:

```env
NEON_DATABASE_URL=postgresql://USUARIO:SENHA@HOST/neondb?sslmode=require
```

- Pegue a URL no [Neon Console](https://console.neon.tech) do seu projeto (Connection string).
- Ou use a variável que já está configurada no **Render** (Environment → `NEON_DATABASE_URL` ou `DATABASE_URL`).

### 2. Rodar o seed contra o Neon

No terminal, na pasta **backend**:

```bash
cd backend
python seed_test.py --reset --cloud
```

No **PowerShell** (Windows):

```powershell
cd c:\Users\rafae\OneDrive\Desktop\mercadinhosys\backend
python seed_test.py --reset --cloud
```

- **--reset**: apaga e recria as tabelas (schema atualizado) e depois popula.
- **--cloud**: usa `NEON_DATABASE_URL` do `.env` (banco na nuvem).

### 3. Credenciais de teste após o seed

- **Admin:** `admin` / `admin123`
- **Caixa:** `caixa01` / `123456`
- **Estoque:** `estoque01` / `123456`

Depois de rodar o seed, faça novo deploy ou reinicie o backend no Render para usar o banco já atualizado e populado. Os erros de coluna indefinida e 500 devem cessar.

## Sem reset (só popular se estiver vazio)

Se o schema já estiver correto e você só quiser popular dados quando o banco estiver vazio:

```bash
python seed_test.py --cloud
```

## Observação

O comando **--reset --cloud** **apaga todos os dados** do Neon e recria as tabelas conforme o `models.py` atual. Use apenas no banco de desenvolvimento/teste ou quando quiser deixar o ambiente de produção alinhado ao código e repopulado.
