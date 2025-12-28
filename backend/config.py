import os
from pathlib import Path

# Caminho absoluto
basedir = Path(__file__).parent.absolute()


class Config:
    SECRET_KEY = "sua-chave-secreta-2025-mercadinho"

    # Banco de dados - SQLite na pasta instance
    db_path = basedir / "instance" / "mercadinho.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)  # Cria pasta

    SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT
    JWT_SECRET_KEY = "sua-chave-jwt-mercadinho-2025"

    # CORS
    CORS_HEADERS = "Content-Type"
    # CORS - PERMITE REQUISIÇÕES DO FRONTEND
    CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # Upload folder
    UPLOAD_FOLDER = basedir / "instance" / "uploads"

    # Tamanho máximo de upload (16MB)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024


# Objeto config que o Flask espera
config = {"development": Config, "production": Config, "default": Config}
