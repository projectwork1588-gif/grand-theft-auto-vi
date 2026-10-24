"""Search shows music by the Music page's own rule: only official rows. A fan or demo ('draft') station, release or track must never be found, in the palette's API,
on the results page or in the per-kind counts, while the same words on an official row are found.

Every test below plants a matched set of rows that differ only in status (same unique word), through the migration account on the TEST database, with 'tt-vis-' slugs
that are removed again before and after. The seeded music is never changed."""
import mysql.connector
import pytest

from app.config import TestingConfig
from app.repositories import search as search_repo
from app.services import search as search_service

API = "/api/v1/search"
WORD = "quillfeather"                       # appears in no seeded row
OFFICIAL_NAMES = ("Quillfeather Official Radio", "Quillfeather Official Album", "Quillfeather Anthem")
HIDDEN_NAMES = ("Quillfeather Demo Radio", "Quillfeather Fan Radio", "Quillfeather Draft Album", "Quillfeather Draft Track", "Quillfeather Fan Album", "Quillfeather Fan Track")


def _connect():
    assert TestingConfig.DB_NAME.endswith("_test"), "refusing: the testing config does not name a *_test database"
    connection = mysql.connector.connect(**TestingConfig.migration_kwargs())
    cursor = connection.cursor()
    cursor.execute("SELECT DATABASE()")
    assert cursor.fetchone()[0].endswith("_test"), "refusing: not a *_test database"
    return connection, cursor


def _wipe(cursor):
    cursor.execute("DELETE FROM radio_stations WHERE slug LIKE 'tt-vis-%'")
    cursor.execute("DELETE FROM music_releases WHERE slug LIKE 'tt-vis-%'")          # its tracks go with it (ON DELETE CASCADE)


def _station(cursor, slug, name, status):
    official = status == "official"
    cursor.execute(
        "INSERT INTO radio_stations (slug, name, hosts, description, sort_order, content_status, source_url) VALUES (%s, %s, NULL, %s, 250, %s, %s)",
        (slug, name, f"{name} plays test records.", status, "https://example.org/source" if official else None))


def _release_with_track(cursor, slug, title, track, status):
    official = status == "official"
    cursor.execute(
        "INSERT INTO music_releases (slug, kind, title, byline, description, content_status, source_url) VALUES (%s, 'album', %s, NULL, %s, %s, %s)",
        (slug, title, f"{title} is a test release.", status, "https://example.org/source" if official else None))
    cursor.execute("INSERT INTO music_tracks (release_id, sort_order, title, artists) VALUES (%s, 1, %s, 'Test Artist')", (cursor.lastrowid, track))


@pytest.fixture()
def planted(app):
    """Official, demo and fan music that all match the same word."""
    connection, cursor = _connect()
    try:
        _wipe(cursor)
        _station(cursor, "tt-vis-official", "Quillfeather Official Radio", "official")
        _station(cursor, "tt-vis-demo", "Quillfeather Demo Radio", "demo")
        _station(cursor, "tt-vis-fan", "Quillfeather Fan Radio", "fan")
        _release_with_track(cursor, "tt-vis-album-official", "Quillfeather Official Album", "Quillfeather Anthem", "official")
        _release_with_track(cursor, "tt-vis-album-demo", "Quillfeather Draft Album", "Quillfeather Draft Track", "demo")
        _release_with_track(cursor, "tt-vis-album-fan", "Quillfeather Fan Album", "Quillfeather Fan Track", "fan")
        connection.commit()
        yield
    finally:
        connection.rollback()
        _wipe(cursor)
        connection.commit()
        connection.close()


def titles(client, **extra):
    response = client.get(API, query_string={"q": WORD, "limit": 20, **extra})
    assert response.status_code == 200, response.get_data(as_text=True)[:200]
    return {hit["title"] for hit in response.get_json()["results"] if hit["kind"] == "music"}


def test_official_music_is_found_and_every_other_status_is_not(client, planted):
    assert titles(client, type="music") == set(OFFICIAL_NAMES)


def test_the_palettes_default_all_kinds_search_applies_the_same_rule(client, planted):
    assert titles(client) == set(OFFICIAL_NAMES)


def test_a_word_only_a_non_official_row_has_finds_nothing(client, planted):
    for word in ("quillfeather draft", "quillfeather demo", "quillfeather fan"):
        body = client.get(API, query_string={"q": word, "type": "music"}).get_json()
        assert body["results"] == [], word


def test_a_track_follows_the_status_of_its_release(client, planted):
    found = titles(client, type="music")
    assert "Quillfeather Anthem" in found
    assert "Quillfeather Draft Track" not in found and "Quillfeather Fan Track" not in found


def test_the_results_page_and_its_counts_show_only_the_official_rows(app, client, planted):
    page = client.get("/search", query_string={"q": WORD, "type": "music"}).get_data(as_text=True)
    assert all(name in page for name in OFFICIAL_NAMES)
    assert not any(name in page for name in HIDDEN_NAMES)
    with app.test_request_context("/search"):                          # building result addresses and reading the database need a request
        context = search_service.page_search({"q": WORD, "type": "music"})
        counted = search_repo.counts(("music",), [f"%{WORD}%"])
    assert context["counts"]["music"] == len(OFFICIAL_NAMES) and context["total"] == len(OFFICIAL_NAMES)
    assert counted == {"music": len(OFFICIAL_NAMES)}


def test_search_and_the_music_page_agree_about_which_stations_exist(client, planted):
    """The page lists every official station and no other. (It draws one score and one album only, so the extra planted releases are not compared here.)"""
    page = client.get("/music").get_data(as_text=True)
    stations = {title for title in titles(client, type="music") if title.endswith("Radio")}
    assert stations == {"Quillfeather Official Radio"} and "Quillfeather Official Radio" in page
    assert "Quillfeather Demo Radio" not in page and "Quillfeather Fan Radio" not in page


def test_the_seeded_official_music_is_still_found(client):
    body = client.get(API, query_string={"q": "flash", "type": "music"}).get_json()
    assert any(hit["kind"] == "music" and hit["url"] == "/music#radio" for hit in body["results"])
    body = client.get(API, query_string={"q": "justice", "type": "music", "limit": 20}).get_json()
    assert any(hit["kind"] == "music" and hit["url"].split("#")[1] in ("score", "album") for hit in body["results"])


def test_every_music_select_names_the_official_rule_and_the_statement_stays_parameterised():
    """The rule is in the SQL itself, once per music SELECT, as a literal (like the character and vehicle SELECTs), and no text from a request is put into it."""
    assert len(search_repo._MUSIC) == 3
    for template in search_repo._MUSIC:
        assert "content_status = 'official'" in template
        sql, params = search_repo._expand(template, ["%x%"], ["x", "x%", "% x%", "%x%"])
        assert "'x'" not in sql and "%x%" not in sql and params.count("%x%") >= 1
