import os
from pathlib import Path
from urllib.parse import urlparse

basedir = Path(__file__).parent.absolute()
db_path = Path("c:/temp/mercadinho_instance/mercadinho.db")


# ==================== DATABASE CONFIGURATION ====================
_database_url = (
    os.environ.get("DATABASE_URL_TARGET")
    or os.environ.get("DB_PRIMARY")
    or os.environ.get("DATABASE_URL")
    or os.environ.get("POSTGRES_URL")
)
_sqlite_db = os.environ.get("SQLITE_DB")
_using_postgres = False
_sqlalchemy_database_uri = None

if _database_url:
    if _database_url.startswith("postgres://"):
        _database_url = _database_url.replace("postgres://", "postgresql://", 1)
    _sqlalchemy_database_uri = _database_url
    _using_postgres = _database_url.startswith("postgresql://")
    source = "ENV_VAR"
    if os.environ.get("DATABASE_URL_TARGET"): source = "DATABASE_URL_TARGET"
    elif os.environ.get("DB_PRIMARY"): source = "DB_PRIMARY"
    elif os.environ.get("DATABASE_URL"): source = "DATABASE_URL"
    elif os.environ.get("POSTGRES_URL"): source = "POSTGRES_URL"
    
    if _using_postgres:
        print(f"[DB: POSTGRES] Source: {source} | URL: {(_database_url.split('@')[1] if '@' in _database_url else 'cloud')}")
    else:
        print(f"[DB: SQLITE] Source: {source} | URL: {_database_url}")
elif _sqlite_db:
    # Garantir prefixo sqlite:///
    if not _sqlite_db.startswith("sqlite:///"):
        _sqlite_db = f"sqlite:///{_sqlite_db}"
    
    # Se for apenas o nome do arquivo, redirecionar para 'instance/'
    db_relative_path = _sqlite_db[10:] # Tirar 'sqlite:///'
    if not any(c in db_relative_path for c in [':', '\\', '/']):
        instance_path = os.path.join(basedir, 'instance', db_relative_path)
        _sqlalchemy_database_uri = f"sqlite:///{instance_path}"
    else:
        _sqlalchemy_database_uri = _sqlite_db
    print(f"[DB: SQLITE] {_sqlalchemy_database_uri}")
else:
    # Padrão: SQLite na pasta instance
    _sqlalchemy_database_uri = f"sqlite:///{os.path.join(basedir, 'instance', 'mercadinho.db')}"
    print(f"[DB: SQLITE] {_sqlalchemy_database_uri}")

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-fallback-secret-key-12345"
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY") or "dev-fallback-jwt-key-67890"

    SQLALCHEMY_DATABASE_URI = _sqlalchemy_database_uri
    USING_POSTGRES = _using_postgres

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 120,
        "pool_size": 5,
        "max_overflow": 10,
        "connect_args": {
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5,
            "connect_timeout": 10,
        },
    } if _using_postgres else {}

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
    # JWT_SECRET_KEY: manter estável entre restarts; se mudar, tokens em uso passam a retornar 401.
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
