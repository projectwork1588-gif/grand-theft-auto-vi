"""Branded error pages (Stage 4A): 404, 403, 405, 500 and 503 show the site's own page, say what happened in the site's words, offer a way on, and never leak internals.
The JSON answer of /api/* is untouched, a sentence a route chose itself is kept, and "Try again" never points off the site."""
import mysql.connector.errors
import pytest
from werkzeug.exceptions import MethodNotAllowed, NotFound

from app.errors import BRANDED, _retry_url
from app.repositories import characters as characters_repo
from app.repositories import missions as missions_repo
from tests import account_helpers as h


def _page(response):
    return response.get_data(as_text=True)


def _assert_branded(response, status, title):
    page = _page(response)
    assert response.status_code == status and "text/html" in response.content_type
    assert page.count("<h1") == 1                                              # one heading, so a screen reader announces one thing
    assert f"Error {status}" in page and title in page                         # the code and the standard name stay on the page and in <title>
    assert BRANDED[status][0] in page                                          # the branded headline
    assert 'class="site-header' in page and "An unofficial educational fan project" in page   # still a full, branded page
    for label in ("Characters", "Garage", "Leonida", "Music", "Media"):
        assert f'class="chip" href="' in page and f'">{label}</a></li>' in page.split('aria-label="Places to go"', 1)[1]
    return page


def test_404_is_branded_and_drops_the_stock_sentence(client):
    page = _assert_branded(client.get("/no-such-page"), 404, "Not Found")
    assert NotFound.description not in page and "Try again" not in page         # nothing to retry on a missing page
    assert 'href="/"' in page


def test_404_for_a_hidden_profile_is_the_same_page(client):
    _assert_branded(client.get("/characters/delia-marsh"), 404, "Not Found")


def test_405_is_branded(client):
    response = client.put("/about")
    page = _assert_branded(response, 405, "Method Not Allowed")
    assert MethodNotAllowed.description not in page                           # Werkzeug's stock sentence is replaced


@pytest.mark.usefixtures("clean_accounts")
def test_403_is_branded_and_keeps_the_sentence_the_route_chose(client):
    h.register(client)
    response = client.get("/admin")
    page = _assert_branded(response, 403, "Forbidden")
    assert "This area is for administrators." in page and BRANDED[403][1] not in page


def _boom(*args, **kwargs):
    raise RuntimeError("secret-host password=hunter2 SELECT * FROM characters")


def _db_down(*args, **kwargs):
    raise mysql.connector.errors.DatabaseError("secret-host password=hunter2 SELECT * FROM characters")


def test_500_is_branded_offers_a_retry_and_leaks_nothing(client, monkeypatch):
    monkeypatch.setattr(characters_repo, "search", _boom)
    response = client.get("/characters")
    page = _assert_branded(response, 500, "Server error")
    assert 'href="/characters">Try again</a>' in page
    assert "hunter2" not in page and "SELECT" not in page and "secret-host" not in page and "RuntimeError" not in page and "Traceback" not in page


def test_503_is_branded_offers_a_retry_and_leaks_nothing(client, monkeypatch):
    monkeypatch.setattr(missions_repo, "search", _db_down)
    response = client.get("/missions", query_string={"q": "x"})
    page = _assert_branded(response, 503, "Database unavailable")
    assert 'href="/missions">Try again</a>' in page                            # the path only: the query string is not echoed back
    assert "hunter2" not in page and "SELECT" not in page and "secret-host" not in page


def test_retry_is_offered_for_a_get_only(app, monkeypatch):
    monkeypatch.setattr(characters_repo, "search", _boom)
    with app.test_request_context("/characters", method="POST"):
        assert _retry_url() is None
    with app.test_request_context("/characters", method="GET"):
        assert _retry_url() == "/characters"


def test_retry_never_points_off_the_site(app):
    for raw in ("//evil.example/path", "///evil.example", "/\\evil.example"):
        with app.test_request_context(environ_overrides={"PATH_INFO": raw}):
            url = _retry_url()
            assert url is None or (url.startswith("/") and not url.startswith("//")), raw


def test_api_errors_stay_json_and_unchanged(client, monkeypatch):
    response = client.get("/api/v1/no-such-endpoint")
    assert response.status_code == 404 and response.is_json
    assert response.get_json() == {"error": {"status": 404, "title": "Not Found", "message": NotFound.description}}
    monkeypatch.setattr(characters_repo, "search", _db_down)
    response = client.get("/api/v1/characters")
    assert response.status_code == 503 and response.is_json
    assert response.get_json()["error"]["title"] == "Database unavailable"
    assert "hunter2" not in response.get_data(as_text=True)
