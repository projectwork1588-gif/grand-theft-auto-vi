"""Saving and listing favourites. The user always comes from the signed-in session, never from the request."""
import mysql.connector
from werkzeug.exceptions import NotFound

from ..repositories import favourites as repo
from ..services.validation import require_slug

FOREIGN_KEY_FAILED = (1216, 1452)      # a child row names a parent that does not exist (the connector reports 1216 or 1452)


def kind_or_404(kind):
    if kind not in repo.KINDS:
        raise NotFound("There is no such kind of favourite.")
    return kind


def _entity_or_404(kind, slug):
    entity = repo.find_public(kind_or_404(kind), require_slug(slug))
    if entity is None:
        raise NotFound("No record with that address.")
    return entity


def save(user_id, kind, slug):
    """Save a public record for this user and return its name. Saving it again changes nothing."""
    entity = _entity_or_404(kind, slug)
    try:
        repo.add(kind, user_id, entity["id"])
    except mysql.connector.IntegrityError as error:
        if error.errno in FOREIGN_KEY_FAILED:          # the record was removed between the lookup and the insert
            raise NotFound("No record with that address.")
        raise
    return entity["name"]


def unsave(user_id, kind, slug):
    """Remove one of this user's favourites and return its name. Removing one that is not saved changes nothing."""
    entity = _entity_or_404(kind, slug)
    repo.remove(kind, user_id, entity["id"])
    return entity["name"]


def is_saved(user_id, kind, slug):
    return repo.is_saved(kind_or_404(kind), user_id, slug)


def overview(user_id):
    """Everything this user has saved, grouped by kind, ready for the page: [{kind, title, endpoint, items}, ...] in a fixed order."""
    titles = {"characters": "Characters", "vehicles": "Vehicles", "locations": "Places", "missions": "Stories"}
    groups = []
    for kind, definition in repo.KINDS.items():
        groups.append({"kind": kind, "title": titles[kind], "endpoint": definition[5], "single": definition[6], "items": repo.list_for_user(kind, user_id)})
    return groups
