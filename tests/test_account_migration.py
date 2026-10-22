"""Migration 010 (users.email may be NULL), exercised on the *_test database only.

The production database is never touched: every connection here is opened by tests.account_helpers.test_connection(), which aborts unless the server
reports a *_test database, and the migration runner is always called with --test."""
import re
from pathlib import Path

import mysql.connector
import pytest

from app.config import TestingConfig
from scripts import migrate_db
from tests import account_helpers as h

ROOT = Path(__file__).resolve().parent.parent
MIGRATION = "010_account_email_optional.sql"
EMAIL_SQL = ("SELECT is_nullable AS n, column_type AS t FROM information_schema.columns "
             "WHERE table_schema = DATABASE() AND table_name = 'users' AND column_name = 'email'")

pytestmark = pytest.mark.usefixtures("clean_accounts")


def as_migrator(sql):
    """Run one statement as the schema account, on the test database only (proved first)."""
    assert TestingConfig.DB_NAME.endswith("_test")
    connection = mysql.connector.connect(**TestingConfig.migration_kwargs())
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT DATABASE()")
        assert cursor.fetchone()[0].endswith("_test"), "refusing: not a test database"
        cursor.execute(sql)
        connection.commit()
    finally:
        connection.close()


def test_the_migration_is_one_non_destructive_statement():
    path = ROOT / "database" / "migrations" / MIGRATION
    migrate_db.check_non_destructive(path)
    statements = migrate_db.split_statements(path.read_text(encoding="utf-8"))
    assert statements == ["ALTER TABLE users MODIFY email VARCHAR(254) NULL"]
    assert path in migrate_db.migration_files()


def test_schema_sql_matches_the_migration():
    schema = (ROOT / "database" / "schema.sql").read_text(encoding="utf-8")
    users = re.search(r"CREATE TABLE users \((.*?)\) ENGINE", schema, re.S).group(1)
    assert re.search(r"email\s+VARCHAR\(254\)\s+NULL,", users) and "uq_users_email" in users
    assert "NOT NULL" in re.search(r"username\s+[^,]*,", users).group(0) and "password_hash  VARCHAR(255)  NOT NULL" in users


def test_a_freshly_built_test_database_has_a_nullable_unique_email():
    row = h.rows(EMAIL_SQL)[0]
    assert row["n"] == "YES" and row["t"] == "varchar(254)"
    indexes = {r["Key_name"]: r["Non_unique"] for r in h.rows("SHOW INDEX FROM users")}
    assert indexes["uq_users_email"] == 0 and indexes["uq_users_username"] == 0


def test_the_plan_for_the_migration_changes_nothing(app, capsys):
    before = h.rows(EMAIL_SQL)
    assert migrate_db.main(["--test", "--only", MIGRATION, "--plan"]) == 0
    out = capsys.readouterr().out
    assert MIGRATION in out and "ALTER TABLE users MODIFY email" in out and "--plan given: nothing was changed" in out and "009_media_screening.sql" not in out
    assert h.rows(EMAIL_SQL) == before


def test_applying_it_to_a_database_that_still_requires_an_email_relaxes_only_that_and_is_safe_to_repeat(app, capsys):
    assert h.rows("SELECT COUNT(*) AS n FROM users")[0]["n"] == 0, "the migration test expects an empty users table"
    columns_before = h.rows("SELECT column_name, column_type, is_nullable, column_default FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = 'users' AND column_name <> 'email' ORDER BY ordinal_position")
    try:
        as_migrator("ALTER TABLE users MODIFY email VARCHAR(254) NOT NULL")                  # put the test database back in its pre-010 state
        assert h.rows(EMAIL_SQL)[0]["n"] == "NO"
        with pytest.raises(mysql.connector.Error):                                             # before 010 an account without an email cannot exist
            h.execute("INSERT INTO users (username, password_hash) VALUES (%s, 'x')", ("tt_pre010",))
        assert migrate_db.main(["--test", "--only", MIGRATION, "--yes"]) == 0
        assert f"Applied {MIGRATION}: 1 statements OK" in capsys.readouterr().out
        assert h.rows(EMAIL_SQL)[0]["n"] == "YES"
        assert migrate_db.main(["--test", "--only", MIGRATION, "--yes"]) == 0                # and again: nothing changes
        assert h.rows(EMAIL_SQL)[0] == {"n": "YES", "t": "varchar(254)"}
    finally:
        as_migrator("ALTER TABLE users MODIFY email VARCHAR(254) NULL")
    columns_after = h.rows("SELECT column_name, column_type, is_nullable, column_default FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = 'users' AND column_name <> 'email' ORDER BY ordinal_position")
    assert columns_after == columns_before


