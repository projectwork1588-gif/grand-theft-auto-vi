"""Helpers for the account and favourites tests. Every database touch goes through test_connection(), which refuses to continue unless the
connection it opened is really on a *_test database."""
import re
import uuid

import mysql.connector

from app.config import TestingConfig
from app.db import query_one

PASSWORD = "correct horse battery staple"
OTHER_PASSWORD = "a different long passphrase"
TOKEN = re.compile(r'name="csrf_token" value="([^"]+)"')


def test_connection():
    """A connection to the test database, after proving that it is one (the name the server reports ends in _test). Aborts otherwise."""
    assert TestingConfig.DB_NAME.endswith("_test"), "refusing: the testing config does not name a *_test database"
    connection = mysql.connector.connect(**TestingConfig.db_kwargs())
    cursor = connection.cursor()
    cursor.execute("SELECT DATABASE()")
    name = cursor.fetchone()[0]
    cursor.close()
    if not (name or "").endswith("_test"):
        connection.close()
        raise AssertionError(f"refusing: connected to {name!r}, which is not a *_test database")
    return connection


test_connection.__test__ = False          # a helper, not a test (its name starts with "test")


def rows(sql, params=()):
    connection = test_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(sql, params)
        return cursor.fetchall()
    finally:
        connection.close()


def execute(sql, params=()):
    """A write on the test database (committed). Only for setting up or checking test state."""
    connection = test_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(sql, params)
        connection.commit()
        return cursor.lastrowid
    finally:
        connection.close()


def wipe_test_accounts(app):
    assert app.config["DB_CONFIG"].DB_NAME.endswith("_test")
    with app.app_context():
        assert query_one("SELECT DATABASE() AS d")["d"].endswith("_test"), "the app's own pool is not on a *_test database"
    execute("DELETE FROM users WHERE username LIKE %s", ("tt\\_%",))
    app.extensions["login_throttle"].clear()


def new_username():
    return "tt_" + uuid.uuid4().hex[:10]


def csrf_from(html):
    found = TOKEN.search(html)
    assert found, "no csrf_token field in the page"
    return found.group(1)


def token(client, path="/login"):
    return csrf_from(client.get(path).get_data(as_text=True))


def post(client, path, data=None, *, with_token=True, token_from="/login", **kwargs):
    data = dict(data or {})
    if with_token and "csrf_token" not in data:
        data["csrf_token"] = token(client, token_from)
    return client.post(path, data=data, **kwargs)


def register(client, username=None, password=PASSWORD, confirm=None, **extra):
    username = new_username() if username is None else username
    data = {"username": username, "password": password, "password_confirm": password if confirm is None else confirm, **extra}
    response = post(client, "/register", data, token_from="/register")
    response.username = username
    return response


def login(client, username, password=PASSWORD):
    return post(client, "/login", {"username": username, "password": password})


def logout(client):
    return post(client, "/logout", {}, token_from="/account/favourites")


def signed_in_client(app, username=None, password=PASSWORD):
    client = app.test_client()
    response = register(client, username, password)
    assert response.status_code == 303, response.get_data(as_text=True)[:300]
    return client, response.username


def user_row(username):
    found = rows("SELECT user_id, username, email, password_hash, role FROM users WHERE username = %s", (username,))
    return found[0] if found else None


def favourites_of(username):
    out = {}
    for kind, table, column in (("characters", "favourite_characters", "character_id"), ("vehicles", "favourite_vehicles", "vehicle_id"),
                                ("locations", "favourite_locations", "location_id"), ("missions", "favourite_missions", "mission_id")):
        out[kind] = {r[column] for r in rows(f"SELECT f.{column} FROM {table} f JOIN users u ON u.user_id = f.user_id WHERE u.username = %s", (username,))}
    return out


def count_favourites(username):
    return sum(len(v) for v in favourites_of(username).values())
