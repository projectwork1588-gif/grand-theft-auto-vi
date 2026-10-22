"""The rules for managing Places (the locations table) from the admin area: validation, the region choice, the official-content guards, and turning database errors
into form errors. The same pattern as admin_stories.

No Flask request handling and no SQL here (SQL is in repositories/admin_locations.py). Official-source places are read-only at every level: the form can only choose
'fan' or 'demo', this service refuses to load an official place for editing, and the repository refuses to write one even when called directly. A place that an
official character lives at cannot be deleted (it would blank that character's home).
"""
import mysql.connector
from flask import current_app
from werkzeug.exceptions import Conflict, Forbidden, NotFound

from ..repositories import admin_locations as repo, locations as locations_repo
from ..repositories.admin_stories import NotEditable, WRITABLE_STATUSES
from . import locations as locations_service, validation as v
from .admin_forms import DUPLICATE_ENTRY, FOREIGN_KEY_FAILED, SOURCE_MAX, clean_source_url, clean_text, slugify

NAME_MIN, NAME_MAX = 3, 100
SUMMARY_MAX = 255
# 3000 characters, as for a story's synopsis. A place form has far fewer fields than a story form (no link lists), so even a description of this length with
# typographic punctuation stays well under the site's 16 KiB request limit, which is therefore not changed (measured in tests/test_admin_places_validation.py).
DESCRIPTION_MAX = 3000

OFFICIAL_EDIT = "Official places come from Rockstar's own material and cannot be edited here."
OFFICIAL_DELETE = "Official places come from Rockstar's own material and cannot be deleted here."
OFFICIAL_RESIDENT = "An official character lives at this place, so deleting it would change an official record. It cannot be deleted here."


class PlaceFormError(Exception):
    """Raised with {field: message} (field "" is a message about the whole form) and the HTTP status the page should answer with."""

    def __init__(self, errors, status=400):
        super().__init__("place form not accepted")
        self.errors = errors
        self.status = status


def parse(form, creating):
    """Validate a submitted place form. Returns (fields, errors); `errors` is empty when the form is acceptable. The region arrives as a slug and is looked up here:
    the form never supplies an id."""
    errors = {}
    name = clean_text(form, "name", errors, "The name", NAME_MAX, minimum=NAME_MIN)
    if creating:
        slug = (form.get("slug") or "").strip() or slugify(name)
        if not slug or len(slug) > 80 or not v.SLUG_PATTERN.match(slug):
            errors["slug"] = "Use a lowercase address such as 'neon-row-district' (letters, numbers and single hyphens, at most 80 characters)."
    else:
        slug = None
    region_slug = (form.get("region") or "").strip()
    region_id = None
    if not region_slug:
        errors["region"] = "Choose the region the place is in."
    elif len(region_slug) > 80 or not v.SLUG_PATTERN.match(region_slug):
        errors["region"] = "That is not a region."
    else:
        region_id = repo.region_id(region_slug)
        if region_id is None:
            errors["region"] = "There is no region with that address."
    location_type = (form.get("location_type") or "").strip().lower()
    if location_type not in v.LOCATION_TYPES:
        errors["location_type"] = f"Choose one of: {', '.join(v.LOCATION_TYPES)}."
    status = (form.get("content_status") or "").strip().lower()
    if status not in WRITABLE_STATUSES:
        errors["content_status"] = "Choose 'fan' or 'demo'. Official places come from Rockstar's own material and cannot be created or changed here."
    summary = clean_text(form, "summary", errors, "The summary", SUMMARY_MAX)
    description = clean_text(form, "description", errors, "The description", DESCRIPTION_MAX, multiline=True)
    source_url = clean_source_url(form, errors)
    source_note = clean_text(form, "source_note", errors, "The source note", SOURCE_MAX, minimum=0)
    fields = {"slug": slug, "region_id": region_id, "name": name, "location_type": location_type, "summary": summary, "description": description,
              "content_status": status, "source_url": source_url, "source_note": source_note or None}
    return fields, errors


def _database_problem(error):
    """A PlaceFormError for the database errors that mean 'the form clashes with what is stored', or None for any other error."""
    if error.errno == DUPLICATE_ENTRY:
        text = str(error.msg or "")
        if "uq_locations_region_name" in text:
            return PlaceFormError({"name": "A place with that name already exists in that region."}, 409)
        if "uq_locations_slug" in text:
            return PlaceFormError({"slug": "A place with that address already exists."}, 409)
        return PlaceFormError({"": "That place clashes with one that already exists."}, 409)
    if error.errno in FOREIGN_KEY_FAILED:                  # the region was removed after the form was drawn
        return PlaceFormError({"region": "That region no longer exists. Reload the form and choose again."}, 409)
    return None


def _audit(admin, action, slug):
    """One log line per change: who (the user id), what and which place. No names, no text, no secrets."""
    current_app.logger.info("Admin %s %s place %s", (admin or {}).get("user_id"), action, slug)


# ------------------------------------------------------------------ pages
def list_places(args):
    """The admin list: the same search, filters, sort and pagination as the public places API (one service), with every label shown."""
    return locations_service.list_locations(args)


def options():
    return {"regions": repo.regions()}


def load_for_edit(slug):
    """The place row (with its region slug) of a place the admin may edit. 404 when there is none; 403 for an official one."""
    v.require_slug(slug)
    place = locations_repo.get_by_slug(slug)
    if place is None:
        raise NotFound("No place with that address.")
    if place["content_status"] not in WRITABLE_STATUSES:
        raise Forbidden(OFFICIAL_EDIT)
    return place


def load_for_delete(slug):
    """(place row, impact counts, residents) for the confirmation page. The counts are read from the database, so they are what the delete would really do."""
    place = load_for_edit(slug)
    return place, repo.impact(place["location_id"]), locations_repo.residents(place["location_id"])


# ------------------------------------------------------------------ changes
def create(form, admin):
    """Create a place from a submitted form. Raises PlaceFormError. Returns the new slug."""
    fields, errors = parse(form, creating=True)
    if errors:
        raise PlaceFormError(errors, 400)
    try:
        repo.create_place(fields)
    except mysql.connector.IntegrityError as error:
        problem = _database_problem(error)
        if problem is None:
            raise
        raise problem
    _audit(admin, "created", fields["slug"])
    return fields["slug"]


def update(slug, form, admin):
    """Change a place (its region too). Raises PlaceFormError, NotFound (no such place) or Forbidden (official)."""
    v.require_slug(slug)
    fields, errors = parse(form, creating=False)
    if errors:
        raise PlaceFormError(errors, 400)
    try:
        repo.update_place(slug, fields)
    except repo.PlaceNotFound:
        raise NotFound("No place with that address.")
    except NotEditable:
        raise Forbidden(OFFICIAL_EDIT)
    except mysql.connector.IntegrityError as error:
        problem = _database_problem(error)
        if problem is None:
            raise
        raise problem
    _audit(admin, "updated", slug)
    return slug


def delete(slug, admin):
    """Delete a place (its story links, favourites and media links cascade; fan and demo residents lose their home). Returns its name.
    Raises NotFound, Forbidden (official place) or Conflict (an official character lives there)."""
    v.require_slug(slug)
    try:
        name = repo.delete_place(slug)
    except repo.PlaceNotFound:
        raise NotFound("No place with that address.")
    except NotEditable:
        raise Forbidden(OFFICIAL_DELETE)
    except repo.InUseByOfficial:
        raise Conflict(OFFICIAL_RESIDENT)
    _audit(admin, "deleted", slug)
    return name
