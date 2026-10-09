"""Regions API through the Flask test client, backed by real MySQL."""

BASE = "/api/v1/regions"


def test_list_regions_with_location_counts(client):
    body = client.get(BASE).get_json()
    by_slug = {r["slug"]: r for r in body["data"]}
    assert len(body["data"]) == 6
    assert by_slug["vice-city"]["location_count"] == 3   # GROUP BY / COUNT from MySQL
    assert by_slug["mount-kalaga"]["location_count"] == 1
    assert [r["name"] for r in body["data"]] == sorted(r["name"] for r in body["data"])


def test_filter_regions_by_status(client):
    assert len(client.get(BASE + "?status=official").get_json()["data"]) == 6
    assert client.get(BASE + "?status=fan").get_json()["data"] == []
    assert client.get(BASE + "?status=nope").status_code == 400


def test_region_detail_lists_locations_and_characters(client):
    body = client.get(BASE + "/vice-city").get_json()
    assert body["content_status"] == "official"
    assert body["source_url"] == "https://www.rockstargames.com/VI/only-in-leonida"
    assert [loc["slug"] for loc in body["locations"]] == [
        "bayfront-studio-lot", "neon-row-district", "sunset-pier-boardwalk"]
    assert [c["slug"] for c in body["characters"]] == ["delia-marsh"]
    assert "region_id" not in body


def test_every_region_is_official_and_sourced(client):
    for slug in ("vice-city", "leonida-keys", "grassrivers", "port-gellhorn", "ambrosia", "mount-kalaga"):
        body = client.get(f"{BASE}/{slug}").get_json()
        assert body["content_status"] == "official", slug
        assert body["source_url"].startswith("https://www.rockstargames.com/VI"), slug


def test_unknown_region_is_a_json_404(client):
    response = client.get(BASE + "/atlantis")
    assert response.status_code == 404
    assert response.get_json()["error"]["title"] == "Not Found"
