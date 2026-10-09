"""Safety rails around which database the app may touch."""
import pytest

from app import config


def test_testing_config_uses_test_database():
    assert config.get_config("testing").DB_NAME.endswith("_test")


def test_testing_config_refuses_non_test_database(monkeypatch):
    monkeypatch.setattr(config.TestingConfig, "DB_NAME", "gta6_vi")
    with pytest.raises(RuntimeError):
        config.get_config("testing")


def test_development_config_refuses_test_database(monkeypatch):
    monkeypatch.setattr(config.DevelopmentConfig, "DB_NAME", "gta6_vi_test")
    with pytest.raises(RuntimeError):
        config.get_config("development")


def test_connection_uses_strict_utf8mb4():
    kwargs = config.TestingConfig.db_kwargs()
    assert kwargs["charset"] == "utf8mb4"
    assert "STRICT_ALL_TABLES" in kwargs["sql_mode"]
    assert kwargs["user"] != "root"
