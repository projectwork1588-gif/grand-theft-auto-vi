"""JSON endpoints added in Phase 2 (vehicles, missions, locations) plus backward compatibility of Phase 1 shapes."""

# ------------------------------------------------------------------ vehicles
def test_vehicle_list_is_paginated_and_database_driven(client):
    body = client.get("/api/v1/vehicles").get_json()
    assert body["pagination"] == {"page": 1, "per_page": 9, "total": 13, "pages": 2}   # 8 concept + 5 official
    assert [v["name"] for v in body["data"]][:3] == ["'67 Vapid Dominator Buggy", "'95 Grotti Cheetah", "Bruiser V8"]
    assert {"slug", "name", "manufacturer", "summary", "content_status", "category_slug", "category_name"} == set(body["data"][0])


def test_vehicle_filters_search_sort_and_pagination(client):
    boats = client.get("/api/v1/vehicles?category=boat").get_json()
    assert boats["pagination"]["total"] == 3 and {v["category_slug"] for v in boats["data"]} == {"boat"}
    assert [v["slug"] for v in client.get("/api/v1/vehicles?q=airboat").get_json()["data"]] == ["swampfox-airboat"]
    assert [v["slug"] for v in client.get("/api/v1/vehicles?q=halcyon").get_json()["data"]] == ["bruiser-v8", "meridian-sedan"]  # manufacturer search
    desc = client.get("/api/v1/vehicles?sort=name_desc&per_page=2").get_json()
    assert [v["name"] for v in desc["data"]] == ["Zephyr 250", "Vapid Stanier"]
    page3 = client.get("/api/v1/vehicles?per_page=5&page=3").get_json()
    assert page3["pagination"]["pages"] == 3 and len(page3["data"]) == 3
    official = client.get("/api/v1/vehicles?status=official&sort=featured").get_json()
    assert [v["slug"] for v in official["data"]] == ["grotti-cheetah", "vapid-dominator-buggy", "shitzu-squalo", "vapid-stanier", "vapid-ganado"]
    assert client.get("/api/v1/vehicles?status=demo").get_json()["pagination"]["total"] == 8
    by_category = client.get("/api/v1/vehicles?sort=category&per_page=50").get_json()["data"]
    assert [v["category_name"] for v in by_category] == sorted(v["category_name"] for v in by_category)


def test_vehicle_invalid_parameters_are_400(client):
    for qs in ("?sort=price", "?category=Not A Slug", "?status=official-ish", "?page=0", "?per_page=51", "?q=" + "x" * 81):
        response = client.get("/api/v1/vehicles" + qs)
        assert response.status_code == 400, qs
        assert response.get_json()["error"]["details"], qs


def test_vehicle_detail_has_related_records(client):
    body = client.get("/api/v1/vehicles/swampfox-airboat").get_json()
    assert body["category_slug"] == "boat" and body["content_status"] == "demo"
    assert [m["slug"] for m in body["missions"]] == ["quiet-water"]
    assert body["missions"][0]["usage_note"] == "Primary transport"
    assert [l["slug"] for l in body["locations"]] == ["heron-reach-dock"]
    assert body["locations"][0]["region_slug"] == "grassrivers"
    assert [v["slug"] for v in body["same_category"]] == ["shitzu-squalo", "tidewalker-skiff"]
    assert "vehicle_id" not in body and "category_id" not in body


def test_vehicle_categories_endpoint_counts_with_group_by(client):
    data = client.get("/api/v1/vehicle-categories").get_json()["data"]
    assert len(data) == 6 and sum(c["vehicle_count"] for c in data) == 13
    assert {c["slug"]: c["vehicle_count"] for c in data}["boat"] == 3
    official = client.get("/api/v1/vehicle-categories?status=official").get_json()["data"]
    assert sum(c["vehicle_count"] for c in official) == 5 and {c["slug"]: c["vehicle_count"] for c in official}["motorcycle"] == 0
    assert client.get("/api/v1/vehicle-categories?status=bogus").status_code == 400


def test_unknown_vehicle_is_json_404(client):
    response = client.get("/api/v1/vehicles/not-a-car")
    assert response.status_code == 404 and response.get_json()["error"]["status"] == 404


# ------------------------------------------------------------------ missions
def test_mission_list_filters_and_counts(client):
    body = client.get("/api/v1/missions").get_json()
    assert body["pagination"]["total"] == 5
    first = next(m for m in body["data"] if m["slug"] == "ledger-of-favours")
    assert (first["cast_count"], first["vehicle_count"], first["location_count"]) == (3, 1, 2)
    assert [m["slug"] for m in client.get("/api/v1/missions?type=heist").get_json()["data"]] == ["last-call-smokestack-row"]
    assert client.get("/api/v1/missions?type=story").get_json()["pagination"]["total"] == 2
    assert [m["slug"] for m in client.get("/api/v1/missions?q=ridge").get_json()["data"]] == ["ridge-run"]
    assert [m["title"] for m in client.get("/api/v1/missions?sort=title_desc&per_page=2").get_json()["data"]] == ["Ridge Run", "Quiet Water"]
    assert client.get("/api/v1/missions?per_page=2&page=3").get_json()["data"][0]["slug"]


