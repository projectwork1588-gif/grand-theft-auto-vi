"""Application factory: builds and configures the Flask app."""
from flask import Flask

from . import db
from .config import get_config
from .errors import register_error_handlers


def create_app(config_name=None):
    app = Flask(__name__)
    config = get_config(config_name)
    app.config.from_object(config)
    app.config["DB_CONFIG"] = config  # used by app.db to build the connection pool
    app.json.sort_keys = False  # keep JSON fields in the order the code wrote them

    db.init_app(app)
    register_error_handlers(app)

    from .blueprints.api import api_bp
    from .blueprints.main import main_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix="/api/v1")
    return app
