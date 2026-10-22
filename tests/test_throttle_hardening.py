"""Phase 2C: the in-process throttle can no longer be cleared wholesale or grown by attacker-chosen text, requests have a size limit, and sign-ups are limited
per address. Unit tests use a fake clock; the route tests commit real rows to the *_test database only (see tests/account_helpers.py)."""
import time

import pytest

from app import security
from tests import account_helpers as h

pytestmark = pytest.mark.usefixtures("clean_accounts")


def fake_throttle(max_keys=100):
    clock = {"now": 1000.0}
    throttle = security.Throttle(clock=lambda: clock["now"])
    throttle.MAX_KEYS = max_keys
    return throttle, clock


# ------------------------------------------------------------------ the counter table
def test_a_flood_of_new_keys_never_unblocks_a_key_that_reached_its_limit():
    throttle, clock = fake_throttle(100)
    for _ in range(5):
        throttle.record_failure("user:attacker:victim", 600)
    for i in range(1000):                                                   # ten times the table size, every key brand new
        throttle.record_failure(f"user:other:{i}", 600)
    assert throttle.blocked_for("user:attacker:victim", 5, 600) > 0
    assert len(throttle._failures) <= 100


def test_the_table_never_grows_past_its_cap_and_is_never_cleared_wholesale():
    throttle, clock = fake_throttle(50)
    for i in range(5000):
        throttle.record_failure(f"k{i}", 600)
        assert len(throttle._failures) <= 50
    assert len(throttle._failures) > 25                                      # the old behaviour emptied it at the cap


def test_the_keys_with_most_events_survive_eviction():
    throttle, clock = fake_throttle(100)
    for name in ("hot1", "hot2", "hot3"):
        for _ in range(3):
            throttle.record_failure(name, 600)
    for i in range(2000):
        clock["now"] += 0.01
        throttle.record_failure(f"cold{i}", 600)
    assert all(name in throttle._failures and len(throttle._failures[name]) == 3 for name in ("hot1", "hot2", "hot3"))


def test_expired_keys_are_forgotten_first_when_the_table_is_full():
    throttle, clock = fake_throttle(100)
    for i in range(100):
        throttle.record_failure(f"old{i}", 600)
    clock["now"] += 601                                                      # all of them are past the window
    throttle.record_failure("fresh", 600)
    assert set(throttle._failures) == {"fresh"} and set(throttle._windows) == {"fresh"}


def test_a_blocked_key_becomes_free_exactly_when_its_window_passes():
    throttle, clock = fake_throttle()
    for _ in range(5):
        throttle.record_failure("k", 600)
    assert throttle.blocked_for("k", 5, 600) > 0
    clock["now"] += 599
    assert throttle.blocked_for("k", 5, 600) > 0
    clock["now"] += 2
    assert throttle.blocked_for("k", 5, 600) == 0 and "k" not in throttle._failures


def test_one_key_cannot_hold_more_than_a_fixed_number_of_events():
    throttle, clock = fake_throttle()
    for _ in range(5000):
        throttle.record_failure("k", 600)
    assert len(throttle._failures["k"]) == security.Throttle.MAX_PER_KEY
    assert throttle.blocked_for("k", 5, 600) > 0


def test_keys_with_different_windows_are_each_expired_by_their_own_window():
    throttle, clock = fake_throttle(100)
    for _ in range(3):
        throttle.record_failure("reg:addr", 3600)                              # a registration key: an hour
    for i in range(100):
        throttle.record_failure(f"login{i}", 600)                              # login keys: ten minutes
    clock["now"] += 700                                                      # the login keys have expired, the registration key has not
    throttle.record_failure("login-new", 600)
    assert "reg:addr" in throttle._failures and throttle.blocked_for("reg:addr", 3, 3600) > 0
    assert not any(key.startswith("login") and key != "login-new" for key in throttle._failures)


def test_clear_one_key_and_clear_all():
    throttle, clock = fake_throttle()
    throttle.record_failure("a", 600)
    throttle.record_failure("b", 600)
    throttle.clear("a")
    assert set(throttle._failures) == {"b"}
    throttle.clear()
    assert throttle._failures == {} and throttle._windows == {}


# ------------------------------------------------------------------ key construction
def test_keys_are_built_from_a_bounded_normalised_username_and_the_address(app):
    with app.test_request_context("/login", environ_overrides={"REMOTE_ADDR": "203.0.113.5"}):
        assert security.throttle_keys("tt_user") == ("user:203.0.113.5:tt_user", "addr:203.0.113.5")
        assert security.throttle_keys("  TT_User  ")[0] == "user:203.0.113.5:tt_user"
        hostile = ("x" * 100000, "<script>alert(1)</script>", "ab", "has space", "émile", "", None, "a" * 31, "x'; DROP TABLE users;--")
        keys = {security.throttle_keys(name)[0] for name in hostile}
        assert keys == {"user:203.0.113.5:*invalid*"}                       # all of it shares one bucket
        assert all(len(key) < 80 for key in keys)


def test_an_over_long_address_is_cut_off(app):
    with app.test_request_context("/login", environ_overrides={"REMOTE_ADDR": "9" * 500}):
        assert len(security.client_address()) == 64


