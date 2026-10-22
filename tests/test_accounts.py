"""Registration, sign-in, sign-out, sessions, change password and the login throttle, against the real *_test MySQL database.

Every test that commits rows uses `clean_accounts`: it proves the active database is a *_test one and removes only the tt_* accounts the tests made."""
import re
import time

import mysql.connector
import pytest
from werkzeug.security import check_password_hash

from app import security
from app.repositories import users as users_repo
from app.services import accounts
from tests import account_helpers as h

pytestmark = pytest.mark.usefixtures("clean_accounts")


# ------------------------------------------------------------------ the forms
def test_register_and_login_pages_render_without_javascript(client):
    for path, button in (("/register", "Create account"), ("/login", "Sign in")):
        page = client.get(path).get_data(as_text=True)
        assert '<form class="acct-form" method="post"' in page and 'name="csrf_token"' in page and button in page
        assert "<script" not in page.split("<main", 1)[1].split("</main>")[0]            # the form itself needs no script
    register = client.get("/register").get_data(as_text=True)
    assert 'autocomplete="new-password"' in register and 'type="password"' in register and 'minlength="10"' in register
    assert 'autocomplete="current-password"' in client.get("/login").get_data(as_text=True)


def test_anonymous_pages_set_no_cookie_and_show_sign_in_links(client):
    response = client.get("/characters")
    assert "Set-Cookie" not in response.headers
    page = response.get_data(as_text=True)
    assert 'href="/login"' in page and 'href="/register"' in page and "Sign out" not in page


# ------------------------------------------------------------------ registration
def test_register_creates_an_account_signs_in_and_stores_only_a_hash(app):
    client = app.test_client()
    response = h.register(client)
    assert response.status_code == 303 and response.headers["Location"].endswith("/account/favourites")
    user = h.user_row(response.username)
    assert user and user["role"] == "user" and user["email"] is None
    stored = user["password_hash"]
    assert stored.startswith("scrypt:") and h.PASSWORD not in stored and check_password_hash(stored, h.PASSWORD)
    page = client.get("/account/favourites")
    assert page.status_code == 200 and response.username in page.get_data(as_text=True)


def test_the_session_cookie_is_http_only_same_site_and_eight_hours(app):
    client = app.test_client()
    response = h.register(client)
    cookie = next(c for c in response.headers.getlist("Set-Cookie") if c.startswith("tv_session="))
    assert "HttpOnly" in cookie and "SameSite=Lax" in cookie
    assert "Path=/" in cookie
    assert app.config["PERMANENT_SESSION_LIFETIME"].total_seconds() == 8 * 3600
    assert re.search(r"Expires=", cookie)
    assert h.PASSWORD not in cookie                                                         # the cookie never holds a password
    assert app.config["SESSION_COOKIE_SECURE"] is False                                     # the test server speaks http; ProductionConfig sets it (tested in test_account_config)


def test_two_identical_passwords_get_different_hashes():
    first, second = accounts.hash_password(h.PASSWORD), accounts.hash_password(h.PASSWORD)
    assert first != second and first.startswith("scrypt:") and accounts.verify_password(first, h.PASSWORD) and not accounts.verify_password(first, h.PASSWORD + "x")


def test_a_sign_up_cannot_choose_its_role_or_id(app):
    client = app.test_client()
    response = h.register(client, role="admin", user_id="1", email="a@example.test")
    assert response.status_code == 303
    user = h.user_row(response.username)
    assert user["role"] == "user" and user["email"] is None and user["user_id"] != 1


def test_usernames_are_stored_lower_case_and_trimmed(app):
    client = app.test_client()
    name = h.new_username()
    response = h.register(client, "  " + name.upper() + " ")
    assert response.status_code == 303 and h.user_row(name)["username"] == name


def test_a_duplicate_username_is_refused_with_409_whatever_its_case(app):
    first = app.test_client()
    name = h.register(first).username
    for attempt in (name, name.upper()):
        second = app.test_client()
        response = h.register(second, attempt)
        assert response.status_code == 409 and "already taken" in response.get_data(as_text=True)
    assert len(h.rows("SELECT user_id FROM users WHERE username = %s", (name,))) == 1


def test_two_sign_ups_racing_for_one_name_leave_one_account(app):
    """The UNIQUE index is the guard, not a check-then-insert (there is no pre-check to race): the second INSERT fails cleanly and becomes a 409."""
    name = h.register(app.test_client()).username
    response = h.register(app.test_client(), name)
    assert response.status_code == 409
    assert len(h.rows("SELECT user_id FROM users WHERE username = %s", (name,))) == 1


