"""The homepage, about and credits pages, locally built media, and the health check."""
from flask import Blueprint, abort, jsonify, render_template, request, send_from_directory, url_for

from .. import local_media
from ..db import DatabaseError
from ..services import site, system

main_bp = Blueprint("main", __name__)

DISCLAIMER = (
    "An unofficial educational fan project by Team Valkyrie. "
    "Not affiliated with or endorsed by Rockstar Games or Take-Two Interactive."
)

# (endpoints that belong to the section, label). The first endpoint is the link target.
NAV = (
    (("pages.characters", "pages.character_detail"), "Characters"),
    (("pages.vehicles", "pages.vehicle_detail"), "Garage"),
    (("pages.regions", "pages.region_detail"), "Leonida"),
    (("pages.locations", "pages.location_detail"), "Locations"),
    (("pages.missions", "pages.mission_detail"), "Stories"),
)


def page_url(number):
    """Current address with only the page number changed, so filters and sorting are kept."""
    params = {**(request.view_args or {}), **request.args.to_dict(), "page": number}
    return url_for(request.endpoint, **params)


def page_window(page, pages, radius=2):
    """Page numbers to show: first, last and a window around the current page. None marks a gap."""
    keep = sorted({1, pages} | set(range(max(1, page - radius), min(pages, page + radius) + 1)))
    window, previous = [], 0
    for number in keep:
        if number - previous > 1:
            window.append(None)
        window.append(number)
        previous = number
    return window


def media_file_url(relative):
    """Address of a locally built clip, or None when it is not there."""
    return url_for("main.media_file", filename=relative) if local_media.is_servable(relative) else None


@main_bp.app_context_processor
def inject_globals():
    return {"disclaimer": DISCLAIMER, "nav_items": NAV}


@main_bp.route("/")
def index():
    return render_template("home.html", **site.home())


@main_bp.route("/about")
def about():
    return render_template("about.html")


@main_bp.route("/credits")
def credits():
    return render_template("credits.html")


@main_bp.route("/media/<path:filename>")
def media_file(filename):
    """Serve a locally built clip. Anything that is not clips/<safe-name>.mp4 or .jpg is a 404."""
    if not local_media.is_servable(filename):
        abort(404)
    return send_from_directory(local_media.root(), filename, max_age=3600, conditional=True)


@main_bp.route("/health")
def health():
    try:
        return jsonify(system.health())
    except DatabaseError:
        return jsonify({"status": "error", "database": "unreachable"}), 503
