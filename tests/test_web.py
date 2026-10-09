"""Homepage, health check and error pages."""
import re

from app.blueprints.main import DISCLAIMER


def test_homepage_renders_identity_and_disclaimer(client):
    response = client.get("/")
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Welcome, gamers" in html
    assert "Team Valkyrie presents" in html
    assert "Grand Theft Auto VI" in html
    assert DISCLAIMER in html


def test_homepage_counts_come_from_the_database(client, cur):
    html = client.get("/").get_data(as_text=True)
    cur.execute("SELECT COUNT(*) AS n FROM characters")
    expected = cur.fetchone()["n"]
    match = re.search(r"Characters</dt>\s*<dd>(\d+)</dd>", html)
    assert match and int(match.group(1)) == expected


def test_health_reports_database_connection(client):
    body = client.get("/health").get_json()
    assert body["status"] == "ok" and body["database"] == "connected"
    assert body["mysql_version"].startswith("8.")


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
