"""Configuration, read from environment variables (and a local .env file).

Nothing secret lives in the source code: copy .env.example to .env and edit it.
"""
import os
import re
import secrets
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def _int(name, default):
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return int(default)


def normalise_origin(value):
    """'HTTPS://Example.org/' -> 'https://example.org'; None unless it is a bare origin (http or https scheme, a host, no path, query, fragment or credentials)."""
    parts = urlsplit((value or "").strip().lower().rstrip("/"))
    if parts.scheme not in ("http", "https") or not parts.netloc or "@" in parts.netloc or parts.path or parts.query or parts.fragment:
        return None
    return f"{parts.scheme}://{parts.netloc}"


def parse_proxy_count(raw):
    """TV_TRUSTED_PROXIES: not set -> 0; a whole number written in plain digits -> that number; ANYTHING else (blank, 'abc', '1.5', '-1', '+2', '1 2') comes back
    unchanged as a string, which get_config() refuses. A typo must stop the site from starting, not quietly mean 'no proxies'."""
    if raw is None:
        return 0
    text = raw.strip()
    return int(text) if re.fullmatch(r"[0-9]{1,3}", text) else raw


def _origins(name):
    return tuple(item.strip() for item in os.getenv(name, "").split(",") if item.strip())


def _flag(name, default="0"):
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes", "on")


class Config:
    # Footage, the cast reel, the region explorer and the garage start by themselves. A visitor whose system asks
    # for reduced motion (or has data saver on) gets a Play button instead, unless this is set: then they autoplay
    # too, muted. A development setting only (a production run ignores it, see ProductionConfig). A visitor's own
    # choice in the menu (the Motion switch) always wins, in either direction.
    AUTOPLAY_ALWAYS = _flag("TV_AUTOPLAY_ALWAYS")
    # Signs the session cookie. A development run without SECRET_KEY gets a random key for this process only (so no well-known key ever exists
    # and sessions simply end when the server restarts). ProductionConfig does not fall back: see check_secret_key().
    SECRET_KEY = os.getenv("SECRET_KEY") or secrets.token_hex(32)
    # Sessions: a signed cookie holding only the user id, the time of sign-in and the CSRF token. Never readable by scripts, never sent on cross-site requests.
    SESSION_COOKIE_NAME = "tv_session"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False       # True in ProductionConfig (a cookie marked Secure is not sent over plain http)
    SESSION_REFRESH_EACH_REQUEST = False
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)    # the longest a sign-in lasts, however busy the visitor is
    # Login throttle (in-process; see app/security.py): failures allowed per username+address and per address within the window.
    LOGIN_MAX_FAILURES = 5
    LOGIN_MAX_FAILURES_PER_ADDRESS = 20
    LOGIN_MAX_FAILURES_PER_ACCOUNT = 50      # per username, from ALL addresses together (a guessing run spread over many addresses); same window
    LOGIN_WINDOW_SECONDS = 600
    # Registration: successful or name-taken sign-ups allowed per client address within the window (the same in-process counter).
    REGISTER_MAX_PER_WINDOW = 10
    REGISTER_WINDOW_SECONDS = 3600
    # Every form on the site is tiny (a password is at most 128 characters): anything larger is refused with 413 before it is read into memory.
    MAX_CONTENT_LENGTH = 16 * 1024
    MAX_FORM_MEMORY_SIZE = 16 * 1024
    # Where the site is reached from. TV_PUBLIC_ORIGINS: comma-separated origins (scheme://host[:port]) that may submit its forms; the CSRF check compares the
    # Origin header with these and never with the (client-supplied) Host header. Unset in development/testing: the origin of the request itself is used.
    # REQUIRED, and https only, in production. TV_TRUSTED_PROXIES: how many reverse proxies sit in front (0 = none). Only then are X-Forwarded-For/-Proto read
    # (ProxyFix), from the right-hand end of the list; the proxy must overwrite, not append to, whatever the client sent.
    PUBLIC_ORIGINS = _origins("TV_PUBLIC_ORIGINS")
    TRUSTED_PROXY_COUNT = parse_proxy_count(os.getenv("TV_TRUSTED_PROXIES"))
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = _int("DB_PORT", 3306)
    DB_NAME = os.getenv("DB_NAME", "gta6_vi")
    DB_USER = os.getenv("DB_USER", "valkyrie_app")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    # Separate account used ONLY by scripts that create/drop tables (never by the running site).
    MIGRATE_DB_USER = os.getenv("MIGRATE_DB_USER", "valkyrie_migrator")
    MIGRATE_DB_PASSWORD = os.getenv("MIGRATE_DB_PASSWORD", "")
    DB_POOL_SIZE = 5
    TESTING = False

    @classmethod
    def db_kwargs(cls):
        """Arguments for mysql.connector.connect(). Strict mode and utf8mb4 are explicit."""
        return {
            "host": cls.DB_HOST,
            "port": cls.DB_PORT,
            "database": cls.DB_NAME,
            "user": cls.DB_USER,
            "password": cls.DB_PASSWORD,
            "charset": "utf8mb4",
            "collation": "utf8mb4_0900_ai_ci",
            "sql_mode": "STRICT_ALL_TABLES,NO_ENGINE_SUBSTITUTION,ONLY_FULL_GROUP_BY",
            "use_pure": True,
            "connection_timeout": 5,
        }

    @classmethod
    def migration_kwargs(cls):
        """Same as db_kwargs() but for the schema-changing account."""
        kwargs = cls.db_kwargs()
        kwargs["user"] = cls.MIGRATE_DB_USER
        kwargs["password"] = cls.MIGRATE_DB_PASSWORD
        return kwargs


