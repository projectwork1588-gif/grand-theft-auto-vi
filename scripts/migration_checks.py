"""Read-only checks that run before a single migration is applied with `scripts.migrate_db --only <file>`.

Each check function takes a cursor (the migration account only SELECTs here), and returns (notes, problems):
  * notes    lines that describe what was found (shown in the plan);
  * problems lines that BLOCK the migration: a missing prerequisite, or data that would be overwritten because it belongs to something else.
Nothing is written. A migration with no entry in CHECKS is simply applied (after the usual non-destructive check).

Migration 006 expects: the tables and columns it writes to; the foreign keys that tie vehicles, media and categories together; the categories
5 (boat) and 6 (motorcycle); the five official vehicles from migration 002 (ids 9 to 13); and ids 14, 15 (vehicles) and 108 to 114 (media) to be free or
already hold exactly what 006 puts there (a second run). Anything else on those ids, slugs or names is a conflict, because the migration's
INSERT ... ON DUPLICATE KEY UPDATE would overwrite it.
"""

# ---- what migration 006 puts in place (tests/test_gate3b_migration.py checks these against the migrated database)
M006_VEHICLES = {14: ("dinka-enduro", "Dinka Enduro Motorcycle", 6), 15: ("crest-kayak", "Crest Kayak", 5)}
M006_MEDIA = {108: "vehicle-dinka-enduro-01", 109: "vehicle-crest-kayak-01", 110: "garage-jasons-safehouse", 111: "garage-rideout-customs-01",
              112: "garage-one-eyed-willies-01", 113: "garage-classic-cars-02", 114: "garage-classic-cars-04"}
M006_LINKS = {(108, 14), (109, 15), (110, 14), (110, 15)}
M006_CATEGORIES = {5: "boat", 6: "motorcycle"}
M006_REWORDED = {9: "grotti-cheetah", 10: "vapid-dominator-buggy", 11: "shitzu-squalo", 12: "vapid-stanier", 13: "vapid-ganado"}
M006_REWORDED_TEXT = {   # the wording the migration sets (summary), to tell the owner which rows it would change
    "grotti-cheetah": "A white coupe with red racing stripes, caught at golden hour.",
    "vapid-dominator-buggy": "A Dominator rebuilt for mud and dirt.",
    "shitzu-squalo": "A white speedboat on the bay at dusk.",
    "vapid-stanier": "A yellow-and-white cruiser under the neon.",
    "vapid-ganado": "A retro pickup with racing stripes on the coast road.",
}
M006_COLUMNS = {
    "vehicles": ["vehicle_id", "category_id", "slug", "name", "manufacturer", "summary", "description", "content_status", "source_url", "source_note"],
    "vehicle_categories": ["category_id", "slug"],
    "media_assets": ["media_id", "slug", "title", "media_type", "intended_use", "source_url", "embed_url", "local_path", "attribution",
                     "usage_status", "approval_status", "notes"],
    "media_vehicles": ["media_id", "vehicle_id"],
}
M006_FOREIGN_KEYS = [   # (table, column, referenced table, referenced column)
    ("vehicles", "category_id", "vehicle_categories", "category_id"),
    ("media_vehicles", "media_id", "media_assets", "media_id"),
    ("media_vehicles", "vehicle_id", "vehicles", "vehicle_id"),
]


