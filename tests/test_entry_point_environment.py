"""Review finding: an unset FLASK_ENV used to start a deployment with development settings (random per-process secret key, cookie without Secure, the request's own
host as the allowed origin). wsgi.py now refuses that case; only the Flask command line (the documented local run) falls back to development.
Nothing here connects to a production database: building an app only creates a lazy pool, and the *_test guard in get_config() is exercised, not bypassed."""
import importlib
import logging
import re
import sys
from pathlib import Path

import pytest

from app import config, create_app

PUBLIC = "https://valkyrie.example.org"
GOOD_SECRET = "5f3a9c1e7b2d4a60" * 4
ROOT = Path(__file__).resolve().parent.parent


def load_wsgi():
    """Import wsgi.py afresh (its top level builds the app, which is exactly what a WSGI server does)."""
    sys.modules.pop("wsgi", None)
    try:
        return importlib.import_module("wsgi")
    finally:
        sys.modules.pop("wsgi", None)


@pytest.fixture()
def environment(monkeypatch):
    """Start from a clean slate: neither FLASK_ENV nor the Flask command line's marker is set (the real .env was already read when the app package was imported)."""
    monkeypatch.delenv("FLASK_ENV", raising=False)
    monkeypatch.delenv("FLASK_RUN_FROM_CLI", raising=False)
    return monkeypatch


@pytest.fixture()
def valid_production(environment):
    environment.setattr(config.ProductionConfig, "SECRET_KEY", GOOD_SECRET)
    environment.setattr(config.ProductionConfig, "PUBLIC_ORIGINS", (PUBLIC,))
    environment.setattr(config.ProductionConfig, "DB_NAME", "gta6_vi")
    environment.setattr(config.ProductionConfig, "TRUSTED_PROXY_COUNT", 0)
    return environment


# ------------------------------------------------------------------ the selection rule itself
def test_a_set_value_is_passed_on_unchanged_for_get_config_to_judge():
    for value in ("production", "development", "testing", "prod", "", "  "):
        assert config.deployment_config_name({"FLASK_ENV": value}) == value


def test_unset_under_the_flask_command_line_is_development():
    assert config.deployment_config_name({"FLASK_RUN_FROM_CLI": "true"}) == "development"


def test_the_command_line_marker_does_not_override_an_explicit_value():
    assert config.deployment_config_name({"FLASK_ENV": "production", "FLASK_RUN_FROM_CLI": "true"}) == "production"


@pytest.mark.parametrize("environ", [{}, {"FLASK_RUN_FROM_CLI": "false"}, {"FLASK_RUN_FROM_CLI": ""}, {"FLASK_RUN_FROM_CLI": "1"}, {"SECRET_KEY": "x" * 40}])
def test_unset_under_any_other_server_refuses_to_start(environ):
    with pytest.raises(RuntimeError, match="FLASK_ENV is not set") as error:
        config.deployment_config_name(environ)
    message = str(error.value)
    assert "FLASK_ENV=production" in message and "x" * 40 not in message          # it names the setting, never a value


# ------------------------------------------------------------------ the real entry point (wsgi.py)
def test_wsgi_with_flask_env_unset_does_not_start_as_development(environment):
    with pytest.raises(RuntimeError, match="FLASK_ENV is not set"):
        load_wsgi()


def test_wsgi_with_flask_env_unset_still_works_for_the_flask_command_line(environment):
    environment.setenv("FLASK_RUN_FROM_CLI", "true")
    module = load_wsgi()
    assert module.app.config["CONFIG_NAME"] == "DevelopmentConfig"


def test_wsgi_with_explicit_development_starts_as_development(environment):
    environment.setenv("FLASK_ENV", "development")
    module = load_wsgi()
    assert module.app.config["CONFIG_NAME"] == "DevelopmentConfig" and module.app.config["SESSION_COOKIE_SECURE"] is False


