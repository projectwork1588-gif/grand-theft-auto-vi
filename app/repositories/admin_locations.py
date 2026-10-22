"""The admin area's SQL for Places (the `locations` table).

Rules this module enforces itself, so they hold for a direct call as well as for a request:

* OFFICIAL-SOURCE ROWS ARE READ-ONLY. A place whose content_status is 'official' is never inserted, updated or deleted here: the write functions refuse a status that
  is not in WRITABLE_STATUSES, lock the row, refuse it when it is not writable (NotEditable), and the UPDATE and DELETE statements repeat the condition in their WHERE.
* A PLACE THAT AN OFFICIAL CHARACTER LIVES AT IS NOT DELETED. Deleting a place blanks `characters.home_location_id` (ON DELETE SET NULL), which would rewrite an
  official character. delete_place() refuses (InUseByOfficial) when any non-writable character has the place as home, and the DELETE statement itself carries a
  NOT EXISTS for the same condition. Characters whose label is fan or demo (Team Valkyrie's own) are blanked as the foreign key says, and the confirmation page counts them.
* Every write is ONE transaction() (commit on success, roll back on any error), and nothing here is outside transaction() except reads.
* Values are always placeholders; no text from a request is ever put into SQL.
"""
from ..db import query_all, query_one, transaction
from .admin_stories import NotEditable, WRITABLE_STATUSES


class PlaceNotFound(LookupError):
    """There is no place with that slug."""


class InUseByOfficial(PermissionError):
    """An official character has this place as home, so deleting it would change an official record."""


def _require_writable_status(status):
    if status not in WRITABLE_STATUSES:
        raise ValueError(f"places written here must be one of {', '.join(WRITABLE_STATUSES)}; official content is read-only")


# ------------------------------------------------------------------ reads
def regions():
    """Every region a place can belong to: [{slug, name}], by name. (Regions themselves are official and are never written here.)"""
    return query_all("SELECT slug, name FROM regions ORDER BY name")


def region_id(slug):
    """The id of the region with that slug, or None."""
    row = query_one("SELECT region_id FROM regions WHERE slug = %s", (slug,))
    return row["region_id"] if row else None


def impact(location_id):
    """What deleting the place would do (the foreign keys act): characters that live here (their home is blanked), how many of those are official (that blocks the
    delete), story links, saved favourites and media links (all three removed)."""
    return query_one(
        """SELECT (SELECT COUNT(*) FROM characters WHERE home_location_id = %s) AS residents,
                  (SELECT COUNT(*) FROM characters WHERE home_location_id = %s AND content_status NOT IN ('fan', 'demo')) AS official_residents,
                  (SELECT COUNT(*) FROM mission_locations WHERE location_id = %s) AS story_links,
                  (SELECT COUNT(*) FROM favourite_locations WHERE location_id = %s) AS favourites,
                  (SELECT COUNT(*) FROM media_locations WHERE location_id = %s) AS media_links""",
        (location_id, location_id, location_id, location_id, location_id))


# ------------------------------------------------------------------ writes (each is one transaction)
def _lock_editable(cursor, slug):
    """Lock the place's row for this transaction and return its id; PlaceNotFound if absent, NotEditable if it is not writable."""
    cursor.execute("SELECT location_id, content_status FROM locations WHERE slug = %s FOR UPDATE", (slug,))
    row = cursor.fetchone()
    if row is None:
        raise PlaceNotFound(slug)
    if row["content_status"] not in WRITABLE_STATUSES:
        raise NotEditable(slug)
    return row["location_id"]


def _before_commit(cursor):
    """The last step inside every write, just before the commit. It does nothing; the rollback tests replace it to prove that a failure here undoes everything."""


def create_place(fields):
    """Insert a place. Returns the new id. A taken slug or (region, name) raises mysql.connector's IntegrityError (1062); an unknown region raises it too (1452)."""
    _require_writable_status(fields["content_status"])
    with transaction() as cursor:
        cursor.execute(
            """INSERT INTO locations (region_id, slug, name, location_type, summary, description, content_status, source_url, source_note)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (fields["region_id"], fields["slug"], fields["name"], fields["location_type"], fields["summary"], fields["description"], fields["content_status"],
             fields["source_url"], fields["source_note"]))
        location_id = cursor.lastrowid
        _before_commit(cursor)
    return location_id


def update_place(slug, fields):
    """Change a writable place (including moving it to another region). The slug itself never changes."""
    _require_writable_status(fields["content_status"])
    with transaction() as cursor:
        location_id = _lock_editable(cursor, slug)
        cursor.execute(
            """UPDATE locations SET region_id = %s, name = %s, location_type = %s, summary = %s, description = %s, content_status = %s, source_url = %s, source_note = %s
               WHERE location_id = %s AND content_status IN ('fan', 'demo')""",
            (fields["region_id"], fields["name"], fields["location_type"], fields["summary"], fields["description"], fields["content_status"], fields["source_url"],
             fields["source_note"], location_id))
        _before_commit(cursor)
    return location_id


def delete_place(slug):
    """Delete a writable place whose residents are all Team Valkyrie's own. The story links, favourites and media links of it go with it (ON DELETE CASCADE) and its
    fan or demo residents are left without a home (ON DELETE SET NULL). Returns the place's name."""
    with transaction() as cursor:
        location_id = _lock_editable(cursor, slug)
        cursor.execute("SELECT content_status FROM characters WHERE home_location_id = %s FOR UPDATE", (location_id,))     # the residents are locked: nobody can make one official meanwhile
        if any(row["content_status"] not in WRITABLE_STATUSES for row in cursor.fetchall()):
            raise InUseByOfficial(slug)
        cursor.execute("SELECT name FROM locations WHERE location_id = %s", (location_id,))
        name = cursor.fetchone()["name"]
        cursor.execute(
            """DELETE FROM locations WHERE location_id = %s AND content_status IN ('fan', 'demo')
                 AND NOT EXISTS (SELECT 1 FROM characters c WHERE c.home_location_id = locations.location_id AND c.content_status NOT IN ('fan', 'demo'))""",
            (location_id,))
        if cursor.rowcount != 1:
            raise NotEditable(slug)                     # rolls everything back: nothing was deleted
        _before_commit(cursor)
    return name
