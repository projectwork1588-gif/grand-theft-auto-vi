"""Phase 3A: the per-account failed-sign-in limit (50 per username in a rolling 10 minutes, from ALL addresses together), on top of the address limits.
Real rows go to the *_test database only (tests/account_helpers.py proves the name first); times use a fake clock where a wait is involved."""
import re
import time

import pytest

from app import create_app, security
from tests import account_helpers as h

pytestmark = pytest.mark.usefixtures("clean_accounts")


def attempt(app, name, password, address, client=None):
    """One sign-in attempt from `address`. Returns the response."""
    client = client or app.test_client()
    extra = {"environ_overrides": {"REMOTE_ADDR": address}}
    token = h.csrf_from(client.get("/login", **extra).get_data(as_text=True))
    return client.post("/login", data={"username": name, "password": password, "csrf_token": token}, **extra)


def spread(app, name, failures, per_address=4, start=1):
    """`failures` wrong passwords for `name`, from addresses that each stay under their own limits. Returns the number of addresses used."""
    used, done = 0, 0
    while done < failures:
        address = f"203.0.113.{start + used}"
        for _ in range(min(per_address, failures - done)):
            assert attempt(app, name, "wrong password !!", address).status_code == 401
            done += 1
        used += 1
    return used


def alert_text(response):
    return re.search(r'<div class="acct-alert".*?</div>', response.get_data(as_text=True), re.S).group(0)


def test_the_default_policy_is_fifty_failures_per_account_in_ten_minutes(app):
    assert app.config["LOGIN_MAX_FAILURES_PER_ACCOUNT"] == 50 and app.config["LOGIN_WINDOW_SECONDS"] == 600
    assert app.config["LOGIN_MAX_FAILURES_PER_ACCOUNT"] > app.config["LOGIN_MAX_FAILURES_PER_ADDRESS"] > app.config["LOGIN_MAX_FAILURES"]


def test_fifty_failures_from_ten_addresses_block_the_fifty_first_from_an_eleventh(app):
    """The whole default policy, end to end. Each address stays at its own limit of 5, so only the account counter can stop the run."""
    name = h.signed_in_client(app)[1]
    assert spread(app, name, 50, per_address=5) == 10
    blocked = attempt(app, name, h.PASSWORD, "198.51.100.11")                # the RIGHT password, from a new address
    assert blocked.status_code == 429 and 0 < int(blocked.headers["Retry-After"]) <= app.config["LOGIN_WINDOW_SECONDS"]
    other = h.signed_in_client(app)[1]
    assert attempt(app, other, h.PASSWORD, "198.51.100.11").status_code == 303   # another account, same address: not affected


def test_forty_nine_failures_do_not_block(app):
    name = h.signed_in_client(app)[1]
    spread(app, name, 49, per_address=5)
    assert attempt(app, name, h.PASSWORD, "198.51.100.12").status_code == 303


def test_failures_spread_over_many_addresses_still_block_the_account(app, monkeypatch):
    monkeypatch.setitem(app.config, "LOGIN_MAX_FAILURES_PER_ACCOUNT", 12)
    name = h.signed_in_client(app)[1]
    assert spread(app, name, 12, per_address=4) == 3                          # 3 addresses x 4: none of them is near its own limit
    for address in ("198.51.100.20", "198.51.100.21"):
        response = attempt(app, name, h.PASSWORD, address)
        assert response.status_code == 429 and "Too many failed attempts" in response.get_data(as_text=True)
    assert attempt(app, name, "wrong password !!", "198.51.100.22").status_code == 429       # a wrong one is refused too


def test_the_block_message_is_generic_and_the_same_for_an_account_that_does_not_exist(app, monkeypatch):
    monkeypatch.setitem(app.config, "LOGIN_MAX_FAILURES_PER_ACCOUNT", 6)
    real = h.signed_in_client(app)[1]
    invented = "tt_nobody_" + h.new_username()[3:9]
    for name in (real, invented):
        spread(app, name, 6, per_address=3)
    first, second = attempt(app, real, h.PASSWORD, "198.51.100.30"), attempt(app, invented, h.PASSWORD, "198.51.100.30")
    assert first.status_code == second.status_code == 429
    assert re.sub(r"\d+ minute", "N minute", alert_text(first)) == re.sub(r"\d+ minute", "N minute", alert_text(second))
    assert real not in alert_text(first) and "exist" not in alert_text(first).lower() and "locked" not in alert_text(first).lower()
    assert "Retry-After" in first.headers and "Retry-After" in second.headers