@pytest.mark.parametrize("bad", ["ab", "a" * 31, "has space", "dash-ed", "émile", "x'; DROP TABLE users;--", "<script>alert(1)</script>", ""])
def test_invalid_usernames_are_refused_and_nothing_is_stored(app, bad):
    before = h.rows("SELECT COUNT(*) AS n FROM users")[0]["n"]
    response = h.register(app.test_client(), bad)
    assert response.status_code == 400
    assert h.rows("SELECT COUNT(*) AS n FROM users")[0]["n"] == before
    assert h.rows("SELECT 1 FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = 'users'")      # the table is still there


@pytest.mark.parametrize("password, confirm, fragment", [
    ("short", "short", "at least 10"),
    ("x" * 129, "x" * 129, "at most 128"),
    ("a perfectly fine passphrase", "a different passphrase", "not the same"),
    ("with\x00nul-character", "with\x00nul-character", "not allowed"),
])
def test_weak_or_mismatched_passwords_are_refused(app, password, confirm, fragment):
    client = app.test_client()
    name = h.new_username()
    response = h.register(client, name, password, confirm)
    assert response.status_code == 400 and fragment in response.get_data(as_text=True)
    assert h.user_row(name) is None


def test_the_password_may_not_equal_the_username(app):
    name = "tt_" + "p" * 9
    response = h.register(app.test_client(), name, name)
    assert response.status_code == 400 and h.user_row(name) is None


def test_a_refused_sign_up_keeps_the_username_but_never_the_password(app):
    client = app.test_client()
    name = h.new_username()
    page = h.register(client, name, "short", "short").get_data(as_text=True)
    assert f'value="{name}"' in page and "short" not in re.findall(r'<input[^>]*type="password"[^>]*>', page)[0]
    assert 'role="alert"' in page and 'aria-invalid="true"' in page and 'aria-describedby="password-note"' in page


def test_registering_while_signed_in_goes_to_the_favourites(app):
    client, _ = h.signed_in_client(app)
    assert client.get("/register").status_code == 303 and client.get("/login").status_code == 303


# ------------------------------------------------------------------ sign in
def test_login_with_the_right_password_signs_in(app):
    name = h.signed_in_client(app)[1]
    client = app.test_client()
    response = h.login(client, name)
    assert response.status_code == 303 and response.headers["Location"].endswith("/account/favourites")
    assert client.get("/account/favourites").status_code == 200


def test_login_ignores_case_and_surrounding_spaces_in_the_username(app):
    name = h.signed_in_client(app)[1]
    assert h.login(app.test_client(), f"  {name.upper()}  ").status_code == 303


def test_wrong_password_and_unknown_user_look_exactly_alike(app):
    name = h.signed_in_client(app)[1]
    wrong = h.login(app.test_client(), name, "not the right password")
    unknown = h.login(app.test_client(), "tt_nobodyhere", "not the right password")
    assert wrong.status_code == unknown.status_code == 401

    def message(response):
        return re.search(r'<div class="acct-alert".*?</div>', response.get_data(as_text=True), re.S).group(0)
    assert message(wrong) == message(unknown) and accounts.GENERIC_LOGIN_ERROR in message(wrong)


@pytest.mark.parametrize("payload", ["' OR '1'='1", "tt_x' --", "\" OR \"\"=\"", "admin'/*", "%", "tt_%"])
def test_sql_metacharacters_in_the_login_form_match_nothing(app, payload):
    h.signed_in_client(app)
    client = app.test_client()
    for username, password in ((payload, payload), (payload, h.PASSWORD)):
        assert h.login(client, username, password).status_code == 401
    assert client.get("/account/favourites").status_code == 303


def test_an_empty_or_oversized_login_is_a_plain_failure(app):
    client = app.test_client()
    assert h.login(client, "", "").status_code == 401
    assert h.login(client, "tt_x", "p" * 5000).status_code == 401


def test_login_signs_in_with_a_new_session_and_a_new_csrf_token(app):
    name = h.signed_in_client(app)[1]
    client = app.test_client()
    before = h.token(client, "/login")
    assert h.login(client, name).status_code == 303
    after = h.csrf_from(client.get("/account/favourites").get_data(as_text=True))
    assert before != after                                                                    # no token (or session) from before sign-in survives it


