"""
sync_sfa_to_aiven.py — Sincronização FOCADA da Força de Vendas (local -> Aiven)
==============================================================================
Diferente do force_sync_to_aiven (banco inteiro, lento), este sobe SOMENTE as
tabelas do módulo SFA, na ordem correta de FK. As dependências (clientes,
produtos, funcionarios) já vivem no Aiven, então isto roda em segundos e é
idempotente (ON CONFLICT id DO UPDATE, respeitando updated_at quando existe).

Uso:
    python -m scripts.sync_sfa_to_aiven            # todos os estabelecimentos
    python -m scripts.sync_sfa_to_aiven --estab 1  # apenas o estab 1

Lê DATABASE_URL (local) e AIVEN_DATABASE_URL do backend/.env.
"""
import os
import sys
import argparse

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import psycopg2
import psycopg2.extras

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BASE_DIR, ".env"))
except ImportError:
    pass

# Ordem de FK: preço/rota antes; itens e pedidos dependem de produtos/clientes.
SFA_TABLES = [
    "tabelas_preco", "rotas",
    "tabela_preco_itens", "produtos_foco", "metas_vendedor",
    "pedidos_venda", "pedido_venda_itens",
]


def _conn_kwargs(url, no_ssl=False):
    url = url.replace("postgresql://", "postgres://", 1) if url.startswith("postgresql://") else url
    body = url[len("postgres://"):]
    params = {}
    if "?" in body:
        body, ps = body.split("?", 1)
        for p in ps.split("&"):
            if "=" in p:
                k, v = p.split("=", 1); params[k] = v
    userpass, rest = body.split("@", 1)
    user, pw = (userpass.split(":", 1) + [""])[:2]
    hostport, db = (rest.rsplit("/", 1) + ["postgres"])[:2]
    host, port = (hostport.rsplit(":", 1) + ["5432"])[:2]
    kw = dict(host=host, port=int(port), user=user, password=pw, dbname=db, connect_timeout=30)
    if no_ssl:
        kw["sslmode"] = "disable"
    elif "sslmode" in params:
        kw["sslmode"] = params["sslmode"]
    return kw


def sync(estab_id=None):
    local_url = os.environ.get("DATABASE_URL")
    aiven_url = os.environ.get("AIVEN_DATABASE_URL")
    if not local_url or not aiven_url:
        print("❌ DATABASE_URL ou AIVEN_DATABASE_URL ausentes no ambiente/.env")
        return 1

    lc = psycopg2.connect(**_conn_kwargs(local_url, no_ssl=True))
    ac = psycopg2.connect(**_conn_kwargs(aiven_url))
    lcur = lc.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    acur = ac.cursor()

    escopo = f"estab {estab_id}" if estab_id else "todos os estabelecimentos"
    print(f"\n🚀 Sync SFA local → Aiven ({escopo})")
    print(f"  {'Tabela':<22}{'Local':>8}{'Antes':>8}{'Depois':>8}")
    print("  " + "-" * 46)

    total = 0
    for table in SFA_TABLES:
        # Colunas em comum (protege contra schema drift)
        lcur.execute("select column_name from information_schema.columns "
                     "where table_name=%s and table_schema='public'", (table,))
        lcols = [r["column_name"] for r in lcur.fetchall()]
        acur.execute("select column_name from information_schema.columns "
                     "where table_name=%s and table_schema='public'", (table,))
        acols = {r[0] for r in acur.fetchall()}
        cols = [c for c in lcols if c in acols]
        if not cols:
            print(f"  {table:<22}{'—':>8}  (tabela ausente no Aiven)")
            continue

        filtro = ""
        params = []
        if estab_id and "estabelecimento_id" in cols:
            filtro = " WHERE estabelecimento_id = %s"
            params = [estab_id]
        elif estab_id and table == "pedido_venda_itens":
            # itens não têm estab? têm; mas garantimos via join se preciso
            pass

        lcur.execute(f'SELECT count(*) c FROM "{table}"{filtro}', params)
        n_local = lcur.fetchone()["c"]
        acur.execute(f'SELECT count(*) FROM "{table}"'); n_antes = acur.fetchone()[0]

        if n_local:
            lcur.execute(f'SELECT {", ".join(chr(34)+c+chr(34) for c in cols)} FROM "{table}"{filtro}', params)
            rows = lcur.fetchall()
            cs = ", ".join(f'"{c}"' for c in cols)
            upd = ", ".join(f'"{c}"=EXCLUDED."{c}"' for c in cols if c != "id")
            if "updated_at" in cols and upd:
                conflict = f'ON CONFLICT (id) DO UPDATE SET {upd} WHERE "{table}".updated_at <= EXCLUDED.updated_at'
            elif upd:
                conflict = f"ON CONFLICT (id) DO UPDATE SET {upd}"
            else:
                conflict = "ON CONFLICT (id) DO NOTHING"
            data = []
            for r in rows:
                vals = []
                for c in cols:
                    v = r[c]
                    if isinstance(v, (dict, list)):
                        v = psycopg2.extras.Json(v)
                    vals.append(v)
                data.append(tuple(vals))
            try:
                psycopg2.extras.execute_values(
                    acur, f'INSERT INTO "{table}" ({cs}) VALUES %s {conflict}', data)
                ac.commit()
            except Exception as e:
                ac.rollback()
                print(f"  ⚠️ {table}: {str(e)[:120]} — fallback linha a linha")
                ph = ", ".join(["%s"] * len(cols))
                for row in data:
                    try:
                        acur.execute(f'INSERT INTO "{table}" ({cs}) VALUES ({ph}) {conflict}', row)
                        ac.commit()
                    except Exception:
                        ac.rollback()

        acur.execute(f'SELECT count(*) FROM "{table}"'); n_depois = acur.fetchone()[0]
        total += (n_depois - n_antes)
        print(f"  {table:<22}{n_local:>8}{n_antes:>8}{n_depois:>8}")

    print("  " + "-" * 46)
    print(f"  ✅ +{total} registros novos no Aiven.\n")

    # Upsert com id explícito nunca avança a sequence -> corrige aqui para o
    # próximo INSERT normal da app não colidir (duplicate key).
    from scripts.fix_sequences import fix_sequences
    fix_sequences(conn=ac, silent=False)

    lc.close(); ac.close()
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--estab", type=int, default=None)
    args = ap.parse_args()
    sys.exit(sync(args.estab))
