"""The request's database connection goes back to the pool BEFORE a password is hashed or verified (a hash takes about 170 ms and the pool has only a few
connections that never wait). The proof is deterministic: the test application gets a pool of ONE connection, and the hashing functions are wrapped so that, at the
moment each one runs, they try to take a connection from that pool. If the request were still holding its own, that would fail. Real rows go to the *_test database only
(tests/account_helpers.py proves the name first)."""
import ast
from pathlib import Path

import mysql.connector
import pytest
from flask import g
from werkzeug.security import check_password_hash

from app import config, create_app
from app.db import TransactionError, get_db, query_one, release_connection, transaction
from app.repositories import users as users_repo
from app.services import accounts
from tests import account_helpers as h

pytestmark = pytest.mark.usefixtures("clean_accounts")
ROOT = Path(__file__).resolve().parent.parent
WRONG = "wrong password !!"


@pytest.fixture()
def one_connection_app(monkeypatch):
    """A test application whose pool holds exactly one connection."""
    monkeypatch.setattr(config.TestingConfig, "DB_POOL_SIZE", 1)
    application = create_app("testing")
    assert application.config["DB_POOL_SIZE"] == 1
    return application


def pool_is_free(application):
    """True when a connection can be taken from the application's pool right now (it is handed straight back). No pool yet means nothing is held."""
    pool = application.extensions.get("db_pool")
    if pool is None:
        return True
    try:
        connection = pool.get_connection()
    except mysql.connector.errors.PoolError:
        return False
    connection.close()
    return True


class Spy:
    """Wraps accounts.verify_password / accounts.hash_password. Each call records (name, was a connection free at that moment, was it the dummy hash)."""

    def __init__(self, application, monkeypatch, names=("verify_password", "hash_password")):
        self.application, self.calls = application, []
        for name in names:
            real = getattr(accounts, name)

            def wrapper(*args, _real=real, _name=name, **kwargs):
                self.calls.append((_name, pool_is_free(self.application), bool(args) and args[0] == accounts._dummy_hash))
                return _real(*args, **kwargs)
            monkeypatch.setattr(accounts, name, wrapper)

    def free(self, name=None):
        return [free for n, free, _ in self.calls if name in (None, n)]


def an_account(app):
    return h.signed_in_client(app)[1]


# ------------------------------------------------------------------ sign in
def test_a_correct_login_verifies_the_password_with_the_connection_already_returned(app, one_connection_app, monkeypatch):
    name = an_account(app)
    spy = Spy(one_connection_app, monkeypatch)
    client = one_connection_app.test_client()
    assert h.login(client, name).status_code == 303                                           # with a pool of one, the request could not have run otherwise
    assert spy.calls == [("verify_password", True, False)]


def test_a_wrong_password_is_also_verified_with_the_connection_returned(app, one_connection_app, monkeypatch):
    name = an_account(app)
    spy = Spy(one_connection_app, monkeypatch)
    assert h.login(one_connection_app.test_client(), name, WRONG).status_code == 401
    assert spy.calls == [("verify_password", True, False)]


def test_an_unknown_username_still_costs_one_dummy_hash_check_and_holds_no_connection(app, one_connection_app, monkeypatch):
    """Timing behaviour preserved: an unknown name does the same work (one scrypt check) as a known one, and does it with the connection already returned."""
    name = an_account(app)
    spy = Spy(one_connection_app, monkeypatch)
    client = one_connection_app.test_client()
    assert h.login(client, "tt_nobody_here", WRONG).status_code == 401
    verifies = lambda: [(free, dummy) for n, free, dummy in spy.calls if n == "verify_password"]       # (the throwaway hash itself is made lazily, the first time it is needed)
    assert verifies() == [(True, True)]                                                       # exactly one check, against the throwaway hash, with the connection returned
    spy.calls.clear()
    assert h.login(client, name, WRONG).status_code == 401
    assert verifies() == [(True, False)]                                                      # a known name: the same single check, against the real hash


def test_the_response_to_a_known_and_an_unknown_account_is_still_identical(app, one_connection_app):
    import re
    name = an_account(app)
    client = one_connection_app.test_client()
    known, unknown = h.login(client, name, WRONG), h.login(client, "tt_nobody_here", WRONG)
    alert = lambda response: re.search(r'<div class="acct-alert".*?</div>', response.get_data(as_text=True), re.S).group(0)
    assert known.status_code == unknown.status_code == 401 and alert(known) == alert(unknown)


