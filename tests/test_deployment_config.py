"""Phase 2C: which origins may submit forms, when forwarded headers are believed, and what production refuses to start with.
Nothing here starts a production app or connects to a production database: get_config() only returns a class. Rows are committed to the *_test database only."""
import pytest

from app import config, create_app
from tests import account_helpers as h

pytestmark = pytest.mark.usefixtures("clean_accounts")
PUBLIC = "https://valkyrie.example.org"


def register_from(client, origin=None, base_url=None, send_origin=True, name=None):
    """Fetch the form and submit it from `base_url`, sending `origin` as the Origin header. Returns the response (and the username)."""
    extra = {"base_url": base_url} if base_url else {}
    token = h.csrf_from(client.get("/register", **extra).get_data(as_text=True))
    name = name or h.new_username()
    headers = {"Origin": origin} if origin is not None and send_origin else {}
    response = client.post("/register", data={"username": name, "password": h.PASSWORD, "password_confirm": h.PASSWORD, "csrf_token": token}, headers=headers, **extra)
    response.username = name
    return response


# ------------------------------------------------------------------ origins without configuration: the request's own scheme, host and port
@pytest.mark.parametrize("origin, accepted", [
    ("http://localhost", True),
    ("HTTP://LOCALHOST", True),
    ("http://localhost/", True),
    ("https://localhost", False),             # wrong scheme
    ("http://localhost:5000", False),         # wrong port
    ("http://evil.example", False),
    ("http://localhost.evil.example", False),
    ("http://evil.example/localhost", False),
    ("null", False),
    ("", False),
    ("not a url", False),
])
def test_without_configuration_the_origin_must_be_this_request_itself(app, origin, accepted):
    response = register_from(app.test_client(), origin)
    assert response.status_code == (303 if accepted else 400), origin
    assert (h.user_row(response.username) is not None) == accepted


def test_a_request_without_an_origin_header_is_decided_by_the_token_alone(app):
    assert register_from(app.test_client(), send_origin=False).status_code == 303


# ------------------------------------------------------------------ TV_PUBLIC_ORIGINS
@pytest.fixture()
def public_app(monkeypatch):
    monkeypatch.setattr(config.TestingConfig, "PUBLIC_ORIGINS", (PUBLIC,))
    return create_app("testing")


@pytest.mark.parametrize("origin, accepted", [
    (PUBLIC, True),
    (PUBLIC + "/", True),
    (PUBLIC.upper(), True),
    ("http://valkyrie.example.org", False),               # the scheme matters
    ("https://valkyrie.example.org:8443", False),         # so does the port
    ("https://www.valkyrie.example.org", False),
    ("https://valkyrie.example.org.evil.example", False),
    ("https://evil.example", False),
    ("null", False),
])
def test_with_public_origins_only_those_origins_may_submit(public_app, origin, accepted):
    response = register_from(public_app.test_client(), origin, base_url=PUBLIC)
    assert response.status_code == (303 if accepted else 400), origin
    assert (h.user_row(response.username) is not None) == accepted


def test_a_forged_host_header_cannot_make_an_attacker_origin_acceptable(public_app):
    """Without configuration the request's own host is the reference, and a client can choose it. With TV_PUBLIC_ORIGINS the Host header is not consulted."""
    response = register_from(public_app.test_client(), "https://evil.example", base_url="https://evil.example")
    assert response.status_code == 400 and h.user_row(response.username) is None


def test_the_token_is_still_required_when_the_origin_is_right(public_app):
    client = public_app.test_client()
    client.get("/register", base_url=PUBLIC)
    response = client.post("/register", data={"username": h.new_username(), "password": h.PASSWORD, "password_confirm": h.PASSWORD}, headers={"Origin": PUBLIC}, base_url=PUBLIC)
    assert response.status_code == 400


# ------------------------------------------------------------------ forwarded headers
def with_address_route(app):
    from flask import request

    @app.get("/_address")
    def address():
        return request.remote_addr
    return app


def test_forwarded_headers_are_ignored_unless_proxies_are_trusted(app):
    probe = with_address_route(create_app("testing"))
    client = probe.test_client()
    response = client.get("/_address", headers={"X-Forwarded-For": "198.51.100.77", "X-Forwarded-Proto": "https", "X-Forwarded-Host": "evil.example"},
                          environ_overrides={"REMOTE_ADDR": "10.0.0.1"})
    assert response.get_data(as_text=True) == "10.0.0.1"
    assert probe.config["TRUSTED_PROXY_COUNT"] == 0


def test_spoofing_a_forwarded_address_does_not_escape_the_login_throttle(app):
    name = h.signed_in_client(app)[1]
    client = app.test_client()
    for i in range(app.config["LOGIN_MAX_FAILURES"]):
        token = h.csrf_from(client.get("/login").get_data(as_text=True))
        client.post("/login", data={"username": name, "password": "wrong password!!", "csrf_token": token}, headers={"X-Forwarded-For": f"203.0.113.{i}"})
    token = h.csrf_from(client.get("/login").get_data(as_text=True))
    blocked = client.post("/login", data={"username": name, "password": h.PASSWORD, "csrf_token": token}, headers={"X-Forwarded-For": "192.0.2.200"})
    assert blocked.status_code == 429


def test_one_trusted_proxy_means_the_right_hand_forwarded_address_is_the_client(monkeypatch):
    monkeypatch.setattr(config.TestingConfig, "TRUSTED_PROXY_COUNT", 1)
    probe = with_address_route(create_app("testing"))
    client = probe.test_client()
    # the proxy appended the address it saw; whatever the client put to the left of it is not believed
    response = client.get("/_address", headers={"X-Forwarded-For": "1.2.3.4, 198.51.100.77"}, environ_overrides={"REMOTE_ADDR": "10.0.0.1"})
    assert response.get_data(as_text=True) == "198.51.100.77"
    assert client.get("/_address", environ_overrides={"REMOTE_ADDR": "10.0.0.1"}).get_data(as_text=True) == "10.0.0.1"      # no header: the connection itself


