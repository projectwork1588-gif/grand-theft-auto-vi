"""Migration 001 is non-destructive, idempotent, and upgrades a Phase 1-shaped database without touching its content."""
import hashlib

import mysql.connector
import pytest

from app.config import TestingConfig
from scripts import migrate_db
from scripts.init_db import init_database

CONTENT_TABLES = ("regions", "locations", "characters", "character_relationships", "vehicle_categories",
                  "missions", "mission_characters", "mission_vehicles", "mission_locations")
MEDIA_TABLES = ("media_assets", "media_characters", "media_regions", "media_vehicles")
PHASE1_SHAPE = ["DROP TABLE media_vehicles", "DROP TABLE media_regions", "DELETE FROM vehicles WHERE vehicle_id > 8",
                "DELETE FROM media_assets WHERE media_id > 3",
                "UPDATE media_assets SET embed_url = NULL, usage_status = 'link_only', approval_status = 'pending_review' WHERE media_id IN (1, 2)",
                "UPDATE characters SET summary = 'Fictional demo character.', biography = 'Fictional demo character invented by Team Valkyrie.', source_note = 'Invented for database demonstration.' WHERE content_status = 'demo'",
                "UPDATE locations SET summary = 'Fictional demo location.', description = 'Fictional demo location invented by Team Valkyrie.', source_note = 'Invented for database demonstration.' WHERE content_status = 'demo'",
                "UPDATE missions SET summary = 'Demo mission.', synopsis = 'Fictional demo mission invented by Team Valkyrie.', source_note = 'Invented for database demonstration.' WHERE content_status = 'demo'",
                "UPDATE vehicles SET summary = 'Fictional demo vehicle.', description = 'Fictional demo vehicle invented by Team Valkyrie.', source_note = 'Invented for database demonstration.' WHERE content_status = 'demo'",
                "UPDATE character_relationships SET description = 'Demo: a relationship.' WHERE content_status = 'demo'"]

OFFICIAL_TABLES = ("regions", "characters", "character_relationships")


def fingerprint(tables):
    """Hash of table contents (ignoring created_at) read on a fresh connection so no locks linger."""
    connection = mysql.connector.connect(**TestingConfig.db_kwargs())
    try:
        cursor = connection.cursor(dictionary=True)
        digest = hashlib.sha256()
        for table in tables:
            cursor.execute(f"SELECT * FROM {table} ORDER BY 1, 2")
            for row in cursor.fetchall():
                row.pop("created_at", None)
                digest.update(repr(sorted(row.items())).encode())
        return digest.hexdigest()
    finally:
        connection.close()


def official_fingerprint():
    """Hash of every official region, character and relationship. Migrations must never change what Rockstar states."""
    connection = mysql.connector.connect(**TestingConfig.db_kwargs())
    try:
        cursor = connection.cursor(dictionary=True)
        digest = hashlib.sha256()
        for table in OFFICIAL_TABLES:
            cursor.execute(f"SELECT * FROM {table} WHERE content_status = 'official' ORDER BY 1, 2")
            for row in cursor.fetchall():
                row.pop("created_at", None)
                digest.update(repr(sorted(row.items())).encode())
        return digest.hexdigest()
    finally:
        connection.close()


def as_migrator(statements):
    connection = mysql.connector.connect(**TestingConfig.migration_kwargs())
    try:
        cursor = connection.cursor()
        for statement in statements:
            cursor.execute(statement)
        connection.commit()
    finally:
        connection.close()


def test_destructive_statement_detector():
    for sql in ("DROP TABLE users", "delete from users", "TRUNCATE TABLE users", "DROP DATABASE x"):
        assert migrate_db.is_destructive(sql), sql
    assert not migrate_db.is_destructive("CREATE TABLE t (a INT, CONSTRAINT f FOREIGN KEY (a) REFERENCES u (id) ON DELETE CASCADE)")
    assert not migrate_db.is_destructive("INSERT IGNORE INTO media_regions (media_id, region_id) VALUES (1, 1)")


