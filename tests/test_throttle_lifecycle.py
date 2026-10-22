"""The reservation lifecycle on the real routes (Phase 3A): sign in, change password and sign up. Requests that arrive together are held INSIDE the service call
with a gate, so the test can see exactly how many were let in and prove that the rest were refused before any password was checked. Ordering comes from the
gate, a barrier and thread joins, never from sleeping. Real rows go to the *_test database only (tests/account_helpers.py proves the name first)."""
import threading
import time

import mysql.connector
import pytest

from app.repositories import users as users_repo
from app.services import accounts
from tests import account_helpers as h

pytestmark = pytest.mark.usefixtures("clean_accounts")
WRONG = "wrong password !!"
ADDRESS = "203.0.113.5"


# ------------------------------------------------------------------ the machinery
class Gate:
    """Replaces a service function. Every call announces itself and then waits at the gate until the test opens it (calls for which `holds` is false pass at once)."""

    def __init__(self, monkeypatch, module, name, holds=lambda *args, **kwargs: True):
        self.real, self.holds, self.count = getattr(module, name), holds, 0
        self._count_lock, self.opened, self._entered = threading.Lock(), threading.Event(), threading.Semaphore(0)
        monkeypatch.setattr(module, name, self)

    def __call__(self, *args, **kwargs):
        if self.holds(*args, **kwargs):
            with self._count_lock:
                self.count += 1
            self._entered.release()
            assert self.opened.wait(60), "the gate was never opened"
        return self.real(*args, **kwargs)

    def wait_until_entered(self, n):
        for _ in range(n):
            assert self._entered.acquire(timeout=30), "fewer requests reached the gate than expected"

    def open(self):
        self.opened.set()


class Burst:
    """POSTs started together by a barrier, one thread (and one client) each. A job: {client, path, data, address}."""

    def __init__(self, jobs):
        self.results, self.barrier = {}, threading.Barrier(len(jobs))
        self.errors, self.total = [], len(jobs)
        self.threads = [threading.Thread(target=self._run, args=(i, job), daemon=True) for i, job in enumerate(jobs)]
        for thread in self.threads:
            thread.start()

    def _run(self, i, job):
        try:
            self.barrier.wait(30)
            self.results[i] = job["client"].post(job["path"], data=job["data"], environ_overrides={"REMOTE_ADDR": job["address"]})
        except BaseException as error:
            self.errors.append(error)

    def wait_for(self, finished):
        """Wait until `finished` of the requests have answered (the others are held at a gate)."""
        deadline = time.monotonic() + 60
        while len(self.results) < finished and not self.errors and time.monotonic() < deadline:
            time.sleep(0.01)                                   # polling for completion only; no assertion depends on how long it took
        assert not self.errors, self.errors
        assert len(self.results) >= finished, f"only {len(self.results)} requests answered"

    def finish(self):
        for thread in self.threads:
            thread.join(60)
            assert not thread.is_alive()
        assert not self.errors, self.errors
        return [self.results[i] for i in range(self.total)]


def codes(responses):
    return sorted(response.status_code for response in responses)


def job(app, path, data, address=ADDRESS, token_page="/login", client=None):
    client = client or app.test_client()
    page = client.get(token_page, environ_overrides={"REMOTE_ADDR": address})
    return {"client": client, "path": path, "data": {**data, "csrf_token": h.csrf_from(page.get_data(as_text=True))}, "address": address}


def sign_in_job(app, name, password=WRONG, address=ADDRESS):
    return job(app, "/login", {"username": name, "password": password}, address)


def _attempt(app, name, password, address):
    j = sign_in_job(app, name, password, address)
    return j["client"].post(j["path"], data=j["data"], environ_overrides={"REMOTE_ADDR": address})


def table(app):
    return app.extensions["login_throttle"]


def events(app, key):
    throttle = table(app)
    with throttle._lock:
        return [list(e) for e in throttle._failures.get(key, ())]


def keys_for(name, address=ADDRESS):
    return f"user:{address}:{name}", f"addr:{address}", f"acct:{name}"


def password_job(app, name, current, new=h.OTHER_PASSWORD, confirm=None, address="127.0.0.1"):
    client = app.test_client()
    assert h.login(client, name).status_code == 303
    page = client.get("/account/password", environ_overrides={"REMOTE_ADDR": address})
    data = {"current_password": current, "new_password": new, "new_password_confirm": new if confirm is None else confirm, "csrf_token": h.csrf_from(page.get_data(as_text=True))}
    return {"client": client, "path": "/account/password", "data": data, "address": address}


