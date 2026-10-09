"""Configuration, read from environment variables (and a local .env file).

Nothing secret lives in the source code: copy .env.example to .env and edit it.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def _int(name, default):
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return int(default)


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-insecure-key")
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = _int("DB_PORT", 3306)
    DB_NAME = os.getenv("DB_NAME", "gta6_vi")
    DB_USER = os.getenv("DB_USER", "valkyrie_app")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    # Separate account used ONLY by scripts that create/drop tables (never by the running site).
    MIGRATE_DB_USER = os.getenv("MIGRATE_DB_USER", "valkyrie_migrator")
    MIGRATE_DB_PASSWORD = os.getenv("MIGRATE_DB_PASSWORD", "")
    DB_POOL_SIZE = 5
    TESTING = False

    @classmethod
    def db_kwargs(cls):
        """Arguments for mysql.connector.connect(). Strict mode and utf8mb4 are explicit."""
        return {
            "host": cls.DB_HOST,
            "port": cls.DB_PORT,
            "database": cls.DB_NAME,
            "user": cls.DB_USER,
            "password": cls.DB_PASSWORD,
            "charset": "utf8mb4",
            "collation": "utf8mb4_0900_ai_ci",
            "sql_mode": "STRICT_ALL_TABLES,NO_ENGINE_SUBSTITUTION,ONLY_FULL_GROUP_BY",
            "use_pure": True,
            "connection_timeout": 5,
        }

    @classmethod
    def migration_kwargs(cls):
        """Same as db_kwargs() but for the schema-changing account."""
        kwargs = cls.db_kwargs()
        kwargs["user"] = cls.MIGRATE_DB_USER
        kwargs["password"] = cls.MIGRATE_DB_PASSWORD
        return kwargs


class DevelopmentConfig(Config):
    pass


class TestingConfig(Config):
    """Uses the separate *_test database so tests can never touch real data."""

    TESTING = True
    DB_NAME = os.getenv("TEST_DB_NAME", "gta6_vi_test")


def get_config(name=None):
    name = (name or os.getenv("FLASK_ENV", "development")).lower()
    config = TestingConfig if name == "testing" else DevelopmentConfig
    if config is TestingConfig and not config.DB_NAME.endswith("_test"):
        raise RuntimeError("Refusing to run tests: TEST_DB_NAME must end with '_test'.")
    if config is DevelopmentConfig and config.DB_NAME.endswith("_test"):
        raise RuntimeError("DB_NAME must not be the test database.")
    return config
