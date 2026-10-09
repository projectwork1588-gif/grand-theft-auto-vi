"""SQL for media records attached to characters, regions and locations.

Media is decoration, never a reason to fail a page: if the media tables are missing (a database that has
not had migration 001 applied yet) every function returns an empty result and logs a warning instead.
"""
import logging
from functools import wraps

from mysql.connector import errors

from ..db import query_all

log = logging.getLogger(__name__)

# Table and column names come from this fixed map, never from user input.
ENTITY_TABLES = {
    "character": ("media_characters", "character_id"),
    "region": ("media_regions", "region_id"),
    "location": ("media_locations", "location_id"),
}
_COLUMNS = "m.media_id, m.slug, m.title, m.media_type, m.source_url, m.embed_url, m.attribution"
_VISIBLE = "m.approval_status = 'approved' AND m.embed_url IS NOT NULL"


def _tolerate_missing_tables(default):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except errors.ProgrammingError as exc:  # e.g. 1146 table doesn't exist
                log.warning("Media lookup skipped (%s). Has migration 001 been applied?", exc)
                return default() if callable(default) else default
        return wrapper
    return decorator


@_tolerate_missing_tables(list)
def for_entity(kind, entity_id, limit=12):
    table, column = ENTITY_TABLES[kind]
    return query_all(
        f"""SELECT {_COLUMNS}
            FROM {table} link
            JOIN media_assets m ON m.media_id = link.media_id
            WHERE link.{column} = %s AND {_VISIBLE} AND m.media_type IN ('artwork', 'screenshot')
            ORDER BY (SELECT COUNT(*) FROM {table} shared WHERE shared.media_id = m.media_id) ASC,
                     (m.media_type = 'artwork') DESC, m.media_id
            LIMIT %s""",
        (entity_id, limit),
    )


@_tolerate_missing_tables(dict)
def covers(kind, entity_ids):
    """Best single image per entity: media used only for that entity first (so each lead gets a solo shot),
    then official artwork, then screenshots. {entity_id: media}."""
    ids = [int(i) for i in entity_ids]
    if not ids:
        return {}
    table, column = ENTITY_TABLES[kind]
    marks = ", ".join(["%s"] * len(ids))
    rows = query_all(
        f"""SELECT link.{column} AS entity_id, {_COLUMNS}
            FROM {table} link
            JOIN media_assets m ON m.media_id = link.media_id
            WHERE link.{column} IN ({marks}) AND {_VISIBLE} AND m.media_type IN ('artwork', 'screenshot')
            ORDER BY (SELECT COUNT(*) FROM {table} shared WHERE shared.media_id = m.media_id) ASC,
                     (m.media_type = 'artwork') DESC, m.media_id""",
        ids,
    )
    best = {}
    for row in rows:
        best.setdefault(row["entity_id"], row)
    return best


@_tolerate_missing_tables(dict)
def by_slugs(slugs):
    slugs = list(slugs)
    if not slugs:
        return {}
    marks = ", ".join(["%s"] * len(slugs))
    rows = query_all(
        f"SELECT {_COLUMNS} FROM media_assets m WHERE m.slug IN ({marks}) AND {_VISIBLE}", slugs)
    return {row["slug"]: row for row in rows}


@_tolerate_missing_tables(list)
def videos():
    return query_all(
        f"""SELECT {_COLUMNS} FROM media_assets m
            WHERE m.media_type IN ('trailer', 'video') AND {_VISIBLE}
            ORDER BY m.media_id""")
