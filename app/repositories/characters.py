"""All SQL for characters. Every value reaches MySQL as a bound parameter."""
import logging

from mysql.connector import errors

from ..db import query_all, query_one

log = logging.getLogger(__name__)

NO_TABLE = 1146  # MySQL: table doesn't exist (a database that has not had migration 005 applied yet)

# User input may only select one of these keys, it is never placed into the SQL text.
SORT_ORDERS = {
    "name_asc": "c.full_name ASC, c.character_id ASC",
    "name_desc": "c.full_name DESC, c.character_id ASC",
    "newest": "c.created_at DESC, c.character_id DESC",
}

_FROM = """
    FROM characters c
    LEFT JOIN locations l ON l.location_id = c.home_location_id
    LEFT JOIN regions r ON r.region_id = l.region_id
"""


def _where(q_like, status, region, include_original=False, via_regions=True):
    """The public site lists Rockstar's own characters only. include_original lifts that for the documented
    API switch and for the DBMS demonstration; it is never set by an HTML page. via_regions=False leaves out the
    character_regions lookup (used only when that table does not exist yet)."""
    clauses, params = [], []
    if not include_original:
        clauses.append("c.content_status = 'official'")
    if q_like:
        clauses.append("(c.full_name LIKE %s ESCAPE '!' OR c.alias LIKE %s ESCAPE '!' OR c.role_title LIKE %s ESCAPE '!')")
        params += [q_like, q_like, q_like]
    if status:
        clauses.append("c.content_status = %s")
        params.append(status)
    if region:
        # a character belongs to a region through a home place (original characters) or through where Rockstar's own
        # text places them (character_regions, official characters)
        if via_regions:
            clauses.append("(r.slug = %s OR EXISTS (SELECT 1 FROM character_regions cg JOIN regions gr ON gr.region_id = cg.region_id"
                           " WHERE cg.character_id = c.character_id AND gr.slug = %s))")
            params += [region, region]
        else:
            clauses.append("r.slug = %s")
            params.append(region)
    return (" WHERE " + " AND ".join(clauses)) if clauses else "", params


def search(q_like, status, region, sort, limit, offset, include_original=False):
    try:
        return _search(q_like, status, region, sort, limit, offset, include_original, True)
    except errors.ProgrammingError as exc:
        if exc.errno != NO_TABLE or not region:
            raise
        log.warning("Region filter fell back to home places only (%s). Has migration 005 been applied?", exc)
        return _search(q_like, status, region, sort, limit, offset, include_original, False)


def _search(q_like, status, region, sort, limit, offset, include_original, via_regions):
    where, params = _where(q_like, status, region, include_original, via_regions)
    total = query_one("SELECT COUNT(*) AS n" + _FROM + where, params)["n"]
    rows = query_all(
        """SELECT c.slug, c.full_name, c.alias, c.role_title, c.summary, c.content_status,
                  l.slug AS home_location_slug, l.name AS home_location_name,
                  r.slug AS region_slug, r.name AS region_name"""
        + _FROM + where + " ORDER BY " + SORT_ORDERS[sort] + " LIMIT %s OFFSET %s",
        params + [limit, offset],
    )
    return rows, total


def get_by_slug(slug, include_original=False):
    return query_one(
        """SELECT c.character_id, c.slug, c.full_name, c.alias, c.role_title, c.summary, c.biography,
                  c.content_status, c.source_url, c.source_note,
                  l.slug AS home_location_slug, l.name AS home_location_name,
                  r.slug AS region_slug, r.name AS region_name"""
        + _FROM + " WHERE c.slug = %s" + ("" if include_original else " AND c.content_status = 'official'"),
        (slug,),
    )


def regions_for(character_id):
    """Regions Rockstar's own text places this character in, with what the source says."""
    try:
        return query_all(
            """SELECT r.slug, r.name, cg.note, cg.source_url
               FROM character_regions cg JOIN regions r ON r.region_id = cg.region_id
               WHERE cg.character_id = %s ORDER BY r.name""",
            (character_id,),
        )
    except errors.ProgrammingError as exc:
        if exc.errno != NO_TABLE:
            raise
        log.warning("Character regions skipped (%s). Has migration 005 been applied?", exc)
        return []