# ------------------------------------------------------------------ sign out and session life
def test_logout_ends_the_session_and_protected_pages_send_you_to_sign_in(app):
    client, name = h.signed_in_client(app)
    assert client.get("/account/favourites").status_code == 200
    response = h.logout(client)
    assert response.status_code == 303 and response.headers["Location"] == "/"
    after = client.get("/account/favourites")
    assert after.status_code == 303 and after.headers["Location"].endswith("/login")
    assert name not in client.get("/").get_data(as_text=True)                               # the page no longer shows the account


def test_logout_is_post_only_and_needs_the_csrf_token(app):
    client, _ = h.signed_in_client(app)
    assert client.get("/logout").status_code == 405
    assert client.post("/logout").status_code == 400
    assert h.post(client, "/logout", {"csrf_token": "forged"}, with_token=False).status_code == 400
    assert client.get("/account/favourites").status_code == 200                                # still signed in after the refused attempts


def test_an_old_sign_in_is_dropped_even_if_the_cookie_is_still_valid(app):
    client, _ = h.signed_in_client(app)
    with client.session_transaction() as session:
        session["iat"] = int(time.time()) - 8 * 3600 - 60
    response = client.get("/account/favourites")
    assert response.status_code == 303 and response.headers["Location"].endswith("/login")


def test_a_tampered_or_garbage_cookie_means_anonymous(app):
    client, _ = h.signed_in_client(app)
    cookie = client.get_cookie("tv_session")
    client.set_cookie("tv_session", cookie.value[:-3] + ("AAA" if not cookie.value.endswith("AAA") else "BBB"))
    assert client.get("/account/favourites").status_code == 303
    client.set_cookie("tv_session", "garbage")
    assert client.get("/account/favourites").status_code == 303


def test_a_session_for_a_deleted_account_is_dropped(app):
    client, name = h.signed_in_client(app)
    h.execute("DELETE FROM users WHERE username = %s", (name,))
    assert client.get("/account/favourites").status_code == 303


def test_a_user_id_the_wrong_type_in_the_session_is_not_trusted(app):
    client, _ = h.signed_in_client(app)
    with client.session_transaction() as session:
        session["uid"] = "1 OR 1=1"
    assert client.get("/account/favourites").status_code == 303


def test_account_pages_are_not_stored_and_signed_in_pages_are_private(app):
    client, _ = h.signed_in_client(app)
    assert client.get("/account/favourites").headers["Cache-Control"] == "no-store"
    assert client.get("/login").headers.get("Cache-Control") == "no-store"
    assert client.get("/characters").headers["Cache-Control"] == "private"
    assert "Cache-Control" not in app.test_client().get("/characters").headers


def test_the_menu_shows_the_signed_in_user_and_a_sign_out_form(app):
    client, name = h.signed_in_client(app)
    page = client.get("/about").get_data(as_text=True)
    assert f"({name})" in page and "Sign out" in page and 'action="/logout"' in page and "Create an account" not in page


def test_a_hostile_stored_username_is_escaped_everywhere(app):
    hostile = "tt_<script>alert(1)</script>"
    h.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", (hostile, accounts.hash_password(h.PASSWORD)))
    client = app.test_client()
    assert h.login(client, hostile).status_code == 303
    for path in ("/account/favourites", "/account/password", "/about"):
        page = client.get(path).get_data(as_text=True)
        assert "<script>alert(1)</script>" not in page and "&lt;script&gt;alert(1)&lt;/script&gt;" in page, path


# ------------------------------------------------------------------ change password
def test_change_password_updates_the_hash_and_keeps_this_browser_signed_in(app):
    client, name = h.signed_in_client(app)
    old_hash = h.user_row(name)["password_hash"]
    response = h.post(client, "/account/password", {"current_password": h.PASSWORD, "new_password": h.OTHER_PASSWORD, "new_password_confirm": h.OTHER_PASSWORD}, token_from="/account/password")
    assert response.status_code == 303
    new_hash = h.user_row(name)["password_hash"]
    assert new_hash != old_hash and check_password_hash(new_hash, h.OTHER_PASSWORD) and not check_password_hash(new_hash, h.PASSWORD)
    assert client.get("/account/favourites").status_code == 200
    assert h.login(app.test_client(), name, h.PASSWORD).status_code == 401                      # the old password no longer works
    assert h.login(app.test_client(), name, h.OTHER_PASSWORD).status_code == 303


