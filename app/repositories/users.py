"""Accounts: every statement is parameterised, and every write goes through db.transaction() (the connection is not in autocommit mode, so an
uncommitted write would be discarded when the connection returns to the pool)."""
from ..db import query_one, transaction


def get_by_username(username):
    """The username is already normalised (lower case); the column's collation would match it case-insensitively anyway."""
    return query_one("SELECT user_id, username, password_hash, role FROM users WHERE username = %s", (username,))


def get_by_id(user_id):
    return query_one("SELECT user_id, username, password_hash, role FROM users WHERE user_id = %s", (user_id,))


def create(username, password_hash):
    """Insert a new account and return its id. `role` is never passed: the column's default ('user') applies, so sign-up cannot create an admin.
    A taken username raises mysql.connector.errors.IntegrityError (errno 1062) from the UNIQUE index, which is what makes two simultaneous sign-ups safe."""
    with transaction() as cursor:
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", (username, password_hash))
        return cursor.lastrowid


def update_password(user_id, password_hash):
    """Replace the stored hash. Returns the number of rows changed (1)."""
    with transaction() as cursor:
        cursor.execute("UPDATE users SET password_hash = %s WHERE user_id = %s", (password_hash, user_id))
        return cursor.rowcount