class DevelopmentConfig(Config):
    pass


class ProductionConfig(DevelopmentConfig):
    """A deployed site always respects a visitor's system setting for reduced motion: TV_AUTOPLAY_ALWAYS (a development convenience) is ignored here."""

    AUTOPLAY_ALWAYS = False
    SECRET_KEY = os.getenv("SECRET_KEY")       # no fallback: get_config("production") refuses to start without a real one
    SESSION_COOKIE_SECURE = True


class TestingConfig(Config):
    """Uses the separate *_test database so tests can never touch real data."""

    TESTING = True
    DB_NAME = os.getenv("TEST_DB_NAME", "gta6_vi_test")
    PUBLIC_ORIGINS = ()            # tests do not depend on the machine's environment
    TRUSTED_PROXY_COUNT = 0
    AUTOPLAY_ALWAYS = False        # a developer's TV_AUTOPLAY_ALWAYS=1 (a development convenience) must not leak into tests or QA runs


# Values that have appeared in this project's files or are obvious placeholders: never acceptable as a production secret.
KNOWN_INSECURE_SECRETS = frozenset({"dev-only-insecure-key", "replace-with-a-long-random-string", "change-me", "changeme", "secret", "dev", "development"})
MIN_SECRET_LENGTH = 32
MIN_SECRET_DISTINCT = 10          # a sanity check against 'aaaa...' and 'abababab...', not a proof of randomness (token_hex(32) has about 16 distinct characters)
ENVIRONMENTS = ("development", "production", "testing")
MAX_TRUSTED_PROXIES = 5


def check_secret_key(secret):
    """Raise RuntimeError unless `secret` can safely sign production sessions. Never includes the value in the message."""
    if not secret:
        raise RuntimeError("Refusing to start in production: SECRET_KEY is not set. Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\"")
    if secret.strip().lower() in KNOWN_INSECURE_SECRETS:
        raise RuntimeError("Refusing to start in production: SECRET_KEY is a known development or placeholder value.")
    if len(secret) < MIN_SECRET_LENGTH:
        raise RuntimeError(f"Refusing to start in production: SECRET_KEY must be at least {MIN_SECRET_LENGTH} characters long.")
    if len(set(secret)) < MIN_SECRET_DISTINCT:
        raise RuntimeError("Refusing to start in production: SECRET_KEY is too repetitive to be random. Generate one with secrets.token_hex(32).")


