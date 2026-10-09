"""All SQL for characters. Every value reaches MySQL as a bound parameter."""
from ..db import query_all, query_one

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


def _where(q_like, status, region):
    clauses, params = [], []
    if q_like:
        clauses.append("(c.full_name LIKE %s ESCAPE '!' OR c.alias LIKE %s ESCAPE '!' OR c.role_title LIKE %s ESCAPE '!')")
        params += [q_like, q_like, q_like]
    if status:
        clauses.append("c.content_status = %s")
        params.append(status)
    if region:
        clauses.append("r.slug = %s")
        params.append(region)
    return (" WHERE " + " AND ".join(clauses)) if clauses else "", params


def search(q_like, status, region, sort, limit, offset):
    where, params = _where(q_like, status, region)
    total = query_one("SELECT COUNT(*) AS n" + _FROM + where, params)["n"]
    rows = query_all(
        """SELECT c.slug, c.full_name, c.alias, c.role_title, c.summary, c.content_status,
                  l.slug AS home_location_slug, l.name AS home_location_name,
                  r.slug AS region_slug, r.name AS region_name"""
        + _FROM + where + " ORDER BY " + SORT_ORDERS[sort] + " LIMIT %s OFFSET %s",
        params + [limit, offset],
    )
    return rows, total


def get_by_slug(slug):
    return query_one(
        """SELECT c.character_id, c.slug, c.full_name, c.alias, c.role_title, c.summary, c.biography,
                  c.content_status, c.source_url, c.source_note,
                  l.slug AS home_location_slug, l.name AS home_location_name,
                  r.slug AS region_slug, r.name AS region_name"""
        + _FROM + " WHERE c.slug = %s",
        (slug,),
    )


def relationships_for(character_id):
    return query_all(
        """SELECT 'outgoing' AS direction, cr.relationship_type, cr.description, cr.content_status,
                  o.slug, o.full_name
           FROM character_relationships cr
           JOIN characters o ON o.character_id = cr.to_character_id
           WHERE cr.from_character_id = %s
           UNION ALL
           SELECT 'incoming' AS direction, cr.relationship_type, cr.description, cr.content_status,
                  o.slug, o.full_name
           FROM character_relationships cr
           JOIN characters o ON o.character_id = cr.from_character_id
           WHERE cr.to_character_id = %s
           ORDER BY full_name""",
        (character_id, character_id),
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
