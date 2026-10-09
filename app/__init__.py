"""Application factory: builds and configures the Flask app."""
from flask import Flask

from . import db, media_urls
from .config import get_config
from .errors import register_error_handlers

# Only our own files, Rockstar's official image/player host, and Google Fonts. No inline scripts or styles.
CONTENT_SECURITY_POLICY = (
    "default-src 'self'; "
    "img-src 'self' https://www.rockstargames.com data:; "
    "frame-src https://www.rockstargames.com; "
    "style-src 'self' https://fonts.googleapis.com; "
    "font-src https://fonts.gstatic.com; "
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
    app.json.sort_keys = False  # keep JSON fields in the order the code wrote them

    db.init_app(app)
    register_error_handlers(app)

    app.jinja_env.globals.update(
        image_src=media_urls.image_src,
        image_srcset=media_urls.image_srcset,
        player_src=media_urls.player_src,
        status_labels=STATUS_LABELS,
    )

    @app.after_request
    def security_headers(response):
        response.headers.setdefault("Content-Security-Policy", CONTENT_SECURITY_POLICY)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        return response

    from .blueprints.api import api_bp
    from .blueprints.main import main_bp, page_url, page_window
    from .blueprints.pages import pages_bp

    # Globals (not context values) so imported macros such as the pager can use them.
    app.jinja_env.globals.update(page_url=page_url, page_window=page_window)

    app.register_blueprint(main_bp)
    app.register_blueprint(pages_bp)
    app.register_blueprint(api_bp, url_prefix="/api/v1")
    return app
