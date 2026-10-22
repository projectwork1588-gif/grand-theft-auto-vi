"""The rules for managing Stories (missions) from the admin area: validation, the official-content guard, and turning database errors into form errors.

No Flask request handling and no SQL here (SQL is in repositories/admin_stories.py). Official-source stories are read-only at every level: the form can
only choose 'fan' or 'demo', this service refuses to load an official story for editing, and the repository refuses to write one even when called directly.
"""
import re
import unicodedata
from urllib.parse import urlsplit

import mysql.connector
from flask import current_app
from werkzeug.exceptions import Forbidden, NotFound

from ..repositories import admin_stats, admin_stories as repo, missions as missions_repo
from . import missions as missions_service, validation as v

TITLE_MIN, TITLE_MAX = 3, 120
SUMMARY_MAX = 255
# 3000 characters: the largest realistic form (all 34 link rows ticked, every note at its maximum, typographic punctuation) is then about 13.5 KB of the site's
# 16 KiB request limit (measured; docs/ADMIN.md). The global limit is deliberately not raised. Text in a non-Latin script is several times larger once the
# browser encodes it, and a form that big gets the normal 413 page.
SYNOPSIS_MAX = 3000
SOURCE_MAX = 500
NOTE_MAX = {"characters": 80, "vehicles": 160}
LABELS = {"characters": "character", "vehicles": "vehicle", "locations": "place"}
MAX_LINKS = 50
DUPLICATE_ENTRY = 1062
FOREIGN_KEY_FAILED = (1216, 1452)


class StoryFormError(Exception):
    """Raised with {field: message} (field "" is a message about the whole form) and the HTTP status the page should answer with."""

    def __init__(self, errors, status=400):
        super().__init__("story form not accepted")
        self.errors = errors
        self.status = status


# ------------------------------------------------------------------ cleaning
def slugify(title):
    """'The Quiet Water' -> 'the-quiet-water' (accents dropped, anything else that is not a letter or digit becomes one hyphen)."""
    plain = unicodedata.normalize("NFKD", title or "").encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "-", plain).strip("-")[:80].strip("-")


def _text(form, name, errors, label, maximum, *, minimum=1, multiline=False):
    """The trimmed value of a text field, or '' after recording a problem. Control characters are refused (a line break and tab are fine in the synopsis)."""
    value = (form.get(name) or "").strip()
    if multiline:
        value = value.replace("\r\n", "\n").replace("\r", "\n")
    allowed = "\n\t" if multiline else ""
    if any(unicodedata.category(c) == "Cc" and c not in allowed for c in value):
        errors[name] = f"{label} contains a character that is not allowed."
        return ""
    if len(value) < minimum:
        errors[name] = f"{label} is required." if minimum <= 1 else f"{label} needs at least {minimum} characters."
        return ""
    if len(value) > maximum:
        errors[name] = f"{label} can have at most {maximum} characters."
        return ""
    return value


def _source_url(form, errors):
    value = (form.get("source_url") or "").strip()
    if not value:
        return None
    parts = urlsplit(value)
    if len(value) > SOURCE_MAX or parts.scheme != "https" or not parts.netloc or "@" in parts.netloc or any(c.isspace() or unicodedata.category(c) == "Cc" for c in value):
        errors["source_url"] = f"The source address must be a plain https address of at most {SOURCE_MAX} characters."
        return None
    return value


def selection_from_form(form):
    """What the form currently has ticked, for showing it again after a problem: {kind: {slug: note}} (places: {slug: is_primary})."""
    primary = (form.get("primary_location") or "").strip()
    selection = {}
    for kind in repo.LINK_KINDS:
        chosen = {}
        for slug in dict.fromkeys(form.getlist(kind)):
            chosen[slug] = (slug == primary) if kind == "locations" else (form.get(f"{kind}_note__{slug}") or "")
        selection[kind] = chosen
    return selection


def _links(form, errors):
    """{kind: [(entity id, note)]} for what is ticked. Slugs are looked up on the server; the form never supplies an id."""
    links = {}
    primary = (form.get("primary_location") or "").strip()
    for kind in repo.LINK_KINDS:
        label = LABELS[kind]
        slugs = list(dict.fromkeys(form.getlist(kind)))
        if len(slugs) > MAX_LINKS or any(len(s) > 80 or not v.SLUG_PATTERN.match(s) for s in slugs):
            errors[kind] = f"Some of the selected {label}s are not valid."
            links[kind] = []
            continue
        ids = repo.ids_by_slug(kind, slugs)
        unknown = [s for s in slugs if s not in ids]
        if unknown:
            errors[kind] = f"There is no {label} called '{unknown[0]}'."
        items = []
        for slug in slugs:
            if slug not in ids:
                continue
            if kind == "locations":
                items.append((ids[slug], slug == primary))
                continue
            field = f"{kind}_note__{slug}"
            label_for_note = "The role" if kind == "characters" else "The use"
            note = _text(form, field, errors, label_for_note, NOTE_MAX[kind])
            items.append((ids[slug], note))
        links[kind] = items
    if primary and primary not in form.getlist("locations"):
        errors["primary_location"] = "The main place must be one of the selected places."
    return links