# ------------------------------------------------------------------ sign in
def test_simultaneous_wrong_guesses_cannot_exceed_the_limit(app, monkeypatch):
    monkeypatch.setitem(app.config, "LOGIN_MAX_FAILURES", 2)
    name = h.signed_in_client(app)[1]
    gate = Gate(monkeypatch, accounts, "authenticate")
    burst = Burst([sign_in_job(app, name) for _ in range(6)])
    gate.wait_until_entered(2)
    burst.wait_for(4)                                                        # four were refused before any password was checked...
    assert gate.count == 2                                                   # ...and only two ever reached the password check
    assert len(events(app, keys_for(name)[0])) == 2 and all(not e[2] for e in events(app, keys_for(name)[0]))        # held as pending
    gate.open()
    assert codes(burst.finish()) == [401, 401, 429, 429, 429, 429]
    assert gate.count == 2 and [e[2] for e in events(app, keys_for(name)[0])] == [True, True]                      # settled: they counted


def test_simultaneous_guesses_from_many_addresses_cannot_exceed_the_account_limit(app, monkeypatch):
    monkeypatch.setitem(app.config, "LOGIN_MAX_FAILURES_PER_ACCOUNT", 3)
    name = h.signed_in_client(app)[1]
    gate = Gate(monkeypatch, accounts, "authenticate")
    burst = Burst([sign_in_job(app, name, address=f"198.51.100.{n}") for n in range(1, 8)])     # seven addresses, none near its own limits
    gate.wait_until_entered(3)
    burst.wait_for(4)
    assert gate.count == 3 and len(events(app, f"acct:{name}")) == 3
    gate.open()
    assert codes(burst.finish()) == [401, 401, 401, 429, 429, 429, 429]


def test_different_spellings_of_one_username_share_the_reservation(app, monkeypatch):
    monkeypatch.setitem(app.config, "LOGIN_MAX_FAILURES_PER_ACCOUNT", 2)
    name = h.signed_in_client(app)[1]
    gate = Gate(monkeypatch, accounts, "authenticate")
    spellings = [name, name.upper(), f"  {name}  ", name.title()]
    burst = Burst([sign_in_job(app, spelling, address=f"198.51.100.{n}") for n, spelling in enumerate(spellings, 1)])
    gate.wait_until_entered(2)
    burst.wait_for(2)
    assert gate.count == 2 and len([k for k in table(app)._failures if k.startswith("acct:")]) == 1
    gate.open()
    assert codes(burst.finish()) == [401, 401, 429, 429]


def test_correct_logins_never_use_the_failed_attempt_budget(app, monkeypatch):
    monkeypatch.setitem(app.config, "LOGIN_MAX_FAILURES", 2)
    monkeypatch.setitem(app.config, "LOGIN_MAX_FAILURES_PER_ADDRESS", 3)
    monkeypatch.setitem(app.config, "LOGIN_MAX_FAILURES_PER_ACCOUNT", 3)
    name = h.signed_in_client(app)[1]
    for _ in range(12):                                                      # twelve successes from one address, far past every limit
        assert _attempt(app, name, h.PASSWORD, ADDRESS).status_code == 303
    assert all(events(app, key) == [] for key in keys_for(name))             # a success leaves nothing behind
    assert [_attempt(app, name, WRONG, ADDRESS).status_code for _ in range(3)] == [401, 401, 429]       # the budget is intact: exactly two guesses


def test_simultaneous_correct_logins_all_succeed_and_leave_nothing(app, monkeypatch):
    name = h.signed_in_client(app)[1]
    gate = Gate(monkeypatch, accounts, "authenticate")
    burst = Burst([sign_in_job(app, name, h.PASSWORD) for _ in range(4)])
    gate.wait_until_entered(4)
    assert all(len(events(app, key)) == 4 for key in keys_for(name))         # four pending reservations while they run
    gate.open()
    assert codes(burst.finish()) == [303, 303, 303, 303]
    assert all(events(app, key) == [] for key in keys_for(name))             # and nothing once they have succeeded


