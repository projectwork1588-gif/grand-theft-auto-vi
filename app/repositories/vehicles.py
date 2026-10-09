"""All SQL for vehicles and vehicle categories. Every value is a bound parameter."""
from ..db import query_all, query_one

SORT_ORDERS = {
    "name_asc": "v.name ASC, v.vehicle_id ASC",
    "name_desc": "v.name DESC, v.vehicle_id ASC",
    "category": "vc.name ASC, v.name ASC",
    "newest": "v.created_at DESC, v.vehicle_id DESC",
}

_FROM = " FROM vehicles v JOIN vehicle_categories vc ON vc.category_id = v.category_id "


def _where(q_like, category, status):
    clauses, params = [], []
    if q_like:
        clauses.append("(v.name LIKE %s ESCAPE '!' OR v.manufacturer LIKE %s ESCAPE '!' OR v.summary LIKE %s ESCAPE '!')")
        params += [q_like, q_like, q_like]
    if category:
        clauses.append("vc.slug = %s")
        params.append(category)
    if status:
        clauses.append("v.content_status = %s")
        params.append(status)
    return (" WHERE " + " AND ".join(clauses)) if clauses else "", params


def search(q_like, category, status, sort, limit, offset):
    where, params = _where(q_like, category, status)
    total = query_one("SELECT COUNT(*) AS n" + _FROM + where, params)["n"]
    rows = query_all(
        """SELECT v.slug, v.name, v.manufacturer, v.summary, v.content_status,
                  vc.slug AS category_slug, vc.name AS category_name"""
        + _FROM + where + " ORDER BY " + SORT_ORDERS[sort] + " LIMIT %s OFFSET %s",
        params + [limit, offset],
    )
    return rows, total


def categories_with_counts():
    return query_all(
        """SELECT vc.slug, vc.name, vc.description, COUNT(v.vehicle_id) AS vehicle_count
           FROM vehicle_categories vc
           LEFT JOIN vehicles v ON v.category_id = vc.category_id
           GROUP BY vc.category_id, vc.slug, vc.name, vc.description
           ORDER BY vc.name""")


def get_by_slug(slug):
    return query_one(
        """SELECT v.vehicle_id, v.category_id, v.slug, v.name, v.manufacturer, v.summary, v.description,
                  v.content_status, v.source_url, v.source_note,
                  vc.slug AS category_slug, vc.name AS category_name, vc.description AS category_description"""
        + _FROM + " WHERE v.slug = %s",
        (slug,),
    )


def missions_for(vehicle_id):
    return query_all(
        """SELECT m.slug, m.title, m.mission_type, m.content_status, mv.usage_note
           FROM mission_vehicles mv JOIN missions m ON m.mission_id = mv.mission_id
           WHERE mv.vehicle_id = %s ORDER BY m.title""",
        (vehicle_id,))


def locations_for(vehicle_id):
    """Locations reached through the vehicle's missions, with their region."""
    return query_all(
        """SELECT DISTINCT l.slug, l.name, l.content_status, r.slug AS region_slug, r.name AS region_name
           FROM mission_vehicles mv
           JOIN mission_locations ml ON ml.mission_id = mv.mission_id
           JOIN locations l ON l.location_id = ml.location_id
           JOIN regions r ON r.region_id = l.region_id
           WHERE mv.vehicle_id = %s ORDER BY l.name""",
        (vehicle_id,))


def same_category(category_id, exclude_id, limit=4):
    return query_all(
        """SELECT v.slug, v.name, v.manufacturer, v.summary, v.content_status,
                  vc.slug AS category_slug, vc.name AS category_name
           FROM vehicles v JOIN vehicle_categories vc ON vc.category_id = v.category_id
           WHERE v.category_id = %s AND v.vehicle_id <> %s ORDER BY v.name LIMIT %s""",
        (category_id, exclude_id, limit))


def featured(limit=4):
    """One vehicle from each of the first categories, so the homepage shows variety."""
    return query_all(
        """SELECT v.slug, v.name, v.manufacturer, v.summary, v.content_status,
                  vc.slug AS category_slug, vc.name AS category_name
           FROM vehicles v JOIN vehicle_categories vc ON vc.category_id = v.category_id
           WHERE v.vehicle_id IN (SELECT MIN(vehicle_id) FROM vehicles GROUP BY category_id)
           ORDER BY vc.category_id LIMIT %s""",
        (limit,))
