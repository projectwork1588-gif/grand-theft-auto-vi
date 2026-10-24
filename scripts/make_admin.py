"""Make an existing TEST-database account an administrator (or take the role away again). TEST DATABASE ONLY.

Usage (from the project root, virtual environment active):
    python -m scripts.make_admin --test <username> --plan          # READ-ONLY: shows the target and the account's current role
    python -m scripts.make_admin --test <username>                 # promote, after you type the username to confirm
    python -m scripts.make_admin --test <username> --revoke        # back to an ordinary user
    python -m scripts.make_admin --test <username> --yes           # promote without the typed confirmation (still the test database only)

Safety rules (this tool fails closed):
  * It only ever works on the test database. `--test` is REQUIRED: without it the tool refuses, and so it does when the testing configuration does not name a
    database ending in _test, and when the server reports a different database. `--yes` skips the typed confirmation and nothing else; it can never point the
    tool at another database.
  * Every refusal above the connection step happens BEFORE any connection is opened (tests/test_make_admin.py proves it by forbidding the connect call).
  * One account, by exact username; one statement, UPDATE users SET role = ... WHERE user_id = ... Passwords and hashes are never read or printed.
  * It uses the migration account, as the other maintenance scripts do. Making a real administrator on the live site is a separate, approved procedure
    that this tool deliberately does not perform.
"""
import argparse
import sys

import mysql.connector

from app.config import TestingConfig
from app.services.accounts import USERNAME_PATTERN

REFUSED = 2


def refuse(message):
    print(f"REFUSED: {message} Nothing was changed.", file=sys.stderr)
    return REFUSED


def main(argv=None):
    parser = argparse.ArgumentParser(description="Make a TEST-database account an administrator (test database only).")
    parser.add_argument("username", help="the account's exact username")
    parser.add_argument("--test", action="store_true", help="REQUIRED: use the test database (the only one this tool works on)")
    parser.add_argument("--revoke", action="store_true", help="remove the administrator role instead of giving it")
    parser.add_argument("--plan", action="store_true", help="read-only: show the target and the current role, change nothing")
    parser.add_argument("--yes", action="store_true", help="skip the typed confirmation (the test database only, as always)")
    args = parser.parse_args(argv)

    # ---- everything that can refuse WITHOUT a connection comes first
    if not args.test:
        return refuse("this tool works on the test database only; pass --test. Making an administrator on any other database is not done by this tool.")
    config = TestingConfig
    if not (config.DB_NAME or "").endswith("_test"):
        return refuse("the testing configuration does not name a database ending in _test.")
    username = (args.username or "").strip().lower()
    if not USERNAME_PATTERN.match(username):
        return refuse("that is not a valid username.")

    print(f"Target: database '{config.DB_NAME}' on {config.DB_HOST}:{config.DB_PORT} as '{config.MIGRATE_DB_USER}'")
    try:
        connection = mysql.connector.connect(**config.migration_kwargs())
    except mysql.connector.Error as error:
        print(f"FAILED: {error}", file=sys.stderr)
        return 1
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT DATABASE()")
        served = cursor.fetchone()[0]
        if not (served or "").endswith("_test"):
            return refuse(f"the server reports database {served!r}, which is not a *_test database.")
        cursor.execute("SELECT user_id, role FROM users WHERE username = %s", (username,))
        row = cursor.fetchone()
        if row is None:
            return refuse(f"there is no account called '{username}' in '{served}'.")
        user_id, role = row
        wanted = "user" if args.revoke else "admin"
        print(f"Account '{username}' currently has the role '{role}'; wanted: '{wanted}'.")
        if args.plan:
            print("--plan given: nothing was changed.")
            return 0
        if role == wanted:
            print("Nothing to do: it already has that role.")
            return 0
        if not args.yes and input(f"Type the username ({username}) to confirm: ").strip() != username:
            print("Confirmation did not match. Nothing was changed.", file=sys.stderr)
            return REFUSED
        cursor.execute("UPDATE users SET role = %s WHERE user_id = %s", (wanted, user_id))
        connection.commit()
        cursor.execute("SELECT role FROM users WHERE user_id = %s", (user_id,))
        print(f"OK: '{username}' now has the role '{cursor.fetchone()[0]}'.")
        return 0
    except mysql.connector.Error as error:
        connection.rollback()
        print(f"FAILED: {error}", file=sys.stderr)
        return 1
    finally:
        connection.close()


if __name__ == "__main__":
    sys.exit(main())
