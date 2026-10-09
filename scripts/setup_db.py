"""One-time MySQL setup: databases, two least-privilege accounts, schema and seed.

Usage (from the project root, virtual environment active):
    python -m scripts.setup_db --plan     # READ-ONLY: show what exists and exactly what would change
    python -m scripts.setup_db            # apply the plan after you type YES
    python -m scripts.setup_db --reset    # also DROP+rebuild existing project tables (you must type RESET)

You are asked for the MySQL ADMIN password with a hidden prompt. It is held in memory for this
run only: never logged, never written to disk, never changed. The admin account itself is never
altered. For automated scratch servers only, MYSQL_ADMIN_USER / MYSQL_ADMIN_PASSWORD may be set.

What this script can touch (and nothing else):
  * Databases  : DB_NAME and TEST_DB_NAME from .env (created only if missing, never dropped).
  * Accounts   : DB_USER (runtime) and MIGRATE_DB_USER (schema changes), host 'localhost'.
                 Existing accounts keep their password. Grants are only ever ADDED.
  * Tables     : only the tables named in database/schema.sql, and only dropped with --reset.
"""
import argparse
import getpass
import os
import re
import sys
from dataclasses import dataclass, field

import mysql.connector

from app.config import DevelopmentConfig, TestingConfig
from scripts.init_db import init_database
from scripts.schema_info import schema_tables, table_inventory

IDENTIFIER = re.compile(r"^[A-Za-z0-9_]{1,32}$")
HOST = "localhost"
# Runtime account: can only read and write rows. Cannot create, alter or drop anything.
APP_PRIVILEGES = ("SELECT", "INSERT", "UPDATE", "DELETE")
# Migration account: used only by scripts.setup_db / scripts.init_db. It cannot pass on privileges, read
# files, administer the server or reach any database outside the two project databases.
# REFERENCES is required by MySQL to create foreign keys (verified: schema load fails without it).
MIGRATE_PRIVILEGES = APP_PRIVILEGES + ("CREATE", "DROP", "ALTER", "INDEX", "REFERENCES")
SYSTEM_SCHEMAS = {"information_schema", "mysql", "performance_schema", "sys"}


@dataclass
class Plan:
    lines: list = field(default_factory=list)
    drops: dict = field(default_factory=dict)   # database -> {table: rows} that WILL be dropped
    loads: list = field(default_factory=list)   # databases that will get schema + seed


def build_plan(state, databases, app_user, migrate_user, reset):
    """Pure function: turn the inspected server state into a human-readable plan."""
    plan = Plan()
    for db in databases:
        info = state["databases"].get(db)
        if info is None:
            plan.lines.append(f"CREATE   database `{db}` (does not exist yet)")
            plan.loads.append(db)
            continue
        tables = info["tables"]
        plan.lines.append(f"KEEP     database `{db}` (already exists, is never dropped)")
        if tables and reset:
            plan.drops[db] = tables
            plan.loads.append(db)
            rows = sum(tables.values())
            plan.lines.append(f"DROP     {len(tables)} project tables in `{db}` holding {rows} rows, then rebuild + seed")
        elif tables:
            plan.lines.append(f"SKIP     `{db}` already has {len(tables)} project tables "
                              f"({sum(tables.values())} rows). Schema and seed NOT applied, data untouched")
            if len(tables) < len(schema_tables()):
                plan.lines.append(f"WARNING  `{db}` has only {len(tables)} of {len(schema_tables())} project tables: "
                                  "probably a failed earlier run. Re-run with --reset to rebuild it")
        else:
            plan.loads.append(db)
            plan.lines.append(f"LOAD     schema + seed into empty `{db}`")
        if info["other_tables"]:
            plan.lines.append(f"NOTE     `{db}` also holds non-project tables {info['other_tables']}: never touched")
    for user, privileges in ((app_user, APP_PRIVILEGES), (migrate_user, MIGRATE_PRIVILEGES)):
        if user in state["users"]:
            plan.lines.append(f"KEEP     account '{user}'@'{HOST}' exists: password NOT changed. Existing grants:")
            plan.lines.extend(f"           {g}" for g in state["users"][user])
        else:
            plan.lines.append(f"CREATE   account '{user}'@'{HOST}' with the password from .env")
        for db in databases:
            plan.lines.append(f"GRANT    {', '.join(privileges)} ON `{db}`.* TO '{user}'@'{HOST}'")
    return plan


def inspect_server(cursor, databases, users):
    cursor.execute("SHOW DATABASES")
    existing = {row[0] for row in cursor.fetchall()}
    state = {"databases": {}, "users": {},
             "other_databases": sorted(existing - SYSTEM_SCHEMAS - set(databases))}
    for db in databases:
        if db in existing:
            counts, others = table_inventory(cursor, db)
            state["databases"][db] = {"tables": counts, "other_tables": others}
    for user in users:
        cursor.execute("SELECT COUNT(*) FROM mysql.user WHERE User = %s AND Host = %s", (user, HOST))
        if cursor.fetchone()[0]:
            cursor.execute(f"SHOW GRANTS FOR %s@'{HOST}'", (user,))
            state["users"][user] = [row[0] for row in cursor.fetchall()]
    return state