def test_wsgi_with_valid_production_starts_with_secure_settings(valid_production):
    valid_production.setenv("FLASK_ENV", "production")
    app = load_wsgi().app
    assert app.config["CONFIG_NAME"] == "ProductionConfig"
    assert app.config["SESSION_COOKIE_SECURE"] is True
    assert app.config["SECRET_KEY"] == GOOD_SECRET and app.config["PUBLIC_ORIGINS"] == (PUBLIC,)


@pytest.mark.parametrize("breakage, message", [
    ({"SECRET_KEY": "replace-with-a-long-random-string"}, "SECRET_KEY"),
    ({"SECRET_KEY": "short"}, "SECRET_KEY"),
    ({"PUBLIC_ORIGINS": ()}, "TV_PUBLIC_ORIGINS is not set"),
    ({"PUBLIC_ORIGINS": ("http://valkyrie.example.org",)}, "https"),
    ({"DB_NAME": "gta6_vi_test"}, "test database"),
])
def test_wsgi_with_invalid_production_refuses_to_start(valid_production, breakage, message):
    valid_production.setenv("FLASK_ENV", "production")
    for name, value in breakage.items():
        valid_production.setattr(config.ProductionConfig, name, value)
    with pytest.raises(RuntimeError, match=message):
        load_wsgi()


@pytest.mark.parametrize("value", ["prod", "Staging", "", "   "])
def test_wsgi_with_a_mistyped_or_blank_flask_env_refuses_to_start(environment, value):
    environment.setenv("FLASK_ENV", value)
    with pytest.raises(RuntimeError, match="Unknown configuration"):
        load_wsgi()


# ------------------------------------------------------------------ create_app() called directly keeps its behaviour but says so out loud
def test_create_app_with_flask_env_unset_still_builds_development_and_warns(environment, caplog):
    with caplog.at_level(logging.WARNING, logger="app"):
        app = create_app()
    assert app.config["CONFIG_NAME"] == "DevelopmentConfig"
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING and "FLASK_ENV is not set" in r.getMessage()]
    assert len(warnings) == 1 and "FLASK_ENV=production" in warnings[0].getMessage()


@pytest.mark.parametrize("name", ["development", "testing"])
def test_create_app_with_an_explicit_name_does_not_warn(environment, caplog, name):
    with caplog.at_level(logging.WARNING, logger="app"):
        create_app(name)
    assert not [r for r in caplog.records if "FLASK_ENV is not set" in r.getMessage()]


def test_create_app_under_the_flask_command_line_does_not_warn(environment, caplog):
    environment.setenv("FLASK_RUN_FROM_CLI", "true")
    with caplog.at_level(logging.WARNING, logger="app"):
        create_app()
    assert not [r for r in caplog.records if "FLASK_ENV is not set" in r.getMessage()]


# ------------------------------------------------------------------ .env.example and the documented commands
def example_values():
    values = {}
    for line in (ROOT / ".env.example").read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"([A-Z_]+)=(.*)", line.strip())
        if match:
            values[match.group(1)] = match.group(2)
    return values


def test_env_example_selects_development_so_a_copy_runs_locally_and_cannot_pass_as_production(environment):
    values = example_values()
    assert values["FLASK_ENV"] == "development"
    environment.setattr(config.ProductionConfig, "SECRET_KEY", values["SECRET_KEY"])         # the placeholder, as someone who forgot to replace it would have
    environment.setattr(config.ProductionConfig, "PUBLIC_ORIGINS", (PUBLIC,))
    environment.setattr(config.ProductionConfig, "DB_NAME", "gta6_vi")
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        config.get_config("production")


def test_the_deployment_variables_in_env_example_stay_commented_out():
    """If TV_PUBLIC_ORIGINS or TV_TRUSTED_PROXIES were live in the example, a copy would silently carry the example host into a real deployment."""
    values = example_values()
    assert "TV_PUBLIC_ORIGINS" not in values and "TV_TRUSTED_PROXIES" not in values