def check_origins(origins, require_https=False, required=False):
    """Raise RuntimeError for a malformed TV_PUBLIC_ORIGINS (and, for production, a missing or non-https one)."""
    if required and not origins:
        raise RuntimeError("Refusing to start in production: TV_PUBLIC_ORIGINS is not set. List the public origin(s) of the site, e.g. https://valkyrie.example.org")
    for origin in origins:
        clean = normalise_origin(origin)
        if clean is None:
            raise RuntimeError("TV_PUBLIC_ORIGINS must list bare origins like https://example.org (a scheme and a host, no path); one entry is not valid.")
        if require_https and not clean.startswith("https://"):
            raise RuntimeError("Refusing to start in production: TV_PUBLIC_ORIGINS must use https (the session cookie is marked Secure).")


def deployment_config_name(environ=None):
    """The configuration name for the WSGI entry point (wsgi.py), which both `flask --app wsgi run` and a production server import.

    FLASK_ENV set  -> that value, unchanged (get_config() then accepts production/development/testing and refuses anything else, blank included).
    FLASK_ENV unset, started by the Flask command line (it sets FLASK_RUN_FROM_CLI) -> "development": the documented local run needs no setup.
    FLASK_ENV unset, started any other way (gunicorn, waitress, mod_wsgi, a bare import) -> an error. That is how a deployment that forgot FLASK_ENV
    used to start quietly with development settings (a random per-process key, a cookie without Secure, the request's own host as the allowed origin).
    The message names the setting, never a value."""
    environ = os.environ if environ is None else environ
    requested = environ.get("FLASK_ENV")
    if requested is not None:
        return requested
    if environ.get("FLASK_RUN_FROM_CLI") == "true":
        return "development"
    raise RuntimeError("Refusing to start: FLASK_ENV is not set. A deployment must set FLASK_ENV=production (see docs/ACCOUNTS.md, 'Production settings'); "
                       "to run on your own computer use FLASK_ENV=development, or start the site with `python -m flask --app wsgi run`.")


def get_config(name=None):
    """The configuration class for `name`, or for FLASK_ENV (development when it is not set at all). An unrecognised name is an error, never a quiet
    fall-back to development: a typo such as FLASK_ENV=prod must not start the site with development settings."""
    requested = name if name is not None else os.getenv("FLASK_ENV", "development")
    environment = (requested or "").strip().lower()
    if environment not in ENVIRONMENTS:
        raise RuntimeError(f"Unknown configuration {requested!r}: FLASK_ENV must be one of {', '.join(ENVIRONMENTS)}.")
    config = {"testing": TestingConfig, "production": ProductionConfig, "development": DevelopmentConfig}[environment]
    if config is TestingConfig and not config.DB_NAME.endswith("_test"):
        raise RuntimeError("Refusing to run tests: TEST_DB_NAME must end with '_test'.")
    if config is DevelopmentConfig and config.DB_NAME.endswith("_test"):
        raise RuntimeError("DB_NAME must not be the test database.")
    proxies = config.TRUSTED_PROXY_COUNT
    if not isinstance(proxies, int) or isinstance(proxies, bool):
        raise RuntimeError(f"TV_TRUSTED_PROXIES must be a whole number between 0 and {MAX_TRUSTED_PROXIES} (digits only); it is not.")
    if not 0 <= proxies <= MAX_TRUSTED_PROXIES:
        raise RuntimeError(f"TV_TRUSTED_PROXIES must be between 0 and {MAX_TRUSTED_PROXIES}.")
    check_origins(config.PUBLIC_ORIGINS)
    if config is ProductionConfig:
        if config.DB_NAME.endswith("_test") or config.DB_NAME == TestingConfig.DB_NAME:
            raise RuntimeError("Refusing to start in production: DB_NAME is a test database.")
        check_secret_key(config.SECRET_KEY)
        check_origins(config.PUBLIC_ORIGINS, require_https=True, required=True)
    return config
