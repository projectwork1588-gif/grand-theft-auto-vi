"""Database TLS (Render + a managed MySQL). With DB_SSL_CA set, the connection verifies the server's certificate AND host name; production refuses to start
without it. Development and tests keep their old behaviour when it is not set. The CA certificate itself is never committed (tests/tls_helpers.py holds throwaway
test certificates only)."""
import os
import re
from pathlib import Path

import mysql.connector
import pytest
from mysql.connector.connection import MySQLConnection

from app import config
from tests import tls_helpers

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = "https://valkyrie.example.org"


@pytest.fixture()
def production(monkeypatch, db_ca_file):
    """ProductionConfig with every setting valid (DB_SSL_CA included); each test breaks exactly one."""
    monkeypatch.setattr(config.ProductionConfig, "SECRET_KEY", "5f3a9c1e7b2d4a60" * 4)
    monkeypatch.setattr(config.ProductionConfig, "PUBLIC_ORIGINS", (PUBLIC,))
    monkeypatch.setattr(config.ProductionConfig, "DB_NAME", "gta6_vi")
    monkeypatch.setattr(config.ProductionConfig, "TRUSTED_PROXY_COUNT", 0)
    monkeypatch.setattr(config.ProductionConfig, "DB_SSL_CA", db_ca_file)
    assert config.get_config("production") is config.ProductionConfig
    return monkeypatch


# ------------------------------------------------------------------ the connection options
@pytest.mark.parametrize("cls", [config.DevelopmentConfig, config.TestingConfig, config.ProductionConfig])
def test_without_a_ca_the_connection_options_are_exactly_what_they_were(monkeypatch, cls):
    monkeypatch.setattr(cls, "DB_SSL_CA", "")
    kwargs = cls.db_kwargs()
    assert not [key for key in kwargs if key.startswith(("ssl_", "tls_"))]
    assert kwargs["charset"] == "utf8mb4" and kwargs["collation"] == "utf8mb4_0900_ai_ci" and kwargs["connection_timeout"] == 5 and kwargs["use_pure"] is True


def test_with_a_ca_the_certificate_and_the_host_name_are_both_verified(monkeypatch, db_ca_file):
    monkeypatch.setattr(config.TestingConfig, "DB_SSL_CA", "")
    plain = config.TestingConfig.db_kwargs()
    monkeypatch.setattr(config.TestingConfig, "DB_SSL_CA", db_ca_file)
    kwargs = config.TestingConfig.db_kwargs()
    assert kwargs["ssl_ca"] == db_ca_file and kwargs["ssl_verify_cert"] is True and kwargs["ssl_verify_identity"] is True
    assert "ssl_disabled" not in kwargs and "tls_versions" not in kwargs                       # TLS stays on, at the connector's default versions (TLS 1.2 and newer)
    assert {key: value for key, value in kwargs.items() if not key.startswith("ssl_")} == plain       # nothing else changed
    migration = config.TestingConfig.migration_kwargs()
    assert migration["ssl_verify_cert"] is True and migration["ssl_verify_identity"] is True        # the setup account (run from a laptop) is verified the same way


def test_the_installed_connector_accepts_exactly_these_options(monkeypatch, db_ca_file):
    """The option names are checked against the installed mysql-connector-python without opening a connection: it raises AttributeError for an unsupported argument."""
    monkeypatch.setattr(config.TestingConfig, "DB_SSL_CA", db_ca_file)
    connection = MySQLConnection()
    connection.config(**config.TestingConfig.db_kwargs())


def test_a_server_certificate_not_signed_by_the_configured_ca_is_refused_by_the_real_connector(monkeypatch, tmp_path):
    """Against the real local TEST server: a CA that did not sign the server's certificate (or a server without TLS) is an error raised before any login. The
    options are not silently ignored and the connection never falls back to an unverified or unencrypted one."""
    other_ca = tmp_path / "other-ca.pem"
    other_ca.write_text(tls_helpers.TEST_CA_PEM, encoding="ascii")
    monkeypatch.setattr(config.TestingConfig, "DB_SSL_CA", str(other_ca))
    assert config.TestingConfig.DB_NAME.endswith("_test")
    with pytest.raises(mysql.connector.Error) as refused:
        mysql.connector.connect(**config.TestingConfig.db_kwargs())
    assert "Access denied" not in str(refused.value) and getattr(refused.value, "errno", None) != 1045      # it failed on the certificate, not on the password


