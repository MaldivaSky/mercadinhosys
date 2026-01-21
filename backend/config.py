import os
from pathlib import Path
from urllib.parse import urlparse

basedir = Path(__file__).parent.absolute()
db_path = Path("c:/temp/mercadinho_instance/mercadinho.db")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")

    # Banco de dados
    DATABASE_URL = os.environ.get("DATABASE_URL")
    SQLITE_DB = os.environ.get("SQLITE_DB")

    if DATABASE_URL:
        if DATABASE_URL.startswith("postgres://"):
            DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    elif SQLITE_DB:
        SQLALCHEMY_DATABASE_URI = SQLITE_DB
    else:
        SQLALCHEMY_DATABASE_URI = "sqlite:///c:/temp/mercadinho_instance/mercadinho.db"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    cors_origins_str = os.environ.get("CORS_ORIGINS", "")
    CORS_ORIGINS = (
        [origin.strip() for origin in cors_origins_str.split(",")]
        if cors_origins_str
        else []
    )

    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")

    JWT_ACCESS_TOKEN_EXPIRES = 3600


class DevelopmentConfig(Config):
    DEBUG = True
    if not Config.CORS_ORIGINS:
        Config.CORS_ORIGINS = ["http://localhost:3000", "http://localhost:5173"]


class ProductionConfig(Config):
    DEBUG = False


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
