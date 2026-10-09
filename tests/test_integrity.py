"""Proves MySQL itself enforces the rules (keys, uniqueness, NOT NULL, CHECK, cascades).

Every test runs in a transaction that is rolled back, so the seed data is never changed.
"""
import mysql.connector
import pytest

DUP_ENTRY, CHECK_FAIL = 1062, 3819
# MySQL reports foreign-key failures as 1452/1451 or the older 1216/1217 depending on the build.
FK_CHILD = (1452, 1216)   # child row points at a missing parent
FK_PARENT = (1451, 1217)  # parent row is still referenced by a child


def errno_of(cur, sql, params=()):
    with pytest.raises(mysql.connector.Error) as info:
        cur.execute(sql, params)
    return info.value.errno


def test_foreign_key_rejects_unknown_home_location(cur):
    sql = ("INSERT INTO characters (slug, full_name, role_title, summary, biography, home_location_id, content_status) "
           "VALUES ('ghost', 'Ghost', 'Test', 's', 'b', 99999, 'demo')")
    assert errno_of(cur, sql) in FK_CHILD


def test_unique_slug_is_enforced(cur):
    sql = ("INSERT INTO characters (slug, full_name, role_title, summary, biography, content_status) "
           "VALUES ('jason-duval', 'Another Jason', 'Test', 's', 'b', 'demo')")
    assert errno_of(cur, sql) == DUP_ENTRY


def test_unique_location_name_within_region(cur):
    sql = ("INSERT INTO locations (region_id, slug, name, location_type, summary, description, content_status) "
           "VALUES (1, 'dup-pier', 'Sunset Pier Boardwalk', 'landmark', 's', 'd', 'demo')")
    assert errno_of(cur, sql) == DUP_ENTRY


def test_cannot_delete_region_that_still_has_locations(cur):
    assert errno_of(cur, "DELETE FROM regions WHERE region_id = 1") in FK_PARENT


def test_cannot_delete_vehicle_category_in_use(cur):
    assert errno_of(cur, "DELETE FROM vehicle_categories WHERE category_id = 1") in FK_PARENT


def test_composite_primary_key_blocks_duplicate_pair(cur):
    sql = "INSERT INTO mission_characters (mission_id, character_id, role_in_mission) VALUES (1, 8, 'again')"
    assert errno_of(cur, sql) == DUP_ENTRY


def test_character_cannot_relate_to_themselves(cur):
    sql = ("INSERT INTO character_relationships (from_character_id, to_character_id, relationship_type, "
           "description, content_status) VALUES (8, 8, 'ally', 'self', 'demo')")
    assert errno_of(cur, sql) == CHECK_FAIL


def test_official_record_requires_source_url(cur):
    sql = ("INSERT INTO characters (slug, full_name, role_title, summary, biography, content_status) "
           "VALUES ('unsourced', 'Unsourced', 'Test', 's', 'b', 'official')")
    assert errno_of(cur, sql) == CHECK_FAIL


def test_not_null_is_enforced(cur):
    sql = "INSERT INTO regions (slug, summary, description, content_status) VALUES ('no-name', 's', 'd', 'fan')"
    assert errno_of(cur, sql) in (1048, 1364)


def test_invalid_enum_value_is_rejected_in_strict_mode(cur):
    sql = ("INSERT INTO regions (slug, name, summary, description, content_status) "
           "VALUES ('bad', 'Bad', 's', 'd', 'confirmed-by-me')")
    assert errno_of(cur, sql) == 1265


def test_media_row_needs_some_location(cur):
    sql = ("INSERT INTO media_assets (slug, title, media_type, intended_use, attribution, usage_status) "
           "VALUES ('nowhere', 'Nowhere', 'artwork', 'x', 'x', 'original')")
    assert errno_of(cur, sql) == CHECK_FAIL


def test_deleting_character_cascades_to_junction_rows(cur):
    cur.execute("SELECT COUNT(*) AS n FROM mission_characters WHERE character_id = 8")
    assert cur.fetchone()["n"] > 0
    cur.execute("DELETE FROM characters WHERE character_id = 8")
    cur.execute("SELECT COUNT(*) AS n FROM mission_characters WHERE character_id = 8")
    assert cur.fetchone()["n"] == 0
    cur.execute("SELECT COUNT(*) AS n FROM character_relationships WHERE from_character_id = 8 OR to_character_id = 8")
    assert cur.fetchone()["n"] == 0


def test_deleting_location_sets_character_home_to_null(cur):
    cur.execute("SELECT home_location_id FROM characters WHERE character_id = 8")
    assert cur.fetchone()["home_location_id"] == 3
    cur.execute("DELETE FROM locations WHERE location_id = 3")
    cur.execute("SELECT home_location_id FROM characters WHERE character_id = 8")
    assert cur.fetchone()["home_location_id"] is None


def test_favourite_requires_existing_user(cur):
    sql = "INSERT INTO favourite_characters (user_id, character_id) VALUES (99999, 1)"
    assert errno_of(cur, sql) in FK_CHILD


def test_favourite_duplicate_blocked_and_deleted_with_user(cur):
    cur.execute("INSERT INTO users (username, email, password_hash) VALUES ('fan1', 'fan1@example.test', 'x')")
    user_id = cur.lastrowid
    cur.execute("INSERT INTO favourite_characters (user_id, character_id) VALUES (%s, 1)", (user_id,))
    assert errno_of(cur, "INSERT INTO favourite_characters (user_id, character_id) VALUES (%s, 1)", (user_id,)) == DUP_ENTRY
    cur.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
    cur.execute("SELECT COUNT(*) AS n FROM favourite_characters WHERE user_id = %s", (user_id,))
    assert cur.fetchone()["n"] == 0


def test_user_email_and_username_are_unique(cur):
    cur.execute("INSERT INTO users (username, email, password_hash) VALUES ('u1', 'u1@example.test', 'x')")
    assert errno_of(cur, "INSERT INTO users (username, email, password_hash) VALUES ('u2', 'u1@example.test', 'x')") == DUP_ENTRY
    assert errno_of(cur, "INSERT INTO users (username, email, password_hash) VALUES ('u1', 'u2@example.test', 'x')") == DUP_ENTRY