def test_mission_invalid_parameters_are_400(client):
    for qs in ("?type=raid", "?sort=random", "?status=real", "?page=-1"):
        assert client.get("/api/v1/missions" + qs).status_code == 400, qs


def test_mission_detail_joins_cast_vehicles_locations_and_related(client):
    body = client.get("/api/v1/missions/harbour-lights").get_json()
    assert {c["slug"] for c in body["characters"]} == {"delia-marsh", "nico-brandt"}
    assert {v["slug"] for v in body["vehicles"]} == {"bruiser-v8", "tidewalker-skiff"}
    assert body["locations"][0]["slug"] == "pelican-quay-terminal" and body["locations"][0]["is_primary"] == 1
    assert [(m["title"], m["shared"]) for m in body["related"]] == [
        ("Last Call at Smokestack Row", 2), ("Ledger of Favours", 2), ("Quiet Water", 1)]
    assert "mission_id" not in body


def test_unknown_mission_is_json_404(client):
    assert client.get("/api/v1/missions/nothing").status_code == 404


# ------------------------------------------------------------------ locations
def test_location_list_filters(client):
    body = client.get("/api/v1/locations").get_json()
    assert body["pagination"]["total"] == 8
    assert body["data"][0]["region_name"] <= body["data"][-1]["region_name"]  # default sort is by region
    assert client.get("/api/v1/locations?region=vice-city").get_json()["pagination"]["total"] == 3
    assert client.get("/api/v1/locations?type=waterfront").get_json()["pagination"]["total"] == 3
    assert [l["slug"] for l in client.get("/api/v1/locations?q=marina").get_json()["data"]] == ["coral-hook-marina"]
    both = client.get("/api/v1/locations?region=port-gellhorn&type=waterfront").get_json()
    assert [l["slug"] for l in both["data"]] == ["pelican-quay-terminal"] and both["data"][0]["mission_count"] == 1
    assert [l["name"] for l in client.get("/api/v1/locations?sort=name_desc&per_page=2").get_json()["data"]] == [
        "Sunset Pier Boardwalk", "Smokestack Row"]


def test_location_invalid_parameters_are_400(client):
    for qs in ("?type=castle", "?region=BAD SLUG", "?sort=x", "?per_page=0"):
        assert client.get("/api/v1/locations" + qs).status_code == 400, qs


def test_location_detail_relationships(client):
    body = client.get("/api/v1/locations/bayfront-studio-lot").get_json()
    assert body["region_slug"] == "vice-city" and body["region_status"] == "official"
    assert [c["slug"] for c in body["residents"]] == ["delia-marsh"]
    assert [m["slug"] for m in body["missions"]] == ["ledger-of-favours"]
    assert {c["slug"] for c in body["characters_in_missions"]} == {"delia-marsh", "tomas-reyes-hall", "nico-brandt"}
    assert {n["slug"] for n in body["neighbours"]} == {"neon-row-district", "sunset-pier-boardwalk"}
    assert "location_id" not in body and "region_id" not in body


def test_unknown_location_is_json_404(client):
    assert client.get("/api/v1/locations/atlantis-pier").status_code == 404


# ------------------------------------------------------------------ Phase 1 backward compatibility
def test_phase1_response_shapes_are_unchanged(client):
    item = client.get("/api/v1/characters").get_json()["data"][0]
    assert set(item) == {"slug", "full_name", "alias", "role_title", "summary", "content_status",
                         "home_location_slug", "home_location_name", "region_slug", "region_name"}
    detail = client.get("/api/v1/characters/jason-duval").get_json()
    assert set(detail) == {"slug", "full_name", "alias", "role_title", "summary", "biography", "content_status",
                           "source_url", "source_note", "home_location_slug", "home_location_name", "region_slug",
                           "region_name", "relationships", "regions", "missions", "locations"}   # regions: added in Gate 3A
    region = client.get("/api/v1/regions").get_json()
    assert set(region) == {"data", "filters"} and set(region["data"][0]) == {"slug", "name", "summary", "content_status", "location_count"}
    assert set(client.get("/api/v1/regions/vice-city").get_json()) == {
        "slug", "name", "summary", "description", "content_status", "source_url", "source_note", "locations", "characters"}
    assert client.get("/health").get_json()["status"] == "ok"
