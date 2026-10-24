"""Search on a database without migration 008's music tables. The Music page already treats those tables as optional (an empty page, not an error); search used to answer 503 for the
default all-types search because one statement spans every kind. Now: an all-types search returns what the other kinds find and names what it left out, an explicit music search is an
empty 200 (nothing is made up), and ONLY a missing music table is tolerated: a missing core table, a permission error, a lost connection or bad SQL is still the generic 503.
Simulated errors prove the classification; a few tests rename the real tables of the *_test database (always put back) to prove it against a genuinely missing table."""
import logging
import re
from contextlib import contextmanager
from pathlib import Path

import mysql.connector
import pytest
from mysql.connector import errors

from app.config import TestingConfig
from app.repositories import search as search_repo

API = "/api/v1/search"
MUSIC_TABLES = ("radio_stations", "music_releases", "music_tracks")
NOTE = "Music results are not available on this copy of the site."


def missing(table="music_tracks", db="gta6_vi_test"):
    return errors.ProgrammingError(msg=f"Table '{db}.{table}' doesn't exist", errno=1146, sqlstate="42S02")


class Spy:
    """Wraps the repository's query function: counts the statements, and raises `error_for(sql)` when it returns an error for a statement."""

    def __init__(self, monkeypatch, error_for=None):
        self.calls, self.error_for, self.real = [], error_for, search_repo.query_all
        monkeypatch.setattr(search_repo, "query_all", self)

    def __call__(self, sql, params=None):
        self.calls.append(sql)
        error = self.error_for(sql, len(self.calls)) if self.error_for else None
        if error:
            raise error
        return self.real(sql, params)


def music_is_missing(sql, _n):
    named = next((t for t in MUSIC_TABLES if re.search(rf"\b{t}\b", sql)), None)
    return missing(named) if named else None


def migration_connection():
    """The migration account's connection to the TEST database. A rename waits for every open read on the table to finish; a short wait turns "something still holds the table"
    into a clear error in seconds instead of a test run that hangs (which once left renamed tables behind)."""
    assert TestingConfig.DB_NAME.endswith("_test")
    conn = mysql.connector.connect(**TestingConfig.migration_kwargs())
    cur = conn.cursor()
    cur.execute("SELECT DATABASE()")
    assert cur.fetchone()[0].endswith("_test")
    cur.execute("SET SESSION lock_wait_timeout = 10")
    return conn, cur


def row_count(table):
    conn, cur = migration_connection()
    try:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        n = cur.fetchone()[0]
        conn.commit()
        return n
    finally:
        conn.close()


@contextmanager
def tables_renamed(*tables):
    """Rename real tables of the TEST database aside and put them back in every case. Each table is restored on its own, so one failure cannot strand the others."""
    conn, cur = migration_connection()
    done, problems = [], []
    try:
        for table in tables:
            cur.execute(f"RENAME TABLE {table} TO {table}__aside")
            done.append(table)
        yield
    finally:
        for table in reversed(done):
            try:
                cur.execute(f"RENAME TABLE {table}__aside TO {table}")
            except Exception as error:                      # keep going: restore the rest, then say what could not be restored
                problems.append(f"{table}: {error}")
        conn.commit()
        conn.close()
        assert not problems, "COULD NOT RESTORE (the next pytest session rebuilds the test database): " + "; ".join(problems)


def find(client, q, **extra):
    response = client.get(API, query_string={"q": q, **extra})
    assert response.status_code == 200, (q, extra, response.status_code, response.get_data(as_text=True)[:200])
    return response.get_json()


def kinds(body):
    return {hit["kind"] for hit in body["results"]}