def parse(form, creating):
    """Validate a submitted story form. Returns (fields, links, errors); `errors` is empty when the form is acceptable."""
    errors = {}
    title = _text(form, "title", errors, "The title", TITLE_MAX, minimum=TITLE_MIN)
    if creating:
        slug = (form.get("slug") or "").strip() or slugify(title)
        if not slug or len(slug) > 80 or not v.SLUG_PATTERN.match(slug):
            errors["slug"] = "Use a lowercase address such as 'the-quiet-water' (letters, numbers and single hyphens, at most 80 characters)."
    else:
        slug = None
    mission_type = (form.get("mission_type") or "").strip().lower()
    if mission_type not in v.MISSION_TYPES:
        errors["mission_type"] = f"Choose one of: {', '.join(v.MISSION_TYPES)}."
    status = (form.get("content_status") or "").strip().lower()
    if status not in repo.WRITABLE_STATUSES:
        errors["content_status"] = "Choose 'fan' or 'demo'. Official stories come from Rockstar's own material and cannot be created or changed here."
    summary = _text(form, "summary", errors, "The summary", SUMMARY_MAX)
    synopsis = _text(form, "synopsis", errors, "The synopsis", SYNOPSIS_MAX, multiline=True)
    source_url = _source_url(form, errors)
    source_note = _text(form, "source_note", errors, "The source note", SOURCE_MAX, minimum=0)
    links = _links(form, errors)
    fields = {"slug": slug, "title": title, "mission_type": mission_type, "summary": summary, "synopsis": synopsis, "content_status": status,
              "source_url": source_url, "source_note": source_note or None}
    return fields, links, errors


def _database_problem(error):
    """A StoryFormError for the database errors that mean 'the form clashes with what is stored', or None for any other error."""
    if error.errno == DUPLICATE_ENTRY:
        text = str(error.msg or "")
        if "uq_missions_title" in text:
            return StoryFormError({"title": "A story with that title already exists."}, 409)
        if "uq_missions_slug" in text:
            return StoryFormError({"slug": "A story with that address already exists."}, 409)
        return StoryFormError({"": "That story clashes with one that already exists."}, 409)
    if error.errno in FOREIGN_KEY_FAILED:                  # a character, vehicle or place was removed after the form was drawn
        return StoryFormError({"": "A character, vehicle or place you selected no longer exists. Reload the form and choose again."}, 409)
    return None


def _audit(admin, action, slug):
    """One log line per change: who (the user id), what and which story. No names, no text, no secrets."""
    current_app.logger.info("Admin %s %s story %s", (admin or {}).get("user_id"), action, slug)


# ------------------------------------------------------------------ pages
def list_stories(args):
    """The admin list: the same search, filters, sort and pagination as the public Stories page (one service), with every status."""
    return missions_service.list_missions(args)


def options():
    return {kind: repo.options(kind) for kind in repo.LINK_KINDS}


def load_for_edit(slug):
    """(story row, current selection) of a story the admin may edit. 404 when there is none; 403 for an official one."""
    v.require_slug(slug)
    story = missions_repo.get_by_slug(slug)
    if story is None:
        raise NotFound("No story with that address.")
    if story["content_status"] not in repo.WRITABLE_STATUSES:
        raise Forbidden("Official stories come from Rockstar's own material and cannot be edited here.")
    mission_id = story["mission_id"]
    selection = {
        "characters": {r["slug"]: r["role_in_mission"] for r in missions_repo.characters_for(mission_id)},
        "vehicles": {r["slug"]: r["usage_note"] for r in missions_repo.vehicles_for(mission_id)},
        "locations": {r["slug"]: bool(r["is_primary"]) for r in missions_repo.locations_for(mission_id)},
    }
    return story, selection


def load_for_delete(slug):
    """(story row, impact counts) for the confirmation page."""
    story, _selection = load_for_edit(slug)
    return story, repo.impact(story["mission_id"])


# ------------------------------------------------------------------ changes
def create(form, admin):
    """Create a story from a submitted form. Raises StoryFormError. Returns the new slug."""
    fields, links, errors = parse(form, creating=True)
    if errors:
        raise StoryFormError(errors, 400)
    try:
        repo.create_story(fields, links)
    except mysql.connector.IntegrityError as error:
        problem = _database_problem(error)
        if problem is None:
            raise
        raise problem
    _audit(admin, "created", fields["slug"])
    return fields["slug"]


def update(slug, form, admin):
    """Change a story and its links. Raises StoryFormError, NotFound (no such story) or Forbidden (official)."""
    v.require_slug(slug)
    fields, links, errors = parse(form, creating=False)
    if errors:
        raise StoryFormError(errors, 400)
    try:
        repo.update_story(slug, fields, links)
    except repo.StoryNotFound:
        raise NotFound("No story with that address.")
    except repo.NotEditable:
        raise Forbidden("Official stories come from Rockstar's own material and cannot be edited here.")
    except mysql.connector.IntegrityError as error:
        problem = _database_problem(error)
        if problem is None:
            raise
        raise problem
    _audit(admin, "updated", slug)
    return slug


def delete(slug, admin):
    """Delete a story (its links and the users' favourites of it cascade). Returns its title."""
    v.require_slug(slug)
    try:
        title = repo.delete_story(slug)
    except repo.StoryNotFound:
        raise NotFound("No story with that address.")
    except repo.NotEditable:
        raise Forbidden("Official stories come from Rockstar's own material and cannot be deleted here.")
    _audit(admin, "deleted", slug)
    return title


# ------------------------------------------------------------------ dashboard
def dashboard():
    return {
        "tables": admin_stats.table_counts(),
        "stories": admin_stats.stories_by_status_and_type(),
        "roles": admin_stats.users_by_role(),
        "favourites": admin_stats.favourites_by_kind(),
        "top_stories": admin_stats.top_favourited_stories(),
        "unlinked": admin_stats.stories_without_links(),
    }
