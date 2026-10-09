"""Server-rendered pages. Phase 1 only has a simple homepage and a health check."""
from flask import Blueprint, jsonify, render_template

from ..db import DatabaseError
from ..services import system

main_bp = Blueprint("main", __name__)

DISCLAIMER = (
    "An unofficial educational fan project by Team Valkyrie. Not affiliated with, endorsed by, "
    "or sponsored by Rockstar Games or Take-Two Interactive."
)


@main_bp.app_context_processor
def inject_globals():
    return {"disclaimer": DISCLAIMER}


@main_bp.route("/")
def index():
    return render_template("index.html", stats=system.homepage_stats())


@main_bp.route("/health")
def health():
    try:
        return jsonify(system.health())
    except DatabaseError:
        return jsonify({"status": "error", "database": "unreachable"}), 503