# ------------------------------------------------------------------ the classifier: only a missing MUSIC table counts
@pytest.mark.parametrize("exc,expected", [
    (missing("music_tracks"), "music"), (missing("radio_stations"), "music"), (missing("music_releases"), "music"), (missing("music_tracks", db="gta6_vi"), "music"),
    (errors.ProgrammingError(msg="Table 'x.music_tracks' DOESN'T EXIST", errno=1146), "music"),
    (missing("characters"), None), (missing("regions"), None), (missing("station_preview_tracks"), None), (missing("music_tracks_backup"), None),
    (errors.ProgrammingError(msg="SELECT command denied to user 'app'@'localhost' for table 'music_tracks'", errno=1142), None),
    (errors.ProgrammingError(msg="You have an error in your SQL syntax", errno=1064), None),
    (errors.ProgrammingError(msg="Table doesn't exist", errno=1146), None),
    (errors.ProgrammingError(msg=None, errno=1146), None),
    (errors.DatabaseError(msg="Table 'x.music_tracks' doesn't exist", errno=1146), None),             # not a ProgrammingError: not recognised, so not hidden
    (errors.OperationalError(msg="Lost connection to MySQL server", errno=2013), None), (errors.InterfaceError(msg="2003: Can't connect", errno=2003), None),
    (errors.IntegrityError(msg="Duplicate entry", errno=1062), None), (RuntimeError("Table 'x.music_tracks' doesn't exist"), None),
])
def test_only_a_missing_music_table_is_classified_as_optional(exc, expected):
    assert search_repo.missing_optional_kind(exc) == expected


def test_tolerant_passes_a_healthy_call_through_unchanged_and_skips_what_is_already_known(caplog):
    caplog.set_level(logging.WARNING)
    seen, unavailable = [], []
    assert search_repo.tolerant(lambda ks: seen.append(ks) or "ok", ("character", "music"), unavailable) == "ok"
    assert seen == [("character", "music")] and unavailable == [] and caplog.records == []
    unavailable = ["music"]
    search_repo.tolerant(lambda ks: seen.append(ks), ("character", "music"), unavailable)
    assert seen[-1] == ("character",), "a kind already known to be missing is not asked for again"


# ------------------------------------------------------------------ normal behaviour is unchanged when every table exists
def test_with_all_tables_present_the_answer_has_its_old_shape_music_included_and_one_query(client, monkeypatch, caplog):
    caplog.set_level(logging.WARNING)
    spy = Spy(monkeypatch)
    body = find(client, "flash")
    assert set(body) == {"query", "type", "results"} and "unavailable" not in body
    assert any(h["kind"] == "music" and h["title"] == "Flash FM" for h in body["results"])
    assert len(spy.calls) == 1 and caplog.records == []                 # still one round trip, and nothing logged
    page = client.get("/search", query_string={"q": "flash"}).get_data(as_text=True)
    assert NOTE not in page and "search-note" not in page and 'class="hit__kind">Music<' in page


def test_with_all_tables_present_the_page_context_says_nothing_is_unavailable(app):
    from app.services import search as service
    with app.test_request_context("/search"):                          # building result addresses needs a request
        assert service.page_search({"q": "vice"})["unavailable"] == [] and service.page_search({})["unavailable"] == []


# ------------------------------------------------------------------ all-types search when the music tables are absent (simulated)
def test_all_types_search_still_returns_the_other_kinds_and_names_what_it_left_out(client, monkeypatch, caplog):
    caplog.set_level(logging.WARNING)
    spy = Spy(monkeypatch, music_is_missing)
    body = find(client, "vice")
    assert {"region", "place"} <= kinds(body) and "music" not in kinds(body)
    assert body["unavailable"] == ["music"] and set(body) == {"query", "type", "results", "unavailable"}
    assert len(spy.calls) == 2                                          # the attempt that found the table missing, then the answer without music
    warnings = [r for r in caplog.records if "migration 008" in r.getMessage()]
    assert len(warnings) == 1 and "music" in warnings[0].getMessage()


def test_a_query_that_only_music_could_answer_is_an_empty_200_not_a_503(client, monkeypatch):
    Spy(monkeypatch, music_is_missing)
    body = find(client, "flash")
    assert body["results"] == [] and body["unavailable"] == ["music"]
    assert "Flash FM" not in str(body)


