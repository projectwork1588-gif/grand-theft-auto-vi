"""The seed must be deterministic, honest about its sources, and free of copied media."""
import hashlib

from app.config import TestingConfig
from scripts.init_db import init_database

TABLES = ("regions", "locations", "characters", "character_relationships", "vehicle_categories",
          "vehicles", "missions", "mission_characters", "mission_vehicles", "mission_locations",
          "media_assets", "media_characters", "media_regions", "media_vehicles")


def count(cur, table):
    cur.execute(f"SELECT COUNT(*) AS n FROM {table}")
    return cur.fetchone()["n"]


def test_exact_row_counts(cur):
    expected = {"regions": 6, "locations": 8, "characters": 11, "character_relationships": 7,
                "vehicle_categories": 6, "vehicles": 13, "missions": 5, "mission_characters": 10,
                "mission_vehicles": 8, "mission_locations": 8, "media_assets": 85,
                "media_characters": 54, "media_regions": 20, "media_vehicles": 17, "media_locations": 0, "users": 0}
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


def test_missions_and_locations_are_all_concept_records(cur):
    for table in ("missions", "locations"):
        cur.execute(f"SELECT COUNT(*) AS n FROM {table} WHERE content_status <> 'demo'")
        assert cur.fetchone()["n"] == 0, table


def test_official_vehicles_are_exactly_the_five_rockstar_shows(cur):
    cur.execute("SELECT slug, source_url FROM vehicles WHERE content_status = 'official' ORDER BY vehicle_id")
    rows = cur.fetchall()
    assert [r["slug"] for r in rows] == ["grotti-cheetah", "vapid-dominator-buggy", "shitzu-squalo", "vapid-stanier", "vapid-ganado"]
    assert all(r["source_url"].startswith("https://www.rockstargames.com/VI/") for r in rows)
    cur.execute("SELECT COUNT(*) AS n FROM vehicles WHERE content_status = 'demo'")
    assert cur.fetchone()["n"] == 8


def test_every_official_vehicle_has_official_images_and_concept_vehicles_have_none(cur):
    cur.execute("SELECT v.slug, COUNT(mv.media_id) AS n FROM vehicles v LEFT JOIN media_vehicles mv ON mv.vehicle_id = v.vehicle_id "
                "WHERE v.content_status = 'official' GROUP BY v.vehicle_id, v.slug")
    counts = {r["slug"]: r["n"] for r in cur.fetchall()}
    assert counts == {"grotti-cheetah": 4, "vapid-dominator-buggy": 4, "shitzu-squalo": 4, "vapid-stanier": 4, "vapid-ganado": 1}
    cur.execute("SELECT COUNT(*) AS n FROM media_vehicles mv JOIN vehicles v ON v.vehicle_id = mv.vehicle_id WHERE v.content_status <> 'official'")
    assert cur.fetchone()["n"] == 0


def test_no_made_up_vehicle_names(cur):
    """Names Rockstar's own page treats as stores or services must never become vehicles."""
    cur.execute("SELECT name FROM vehicles WHERE content_status = 'official'")
    names = " ".join(r["name"] for r in cur.fetchall())
    for not_a_vehicle in ("Stock 305", "Electric Fang", "Rideout", "One-Eyed Willie", "Sara"):
        assert not_a_vehicle not in names


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


def test_media_sources_are_official_rockstar_pages(cur):
    cur.execute("SELECT slug, source_url FROM media_assets")
    for row in cur.fetchall():
        assert row["source_url"].startswith("https://www.rockstargames.com/VI"), row["slug"]


def test_media_is_remote_official_only_and_nothing_is_copied_locally(cur):
    """Images and players are remote references to Rockstar. No file is stored in this project."""
    cur.execute("SELECT COUNT(*) AS n FROM media_assets WHERE local_path IS NOT NULL")
    assert cur.fetchone()["n"] == 0
    cur.execute("SELECT slug, embed_url FROM media_assets WHERE embed_url IS NOT NULL")
    for row in cur.fetchall():
        assert (row["embed_url"].startswith("https://www.rockstargames.com/VI/_next/static/media/")
                or row["embed_url"].startswith("https://www.rockstargames.com/videoplayer?")), row["slug"]


def test_video_embeds_are_official_players_and_documented(cur):
    cur.execute("SELECT slug, usage_status, approval_status, embed_url FROM media_assets "
                "WHERE media_type IN ('trailer', 'video') AND usage_status = 'embed_permitted' ORDER BY media_id")
    rows = cur.fetchall()
    assert [r["slug"] for r in rows] == ["official-trailer-1", "official-trailer-2", "official-an-extended-look"]
    for r in rows:
        assert "videoplayer?id=" in r["embed_url"]
    # One poster-and-link clip card per named character. The clip files themselves are never hosted or played here.
    cur.execute("SELECT m.slug, m.source_url, m.embed_url, c.slug AS character_slug FROM media_assets m "
                "JOIN media_characters mc ON mc.media_id = m.media_id JOIN characters c ON c.character_id = mc.character_id "
                "WHERE m.media_type = 'video' AND m.usage_status = 'link_only' ORDER BY m.media_id")
    clips = cur.fetchall()
    assert len(clips) == 8 and len({c["character_slug"] for c in clips}) == 8
    assert all(c["source_url"] == "https://www.rockstargames.com/VI/media/videos" and c["embed_url"].endswith(".jpg") for c in clips)


def test_every_official_character_and_region_has_official_media(cur):
    cur.execute("SELECT c.slug FROM characters c LEFT JOIN media_characters mc ON mc.character_id = c.character_id "
                "WHERE c.content_status = 'official' GROUP BY c.character_id, c.slug HAVING COUNT(mc.media_id) = 0")
    assert cur.fetchall() == []
    cur.execute("SELECT r.slug FROM regions r LEFT JOIN media_regions mr ON mr.region_id = r.region_id "
                "GROUP BY r.region_id, r.slug HAVING COUNT(mr.media_id) = 0")
    assert cur.fetchall() == []


def test_demo_records_never_get_official_media(cur):
    """Official images must not be attached to fictional characters or locations."""
    cur.execute("SELECT COUNT(*) AS n FROM media_characters mc JOIN characters c ON c.character_id = mc.character_id "
                "WHERE c.content_status = 'demo'")
    assert cur.fetchone()["n"] == 0
    cur.execute("SELECT COUNT(*) AS n FROM media_locations")
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
