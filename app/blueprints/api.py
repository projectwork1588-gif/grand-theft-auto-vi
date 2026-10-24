"""JSON API (version 1). Routes stay thin: parse the request, call a service, return JSON."""
from flask import Blueprint, jsonify, request

from ..services import characters, locations, missions, regions, search, vehicles

api_bp = Blueprint("api", __name__)


@api_bp.route("/characters")
def list_characters():
    return jsonify(characters.list_characters(request.args, characters.wants_original(request.args)))


@api_bp.route("/characters/<slug>")
def character_detail(slug):
    return jsonify(characters.get_character(slug, characters.wants_original(request.args)))


@api_bp.route("/regions")
def list_regions():
    return jsonify(regions.list_regions(request.args))


@api_bp.route("/regions/<slug>")
def region_detail(slug):
    return jsonify(regions.get_region(slug))


# ----- Phase 2 additions (the four routes above are unchanged) -----
@api_bp.route("/vehicles")
def list_vehicles():
    return jsonify(vehicles.list_vehicles(request.args))


@api_bp.route("/vehicles/<slug>")
def vehicle_detail(slug):
    return jsonify(vehicles.get_vehicle(slug))


@api_bp.route("/vehicle-categories")
def list_vehicle_categories():
    return jsonify(vehicles.list_categories(request.args))


@api_bp.route("/missions")
def list_missions():
    return jsonify(missions.list_missions(request.args))


@api_bp.route("/missions/<slug>")
def mission_detail(slug):
    return jsonify(missions.get_mission(slug))


@api_bp.route("/locations")
def list_locations():
    return jsonify(locations.list_locations(request.args))


@api_bp.route("/locations/<slug>")
def location_detail(slug):
    return jsonify(locations.get_location(slug))


@api_bp.route("/search")
def search_site():
    """The few best matches for the command palette (Stage 4B). Public, read-only, one database query."""
    return jsonify(search.api_search(request.args))
