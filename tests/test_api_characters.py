"""Characters API through the Flask test client, backed by real MySQL."""

BASE = "/api/v1/characters"


def test_list_returns_paginated_database_rows(client):
    body = client.get(BASE).get_json()
    assert body["pagination"] == {"page": 1, "per_page": 12, "total": 11, "pages": 1}
    assert len(body["data"]) == 11
    assert body["data"][0]["full_name"] == "Boobie Ike"  # alphabetical from the database
    assert "character_id" not in body["data"][0]


def test_pagination_slices_results(client):
    body = client.get(BASE + "?per_page=4&page=3").get_json()
    assert body["pagination"]["pages"] == 3
    assert len(body["data"]) == 3


def test_page_beyond_end_is_empty_not_an_error(client):
    response = client.get(BASE + "?per_page=4&page=50")
    assert response.status_code == 200
    assert response.get_json()["data"] == []


def test_search_matches_name_alias_and_role(client):
    names = lambda qs: [c["slug"] for c in client.get(BASE + qs).get_json()["data"]]
    assert names("?q=lucia") == ["lucia-caminos"]
    assert names("?q=gator") == ["tomas-reyes-hall"]  # alias
    assert names("?q=fixer") == ["delia-marsh"]       # role title


def test_filter_by_status(client):
    body = client.get(BASE + "?status=demo").get_json()
    assert body["pagination"]["total"] == 3
    assert {c["content_status"] for c in body["data"]} == {"demo"}


def test_filter_by_region(client):
    body = client.get(BASE + "?region=vice-city").get_json()
    assert [c["slug"] for c in body["data"]] == ["delia-marsh"]


def test_sorting(client):
    body = client.get(BASE + "?sort=name_desc&per_page=2").get_json()
    assert [c["full_name"] for c in body["data"]] == ["Tomas Reyes-Hall", "Real Dimez"]


def test_invalid_parameters_return_400_with_details(client):
    for qs in ("?status=bogus", "?sort=password", "?page=0", "?per_page=500", "?page=abc",
               "?region=Not A Slug", "?q=" + "x" * 81):
        response = client.get(BASE + qs)
        assert response.status_code == 400, qs
        assert response.get_json()["error"]["details"], qs


def test_sql_injection_attempt_is_just_text(client):
    for payload in ("' OR '1'='1", "'; DROP TABLE characters; --", "%", "_"):
        response = client.get(BASE, query_string={"q": payload})
        assert response.status_code == 200
        assert response.get_json()["pagination"]["total"] == 0, payload
    assert client.get(BASE).get_json()["pagination"]["total"] == 11  # table still intact


def test_detail_includes_related_records(client):
    body = client.get(BASE + "/delia-marsh").get_json()
    assert body["full_name"] == "Delia Marsh"
    assert body["content_status"] == "demo"
    assert body["home_location_name"] == "Bayfront Studio Lot"
    assert body["region_slug"] == "vice-city"
    assert {m["slug"] for m in body["missions"]} == {
        "harbour-lights", "quiet-water", "last-call-smokestack-row", "ledger-of-favours"}
    assert {r["slug"] for r in body["relationships"]} == {"nico-brandt", "tomas-reyes-hall"}
    assert "Pelican Quay Terminal" in {loc["name"] for loc in body["locations"]}
    assert "character_id" not in body


def test_relationships_show_both_directions(client):
    body = client.get(BASE + "/lucia-caminos").get_json()
    assert body["relationships"] == [{
        "direction": "incoming", "relationship_type": "partner",
        "description": "Presented on the official site as the two leads of the story.",
        "content_status": "official", "slug": "jason-duval", "full_name": "Jason Duval"}]


def test_official_character_exposes_source_and_no_invented_missions(client):
    body = client.get(BASE + "/jason-duval").get_json()
    assert body["content_status"] == "official"
    assert body["source_url"].startswith("https://")
    assert body["missions"] == []
    assert {r["slug"] for r in body["relationships"]} == {"lucia-caminos", "brian-heder", "cal-hampton"}


def test_unknown_character_is_a_json_404(client):
    response = client.get(BASE + "/nobody")
    assert response.status_code == 404
    assert response.get_json()["error"]["status"] == 404
