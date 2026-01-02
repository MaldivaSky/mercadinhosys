"""
backend/backup_db.py
Sistema de backup automático do banco de dados
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
import zipfile
import schedule
import time


class BackupManager:
    """Gerenciador de backups do banco de dados"""

    def __init__(self, db_path, backup_dir="backups"):
        self.db_path = Path(db_path)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self):
        """Cria um backup do banco de dados"""
        if not self.db_path.exists():
            print(f"❌ Banco de dados não encontrado: {self.db_path}")
            return False

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}.db"
        backup_path = self.backup_dir / backup_name

        try:
            # Copia o arquivo do banco
            shutil.copy2(self.db_path, backup_path)

            # Compacta o backup
            zip_path = self.backup_dir / f"backup_{timestamp}.zip"
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(backup_path, backup_name)

            # Remove o arquivo não compactado
            backup_path.unlink()

            print(f"✅ Backup criado: {zip_path}")

            # Limpa backups antigos (mantém últimos 7 dias)
            self.cleanup_old_backups(days=7)

            return True
        except Exception as e:
            print(f"❌ Erro ao criar backup: {e}")
            return False

    def cleanup_old_backups(self, days=7):
        """Remove backups mais antigos que X dias"""
        cutoff_time = time.time() - (days * 24 * 60 * 60)

        for backup_file in self.backup_dir.glob("backup_*.zip"):
            if backup_file.stat().st_mtime < cutoff_time:
                backup_file.unlink()
                print(f"🗑️  Backup antigo removido: {backup_file.name}")

    def restore_backup(self, backup_file):
        """Restaura um backup específico"""
        backup_path = self.backup_dir / backup_file

        if not backup_path.exists():
            print(f"❌ Backup não encontrado: {backup_file}")
            return False

        try:
            # Faz backup do estado atual antes de restaurar
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            current_backup = self.backup_dir / f"pre_restore_{timestamp}.db"
            shutil.copy2(self.db_path, current_backup)

            # Extrai e restaura
            with zipfile.ZipFile(backup_path, "r") as zipf:
                zipf.extractall(self.backup_dir)
                extracted_db = self.backup_dir / backup_file.replace(".zip", ".db")
                shutil.copy2(extracted_db, self.db_path)
                extracted_db.unlink()

            print(f"✅ Backup restaurado: {backup_file}")
            return True
        except Exception as e:
            print(f"❌ Erro ao restaurar backup: {e}")
            return False

    def list_backups(self):
        """Lista todos os backups disponíveis"""
        backups = sorted(self.backup_dir.glob("backup_*.zip"), reverse=True)
        return [b.name for b in backups]

    def schedule_daily_backup(self, time_str="02:00"):
        """Agenda backup diário"""
        schedule.every().day.at(time_str).do(self.create_backup)
        print(f"📅 Backup diário agendado para {time_str}")

        # Loop para manter o agendamento ativo
        while True:
            schedule.run_pending()
            time.sleep(60)


if __name__ == "__main__":
    # Exemplo de uso
    db_path = "instance/mercadinho.db"
    backup_manager = BackupManager(db_path)

    # Criar backup manual
    backup_manager.create_backup()

    # Listar backups
    print("\n📦 Backups disponíveis:")
    for backup in backup_manager.list_backups():
        print(f"  - {backup}")
