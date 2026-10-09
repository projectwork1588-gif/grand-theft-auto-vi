"""Create the tables and load the seed data using the MIGRATION account.

Usage (from the project root, virtual environment active):
    python -m scripts.init_db                   # first-time load into an EMPTY development database
    python -m scripts.init_db --reset           # DROP and rebuild the project tables (asks you to confirm)
    python -m scripts.init_db --test --reset --yes    # rebuild the *_test database without a prompt

Safety rules:
  * Without --reset the script refuses to touch a database that already has project tables.
  * Only the tables named in database/schema.sql are ever dropped. Other tables are never touched.
  * --yes (skip the typed confirmation) is honoured ONLY for databases whose name ends in _test.
"""
import argparse
import sys

import mysql.connector

from app.config import DevelopmentConfig, TestingConfig
from scripts.schema_info import SCHEMA, SEED, table_inventory
from scripts.sqlfile import run_sql_file


class DatabaseNotEmpty(RuntimeError):
    def __init__(self, database, tables):
        super().__init__(f"Database '{database}' already contains project tables: {', '.join(tables)}")
        self.database = database
        self.tables = tables


def init_database(config, seed=True, reset=False):
    """Build the schema (and optionally the seed). Returns (schema_statements, seed_statements).

    Raises DatabaseNotEmpty if project tables already exist and reset is False.
    """
    connection = mysql.connector.connect(**config.migration_kwargs())
    try:
        counts, _others = table_inventory(connection.cursor(), config.DB_NAME)
        if counts and not reset:
            raise DatabaseNotEmpty(config.DB_NAME, sorted(counts))
        schema_count = run_sql_file(connection, SCHEMA)
        seed_count = 0
        if seed:
            connection.start_transaction()
            try:
                seed_count = run_sql_file(connection, SEED)
                connection.commit()
            except Exception:
                connection.rollback()  # all-or-nothing seed
                raise
        return schema_count, seed_count
    finally:
        connection.close()


def _confirm_reset(config, counts):
    rows = sum(counts.values())
    print(f"\nThis will DROP {len(counts)} tables in '{config.DB_NAME}' holding {rows} rows:")
    for name, n in counts.items():
        print(f"  {name}: {n} rows")
    typed = input(f"Type the database name ({config.DB_NAME}) to confirm: ").strip()
    return typed == config.DB_NAME


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--test", action="store_true", help="use the pytest database")
    parser.add_argument("--no-seed", action="store_true", help="create tables only")
    parser.add_argument("--reset", action="store_true", help="drop and rebuild existing project tables")
    parser.add_argument("--yes", action="store_true", help="skip confirmation (test databases only)")
    args = parser.parse_args(argv)

    config = TestingConfig if args.test else DevelopmentConfig
    print(f"Target: database '{config.DB_NAME}' on {config.DB_HOST}:{config.DB_PORT} as '{config.MIGRATE_DB_USER}'")
    try:
        probe = mysql.connector.connect(**config.migration_kwargs())
        counts, _ = table_inventory(probe.cursor(), config.DB_NAME)
        probe.close()
        if counts and not args.reset:
            print(f"REFUSED: it already has {len(counts)} project tables. Nothing was changed.\n"
                  "Re-run with --reset if you really want to drop and rebuild them.", file=sys.stderr)
            return 2
        if counts and args.reset:
            skip_prompt = args.yes and config.DB_NAME.endswith("_test")
            if not skip_prompt and not _confirm_reset(config, counts):
                print("Confirmation did not match. Nothing was changed.", file=sys.stderr)
                return 2
        schema_count, seed_count = init_database(config, seed=not args.no_seed, reset=args.reset)
    except mysql.connector.Error as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1
    print(f"OK: ran {schema_count} schema statements and {seed_count} seed statements.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