def test_garbage_usernames_cannot_create_keys(app):
    client = app.test_client()
    throttle = app.extensions["login_throttle"]
    for i in range(40):
        h.login(client, f"garbage name {i} " + "z" * 200, "wrong password!!")
    assert len(throttle._failures) <= 2                                      # the shared invalid bucket and the address; 40 distinct strings made no new keys
    assert max(len(key) for key in throttle._failures) < 80


# ------------------------------------------------------------------ request size
def test_an_oversized_form_is_refused_with_413_before_it_is_read(app):
    client = app.test_client()
    limit = app.config["MAX_CONTENT_LENGTH"]
    assert 1024 <= limit <= 64 * 1024
    for path in ("/login", "/register", "/account/password", "/favourites/characters/jason-duval"):
        response = client.post(path, data={"username": "x", "password": "p" * (limit + 1000), "csrf_token": "x"})
        assert response.status_code == 413, path
        assert "text/html" in response.headers["Content-Type"] and "Traceback" not in response.get_data(as_text=True)


def test_a_normal_sized_form_is_not_affected_and_reading_pages_never_is(app):
    client = app.test_client()
    assert h.login(client, "tt_nobody", "p" * 128).status_code == 401
    assert client.get("/characters?q=" + "a" * 70).status_code in (200, 400)
    assert client.get("/", headers={"Content-Length": "0"}).status_code == 200


# ------------------------------------------------------------------ registration abuse control
def sign_up(app_or_client, name=None, address=None, password=h.PASSWORD, confirm=None):
    client = app_or_client.test_client() if hasattr(app_or_client, "test_client") else app_or_client
    extra = {"environ_overrides": {"REMOTE_ADDR": address}} if address else {}
    page = client.get("/register", **extra).get_data(as_text=True)
    name = h.new_username() if name is None else name
    data = {"username": name, "password": password, "password_confirm": password if confirm is None else confirm, "csrf_token": h.csrf_from(page)}
    response = client.post("/register", data=data, **extra)
    response.username = name
    return response


def test_an_address_can_create_only_a_limited_number_of_accounts_per_window(app, monkeypatch):
    monkeypatch.setitem(app.config, "REGISTER_MAX_PER_WINDOW", 3)
    assert [sign_up(app).status_code for _ in range(3)] == [303, 303, 303]
    name = h.new_username()
    blocked = sign_up(app, name)
    assert blocked.status_code == 429 and int(blocked.headers["Retry-After"]) > 0
    assert "accounts created from this address" in blocked.get_data(as_text=True)
    assert h.user_row(name) is None                                           # nothing was created, nothing was hashed


def test_other_addresses_are_not_affected(app, monkeypatch):
    monkeypatch.setitem(app.config, "REGISTER_MAX_PER_WINDOW", 2)
    for _ in range(2):
        assert sign_up(app, address="198.51.100.1").status_code == 303
    assert sign_up(app, address="198.51.100.1").status_code == 429
    assert sign_up(app, address="198.51.100.2").status_code == 303


def test_invalid_forms_do_not_use_up_the_allowance_but_a_taken_name_does(app, monkeypatch):
    monkeypatch.setitem(app.config, "REGISTER_MAX_PER_WINDOW", 2)
    for _ in range(6):
        assert sign_up(app, password="short").status_code == 400            # refused before any hashing: free
    taken = sign_up(app)
    assert taken.status_code == 303
    assert sign_up(app, taken.username).status_code == 409                 # reached the hash and the INSERT: counted
    assert sign_up(app).status_code == 429


def test_the_allowance_returns_when_the_window_passes(app, monkeypatch):
    monkeypatch.setitem(app.config, "REGISTER_MAX_PER_WINDOW", 1)
    clock = {"now": 5000.0}
    throttle = app.extensions["login_throttle"]
    throttle._clock = lambda: clock["now"]
    try:
        assert sign_up(app).status_code == 303 and sign_up(app).status_code == 429
        clock["now"] += app.config["REGISTER_WINDOW_SECONDS"] + 1
        assert sign_up(app).status_code == 303
    finally:
        throttle._clock = time.monotonic


def test_the_registration_counter_and_the_login_counters_are_separate(app, monkeypatch):
    monkeypatch.setitem(app.config, "REGISTER_MAX_PER_WINDOW", 1)
    name = h.signed_in_client(app)[1]
    client = app.test_client()
    for _ in range(app.config["LOGIN_MAX_FAILURES"]):
        h.login(client, name, "wrong password!!")
    assert h.login(client, name, h.PASSWORD).status_code == 429             # login is blocked ...
    assert sign_up(app).status_code == 429                                   # ... and so is registration (it used its one), but by its own counter
    assert any(key.startswith("reg:") for key in app.extensions["login_throttle"]._failures)


def test_defaults_are_sensible(app):
    assert app.config["REGISTER_MAX_PER_WINDOW"] >= 5 and app.config["REGISTER_WINDOW_SECONDS"] >= 600
    assert app.config["LOGIN_MAX_FAILURES"] < app.config["LOGIN_MAX_FAILURES_PER_ADDRESS"]
