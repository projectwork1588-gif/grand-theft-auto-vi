"""`scripts.migrate_db --only <file>`: apply or plan exactly one migration, with the prerequisite and conflict checks migration 006 needs.

Everything here runs against the TEST database only; the seeded test database is restored at the end of each test that changes it."""
import mysql.connector
import pytest

from app.config import TestingConfig
from scripts import migrate_db, migration_checks
from scripts.init_db import init_database
from tests.test_gate3b_migration import BEFORE_006, official_slugs, rows
from tests.test_migration import CONTENT_TABLES, MEDIA_TABLES, as_migrator, fingerprint

ONLY = ["--test", "--only", "006_gate3b_garage.sql"]
EVERYTHING = CONTENT_TABLES + ("vehicles",) + MEDIA_TABLES


# ------------------------------------------------------------------ choosing the file
@pytest.mark.parametrize("bad", ["", "nope.sql", "006", "006_gate3b_garage", "006_GATE3B_GARAGE.SQL", "../006_gate3b_garage.sql", "./006_gate3b_garage.sql",
                                 "database/migrations/006_gate3b_garage.sql", "migrations\\006_gate3b_garage.sql", "..\\seed.sql", "/etc/passwd",
                                 "C:\\Windows\\win.ini", "../seed.sql", "seed.sql", "schema.sql", "..", "006_gate3b_garage.sql ", "006_gate3b_garage.sql\n"])
def test_an_unknown_name_or_a_path_is_refused(bad):
    with pytest.raises(ValueError):
        migrate_db.select_migration(bad)


def test_an_exact_file_name_selects_that_one_file_inside_the_migrations_folder():
    path = migrate_db.select_migration("006_gate3b_garage.sql")
    assert path.name == "006_gate3b_garage.sql" and path.parent == migrate_db.MIGRATIONS
    assert [migrate_db.select_migration(p.name) for p in migrate_db.migration_files()] == migrate_db.migration_files()


def test_a_refused_name_exits_with_a_message_before_any_database_is_touched(capsys, monkeypatch):
    def no_connection(**kwargs):
        raise AssertionError("the runner must not connect when the name is refused")
    monkeypatch.setattr(mysql.connector, "connect", no_connection)
    for bad in ("../seed.sql", "unknown.sql"):
        assert migrate_db.main(["--test", "--only", bad, "--plan"]) == 2
    assert "FAILED" in capsys.readouterr().err


# ------------------------------------------------------------------ the plan
def test_the_plan_for_one_migration_lists_only_that_migration_and_changes_nothing(app, capsys):
    before = fingerprint(EVERYTHING)
    assert migrate_db.main(ONLY + ["--plan"]) == 0
    out = capsys.readouterr().out
    assert "006_gate3b_garage.sql" in out and "All checks passed" in out and "--plan given: nothing was changed" in out
    for other in ("001_phase2_media.sql", "002_phase2_garage.sql", "003_concept_copy.sql", "004_leonida_in_motion.sql", "005_gate3a_cast.sql", "007_region_wording.sql", "008_music.sql"):
        assert other not in out
    assert fingerprint(EVERYTHING) == before


def test_the_default_plan_still_lists_every_migration(app, capsys):
    assert migrate_db.main(["--test", "--plan"]) == 0
    out = capsys.readouterr().out
    assert all(p.name in out for p in migrate_db.migration_files()) and "CHECKS before applying" not in out


def test_the_plan_on_a_database_without_006_says_what_it_will_add(app, capsys):
    try:
        as_migrator(BEFORE_006)
        assert migrate_db.main(ONLY + ["--plan"]) == 0
        out = capsys.readouterr().out
        assert "vehicle id 14 (Dinka Enduro Motorcycle): free, will be added" in out and "media ids 108 to 114: 0 already present, 7 will be added" in out
        assert "5 official vehicles" in out
    finally:
        init_database(TestingConfig, seed=True, reset=True)


