"""Accounts, sessions and CSRF: the parts every state-changing request passes through.

* Sessions are Flask's signed cookie. It holds the user id, the time of sign-in, a stamp of the password (see password_stamp) and the CSRF token, and nothing else.
* CSRF uses the synchronizer-token pattern: a random token lives in the session, every form carries it, and every POST/PUT/PATCH/DELETE must send the same one
  (compared in constant time). Registration and login are covered too. SameSite=Lax and a same-origin check are a second layer.
* The login throttle is an in-process counter. It does NOT coordinate several worker processes or survive a restart (see docs/ACCOUNTS.md).
"""
import hashlib
import hmac
import itertools
import secrets
import threading
import time
from functools import wraps

from flask import current_app, flash, g, redirect, request, session, url_for
from werkzeug.exceptions import BadRequest

from .config import normalise_origin
from .repositories import users as users_repo
from .services.accounts import USERNAME_PATTERN

CSRF_FIELD = "csrf_token"
CSRF_HEADER = "X-CSRF-Token"
UNSAFE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


class CSRFError(BadRequest):
    description = "The form could not be checked (it has expired, or this browser is blocking cookies). Go back, reload the page and try again."


# ------------------------------------------------------------------ CSRF
def csrf_token():
    """The session's token (created on first use). Called while rendering a form, so visitors who never see a form never get a cookie."""
    token = session.get("csrf")
    if not token:
        token = session["csrf"] = secrets.token_urlsafe(32)
        session.permanent = True
    return token


def allowed_origins():
    """The origins that may submit a form: TV_PUBLIC_ORIGINS when it is set (the only source then; the Host header is not consulted), otherwise the origin
    of this request itself (development and tests, where the server is reached directly)."""
    configured = tuple(filter(None, (normalise_origin(o) for o in current_app.config.get("PUBLIC_ORIGINS") or ())))
    return configured or (f"{request.scheme}://{request.host}".lower(),)


def _same_origin():
    """Browsers send Origin on cross-site POSTs. If it is there it must be one of allowed_origins() (scheme, host and port); 'null' never is. If it is
    absent the token alone decides."""
    origin = request.headers.get("Origin")
    if origin is None:
        return True
    return normalise_origin(origin) in allowed_origins()


def protect_csrf():
    if request.method not in UNSAFE_METHODS:
        return None
    if request.url_rule is None or request.method not in request.url_rule.methods:
        return None             # no route accepts this method here, so there is nothing to protect: the normal 404/405 answer stands
    sent = request.form.get(CSRF_FIELD) or request.headers.get(CSRF_HEADER) or ""
    expected = session.get("csrf") or ""
    if not expected or not sent or not hmac.compare_digest(sent.encode("utf-8"), expected.encode("utf-8")):
        raise CSRFError()
    if not _same_origin():
        raise CSRFError()
    return None


# ------------------------------------------------------------------ the signed-in user
def password_stamp(password_hash):
    """A keyed digest of the stored password hash. Kept in the session so that changing the password signs every other browser out, without a sessions table.
    HMAC with the app's secret: the cookie reveals nothing about the hash."""
    key = current_app.config["SECRET_KEY"].encode("utf-8")
    return hmac.new(key, password_hash.encode("utf-8"), hashlib.sha256).hexdigest()[:32]


def sign_in(user):
    """Start a fresh session for `user` (a row from users_repo). The old session, including its CSRF token, is discarded first."""
    session.clear()
    session.permanent = True
    session["uid"] = user["user_id"]
    session["iat"] = int(time.time())
    session["stamp"] = password_stamp(user["password_hash"])
    session["csrf"] = secrets.token_urlsafe(32)


def sign_out():
    session.clear()


def load_user():
    """Before every request: attach g.user (or None). A cookie that is too old, names a deleted user, or predates a password change is dropped."""
    g.user = None
    if request.endpoint in (None, "static", "main.media_file") or "uid" not in session:
        return None
    lifetime = current_app.config["PERMANENT_SESSION_LIFETIME"].total_seconds()
    user = None
    if isinstance(session.get("uid"), int) and time.time() - session.get("iat", 0) <= lifetime:
        user = users_repo.get_by_id(session["uid"])
    if user is None or not hmac.compare_digest(str(session.get("stamp", "")), password_stamp(user["password_hash"])):
        session.clear()
        return None
    g.user = {"user_id": user["user_id"], "username": user["username"], "role": user["role"]}
    return None


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.get("user") is None:
            flash("Sign in to continue.", "info")
            return redirect(url_for("account.login"), code=303)
        return view(*args, **kwargs)
    return wrapped


