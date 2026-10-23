"""Site search, backend and JSON API (Stage 4B, milestone 1): what is found, who may see it, how it is ranked, what a query may look like, and that no input can
reach the SQL text. Reads the *_test database only; nothing is written."""
import mysql.connector.errors
import pytest

from app.db import query_all
from app.repositories import search as search_repo
from app.services import search as search_service

API = "/api/v1/search"


def find(client, q, **extra):
    response = client.get(API, query_string={"q": q, **extra})
    assert response.status_code == 200, (q, response.get_json())
    return response.get_json()


def titles(body):
    return [hit["title"] for hit in body["results"]]


# ------------------------------------------------------------------ what is found, and who may see it
def test_each_kind_of_record_is_found_with_its_own_page_address(client):
    expected = {"jason": ("character", "/characters/jason-duval"), "cheetah": ("vehicle", "/vehicles/grotti-cheetah"), "vice city": ("region", "/regions/vice-city"),
                "neon row": ("place", "/locations/neon-row-district"), "harbour lights": ("story", "/missions/harbour-lights")}
    for q, (kind, url) in expected.items():
        hit = next((h for h in find(client, q)["results"] if h["kind"] == kind), None)
        assert hit and hit["url"] == url, q


def test_the_original_characters_and_the_concept_vehicles_are_never_found(client, app_context):
    hidden_characters = [r["full_name"] for r in query_all("SELECT full_name FROM characters WHERE content_status <> 'official'")]
    hidden_vehicles = [r["name"] for r in query_all("SELECT name FROM vehicles WHERE content_status <> 'official'")]
    assert hidden_characters and hidden_vehicles
    for name in hidden_characters:
        assert not any(h["kind"] == "character" for h in find(client, name)["results"]), name
    for name in hidden_vehicles:
        assert not any(h["kind"] == "vehicle" for h in find(client, name)["results"]), name


def test_places_and_stories_are_found_and_labelled_concept(client):
    place = next(h for h in find(client, "neon row")["results"] if h["kind"] == "place")
    story = next(h for h in find(client, "harbour lights")["results"] if h["kind"] == "story")
    assert place["status"] == "demo" == story["status"]
    assert place["status_label"] == "Concept" == story["status_label"]
    official = next(h for h in find(client, "jason")["results"] if h["kind"] == "character")
    assert official["status_label"] == "Official"


def test_every_result_address_is_a_page_that_exists(client):
    seen = set()
    for q in ("a", "e", "o", "vice", "radio", "justice", "garage", "story"):
        for hit in find(client, q, limit=20)["results"]:
            seen.add(hit["url"])
    assert len(seen) > 15
    for url in sorted(seen):
        assert client.get(url.split("#")[0]).status_code == 200, url
        assert url.startswith("/") and not url.startswith("//")


def test_music_results_land_on_the_right_section_of_the_music_page(client):
    assert next(h for h in find(client, "flash")["results"] if h["kind"] == "music")["url"] == "/music#radio"
    kinds = {h["url"] for h in find(client, "justice", limit=20)["results"] if h["kind"] == "music"}
    assert kinds and all(url.startswith("/music#") and url.split("#")[1] in ("score", "album") for url in kinds)


def test_the_sites_own_pages_are_found_by_name_and_by_what_a_visitor_might_type(client):
    assert find(client, "garage")["results"][0]["url"] == "/vehicles"
    assert any(h["url"] == "/vehicles" for h in find(client, "cars")["results"])
    assert find(client, "credits")["results"][0]["url"] == "/credits"
    assert all(h["status_label"] is None for h in find(client, "about")["results"] if h["kind"] == "page")


# ------------------------------------------------------------------ ranking and matching
def test_an_exact_title_ranks_above_a_prefix_a_word_start_and_a_contains(client):
    assert find(client, "vice city")["results"][0]["title"] == "Vice City"
    ranks = {h["title"]: i for i, h in enumerate(find(client, "port", limit=20)["results"])}
    assert ranks["Port Gellhorn"] < ranks.get("Sunset Pier Boardwalk", 99)


def test_case_and_accents_do_not_matter(client):
    assert titles(find(client, "JASON")) == titles(find(client, "jason"))
    assert search_service.fold("Café") == "cafe" == search_service.fold("CAFÉ")


def test_every_word_must_match_and_wildcards_are_literal(client):
    assert "Neon Row District" in titles(find(client, "neon row"))
    assert find(client, "neon zzzzqq")["results"] == []
    assert find(client, "%")["results"] == [] and find(client, "_")["results"] == [] and find(client, "!")["results"] == []


def test_the_type_filter_and_the_limit_work(client):
    only = find(client, "a", type="place", limit=20)["results"]
    assert only and {h["kind"] for h in only} == {"place"}
    assert len(find(client, "a", limit=3)["results"]) == 3
    assert find(client, "a")["type"] == "all"


# ------------------------------------------------------------------ what a query may look like
@pytest.mark.parametrize("params", [{}, {"q": ""}, {"q": "   "}, {"q": "x" * 81}, {"q": "a b c d e f"}, {"q": "a", "type": "nonsense"},
                                    {"q": "a", "limit": "0"}, {"q": "a", "limit": "21"}, {"q": "a", "limit": "many"}])
def test_bad_input_is_a_json_400_naming_the_problem(client, params):
    response = client.get(API, query_string=params)
    body = response.get_json()
    assert response.status_code == 400 and body["error"]["status"] == 400 and body["error"]["details"], params


