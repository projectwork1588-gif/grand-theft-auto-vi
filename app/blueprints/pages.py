"""Server-rendered catalogue and detail pages. Each route: read the request, call a service, render a template."""
from flask import Blueprint, redirect, render_template, request, url_for

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
    return render_template("vehicles/concept.html", **site.vehicle_concept(request.args))


@pages_bp.route("/garage-concept")
def garage_concept():
    """The Garage's old prototype address, kept so earlier links still work: it goes to /vehicles with the query string unchanged."""
    query = request.query_string.decode("utf-8", "replace")
    return redirect(url_for("pages.vehicles") + ("?" + query if query else ""), code=301)


@pages_bp.route("/vehicles/<slug>")
def vehicle_detail(slug):
    return render_template("vehicles/detail.html", vehicle=site.vehicle_detail(slug))


@pages_bp.route("/regions")
def regions():
    return render_template("regions/index.html", **site.region_index(request.args))


@pages_bp.route("/regions/<slug>")
def region_detail(slug):
    return render_template("regions/detail.html", region=site.region_detail(slug))


@pages_bp.route("/music")
def music():
    return render_template("music/index.html", **site.music_page())


@pages_bp.route("/media")
def media():
    return render_template("media/index.html", **site.media_page())


@pages_bp.route("/locations")
def locations():
    """The old Places index. Its places were Team Valkyrie's own, not Rockstar's, so the section is now the Music page; the places themselves, their pages (/locations/<slug>, which
    the stories and characters that use them still link to) and the API are untouched. The old filters (q, region, type, sort, page) mean nothing on the Music page and are dropped."""
    return redirect(url_for("pages.music"), code=302)


@pages_bp.route("/locations/<slug>")
def location_detail(slug):
    return render_template("locations/detail.html", location=site.location_detail(slug))


@pages_bp.route("/missions")
def missions():
    return render_template("missions/index.html", **site.mission_index(request.args))


@pages_bp.route("/missions/<slug>")
def mission_detail(slug):
    return render_template("missions/detail.html", mission=site.mission_detail(slug))
