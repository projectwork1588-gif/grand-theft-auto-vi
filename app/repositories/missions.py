"""All SQL for missions and story records."""
from ..db import query_all, query_one

SORT_ORDERS = {
    "title_asc": "m.title ASC, m.mission_id ASC",
    "title_desc": "m.title DESC, m.mission_id ASC",
    "type": "m.mission_type ASC, m.title ASC",
    "newest": "m.created_at DESC, m.mission_id DESC",
}

_COUNTS = """
    (SELECT COUNT(*) FROM mission_characters mc WHERE mc.mission_id = m.mission_id) AS cast_count,
    (SELECT COUNT(*) FROM mission_vehicles mv WHERE mv.mission_id = m.mission_id) AS vehicle_count,
    (SELECT COUNT(*) FROM mission_locations ml WHERE ml.mission_id = m.mission_id) AS location_count
"""


def _where(q_like, mission_type, status):
    clauses, params = [], []
    if q_like:
        clauses.append("(m.title LIKE %s ESCAPE '!' OR m.summary LIKE %s ESCAPE '!')")
        params += [q_like, q_like]
    if mission_type:
        clauses.append("m.mission_type = %s")
        params.append(mission_type)
    if status:
        clauses.append("m.content_status = %s")
        params.append(status)
    return (" WHERE " + " AND ".join(clauses)) if clauses else "", params


def search(q_like, mission_type, status, sort, limit, offset):
    where, params = _where(q_like, mission_type, status)
    total = query_one("SELECT COUNT(*) AS n FROM missions m" + where, params)["n"]
    rows = query_all(
        f"""SELECT m.slug, m.title, m.mission_type, m.summary, m.content_status, {_COUNTS}
            FROM missions m""" + where + " ORDER BY " + SORT_ORDERS[sort] + " LIMIT %s OFFSET %s",
        params + [limit, offset],
    )
    return rows, total


def type_counts():
    return query_all(
        "SELECT mission_type, COUNT(*) AS n FROM missions GROUP BY mission_type ORDER BY mission_type")


def get_by_slug(slug):
    return query_one(
        """SELECT mission_id, slug, title, mission_type, summary, synopsis, content_status, source_url, source_note
           FROM missions WHERE slug = %s""",
        (slug,))


def characters_for(mission_id):
    return query_all(
        """SELECT c.slug, c.full_name, c.alias, c.role_title, c.content_status, mc.role_in_mission
           FROM mission_characters mc JOIN characters c ON c.character_id = mc.character_id
           WHERE mc.mission_id = %s ORDER BY c.full_name""",
        (mission_id,))


def vehicles_for(mission_id):
    return query_all(
        """SELECT v.slug, v.name, v.manufacturer, v.content_status, vc.slug AS category_slug,
                  vc.name AS category_name, mv.usage_note
           FROM mission_vehicles mv
           JOIN vehicles v ON v.vehicle_id = mv.vehicle_id
           JOIN vehicle_categories vc ON vc.category_id = v.category_id
           WHERE mv.mission_id = %s ORDER BY v.name""",
        (mission_id,))


def locations_for(mission_id):
    return query_all(
        """SELECT l.slug, l.name, l.location_type, l.content_status, ml.is_primary,
                  r.slug AS region_slug, r.name AS region_name
           FROM mission_locations ml
           JOIN locations l ON l.location_id = ml.location_id
           JOIN regions r ON r.region_id = l.region_id
           WHERE ml.mission_id = %s ORDER BY ml.is_primary DESC, l.name""",
        (mission_id,))


def related(mission_id, limit=4):
    """Other missions that share a character, a location or a vehicle, strongest overlap first."""
    return query_all(
        """SELECT m.slug, m.title, m.mission_type, m.content_status, COUNT(*) AS shared
           FROM missions m
           JOIN (
               SELECT b.mission_id FROM mission_characters a
                 JOIN mission_characters b ON b.character_id = a.character_id AND b.mission_id <> a.mission_id
                 WHERE a.mission_id = %s
               UNION ALL
               SELECT b.mission_id FROM mission_locations a
                 JOIN mission_locations b ON b.location_id = a.location_id AND b.mission_id <> a.mission_id
                 WHERE a.mission_id = %s
               UNION ALL
               SELECT b.mission_id FROM mission_vehicles a
                 JOIN mission_vehicles b ON b.vehicle_id = a.vehicle_id AND b.mission_id <> a.mission_id
                 WHERE a.mission_id = %s
           ) overlap ON overlap.mission_id = m.mission_id
           GROUP BY m.mission_id, m.slug, m.title, m.mission_type, m.content_status
           ORDER BY shared DESC, m.title LIMIT %s""",
        (mission_id, mission_id, mission_id, limit))


def in_region(region_id):
    return query_all(
        """SELECT DISTINCT m.slug, m.title, m.mission_type, m.content_status
           FROM missions m
           JOIN mission_locations ml ON ml.mission_id = m.mission_id
           JOIN locations l ON l.location_id = ml.location_id
           WHERE l.region_id = %s ORDER BY m.title""",
        (region_id,))