def test_many_logins_in_a_row_on_a_pool_of_one_never_leak_the_connection(app, one_connection_app):
    name = an_account(app)
    for number in range(6):
        password = WRONG if number % 3 == 0 else h.PASSWORD
        assert h.login(one_connection_app.test_client(), name, password).status_code == (401 if password == WRONG else 303)
        assert pool_is_free(one_connection_app)                                                  # given back after every request, successful or not


def test_a_failure_after_the_release_still_releases_the_throttle_reservation(app, one_connection_app, monkeypatch):
    name = an_account(app)

    def explode(*args, **kwargs):
        raise RuntimeError("bug in the hash check")
    monkeypatch.setattr(accounts, "verify_password", explode)
    client = one_connection_app.test_client()
    assert h.login(client, name, WRONG).status_code == 500
    throttle = one_connection_app.extensions["login_throttle"]
    with throttle._lock:
        assert [e for events in throttle._failures.values() for e in events] == []              # nothing pending, nothing counted
    assert pool_is_free(one_connection_app)


# ------------------------------------------------------------------ change password
def password_post(application, name, current, new):
    client = application.test_client()
    assert h.login(client, name).status_code == 303
    token = h.csrf_from(client.get("/account/password").get_data(as_text=True))
    response = client.post("/account/password", data={"current_password": current, "new_password": new, "new_password_confirm": new, "csrf_token": token})
    return client, response


def test_changing_the_password_hashes_twice_with_the_connection_returned_and_still_updates(app, one_connection_app, monkeypatch):
    name = an_account(app)
    before = h.user_row(name)["password_hash"]
    spy = Spy(one_connection_app, monkeypatch)
    client, response = password_post(one_connection_app, name, h.PASSWORD, h.OTHER_PASSWORD)
    assert response.status_code == 303
    assert [(n, free) for n, free, _dummy in spy.calls][-2:] == [("verify_password", True), ("hash_password", True)]
    after = h.user_row(name)["password_hash"]
    assert after != before and check_password_hash(after, h.OTHER_PASSWORD)                    # the UPDATE took a fresh connection and was committed
    assert client.get("/account/favourites").status_code == 200                                # and this browser stays signed in
    assert h.login(app.test_client(), name, h.OTHER_PASSWORD).status_code == 303 and pool_is_free(one_connection_app)


def test_a_wrong_current_password_is_verified_with_the_connection_returned_and_counted(app, one_connection_app, monkeypatch):
    name = an_account(app)
    spy = Spy(one_connection_app, monkeypatch, names=("verify_password",))
    _client, response = password_post(one_connection_app, name, WRONG, h.OTHER_PASSWORD)
    assert response.status_code == 400
    assert spy.free()[-1] is True
    throttle = one_connection_app.extensions["login_throttle"]
    with throttle._lock:
        assert [e[2] for e in throttle._failures[f"acct:{name}"]] == [True]                     # settled: the guess counted


def test_a_weak_new_password_is_refused_and_not_counted_and_leaks_nothing(app, one_connection_app):
    name = an_account(app)
    _client, response = password_post(one_connection_app, name, h.PASSWORD, "short")
    assert response.status_code == 400 and pool_is_free(one_connection_app)
    throttle = one_connection_app.extensions["login_throttle"]
    with throttle._lock:
        assert f"acct:{name}" not in throttle._failures


def test_a_database_error_during_the_update_is_a_503_and_the_pool_recovers(app, one_connection_app, monkeypatch):
    name = an_account(app)
    before = h.user_row(name)["password_hash"]

    def broken(*args, **kwargs):
        raise mysql.connector.Error("boom")
    with monkeypatch.context() as patched:
        patched.setattr(users_repo, "update_password", broken)
        _client, response = password_post(one_connection_app, name, h.PASSWORD, h.OTHER_PASSWORD)
    assert response.status_code == 503 and h.user_row(name)["password_hash"] == before
    assert pool_is_free(one_connection_app) and h.login(one_connection_app.test_client(), name).status_code == 303


