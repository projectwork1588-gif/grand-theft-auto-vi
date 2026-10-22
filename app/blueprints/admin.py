"""The admin area: Stories (missions) with the people, vehicles and places they link to, and Places (locations) with the region they belong to. Administrators only.

Every route carries @security.admin_required (tests/test_admin_authz.py fails if one does not). Every state-changing route is a POST that passes the CSRF check in
app/security.py. The administrator is the signed-in user from the session; no route takes a user id, a role or a redirect address from the request.
"""
from flask import Blueprint, flash, g, make_response, redirect, render_template, request, url_for

from .. import security
from ..services import admin_places as places, admin_stories as stories, validation as v

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

TYPE_CHOICES = [(t, t.capitalize()) for t in v.MISSION_TYPES]
DEFAULTS = {"mission_type": "side", "content_status": "demo"}
PLACE_TYPE_CHOICES = [(t, t.capitalize()) for t in v.LOCATION_TYPES]
PLACE_DEFAULTS = {"location_type": "district", "content_status": "demo"}


def _to(endpoint, **values):
    return redirect(url_for(endpoint, **values), code=303)        # 303: a refresh after a change does not repeat it


def _form_page(status=200, **context):
    context.setdefault("primary_location", next((s for s, is_primary in context["selection"]["locations"].items() if is_primary), ""))
    return make_response(render_template("admin/story_form.html", options=stories.options(), type_choices=TYPE_CHOICES, **context), status)


@admin_bp.get("")
@security.admin_required
def dashboard():
    return render_template("admin/dashboard.html", stats=stories.dashboard())


@admin_bp.get("/stories")
@security.admin_required
def story_list():
    return render_template("admin/stories_list.html", mission_types=v.MISSION_TYPES, **stories.list_stories(request.args))


@admin_bp.route("/stories/new", methods=["GET", "POST"])
@security.admin_required
def story_new():
    if request.method == "GET":
        return _form_page(creating=True, slug=None, values=DEFAULTS, selection={"characters": {}, "vehicles": {}, "locations": {}}, errors={})
    try:
        stories.create(request.form, g.user)
    except stories.StoryFormError as error:
        selection = stories.selection_from_form(request.form)
        return _form_page(error.status, creating=True, slug=None, values=request.form, selection=selection, errors=error.errors,
                          primary_location=(request.form.get("primary_location") or "").strip())
    flash("The story was created.", "success")
    return _to("admin.story_list", q=(request.form.get("title") or "").strip())


@admin_bp.route("/stories/<slug>/edit", methods=["GET", "POST"])
@security.admin_required
def story_edit(slug):
    if request.method == "GET":
        story, selection = stories.load_for_edit(slug)
        return _form_page(creating=False, slug=slug, values=story, selection=selection, errors={})
    try:
        stories.update(slug, request.form, g.user)
    except stories.StoryFormError as error:
        selection = stories.selection_from_form(request.form)
        return _form_page(error.status, creating=False, slug=slug, values=request.form, selection=selection, errors=error.errors,
                          primary_location=(request.form.get("primary_location") or "").strip())
    flash("The story was saved.", "success")
    return _to("admin.story_list", q=(request.form.get("title") or "").strip())


@admin_bp.route("/stories/<slug>/delete", methods=["GET", "POST"])
@security.admin_required
def story_delete(slug):
    if request.method == "GET":
        story, impact = stories.load_for_delete(slug)
        return render_template("admin/story_delete.html", story=story, impact=impact)
    title = stories.delete(slug, g.user)
    flash(f"{title} was deleted.", "info")
    return _to("admin.story_list")


# ------------------------------------------------------------------ Places
def _place_form_page(status=200, **context):
    region_choices = [("", "Choose a region")] + [(r["slug"], r["name"]) for r in places.options()["regions"]]
    return make_response(render_template("admin/place_form.html", region_choices=region_choices, type_choices=PLACE_TYPE_CHOICES, **context), status)


def _place_values(place):
    """The form values of a stored place: the form names the region by its slug."""
    return {**place, "region": place["region_slug"]}


@admin_bp.get("/places")
@security.admin_required
def place_list():
    return render_template("admin/places_list.html", location_types=v.LOCATION_TYPES, regions=places.options()["regions"], **places.list_places(request.args))


@admin_bp.route("/places/new", methods=["GET", "POST"])
@security.admin_required
def place_new():
    if request.method == "GET":
        return _place_form_page(creating=True, slug=None, values=PLACE_DEFAULTS, errors={})
    try:
        places.create(request.form, g.user)
    except places.PlaceFormError as error:
        return _place_form_page(error.status, creating=True, slug=None, values=request.form, errors=error.errors)
    flash("The place was created.", "success")
    return _to("admin.place_list", q=(request.form.get("name") or "").strip())


@admin_bp.route("/places/<slug>/edit", methods=["GET", "POST"])
@security.admin_required
def place_edit(slug):
    if request.method == "GET":
        place = places.load_for_edit(slug)
        return _place_form_page(creating=False, slug=slug, values=_place_values(place), errors={})
    try:
        places.update(slug, request.form, g.user)
    except places.PlaceFormError as error:
        return _place_form_page(error.status, creating=False, slug=slug, values=request.form, errors=error.errors)
    flash("The place was saved.", "success")
    return _to("admin.place_list", q=(request.form.get("name") or "").strip())


@admin_bp.route("/places/<slug>/delete", methods=["GET", "POST"])
@security.admin_required
def place_delete(slug):
    if request.method == "GET":
        place, impact, residents = places.load_for_delete(slug)
        return render_template("admin/place_delete.html", place=place, impact=impact, residents=residents)
    name = places.delete(slug, g.user)
    flash(f"{name} was deleted.", "info")
    return _to("admin.place_list")
