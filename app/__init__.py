"""Application factory: builds and configures the Flask app."""
import logging
import os

from flask import Flask, g, request
from werkzeug.middleware.proxy_fix import ProxyFix

from . import db, media_slots, media_urls, security
from .config import get_config
from .errors import register_error_handlers

# Only our own files, Rockstar's official image and player host, and YouTube's embedded player (privacy-enhanced
# domain) inside the trailer dialog. No third-party scripts. Fonts are bundled. No inline scripts or styles.
CONTENT_SECURITY_POLICY = (
    "default-src 'self'; "
    "img-src 'self' https://www.rockstargames.com data:; "
    "media-src 'self'; "
    "frame-src https://www.rockstargames.com https://www.youtube-nocookie.com; "
    "style-src 'self'; "
    "font-src 'self'; "
    "script-src 'self'; connect-src 'self'; object-src 'none'; "
    "base-uri 'self'; form-action 'self'; frame-ancestors 'self'"
)

# Shown on every card and page. The database values stay official / fan / demo.
STATUS_LABELS = {
    "official": "Official",
    "fan": "Fan view",
    "demo": "Concept",
}


def create_app(config_name=None):
    app = Flask(__name__)
    config = get_config(config_name)
    app.config.from_object(config)
    app.config["DB_CONFIG"] = config  # used by app.db to build the connection pool
    app.config["CONFIG_NAME"] = config.__name__
    if app.logger.level == logging.NOTSET:
        app.logger.setLevel(logging.INFO)       # the default (WARNING) would hide the line below; an operator who set a level of their own keeps it
    # One line an operator can look for. Only facts that are safe to print: which configuration, and yes/no or counts. Never the secret key, the database name,
    # user or password, or the origin addresses themselves.
    app.logger.info("Starting with %s (secure session cookie: %s, public origins configured: %d, trusted proxies: %d)", config.__name__,
                    "yes" if app.config["SESSION_COOKIE_SECURE"] else "no", len(app.config["PUBLIC_ORIGINS"]), app.config["TRUSTED_PROXY_COUNT"])
    if config_name is None and config.__name__ == "DevelopmentConfig" and os.getenv("FLASK_ENV") is None and os.getenv("FLASK_RUN_FROM_CLI") != "true":
        # create_app() called directly (wsgi.py refuses this case outright) with FLASK_ENV unset: say so where an operator will see it.
        app.logger.warning("FLASK_ENV is not set, so this is running with DEVELOPMENT settings. A deployment must set FLASK_ENV=production.")
    if app.config["TRUSTED_PROXY_COUNT"]:
        # Only when the operator says how many reverse proxies are in front (TV_TRUSTED_PROXIES): client address and scheme are then read from the proxies' headers.
        # Never enabled by default, and the Host header is never taken from a forwarded header.
        count = app.config["TRUSTED_PROXY_COUNT"]
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=count, x_proto=count, x_host=0, x_port=0, x_prefix=0)
    app.json.sort_keys = False  # keep JSON fields in the order the code wrote them

    db.init_app(app)
    register_error_handlers(app)
    security.init_app(app)   # sessions, CSRF protection, the signed-in user (g.user) and the login throttle

    app.jinja_env.globals.update(
        image_src=media_urls.image_src,
        image_srcset=media_urls.image_srcset,
        player_src=media_urls.player_src,
        status_labels=STATUS_LABELS,
        focus_for=lambda slug: media_slots.FOCUS.get(slug, "center"),
    )

    @app.after_request
    def security_headers(response):
        response.headers.setdefault("Content-Security-Policy", CONTENT_SECURITY_POLICY)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        # HSTS tells a browser to use https for this host from now on. Only when the production config asks for it AND this very request came over https
        # (request.is_secure reads the proxy's scheme header only when TV_TRUSTED_PROXIES says a proxy is there, so a client cannot fake it). No includeSubDomains, no preload.
        max_age = app.config.get("HSTS_MAX_AGE", 0)
        if max_age and request.is_secure:
            response.headers.setdefault("Strict-Transport-Security", f"max-age={max_age}")
        return response

    from .blueprints.account import account_bp
    from .blueprints.admin import admin_bp
    from .blueprints.api import api_bp
    from .blueprints.main import main_bp, media_file_url, page_url, page_window
    from .blueprints.pages import pages_bp

    # Globals (not context values) so imported macros such as the pager can use them.
    app.jinja_env.globals.update(page_url=page_url, page_window=page_window, media_file_url=media_file_url)

    def is_saved(kind, slug):
        """True when the signed-in visitor has saved this record (one query, only for signed-in visitors)."""
        from .services import favourites
        return bool(g.get("user")) and favourites.is_saved(g.user["user_id"], kind, slug)

    app.jinja_env.globals["is_saved"] = is_saved

    app.register_blueprint(main_bp)
    app.register_blueprint(pages_bp)
    app.register_blueprint(account_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp, url_prefix="/api/v1")
    return app