def check_006(cursor, database):
    notes, problems = [], []

    def q(sql, params=()):
        cursor.execute(sql, params)
        return cursor.fetchall()

    # 1. tables and columns
    present = {}
    for table in M006_COLUMNS:
        rows = q("SELECT COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s", (database, table))
        present[table] = {r[0] for r in rows}
        if not present[table]:
            problems.append(f"table '{table}' does not exist (migrations 001 to 005 must be applied first)")
            continue
        missing = [c for c in M006_COLUMNS[table] if c not in present[table]]
        if missing:
            problems.append(f"table '{table}' lacks column(s) {', '.join(missing)}")
    if problems:
        return notes, problems                      # the rest cannot be judged without the tables
    notes.append("tables and columns: vehicles, vehicle_categories, media_assets, media_vehicles are all present")

    # 2. foreign keys
    for table, column, ref_table, ref_column in M006_FOREIGN_KEYS:
        rows = q("SELECT COUNT(*) FROM information_schema.KEY_COLUMN_USAGE WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND COLUMN_NAME = %s "
                 "AND REFERENCED_TABLE_NAME = %s AND REFERENCED_COLUMN_NAME = %s", (database, table, column, ref_table, ref_column))
        if not rows[0][0]:
            problems.append(f"foreign key {table}.{column} -> {ref_table}.{ref_column} is missing")
    if not any(p.startswith("foreign key") for p in problems):
        notes.append("foreign keys: vehicles -> categories, media_vehicles -> media and vehicles are in place")

    # 3. categories
    cats = dict(q("SELECT category_id, slug FROM vehicle_categories WHERE category_id IN (5, 6)"))
    wrong = [f"vehicle category {cid} should be '{slug}' but is {cats.get(cid)!r}" for cid, slug in M006_CATEGORIES.items() if cats.get(cid) != slug]
    problems.extend(wrong)
    if not wrong:
        notes.append("categories: 5 = boat, 6 = motorcycle")

    # 4. the five official vehicles the migration rewords must exist (they come from migration 002)
    have = {r[0]: (r[1], r[2], r[3]) for r in q("SELECT vehicle_id, slug, content_status, summary FROM vehicles WHERE vehicle_id BETWEEN 9 AND 13")}
    stale = []
    for vid, slug in M006_REWORDED.items():
        if vid not in have or have[vid][0] != slug:
            stale.append(f"official vehicle {vid} should be '{slug}' (from migration 002) but is {have.get(vid, ('missing',))[0]!r}")
        elif have[vid][1] != "official":
            stale.append(f"vehicle '{slug}' is not marked official; the migration only rewords official vehicles")
    problems.extend(stale)
    if not stale:
        changing = [M006_REWORDED[v] for v in M006_REWORDED if have[v][2] != M006_REWORDED_TEXT[M006_REWORDED[v]]]
        notes.append("existing official vehicles 9 to 13 found; wording (summary and description) will be set on: " + (", ".join(changing) if changing else "none (already current)"))

    # 5. vehicle ids, slugs and names the migration adds
    for vid, (slug, name, cat) in M006_VEHICLES.items():
        by_id = q("SELECT slug, name, category_id FROM vehicles WHERE vehicle_id = %s", (vid,))
        by_slug = q("SELECT vehicle_id FROM vehicles WHERE slug = %s AND vehicle_id <> %s", (slug, vid))
        by_name = q("SELECT vehicle_id FROM vehicles WHERE name = %s AND vehicle_id <> %s", (name, vid))
        if by_id and by_id[0][:2] != (slug, name):
            problems.append(f"vehicle id {vid} already holds '{by_id[0][0]}' ({by_id[0][1]}); the migration would overwrite it")
        if by_slug:
            problems.append(f"slug '{slug}' already belongs to vehicle id {by_slug[0][0]}, not {vid}")
        if by_name:
            problems.append(f"name '{name}' already belongs to vehicle id {by_name[0][0]}, not {vid}")
        if not (by_id or by_slug or by_name):
            notes.append(f"vehicle id {vid} ({name}): free, will be added")
        elif by_id and by_id[0][:2] == (slug, name) and not (by_slug or by_name):
            notes.append(f"vehicle id {vid} ({name}): already present, will be refreshed with the same content")

    # 6. media ids and slugs
    for mid, slug in M006_MEDIA.items():
        by_id = q("SELECT slug FROM media_assets WHERE media_id = %s", (mid,))
        by_slug = q("SELECT media_id FROM media_assets WHERE slug = %s AND media_id <> %s", (slug, mid))
        if by_id and by_id[0][0] != slug:
            problems.append(f"media id {mid} already holds '{by_id[0][0]}'; the migration would overwrite it")
        if by_slug:
            problems.append(f"media slug '{slug}' already belongs to media id {by_slug[0][0]}, not {mid}")
    ids = [r[0] for r in q("SELECT media_id FROM media_assets WHERE media_id BETWEEN 108 AND 114")]
    notes.append(f"media ids 108 to 114: {len(ids)} already present, {len(M006_MEDIA) - len(ids)} will be added")

    # 7. links: the migration adds four; any other link on its pictures or vehicles is reported, never changed
    links = {(r[0], r[1]) for r in q("SELECT media_id, vehicle_id FROM media_vehicles WHERE media_id BETWEEN 108 AND 114 OR vehicle_id IN (14, 15)")}
    stray = sorted(links - M006_LINKS)
    if stray:
        problems.append("media_vehicles already links other pairs to the migration's pictures or vehicles: " + ", ".join(f"(media {m}, vehicle {v})" for m, v in stray))
    notes.append(f"media_vehicles: {len(links & M006_LINKS)} of the 4 links already present, {len(M006_LINKS - links)} will be added")

    # 8. what is there now
    official = q("SELECT COUNT(*) FROM vehicles WHERE content_status = 'official'")[0][0]
    notes.append(f"now: {official} official vehicles in the database")
    return notes, problems


