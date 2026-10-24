"""All SQL for site search. Every value reaches MySQL as a bound parameter; the SQL text is built only from the constants in this file and from a count of placeholders.

One statement searches every kind of record at once (UNION ALL), so a search is one round trip. Each kind says which columns it matches, which one is its title (for
ranking) and who may see it, with the same rules as the pages: only official characters and vehicles have public pages, and nothing here selects anything else."""
import logging
import re

from mysql.connector import errors

from ..db import query_all

log = logging.getLogger(__name__)

# The order kinds are listed in when two results rank the same.
KIND_ORDER = ("character", "vehicle", "region", "place", "story", "music")

# Columns: kind, slug, title, detail (a short line under the title), summary, status, anchor (a page section for kinds that share one page), rank.
# `{rank}` is the ranking expression on the title; `{where}` is the per-term match clause. Both are filled with placeholders only.
_SELECTS = {
    "character": """
        SELECT 'character' AS kind,
               c.slug AS slug,
               c.full_name AS title,
               c.role_title AS detail,
               c.summary AS summary,
               c.content_status AS status,
               '' AS anchor,
               {rank:c.full_name} AS rank_
        FROM characters c
        WHERE c.content_status = 'official' AND {where:c.full_name,c.alias,c.role_title,c.summary}""",
    "vehicle": """
        SELECT 'vehicle' AS kind,
               v.slug AS slug,
               v.name AS title,
               v.manufacturer AS detail,
               v.summary AS summary,
               v.content_status AS status,
               '' AS anchor,
               {rank:v.name} AS rank_
        FROM vehicles v
        WHERE v.content_status = 'official' AND {where:v.name,v.manufacturer,v.summary}""",
    "region": """
        SELECT 'region' AS kind,
               r.slug AS slug,
               r.name AS title,
               'Region of Leonida' AS detail,
               r.summary AS summary,
               r.content_status AS status,
               '' AS anchor,
               {rank:r.name} AS rank_
        FROM regions r
        WHERE {where:r.name,r.summary}""",
    "place": """
        SELECT 'place' AS kind,
               l.slug AS slug,
               l.name AS title,
               CONCAT(UPPER(SUBSTRING(l.location_type, 1, 1)), SUBSTRING(l.location_type, 2), ' in ', rg.name) AS detail,
               l.summary AS summary,
               l.content_status AS status,
               '' AS anchor,
               {rank:l.name} AS rank_
        FROM locations l
        JOIN regions rg ON rg.region_id = l.region_id
        WHERE {where:l.name,l.summary,rg.name}""",
    "story": """
        SELECT 'story' AS kind,
               m.slug AS slug,
               m.title AS title,
               CONCAT(UPPER(SUBSTRING(m.mission_type, 1, 1)), SUBSTRING(m.mission_type, 2)) AS detail,
               m.summary AS summary,
               m.content_status AS status,
               '' AS anchor,
               {rank:m.title} AS rank_
        FROM missions m
        WHERE {where:m.title,m.summary,m.mission_type}""",
}

# The Music page holds stations, the score and the album on one page: its search rows say which section to land on.
_MUSIC = (
    """
        SELECT 'music' AS kind,
               s.slug AS slug,
               s.name AS title,
               'Radio station' AS detail,
               LEFT(s.description, 200) AS summary,
               s.content_status AS status,
               'radio' AS anchor,
               {rank:s.name} AS rank_
        FROM radio_stations s
        WHERE {where:s.name,s.hosts,s.description}""",
    """
        SELECT 'music' AS kind,
               mr.slug AS slug,
               mr.title AS title,
               CONCAT_WS(' by ', CONCAT(UPPER(SUBSTRING(mr.kind, 1, 1)), SUBSTRING(mr.kind, 2)), mr.byline) AS detail,
               LEFT(mr.description, 200) AS summary,
               mr.content_status AS status,
               mr.kind AS anchor,
               {rank:mr.title} AS rank_
        FROM music_releases mr
        WHERE {where:mr.title,mr.byline}""",
    """
        SELECT 'music' AS kind,
               mr.slug AS slug,
               t.title AS title,
               CONCAT('Track on ', mr.title, ' by ', t.artists) AS detail,
               '' AS summary,
               mr.content_status AS status,
               mr.kind AS anchor,
               {rank:t.title} AS rank_
        FROM music_tracks t
        JOIN music_releases mr ON mr.release_id = t.release_id
        WHERE {where:t.title,t.artists}""",
)

_RANK_PARAMS = 4          # exact, prefix, word prefix, contains