def relationships_for(character_id, include_original=False):
    """Both directions. The public site shows a link only between two official characters."""
    keep = 1 if include_original else 0
    return query_all(
        """SELECT 'outgoing' AS direction, cr.relationship_type, cr.description, cr.content_status,
                  o.slug, o.full_name
           FROM character_relationships cr
           JOIN characters o ON o.character_id = cr.to_character_id
           WHERE cr.from_character_id = %s AND (o.content_status = 'official' OR %s = 1)
           UNION ALL
           SELECT 'incoming' AS direction, cr.relationship_type, cr.description, cr.content_status,
                  o.slug, o.full_name
           FROM character_relationships cr
           JOIN characters o ON o.character_id = cr.from_character_id
           WHERE cr.to_character_id = %s AND (o.content_status = 'official' OR %s = 1)
           ORDER BY full_name""",
        (character_id, keep, character_id, keep),
    )


def missions_for(character_id):
    return query_all(
        """SELECT m.slug, m.title, m.mission_type, m.content_status, mc.role_in_mission
           FROM mission_characters mc
           JOIN missions m ON m.mission_id = mc.mission_id
           WHERE mc.character_id = %s
           ORDER BY m.title""",
        (character_id,),
    )


def locations_for(character_id):
    """Locations reached through the character's missions."""
    return query_all(
        """SELECT DISTINCT l.slug, l.name, l.content_status
           FROM mission_characters mc
           JOIN mission_locations ml ON ml.mission_id = mc.mission_id
           JOIN locations l ON l.location_id = ml.location_id
           WHERE mc.character_id = %s
           ORDER BY l.name""",
        (character_id,),
    )


def costars_for(character_id, limit=6, include_original=False):
    """Characters who share at least one mission with this character, most shared missions first."""
    keep = 1 if include_original else 0
    return query_all(
        """SELECT c.slug, c.full_name, c.role_title, c.content_status, COUNT(*) AS shared_missions
           FROM mission_characters me
           JOIN mission_characters other ON other.mission_id = me.mission_id AND other.character_id <> me.character_id
           JOIN characters c ON c.character_id = other.character_id
           WHERE me.character_id = %s AND (c.content_status = 'official' OR %s = 1)
           GROUP BY c.character_id, c.slug, c.full_name, c.role_title, c.content_status
           ORDER BY shared_missions DESC, c.full_name LIMIT %s""",
        (character_id, keep, limit),
    )


def featured_official(limit=8):
    """Official characters in database order (the two leads first)."""
    return query_all(
        """SELECT c.character_id, c.slug, c.full_name, c.role_title, c.summary, c.content_status
           FROM characters c WHERE c.content_status = 'official'
           ORDER BY c.character_id LIMIT %s""",
        (limit,),
    )


def official_relationships(limit=6, exclude=()):
    """Relationships Rockstar's own page states, with both names. exclude is a tuple of (from_slug, to_slug) pairs to
    leave out (the homepage keeps its approved four lines)."""
    skip, skip_params = "", []
    for from_slug, to_slug in exclude:
        skip += " AND NOT (a.slug = %s AND b.slug = %s)"
        skip_params += [from_slug, to_slug]
    return query_all(
        """SELECT a.slug AS from_slug, a.full_name AS from_name, b.slug AS to_slug, b.full_name AS to_name,
                  cr.relationship_type, cr.description
           FROM character_relationships cr
           JOIN characters a ON a.character_id = cr.from_character_id
           JOIN characters b ON b.character_id = cr.to_character_id
           WHERE cr.content_status = 'official'""" + skip + """
           ORDER BY cr.from_character_id, cr.to_character_id LIMIT %s""",
        skip_params + [limit],
    )


def ids_by_slug(slugs):
    """{slug: character_id} for a list of slugs (used to attach media)."""
    slugs = list(slugs)
    if not slugs:
        return {}
    marks = ", ".join(["%s"] * len(slugs))
    rows = query_all(f"SELECT slug, character_id FROM characters WHERE slug IN ({marks})", slugs)
    return {row["slug"]: row["character_id"] for row in rows}
