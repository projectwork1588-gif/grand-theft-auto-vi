"""Accounts, sessions and CSRF: the parts every state-changing request passes through.

* Sessions are Flask's signed cookie. It holds the user id, the time of sign-in, a stamp of the password (see password_stamp) and the CSRF token, and nothing else.
* CSRF uses the synchronizer-token pattern: a random token lives in the session, every form carries it, and every POST/PUT/PATCH/DELETE must send the same one
  (compared in constant time). Registration and login are covered too. SameSite=Lax and a same-origin check are a second layer.
* The login throttle is an in-process counter. It does NOT coordinate several worker processes or survive a restart (see docs/ACCOUNTS.md).
"""
import hashlib
import hmac
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
class Throttle:
    """Counts events (failed logins, registrations) per key in a sliding window. In-process and thread-safe.

    Memory is bounded in three ways: a key's list never holds more than MAX_PER_KEY timestamps, a key is forgotten once all its timestamps have left
    the window, and the table never holds more than MAX_KEYS keys. At the cap, expired keys go first; if the table is still full, the keys with the
    FEWEST recent events (oldest first) are evicted. Counters are never cleared wholesale, so a key that has reached its limit stays blocked while
    other keys are being flooded. Each key remembers the window it was recorded with (logins use minutes, registrations an hour)."""

    MAX_KEYS = 10000
    MAX_PER_KEY = 100

    def __init__(self, clock=time.monotonic):
        self._clock = clock
        self._lock = threading.Lock()
        self._failures = {}
        self._windows = {}

    def _recent(self, key, window):
        now = self._clock()
        kept = [t for t in self._failures.get(key, ()) if now - t < window]
        if kept:
            self._failures[key] = kept
        else:
            self._failures.pop(key, None)
            self._windows.pop(key, None)
        return kept

    def blocked_for(self, key, limit, window):
        """Seconds until `key` may try again, or 0 when it may try now."""
        with self._lock:
            recent = self._recent(key, window)
            if len(recent) < limit:
                return 0
            return max(1, int(window - (self._clock() - recent[0])) + 1)

    def _make_room(self):
        for key in list(self._failures):                           # first, forget what has expired
            self._recent(key, self._windows[key])
        if len(self._failures) >= self.MAX_KEYS:                   # still full: drop the least valuable 1 percent (fewest events, then oldest)
            ranked = sorted(self._failures, key=lambda k: (len(self._failures[k]), self._failures[k][-1]))
            for key in ranked[:max(1, self.MAX_KEYS // 100)]:
                del self._failures[key]
                del self._windows[key]

    def record_failure(self, key, window):
        with self._lock:
            if key not in self._failures and len(self._failures) >= self.MAX_KEYS:
                self._make_room()
            self._windows[key] = window
            events = self._failures.setdefault(key, [])
            events.append(self._clock())
            del events[:-self.MAX_PER_KEY]

    def clear(self, key=None):
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


def login_blocked_for(username):
    cfg = current_app.config
    window = cfg["LOGIN_WINDOW_SECONDS"]
    by_user, by_address = throttle_keys(username)
    return max(throttle().blocked_for(by_user, cfg["LOGIN_MAX_FAILURES"], window),
               throttle().blocked_for(by_address, cfg["LOGIN_MAX_FAILURES_PER_ADDRESS"], window))


def record_login_failure(username):
    window = current_app.config["LOGIN_WINDOW_SECONDS"]
    for key in throttle_keys(username):
        throttle().record_failure(key, window)


def clear_login_failures(username):
    throttle().clear(throttle_keys(username)[0])


def register_blocked_for():
    """Seconds until this address may create another account (0 = now). The same in-process counter, one key per address."""
    cfg = current_app.config
    return throttle().blocked_for(f"reg:{client_address()}", cfg["REGISTER_MAX_PER_WINDOW"], cfg["REGISTER_WINDOW_SECONDS"])


def record_registration():
    throttle().record_failure(f"reg:{client_address()}", current_app.config["REGISTER_WINDOW_SECONDS"])


def init_app(app):
    app.extensions["login_throttle"] = Throttle()
    app.before_request(protect_csrf)
    app.before_request(load_user)
    app.after_request(add_cache_headers)
    app.jinja_env.globals["csrf_token"] = csrf_token

    @app.context_processor
    def inject_user():
        return {"current_user": g.get("user")}
