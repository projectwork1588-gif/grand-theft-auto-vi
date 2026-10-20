"""Connectivity and structure checks against the real MySQL test database."""
import pytest

from app.config import TestingConfig
from app.db import get_db, transaction

EXPECTED_TABLES = {
    "users", "regions", "locations", "characters", "character_relationships", "character_regions",
    "vehicle_categories", "vehicles", "missions", "mission_characters", "mission_vehicles",
    "mission_locations", "favourite_characters", "favourite_vehicles", "favourite_missions",
    "favourite_locations", "media_assets", "media_characters", "media_locations", "media_regions", "media_vehicles",
    "radio_stations", "station_preview_tracks", "music_releases", "music_tracks",      # Music (migration 008)
    "media_collections", "media_collection_items",      # Media / The Screening (migration 009)
}


def test_can_connect_and_select(cur):
    cur.execute("SELECT 1 AS ok")
    assert cur.fetchone()["ok"] == 1


def test_mysql_version_is_8_or_newer(cur):
    cur.execute("SELECT VERSION() AS v")
    assert int(cur.fetchone()["v"].split(".")[0]) >= 8


def test_connected_to_test_database_with_non_root_user(cur):
    cur.execute("SELECT DATABASE() AS db, CURRENT_USER() AS u")
    row = cur.fetchone()
    assert row["db"] == TestingConfig.DB_NAME
    assert not row["u"].startswith("root@")


def test_all_expected_tables_exist(cur):
    cur.execute("SELECT TABLE_NAME AS t FROM information_schema.TABLES WHERE TABLE_SCHEMA = DATABASE()")
    assert {r["t"] for r in cur.fetchall()} == EXPECTED_TABLES


def test_every_table_is_innodb_utf8mb4(cur):
    cur.execute(
        "SELECT TABLE_NAME AS t, ENGINE AS e, TABLE_COLLATION AS c "
        "FROM information_schema.TABLES WHERE TABLE_SCHEMA = DATABASE()"
    )
    for row in cur.fetchall():
        assert row["e"] == "InnoDB", row
        assert row["c"].startswith("utf8mb4"), row


def test_foreign_keys_are_defined(cur):
    cur.execute(
        "SELECT COUNT(*) AS n FROM information_schema.REFERENTIAL_CONSTRAINTS "
        "WHERE CONSTRAINT_SCHEMA = DATABASE()"
    )
    assert cur.fetchone()["n"] == 34  # 23 from Phase 1, media_regions (2), media_vehicles (2), character_regions (2, Gate 3A), station_preview_tracks (1), music_tracks (1) and media_collection_items (3)


def test_composite_primary_keys_exist(cur):
    cur.execute(
        "SELECT TABLE_NAME AS t FROM information_schema.KEY_COLUMN_USAGE "
        "WHERE TABLE_SCHEMA = DATABASE() AND CONSTRAINT_NAME = 'PRIMARY' "
        "GROUP BY TABLE_NAME HAVING COUNT(*) > 1"
    )
    assert len(cur.fetchall()) == 15  # 10 from Phase 1, media_regions, media_vehicles, character_regions, station_preview_tracks and media_collection_items


def test_pool_connection_from_flask_app(app_context):
    cursor = get_db().cursor()
    cursor.execute("SELECT DATABASE()")
    assert cursor.fetchone()[0] == TestingConfig.DB_NAME
    cursor.close()


def test_transaction_helper_rolls_back_on_error(app_context):
    with pytest.raises(RuntimeError):
        with transaction() as cursor:
            cursor.execute(
                "INSERT INTO users (username, email, password_hash) VALUES ('tx_user', 'tx@example.test', 'x')"
            )
            raise RuntimeError("boom")
    cursor = get_db().cursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'tx_user'")
    assert cursor.fetchone()[0] == 0
    cursor.close()


def test_transaction_helper_commits_on_success(app_context):
    with transaction() as cursor:
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES ('tx_ok', 'tx_ok@example.test', 'x')"
        )
    cursor = get_db().cursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'tx_ok'")
    assert cursor.fetchone()[0] == 1
    cursor.execute("DELETE FROM users WHERE username = 'tx_ok'")  # clean up the committed row
    get_db().commit()
    cursor.close()
