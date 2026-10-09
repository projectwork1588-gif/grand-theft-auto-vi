"""The homepage and the health check."""
from flask import Blueprint, jsonify, render_template, request, url_for

from ..db import DatabaseError
from ..services import site, system

main_bp = Blueprint("main", __name__)

DISCLAIMER = (
    "An unofficial educational fan project by Team Valkyrie. Not affiliated with, endorsed by, "
    "or sponsored by Rockstar Games or Take-Two Interactive."
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


@main_bp.app_context_processor
def inject_globals():
    return {"disclaimer": DISCLAIMER, "nav_items": NAV}


@main_bp.route("/")
def index():
    return render_template("home.html", **site.home())


@main_bp.route("/health")
def health():
    try:
        return jsonify(system.health())
    except DatabaseError:
        return jsonify({"status": "error", "database": "unreachable"}), 503