def test_the_cooldown_ends_by_itself_and_the_right_password_works_again(app, monkeypatch):
    monkeypatch.setitem(app.config, "LOGIN_MAX_FAILURES_PER_ACCOUNT", 8)
    name = h.signed_in_client(app)[1]
    clock = {"now": 9000.0}
    throttle = app.extensions["login_throttle"]
    throttle._clock = lambda: clock["now"]
    try:
        spread(app, name, 8, per_address=4)
        assert attempt(app, name, h.PASSWORD, "198.51.100.40").status_code == 429
        clock["now"] += app.config["LOGIN_WINDOW_SECONDS"] - 5               # still inside the window
        assert attempt(app, name, h.PASSWORD, "198.51.100.41").status_code == 429
        clock["now"] += 10                                                   # the failures have left the window: a temporary cooldown, not a lock
        assert attempt(app, name, h.PASSWORD, "198.51.100.42").status_code == 303
    finally:
        throttle._clock = time.monotonic


def test_the_cooldown_shortens_as_old_failures_leave_the_window(app, monkeypatch):
    monkeypatch.setitem(app.config, "LOGIN_MAX_FAILURES_PER_ACCOUNT", 6)
    name = h.signed_in_client(app)[1]
    clock = {"now": 100.0}
    app.extensions["login_throttle"]._clock = lambda: clock["now"]
    try:
        spread(app, name, 3, per_address=3, start=50)
        clock["now"] += 400
        spread(app, name, 3, per_address=3, start=60)                        # the first three are 400 s old, the last three are new
        wait_now = int(attempt(app, name, h.PASSWORD, "198.51.100.43").headers["Retry-After"])
        assert 190 <= wait_now <= 210                                        # until the OLDEST failure leaves the 600 s window, not a full ten minutes
    finally:
        app.extensions["login_throttle"]._clock = time.monotonic


def test_a_successful_sign_in_consumes_nothing_and_does_not_reset_the_account_wide_counter(app, monkeypatch):
    """The documented semantics (Phase 3A reservations): the owner's correct password says nothing about OTHER people's guesses, so the account-wide counter keeps
    them; and the success itself uses none of the budget."""
    monkeypatch.setitem(app.config, "LOGIN_MAX_FAILURES_PER_ACCOUNT", 10)
    name = h.signed_in_client(app)[1]
    throttle = app.extensions["login_throttle"]
    spread(app, name, 8, per_address=4, start=70)
    assert len(throttle._failures[f"acct:{name}"]) == 8
    assert attempt(app, name, h.PASSWORD, "198.51.100.50").status_code == 303
    assert len(throttle._failures[f"acct:{name}"]) == 8                      # not reset, and the success added nothing
    assert f"user:198.51.100.50:{name}" not in throttle._failures and "addr:198.51.100.50" not in throttle._failures
    assert attempt(app, name, "wrong password !!", "203.0.113.90").status_code == 401      # so exactly two more guesses fit in the account budget
    assert attempt(app, name, "wrong password !!", "203.0.113.91").status_code == 401
    assert attempt(app, name, h.PASSWORD, "198.51.100.51").status_code == 429


def test_every_spelling_of_a_username_counts_against_the_same_account(app, monkeypatch):
    monkeypatch.setitem(app.config, "LOGIN_MAX_FAILURES_PER_ACCOUNT", 10)
    name = h.signed_in_client(app)[1]
    spellings = [name, name.upper(), f"  {name}  ", name.title(), name.upper() + " "]
    for number, spelling in enumerate(spellings * 2):
        assert attempt(app, spelling, "wrong password !!", f"203.0.113.{100 + number}").status_code == 401
    throttle = app.extensions["login_throttle"]
    assert len(throttle._failures[f"acct:{name}"]) == 10 and [k for k in throttle._failures if k.startswith("acct:")] == [f"acct:{name}"]
    assert attempt(app, name, h.PASSWORD, "198.51.100.60").status_code == 429


@pytest.mark.parametrize("text", [None, "", "   ", "ab", "a" * 31, "x" * 5000, "has space", "dash-ed", "émile", "<script>alert(1)</script>", "x';--", "tt_ok\x00", "\n"])
def test_invalid_usernames_have_no_account_key(app, text):
    with app.test_request_context("/login"):
        assert security.account_key(text) is None