# ------------------------------------------------------------------ production fails closed
@pytest.mark.parametrize("value", [None, "", "   "])
def test_production_refuses_to_start_without_a_ca(production, value):
    production.setattr(config.ProductionConfig, "DB_SSL_CA", value)
    with pytest.raises(RuntimeError, match="DB_SSL_CA is not set"):
        config.get_config("production")


@pytest.mark.parametrize("make", ["missing", "directory", "empty", "text", "leaf"])
def test_production_refuses_a_ca_file_that_is_not_a_usable_ca_certificate(production, tmp_path, make):
    path = tmp_path / "db-ca.pem"
    if make == "directory":
        path.mkdir()
    elif make == "empty":
        path.write_text("", encoding="ascii")
    elif make == "text":
        path.write_text("this is not a certificate\n", encoding="ascii")
    elif make == "leaf":
        path.write_text(tls_helpers.TEST_LEAF_PEM, encoding="ascii")          # a valid certificate, but not a CA: it cannot anchor the check
    production.setattr(config.ProductionConfig, "DB_SSL_CA", str(path))
    with pytest.raises(RuntimeError, match="DB_SSL_CA|CA certificate") as refused:
        config.get_config("production")
    assert str(path) not in str(refused.value) and "BEGIN CERTIFICATE" not in str(refused.value)         # the message names the setting, never a path or contents


def test_production_accepts_a_real_ca_file_and_builds_verifying_options(production, db_ca_file):
    options = config.ProductionConfig.db_kwargs()
    assert options["ssl_ca"] == db_ca_file and options["ssl_verify_cert"] is True and options["ssl_verify_identity"] is True


@pytest.mark.parametrize("weaker", [
    {"ssl_verify_cert": False, "ssl_verify_identity": True},
    {"ssl_verify_cert": True, "ssl_verify_identity": False},
    {"ssl_verify_cert": True, "ssl_verify_identity": True, "ssl_disabled": True},
])
def test_production_refuses_to_start_if_the_options_ever_stop_verifying(production, db_ca_file, weaker):
    """A later edit that weakened the connection options must stop the site from starting rather than quietly connect without the checks."""
    options = {"ssl_ca": db_ca_file, **weaker}
    production.setattr(config.ProductionConfig, "db_kwargs", classmethod(lambda cls: dict(options)))
    with pytest.raises(RuntimeError, match="verification"):
        config.get_config("production")


def test_the_startup_line_does_not_name_the_ca_path(production, db_ca_file):
    from app import create_app
    import logging
    records = []

    class Catch(logging.Handler):
        def emit(self, record):
            records.append(record.getMessage())

    handler = Catch()
    logger = logging.getLogger("app")
    logger.addHandler(handler)
    try:
        create_app("production")
    finally:
        logger.removeHandler(handler)
    line = next(text for text in records if text.startswith("Starting with ProductionConfig"))
    assert "database certificate verified: yes" in line and db_ca_file not in line


# ------------------------------------------------------------------ nothing secret or certificate-like is committed
def test_env_example_documents_the_setting_but_leaves_it_commented_out_and_empty_of_any_real_path():
    example = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert re.search(r"^# DB_SSL_CA=/etc/secrets/[A-Za-z0-9._-]+\.pem$", example, re.MULTILINE)
    assert not re.search(r"^DB_SSL_CA=", example, re.MULTILINE)              # a copy of the file does not switch it on by itself


def test_no_certificate_or_key_file_is_part_of_the_source_tree():
    """The database CA certificate comes from the host (a secret file). The only certificates in the repository are the throwaway PEM strings in tests/tls_helpers.py."""
    skipped = {".git", ".venv", "node_modules", "media", "review", "backups", ".claude", "__pycache__", ".pytest_cache"}
    found = []
    for folder, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in skipped]
        found += [str(Path(folder, name).relative_to(ROOT)) for name in files if name.lower().endswith((".pem", ".crt", ".cer", ".key", ".p12", ".pfx"))]
    assert found == [], f"certificate or key files in the source tree: {found}"
    helpers = (ROOT / "tests" / "tls_helpers.py").read_text(encoding="utf-8")
    assert "PRIVATE KEY" not in helpers