def after_006(cursor):
    """What is stored after the migration, for the report (read on a new connection)."""
    cursor.execute("SELECT COUNT(*) FROM vehicles WHERE content_status = 'official'")
    official = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM vehicles WHERE vehicle_id IN (14, 15)")
    added = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM media_assets WHERE media_id BETWEEN 108 AND 114")
    media = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM media_vehicles WHERE media_id BETWEEN 108 AND 114")
    links = cursor.fetchone()[0]
    ok = official == 7 and added == 2 and media == 7 and links == 4
    return f"After 006: {official} official vehicles (expected 7), vehicles 14 and 15 present: {added}/2, media 108 to 114: {media}/7, links: {links}/4 - {'OK' if ok else 'CHECK THIS'}"


# ---- migration 010: users.email may be NULL (accounts sign up with a username and a password only)
M010_COLUMN_TYPE = "varchar(254)"
M010_UNIQUE_INDEX = "uq_users_email"


def _email_column(cursor, database):
    cursor.execute("SELECT COLUMN_TYPE, IS_NULLABLE FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'users' AND COLUMN_NAME = 'email'", (database,))
    return cursor.fetchone()


def _email_unique(cursor, database):
    cursor.execute("SELECT COUNT(*) FROM information_schema.STATISTICS WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'users' AND INDEX_NAME = %s AND NON_UNIQUE = 0",
                   (database, M010_UNIQUE_INDEX))
    return cursor.fetchone()[0] > 0


def check_010(cursor, database):
    """010 relaxes ONE column. It needs the users table and that column, exactly as schema.sql defines it: with any other type the ALTER would also
    change the type (and could shorten stored emails), so that blocks it. Reads only; counts rows without reading any of them."""
    notes, problems = [], []
    cursor.execute("SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'users'", (database,))
    if not cursor.fetchone()[0]:
        return notes, ["table 'users' does not exist (build the schema first: scripts.init_db)"]
    column = _email_column(cursor, database)
    if column is None:
        return notes, ["table 'users' has no column 'email', so there is nothing for 010 to relax"]
    column_type, nullable = str(column[0]).lower(), column[1]
    if column_type != M010_COLUMN_TYPE:
        problems.append(f"users.email is {column_type}, not {M010_COLUMN_TYPE}: the migration would change its type as well as its nullability")
    if nullable == "YES":
        notes.append("users.email is already nullable: running 010 changes nothing")
    else:
        notes.append("users.email is NOT NULL now; 010 makes it nullable")
    notes.append(f"unique index {M010_UNIQUE_INDEX}: {'present, it stays' if _email_unique(cursor, database) else 'ABSENT (not created by 010; check schema.sql)'}")
    cursor.execute("SELECT COUNT(*) FROM users")
    notes.append(f"users holds {cursor.fetchone()[0]} account(s); none is changed (the ALTER only drops the NOT NULL rule)")
    notes.append("rollback note: once any account has no email, `MODIFY email ... NOT NULL` fails; undoing 010 then needs a decision about those accounts")
    return notes, problems


def after_010(cursor):
    """What is stored after the migration (read on a new connection)."""
    cursor.execute("SELECT DATABASE()")
    database = cursor.fetchone()[0]
    column = _email_column(cursor, database)
    unique = _email_unique(cursor, database)
    ok = column is not None and str(column[0]).lower() == M010_COLUMN_TYPE and column[1] == "YES" and unique
    return f"After 010: users.email is {column[0] if column else 'MISSING'}, nullable: {column[1] if column else '?'}, unique index kept: {unique} - {'OK' if ok else 'CHECK THIS'}"


CHECKS = {"006_gate3b_garage.sql": (check_006, after_006), "010_account_email_optional.sql": (check_010, after_010)}
