"""Apply non-destructive migrations from database/migrations/ with the migration account.

Usage (from the project root, virtual environment active):
    python -m scripts.migrate_db --plan          # READ-ONLY: what exists now and what would run
    python -m scripts.migrate_db                 # apply to the development database after you type YES
    python -m scripts.migrate_db --test --yes    # apply to the *_test database without a prompt
    python -m scripts.migrate_db --only 006_gate3b_garage.sql --plan   # ONE migration: read-only plan and prerequisite/conflict checks
    python -m scripts.migrate_db --only 006_gate3b_garage.sql          # apply just that file, after you type YES

Migrations here never DROP, DELETE or TRUNCATE, and are safe to run more than once.
This script refuses to run a migration file that contains those words.
"""
import argparse
import re
import sys
from pathlib import Path

import mysql.connector

from app.config import DevelopmentConfig, TestingConfig
from scripts import migration_checks
from scripts.schema_info import ROOT
from scripts.sqlfile import run_sql_file, split_statements

MIGRATIONS = ROOT / "database" / "migrations"
DESTRUCTIVE = re.compile(r"\b(DROP|DELETE|TRUNCATE)\b", re.IGNORECASE)


def migration_files():
    return sorted(MIGRATIONS.glob("*.sql"))


def select_migration(name):
    """The one migration file called `name`. Only a bare file name from the migrations folder is accepted: no path, no folder, no unknown file."""
    available = {path.name: path for path in migration_files()}
    if not name or name != Path(name).name or "/" in name or "\\" in name or name in (".", ".."):
        raise ValueError(f"--only takes a file name from database/migrations/, not a path: {name!r}")
    if name not in available:
        raise ValueError(f"--only: no migration called {name!r}. Available: " + ", ".join(available))
    path = available[name]
    if path.resolve().parent != MIGRATIONS.resolve():      # a link that points out of the folder is refused
        raise ValueError(f"--only: {name} does not resolve to a file inside database/migrations/")
    return path


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
    parser.add_argument("--only", metavar="FILE", help="apply or plan ONE migration, by its exact file name in database/migrations/ (for example 006_gate3b_garage.sql)")
    args = parser.parse_args(argv)

    config = TestingConfig if args.test else DevelopmentConfig
    try:
        files = [select_migration(args.only)] if args.only else migration_files()
    except ValueError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 2
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
        checks = migration_checks.CHECKS.get(files[0].name) if args.only else None
        if checks:
            notes, problems = checks[0](cursor, config.DB_NAME)
            print(f"\nCHECKS before applying {files[0].name} (read-only):")
            for note in notes:
                print("  ok   " + note)
            for problem in problems:
                print("  STOP " + problem)
            if problems:
                print(f"\nBLOCKED: {len(problems)} problem(s) above. Nothing was changed" + ("." if args.plan else " and nothing will be applied."))
                return 1
            print("  All checks passed: no prerequisite is missing and nothing the migration writes belongs to something else.")
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
        if checks:
            verify = mysql.connector.connect(**config.migration_kwargs())
            try:
                print(checks[1](verify.cursor()))
            finally:
                verify.close()
        return 0
    except mysql.connector.Error as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1
    finally:
        connection.close()


if __name__ == "__main__":
    sys.exit(main())