def test_control_characters_and_odd_spacing_are_cleaned_not_fatal(client):
    assert search_service.normalise("  ja\x00son \t\n  duval \x7f") == "ja son duval"
    for q in ("ja\x00son", "\x01\x02", "jason\r\nduval", "  jason  "):
        assert client.get(API, query_string={"q": q}).status_code in (200, 400)


# ------------------------------------------------------------------ no input reaches the SQL text
HOSTILE = ["' OR 1=1 --", "'; DROP TABLE characters; --", "\" OR \"\"=\"", "%' UNION SELECT user,password FROM users --", "\\", "\\' OR 1=1 --", "!%", "ｊａｓｏｎ", "<script>alert(1)</script>",
           "$(rm -rf /)", "`id`", "a" * 80, "😀", "'" * 40]


@pytest.mark.parametrize("q", HOSTILE)
def test_hostile_queries_never_fail_and_never_change_the_data(client, app_context, q):
    before = query_all("SELECT (SELECT COUNT(*) FROM characters) AS c, (SELECT COUNT(*) FROM users) AS u, (SELECT COUNT(*) FROM missions) AS m")
    response = client.get(API, query_string={"q": q})
    assert response.status_code in (200, 400), (q, response.status_code)
    assert "SELECT" not in response.get_data(as_text=True).replace("%' UNION SELECT user,password FROM users --", "")    # no SQL echoed back
    assert query_all("SELECT (SELECT COUNT(*) FROM characters) AS c, (SELECT COUNT(*) FROM users) AS u, (SELECT COUNT(*) FROM missions) AS m") == before


def test_the_query_text_is_only_ever_a_bound_parameter(monkeypatch):
    seen = []

    def capture(sql, params=None):
        seen.append((sql, list(params or [])))
        return []
    monkeypatch.setattr(search_repo, "query_all", capture)
    secret = "zq'x\\y%z_!w"
    terms, phrase = search_service.like_parts(secret)
    search_repo.search(search_repo.KIND_ORDER, terms, phrase, 8, 0)
    search_repo.counts(search_repo.KIND_ORDER, terms)
    assert len(seen) == 2
    for sql, params in seen:
        assert "zq" not in sql and "'x" not in sql and "!w" not in sql
        assert sql.count("%s") == len(params), "every value is a placeholder and every placeholder has a value"
        assert any("zq" in str(p) for p in params)


def test_wildcards_in_the_text_are_escaped_before_they_reach_the_database():
    terms, phrase = search_service.like_parts("50%_off!")
    assert terms == ["%50!%!_off!!%"]
    assert phrase == ["50%_off!", "50!%!_off!!%", "% 50!%!_off!!%", "%50!%!_off!!%"]


def test_the_search_repository_builds_no_sql_from_user_text():
    import ast
    from pathlib import Path
    source = (Path(search_repo.__file__)).read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name in ("search", "counts"):
            names = {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}
            assert not names & {"q", "query", "text", "raw"}, f"{node.name} must not see the raw query"


# ------------------------------------------------------------------ cost and failure
def test_a_search_is_one_database_round_trip(client, monkeypatch):
    calls = []
    real = search_repo.query_all
    monkeypatch.setattr(search_repo, "query_all", lambda sql, params=None: calls.append(sql) or real(sql, params))
    assert client.get(API, query_string={"q": "vice"}).status_code == 200
    assert len(calls) == 1


def test_a_database_failure_is_a_generic_json_503(client, monkeypatch):
    def broken(sql, params=None):
        raise mysql.connector.errors.DatabaseError("secret-host password=hunter2")
    monkeypatch.setattr(search_repo, "query_all", broken)
    response = client.get(API, query_string={"q": "vice"})
    assert response.status_code == 503 and response.is_json
    assert "hunter2" not in response.get_data(as_text=True) and "secret-host" not in response.get_data(as_text=True)


def test_a_search_is_read_only(client, app_context):
    before = query_all("SELECT (SELECT COUNT(*) FROM media_assets) AS a, (SELECT COUNT(*) FROM users) AS u")
    for q in ("vice", "jason", "radio", "neon"):
        client.get(API, query_string={"q": q})
    assert query_all("SELECT (SELECT COUNT(*) FROM media_assets) AS a, (SELECT COUNT(*) FROM users) AS u") == before


@pytest.mark.parametrize("kind", search_service.KINDS)
def test_every_kind_works_as_the_only_type_filter(client, kind):
    """A union whose first SELECT is not the character one must still be a valid statement (a regression found while building this)."""
    body = find(client, "a", type=kind, limit=20)
    assert body["type"] == kind and {h["kind"] for h in body["results"]} <= {kind}


def test_the_api_meets_its_budget_p95_under_50_ms_and_a_response_under_6_kb(client):
    """The Stage 4B budget (measured at about 6 ms p95 and 2 KB; the limits leave room for a slow machine). Warm: the first request opens the connection."""
    import time
    client.get(API, query_string={"q": "warm"})
    times, largest = [], 0
    for q in ("j", "jason", "vice city", "neon row", "radio", "a", "harbour lights", "cheetah"):
        for _ in range(8):
            start = time.perf_counter()
            response = client.get(API, query_string={"q": q, "limit": 20})
            times.append((time.perf_counter() - start) * 1000)
            largest = max(largest, len(response.data))
    times.sort()
    assert times[int(len(times) * 0.95)] < 50, f"p95 {times[int(len(times) * 0.95)]:.1f} ms"
    assert largest < 6 * 1024, f"largest response {largest} bytes"