def add_cache_headers(response):
    """Pages that differ per visitor must not be stored by shared caches; account pages are not stored at all."""
    if request.endpoint and request.endpoint.startswith("account."):
        response.headers["Cache-Control"] = "no-store"
    elif g.get("user"):
        response.headers.setdefault("Cache-Control", "private")
    return response


# ------------------------------------------------------------------ login and registration throttle
class Ticket:
    """One reservation made with Throttle.reserve(): the events it recorded, as (key, event id). Its state changes only while the Throttle's lock is held.

        "open"      capacity is reserved for an attempt that is still running;
        "settled"   the attempt COUNTED (a wrong password, a sign-up that reached the database): its events stay and age out with the window;
        "released"  the attempt did not count (it succeeded, the form was invalid, the server failed): ITS OWN events were removed, nothing else.

    A ticket leaves "open" once. Settling or releasing it again, or releasing a settled one, does nothing."""

    __slots__ = ("id", "events", "state")

    def __init__(self, ticket_id, events):
        self.id = ticket_id
        self.events = tuple(events)
        self.state = "open"


class Throttle:
    """Counts events (failed sign-ins, sign-ups) per key in a sliding window. In-process and thread-safe: every operation, and a reservation across SEVERAL keys,
    happens while one lock is held.

    reserve() is check-and-record in one step: if every limit allows the attempt, one event per key is recorded for it (pending) and a Ticket is returned;
    if any limit refuses, NOTHING is recorded on any key. The attempt is then settled (it counts) or released (it does not), by its ticket alone. Pending events
    count toward the limits, so requests that arrive at the same instant cannot all pass the check before any of them is recorded. An event that is never
    settled or released (a crash in the middle of a request) ages out with the window like any other.

    Memory is bounded: a key's list never holds more than MAX_PER_KEY events (and a limit is never above that), a key is forgotten once all its events have
    left the window, and the table never holds more than MAX_KEYS keys. At the cap, expired keys go first; if the table is still full, the least valuable 1 percent
    are evicted: keys with no pending event before keys with one, then the fewest events, then the oldest. Counters are never cleared wholesale, so a key that
    has reached its limit stays blocked while others are flooded. Each key remembers the window it was recorded with (sign-ins use minutes, sign-ups an hour)."""

    MAX_KEYS = 10000
    MAX_PER_KEY = 100

    def __init__(self, clock=time.monotonic):
        self._clock = clock
        self._lock = threading.Lock()
        self._failures = {}            # key -> [[timestamp, event id, settled], ...], oldest first
        self._windows = {}             # key -> the window its events are judged by
        self._ids = itertools.count(1)

    # ---- everything below ending in _locked is called with self._lock held
    def _recent(self, key, window):
        now = self._clock()
        kept = [e for e in self._failures.get(key, ()) if now - e[0] < window]
        if kept:
            self._failures[key] = kept
        else:
            self._failures.pop(key, None)
            self._windows.pop(key, None)
        return kept

    def _wait_locked(self, key, limit, window):
        recent = self._recent(key, window)
        if len(recent) < limit:
            return 0
        return max(1, int(window - (self._clock() - recent[0][0])) + 1)

    def _make_room_locked(self):
        for key in list(self._failures):                           # first, forget what has expired
            self._recent(key, self._windows[key])
        if len(self._failures) >= self.MAX_KEYS:                   # still full: drop the least valuable 1 percent
            def value(key):
                events = self._failures[key]
                return (any(not e[2] for e in events), len(events), events[-1][0])      # pending first protected, then more events, then newer
            for key in sorted(self._failures, key=value)[:max(1, self.MAX_KEYS // 100)]:
                del self._failures[key]
                del self._windows[key]

    def _add_locked(self, key, window, settled):
        if key not in self._failures and len(self._failures) >= self.MAX_KEYS:
            self._make_room_locked()
        self._windows[key] = window
        events = self._failures.setdefault(key, [])
        event_id = next(self._ids)
        events.append([self._clock(), event_id, settled])
        del events[:-self.MAX_PER_KEY]
        return event_id

    def _drop_empty_locked(self, key):
        if not self._failures.get(key):
            self._failures.pop(key, None)
            self._windows.pop(key, None)

    # ---- the public operations
    def blocked_for(self, key, limit, window):
        """Seconds until `key` may try again, or 0 when it may try now. A check only: it records nothing (use reserve() to attempt)."""
        with self._lock:
            return self._wait_locked(key, limit, window)

    def record_failure(self, key, window):
        """Record one settled event on `key`, with no check (for tests and diagnostics; the routes use reserve())."""
        with self._lock:
            self._add_locked(key, window, True)

    def reserve(self, checks):
        """checks: [(key, limit, window), ...]. All-or-nothing. Returns (0, Ticket) when every limit allows the attempt (one pending event is now recorded per
        key), or (seconds, None) when any limit refuses: the wait is the longest of the refusing keys' waits, and nothing at all has been recorded."""
        with self._lock:
            wait = max((self._wait_locked(key, limit, window) for key, limit, window in checks), default=0)
            if wait:
                return wait, None
            events = [(key, self._add_locked(key, window, False)) for key, _limit, window in checks]
            return 0, Ticket(next(self._ids), events)

    def settle(self, ticket):
        """The attempt counted: its events become ordinary failures and stay until they age out."""
        with self._lock:
            if ticket.state != "open":
                return
            wanted = dict.fromkeys(event_id for _key, event_id in ticket.events)
            for key, _event_id in ticket.events:
                for event in self._failures.get(key, ()):
                    if event[1] in wanted:
                        event[2] = True
            ticket.state = "settled"

    def release(self, ticket, forgive=()):
        """The attempt did not count: remove THIS TICKET'S events, and only those (another request's events, settled or pending, are never touched).
        `forgive`: keys whose already-settled failures are dropped too, in the same step (a sign-in that succeeded forgives the typos of that address and
        username); pending events are never forgiven, because they belong to attempts still running."""
        with self._lock:
            if ticket.state != "open":
                return
            ticket.state = "released"
            own = {event_id for _key, event_id in ticket.events}
            for key in {key for key, _event_id in ticket.events} | set(forgive):
                events = self._failures.get(key)
                if events:
                    events[:] = [e for e in events if e[1] not in own and not (key in forgive and e[2])]
                    self._drop_empty_locked(key)

    def clear(self, key=None):
        """Forget a key's events, pending ones included (tests and resets). A ticket whose events are gone simply has nothing left to settle or release."""
        with self._lock:
            if key is None:
                self._failures.clear()
                self._windows.clear()
            else:
                self._failures.pop(key, None)
                self._windows.pop(key, None)


def throttle():
    return current_app.extensions["login_throttle"]


def client_address():
    """The address the throttle counts against: request.remote_addr. It is the real client only if the server is reached directly, or if the app was told
    how many proxies to trust (TV_TRUSTED_PROXIES); forwarded headers are never read otherwise."""
    return (request.remote_addr or "unknown")[:64]


def throttle_keys(username):
    """(per username and address, per address). The username is normalised and bounded before it is part of a key: anything that is not a valid username
    shares one bucket per address, so attacker-chosen text cannot create keys."""
    candidate = (username or "").strip().lower()
    name = candidate if USERNAME_PATTERN.match(candidate) else "*invalid*"
    address = client_address()
    return (f"user:{address}:{name}", f"addr:{address}")


def account_key(username):
    """The key that counts failures against ONE ACCOUNT, whatever address they come from, or None when `username` cannot be an account name (so
    attacker-chosen text creates no key). The username is trimmed and lower-cased exactly as at sign-in. The key is made whether or not the account exists,
    so a block looks the same for a real and an invented name: it never says which usernames exist."""
    candidate = (username or "").strip().lower()
    return f"acct:{candidate}" if USERNAME_PATTERN.match(candidate) else None


def _login_checks(username):
    """The three limits a sign-in (or a change-password attempt) is held to: [(key, limit, window)]. This address with this username, this address with any
    username, and this account from anywhere (see account_key)."""
    cfg = current_app.config
    window = cfg["LOGIN_WINDOW_SECONDS"]
    by_user, by_address = throttle_keys(username)
    checks = [(by_user, cfg["LOGIN_MAX_FAILURES"], window), (by_address, cfg["LOGIN_MAX_FAILURES_PER_ADDRESS"], window)]
    account = account_key(username)
    if account:
        checks.append((account, cfg["LOGIN_MAX_FAILURES_PER_ACCOUNT"], window))
    return checks


# ---- The lifecycle of an attempt. Reserve BEFORE the password is checked, so that simultaneous requests cannot all pass the check before any is recorded:
#
#     sign in          begin_login_attempt -> refused (429, nothing recorded) | ticket
#                      wrong password / unknown name ......... settle_attempt   (it counts)
#                      correct password ...................... login_succeeded  (own events released; this address's earlier typos for this name forgiven)
#                      database or other server error ........ release_attempt  (it never happened)
#     change password  the same reservation (the "current password" field is a password check)
#                      wrong current password ................ settle_attempt
#                      anything else wrong with the form ..... release_attempt  (a weak or mismatched NEW password is not a guess at the old one)
#                      success ............................... login_succeeded;  server error: release_attempt
#     sign up          begin_registration -> refused | ticket
#                      created, or the name was taken ........ settle_attempt   (it reached the hash and the INSERT, which is what the limit is for)
#                      invalid form, or server error ......... release_attempt
def begin_login_attempt(username):
    """Reserve capacity for one sign-in or password check: (0, ticket), or (seconds to wait, None) when any limit refuses, with nothing recorded.
    The wait ends when enough of the oldest events have left the rolling window: a temporary cooldown, never a permanent lock."""
    return throttle().reserve(_login_checks(username))


def begin_registration():
    """Reserve capacity for one sign-up from this address: (0, ticket) or (seconds to wait, None)."""
    cfg = current_app.config
    return throttle().reserve([(f"reg:{client_address()}", cfg["REGISTER_MAX_PER_WINDOW"], cfg["REGISTER_WINDOW_SECONDS"])])


def settle_attempt(ticket):
    """The attempt counts (a wrong password; a sign-up that reached the database). Safe to call twice."""
    throttle().settle(ticket)


def release_attempt(ticket):
    """The attempt does not count (invalid form, server error): remove its own events. Safe to call twice, and a settled attempt cannot be released."""
    throttle().release(ticket)


def login_succeeded(ticket, username):
    """A correct password. Releases THIS attempt's own events, so a success never uses up the failed-attempt budget, and forgives the failures already settled
    for this address and username (the owner's own typos).

    Deliberately NOT reset: the account-wide counter and the address counter. They count guesses by everyone, and a correct password from the owner says nothing
    about anyone else's guesses: resetting them would hand an attacker a fresh budget every time the owner signs in, and (while requests are in flight) would erase
    their pending events. Pending events of other attempts are never forgiven either."""
    throttle().release(ticket, forgive=(throttle_keys(username)[0],))


def login_blocked_for(username):
    """A check that does not reserve: seconds this client would have to wait for this username (0 = may try). For tests and diagnostics; the routes call
    begin_login_attempt, which checks and reserves in one step."""
    return max((throttle().blocked_for(key, limit, window) for key, limit, window in _login_checks(username)), default=0)


def record_login_failure(username):
    """Record one settled failure on every sign-in key for `username`, with no check (tests and diagnostics)."""
    for key, _limit, window in _login_checks(username):
        throttle().record_failure(key, window)


def init_app(app):
    for name in ("LOGIN_MAX_FAILURES", "LOGIN_MAX_FAILURES_PER_ADDRESS", "LOGIN_MAX_FAILURES_PER_ACCOUNT", "REGISTER_MAX_PER_WINDOW"):
        if not 1 <= app.config[name] <= Throttle.MAX_PER_KEY:          # a key remembers at most MAX_PER_KEY events, so a larger limit could never be reached
            raise RuntimeError(f"{name} must be between 1 and {Throttle.MAX_PER_KEY}.")
    app.extensions["login_throttle"] = Throttle()
    app.before_request(protect_csrf)
    app.before_request(load_user)
    app.after_request(add_cache_headers)
    app.jinja_env.globals["csrf_token"] = csrf_token

    @app.context_processor
    def inject_user():
        return {"current_user": g.get("user")}