def test_the_other_kinds_are_ranked_and_labelled_exactly_as_before(client, monkeypatch):
    healthy = [(h["kind"], h["title"], h["status_label"]) for h in find(client, "vice", limit=20)["results"] if h["kind"] != "music"]
    Spy(monkeypatch, music_is_missing)
    degraded = [(h["kind"], h["title"], h["status_label"]) for h in find(client, "vice", limit=20)["results"]]
    assert degraded == healthy and degraded


def test_the_sites_own_pages_are_still_found_without_touching_the_missing_tables(client, monkeypatch):
    spy = Spy(monkeypatch, music_is_missing)
    body = find(client, "music", type="page")
    assert [h["title"] for h in body["results"]] == ["Music"] and body["results"][0]["url"] == "/music"
    assert spy.calls == [] and "unavailable" not in body              # the pages kind never needed the database


# ------------------------------------------------------------------ the command palette
def test_the_request_the_palette_makes_gets_useful_results_not_its_error_note(client, monkeypatch):
    Spy(monkeypatch, music_is_missing)
    response = client.get(API, query_string={"limit": 8, "q": "vice"})                      # exactly the palette's request (palette.js: API + "?limit=" + LIMIT + "&q=")
    body = response.get_json()
    assert response.status_code == 200 and response.is_json and 1 <= len(body["results"]) <= 8
    assert all(h["url"].startswith("/") and not h["url"].startswith("//") for h in body["results"])
    script = (Path(__file__).resolve().parent.parent / "app" / "static" / "js" / "palette.js").read_text(encoding="utf-8")
    assert "if (!response.ok) { throw" in script and "unavailable" not in script and "body.results" in script
    # a 200 can never reach the palette's "Search is not available" note, which only the failure branch shows:
    assert script.index("Search is not available right now") > script.index(".catch(function (error)")


# ------------------------------------------------------------------ explicit music search when the tables are absent
def test_an_explicit_music_search_is_an_empty_200_in_the_projects_response_format(client, monkeypatch):
    spy = Spy(monkeypatch, music_is_missing)
    response = client.get(API, query_string={"q": "radio", "type": "music"})
    body = response.get_json()
    assert response.status_code == 200 and response.is_json
    assert body == {"query": "radio", "type": "music", "results": [], "unavailable": ["music"]}
    assert len(spy.calls) == 1                                          # one failed attempt; with nothing left to ask, no second query


def test_the_results_page_says_music_is_unavailable_and_does_not_invent_any(client, monkeypatch):
    Spy(monkeypatch, music_is_missing)
    explicit = client.get("/search", query_string={"q": "radio", "type": "music"})
    page = explicit.get_data(as_text=True)
    assert explicit.status_code == 200 and NOTE in page and "No matches for" in page and 'class="hit"' not in page
    default = client.get("/search", query_string={"q": "vice"})
    page = default.get_data(as_text=True)
    assert default.status_code == 200 and NOTE in page and 'class="hit__kind">Place<' in page and 'class="hit__kind">Music<' not in page
    assert re.search(r'>Music <small>', page) is None, "no Music chip when music cannot be searched"
    assert page.count("search-note") == 1 and page.count("<h1") == 1


def test_the_degraded_state_is_not_remembered_the_next_request_sees_the_tables_again(client, monkeypatch):
    with monkeypatch.context() as m:
        Spy(m, music_is_missing)
        assert find(client, "flash")["unavailable"] == ["music"]
    healthy = find(client, "flash")
    assert "unavailable" not in healthy and any(h["kind"] == "music" for h in healthy["results"])


