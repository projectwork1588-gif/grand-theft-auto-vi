"""CSRF protection, session configuration and the production secret check."""
from pathlib import Path

import pytest

from app import config, create_app
from tests import account_helpers as h

pytestmark = pytest.mark.usefixtures("clean_accounts")


# ------------------------------------------------------------------ CSRF
def test_reading_pages_never_needs_a_token(client):
    for path in ("/", "/characters", "/login", "/register", "/api/v1/characters"):
        assert client.get(path).status_code == 200


@pytest.mark.parametrize("path", ["/login", "/register", "/logout", "/account/password", "/favourites/characters/jason-duval", "/favourites/vehicles/grotti-cheetah/remove"])
def test_every_post_route_refuses_a_request_without_a_token(client, path):
    response = client.post(path, data={"username": "tt_x"})
    assert response.status_code == 400 and "form could not be checked" in response.get_data(as_text=True)


@pytest.mark.parametrize("path", ["/characters", "/api/v1/characters", "/garage-concept", "/login", "/account/favourites"])
@pytest.mark.parametrize("method", ["put", "patch", "delete"])
def test_routes_that_do_not_accept_a_method_still_answer_405(client, path, method):
    assert getattr(client, method)(path, data={"x": "1"}).status_code == 405
    assert client.post("/characters", data={"x": "1"}).status_code == 405 and client.post("/api/v1/characters").status_code == 405


def test_a_token_from_another_session_is_refused(app):
    one, two = app.test_client(), app.test_client()
    stolen = h.token(one)
    h.token(two)
    response = two.post("/register", data={"username": h.new_username(), "password": h.PASSWORD, "password_confirm": h.PASSWORD, "csrf_token": stolen})
    assert response.status_code == 400


def test_a_token_in_the_header_is_accepted_as_well_as_one_in_the_form(app):
    client = app.test_client()
    token = h.token(client)
    name = h.new_username()
    response = client.post("/register", data={"username": name, "password": h.PASSWORD, "password_confirm": h.PASSWORD}, headers={"X-CSRF-Token": token})
    assert response.status_code == 303 and h.user_row(name)


def test_a_cross_site_origin_is_refused_even_with_a_valid_token(app):
    client = app.test_client()
    token = h.token(client)
    data = {"username": h.new_username(), "password": h.PASSWORD, "password_confirm": h.PASSWORD, "csrf_token": token}
    assert client.post("/register", data=data, headers={"Origin": "https://evil.example"}).status_code == 400
    assert client.post("/register", data=data, headers={"Origin": "null"}).status_code == 400
    assert client.post("/register", data=data, headers={"Origin": "http://localhost"}).status_code == 303      # the test client's own host


def test_the_token_is_the_same_across_forms_in_one_session_and_unpredictable_across_sessions(app):
    client = app.test_client()
    assert h.token(client, "/login") == h.token(client, "/register")
    tokens = {h.token(app.test_client()) for _ in range(5)}
    assert len(tokens) == 5 and all(len(t) >= 40 for t in tokens)


def test_a_refused_request_changes_nothing_in_the_database(app):
    before = h.rows("SELECT COUNT(*) AS n FROM users")[0]["n"]
    app.test_client().post("/register", data={"username": h.new_username(), "password": h.PASSWORD, "password_confirm": h.PASSWORD})
    assert h.rows("SELECT COUNT(*) AS n FROM users")[0]["n"] == before


def test_every_form_in_the_account_pages_carries_a_token(app):
    client, _ = h.signed_in_client(app)
    for path in ("/account/favourites", "/account/password", "/characters/jason-duval", "/about"):
        page = client.get(path).get_data(as_text=True)
        forms = page.count('method="post"')
        assert forms >= 1 and page.count('name="csrf_token"') >= forms, path


# ------------------------------------------------------------------ session and secret configuration
def test_the_session_settings_are_the_approved_ones(app):
    assert app.config["SESSION_COOKIE_HTTPONLY"] is True and app.config["SESSION_COOKIE_SAMESITE"] == "Lax"
    assert app.config["PERMANENT_SESSION_LIFETIME"].total_seconds() == 8 * 3600
    assert app.config["SESSION_COOKIE_NAME"] == "tv_session"


def test_production_marks_the_cookie_secure_and_has_no_fallback_secret():
    assert config.ProductionConfig.SESSION_COOKIE_SECURE is True
    source = Path(config.__file__).read_text(encoding="utf-8")
    production = source.split("class ProductionConfig")[1].split("class TestingConfig")[0]
    assert 'SECRET_KEY = os.getenv("SECRET_KEY")' in production and "token_hex" not in production      # no random or built-in fallback


@pytest.mark.parametrize("secret", [None, "", "dev-only-insecure-key", "replace-with-a-long-random-string", "CHANGE-ME", "too-short", "x" * 31])
def test_a_missing_known_or_short_secret_is_rejected_without_being_printed(secret):
    with pytest.raises(RuntimeError) as refused:
        config.check_secret_key(secret)
    assert not secret or secret not in str(refused.value)


def test_a_long_random_secret_is_accepted():
    import secrets
    config.check_secret_key(secrets.token_hex(32))                                           # what the documented command produces


def test_the_production_config_refuses_to_load_with_the_development_secret(monkeypatch):
    monkeypatch.setattr(config.ProductionConfig, "SECRET_KEY", "dev-only-insecure-key")
    with pytest.raises(RuntimeError):
        config.get_config("production")
    monkeypatch.setattr(config.ProductionConfig, "SECRET_KEY", None)
    with pytest.raises(RuntimeError):
        config.get_config("production")
    monkeypatch.setattr(config.ProductionConfig, "SECRET_KEY", "5f3a9c1e7b2d4a60" * 4)
    monkeypatch.setattr(config.ProductionConfig, "PUBLIC_ORIGINS", ("https://valkyrie.example.org",))
    monkeypatch.setattr(config.ProductionConfig, "DB_NAME", "gta6_vi")
    assert config.get_config("production") is config.ProductionConfig                       # only the class is returned: nothing connects to a database


def test_the_development_secret_is_never_the_old_well_known_value():
    assert config.DevelopmentConfig.SECRET_KEY not in config.KNOWN_INSECURE_SECRETS and len(config.DevelopmentConfig.SECRET_KEY) >= 32
    assert config.TestingConfig.DB_NAME.endswith("_test")


def test_two_apps_in_one_process_share_one_secret_so_cookies_stay_valid(app):
    assert create_app("testing").config["SECRET_KEY"] == app.config["SECRET_KEY"]