# ------------------------------------------------------------------ applying exactly one file
def test_applying_only_006_leaves_the_older_migrations_unrun_and_the_default_run_still_runs_them(app):
    tamper = "UPDATE vehicles SET summary = 'OWNER EDIT' WHERE vehicle_id = 1"          # migration 003 sets this demo vehicle's wording
    try:
        as_migrator(BEFORE_006 + [tamper])
        assert migrate_db.main(ONLY + ["--yes"]) == 0
        assert official_slugs()[-2:] == ["dinka-enduro", "crest-kayak"]
        assert rows("SELECT summary FROM vehicles WHERE vehicle_id = 1") == [("OWNER EDIT",)]      # 003 was not run
        assert migrate_db.main(["--test", "--yes"]) == 0                                   # the default behaviour is unchanged: it runs all of them
        assert rows("SELECT summary FROM vehicles WHERE vehicle_id = 1") == [("A concept sports coupe.",)]
    finally:
        init_database(TestingConfig, seed=True, reset=True)


def test_applying_only_006_twice_changes_nothing_the_second_time(app, capsys):
    try:
        as_migrator(BEFORE_006)
        assert migrate_db.main(ONLY + ["--yes"]) == 0
        assert "After 006: 7 official vehicles (expected 7)" in capsys.readouterr().out
        once = fingerprint(EVERYTHING)
        assert migrate_db.main(ONLY + ["--plan"]) == 0
        assert "already present, will be refreshed with the same content" in capsys.readouterr().out
        assert migrate_db.main(ONLY + ["--yes"]) == 0
        assert fingerprint(EVERYTHING) == once
    finally:
        init_database(TestingConfig, seed=True, reset=True)


# ------------------------------------------------------------------ conflicts are reported, never overwritten
CONFLICTS = [
    ("vehicle id 14 already holds another vehicle",
     ["INSERT INTO vehicles (vehicle_id, category_id, slug, name, manufacturer, summary, description, content_status, source_url) VALUES "
      "(14, 1, 'owners-own-car', 'Owners Own Car', 'Me', 'mine', 'mine', 'official', 'https://example.test')"],
     ["DELETE FROM vehicles WHERE vehicle_id = 14"], "vehicle id 14 already holds 'owners-own-car'"),
    ("the slug belongs to a different id",
     ["INSERT INTO vehicles (vehicle_id, category_id, slug, name, manufacturer, summary, description, content_status, source_url) VALUES "
      "(40, 5, 'crest-kayak', 'Another Kayak', 'Me', 'mine', 'mine', 'official', 'https://example.test')"],
     ["DELETE FROM vehicles WHERE vehicle_id = 40"], "slug 'crest-kayak' already belongs to vehicle id 40"),
    ("the name belongs to a different id",
     ["INSERT INTO vehicles (vehicle_id, category_id, slug, name, manufacturer, summary, description, content_status, source_url) VALUES "
      "(41, 6, 'my-bike', 'Dinka Enduro Motorcycle', 'Me', 'mine', 'mine', 'official', 'https://example.test')"],
     ["DELETE FROM vehicles WHERE vehicle_id = 41"], "name 'Dinka Enduro Motorcycle' already belongs to vehicle id 41"),
    ("media id 110 already holds another picture",
     ["INSERT INTO media_assets (media_id, slug, title, media_type, intended_use, source_url, attribution, usage_status, approval_status) VALUES "
      "(110, 'owners-picture', 'Mine', 'screenshot', 'mine', 'https://example.test', 'me', 'link_only', 'pending_review')"],
     ["DELETE FROM media_assets WHERE media_id = 110"], "media id 110 already holds 'owners-picture'"),
    ("a media slug belongs to a different id",
     ["INSERT INTO media_assets (media_id, slug, title, media_type, intended_use, source_url, attribution, usage_status, approval_status) VALUES "
      "(300, 'garage-jasons-safehouse', 'Mine', 'screenshot', 'mine', 'https://example.test', 'me', 'link_only', 'pending_review')"],
     ["DELETE FROM media_assets WHERE media_id = 300"], "media slug 'garage-jasons-safehouse' already belongs to media id 300"),
    ("an older official vehicle is missing",
     ["DELETE FROM vehicles WHERE vehicle_id = 13"], [], "official vehicle 13 should be 'vapid-ganado'"),
]