def _expand(template, terms, phrase_params):
    """Fill {rank:col} and {where:cols} in one SELECT. Returns (sql, params) with the params in the order the placeholders appear."""
    params = []

    def rank(match):
        column = match.group(1)
        params.extend(phrase_params)
        return (f"CASE WHEN {column} = %s THEN 100 WHEN {column} LIKE %s ESCAPE '!' THEN 80 WHEN {column} LIKE %s ESCAPE '!' THEN 60 "
                f"WHEN {column} LIKE %s ESCAPE '!' THEN 40 ELSE 20 END")

    def where(match):
        columns = match.group(1).split(",")
        clauses = []
        for like in terms:
            clauses.append("(" + " OR ".join(f"{column} LIKE %s ESCAPE '!'" for column in columns) + ")")
            params.extend([like] * len(columns))
        return " AND ".join(clauses)

    sql = re.sub(r"\{rank:([^}]+)\}", rank, template)       # the rank sits before the WHERE in the text, so its params come first
    sql = re.sub(r"\{where:([^}]+)\}", where, sql)
    return sql, params


def _union(kinds, terms, phrase_params):
    """The UNION ALL over the wanted kinds, as (sql, params). `kinds` is a subset of KIND_ORDER (already whitelisted by the service)."""
    parts, params = [], []
    templates = [_SELECTS[kind] for kind in kinds if kind in _SELECTS]
    if "music" in kinds:
        templates += list(_MUSIC)
    for template in templates:
        sql, p = _expand(template, terms, phrase_params)
        parts.append(f"({sql.strip()})")
        params += p
    return "\nUNION ALL\n".join(parts), params


def search(kinds, terms, phrase_params, limit, offset):
    """Matching rows, best first. `terms` are LIKE patterns (already escaped, '%word%'); `phrase_params` are the four patterns for the whole phrase
    (exact, prefix, word prefix, contains). Rows: kind, slug, title, detail, summary, status, anchor, rank_."""
    if not kinds:
        return []
    union, params = _union(kinds, terms, phrase_params)
    order = "FIELD(kind, " + ", ".join(["%s"] * len(KIND_ORDER)) + ")"
    sql = f"SELECT * FROM (\n{union}\n) hits ORDER BY rank_ DESC, {order}, title ASC, slug ASC LIMIT %s OFFSET %s"
    return query_all(sql, params + list(KIND_ORDER) + [limit, offset])


# Kinds whose tables come from a later migration (008) than the rest of the schema: a database that has not had it applied has none of them, and the site still works without them
# (the Music page shows an empty page). Only these tables may be missing without it being an error; a missing characters or regions table is a broken database.
OPTIONAL_TABLES = {"music": frozenset({"radio_stations", "music_releases", "music_tracks"})}
TABLE_MISSING = 1146
_MISSING_TABLE = re.compile(r"Table '([^']+)' doesn't exist", re.IGNORECASE)


def missing_optional_kind(exc):
    """The kind whose optional table `exc` reports as missing, or None for anything else: a missing core table, a permission error (1142), a lost connection, bad SQL, or a
    "table missing" message that does not name a table we can recognise. When in doubt it says None, so the error is raised, never hidden."""
    if not isinstance(exc, errors.ProgrammingError) or exc.errno != TABLE_MISSING:
        return None
    found = _MISSING_TABLE.search(str(exc.msg or ""))
    if not found:
        return None
    table = found.group(1).split(".")[-1]                       # the message says 'database.table'
    return next((kind for kind, tables in OPTIONAL_TABLES.items() if table in tables), None)


def tolerant(run, kinds, unavailable):
    """run(kinds), leaving out an optional kind whose tables are missing: that kind is added to `unavailable` (a list the caller owns) and `run` is called again without it.
    `kinds` already in `unavailable` are left out from the start, so a caller that asks twice does not hit the missing table twice. Every other error propagates unchanged."""
    kinds = tuple(k for k in kinds if k not in unavailable)
    while True:
        try:
            return run(kinds)
        except errors.ProgrammingError as exc:
            missing = missing_optional_kind(exc)
            if missing is None or missing not in kinds:
                raise
            log.warning("Search leaves out %s: its tables are missing (%s). Has migration 008 been applied?", missing, exc)
            unavailable.append(missing)
            kinds = tuple(k for k in kinds if k != missing)


def counts(kinds, terms):
    """How many rows each kind matches: {kind: n}. Same filters as search()."""
    if not kinds:
        return {}
    union, params = _union(kinds, terms, ["", "", "", ""])
    rows = query_all(f"SELECT kind, COUNT(*) AS n FROM (\n{union}\n) hits GROUP BY kind", params)
    return {row["kind"]: row["n"] for row in rows}