def test_changing_the_password_signs_every_other_browser_out(app):
    first, name = h.signed_in_client(app)
    second = app.test_client()
    assert h.login(second, name).status_code == 303 and second.get("/account/favourites").status_code == 200
    h.post(first, "/account/password", {"current_password": h.PASSWORD, "new_password": h.OTHER_PASSWORD, "new_password_confirm": h.OTHER_PASSWORD}, token_from="/account/password")
    assert first.get("/account/favourites").status_code == 200
    stale = second.get("/account/favourites")
    assert stale.status_code == 303 and stale.headers["Location"].endswith("/login")


@pytest.mark.parametrize("current, new, confirm, field", [
    ("not the current one", h.OTHER_PASSWORD, h.OTHER_PASSWORD, "current_password"),
    (h.PASSWORD, "short", "short", "new_password"),
    (h.PASSWORD, h.PASSWORD, h.PASSWORD, "new_password"),
    (h.PASSWORD, h.OTHER_PASSWORD, "something else entirely", "new_password_confirm"),
    ("", h.OTHER_PASSWORD, h.OTHER_PASSWORD, "current_password"),
])
def test_a_refused_change_leaves_the_password_alone(app, current, new, confirm, field):
    client, name = h.signed_in_client(app)
    before = h.user_row(name)["password_hash"]
    response = h.post(client, "/account/password", {"current_password": current, "new_password": new, "new_password_confirm": confirm}, token_from="/account/password")
    assert response.status_code == 400 and f'id="{field}-note"' in response.get_data(as_text=True)
    assert h.user_row(name)["password_hash"] == before


def test_change_password_needs_sign_in_and_the_csrf_token(app):
    anonymous = app.test_client()
    response = h.post(anonymous, "/account/password", {"current_password": "x", "new_password": h.OTHER_PASSWORD, "new_password_confirm": h.OTHER_PASSWORD})
    assert response.status_code == 303 and response.headers["Location"].endswith("/login")
    assert anonymous.get("/account/password").status_code == 303
    client, name = h.signed_in_client(app)
    before = h.user_row(name)["password_hash"]
    refused = client.post("/account/password", data={"current_password": h.PASSWORD, "new_password": h.OTHER_PASSWORD, "new_password_confirm": h.OTHER_PASSWORD})
    assert refused.status_code == 400 and h.user_row(name)["password_hash"] == before


def test_guessing_the_current_password_is_throttled(app):
    client, name = h.signed_in_client(app)
    guess = {"current_password": "wrong guess number one", "new_password": h.OTHER_PASSWORD, "new_password_confirm": h.OTHER_PASSWORD}
    codes = [h.post(client, "/account/password", guess, token_from="/account/password").status_code for _ in range(app.config["LOGIN_MAX_FAILURES"] + 1)]
    assert codes == [400] * app.config["LOGIN_MAX_FAILURES"] + [429]
    right = {**guess, "current_password": h.PASSWORD}
    blocked = h.post(client, "/account/password", right, token_from="/account/password")
    assert blocked.status_code == 429 and int(blocked.headers["Retry-After"]) > 0
    assert check_password_hash(h.user_row(name)["password_hash"], h.PASSWORD)


# ------------------------------------------------------------------ the login throttle
def test_five_failures_block_the_sixth_attempt_even_with_the_right_password(app):
    name = h.signed_in_client(app)[1]
    client = app.test_client()
    codes = [h.login(client, name, "wrong password!!").status_code for _ in range(app.config["LOGIN_MAX_FAILURES"])]
    assert codes == [401] * app.config["LOGIN_MAX_FAILURES"]
    blocked = h.login(client, name, h.PASSWORD)
    assert blocked.status_code == 429 and int(blocked.headers["Retry-After"]) > 0 and "Too many failed attempts" in blocked.get_data(as_text=True)
    assert client.get("/account/favourites").status_code == 303


def test_the_block_is_per_username_and_a_success_clears_the_count(app):
    one = h.signed_in_client(app)[1]
    two = h.signed_in_client(app)[1]
    client = app.test_client()
    for _ in range(app.config["LOGIN_MAX_FAILURES"] - 1):
        h.login(client, one, "wrong password!!")
    assert h.login(client, two, h.PASSWORD).status_code == 303                               # another username is not blocked
    client2 = app.test_client()
    assert h.login(client2, one, h.PASSWORD).status_code == 303                              # a success before the limit clears the count
    client3 = app.test_client()
    for _ in range(app.config["LOGIN_MAX_FAILURES"] - 1):
        assert h.login(client3, one, "wrong password!!").status_code == 401