def test_many_accounts_may_have_no_email_but_a_given_email_is_still_unique():
    h.execute("INSERT INTO users (username, password_hash) VALUES ('tt_noemail1', 'x'), ('tt_noemail2', 'x')")
    assert h.rows("SELECT COUNT(*) AS n FROM users WHERE username LIKE 'tt\\_noemail%' AND email IS NULL")[0]["n"] == 2
    h.execute("INSERT INTO users (username, email, password_hash) VALUES ('tt_withemail1', 'dup@example.test', 'x')")
    with pytest.raises(mysql.connector.IntegrityError) as duplicate:
        h.execute("INSERT INTO users (username, email, password_hash) VALUES ('tt_withemail2', 'dup@example.test', 'x')")
    assert duplicate.value.errno == 1062


def test_the_role_column_still_defaults_to_user_and_is_an_enum():
    h.execute("INSERT INTO users (username, password_hash) VALUES ('tt_default_role', 'x')")
    assert h.rows("SELECT role FROM users WHERE username = 'tt_default_role'")[0]["role"] == "user"
    with pytest.raises(mysql.connector.Error):
        h.execute("INSERT INTO users (username, password_hash, role) VALUES ('tt_bad_role', 'x', 'superuser')")


def test_the_favourite_tables_keep_their_keys_and_cascades():
    for kind, column in (("characters", "character_id"), ("vehicles", "vehicle_id"), ("locations", "location_id"), ("missions", "mission_id")):
        table = f"favourite_{kind}"
        primary = [r["Column_name"] for r in h.rows(f"SHOW INDEX FROM {table} WHERE Key_name = 'PRIMARY' ")]
        assert primary == ["user_id", column]
        rules = {r["referenced"]: (r["on_delete"], r["on_update"]) for r in h.rows(
            "SELECT k.referenced_table_name AS referenced, r.delete_rule AS on_delete, r.update_rule AS on_update FROM information_schema.key_column_usage k "
            "JOIN information_schema.referential_constraints r ON r.constraint_schema = k.table_schema AND r.constraint_name = k.constraint_name AND r.table_name = k.table_name "
            "WHERE k.table_schema = DATABASE() AND k.table_name = %s AND k.referenced_table_name IS NOT NULL", (table,))}
        assert rules == {"users": ("CASCADE", "CASCADE"), kind: ("CASCADE", "CASCADE")}


# ------------------------------------------------------------------ Phase 2C: the runner and the prerequisite checks
import builtins

from scripts import migration_checks

ALL_OTHER_FILES = [p.name for p in migrate_db.migration_files() if p.name != MIGRATION]


class FakeCursor:
    """Scripted answers for check_010, so the blocking cases can be tested without touching any database."""

    def __init__(self, tables=1, column=("varchar(254)", "NO"), unique=1, users=0):
        self.tables, self.column, self.unique, self.users, self.sql = tables, column, unique, users, ""

    def execute(self, sql, params=()):
        self.sql = sql

    def fetchone(self):
        if "information_schema.TABLES" in self.sql:
            return (self.tables,)
        if "information_schema.COLUMNS" in self.sql:
            return self.column
        if "information_schema.STATISTICS" in self.sql:
            return (self.unique,)
        return (self.users,)


def test_010_has_a_prerequisite_check_registered():
    assert migration_checks.CHECKS[MIGRATION] == (migration_checks.check_010, migration_checks.after_010)


