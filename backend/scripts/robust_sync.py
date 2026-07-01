"""
Motor de sincronização ROBUSTO local → Aiven.

Por que existe: o force_sync original caía em fallback linha-a-linha (commit por
linha) quando um lote falhava por FK, travando indefinidamente — e o Aiven não
permite `session_replication_role = replica` (avnadmin não é superuser).

Estratégia desta versão:
- Fonte Agnostica: Lê dados do banco local usando SQLAlchemy (suporta SQLite perfeitamente).
- Destino Otimizado: Grava dados no Aiven via psycopg2 bulk (execute_values).
- Ordem por dependência (pais antes de filhos).
- Para tabelas-filho, carrega os IDs válidos do PAI no Aiven e **descarta órfãos**
  (filhos cujo FK não existe no destino) → o lote nunca falha por FK.
"""
import os
import sys
import psycopg2
import psycopg2.extras
from psycopg2.extras import Json

from sqlalchemy import inspect, text

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

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


def _get_local_engine():
    """Garante que temos o engine do SQLAlchemy ativo, mesmo executado por CLI."""
    from flask import current_app
    from app.models import db
    if current_app:
        return db.engine
    
    from app import create_app
    app = create_app()
    with app.app_context():
        return db.engine


def _get_local_columns(engine, table):
    """Retorna as colunas de uma tabela local independente do dialeto."""
    inspector = inspect(engine)
    if not inspector.has_table(table):
        return []
    return [col['name'] for col in inspector.get_columns(table)]


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

    aiven_url = os.environ.get("AIVEN_DATABASE_URL")
    if not aiven_url:
        return {"success": False, "erro": "AIVEN_DATABASE_URL ausente"}

    try:
        # Aiven (Destino) sempre em PostgreSQL via psycopg2
        aconn = psycopg2.connect(**_parse_url(aiven_url))
        
        # Local (Fonte) via SQLAlchemy (suporta SQLite e Postgres)
        local_engine = _get_local_engine()
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

    with local_engine.connect() as lconn:
        for table, fks in PLAN:
            if table not in aiven_tables:
                continue
            try:
                lcols = _get_local_columns(local_engine, table)
                if not lcols:
                    continue
                    
                ac = aconn.cursor()
                acols = set(_cols(ac, table))
                cols = [c for c in lcols if c in acols]
                if "id" not in cols:
                    ac.close(); continue

                fk_filters = [(c, p) for (c, p) in fks if c in cols and p in aiven_tables]
                fk_sets = {c: parent_ids(p) for (c, p) in fk_filters}

                has_upd = "updated_at" in cols
                collist = ", ".join(f'"{c}"' for c in cols)
                upd = ", ".join(f'"{c}"=EXCLUDED."{c}"' for c in cols if c != "id")
                conflict = (
                    f'ON CONFLICT (id) DO UPDATE SET {upd} '
                    + (f'WHERE "{table}".updated_at <= EXCLUDED.updated_at' if has_upd else "")
                ) if upd else "ON CONFLICT (id) DO NOTHING"
                sql_bulk = f'INSERT INTO "{table}" ({collist}) VALUES %s {conflict}'
                placeholders = ", ".join(["%s"] * len(cols))
                sql_single = f'INSERT INTO "{table}" ({collist}) VALUES ({placeholders}) {conflict}'

                # SQLAlchemy execution (agnostic)
                result = lconn.execute(text(f'SELECT {collist} FROM "{table}"'))
                
                lidos = enviados = orfaos = 0
                batch = []

                def flush(rows):
                    nonlocal enviados
                    if not rows:
                        return
                    try:
                        psycopg2.extras.execute_values(ac, sql_bulk, rows, page_size=BATCH)
                        aconn.commit()
                        enviados += len(rows)
                    except Exception as e:
                        aconn.rollback()
                        log(f"    ⚠ lote {table}: {str(e)[:90]} (fallback para linha-a-linha)")
                        for r in rows:
                            try:
                                ac.execute(sql_single, r)
                                aconn.commit()
                                enviados += 1
                            except Exception:
                                aconn.rollback()

                # Using row mappings to simulate dict access
                for row_data in result.mappings():
                    lidos += 1
                    orfao = False
                    for c, valid in fk_sets.items():
                        v = row_data[c]
                        if v is not None and v not in valid:
                            orfao = True
                            break
                    if orfao:
                        orfaos += 1
                        continue
                    batch.append(tuple(_adapt(row_data[c]) for c in cols))
                    if len(batch) >= BATCH:
                        flush(batch); batch = []
                        
                flush(batch)
                ac.close()

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
    aconn.close()
    return {"success": True, "total_registros": total}


if __name__ == "__main__":
    robust_sync(silent=False)
