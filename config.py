import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent


def _as_bool(value, default=False):
    if value is None:
        return default

    return value.strip().lower() in {"1", "true", "yes", "on"}


def resolve_database_uri(database_url=None):
    database_url = database_url or os.getenv(
        "DATABASE_URL",
        "sqlite:///task_manager_api.db"
    )

    if database_url.startswith("sqlite:///") and not database_url.startswith("sqlite:////"):
        db_name = database_url.removeprefix("sqlite:///")
        db_path = (BASE_DIR / db_name).resolve()
        return f"sqlite:///{db_path.as_posix()}"

    return database_url


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "devkey")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-in-production")

    SQLALCHEMY_DATABASE_URI = resolve_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", "30"))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        days=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES_DAYS", "30"))
    )

    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_HEADERS_ENABLED = True
    RATELIMIT_DEFAULT = os.getenv("RATELIMIT_DEFAULT", "200 per day")

    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")
    CREATE_DB_ON_STARTUP = _as_bool(os.getenv("CREATE_DB_ON_STARTUP"), True)
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
    JSON_SORT_KEYS = False
    TESTING = False
    DEBUG = False


class TestingConfig(Config):
    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(minutes=30)
    RATELIMIT_ENABLED = False
    CREATE_DB_ON_STARTUP = True
