"""The admin area's SQL for Stories (the `missions` table and its three link tables).

Rules this module enforces itself, so they hold for a direct call as well as for a request:

* OFFICIAL-SOURCE ROWS ARE READ-ONLY. A story whose content_status is 'official' (Rockstar-sourced, source_url required by the table's CHECK) is never
  inserted, updated, relinked or deleted here. The write functions refuse a status that is not in WRITABLE_STATUSES, lock the story row, refuse it when it is
  not writable (NotEditable), and the UPDATE and DELETE statements repeat the condition in their WHERE clause.
* Every write is ONE transaction() (commit on success, roll back on any error), and nothing here is outside transaction() except reads.
* Values are always placeholders. The only text put into SQL is a table or column name taken from LINK_KINDS, a fixed map, never from a request.
"""
from ..db import query_all, query_one, transaction

WRITABLE_STATUSES = ("fan", "demo")

# kind -> (link table, id column in both tables, entity table, name column, the note column of the link table)
LINK_KINDS = {
    "characters": ("mission_characters", "character_id", "characters", "full_name", "role_in_mission"),
    "vehicles": ("mission_vehicles", "vehicle_id", "vehicles", "name", "usage_note"),
    "locations": ("mission_locations", "location_id", "locations", "name", "is_primary"),
}


class StoryNotFound(LookupError):
    """There is no story with that slug."""


class NotEditable(PermissionError):
    """The story is not writable (it is official, Rockstar-sourced content)."""


def _require_writable_status(status):
    if status not in WRITABLE_STATUSES:
        raise ValueError(f"stories written here must be one of {', '.join(WRITABLE_STATUSES)}; official content is read-only")


# ------------------------------------------------------------------ reads
def options(kind):
    """Every entity of one kind that a story can be linked to: [{slug, name, content_status}], by name."""
    _link, _id, table, label, _note = LINK_KINDS[kind]
    return query_all(f"SELECT slug, {label} AS name, content_status FROM {table} ORDER BY {label}")


def ids_by_slug(kind, slugs):
    """{slug: id} for the slugs that exist (an unknown slug is simply missing from the answer)."""
    slugs = list(dict.fromkeys(slugs))
    if not slugs:
        return {}
    _link, id_col, table, _label, _note = LINK_KINDS[kind]
    marks = ", ".join(["%s"] * len(slugs))
    return {row["slug"]: row[id_col] for row in query_all(f"SELECT slug, {id_col} FROM {table} WHERE slug IN ({marks})", slugs)}


def impact(mission_id):
    """What deleting the story would take with it (the foreign keys cascade): link rows per kind and users' favourites of it."""
    return query_one(
        """SELECT (SELECT COUNT(*) FROM mission_characters WHERE mission_id = %s) AS characters,
                  (SELECT COUNT(*) FROM mission_vehicles WHERE mission_id = %s) AS vehicles,
                  (SELECT COUNT(*) FROM mission_locations WHERE mission_id = %s) AS locations,
                  (SELECT COUNT(*) FROM favourite_missions WHERE mission_id = %s) AS favourites""",
        (mission_id, mission_id, mission_id, mission_id))


# ------------------------------------------------------------------ writes (each is one transaction)
def _lock_editable(cursor, slug):
    """Lock the story's row for this transaction and return its id; StoryNotFound if absent, NotEditable if it is not writable."""
    cursor.execute("SELECT mission_id, content_status FROM missions WHERE slug = %s FOR UPDATE", (slug,))
    row = cursor.fetchone()
    if row is None:
        raise StoryNotFound(slug)
    if row["content_status"] not in WRITABLE_STATUSES:
        raise NotEditable(slug)
    return row["mission_id"]


def _insert_links(cursor, mission_id, links):
    """links: {kind: [(entity id, note)]} (for locations the second value is is_primary). Each INSERT selects its mission_id FROM missions with the writable
    condition, so even if the lock check above were bypassed, a link row is never added to an official story."""
    for kind, items in links.items():
        link_table, id_col, _table, _label, note_col = LINK_KINDS[kind]
        for entity_id, note in items:
            cursor.execute(
                f"INSERT INTO {link_table} (mission_id, {id_col}, {note_col}) SELECT mission_id, %s, %s FROM missions WHERE mission_id = %s AND content_status IN ('fan', 'demo')",
                (entity_id, note, mission_id))


def _delete_links(cursor, mission_id):
    """Remove a writable story's links. The JOIN carries the writable condition, so an official story's links are never deleted."""
    for link_table, *_rest in LINK_KINDS.values():
        cursor.execute(
            f"DELETE l FROM {link_table} l JOIN missions m ON m.mission_id = l.mission_id WHERE l.mission_id = %s AND m.content_status IN ('fan', 'demo')",
            (mission_id,))


def _before_commit(cursor):
    """The last step inside every write, just before the commit. It does nothing; the rollback tests replace it to prove that a failure here undoes everything."""


def create_story(fields, links):
    """Insert a story and its links, atomically. Returns the new id. A taken slug or title raises mysql.connector's IntegrityError (1062)."""
    _require_writable_status(fields["content_status"])
    with transaction() as cursor:
        cursor.execute(
            """INSERT INTO missions (slug, title, mission_type, summary, synopsis, content_status, source_url, source_note)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (fields["slug"], fields["title"], fields["mission_type"], fields["summary"], fields["synopsis"], fields["content_status"],
             fields["source_url"], fields["source_note"]))
        mission_id = cursor.lastrowid
        _insert_links(cursor, mission_id, links)
        _before_commit(cursor)
    return mission_id


def update_story(slug, fields, links):
    """Replace a writable story's fields and all its links, atomically. The slug itself never changes."""
    _require_writable_status(fields["content_status"])
    with transaction() as cursor:
        mission_id = _lock_editable(cursor, slug)
        cursor.execute(
            """UPDATE missions SET title = %s, mission_type = %s, summary = %s, synopsis = %s, content_status = %s, source_url = %s, source_note = %s
               WHERE mission_id = %s AND content_status IN ('fan', 'demo')""",
            (fields["title"], fields["mission_type"], fields["summary"], fields["synopsis"], fields["content_status"], fields["source_url"],
             fields["source_note"], mission_id))
        _delete_links(cursor, mission_id)
        _insert_links(cursor, mission_id, links)
        _before_commit(cursor)
    return mission_id


def delete_story(slug):
    """Delete a writable story. The link rows and the users' favourites of it go with it (ON DELETE CASCADE). Returns its title."""
    with transaction() as cursor:
        mission_id = _lock_editable(cursor, slug)
        cursor.execute("SELECT title FROM missions WHERE mission_id = %s", (mission_id,))
        title = cursor.fetchone()["title"]
        cursor.execute("DELETE FROM missions WHERE mission_id = %s AND content_status IN ('fan', 'demo')", (mission_id,))
        if cursor.rowcount != 1:
            raise NotEditable(slug)                     # rolls everything back: nothing was deleted
        _before_commit(cursor)
    return title
