"""The homepage, about and credits pages, locally built media, and the health check."""
from flask import Blueprint, abort, current_app, jsonify, render_template, request, send_from_directory, url_for

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
    (("pages.music",), "Music"),
    (("pages.media",), "Media"),
)


def page_url(number, anchor=None):
    """Current address with only the page number changed, so filters and sorting are kept. `anchor` names an element id to land on."""
    params = {**(request.view_args or {}), **request.args.to_dict(), "page": number}
    if anchor:
        params["_anchor"] = anchor
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
    """Serve a locally built clip, moment or hero layer. Anything outside clips/, cinematic/ and hero/ safe names is a 404."""
    if not local_media.is_servable(filename):
        abort(404)
    return send_from_directory(local_media.root(), filename, max_age=3600, conditional=True)


@main_bp.route("/health")
def health():
    """Is the site up and the database reachable? Public, so it says only that: no server version, address, account or error text."""
    try:
        return jsonify(system.health())
    except DatabaseError as error:
        current_app.logger.warning("Health check: the database could not be reached: %s", error)      # the reason goes to the server log only, never to the visitor
        return jsonify({"status": "error", "database": "unreachable"}), 503