def apply_plan(cursor, state, databases, app_user, app_password, migrate_user, migrate_password):
    for db in databases:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db}` CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci")
    for user, password in ((app_user, app_password), (migrate_user, migrate_password)):
        if user not in state["users"]:
            cursor.execute(f"CREATE USER %s@'{HOST}' IDENTIFIED BY %s", (user, password))
    for user, privileges in ((app_user, APP_PRIVILEGES), (migrate_user, MIGRATE_PRIVILEGES)):
        for db in databases:  # identifiers were validated; user is a bound parameter
            cursor.execute(f"GRANT {', '.join(privileges)} ON `{db}`.* TO %s@'{HOST}'", (user,))


def validate_config(dev, test, need_passwords):
    problems = []
    for label, value in (("DB_NAME", dev.DB_NAME), ("TEST_DB_NAME", test.DB_NAME),
                         ("DB_USER", dev.DB_USER), ("MIGRATE_DB_USER", dev.MIGRATE_DB_USER)):
        if not IDENTIFIER.match(value):
            problems.append(f"{label} must be letters, digits or underscore (max 32): {value!r}")
    if not test.DB_NAME.endswith("_test"):
        problems.append("TEST_DB_NAME must end with '_test'.")
    if dev.DB_NAME == test.DB_NAME:
        problems.append("DB_NAME and TEST_DB_NAME must differ.")
    if "root" in (dev.DB_USER.lower(), dev.MIGRATE_DB_USER.lower()):
        problems.append("The application accounts must not be 'root'.")
    if dev.DB_USER == dev.MIGRATE_DB_USER:
        problems.append("DB_USER and MIGRATE_DB_USER must be two different accounts.")
    if need_passwords:
        for label, value in (("DB_PASSWORD", dev.DB_PASSWORD), ("MIGRATE_DB_PASSWORD", dev.MIGRATE_DB_PASSWORD)):
            if not value or value.startswith("change_me"):
                problems.append(f"Set {label} in .env first (python -m scripts.make_env can generate one).")
        if dev.DB_PASSWORD and dev.DB_PASSWORD == dev.MIGRATE_DB_PASSWORD:
            problems.append("Use different passwords for the two accounts.")
    return problems


def admin_connection(host, port):
    user = os.getenv("MYSQL_ADMIN_USER") or input("MySQL admin user [root]: ").strip() or "root"
    password = os.getenv("MYSQL_ADMIN_PASSWORD")
    if password is None:
        password = getpass.getpass(f"Password for MySQL user '{user}' (typing is hidden): ")
    return mysql.connector.connect(host=host, port=port, user=user, password=password), user


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--plan", action="store_true", help="read-only: show the plan and exit")
    parser.add_argument("--reset", action="store_true", help="allow DROP + rebuild of existing project tables")
    parser.add_argument("--yes", action="store_true", help="skip the YES prompt (never skips the RESET prompt)")
    args = parser.parse_args(argv)

    dev, test = DevelopmentConfig, TestingConfig
    problems = validate_config(dev, test, need_passwords=not args.plan)
    if problems:
        print("Configuration problems:\n  - " + "\n  - ".join(problems), file=sys.stderr)
        return 1
    databases = (dev.DB_NAME, test.DB_NAME)

    try:
        admin, admin_user = admin_connection(dev.DB_HOST, dev.DB_PORT)
    except mysql.connector.Error as exc:
        print(f"Could not connect as admin: {exc}", file=sys.stderr)
        return 1

    try:
        cursor = admin.cursor()
        cursor.execute("SELECT VERSION()")
        print(f"\nConnected to MySQL {cursor.fetchone()[0]} at {dev.DB_HOST}:{dev.DB_PORT} as '{admin_user}'.")
        state = inspect_server(cursor, databases, (dev.DB_USER, dev.MIGRATE_DB_USER))
        plan = build_plan(state, databases, dev.DB_USER, dev.MIGRATE_DB_USER, args.reset)
        print("\nOther databases on this server (never touched): "
              + (", ".join(state["other_databases"]) or "none"))
        print("\nPLAN:\n  " + "\n  ".join(plan.lines))
        if args.plan:
            print("\n--plan given: nothing was changed.")
            return 0

        expected = "RESET" if plan.drops else "YES"
        if plan.drops or not args.yes:
            if input(f"\nType {expected} to apply this plan (anything else cancels): ").strip() != expected:
                print("Cancelled. Nothing was changed.")
                return 0

        apply_plan(cursor, state, databases, dev.DB_USER, dev.DB_PASSWORD,
                   dev.MIGRATE_DB_USER, dev.MIGRATE_DB_PASSWORD)
        print("\nDatabases, accounts and grants are in place.")
    except mysql.connector.Error as exc:
        print(f"Admin setup failed: {exc}", file=sys.stderr)
        return 1
    finally:
        admin.close()

    try:
        for config in (dev, test):
            if config.DB_NAME in plan.loads:
                schema_count, seed_count = init_database(config, seed=True, reset=args.reset)
                print(f"  {config.DB_NAME}: {schema_count} schema + {seed_count} seed statements OK")
            else:
                print(f"  {config.DB_NAME}: left untouched")
    except mysql.connector.Error as exc:
        print(f"Schema/seed failed as '{dev.MIGRATE_DB_USER}': {exc}\n"
              "If that account already existed, its password may differ from .env.", file=sys.stderr)
        return 1
    print("Setup complete. Next: python -m pytest   then   python -m flask --app wsgi run")
    return 0


if __name__ == "__main__":
    sys.exit(main())
