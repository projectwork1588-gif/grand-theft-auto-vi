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
    "vehicle": ("media_vehicles", "vehicle_id"),
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
def counts(kind, entity_ids):
    """How many official pictures (artwork and screenshots) each entity has: {entity_id: n}."""
    ids = [int(i) for i in entity_ids]
    if not ids:
        return {}
    table, column = ENTITY_TABLES[kind]
    marks = ", ".join(["%s"] * len(ids))
    rows = query_all(
        f"""SELECT link.{column} AS entity_id, COUNT(*) AS n
            FROM {table} link JOIN media_assets m ON m.media_id = link.media_id
            WHERE link.{column} IN ({marks}) AND {_VISIBLE} AND m.media_type IN ('artwork', 'screenshot')
            GROUP BY link.{column}""",
        ids,
    )
    return {row["entity_id"]: row["n"] for row in rows}


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
    """Videos that play in Rockstar's own player (not the poster-and-link clip cards)."""
    return query_all(
        f"""SELECT {_COLUMNS} FROM media_assets m
            WHERE m.media_type IN ('trailer', 'video') AND m.usage_status = 'embed_permitted' AND {_VISIBLE}
            ORDER BY m.media_id""")


@_tolerate_missing_tables(list)
def character_clips():
    """One poster-and-link card per character clip. embed_url holds the poster image, source_url the clip page."""
    return query_all(
        f"""SELECT {_COLUMNS}, c.slug AS character_slug, c.full_name AS character_name
            FROM media_assets m
            JOIN media_characters mc ON mc.media_id = m.media_id
            JOIN characters c ON c.character_id = mc.character_id
            WHERE m.media_type = 'video' AND m.usage_status = 'link_only' AND {_VISIBLE}
            ORDER BY c.character_id"""
    )


# ---------------------------------------------------------------- The Screening (/media): Rockstar's own media collections, in Rockstar's order
@_tolerate_missing_tables(list)
def collections():
    """Rockstar's own media sections (Videos, Clips, Screenshots, ...) in page order, each with its source, its zip download and the number of items listed."""
    return query_all(
        """SELECT c.collection_id, c.slug, c.title, c.kind, c.sort_order, c.source_url, c.download_url, c.download_bytes, c.verified_on,
                  (SELECT COUNT(*) FROM media_collection_items i WHERE i.collection_id = c.collection_id) AS item_count
           FROM media_collections c WHERE c.content_status = 'official' ORDER BY c.sort_order""")


@_tolerate_missing_tables(list)
def collection_items(slug):
    """The items of one collection in Rockstar's order. A picture's address is `embed_url`; a video's is its player address, and its poster comes from the poster row.
    Only approved rows are returned; the service still checks every address before it is drawn."""
    return query_all(
        """SELECT i.position, i.title, i.published_on, i.runtime_seconds, i.description,
                  m.media_id, m.slug AS media_slug, m.media_type, m.source_url, m.embed_url,
                  p.embed_url AS poster_url, p.slug AS poster_slug
           FROM media_collection_items i
           JOIN media_collections c ON c.collection_id = i.collection_id
           JOIN media_assets m ON m.media_id = i.media_id AND m.approval_status = 'approved'
           LEFT JOIN media_assets p ON p.media_id = i.poster_media_id AND p.approval_status = 'approved'
           WHERE c.slug = %s AND c.content_status = 'official'
           ORDER BY i.position""", (slug,))


@_tolerate_missing_tables(list)
def solo_vehicle_pictures():
    """Official pictures linked to exactly one official vehicle (so a picture that shows two machines is never asked about as one), in the Garage's order, then the picture's own."""
    return query_all(
        f"""SELECT {_COLUMNS}, v.slug AS vehicle_slug
            FROM media_vehicles link
            JOIN vehicles v ON v.vehicle_id = link.vehicle_id AND v.content_status = 'official'
            JOIN media_assets m ON m.media_id = link.media_id
            WHERE {_VISIBLE} AND m.media_type IN ('artwork', 'screenshot')
              AND (SELECT COUNT(*) FROM media_vehicles shared WHERE shared.media_id = m.media_id) = 1
            ORDER BY v.vehicle_id, m.media_id""")
