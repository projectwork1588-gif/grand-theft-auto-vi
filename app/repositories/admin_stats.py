"""Read-only statistics for the admin dashboard: aggregates over the tables the site already has. Every statement is a read and every value is a placeholder;
the table names below are a fixed list in this file, never taken from a request."""
from ..db import query_all

# Core tables only (the original schema), so the dashboard works on any database that has the site's base tables.
COUNTED_TABLES = ("users", "characters", "vehicles", "regions", "locations", "missions", "media_assets")


def table_counts():
    """[{name, n}]: how many rows each core table holds (one UNION ALL of fixed counts)."""
    sql = " UNION ALL ".join(f"SELECT '{name}' AS name, COUNT(*) AS n FROM {name}" for name in COUNTED_TABLES)
    return query_all(sql)


def stories_by_status_and_type():
    """GROUP BY on two columns: how many stories of each status and type."""
    return query_all(
        """SELECT content_status, mission_type, COUNT(*) AS n
           FROM missions GROUP BY content_status, mission_type ORDER BY content_status, mission_type""")


def users_by_role():
    return query_all("SELECT role, COUNT(*) AS n FROM users GROUP BY role ORDER BY role")


def favourites_by_kind():
    """[{kind, n}]: favourites saved per kind of record (UNION ALL of the four favourite tables)."""
    return query_all(
        """SELECT 'characters' AS kind, COUNT(*) AS n FROM favourite_characters
           UNION ALL SELECT 'vehicles', COUNT(*) FROM favourite_vehicles
           UNION ALL SELECT 'places', COUNT(*) FROM favourite_locations
           UNION ALL SELECT 'stories', COUNT(*) FROM favourite_missions""")


def top_favourited_stories(limit=5):
    """The stories users have saved most: a JOIN, GROUP BY and ORDER BY ... LIMIT."""
    return query_all(
        """SELECT m.slug, m.title, COUNT(*) AS saved
           FROM favourite_missions f JOIN missions m ON m.mission_id = f.mission_id
           GROUP BY m.mission_id, m.slug, m.title
           ORDER BY saved DESC, m.title LIMIT %s""",
        (limit,))


def stories_without_links(limit=10):
    """Stories that have no character, vehicle or place yet (NOT EXISTS over the three link tables)."""
    return query_all(
        """SELECT m.slug, m.title FROM missions m
           WHERE NOT EXISTS (SELECT 1 FROM mission_characters mc WHERE mc.mission_id = m.mission_id)
             AND NOT EXISTS (SELECT 1 FROM mission_vehicles mv WHERE mv.mission_id = m.mission_id)
             AND NOT EXISTS (SELECT 1 FROM mission_locations ml WHERE ml.mission_id = m.mission_id)
           ORDER BY m.title LIMIT %s""",
        (limit,))