def test_one_address_trying_many_usernames_is_blocked_too(app, monkeypatch):
    monkeypatch.setitem(app.config, "LOGIN_MAX_FAILURES_PER_ADDRESS", 4)
    client = app.test_client()
    assert [h.login(client, f"tt_nobody{i}", "wrong password!!").status_code for i in range(4)] == [401] * 4
    assert h.login(client, "tt_nobody9", "wrong password!!").status_code == 429


def test_the_block_ends_when_the_window_passes(app, monkeypatch):
    name = h.signed_in_client(app)[1]
    clock = {"now": 1000.0}
    app.extensions["login_throttle"]._clock = lambda: clock["now"]
    try:
        client = app.test_client()
        for _ in range(app.config["LOGIN_MAX_FAILURES"]):
            h.login(client, name, "wrong password!!")
        assert h.login(client, name, h.PASSWORD).status_code == 429
        clock["now"] += app.config["LOGIN_WINDOW_SECONDS"] + 1
        assert h.login(client, name, h.PASSWORD).status_code == 303
    finally:
        app.extensions["login_throttle"]._clock = time.monotonic


def test_throttle_unit_behaviour():
    clock = {"now": 0.0}
    throttle = security.Throttle(clock=lambda: clock["now"])
    for _ in range(3):
        throttle.record_failure("k", 60)
    assert throttle.blocked_for("k", 3, 60) > 0 and throttle.blocked_for("k", 4, 60) == 0 and throttle.blocked_for("other", 3, 60) == 0
    clock["now"] = 61
    assert throttle.blocked_for("k", 3, 60) == 0 and "k" not in throttle._failures
    throttle.record_failure("k", 60)
    throttle.clear("k")
    assert throttle.blocked_for("k", 1, 60) == 0


def test_the_throttle_does_not_grow_without_bound():
    throttle = security.Throttle(clock=lambda: 0.0)
    throttle.MAX_KEYS = 50
    for i in range(500):
        throttle.record_failure(f"k{i}", 600)
    assert len(throttle._failures) <= 50


# ------------------------------------------------------------------ failures and rollback
def test_a_database_failure_during_sign_up_is_a_generic_503_and_stores_nothing(app, monkeypatch):
    def broken(*args, **kwargs):
        raise mysql.connector.Error("boom: secret details")
    monkeypatch.setattr(users_repo, "create", broken)
    name = h.new_username()
    response = h.register(app.test_client(), name)
    body = response.get_data(as_text=True)
    assert response.status_code == 503 and "secret details" not in body and "boom" not in body
    assert h.user_row(name) is None


def test_a_failure_before_commit_rolls_the_sign_up_back(app, monkeypatch):
    """The INSERT has run; then something fails before the commit. The transaction rolls back, so the account does not exist."""
    from contextlib import contextmanager
    from app.db import transaction

    @contextmanager
    def fails_before_commit():
        with transaction() as cursor:
            yield cursor
            raise mysql.connector.Error("failure just before the commit")
    monkeypatch.setattr(users_repo, "transaction", fails_before_commit)
    name = h.new_username()
    assert h.register(app.test_client(), name).status_code == 503
    assert h.user_row(name) is None


def test_a_committed_sign_up_is_visible_to_a_different_connection(app):
    name = h.register(app.test_client()).username
    assert h.user_row(name) is not None                                                      # h.rows() opens its own connection: the write was really committed


def test_a_database_failure_while_signing_in_is_a_generic_503(app, monkeypatch):
    def broken(username):
        raise mysql.connector.Error("boom")
    monkeypatch.setattr(users_repo, "get_by_username", broken)
    response = h.login(app.test_client(), "tt_whoever")
    assert response.status_code == 503 and "boom" not in response.get_data(as_text=True)


def test_the_transaction_helper_works_after_a_read_on_the_same_connection(app):
    """Regression: with autocommit off, a SELECT opens an implicit transaction and start_transaction() used to refuse with 'Transaction already in progress'."""
    from app.db import query_all, transaction
    name = h.new_username()
    with app.app_context():
        assert query_all("SELECT COUNT(*) AS n FROM users")                                    # a read first, as every signed-in request does
        with transaction() as cursor:
            cursor.execute("INSERT INTO users (username, password_hash) VALUES (%s, 'x')", (name,))
        assert query_all("SELECT user_id FROM users WHERE username = %s", (name,))
    assert h.user_row(name) is not None                                                        # committed, visible to a different connection