def test_valid_usernames_get_a_normalised_key(app):
    with app.test_request_context("/login"):
        assert security.account_key("  TT_User_1 ") == "acct:tt_user_1"
        assert security.account_key("abc") == "acct:abc" and security.account_key("a" * 30) == "acct:" + "a" * 30


def test_attacker_chosen_text_cannot_create_account_keys(app):
    throttle = app.extensions["login_throttle"]
    for number in range(30):
        attempt(app, f"garbage name {number} " + "z" * 300, "wrong password !!", f"203.0.113.{150 + number % 20}")
    assert [k for k in throttle._failures if k.startswith("acct:")] == []
    assert max(len(k) for k in throttle._failures) < 80


def test_memory_stays_bounded_and_a_blocked_account_survives_a_flood(app):
    throttle = app.extensions["login_throttle"]
    throttle.MAX_KEYS = 200                                                   # an instance setting for this test; removed again below
    try:
        victim = "tt_victim_account"
        with app.test_request_context("/login", environ_overrides={"REMOTE_ADDR": "203.0.113.1"}):
            for _ in range(app.config["LOGIN_MAX_FAILURES_PER_ACCOUNT"]):
                security.record_login_failure(victim)
            assert security.login_blocked_for(victim) > 0
        for number in range(3000):                                           # 3000 invented accounts from 3000 addresses, each failing once
            with app.test_request_context("/login", environ_overrides={"REMOTE_ADDR": f"10.{number // 250}.{number % 250}.7"}):
                security.record_login_failure(f"tt_flood_{number}")
            assert len(throttle._failures) <= 200
        with app.test_request_context("/login", environ_overrides={"REMOTE_ADDR": "203.0.113.99"}):
            assert security.login_blocked_for(victim) > 0                    # the account that reached its limit is still blocked
        assert len(throttle._failures) <= 200 and len(throttle._windows) == len(throttle._failures)
    finally:
        del throttle.MAX_KEYS


def test_each_key_holds_a_bounded_number_of_events_at_the_account_level_too(app):
    throttle = app.extensions["login_throttle"]
    with app.test_request_context("/login", environ_overrides={"REMOTE_ADDR": "203.0.113.2"}):
        for _ in range(500):
            security.record_login_failure("tt_hammered")
    assert len(throttle._failures["acct:tt_hammered"]) == security.Throttle.MAX_PER_KEY


def test_changing_the_password_with_wrong_current_passwords_counts_against_the_account(app, monkeypatch):
    monkeypatch.setitem(app.config, "LOGIN_MAX_FAILURES_PER_ACCOUNT", 3)
    client, name = h.signed_in_client(app)
    guess = {"current_password": "wrong guess number one", "new_password": h.OTHER_PASSWORD, "new_password_confirm": h.OTHER_PASSWORD}
    codes = [h.post(client, "/account/password", guess, token_from="/account/password").status_code for _ in range(4)]
    assert codes == [400, 400, 400, 429]
    assert attempt(app, name, h.PASSWORD, "198.51.100.70").status_code == 429       # the same counter guards the sign-in form


def test_the_address_limits_still_apply_alongside_the_account_limit(app):
    name = h.signed_in_client(app)[1]
    client = app.test_client()
    for _ in range(app.config["LOGIN_MAX_FAILURES"]):
        assert attempt(app, name, "wrong password !!", "203.0.113.200", client).status_code == 401
    assert attempt(app, name, h.PASSWORD, "203.0.113.200", client).status_code == 429       # this address + this username: blocked at 5
    assert attempt(app, name, h.PASSWORD, "203.0.113.201").status_code == 303               # another address is fine (the account total is only 5)


@pytest.mark.parametrize("setting", ["LOGIN_MAX_FAILURES_PER_ACCOUNT", "LOGIN_MAX_FAILURES_PER_ADDRESS", "LOGIN_MAX_FAILURES", "REGISTER_MAX_PER_WINDOW"])
def test_a_limit_the_table_could_never_reach_is_refused_at_start_up(monkeypatch, setting):
    from app import config
    monkeypatch.setattr(config.TestingConfig, setting, security.Throttle.MAX_PER_KEY + 1)
    with pytest.raises(RuntimeError, match=setting):
        create_app("testing")
