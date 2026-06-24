"""
Motor de sincronização ROBUSTO local → Aiven.

Por que existe: o force_sync original caía em fallback linha-a-linha (commit por
linha) quando um lote falhava por FK, travando indefinidamente — e o Aiven não
permite `session_replication_role = replica` (avnadmin não é superuser).

Estratégia desta versão:
- Ordem por dependência (pais antes de filhos).
- Para tabelas-filho, carrega os IDs válidos do PAI no Aiven e **descarta órfãos**
  (filhos cujo FK não existe no destino) → o lote nunca falha por FK.
- Upsert em lote (execute_values) com guarda de updated_at; SEM fallback lento.
- Cursor server-side no local (sem OFFSET, escala para centenas de milhares).
"""
import os
import psycopg2
import psycopg2.extras
from psycopg2.extras import Json

from scripts.force_sync_to_aiven import _parse_url

BATCH = 2000

_E = ("estabelecimento_id", "estabelecimentos")  # FK de tenant presente em quase tudo

# (tabela, [(coluna_fk, tabela_pai), ...]) — ordem importa (pais primeiro)
PLAN = [
    ("estabelecimentos", []),
    ("fornecedores", [_E]),
    ("categorias_produto", [_E]),
    ("funcionarios", [_E]),
    ("clientes", [_E]),
    ("produtos", [_E, ("categoria_id", "categorias_produto"), ("fornecedor_id", "fornecedores")]),
    ("produto_lotes", [_E, ("produto_id", "produtos")]),
    ("caixas", [_E, ("funcionario_id", "funcionarios")]),
    ("vendas", [_E, ("funcionario_id", "funcionarios"), ("cliente_id", "clientes"), ("caixa_id", "caixas")]),
    ("venda_itens", [_E, ("venda_id", "vendas"), ("produto_id", "produtos")]),
    ("pagamentos", [_E, ("venda_id", "vendas")]),
    ("movimentacoes_estoque", [_E, ("produto_id", "produtos"), ("venda_id", "vendas"), ("funcionario_id", "funcionarios")]),
    ("despesas", [_E, ("fornecedor_id", "fornecedores")]),
    ("contas_pagar", [_E, ("fornecedor_id", "fornecedores")]),
    ("contas_receber", [_E, ("cliente_id", "clientes")]),
    ("documentos_fiscais", [_E, ("venda_id", "vendas")]),
    ("notas_fiscais_entrada", [_E, ("fornecedor_id", "fornecedores")]),
]


def _adapt(v):
    # psycopg2 não adapta dict/list nativamente (colunas JSON) → embrulha em Json
    return Json(v) if isinstance(v, (dict, list)) else v


def _cols(cur, table):
    cur.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_name=%s AND table_schema='public'",
        (table,),
    )
    return [r[0] for r in cur.fetchall()]


def robust_sync(silent=False):
    def log(m):
        if not silent:
            print(m, flush=True)

    local_url = os.environ.get("DATABASE_URL")
    aiven_url = os.environ.get("AIVEN_DATABASE_URL")
    if not local_url or not aiven_url:
        return {"success": False, "erro": "DATABASE_URL/AIVEN_DATABASE_URL ausentes"}

    try:
        lconn = psycopg2.connect(**_parse_url(local_url, force_no_ssl=True))
        aconn = psycopg2.connect(**_parse_url(aiven_url))
        lconn.autocommit = False
    except Exception as e:
        return {"success": False, "erro": f"conexao: {e}"}

    meta = aconn.cursor()
    meta.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")
    aiven_tables = {r[0] for r in meta.fetchall()}

    parent_ids_cache = {}

    def parent_ids(table):
        if table not in parent_ids_cache:
            c = aconn.cursor()
            c.execute(f'SELECT id FROM "{table}"')
            parent_ids_cache[table] = {r[0] for r in c.fetchall()}
            c.close()
        return parent_ids_cache[table]

    total = 0
    log("=" * 58)
    log(f"  {'Tabela':<26}{'Lidos':>9}{'Enviados':>10}{'Órfãos':>8}")
    log("-" * 58)

    for table, fks in PLAN:
        if table not in aiven_tables:
            continue
        try:
            lc = lconn.cursor()
            lcols = _cols(lc, table)
            ac = aconn.cursor()
            acols = set(_cols(ac, table))
            cols = [c for c in lcols if c in acols]
            if "id" not in cols:
                lc.close(); ac.close(); continue

            fk_filters = [(c, p) for (c, p) in fks if c in cols and p in aiven_tables]
            fk_sets = {c: parent_ids(p) for (c, p) in fk_filters}

            has_upd = "updated_at" in cols
            collist = ", ".join(f'"{c}"' for c in cols)
            upd = ", ".join(f'"{c}"=EXCLUDED."{c}"' for c in cols if c != "id")
            conflict = (
                f'ON CONFLICT (id) DO UPDATE SET {upd} '
                + (f'WHERE "{table}".updated_at <= EXCLUDED.updated_at' if has_upd else "")
            ) if upd else "ON CONFLICT (id) DO NOTHING"
            sql = f'INSERT INTO "{table}" ({collist}) VALUES %s {conflict}'

            scur = lconn.cursor(name=f"srv_{table}", cursor_factory=psycopg2.extras.RealDictCursor)
            scur.itersize = BATCH
            scur.execute(f'SELECT {collist} FROM "{table}"')

            lidos = enviados = orfaos = 0
            batch = []

            def flush(rows):
                nonlocal enviados
                if not rows:
                    return
                try:
                    psycopg2.extras.execute_values(ac, sql, rows, page_size=BATCH)
                    aconn.commit()
                    enviados += len(rows)
                except Exception as e:
                    aconn.rollback()
                    log(f"    ⚠ lote {table}: {str(e)[:90]}")

            for row in scur:
                lidos += 1
                orfao = False
                for c, valid in fk_sets.items():
                    v = row[c]
                    if v is not None and v not in valid:
                        orfao = True
                        break
                if orfao:
                    orfaos += 1
                    continue
                batch.append(tuple(_adapt(row[c]) for c in cols))
                if len(batch) >= BATCH:
                    flush(batch); batch = []
            flush(batch)
            scur.close(); lc.close(); ac.close()

            # invalida cache deste destino (acabou de receber linhas) p/ filhos seguintes
            parent_ids_cache.pop(table, None)
            total += enviados
            log(f"  {table:<26}{lidos:>9}{enviados:>10}{orfaos:>8}")
        except Exception as e:
            try: aconn.rollback()
            except Exception: pass
            log(f"  ❌ {table}: {str(e)[:120]}")
            continue

    log("-" * 58)
    log(f"  TOTAL ENVIADO: {total}")
    lconn.close(); aconn.close()
    return {"success": True, "total_registros": total}


if __name__ == "__main__":
    robust_sync(silent=False)
