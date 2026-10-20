"""Migration 006 (Gate 3B): the Garage is right on a database that has not had it, right after it, and the migration changes nothing twice.

The owner's development database has migrations 001 to 005 but not 006 until they run it, so the Garage must show what that database
holds (five official vehicles) without claiming seven, and then show seven after the migration. These tests rebuild exactly that state in
the TEST database only (never the development one) and always restore the seeded test database afterwards."""
import re

import mysql.connector

from app.config import TestingConfig
from scripts import migrate_db
from scripts.init_db import init_database
from tests.test_migration import CONTENT_TABLES, MEDIA_TABLES, as_migrator, fingerprint

# the state of a database migrated through 005: the 006 vehicles, links and pictures are not there yet
BEFORE_006 = ["DELETE FROM media_vehicles WHERE vehicle_id IN (14, 15) OR media_id BETWEEN 108 AND 114",
              "DELETE FROM media_assets WHERE media_id BETWEEN 108 AND 114",
              "DELETE FROM vehicles WHERE vehicle_id IN (14, 15)"]
FIVE = ["grotti-cheetah", "vapid-dominator-buggy", "shitzu-squalo", "vapid-stanier", "vapid-ganado"]
SEVEN = FIVE + ["dinka-enduro", "crest-kayak"]


def page(client, path):
    response = client.get(path)
    assert response.status_code == 200, path
    return response.get_data(as_text=True)


def tiles(text):
    """The names a filtered list of the Garage shows (cards), in order."""
    return re.findall(r'<h3 class="gx-(?:m|f)__name">([^<]+)</h3>', text)


def cards(text):
    """Every machine the Garage landing links to (a stage, a half of the pair, or a card)."""
    return re.findall(r'<a class="gx-(?:f|d|m) [^"]*" href="/vehicles/([a-z-]+)"', text)


def rows(sql):
    connection = mysql.connector.connect(**TestingConfig.db_kwargs())
    try:
        cursor = connection.cursor()
        cursor.execute(sql)
        return cursor.fetchall()
    finally:
        connection.close()


def official_slugs():
    return [r[0] for r in rows("SELECT slug FROM vehicles WHERE content_status = 'official' ORDER BY vehicle_id")]


def test_migration_006_only_adds_and_rewords():
    path = next(f for f in migrate_db.migration_files() if f.name.startswith("006"))
    migrate_db.check_non_destructive(path)                                         # raises on DROP, DELETE or TRUNCATE outside comments
    sql = path.read_text(encoding="utf-8")
    assert "INSERT IGNORE INTO media_vehicles" in sql and "ON DUPLICATE KEY UPDATE" in sql
    updates = re.findall(r"UPDATE vehicles SET.*?;", sql, re.S)
    assert len(updates) == 5                                                       # only the five older vehicles' wording
    for statement in updates:                                                      # never a name, slug, category, label or source link
        assert not re.search(r"\b(slug|name|category_id|content_status|source_url)\s*=", statement.split("WHERE")[0]), statement


def test_a_database_without_006_shows_five_machines_and_never_claims_seven(app):
    client = app.test_client()
    try:
        as_migrator(BEFORE_006)
        assert official_slugs() == FIVE
        landing = page(client, "/vehicles")
        assert "Five machines of Leonida" in landing and "Seven" not in landing
        assert len(cards(landing)) == 5
        stage = landing.split("data-stage")[1].split("</section>")[0]
        assert stage.count("data-panel=") == 5 and stage.count("data-pick=") == 5       # the lineup is the five, not seven with two empty
        assert not re.search(r"Dinka|Enduro|Kayak|Crest", landing)                      # nothing names a vehicle the database lacks
        for slug in FIVE:
            assert not re.search(r"Dinka|Enduro|Kayak", page(client, f"/vehicles/{slug}")), slug   # previous and next wrap round the five that exist
        for slug in ("dinka-enduro", "crest-kayak"):
            assert client.get(f"/vehicles/{slug}").status_code == 404
        for path in ("/vehicles?q=grotti", "/vehicles?category=boat", "/vehicles?category=motorcycle", "/vehicles?sort=name_desc",
                     "/vehicles?sort=category", "/vehicles?q=zzzz", "/vehicles?per_page=2&page=2", "/vehicles?per_page=2&page=3", "/"):
            assert client.get(path).status_code == 200, path
        assert tiles(page(client, "/vehicles?category=boat")) == ["Squalo"]
        assert tiles(page(client, "/vehicles?q=kayak")) == []
        assert len(client.get("/api/v1/vehicles?status=official&per_page=50").get_json()["data"]) == 5
    finally:
        init_database(TestingConfig, seed=True, reset=True)