def test_shipped_migrations_contain_nothing_destructive():
    files = migrate_db.migration_files()
    assert [f.name for f in files] == ["001_phase2_media.sql", "002_phase2_garage.sql", "003_concept_copy.sql", "004_leonida_in_motion.sql"]
    for path in files:
        migrate_db.check_non_destructive(path)  # raises if it finds DROP, DELETE or TRUNCATE


def test_runner_refuses_a_destructive_migration(tmp_path):
    bad = tmp_path / "002_bad.sql"
    bad.write_text("DELETE FROM characters;")
    with pytest.raises(ValueError):
        migrate_db.check_non_destructive(bad)


def test_plan_mode_changes_nothing(app, capsys):
    before = fingerprint(CONTENT_TABLES + ("vehicles",) + MEDIA_TABLES)
    assert migrate_db.main(["--test", "--plan"]) == 0
    out = capsys.readouterr().out
    assert "nothing is dropped, deleted or truncated" in out.lower() and "--plan given: nothing was changed" in out
    assert fingerprint(CONTENT_TABLES + ("vehicles",) + MEDIA_TABLES) == before


def test_migration_is_idempotent_on_a_seeded_database(app):
    before = fingerprint(CONTENT_TABLES + ("vehicles",) + MEDIA_TABLES)
    assert migrate_db.main(["--test", "--yes"]) == 0
    assert migrate_db.main(["--test", "--yes"]) == 0
    assert fingerprint(CONTENT_TABLES + ("vehicles",) + MEDIA_TABLES) == before


def test_seed_and_migration_agree(app):
    """A fresh database (schema + seed) must equal an upgraded one, otherwise the two would drift apart."""
    seeded = fingerprint(CONTENT_TABLES + ("vehicles",) + MEDIA_TABLES)
    try:
        # Rebuild WITHOUT the Phase 2 media, as the owner's existing Phase 1 database looks.
        as_migrator(PHASE1_SHAPE)
        official_before = official_fingerprint()
        phase1_content = fingerprint(CONTENT_TABLES)
        phase1_vehicles = fingerprint(("vehicles",))
        assert fingerprint(MEDIA_TABLES[:2]) != seeded
        assert migrate_db.main(["--test", "--yes"]) == 0
        assert fingerprint(CONTENT_TABLES) != phase1_content                 # the concept copy was rewritten (migration 003)
        assert official_fingerprint() == official_before                       # nothing Rockstar states was touched
        assert fingerprint(("vehicles",)) != phase1_vehicles                 # the five official vehicles were added
        assert fingerprint(CONTENT_TABLES + ("vehicles",) + MEDIA_TABLES) == seeded   # upgraded == freshly seeded
    finally:
        init_database(TestingConfig, seed=True, reset=True)                  # leave a pristine test database


def test_pages_work_on_a_phase1_shaped_database_and_the_migration_adds_the_visuals(app):
    client = app.test_client()
    try:
        as_migrator(PHASE1_SHAPE)
        for path in ("/", "/characters", "/characters/jason-duval", "/regions", "/regions/vice-city", "/missions", "/vehicles"):
            response = client.get(path)
            assert response.status_code == 200, path
            assert "rockstargames.com/VI/_next/static/media" not in response.get_data(as_text=True), path
        assert "rockstargames.com/VI/trailer-1" in client.get("/").get_data(as_text=True)

        assert migrate_db.main(["--test", "--yes"]) == 0
        page = client.get("/regions/vice-city").get_data(as_text=True)
        assert "rockstargames.com/VI/_next/static/media/Vice_City_Postcard" in page
        assert 'data-video="https://www.rockstargames.com/videoplayer' in client.get("/").get_data(as_text=True)
    finally:
        init_database(TestingConfig, seed=True, reset=True)
