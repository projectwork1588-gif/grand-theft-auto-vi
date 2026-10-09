"""Server-rendered catalogue and detail pages. Each route: read the request, call a service, render a template."""
from flask import Blueprint, render_template, request

from ..services import site

pages_bp = Blueprint("pages", __name__)


@pages_bp.route("/characters")
def characters():
    return render_template("characters/index.html", **site.character_index(request.args))


@pages_bp.route("/characters/<slug>")
def character_detail(slug):
    return render_template("characters/detail.html", character=site.character_detail(slug))


@pages_bp.route("/vehicles")
def vehicles():
    return render_template("vehicles/index.html", **site.vehicle_index(request.args))


@pages_bp.route("/vehicles/<slug>")
def vehicle_detail(slug):
    return render_template("vehicles/detail.html", vehicle=site.vehicle_detail(slug))


@pages_bp.route("/regions")
def regions():
    return render_template("regions/index.html", **site.region_index(request.args))


@pages_bp.route("/regions/<slug>")
def region_detail(slug):
    return render_template("regions/detail.html", region=site.region_detail(slug))


@pages_bp.route("/locations")
def locations():
    return render_template("locations/index.html", **site.location_index(request.args))


@pages_bp.route("/locations/<slug>")
def location_detail(slug):
    return render_template("locations/detail.html", location=site.location_detail(slug))


@pages_bp.route("/missions")
def missions():
    return render_template("missions/index.html", **site.mission_index(request.args))


@pages_bp.route("/missions/<slug>")
def mission_detail(slug):
    return render_template("missions/detail.html", mission=site.mission_detail(slug))