def test_running_006_gives_seven_machines_and_every_route_works(app):
    client = app.test_client()
    try:
        as_migrator(BEFORE_006)
        before = fingerprint(("vehicles",) + MEDIA_TABLES)
        assert migrate_db.main(["--test", "--yes"]) == 0
        assert fingerprint(("vehicles",) + MEDIA_TABLES) != before
        assert official_slugs() == SEVEN

        landing = page(client, "/vehicles")
        assert "Seven machines of Leonida" in landing and len(cards(landing)) == 7
        stage = landing.split("data-stage")[1].split("</section>")[0]
        assert stage.count("data-panel=") == 7 and stage.count("data-pick=") == 7
        for slug in SEVEN:
            assert page(client, f"/vehicles/{slug}").count("<h1") == 1, slug
        assert tiles(page(client, "/vehicles?q=kayak")) == ["Kayak"]
        assert sorted(tiles(page(client, "/vehicles?category=boat"))) == ["Kayak", "Squalo"]
        assert tiles(page(client, "/vehicles?category=motorcycle")) == ["Enduro Motorcycle"]
        asc = tiles(page(client, "/vehicles?sort=name_asc"))
        assert len(asc) == 7 and tiles(page(client, "/vehicles?sort=name_desc")) == list(reversed(asc))
        assert len(re.findall(r'<a class="gx-m ', page(client, "/vehicles?per_page=2&page=4"))) == 1
        assert len(client.get("/api/v1/vehicles?status=official&per_page=50").get_json()["data"]) == 7
        assert landing.count("gx-customs__track") == 1
    finally:
        init_database(TestingConfig, seed=True, reset=True)


def test_the_media_and_names_the_migration_adds_are_the_ones_the_pages_use(app):
    assert rows("SELECT slug, name, manufacturer, category_id FROM vehicles WHERE vehicle_id IN (14, 15) ORDER BY vehicle_id") == [
        ("dinka-enduro", "Dinka Enduro Motorcycle", "Dinka", 6), ("crest-kayak", "Crest Kayak", "Crest", 5)]
    assert rows("SELECT media_id, vehicle_id FROM media_vehicles WHERE media_id BETWEEN 108 AND 114 ORDER BY media_id, vehicle_id") == [(108, 14), (109, 15), (110, 14), (110, 15)]
    titles = dict(rows("SELECT media_id, title FROM media_assets WHERE media_id BETWEEN 108 AND 114"))
    assert sorted(titles) == list(range(108, 115))
    assert titles[108].startswith("Dinka Enduro Motorcycle") and titles[109].startswith("Crest Kayak") and titles[110].startswith("Jason")
    # every picture row is a remote reference to Rockstar's own server, with no local file
    assert all(u.startswith("https://www.rockstargames.com/VI/_next/static/media/") and p is None
               for u, p in rows("SELECT embed_url, local_path FROM media_assets WHERE media_id BETWEEN 108 AND 114"))


def test_running_006_twice_changes_nothing_the_second_time(app):
    try:
        as_migrator(BEFORE_006)
        assert migrate_db.main(["--test", "--yes"]) == 0
        once = fingerprint(CONTENT_TABLES + ("vehicles",) + MEDIA_TABLES)
        assert migrate_db.main(["--test", "--yes"]) == 0
        assert fingerprint(CONTENT_TABLES + ("vehicles",) + MEDIA_TABLES) == once
    finally:
        init_database(TestingConfig, seed=True, reset=True)
