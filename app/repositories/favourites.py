"""Favourites: user (M) <-> (N) entity, one table per entity so each keeps real foreign keys.

The table and column names below are the ONLY dynamic parts of any statement; they come from this fixed map and never from a request. Values are
always placeholders. The "public" condition is the same rule the entity's own page applies (an unpublished record cannot be saved or listed).
"""
from ..db import query_all, query_one, transaction

# kind -> (favourites table, id column in both tables, entity table, label column, public condition, page endpoint, singular label)
KINDS = {
    "characters": ("favourite_characters", "character_id", "characters", "full_name", "e.content_status = 'official'", "pages.character_detail", "character"),
    "vehicles": ("favourite_vehicles", "vehicle_id", "vehicles", "name", "e.content_status = 'official'", "pages.vehicle_detail", "vehicle"),
    "locations": ("favourite_locations", "location_id", "locations", "name", "1 = 1", "pages.location_detail", "place"),
    "missions": ("favourite_missions", "mission_id", "missions", "title", "1 = 1", "pages.mission_detail", "story"),
}


def find_public(kind, slug):
    """The entity a visitor can see at /<kind>/<slug>, as {id, name}; None when there is none."""
    _fav, id_col, table, label, public, _endpoint, _single = KINDS[kind]
    return query_one(f"SELECT e.{id_col} AS id, e.{label} AS name FROM {table} e WHERE e.slug = %s AND {public}", (slug,))


def add(kind, user_id, entity_id):
    """Save an entity. Saving twice is harmless (ON DUPLICATE KEY UPDATE changes nothing). Not INSERT IGNORE: that would also swallow a foreign-key failure."""
    table, id_col = KINDS[kind][:2]
    with transaction() as cursor:
        cursor.execute(f"INSERT INTO {table} (user_id, {id_col}) VALUES (%s, %s) ON DUPLICATE KEY UPDATE user_id = user_id", (user_id, entity_id))


def remove(kind, user_id, entity_id):
    """Remove one of this user's favourites. Returns the number of rows deleted (0 when it was not saved). The WHERE always names the user."""
    table, id_col = KINDS[kind][:2]
    with transaction() as cursor:
        cursor.execute(f"DELETE FROM {table} WHERE user_id = %s AND {id_col} = %s", (user_id, entity_id))
        return cursor.rowcount


def is_saved(kind, user_id, slug):
    table, id_col, entity, _label, public, _endpoint, _single = KINDS[kind]
    row = query_one(
        f"SELECT 1 AS saved FROM {table} f JOIN {entity} e ON e.{id_col} = f.{id_col} WHERE f.user_id = %s AND e.slug = %s AND {public}",
        (user_id, slug))
    return row is not None


def list_for_user(kind, user_id):
    """This user's favourites of one kind, newest first, as {slug, name, saved_at}. Records that are no longer public are left out."""
    table, id_col, entity, label, public, _endpoint, _single = KINDS[kind]
    return query_all(
        f"""SELECT e.slug, e.{label} AS name, f.created_at AS saved_at
            FROM {table} f JOIN {entity} e ON e.{id_col} = f.{id_col}
            WHERE f.user_id = %s AND {public}
            ORDER BY f.created_at DESC, e.{label}""",
        (user_id,))
