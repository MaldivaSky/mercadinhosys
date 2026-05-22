import click
from flask import current_app
from flask.cli import with_appcontext
from app.models import SyncQueue
import logging

logger = logging.getLogger(__name__)

def register_commands(app):
    @app.cli.command("push-to-aiven")
    @with_appcontext
    def push_to_aiven():
        """Sincroniza dados locais com o Aiven Cloud"""
        click.echo("🚀 Iniciando push manual para Aiven...")
        try:
            from app.services.sync_worker import GuerrillaSyncWorker
            worker = GuerrillaSyncWorker(current_app._get_current_object())
            click.echo("Processando fila de sincronização...")
            worker.process_queue()
            click.echo("✅ Sincronização concluída!")
        except Exception as e:
            click.echo(f"❌ Erro durante sincronização: {e}")
            logger.error(f"Erro no comando push-to-aiven: {e}")

    @app.cli.command("sync-status")
    @with_appcontext
    def sync_status():
        """Exibe o status da fila de sincronização local"""
        try:
            pendentes = SyncQueue.query.filter_by(status='pendente').count()
            erros = SyncQueue.query.filter_by(status='erro').count()
            sincronizados = SyncQueue.query.filter_by(status='sincronizado').count()
            
            click.echo("="*30)
            click.echo("📊 STATUS DA SINCRONIZAÇÃO")
            click.echo("="*30)
            click.echo(f"Pendentes:   {pendentes}")
            click.echo(f"Erros:       {erros}")
            click.echo(f"Sincronizados: {sincronizados}")
            click.echo("="*30)
        except Exception as e:
            click.echo(f"❌ Erro ao consultar status: {e}")