def test_a_success_forgives_settled_typos_but_not_attempts_still_running(app, monkeypatch):
    name = h.signed_in_client(app)[1]
    user_key, address_key, account_key = keys_for(name)
    assert [_attempt(app, name, WRONG, ADDRESS).status_code for _ in range(2)] == [401, 401]      # two typos, settled
    gate = Gate(monkeypatch, accounts, "authenticate", holds=lambda form: form.get("password") == WRONG)    # only wrong guesses wait at the gate
    burst = Burst([sign_in_job(app, name, WRONG)])
    gate.wait_until_entered(1)                                               # a wrong guess is now in flight (pending)
    assert _attempt(app, name, h.PASSWORD, ADDRESS).status_code == 303       # the owner signs in from the same address meanwhile
    mine = events(app, user_key)
    assert len(mine) == 1 and mine[0][2] is False                            # the typos are forgiven; the attempt in flight is NOT
    assert len(events(app, address_key)) == 3 and len(events(app, account_key)) == 3        # address and account counters are not reset
    gate.open()
    assert codes(burst.finish()) == [401]
    assert [e[2] for e in events(app, user_key)] == [True]                   # and it still settles as a failure
    assert len(events(app, address_key)) == 3 and len(events(app, account_key)) == 3


def test_a_success_does_not_hand_back_the_account_budget_while_guesses_are_in_flight(app, monkeypatch):
    monkeypatch.setitem(app.config, "LOGIN_MAX_FAILURES_PER_ACCOUNT", 4)
    monkeypatch.setitem(app.config, "LOGIN_MAX_FAILURES", 10)
    name = h.signed_in_client(app)[1]
    for n in (1, 2):
        assert _attempt(app, name, WRONG, f"198.51.100.{n}").status_code == 401
    gate = Gate(monkeypatch, accounts, "authenticate", holds=lambda form: form.get("password") == WRONG)
    burst = Burst([sign_in_job(app, name, WRONG, "198.51.100.3")])
    gate.wait_until_entered(1)
    assert _attempt(app, name, h.PASSWORD, "198.51.100.4").status_code == 303
    assert len(events(app, f"acct:{name}")) == 3                             # 2 settled + 1 pending: the success neither added to it nor wiped it
    gate.open()
    assert codes(burst.finish()) == [401]
    assert _attempt(app, name, WRONG, "198.51.100.5").status_code == 401     # the fourth and last guess fits...
    assert _attempt(app, name, h.PASSWORD, "198.51.100.6").status_code == 429       # ...and then even the right password waits out the cooldown


def test_a_database_error_is_not_counted_and_leaves_no_reservation(app, monkeypatch):
    monkeypatch.setitem(app.config, "LOGIN_MAX_FAILURES", 1)
    name = h.signed_in_client(app)[1]

    def broken(*args, **kwargs):
        raise mysql.connector.Error("boom: internal detail")
    with monkeypatch.context() as patched:
        patched.setattr(users_repo, "get_by_username", broken)
        responses = [_attempt(app, name, WRONG, ADDRESS) for _ in range(3)]
    assert [r.status_code for r in responses] == [503, 503, 503]             # never 429: the failed requests held nothing
    assert all("internal detail" not in r.get_data(as_text=True) for r in responses)
    assert all(events(app, key) == [] for key in keys_for(name))
    assert [_attempt(app, name, WRONG, ADDRESS).status_code for _ in range(2)] == [401, 429]       # the budget was untouched: one guess, then the limit


def test_an_unexpected_error_is_not_counted_either(app, monkeypatch):
    monkeypatch.setitem(app.config, "LOGIN_MAX_FAILURES", 1)
    name = h.signed_in_client(app)[1]

    def explode(form):
        raise RuntimeError("bug")
    with monkeypatch.context() as patched:
        patched.setattr(accounts, "authenticate", explode)
        assert [_attempt(app, name, WRONG, ADDRESS).status_code for _ in range(3)] == [500, 500, 500]
    assert all(events(app, key) == [] for key in keys_for(name))


def test_an_unknown_username_counts_like_a_wrong_password_and_gets_the_same_answer(app, monkeypatch):
    monkeypatch.setitem(app.config, "LOGIN_MAX_FAILURES", 2)
    real = h.signed_in_client(app)[1]
    invented = "tt_nobody_" + h.new_username()[3:9]
    results = {name: [_attempt(app, name, WRONG, ADDRESS).status_code for _ in range(3)] for name in (real, invented)}
    assert results[real] == results[invented] == [401, 401, 429]
    assert [e[2] for e in events(app, keys_for(invented)[0])] == [True, True]


# ------------------------------------------------------------------ change password
def test_wrong_current_passwords_count_and_simultaneous_ones_cannot_exceed_the_limit(app, monkeypatch):
    monkeypatch.setitem(app.config, "LOGIN_MAX_FAILURES", 2)
    name = h.signed_in_client(app)[1]
    gate = Gate(monkeypatch, accounts, "change_password")
    burst = Burst([password_job(app, name, WRONG) for _ in range(4)])                # four, so the 5-connection database pool is never the limit
    gate.wait_until_entered(2)
    burst.wait_for(2)
    assert gate.count == 2
    gate.open()
    assert codes(burst.finish()) == [400, 400, 429, 429]
    assert [e[2] for e in events(app, keys_for(name, "127.0.0.1")[0])] == [True, True]


