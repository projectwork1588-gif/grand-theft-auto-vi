"""JSON API (version 1). Routes stay thin: parse the request, call a service, return JSON."""
from flask import Blueprint, jsonify, request

from ..services import characters, regions

api_bp = Blueprint("api", __name__)


@api_bp.route("/characters")
def list_characters():
    return jsonify(characters.list_characters(request.args))


@api_bp.route("/characters/<slug>")
def character_detail(slug):
    return jsonify(characters.get_character(slug))


@api_bp.route("/regions")
def list_regions():
    return jsonify(regions.list_regions(request.args))


@api_bp.route("/regions/<slug>")
def region_detail(slug):
    return jsonify(regions.get_region(slug))
