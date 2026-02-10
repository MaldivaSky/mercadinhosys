import os
from pathlib import Path
from urllib.parse import urlparse

basedir = Path(__file__).parent.absolute()
db_path = Path("c:/temp/mercadinho_instance/mercadinho.db")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-fallback-secret-key-12345"
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY") or "dev-fallback-jwt-key-67890"

    # ==================== DATABASE CONFIGURATION ====================
    # Seleção robusta do banco: usa Postgres quando disponível; caso contrário, SQLite cross-platform
    
    DATABASE_URL = (
        os.environ.get("NEON_DATABASE_URL")
        or os.environ.get("DATABASE_URL_TARGET")
        or os.environ.get("DB_PRIMARY")
        or os.environ.get("DATABASE_URL")
        or os.environ.get("POSTGRES_URL")
    )
    SQLITE_DB = os.environ.get("SQLITE_DB")
    USING_POSTGRES = False
    
    if DATABASE_URL:
        if DATABASE_URL.startswith("postgres://"):
            DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
        USING_POSTGRES = DATABASE_URL.startswith("postgresql://")
        if USING_POSTGRES:
            print(f"[DB: POSTGRES] {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'cloud'}")
        else:
            print(f"[DB: SQLITE] {DATABASE_URL}")
    elif SQLITE_DB:
        SQLALCHEMY_DATABASE_URI = SQLITE_DB
        print(f"[DB: SQLITE] {SQLITE_DB}")
    else:
        SQLALCHEMY_DATABASE_URI = "sqlite:///mercadinho.db"
        print(f"[DB: SQLITE] {SQLALCHEMY_DATABASE_URI}")

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,  # Verifica conexão antes de usar
        "pool_recycle": 300,    # Recicla conexões a cada 5 minutos
        "pool_size": 10,        # Pool de 10 conexões
        "max_overflow": 20,     # Até 20 conexões extras
    } if USING_POSTGRES else {}

    # ==================== CORS ====================
    cors_origins_str = os.environ.get("CORS_ORIGINS", "")
    CORS_ORIGINS = (
        [origin.strip() for origin in cors_origins_str.split(",")]
        if cors_origins_str
        else []
    )

    # ==================== EMAIL ====================
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USE_SSL = os.environ.get("MAIL_USE_SSL", "false").lower() == "true"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", os.environ.get("MAIL_USERNAME"))

    # ==================== UPLOADS ====================
    UPLOAD_FOLDER = os.path.join(basedir, "uploads")
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB max

    # ==================== JWT ====================
    JWT_ACCESS_TOKEN_EXPIRES = 3600
    JWT_REFRESH_TOKEN_EXPIRES = 604800  # 7 dias


class DevelopmentConfig(Config):
    DEBUG = True
    if not Config.CORS_ORIGINS:
        Config.CORS_ORIGINS = ["http://localhost:3000", "http://localhost:5173"]


class ProductionConfig(Config):
    DEBUG = False
    # Forçar HTTPS em produção
    PREFERRED_URL_SCHEME = 'https'


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    DEBUG = True

config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
    "testing": TestingConfig,
}