@pytest.mark.parametrize("name, setup, undo, expected", CONFLICTS, ids=[c[0] for c in CONFLICTS])
def test_a_conflict_blocks_the_migration_and_nothing_is_overwritten(app, capsys, name, setup, undo, expected):
    try:
        as_migrator(BEFORE_006 + setup)
        before = fingerprint(("vehicles",) + MEDIA_TABLES)
        assert migrate_db.main(ONLY + ["--plan"]) == 1                                      # the plan reports it
        out = capsys.readouterr().out
        assert "STOP " in out and expected in out and "BLOCKED" in out
        assert migrate_db.main(ONLY + ["--yes"]) == 1                                       # and applying refuses, even with --yes
        assert fingerprint(("vehicles",) + MEDIA_TABLES) == before                          # not one row was touched
        assert "Applied" not in capsys.readouterr().out
    finally:
        init_database(TestingConfig, seed=True, reset=True)


def test_a_stray_link_on_the_migrations_pictures_is_a_conflict(app, capsys):
    try:
        as_migrator(BEFORE_006 + ["INSERT INTO media_assets (media_id, slug, title, media_type, intended_use, source_url, attribution, usage_status, approval_status) VALUES "
                                  "(108, 'vehicle-dinka-enduro-01', 'Dinka', 'screenshot', 'x', 'https://example.test', 'me', 'link_only', 'pending_review')",
                                  "INSERT INTO media_vehicles (media_id, vehicle_id) VALUES (108, 9)"])
        assert migrate_db.main(ONLY + ["--plan"]) == 1
        assert "(media 108, vehicle 9)" in capsys.readouterr().out
    finally:
        init_database(TestingConfig, seed=True, reset=True)


# ------------------------------------------------------------------ the checker itself
class EmptyCursor:
    """A database with none of the tables."""
    def execute(self, sql, params=()):
        pass

    def fetchall(self):
        return []


def test_missing_tables_are_named_as_prerequisites():
    notes, problems = migration_checks.check_006(EmptyCursor(), "somewhere")
    assert not notes and any("table 'vehicles' does not exist" in p and "001 to 005" in p for p in problems)


def test_what_the_checker_expects_is_what_the_migration_puts_in_the_database(app):
    assert dict((v, (s, n, c)) for v, s, n, c in rows("SELECT vehicle_id, slug, name, category_id FROM vehicles WHERE vehicle_id IN (14, 15)")) == migration_checks.M006_VEHICLES
    assert dict(rows("SELECT media_id, slug FROM media_assets WHERE media_id BETWEEN 108 AND 114")) == migration_checks.M006_MEDIA
    assert set(rows("SELECT media_id, vehicle_id FROM media_vehicles WHERE media_id >= 108")) == migration_checks.M006_LINKS
    assert dict(rows("SELECT category_id, slug FROM vehicle_categories WHERE category_id IN (5, 6)")) == migration_checks.M006_CATEGORIES
    assert dict(rows("SELECT vehicle_id, slug FROM vehicles WHERE vehicle_id BETWEEN 9 AND 13")) == migration_checks.M006_REWORDED
    assert dict(rows("SELECT slug, summary FROM vehicles WHERE vehicle_id BETWEEN 9 AND 13")) == migration_checks.M006_REWORDED_TEXT


def test_every_check_has_a_migration_file_to_belong_to():
    names = {p.name for p in migrate_db.migration_files()}
    assert set(migration_checks.CHECKS) <= names
