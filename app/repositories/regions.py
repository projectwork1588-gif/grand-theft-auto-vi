"""All SQL for regions."""
from ..db import query_all, query_one


def list_all(status=None):
    where, params = ("WHERE r.content_status = %s", [status]) if status else ("", [])
    return query_all(
        f"""SELECT r.slug, r.name, r.summary, r.content_status,
                   COUNT(l.location_id) AS location_count
            FROM regions r
            LEFT JOIN locations l ON l.region_id = r.region_id
            {where}
            GROUP BY r.region_id, r.slug, r.name, r.summary, r.content_status
            ORDER BY r.name""",
        params,
    )


def get_by_slug(slug):
    return query_one(
        """SELECT region_id, slug, name, summary, description, content_status, source_url, source_note
           FROM regions WHERE slug = %s""",
        (slug,),
    )


def locations_in(region_id):
    return query_all(
        """SELECT slug, name, location_type, summary, content_status
           FROM locations WHERE region_id = %s ORDER BY name""",
        (region_id,),
    )


def characters_based_in(region_id):
    return query_all(
        """SELECT c.slug, c.full_name, c.role_title, c.content_status, l.name AS home_location_name
           FROM characters c
           JOIN locations l ON l.location_id = c.home_location_id
           WHERE l.region_id = %s
           ORDER BY c.full_name""",
        (region_id,),
    )
