import os
import click
from flask.cli import with_appcontext
import logging

logger = logging.getLogger(__name__)


def register_commands(app):
    @app.cli.command("push-to-aiven")
    @with_appcontext
    def push_to_aiven():
        """Replicação completa local → Aiven (motor force_sync, idempotente)."""
        click.echo("🚀 Sincronizando local → Aiven (robust_sync)...")
        try:
            from scripts.robust_sync import robust_sync
            res = robust_sync(silent=False)
            if res.get("success"):
                click.echo(f"✅ Concluído: {res.get('total_registros', 0)} registros enviados ao Aiven.")
            else:
                click.echo(f"❌ Falha: {res.get('erro')}")
        except Exception as e:
            click.echo(f"❌ Erro durante sincronização: {e}")
            logger.error(f"Erro no comando push-to-aiven: {e}")

    @app.cli.command("sync-status")
    @with_appcontext
    def sync_status():
        """Mostra o gap de registros entre o banco local e o Aiven."""
        import psycopg2
        tabelas = ["vendas", "produtos", "clientes", "despesas", "documentos_fiscais", "notas_fiscais_entrada"]
        local_url = os.environ.get("DATABASE_URL")
        aiven_url = os.environ.get("AIVEN_DATABASE_URL")
        if not local_url or not aiven_url:
            click.echo("❌ DATABASE_URL/AIVEN_DATABASE_URL não configurados.")
            return

        def _counts(url):
            out = {}
            try:
                conn = psycopg2.connect(url.replace("postgres://", "postgresql://", 1), connect_timeout=15)
                cur = conn.cursor()
                for t in tabelas:
                    try:
                        cur.execute(f'SELECT count(*) FROM "{t}"')
                        out[t] = cur.fetchone()[0]
                    except Exception:
                        conn.rollback()
                        out[t] = None
                conn.close()
            except Exception as e:
                click.echo(f"  ⚠️ Conexão falhou: {str(e)[:80]}")
            return out

        loc = _counts(local_url)
        aiv = _counts(aiven_url)
        click.echo("=" * 52)
        click.echo(f"  {'Tabela':<24}{'Local':>8}{'Aiven':>8}{'Gap':>8}")
        click.echo("-" * 52)
        for t in tabelas:
            l, a = loc.get(t), aiv.get(t)
            gap = (l - a) if (isinstance(l, int) and isinstance(a, int)) else "—"
            click.echo(f"  {t:<24}{str(l):>8}{str(a):>8}{str(gap):>8}")
        click.echo("=" * 52)