def test_check_010_passes_on_the_schema_as_defined_and_reports_the_state():
    notes, problems = migration_checks.check_010(FakeCursor(), "any_test")
    assert problems == [] and any("NOT NULL now" in n for n in notes) and any("present, it stays" in n for n in notes)
    notes, problems = migration_checks.check_010(FakeCursor(column=("varchar(254)", "YES"), users=7), "any_test")
    assert problems == [] and any("already nullable" in n for n in notes) and any("7 account(s)" in n for n in notes)
    assert any("rollback note" in n for n in notes)


@pytest.mark.parametrize("cursor, fragment", [
    (FakeCursor(tables=0), "table 'users' does not exist"),
    (FakeCursor(column=None), "no column 'email'"),
    (FakeCursor(column=("varchar(100)", "NO")), "would change its type"),
    (FakeCursor(column=("text", "YES")), "would change its type"),
])
def test_check_010_blocks_when_a_prerequisite_is_missing_or_the_column_is_different(cursor, fragment):
    notes, problems = migration_checks.check_010(cursor, "any_test")
    assert problems and fragment in problems[0]


def test_check_010_on_the_real_test_database_finds_nothing_wrong():
    assert TestingConfig.DB_NAME.endswith("_test")
    connection = mysql.connector.connect(**TestingConfig.migration_kwargs())
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT DATABASE()")
        assert cursor.fetchone()[0].endswith("_test")
        notes, problems = migration_checks.check_010(cursor, TestingConfig.DB_NAME)
        assert problems == [] and any("unique index uq_users_email: present" in n for n in notes)
        assert "OK" in migration_checks.after_010(cursor)
    finally:
        connection.close()


def test_the_plan_shows_the_checks_and_names_only_the_requested_migration(app, capsys):
    assert migrate_db.main(["--test", "--only", MIGRATION, "--plan"]) == 0
    out = capsys.readouterr().out
    assert f"Selected: exactly one migration, {MIGRATION}" in out and "CHECKS before applying" in out and "All checks passed" in out
    assert not any(name in out for name in ALL_OTHER_FILES)


@pytest.mark.parametrize("name", ["010", "010_account_email_optional", "010_ACCOUNT_EMAIL_OPTIONAL.SQL", "../seed.sql", "database/migrations/010_account_email_optional.sql",
                                  "010_account_email_optional.sql ", "*.sql", "", "010_account_email_optional.sql/../009_media_screening.sql"])
def test_only_accepts_an_exact_file_name_and_nothing_else_is_opened(monkeypatch, capsys, name):
    def no_connection(**kwargs):
        raise AssertionError("the runner must not connect when the name is refused")
    monkeypatch.setattr(mysql.connector, "connect", no_connection)
    assert migrate_db.main(["--test", "--only", name, "--plan"]) == 2
    assert "FAILED" in capsys.readouterr().err


def test_running_every_migration_is_spelled_out_and_needs_the_longer_phrase(app, capsys, monkeypatch):
    prompts = []

    def answer(prompt=""):
        prompts.append(prompt)
        return "YES"                                                         # the short phrase is not enough for the all-files run
    monkeypatch.setattr(builtins, "input", answer)
    assert migrate_db.main(["--test"]) == 0
    out = capsys.readouterr().out
    assert f"Selected: ALL {len(migrate_db.migration_files())} migrations" in out and "no migration history" in out
    assert "Cancelled. Nothing was changed." in out and "Applied" not in out
    assert prompts and "YES ALL" in prompts[0] and "gta6_vi_test" in prompts[0]


def test_a_targeted_run_is_not_confirmed_by_the_all_files_phrase(app, capsys, monkeypatch):
    monkeypatch.setattr(builtins, "input", lambda prompt="": "YES ALL")
    before = h.rows(EMAIL_SQL)
    assert migrate_db.main(["--test", "--only", MIGRATION]) == 0
    out = capsys.readouterr().out
    assert "Cancelled. Nothing was changed." in out and "Applied" not in out
    assert h.rows(EMAIL_SQL) == before


def test_the_default_plan_warns_that_everything_would_run_again(app, capsys):
    assert migrate_db.main(["--test", "--plan"]) == 0
    out = capsys.readouterr().out
    assert "no migration history" in out and "--only <file>" in out and "--plan given: nothing was changed" in out
    assert "CHECKS before applying" not in out
