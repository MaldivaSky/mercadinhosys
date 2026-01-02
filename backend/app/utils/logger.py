"""
app/utils/logger.py
Sistema de logging estruturado
"""

import logging
import json
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler


class StructuredLogger:
    """Logger com formatação estruturada JSON"""

    def __init__(self, name="mercadinhosys", log_dir="logs"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        # Cria diretório de logs
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

        # Handler para arquivo (rotativo)
        file_handler = RotatingFileHandler(
            log_path / "app.log", maxBytes=10 * 1024 * 1024, backupCount=5  # 10MB
        )
        file_handler.setFormatter(self.JsonFormatter())

        # Handler para console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(self.HumanFormatter())

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    class JsonFormatter(logging.Formatter):
        """Formata logs em JSON"""

        def format(self, record):
            log_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
            }

            if hasattr(record, "extra"):
                log_data.update(record.extra)

            if record.exc_info:
                log_data["exception"] = self.formatException(record.exc_info)

            return json.dumps(log_data)

    class HumanFormatter(logging.Formatter):
        """Formata logs para leitura humana"""

        def format(self, record):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return f"[{timestamp}] {record.levelname:8} | {record.module:20} | {record.getMessage()}"

    def info(self, message, **kwargs):
        """Log de informação"""
        self.logger.info(message, extra=kwargs)

    def error(self, message, **kwargs):
        """Log de erro"""
        self.logger.error(message, extra=kwargs)

    def warning(self, message, **kwargs):
        """Log de aviso"""
        self.logger.warning(message, extra=kwargs)

    def debug(self, message, **kwargs):
        """Log de debug"""
        self.logger.debug(message, extra=kwargs)


# Instância global do logger
app_logger = StructuredLogger()