def test_trusted_proxies_never_make_the_host_header_forwardable(monkeypatch):
    monkeypatch.setattr(config.TestingConfig, "TRUSTED_PROXY_COUNT", 1)
    probe = create_app("testing")

    @probe.get("/_host")
    def host():
        from flask import request
        return request.host
    response = probe.test_client().get("/_host", headers={"X-Forwarded-Host": "evil.example"}, base_url="http://real.example")
    assert response.get_data(as_text=True) == "real.example"


def test_the_number_of_trusted_proxies_is_range_checked(monkeypatch):
    for bad in (-1, config.MAX_TRUSTED_PROXIES + 1, 99):
        monkeypatch.setattr(config.TestingConfig, "TRUSTED_PROXY_COUNT", bad)
        with pytest.raises(RuntimeError, match="TV_TRUSTED_PROXIES"):
            config.get_config("testing")


# ------------------------------------------------------------------ environments never fall back quietly
@pytest.mark.parametrize("name", ["prod", "Prod", "staging", "", "  ", "devel", "test"])
def test_an_unknown_environment_name_is_an_error_not_development(name):
    with pytest.raises(RuntimeError, match="Unknown configuration"):
        config.get_config(name)


def test_a_mistyped_flask_env_stops_the_site_from_starting(monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "prod")
    with pytest.raises(RuntimeError, match="Unknown configuration"):
        config.get_config()
    with pytest.raises(RuntimeError):
        create_app()


def test_development_and_testing_workflows_are_unchanged(monkeypatch):
    monkeypatch.delenv("FLASK_ENV", raising=False)
    assert config.get_config() is config.DevelopmentConfig
    assert config.get_config("development") is config.DevelopmentConfig and config.get_config("testing") is config.TestingConfig
    assert config.get_config(" Testing ") is config.TestingConfig
    assert config.TestingConfig.PUBLIC_ORIGINS == () and config.TestingConfig.TRUSTED_PROXY_COUNT == 0


# ------------------------------------------------------------------ production
@pytest.fixture()
def production(monkeypatch, db_ca_file):
    """ProductionConfig with every setting valid; each test breaks exactly one."""
    monkeypatch.setattr(config.ProductionConfig, "SECRET_KEY", "5f3a9c1e7b2d4a60" * 4)
    monkeypatch.setattr(config.ProductionConfig, "PUBLIC_ORIGINS", (PUBLIC,))
    monkeypatch.setattr(config.ProductionConfig, "DB_NAME", "gta6_vi")
    monkeypatch.setattr(config.ProductionConfig, "TRUSTED_PROXY_COUNT", 0)
    monkeypatch.setattr(config.ProductionConfig, "DB_SSL_CA", db_ca_file)
    assert config.get_config("production") is config.ProductionConfig
    return monkeypatch


@pytest.mark.parametrize("name", ["gta6_vi_test", "anything_test", config.TestingConfig.DB_NAME])
def test_production_refuses_a_test_database(production, name):
    production.setattr(config.ProductionConfig, "DB_NAME", name)
    with pytest.raises(RuntimeError, match="test database"):
        config.get_config("production")


@pytest.mark.parametrize("secret", [None, "", "dev-only-insecure-key", "replace-with-a-long-random-string", "short", "a" * 64, "ab" * 32, "0123" * 2])
def test_production_refuses_a_missing_known_short_or_repetitive_secret(production, secret):
    production.setattr(config.ProductionConfig, "SECRET_KEY", secret)
    with pytest.raises(RuntimeError, match="SECRET_KEY") as refused:
        config.get_config("production")
    assert not secret or secret not in str(refused.value)


def test_a_generated_secret_is_accepted_and_the_documented_command_makes_one():
    import secrets
    for _ in range(20):
        config.check_secret_key(secrets.token_hex(32))
        config.check_secret_key(secrets.token_urlsafe(48))


@pytest.mark.parametrize("origins, message", [
    ((), "TV_PUBLIC_ORIGINS is not set"),
    (("http://valkyrie.example.org",), "https"),
    (("https://valkyrie.example.org/path",), "bare origins"),
    (("https://user:pw@valkyrie.example.org",), "bare origins"),
    (("valkyrie.example.org",), "bare origins"),
    (("https://valkyrie.example.org", "ftp://x.example"), "bare origins"),
])
def test_production_needs_https_public_origins(production, origins, message):
    production.setattr(config.ProductionConfig, "PUBLIC_ORIGINS", origins)
    with pytest.raises(RuntimeError, match=message):
        config.get_config("production")


def test_production_marks_the_cookie_secure_and_never_uses_the_random_fallback(production):
    assert config.ProductionConfig.SESSION_COOKIE_SECURE is True
    assert config.ProductionConfig.SECRET_KEY == "5f3a9c1e7b2d4a60" * 4


def test_malformed_origins_are_refused_in_every_environment(monkeypatch):
    monkeypatch.setattr(config.TestingConfig, "PUBLIC_ORIGINS", ("https://ok.example", "https://bad.example/with/path"))
    with pytest.raises(RuntimeError, match="bare origins"):
        config.get_config("testing")


def test_normalise_origin():
    assert config.normalise_origin(" HTTPS://Example.ORG/ ") == "https://example.org"
    assert config.normalise_origin("http://localhost:5000") == "http://localhost:5000"
    for bad in ("", None, "example.org", "ftp://example.org", "https://example.org/a", "https://example.org?x=1", "https://a@example.org", "https://"):
        assert config.normalise_origin(bad) is None, bad
