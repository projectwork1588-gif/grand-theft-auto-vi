"""The running site's account must be able to read and write rows but never change the schema."""
import mysql.connector
import pytest

from app.config import TestingConfig

DDL_DENIED = 1142   # "<command> denied to user"
FORBIDDEN_WORDS = ("ALL PRIVILEGES", "GRANT OPTION", "CREATE", "DROP", "ALTER", "INDEX", "SUPER", "FILE", "PROCESS")


def test_runtime_account_has_only_row_level_grants(cur):
    cur.execute("SHOW GRANTS")
    grants = [list(row.values())[0] for row in cur.fetchall()]
    for grant in grants:
        head = grant.split(" ON ")[0]
        assert not any(word in head for word in FORBIDDEN_WORDS), grant
        if "ON *.*" not in grant:  # anything beyond USAGE must be limited to the project databases
            assert f"`{TestingConfig.DB_NAME}`.*" in grant or "`gta6_vi`.*" in grant, grant


@pytest.mark.parametrize("sql", [
    "DROP TABLE characters",
    "CREATE TABLE sneaky (id INT)",
    "ALTER TABLE characters ADD COLUMN sneaky INT",
    "TRUNCATE TABLE characters",
    "CREATE USER 'evil'@'localhost' IDENTIFIED BY 'x'",
    "DROP DATABASE " + TestingConfig.DB_NAME,
])
def test_runtime_account_cannot_change_schema_or_accounts(cur, sql):
    with pytest.raises(mysql.connector.Error) as info:
        cur.execute(sql)
    assert info.value.errno in (DDL_DENIED, 1044, 1227), info.value  # denied, not "syntax" or "missing"


def test_runtime_account_cannot_read_the_mysql_system_schema(cur):
    with pytest.raises(mysql.connector.Error):
        cur.execute("SELECT * FROM mysql.user")


def test_runtime_account_can_still_read_and_write_rows(cur):
    cur.execute("SELECT COUNT(*) AS n FROM characters")
    assert cur.fetchone()["n"] > 0
    cur.execute("INSERT INTO users (username, email, password_hash) VALUES ('priv', 'priv@example.test', 'x')")
    cur.execute("DELETE FROM users WHERE username = 'priv'")


def test_migration_account_is_a_different_non_root_user():
    assert TestingConfig.MIGRATE_DB_USER != TestingConfig.DB_USER
    assert TestingConfig.MIGRATE_DB_USER.lower() != "root"
    kwargs = TestingConfig.migration_kwargs()
    assert kwargs["user"] == TestingConfig.MIGRATE_DB_USER and kwargs["password"] == TestingConfig.MIGRATE_DB_PASSWORD


def test_migration_account_can_alter_schema_only_in_project_databases():
    connection = mysql.connector.connect(**TestingConfig.migration_kwargs())
    cursor = connection.cursor()
    try:
        cursor.execute("CREATE TABLE priv_probe (id INT)")
        cursor.execute("DROP TABLE priv_probe")
        with pytest.raises(mysql.connector.Error):
            cursor.execute("CREATE DATABASE valkyrie_should_not_exist")
        with pytest.raises(mysql.connector.Error):
            cursor.execute("CREATE USER 'evil'@'localhost' IDENTIFIED BY 'x'")
    finally:
        cursor.close()
        connection.close()