def test_a_weak_or_mismatched_new_password_is_not_a_guess_and_is_not_counted(app, monkeypatch):
    monkeypatch.setitem(app.config, "LOGIN_MAX_FAILURES", 2)
    name = h.signed_in_client(app)[1]
    for _ in range(4):
        weak = password_job(app, name, h.PASSWORD, new="short")
        mismatch = password_job(app, name, h.PASSWORD, new=h.OTHER_PASSWORD, confirm="something else entirely")
        assert weak["client"].post(weak["path"], data=weak["data"]).status_code == 400
        assert mismatch["client"].post(mismatch["path"], data=mismatch["data"]).status_code == 400
    assert all(events(app, key) == [] for key in keys_for(name, "127.0.0.1"))        # eight refused forms, no reservation left, nothing counted
    wrong = password_job(app, name, WRONG)
    assert wrong["client"].post(wrong["path"], data=wrong["data"]).status_code == 400             # and the full budget of two guesses is still there
    again = password_job(app, name, WRONG)
    assert again["client"].post(again["path"], data=again["data"]).status_code == 400


def test_a_successful_password_change_leaves_nothing_and_forgives_this_addresss_typos(app):
    name = h.signed_in_client(app)[1]
    one = password_job(app, name, WRONG)
    assert one["client"].post(one["path"], data=one["data"]).status_code == 400
    assert len(events(app, keys_for(name, "127.0.0.1")[0])) == 1
    good = password_job(app, name, h.PASSWORD)
    assert good["client"].post(good["path"], data=good["data"]).status_code == 303
    assert events(app, keys_for(name, "127.0.0.1")[0]) == []                          # the typo is forgiven, the success left nothing
    assert len(events(app, f"acct:{name}")) == 1                                       # the account-wide counter keeps the one real wrong guess


def test_a_database_error_while_changing_the_password_is_not_counted(app, monkeypatch):
    monkeypatch.setitem(app.config, "LOGIN_MAX_FAILURES", 1)
    name = h.signed_in_client(app)[1]

    def broken(*args, **kwargs):
        raise mysql.connector.Error("boom")
    with monkeypatch.context() as patched:
        patched.setattr(users_repo, "update_password", broken)
        statuses = []
        for _ in range(3):
            j = password_job(app, name, h.PASSWORD)
            statuses.append(j["client"].post(j["path"], data=j["data"]).status_code)
    assert statuses == [503, 503, 503]
    assert all(events(app, key) == [] for key in keys_for(name, "127.0.0.1"))


# ------------------------------------------------------------------ sign up
def register_job(app, name=None, password=h.PASSWORD, address="198.51.100.9"):
    return job(app, "/register", {"username": name or h.new_username(), "password": password, "password_confirm": password}, address, token_page="/register")


def test_simultaneous_sign_ups_cannot_exceed_the_limit_and_create_exactly_that_many(app, monkeypatch):
    monkeypatch.setitem(app.config, "REGISTER_MAX_PER_WINDOW", 2)
    names = [h.new_username() for _ in range(5)]
    gate = Gate(monkeypatch, accounts, "register")
    burst = Burst([register_job(app, name) for name in names])
    gate.wait_until_entered(2)
    burst.wait_for(3)
    assert gate.count == 2                                                    # the other three were refused before anything was hashed
    gate.open()
    assert codes(burst.finish()) == [303, 303, 429, 429, 429]
    created = h.rows("SELECT username FROM users WHERE username IN (%s, %s, %s, %s, %s)", tuple(names))
    assert len(created) == 2
    assert [e[2] for e in events(app, "reg:198.51.100.9")] == [True, True]    # both counted


def test_invalid_forms_leave_no_reservation_so_they_cost_nothing(app, monkeypatch):
    monkeypatch.setitem(app.config, "REGISTER_MAX_PER_WINDOW", 2)
    for _ in range(6):
        j = register_job(app, password="short")
        assert j["client"].post(j["path"], data=j["data"], environ_overrides={"REMOTE_ADDR": j["address"]}).status_code == 400
    assert events(app, "reg:198.51.100.9") == []
    for _ in range(2):
        j = register_job(app)
        assert j["client"].post(j["path"], data=j["data"], environ_overrides={"REMOTE_ADDR": j["address"]}).status_code == 303
    j = register_job(app)
    assert j["client"].post(j["path"], data=j["data"], environ_overrides={"REMOTE_ADDR": j["address"]}).status_code == 429


