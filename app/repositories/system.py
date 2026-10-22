"""Health and statistics queries."""
from ..db import query_one

# Fixed list of table names: never built from user input.
COUNTED_TABLES = ("regions", "locations", "characters", "vehicles", "missions", "media_assets")


def ping():
    return query_one("SELECT 1 AS ok")


def table_counts():
    return {table: query_one(f"SELECT COUNT(*) AS n FROM {table}")["n"] for table in COUNTED_TABLES}
