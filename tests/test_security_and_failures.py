"""Security headers, output escaping, and what visitors see when the database fails."""
import re

import mysql.connector
import pytest

from app.repositories import characters as characters_repo
from app.repositories import missions as missions_repo
from app.repositories import regions as regions_repo
from app.repositories import system as system_repo
from app.repositories import vehicles as vehicles_repo

PAGES = ["/", "/characters", "/characters/jason-duval", "/vehicles", "/vehicles/grotti-cheetah", "/regions",
         "/regions/vice-city", "/locations", "/locations/neon-row-district", "/missions", "/missions/harbour-lights"]


# ------------------------------------------------------------------ headers and markup hygiene
@pytest.mark.parametrize("path", PAGES + ["/api/v1/characters", "/health"])
def test_security_headers_are_present(client, path):
    headers = client.get(path).headers
    csp = headers["Content-Security-Policy"]
    assert "script-src 'self'" in csp and "object-src 'none'" in csp and "frame-ancestors 'self'" in csp
    assert "frame-src https://www.rockstargames.com" in csp and "img-src 'self' https://www.rockstargames.com" in csp
    assert headers["X-Content-Type-Options"] == "nosniff" and "Referrer-Policy" in headers


@pytest.mark.parametrize("path", PAGES)
def test_pages_have_no_inline_scripts_styles_or_event_handlers(client, path):
    page = client.get(path).get_data(as_text=True)
    for tag in re.findall(r"<script\b[^>]*>", page):
        assert " src=" in tag, tag                        # no inline <script> blocks
    assert " style=" not in page                          # no inline style attributes (CSP style-src has no 'unsafe-inline')
    assert not re.search(r"\son[a-z]+=", page)            # no onclick= and friends


@pytest.mark.parametrize("path", PAGES)
def test_external_links_are_safe(client, path):
    page = client.get(path).get_data(as_text=True)
    for tag in re.findall(r"<a\b[^>]*target=\"_blank\"[^>]*>", page):
        assert 'rel="noopener noreferrer"' in tag, tag
    for tag in re.findall(r"<iframe\b[^>]*>", page):
        assert False, f"iframes are only created on demand by JavaScript: {tag}"


# ------------------------------------------------------------------ escaping untrusted content
def test_list_page_escapes_hostile_database_values(client, monkeypatch):
    hostile = {"slug": "x", "full_name": "<script>alert(1)</script>", "alias": '"><img src=x onerror=alert(2)>',
               "role_title": "<b>role</b>", "summary": "s", "content_status": "official",
               "home_location_slug": None, "home_location_name": None, "region_slug": None, "region_name": "<i>r</i>"}
    monkeypatch.setattr(characters_repo, "search", lambda *a, **k: ([hostile], 1))
    monkeypatch.setattr(characters_repo, "ids_by_slug", lambda slugs: {})
    page = client.get("/characters").get_data(as_text=True)
    assert "<script>alert(1)</script>" not in page and "&lt;script&gt;alert(1)&lt;/script&gt;" in page
    assert "<img src=x" not in page and "&lt;b&gt;role&lt;/b&gt;" in page


def test_detail_page_escapes_hostile_database_values(client, monkeypatch):
    original = characters_repo.get_by_slug
    monkeypatch.setattr(characters_repo, "get_by_slug",
                        lambda slug: dict(original(slug), biography="<img src=x onerror=alert(1)>", source_url="javascript:alert(1)"))
    page = client.get("/characters/jason-duval").get_data(as_text=True)
    assert "<img src=x onerror" not in page and "&lt;img src=x onerror=alert(1)&gt;" in page


def test_search_text_is_reflected_escaped(client):
    page = client.get("/characters", query_string={"q": '"><script>alert(1)</script>'}).get_data(as_text=True)
    assert "<script>alert" not in page and "&#34;&gt;&lt;script&gt;" in page


# ------------------------------------------------------------------ database failures
def _broken(*args, **kwargs):
    raise mysql.connector.errors.DatabaseError("secret-host password=hunter2 SELECT * FROM characters")


@pytest.mark.parametrize("path,module,function", [
    ("/", system_repo, "table_counts"),
    ("/characters", characters_repo, "search"),
    ("/characters/jason-duval", characters_repo, "get_by_slug"),
    ("/vehicles", vehicles_repo, "search"),
    ("/vehicles/grotti-cheetah", vehicles_repo, "get_by_slug"),
    ("/regions", regions_repo, "list_all"),
    ("/regions/vice-city", regions_repo, "get_by_slug"),
    ("/locations", regions_repo, "list_all"),
    ("/missions", missions_repo, "search"),
    ("/missions/harbour-lights", missions_repo, "get_by_slug"),
])
def test_pages_show_a_safe_503_when_the_database_fails(client, monkeypatch, path, module, function):
    monkeypatch.setattr(module, function, _broken)
    response = client.get(path)
    page = response.get_data(as_text=True)
    assert response.status_code == 503 and "Database unavailable" in page and "text/html" in response.content_type
    assert "hunter2" not in page and "SELECT" not in page and "secret-host" not in page
    assert "An unofficial educational fan project" in page  # the error page is still a full, branded page


@pytest.mark.parametrize("path,module,function", [
    ("/api/v1/vehicles", vehicles_repo, "search"),
    ("/api/v1/vehicles/corvina-gt", vehicles_repo, "get_by_slug"),
    ("/api/v1/missions", missions_repo, "search"),
    ("/api/v1/vehicle-categories", vehicles_repo, "categories_with_counts"),
])
def test_api_returns_json_503_when_the_database_fails(client, monkeypatch, path, module, function):
    monkeypatch.setattr(module, function, _broken)
    response = client.get(path)
    assert response.status_code == 503 and response.get_json()["error"]["status"] == 503
    assert "hunter2" not in response.get_data(as_text=True)


def test_unexpected_errors_are_a_generic_500(app, monkeypatch):
    def explode(*args, **kwargs):
        raise RuntimeError("internal detail /etc/passwd")

    monkeypatch.setattr(vehicles_repo, "search", explode)
    client = app.test_client()
    response = client.get("/vehicles")
    assert response.status_code == 500 and "internal detail" not in response.get_data(as_text=True)
    assert client.get("/api/v1/vehicles").get_json()["error"]["status"] == 500