def test_a_name_that_is_taken_counts_because_it_reached_the_database(app, monkeypatch):
    monkeypatch.setitem(app.config, "REGISTER_MAX_PER_WINDOW", 3)
    taken = h.signed_in_client(app)[1]                                         # (the helper's own sign-up came from 127.0.0.1)
    j = register_job(app, taken)
    assert j["client"].post(j["path"], data=j["data"], environ_overrides={"REMOTE_ADDR": j["address"]}).status_code == 409
    assert [e[2] for e in events(app, "reg:198.51.100.9")] == [True]


def test_a_database_error_while_signing_up_is_not_counted(app, monkeypatch):
    monkeypatch.setitem(app.config, "REGISTER_MAX_PER_WINDOW", 1)

    def broken(*args, **kwargs):
        raise mysql.connector.Error("boom")
    with monkeypatch.context() as patched:
        patched.setattr(users_repo, "create", broken)
        statuses = []
        for _ in range(3):
            j = register_job(app)
            statuses.append(j["client"].post(j["path"], data=j["data"], environ_overrides={"REMOTE_ADDR": j["address"]}).status_code)
    assert statuses == [503, 503, 503]                                         # never 429: nothing stayed reserved
    assert events(app, "reg:198.51.100.9") == []
    j = register_job(app)
    assert j["client"].post(j["path"], data=j["data"], environ_overrides={"REMOTE_ADDR": j["address"]}).status_code == 303


# ------------------------------------------------------------------ the guarantees that must not change
def test_a_refusal_is_generic_and_identical_for_a_real_and_an_invented_account(app, monkeypatch):
    import re
    monkeypatch.setitem(app.config, "LOGIN_MAX_FAILURES_PER_ACCOUNT", 3)
    real = h.signed_in_client(app)[1]
    invented = "tt_nobody_" + h.new_username()[3:9]
    for name in (real, invented):
        for n in range(3):
            assert _attempt(app, name, WRONG, f"198.51.100.{n + 20}").status_code == 401
    pages = [_attempt(app, name, h.PASSWORD, "198.51.100.30") for name in (real, invented)]
    assert [p.status_code for p in pages] == [429, 429]
    alerts = [re.sub(r"\d+ minute", "N minute", re.search(r'<div class="acct-alert".*?</div>', p.get_data(as_text=True), re.S).group(0)) for p in pages]
    assert alerts[0] == alerts[1] and "Retry-After" in pages[0].headers and "exist" not in alerts[0].lower() and "lock" not in alerts[0].lower()


def test_the_cooldown_still_ends_by_itself_after_the_window(app, monkeypatch):
    monkeypatch.setitem(app.config, "LOGIN_MAX_FAILURES", 2)
    name = h.signed_in_client(app)[1]
    clock = {"now": 5000.0}
    throttle = table(app)
    throttle._clock = lambda: clock["now"]
    try:
        assert [_attempt(app, name, WRONG, ADDRESS).status_code for _ in range(3)] == [401, 401, 429]
        clock["now"] += app.config["LOGIN_WINDOW_SECONDS"] + 1
        assert _attempt(app, name, h.PASSWORD, ADDRESS).status_code == 303          # no permanent lockout
    finally:
        throttle._clock = time.monotonic


def test_the_address_limit_still_applies_across_usernames(app, monkeypatch):
    monkeypatch.setitem(app.config, "LOGIN_MAX_FAILURES_PER_ADDRESS", 3)
    results = [_attempt(app, f"tt_nobody_{n}", WRONG, ADDRESS).status_code for n in range(5)]
    assert results == [401, 401, 401, 429, 429]


def test_every_attempt_ends_settled_or_released_never_pending(app):
    """After a mixed run of sign-ins (right and wrong) and sign-ups (valid, invalid, taken), no event is left pending."""
    name = h.signed_in_client(app)[1]
    for password in (WRONG, h.PASSWORD, WRONG, "", h.PASSWORD, "x" * 200):
        _attempt(app, name, password, ADDRESS)
    _attempt(app, "tt_nobody_x", WRONG, ADDRESS)
    for pw in ("short", h.PASSWORD):
        j = register_job(app, password=pw)
        j["client"].post(j["path"], data=j["data"], environ_overrides={"REMOTE_ADDR": j["address"]})
    throttle = table(app)
    with throttle._lock:
        pending = [(key, e) for key, es in throttle._failures.items() for e in es if not e[2]]
    assert pending == []
