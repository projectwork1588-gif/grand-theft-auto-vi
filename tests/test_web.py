"""Homepage, health check and error pages."""
from markupsafe import escape

from app.blueprints.main import DISCLAIMER


def test_homepage_renders_identity_and_disclaimer(client):
    response = client.get("/")
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Welcome, gamers" in html
    assert "Team Valkyrie presents" in html
    assert "Grand Theft Auto VI" in html
    assert DISCLAIMER in html


def test_homepage_names_come_from_the_database(client, cur):
    html = client.get("/").get_data(as_text=True)
    cur.execute("SELECT full_name FROM characters WHERE content_status = 'official'")
    names = [r["full_name"] for r in cur.fetchall()]
    assert len(names) == 8 and all(escape(name) in html for name in names)
    cur.execute("SELECT name FROM regions")
    assert all(r["name"] in html for r in cur.fetchall())


def test_health_reports_database_connection(client):
    body = client.get("/health").get_json()
    assert body == {"status": "ok", "database": "connected"}                       # only that: the server version is not published (see tests/test_phase3a_hardening.py)


def test_unknown_page_gets_html_404(client):
    response = client.get("/no-such-page")
    assert response.status_code == 404
    assert "text/html" in response.content_type


def test_no_server_details_leak_on_database_failure(app, monkeypatch):
    """If MySQL is unreachable, visitors see a generic message, never SQL or credentials."""
    import mysql.connector
    from app.repositories import characters as repo

    def broken(*args, **kwargs):
        raise mysql.connector.errors.DatabaseError("secret-host password=hunter2")

    monkeypatch.setattr(repo, "search", broken)
    response = app.test_client().get("/api/v1/characters")
    assert response.status_code == 503
    assert "hunter2" not in response.get_data(as_text=True)
