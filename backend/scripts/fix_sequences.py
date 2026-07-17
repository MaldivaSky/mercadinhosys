"""
Realinha as sequences de ID (nextval) com o MAX(id) real de cada tabela.

Por que existe: force_sync_to_aiven.py e robust_sync.py fazem upsert com "id"
explícito (INSERT ... ON CONFLICT). Isso nunca avança a sequence associada à
coluna, então depois de sincronizar, o próximo INSERT feito pela aplicação
(sem id explícito) tenta reusar um id já ocupado -> "duplicate key value
violates unique constraint pk_<tabela>". Já aconteceu antes (vendas,
produtos, clientes...) e voltou a acontecer em caixas em 2026-07-17.

Chamado automaticamente ao final de force_sync() e robust_sync(). Também
pode ser rodado isoladamente contra o Aiven.
"""
import os
import sys
import psycopg2

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from scripts.force_sync_to_aiven import _parse_url


def fix_sequences(conn=None, dsn=None, silent=False):
    """Ajusta toda sequence de coluna 'id' para MAX(id) da respectiva tabela.

    Se `conn` for passado, reusa a conexão aberta (não fecha ao final).
    Caso contrário, abre uma nova a partir de `dsn` ou AIVEN_DATABASE_URL.
    """
    def log(msg):
        if not silent:
            print(msg, flush=True)

    own_conn = conn is None
    if own_conn:
        url = dsn or os.environ.get("AIVEN_DATABASE_URL")
        if not url:
            return {"success": False, "erro": "AIVEN_DATABASE_URL ausente"}
        conn = psycopg2.connect(**_parse_url(url))

    ajustadas = []
    try:
        cur = conn.cursor()
        # Passo 1: lista tabelas com coluna 'id' (via information_schema, sem
        # chamar pg_get_serial_sequence ainda). Necessário separar em dois
        # passos: o planner do Postgres não garante ordem de avaliação do
        # WHERE, então chamar pg_get_serial_sequence na mesma query para
        # tabelas sem 'id' (ex.: alembic_version) derruba a query inteira
        # com "column id of relation X does not exist".
        cur.execute("""
            SELECT table_name FROM information_schema.columns
            WHERE table_schema = 'public' AND column_name = 'id'
            ORDER BY table_name
        """)
        table_names = [r[0] for r in cur.fetchall()]

        rows = []
        for table_name in table_names:
            cur.execute("SELECT pg_get_serial_sequence(%s, 'id')", (f"public.{table_name}",))
            seq_name = cur.fetchone()[0]
            if seq_name:
                rows.append((table_name, seq_name))

        for table_name, seq_name in rows:
            cur.execute(f'SELECT COALESCE(MAX(id), 0) FROM "{table_name}"')
            max_id = cur.fetchone()[0]
            cur.execute(f"SELECT last_value FROM {seq_name}")
            current = cur.fetchone()[0]
            if current < max_id:
                cur.execute("SELECT setval(%s, %s, true)", (seq_name, max_id))
                ajustadas.append((table_name, current, max_id))
                log(f"  🔧 {table_name:<28} seq {current:>8} -> {max_id:>8}")
        conn.commit()
        log(f"\n✅ {len(ajustadas)} sequence(s) corrigida(s) de {len(rows)} verificada(s).")
        return {"success": True, "ajustadas": ajustadas, "total_verificadas": len(rows)}
    except Exception as e:
        conn.rollback()
        log(f"❌ Erro ao corrigir sequences: {e}")
        return {"success": False, "erro": str(e)}
    finally:
        if own_conn:
            conn.close()


if __name__ == "__main__":
    try:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(BASE_DIR, '.env'))
    except ImportError:
        pass
    fix_sequences(silent=False)
