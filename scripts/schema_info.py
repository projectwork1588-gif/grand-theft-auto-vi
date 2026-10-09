"""Facts about schema.sql shared by the setup scripts (single source of truth)."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "database" / "schema.sql"
SEED = ROOT / "database" / "seed.sql"


def schema_tables():
    """Names of the tables schema.sql creates. These are the ONLY tables our scripts may drop."""
    text = SCHEMA.read_text(encoding="utf-8")
    return tuple(re.findall(r"^CREATE TABLE (\w+)", text, flags=re.MULTILINE))


def table_inventory(cursor, database):
    """Return ({our_table: row_count}, [other_table_names]) for a database that exists."""
    cursor.execute(
        "SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA = %s ORDER BY TABLE_NAME",
        (database,),
    )
    present = [row[0] for row in cursor.fetchall()]
    ours = set(schema_tables())
    counts = {}
    for name in present:
        if name in ours:  # name comes from schema.sql (\w+ only), never from user input
            cursor.execute(f"SELECT COUNT(*) FROM `{database}`.`{name}`")
            counts[name] = cursor.fetchone()[0]
    others = [name for name in present if name not in ours]
    return counts, others
