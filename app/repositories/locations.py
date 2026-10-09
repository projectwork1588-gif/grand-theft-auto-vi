"""All SQL for locations (places inside a region)."""
from ..db import query_all, query_one

SORT_ORDERS = {
    "name_asc": "l.name ASC, l.location_id ASC",
    "name_desc": "l.name DESC, l.location_id ASC",
    "region": "r.name ASC, l.name ASC",
    "newest": "l.created_at DESC, l.location_id DESC",
}

_FROM = " FROM locations l JOIN regions r ON r.region_id = l.region_id "


def _where(q_like, region, location_type, status):
    clauses, params = [], []
    if q_like:
        clauses.append("(l.name LIKE %s ESCAPE '!' OR l.summary LIKE %s ESCAPE '!')")
        params += [q_like, q_like]
    if region:
        clauses.append("r.slug = %s")
        params.append(region)
    if location_type:
        clauses.append("l.location_type = %s")
        params.append(location_type)
    if status:
        clauses.append("l.content_status = %s")
        params.append(status)
    return (" WHERE " + " AND ".join(clauses)) if clauses else "", params


def search(q_like, region, location_type, status, sort, limit, offset):
    where, params = _where(q_like, region, location_type, status)
    total = query_one("SELECT COUNT(*) AS n" + _FROM + where, params)["n"]
    rows = query_all(
        """SELECT l.slug, l.name, l.location_type, l.summary, l.content_status,
                  r.slug AS region_slug, r.name AS region_name,
                  (SELECT COUNT(*) FROM mission_locations ml WHERE ml.location_id = l.location_id) AS mission_count"""
        + _FROM + where + " ORDER BY " + SORT_ORDERS[sort] + " LIMIT %s OFFSET %s",
        params + [limit, offset],
    )
    return rows, total


def get_by_slug(slug):
    return query_one(
        """SELECT l.location_id, l.region_id, l.slug, l.name, l.location_type, l.summary, l.description,
                  l.content_status, l.source_url, l.source_note,
                  r.slug AS region_slug, r.name AS region_name, r.content_status AS region_status"""
        + _FROM + " WHERE l.slug = %s",
        (slug,))


def residents(location_id):
    return query_all(
        """SELECT slug, full_name, role_title, content_status
           FROM characters WHERE home_location_id = %s ORDER BY full_name""",
        (location_id,))


def characters_in_missions_here(location_id):
    return query_all(
        """SELECT DISTINCT c.slug, c.full_name, c.role_title, c.content_status
           FROM mission_locations ml
           JOIN mission_characters mc ON mc.mission_id = ml.mission_id
           JOIN characters c ON c.character_id = mc.character_id
           WHERE ml.location_id = %s ORDER BY c.full_name""",
        (location_id,))


def missions_here(location_id):
    return query_all(
        """SELECT m.slug, m.title, m.mission_type, m.content_status, ml.is_primary
           FROM mission_locations ml JOIN missions m ON m.mission_id = ml.mission_id
           WHERE ml.location_id = %s ORDER BY ml.is_primary DESC, m.title""",
        (location_id,))


def neighbours(region_id, exclude_id, limit=6):
    return query_all(
        """SELECT slug, name, location_type, content_status
           FROM locations WHERE region_id = %s AND location_id <> %s ORDER BY name LIMIT %s""",
        (region_id, exclude_id, limit))