# ------------------------------------------------------------------ sign up
def test_signing_up_hashes_before_any_connection_is_taken(one_connection_app, monkeypatch):
    spy = Spy(one_connection_app, monkeypatch, names=("hash_password",))
    client = one_connection_app.test_client()
    name = h.new_username()
    token = h.csrf_from(client.get("/register").get_data(as_text=True))
    response = client.post("/register", data={"username": name, "password": h.PASSWORD, "password_confirm": h.PASSWORD, "csrf_token": token})
    assert response.status_code == 303 and spy.calls == [("hash_password", True, False)] and h.user_row(name) is not None
    assert pool_is_free(one_connection_app)


# ------------------------------------------------------------------ release_connection itself
def test_release_with_no_connection_is_a_no_op(app):
    with app.app_context():
        release_connection()
        release_connection()
        assert "db" not in g


def test_release_returns_the_connection_and_the_next_query_takes_a_fresh_one(one_connection_app):
    with one_connection_app.app_context():
        assert query_one("SELECT 1 AS one")["one"] == 1
        assert not pool_is_free(one_connection_app)                                              # held
        release_connection()
        assert "db" not in g and pool_is_free(one_connection_app)                                # returned at once, not at the end of the request
        assert query_one("SELECT 2 AS two")["two"] == 2 and g.db is not None
        release_connection()
        release_connection()                                                                     # twice is harmless
    assert pool_is_free(one_connection_app)                                                      # and the end-of-request cleanup finds nothing to do


def test_release_is_refused_inside_a_transaction_and_the_unit_of_work_survives(app):
    name = h.new_username()
    with app.app_context():
        with transaction() as cursor:
            cursor.execute("INSERT INTO users (username, password_hash) VALUES (%s, 'x')", (name,))
            with pytest.raises(TransactionError, match="inside transaction"):
                release_connection()
            assert g.db is not None                                                              # untouched
    assert h.user_row(name) is not None                                                          # and the write was committed as usual


def test_release_is_refused_while_raw_work_may_be_uncommitted(app):
    raw = h.new_username()
    with app.app_context():
        cursor = get_db().cursor()
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (%s, 'x')", (raw,))
        cursor.close()
        assert get_db().in_transaction
        with pytest.raises(TransactionError, match="get_db"):
            release_connection()
        get_db().commit()                                                                        # the owner of the raw work decides
        release_connection()                                                                     # once it is committed, releasing is fine again
        assert "db" not in g and g.get("db_raw") is False
    assert h.user_row(raw) is not None


def test_a_transaction_after_a_release_gets_a_fresh_connection_and_commits(app):
    name = h.new_username()
    with app.app_context():
        assert query_one("SELECT COUNT(*) AS n FROM users") is not None
        release_connection()
        with transaction() as cursor:
            cursor.execute("INSERT INTO users (username, password_hash) VALUES (%s, 'x')", (name,))
        assert query_one("SELECT user_id FROM users WHERE username = %s", (name,))
    assert h.user_row(name) is not None


# ------------------------------------------------------------------ the order of the calls is guarded in the source too
def _calls_in(function):
    # evaluation order: by line, and on one line the inner (later-starting) call runs before the outer one that takes it as an argument
    return sorted(((node.lineno, -node.col_offset, ast.unparse(node.func)) for node in ast.walk(function) if isinstance(node, ast.Call)))


def test_the_service_releases_the_connection_after_reading_and_before_hashing():
    tree = ast.parse((ROOT / "app" / "services" / "accounts.py").read_text(encoding="utf-8"))
    functions = {node.name: node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}

    def order(name):
        return [call for _line, _col, call in _calls_in(functions[name])]
    authenticate, change = order("authenticate"), order("change_password")
    assert authenticate.index("users_repo.get_by_username") < authenticate.index("db.release_connection") < authenticate.index("_burn_a_hash") < authenticate.index("verify_password")
    assert change.index("users_repo.get_by_id") < change.index("db.release_connection") < change.index("verify_password") < change.index("hash_password") < change.index("users_repo.update_password")
    register = order("register")
    assert "users_repo.get_by_id" not in register[:register.index("hash_password")] and "db.release_connection" not in register      # sign-up hashes before any database call
