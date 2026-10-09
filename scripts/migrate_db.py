"""Apply non-destructive migrations from database/migrations/ with the migration account.

Usage (from the project root, virtual environment active):
    python -m scripts.migrate_db --plan          # READ-ONLY: what exists now and what would run
    python -m scripts.migrate_db                 # apply to the development database after you type YES
    python -m scripts.migrate_db --test --yes    # apply to the *_test database without a prompt

Migrations here never DROP, DELETE or TRUNCATE, and are safe to run more than once.
This script refuses to run a migration file that contains those words.
"""
import argparse
import re
import sys
from pathlib import Path

import mysql.connector

from app.config import DevelopmentConfig, TestingConfig
from scripts.schema_info import ROOT
from scripts.sqlfile import run_sql_file, split_statements

MIGRATIONS = ROOT / "database" / "migrations"
DESTRUCTIVE = re.compile(r"\b(DROP|DELETE|TRUNCATE)\b", re.IGNORECASE)


def migration_files():
    return sorted(MIGRATIONS.glob("*.sql"))


def is_destructive(statement):
    """True for DROP / DELETE / TRUNCATE. The foreign-key clause 'ON DELETE CASCADE' is not a delete."""
    return bool(DESTRUCTIVE.search(re.sub(r"\bON\s+DELETE\b", "", statement, flags=re.IGNORECASE)))


def check_non_destructive(path):
    for statement in split_statements(path.read_text(encoding="utf-8")):
        if is_destructive(statement):
            raise ValueError(f"{path.name} contains a destructive statement and will not be run: {statement[:60]}")


def current_state(cursor, database):
    cursor.execute("SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'media_regions'",
                   (database,))
    has_regions_table = bool(cursor.fetchone()[0])
    cursor.execute("SELECT COUNT(*) FROM media_assets")
    media_rows = cursor.fetchone()[0]
    return has_regions_table, media_rows


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--test", action="store_true", help="use the pytest database")
    parser.add_argument("--plan", action="store_true", help="read-only: show the plan and exit")
    parser.add_argument("--yes", action="store_true", help="skip the YES prompt (test database only)")
    args = parser.parse_args(argv)

    config = TestingConfig if args.test else DevelopmentConfig
    files = migration_files()
    try:
        for path in files:
            check_non_destructive(path)
        connection = mysql.connector.connect(**config.migration_kwargs())
    except (ValueError, mysql.connector.Error) as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1

    try:
        cursor = connection.cursor()
        has_table, media_rows = current_state(cursor, config.DB_NAME)
        print(f"Target: database '{config.DB_NAME}' on {config.DB_HOST}:{config.DB_PORT} as '{config.MIGRATE_DB_USER}'")
        print(f"Now: media_regions table {'exists' if has_table else 'MISSING'}; media_assets holds {media_rows} rows (kept, never deleted).")
        print("\nPLAN (nothing is dropped, deleted or truncated):")
        for path in files:
            print(f"  {path.name}")
            for statement in split_statements(path.read_text(encoding="utf-8")):
                print("    - " + " ".join(statement.split())[:100])
        if args.plan:
            print("\n--plan given: nothing was changed.")
            return 0
        if not (args.yes and config.DB_NAME.endswith("_test")):
            if input("\nType YES to apply (anything else cancels): ").strip() != "YES":
                print("Cancelled. Nothing was changed.")
                return 0
        for path in files:
            try:
                count = run_sql_file(connection, path)
                connection.commit()  # DDL commits itself, but the INSERTs need an explicit commit
            except mysql.connector.Error:
                connection.rollback()
                raise
            print(f"Applied {path.name}: {count} statements OK")
        # Verify on a NEW connection, so we report what is really stored and not what this session can see.
        verify = mysql.connector.connect(**config.migration_kwargs())
        try:
            has_table, media_rows = current_state(verify.cursor(), config.DB_NAME)
        finally:
            verify.close()
        print(f"After: media_regions table {'exists' if has_table else 'MISSING'}; media_assets holds {media_rows} rows.")
        return 0
    except mysql.connector.Error as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1
    finally:
        connection.close()


if __name__ == "__main__":
    sys.exit(main())
