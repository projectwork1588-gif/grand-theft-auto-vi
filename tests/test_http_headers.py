"""Small HTTP behaviours (Stage 5.4): a 405 says what is allowed (RFC 9110), HSTS is sent only by the production config and only over https, and robots.txt tells crawlers to leave
results, API, account and admin pages alone without needing the database. No database writes."""
import pytest

from app import create_app
from app.blueprints.main import ROBOTS_DISALLOWED, ROBOTS_TXT
from app.config import HSTS_DEFAULT_SECONDS, HSTS_MAX_SECONDS, ProductionConfig, hsts_max_age
from app.repositories import characters as characters_repo

# ------------------------------------------------------------------ 405 carries Allow
CASES = [("PUT", "/", {"GET", "HEAD", "OPTIONS"}), ("PUT", "/login", {"GET", "HEAD", "OPTIONS", "POST"}), ("DELETE", "/characters", {"GET", "HEAD", "OPTIONS"}),
         ("POST", "/characters/jason-duval", {"GET", "HEAD", "OPTIONS"}), ("PATCH", "/admin/stories/some-story/delete", {"GET", "HEAD", "OPTIONS", "POST"}),
         ("POST", "/api/v1/search", {"GET", "HEAD", "OPTIONS"}), ("PUT", "/api/v1/characters", {"GET", "HEAD", "OPTIONS"}), ("GET", "/logout", {"POST", "OPTIONS"})]


@pytest.mark.parametrize("method,path,allowed", CASES)
def test_a_405_lists_what_the_route_allows(client, method, path, allowed):
    response = client.open(path, method=method)
    assert response.status_code == 405, (method, path, response.status_code)
    listed = {m.strip() for m in response.headers["Allow"].split(",")}
    assert listed == allowed, (path, response.headers["Allow"])


def test_the_405_page_is_still_the_branded_page_and_the_api_405_still_json(client):
    page = client.put("/login")
    assert "text/html" in page.content_type and "Wrong turn" in page.get_data(as_text=True) and "Error 405" in page.get_data(as_text=True)
    api = client.post("/api/v1/search")
    assert api.is_json and api.get_json()["error"]["status"] == 405 and "Allow" in api.headers


def test_allow_is_only_on_405_answers_and_agrees_with_the_routing_table_everywhere(app):
    client = app.test_client()
    checked = 0
    for rule in app.url_map.iter_rules():
        if rule.endpoint == "static":
            continue
        path = rule.rule.replace("<slug>", "x").replace("<kind>", "characters").replace("<path:filename>", "clips/x.mp4")
        for method in ("PUT", "PATCH", "DELETE"):
            response = client.open(path, method=method)
            if response.status_code == 405:
                assert {m.strip() for m in response.headers["Allow"].split(",")} == set(rule.methods) | {"OPTIONS"}, (method, rule.rule)
                checked += 1
            else:
                assert "Allow" not in response.headers, (method, rule.rule, response.status_code)
    assert checked >= 100
    assert "Allow" not in client.get("/no-such-page").headers


# ------------------------------------------------------------------ HSTS
def hsts_app(seconds):
    app = create_app("testing")
    app.config["HSTS_MAX_AGE"] = seconds
    return app.test_client()


def test_hsts_is_sent_over_https_when_the_config_asks_for_it():
    response = hsts_app(31536000).get("/", base_url="https://example.org")
    assert response.headers["Strict-Transport-Security"] == "max-age=31536000"
    assert "includeSubDomains" not in response.headers["Strict-Transport-Security"] and "preload" not in response.headers["Strict-Transport-Security"]


@pytest.mark.parametrize("path", ["/", "/login", "/api/v1/search?q=a", "/no-such-page", "/robots.txt", "/static/css/site.css"])
def test_hsts_is_on_every_kind_of_https_answer(path):
    assert "Strict-Transport-Security" in hsts_app(600).get(path, base_url="https://example.org").headers


def test_hsts_is_never_sent_over_plain_http():
    assert "Strict-Transport-Security" not in hsts_app(31536000).get("/", base_url="http://example.org").headers


def test_a_client_cannot_fake_https_with_a_forwarded_header():
    """TV_TRUSTED_PROXIES is 0 here, so X-Forwarded-Proto means nothing: the request is http and gets no HSTS."""
    response = hsts_app(31536000).get("/", base_url="http://example.org", headers={"X-Forwarded-Proto": "https", "X-Forwarded-For": "203.0.113.9"})
    assert "Strict-Transport-Security" not in response.headers


def test_hsts_is_off_unless_turned_on(client):
    """The testing config (and development) leave it at 0: no header, even over https."""
    assert create_app("testing").config["HSTS_MAX_AGE"] == 0
    assert "Strict-Transport-Security" not in client.get("/", base_url="https://example.org").headers
    assert "Strict-Transport-Security" not in hsts_app(0).get("/", base_url="https://example.org").headers


def test_only_the_production_config_turns_it_on():
    from app import config
    assert config.Config.HSTS_MAX_AGE == 0 and config.DevelopmentConfig.HSTS_MAX_AGE == 0 and config.TestingConfig.HSTS_MAX_AGE == 0
    import os
    assert ProductionConfig.HSTS_MAX_AGE == hsts_max_age(os.environ.get("TV_HSTS_MAX_AGE"))      # whatever the operator set, parsed the same safe way
    if "TV_HSTS_MAX_AGE" not in os.environ:
        assert ProductionConfig.HSTS_MAX_AGE == HSTS_DEFAULT_SECONDS == 31536000                 # one year by default


@pytest.mark.parametrize("value,expected", [(None, HSTS_DEFAULT_SECONDS), ("", HSTS_DEFAULT_SECONDS), ("   ", HSTS_DEFAULT_SECONDS), ("abc", HSTS_DEFAULT_SECONDS), ("1.5", HSTS_DEFAULT_SECONDS),
                                            ("0", 0), ("-5", 0), ("600", 600), (" 600 ", 600), ("31536000", 31536000), ("63072000", HSTS_MAX_SECONDS),
                                            ("99999999999", HSTS_MAX_SECONDS)])
def test_the_hsts_setting_is_parsed_safely(value, expected):
    assert hsts_max_age(value) == expected


# ------------------------------------------------------------------ robots.txt
def test_robots_txt_is_plain_text_cached_and_lists_what_crawlers_should_leave(client):
    response = client.get("/robots.txt")
    assert response.status_code == 200 and response.content_type.startswith("text/plain")
    body = response.get_data(as_text=True)
    assert body == ROBOTS_TXT and body.startswith("User-agent: *\nAllow: /\n") and body.endswith("\n")
    assert "max-age=3600" in response.headers["Cache-Control"]
    for path in ROBOTS_DISALLOWED:
        assert f"Disallow: {path}\n" in body


def test_every_disallowed_path_is_a_real_part_of_the_site(app):
    rules = [r.rule for r in app.url_map.iter_rules()]
    for path in ROBOTS_DISALLOWED:
        assert any(rule == path or rule.startswith(path.rstrip("/") + "/") or rule.startswith(path) for rule in rules), f"{path} matches no route, so robots.txt has gone stale"


def test_robots_txt_needs_no_database(client, monkeypatch):
    def boom(*args, **kwargs):
        raise AssertionError("robots.txt must not read the database (a host probes it while MySQL sleeps)")
    monkeypatch.setattr(characters_repo, "search", boom)
    assert client.get("/robots.txt").status_code == 200
    assert client.head("/robots.txt").status_code == 200 and client.head("/robots.txt").get_data() == b""
