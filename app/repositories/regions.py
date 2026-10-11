"""All SQL for regions."""
import logging

from mysql.connector import errors

from ..db import query_all, query_one

log = logging.getLogger(__name__)


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
    """Official characters Rockstar's own text places in this region (character_regions), with what the source says.
    Original characters are not listed on a region page."""
    try:
        return query_all(
            """SELECT c.slug, c.full_name, c.role_title, c.content_status, cg.note AS home_location_name
               FROM character_regions cg
               JOIN characters c ON c.character_id = cg.character_id
               WHERE cg.region_id = %s AND c.content_status = 'official'
               ORDER BY c.full_name""",
            (region_id,),
        )
    except errors.ProgrammingError as exc:
        if exc.errno != 1146:   # table missing: a database that has not had migration 005 applied yet
            raise
        log.warning("Region characters skipped (%s). Has migration 005 been applied?", exc)
        return []


def ids_by_slug(slugs):
    """{slug: region_id}, used to attach media."""
    slugs = list(slugs)
    if not slugs:
        return {}
    marks = ", ".join(["%s"] * len(slugs))
    rows = query_all(f"SELECT slug, region_id FROM regions WHERE slug IN ({marks})", slugs)
    return {row["slug"]: row["region_id"] for row in rows}
