import os
from pathlib import Path
from urllib.parse import urlparse
from dotenv import load_dotenv

basedir = Path(__file__).parent.absolute()
db_path = Path("c:/temp/mercadinho_instance/mercadinho.db")

# Carrega .env cedo para que todas as variáveis estejam disponíveis
# antes da avaliação das classes de configuração.
load_dotenv(dotenv_path=basedir / ".env", override=False)


# ==================== HYBRID DATABASE CONFIGURATION ====================
# Hybrid Logic: Cloud First, Local Fallback
# CLOUD_ENABLED: 'true' (default, use cloud if possible), 'false' (standalone local only)
# HYBRID_MODE: 'online' (try cloud, fallback), 'offline' (straight to local)

_cloud_enabled = os.environ.get("CLOUD_ENABLED", "true").lower() == "true"
_hybrid_mode = os.environ.get("HYBRID_MODE", "online").lower()
_database_url = (
    os.environ.get("DATABASE_URL_TARGET")
    or os.environ.get("DB_PRIMARY")
    or os.environ.get("DATABASE_URL")
    or os.environ.get("POSTGRES_URL")
    or os.environ.get("AIVEN_DATABASE_URL")
)

_using_postgres = False
_sqlalchemy_database_uri = None
_db_source = "DEFAULT"

# Caminho padrão para SQLite (Instalável / Fallback)
_local_sqlite_uri = f"sqlite:///{os.path.join(basedir, 'instance', 'mercadinho_local.db')}"

if not _cloud_enabled or _hybrid_mode == "offline":
    _sqlalchemy_database_uri = _local_sqlite_uri
    _db_source = "LOCAL_ONLY"
    reason = "CLOUD_ENABLED=false" if not _cloud_enabled else "HYBRID_MODE=offline"
    print(f"[DB: HYBRID] Mode: {reason} | Using Local SQLite: {_sqlalchemy_database_uri}")
else:
    # Tentar configurar Cloud (Postgres)
    if _database_url:
        if _database_url.startswith("postgres://"):
            _database_url = _database_url.replace("postgres://", "postgresql://", 1)
        
        _sqlalchemy_database_uri = _database_url
        _using_postgres = _database_url.startswith("postgresql://")
        _db_source = "CLOUD_ENV"
        
        if _using_postgres:
            print(f"[DB: HYBRID] Mode: ONLINE | Source: CLOUD (Postgres)")
        else:
            print(f"[DB: HYBRID] Mode: ONLINE | Source: CLOUD (SQLite via URL?)")
    else:
        # Sem URL de nuvem configura automaticamente para local
        _sqlalchemy_database_uri = _local_sqlite_uri
        _db_source = "AUTO_LOCAL"
        print(f"[DB: HYBRID] Mode: ONLINE | No Cloud URL found. Fallback to Local SQLite.")

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-fallback-secret-key-12345"
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY") or "dev-fallback-jwt-key-67890"

    SQLALCHEMY_DATABASE_URI = _sqlalchemy_database_uri
    USING_POSTGRES = _using_postgres

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,  # Aumentado para 5 minutos
        "pool_size": 10,      # Aumentado para suportar mais threads
        "max_overflow": 20,   # Margem de manobra maior
        "pool_timeout": 30,   # Esperar até 30s por uma conexão livre
        "connect_args": {
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5,
            "connect_timeout": 10,
            # "options": "-c statement_timeout=30000" # Removido para compatibilidade Neon/PgBouncer
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
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD") or os.environ.get("EMAIL_APP_PASSWORD")
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