# ------------------------------------------------------------------ everything else is still an error, still the generic 503
SECRET = "secret-host password=hunter2 SELECT * FROM characters"
UNRELATED = [
    ("a missing core table", lambda: missing("characters")),
    ("a missing region table", lambda: missing("regions")),
    ("a permission error on a music table", lambda: errors.ProgrammingError(msg="SELECT command denied to user 'app'@'localhost' for table 'music_tracks'", errno=1142)),
    ("bad SQL", lambda: errors.ProgrammingError(msg="You have an error in your SQL syntax near 'x'", errno=1064)),
    ("a table-missing message that names nothing", lambda: errors.ProgrammingError(msg="Table doesn't exist", errno=1146)),
    ("table-missing reported by a different error class", lambda: errors.DatabaseError(msg="Table 'x.music_tracks' doesn't exist", errno=1146)),
    ("a lost connection", lambda: errors.OperationalError(msg=SECRET, errno=2013)),
    ("a refused connection", lambda: errors.InterfaceError(msg=SECRET, errno=2003)),
    ("any other database error", lambda: errors.DatabaseError(msg=SECRET)),
]


@pytest.mark.parametrize("label,make", UNRELATED, ids=[u[0] for u in UNRELATED])
def test_unrelated_database_errors_are_still_the_generic_503_and_are_never_logged_as_a_skip(client, monkeypatch, caplog, label, make):
    caplog.set_level(logging.WARNING)
    Spy(monkeypatch, lambda sql, n: make())
    for params in ({"q": "vice"}, {"q": "radio", "type": "music"}, {"q": "jason", "type": "character"}):
        api = client.get(API, query_string=params)
        assert api.status_code == 503 and api.is_json and api.get_json()["error"]["title"] == "Database unavailable", (label, params)
        assert "hunter2" not in api.get_data(as_text=True) and "secret-host" not in api.get_data(as_text=True)
    page = client.get("/search", query_string={"q": "vice"})
    assert page.status_code == 503 and "Back in a moment" in page.get_data(as_text=True) and "hunter2" not in page.get_data(as_text=True)
    assert not [r for r in caplog.records if "leaves out" in r.getMessage()], "an unrelated error must never be reported as a skipped kind"


def test_an_error_after_the_music_fallback_is_not_swallowed(client, monkeypatch):
    """The first statement finds the music table missing; the retry without music then loses the connection. That second error must surface."""
    def script(sql, n):
        return missing("music_tracks") if n == 1 else errors.OperationalError(msg="Lost connection to MySQL server", errno=2013)
    Spy(monkeypatch, script)
    assert client.get(API, query_string={"q": "vice"}).status_code == 503


# ------------------------------------------------------------------ against genuinely missing tables (the test database, tables renamed and put back)
def test_with_the_music_tables_really_missing_search_degrades_and_the_music_page_still_works(client):
    before = row_count("music_tracks")
    assert before > 0
    with tables_renamed(*MUSIC_TABLES):
        body = find(client, "vice")
        assert {"region", "place"} <= kinds(body) and "music" not in kinds(body) and body["unavailable"] == ["music"]
        assert find(client, "radio", type="music") == {"query": "radio", "type": "music", "results": [], "unavailable": ["music"]}
        palette = client.get(API, query_string={"limit": 8, "q": "jason"})
        assert palette.status_code == 200 and any(h["kind"] == "character" for h in palette.get_json()["results"])
        page = client.get("/search", query_string={"q": "vice"})
        assert page.status_code == 200 and NOTE in page.get_data(as_text=True)
        assert client.get("/music").status_code == 200
    healthy = find(client, "flash")
    assert "unavailable" not in healthy and any(h["kind"] == "music" for h in healthy["results"])
    assert row_count("music_tracks") == before


@pytest.mark.parametrize("only_one", MUSIC_TABLES)
def test_a_single_missing_music_table_is_enough_to_leave_music_out(client, only_one):
    with tables_renamed(only_one):
        body = find(client, "vice")
        assert body["unavailable"] == ["music"] and "music" not in kinds(body) and {"region", "place"} <= kinds(body)
    assert "unavailable" not in find(client, "flash")


def test_a_genuinely_missing_core_table_is_still_a_503(client):
    with tables_renamed("characters"):
        assert client.get(API, query_string={"q": "vice"}).status_code == 503
        assert client.get("/search", query_string={"q": "vice"}).status_code == 503
    assert find(client, "jason")["results"]
