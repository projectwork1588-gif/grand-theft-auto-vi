"""The seed must be deterministic, honest about its sources, and free of copied media."""
import hashlib

from app.config import TestingConfig
from scripts.init_db import init_database

TABLES = ("regions", "locations", "characters", "character_relationships", "vehicle_categories",
          "vehicles", "missions", "mission_characters", "mission_vehicles", "mission_locations",
          "media_assets")


def count(cur, table):
    cur.execute(f"SELECT COUNT(*) AS n FROM {table}")
    return cur.fetchone()["n"]


def test_exact_row_counts(cur):
    expected = {"regions": 6, "locations": 8, "characters": 11, "character_relationships": 7,
                "vehicle_categories": 6, "vehicles": 8, "missions": 5, "mission_characters": 10,
                "mission_vehicles": 8, "mission_locations": 8, "media_assets": 3,
                "users": 0}
    for table, n in expected.items():
        assert count(cur, table) == n, table


def test_official_records_always_have_a_source(cur):
    for table in ("regions", "locations", "characters", "vehicles", "missions"):
        cur.execute(f"SELECT COUNT(*) AS n FROM {table} WHERE content_status = 'official' AND source_url IS NULL")
        assert cur.fetchone()["n"] == 0, table


def test_only_confirmed_names_are_marked_official(cur):
    cur.execute("SELECT slug FROM characters WHERE content_status = 'official' ORDER BY slug")
    assert [r["slug"] for r in cur.fetchall()] == [
        "boobie-ike", "brian-heder", "cal-hampton", "dre-quan-priest", "jason-duval", "lucia-caminos",
        "raul-bautista", "real-dimez"]  # the eight names on rockstargames.com/VI/only-in-leonida
    cur.execute("SELECT slug FROM regions WHERE content_status = 'official' ORDER BY slug")
    assert [r["slug"] for r in cur.fetchall()] == [
        "ambrosia", "grassrivers", "leonida-keys", "mount-kalaga", "port-gellhorn", "vice-city"]


def test_official_sources_point_at_rockstar(cur):
    for table in ("regions", "characters"):
        cur.execute(f"SELECT DISTINCT source_url FROM {table} WHERE content_status = 'official'")
        for row in cur.fetchall():
            assert row["source_url"].startswith("https://www.rockstargames.com/VI"), (table, row)


def test_vehicles_and_missions_are_all_demo(cur):
    for table in ("vehicles", "missions", "locations"):
        cur.execute(f"SELECT COUNT(*) AS n FROM {table} WHERE content_status <> 'demo'")
        assert cur.fetchone()["n"] == 0, table


def test_no_demo_mission_features_an_official_character(cur):
    """We never write invented story about real GTA VI characters."""
    cur.execute(
        "SELECT COUNT(*) AS n FROM mission_characters mc "
        "JOIN characters c ON c.character_id = mc.character_id "
        "JOIN missions m ON m.mission_id = mc.mission_id "
        "WHERE m.content_status = 'demo' AND c.content_status = 'official'"
    )
    assert cur.fetchone()["n"] == 0


def test_every_region_has_a_location_and_every_mission_a_primary_location(cur):
    cur.execute("SELECT COUNT(*) AS n FROM regions r LEFT JOIN locations l ON l.region_id = r.region_id "
                "WHERE l.location_id IS NULL")
    assert cur.fetchone()["n"] == 0
    cur.execute("SELECT m.mission_id FROM missions m LEFT JOIN mission_locations ml "
                "ON ml.mission_id = m.mission_id AND ml.is_primary = TRUE GROUP BY m.mission_id "
                "HAVING COUNT(ml.location_id) <> 1")
    assert cur.fetchall() == []


def test_media_sources_are_official_pages(cur):
    cur.execute("SELECT source_url FROM media_assets ORDER BY media_id")
    assert [r["source_url"] for r in cur.fetchall()] == [
        "https://www.rockstargames.com/VI/trailer-1",
        "https://www.rockstargames.com/VI/trailer-2",
        "https://www.rockstargames.com/VI/media"]


def test_media_rows_are_links_only_and_await_human_review(cur):
    cur.execute("SELECT COUNT(*) AS n FROM media_assets WHERE local_path IS NOT NULL OR embed_url IS NOT NULL")
    assert cur.fetchone()["n"] == 0
    cur.execute("SELECT COUNT(*) AS n FROM media_assets WHERE approval_status <> 'pending_review'")
    assert cur.fetchone()["n"] == 0


def _fingerprint(cur):
    digest = hashlib.sha256()
    for table in TABLES:
        cur.execute(f"SELECT * FROM {table} ORDER BY 1, 2")
        for row in cur.fetchall():
            row.pop("created_at", None)
            digest.update(repr(sorted(row.items())).encode())
    return digest.hexdigest()


def test_reseeding_gives_identical_data(cur):
    before = _fingerprint(cur)
    cur.execute("COMMIT")  # release metadata locks, otherwise DROP TABLE would wait on us
    init_database(TestingConfig, seed=True, reset=True)
    assert _fingerprint(cur) == before
