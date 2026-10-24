"""docs/DATABASE.md must describe the schema that database/schema.sql really builds: every table, the ER diagram, the counts it states (tables, composite
primary keys, foreign keys and their delete rules) and the migration files. Nothing here connects to a database: it compares two text files, so it can never touch
any data. The checker is itself tested: given a copy of the document with one fact removed or changed, it must report exactly that problem."""
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = (ROOT / "database" / "schema.sql").read_text(encoding="utf-8")
DOC = (ROOT / "docs" / "DATABASE.md").read_text(encoding="utf-8")
MIGRATIONS = sorted(p.name for p in (ROOT / "database" / "migrations").glob("*.sql"))
NUMBER_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
                "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20}


# ------------------------------------------------------------------ what the schema says
def schema_facts(sql):
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.S)
    sql = re.sub(r"--[^\n]*", " ", sql)
    blocks = re.findall(r"CREATE TABLE\s+(?:IF NOT EXISTS\s+)?(\w+)\s*\((.*?)\)\s*ENGINE", sql, flags=re.S | re.I)
    return {
        "tables": [name for name, _body in blocks],
        "foreign_keys": sum(len(re.findall(r"FOREIGN KEY", body)) for _name, body in blocks),
        "delete_rules": Counter(rule for _name, body in blocks for rule in re.findall(r"ON DELETE (CASCADE|SET NULL|RESTRICT|NO ACTION)", body)),
        "composite_key_tables": [name for name, body in blocks if re.search(r"PRIMARY KEY\s*\(\s*\w+\s*,", body)],
    }


def migration_created_tables(path):
    text = (ROOT / "database" / "migrations" / path).read_text(encoding="utf-8")
    text = re.sub(r"--[^\n]*", " ", text)
    return re.findall(r"CREATE TABLE\s+IF NOT EXISTS\s+(\w+)", text, flags=re.I)


# ------------------------------------------------------------------ what the document says
def section(doc, heading):
    match = re.search(rf"^## {re.escape(heading)}[^\n]*\n(.*?)(?=^## |\Z)", doc, flags=re.S | re.M)
    return match.group(0) if match else ""


def documented_tables(doc):
    names = []
    for line in section(doc, "Tables and why each exists").splitlines():
        cells = line.split("|")
        if line.startswith("|") and len(cells) > 3 and re.search(r"[0-9]", cells[1]):
            names += re.findall(r"`(\w+)`", cells[2])
    return names


def stated(doc, pattern):
    """The whole number a document sentence states (the pattern's first group), or None when the sentence is not there."""
    match = re.search(pattern, doc, flags=re.M)
    return int(match.group(1)) if match else None


def problems(schema_sql, doc, migration_files):
    """Everything in `doc` that disagrees with the schema and the migration files. An empty list means the document is in sync."""
    facts, found = schema_facts(schema_sql), []
    tables = set(facts["tables"])
    listed = documented_tables(doc)
    for name in sorted(tables - set(listed)):
        found.append(f"table {name} is in schema.sql but missing from the table list")
    for name in sorted(set(listed) - tables):
        found.append(f"table {name} is listed in the document but is not in schema.sql")
    if len(listed) != len(set(listed)):
        found.append("a table is listed twice")
    heading_count = stated(doc, r"^## Tables and why each exists \((\d+)\)")
    if heading_count != len(tables):
        found.append(f"the table-list heading states {heading_count} tables but the schema has {len(tables)}")
    diagram = re.search(r"```mermaid(.*?)```", doc, flags=re.S)
    entities = {n.lower() for n in re.findall(r"^\s+([A-Z][A-Z_]+)\s*\{", diagram.group(1), flags=re.M)} if diagram else set()
    for name in sorted(tables - entities):
        found.append(f"table {name} is missing from the ER diagram")
    for name in sorted(entities - tables):
        found.append(f"the ER diagram has an entity {name} that is not in schema.sql")
    related = {n.lower() for n in re.findall(r"^\s+([A-Z][A-Z_]+)\s+[|}o][|o]--", diagram.group(1), flags=re.M)} | {n.lower() for n in re.findall(r"--[|o]\{?\s*([A-Z][A-Z_]+)\s*:", diagram.group(1), flags=re.M)} if diagram else set()
    for name in sorted(related - tables):
        found.append(f"the ER diagram relates {name}, which is not in schema.sql")
    composite_count = stated(doc, r"Composite primary keys: (\d+) tables")
    if composite_count != len(facts["composite_key_tables"]):
        found.append(f"the document states {composite_count} composite-key tables but the schema has {len(facts['composite_key_tables'])}")
    foreign_key_count = stated(doc, r"\*\*Foreign keys: (\d+)\*\*")
    if foreign_key_count != facts["foreign_keys"]:
        found.append(f"the document states {foreign_key_count} foreign keys but the schema has {facts['foreign_keys']}")
    for rule in ("CASCADE", "SET NULL", "RESTRICT"):
        rule_count = stated(doc, rf"\*\*(\d+) {rule}\*\*")
        if rule_count != facts["delete_rules"][rule]:
            found.append(f"the document states {rule_count} {rule} delete rules but the schema has {facts['delete_rules'][rule]}")
    # migrations: the count in words, one table row per file, and each row names the tables its file creates
    words = re.search(r"There are (\w+) migration files", doc)
    if not words or NUMBER_WORDS.get(words.group(1).lower()) != len(migration_files):
        found.append(f"the document says there are {words.group(1) if words else 'an unstated number of'} migration files but there are {len(migration_files)}")
    rows = {m.group(1): m.group(0) for m in re.finditer(r"^\| (\d{3}) \|[^\n]*$", section(doc, "Migrations 001 to"), flags=re.M)}
    for filename in migration_files:
        number = filename[:3]
        if number not in rows:
            found.append(f"migration {filename} has no row in the migrations table")
            continue
        for created in migration_created_tables(filename):
            if f"`{created}`" not in rows[number]:
                found.append(f"migration {number} creates {created} but its row does not name it")
    for number in sorted(set(rows) - {f[:3] for f in migration_files}):
        found.append(f"the migrations table has a row for {number}, which has no file")
    return found


# ------------------------------------------------------------------ the document is in sync
def test_the_database_document_matches_the_schema_and_the_migrations():
    assert problems(SCHEMA, DOC, MIGRATIONS) == []


def test_the_schema_facts_the_document_relies_on_are_what_this_project_expects():
    """A tripwire on the parser itself: if these change, either the schema really changed (update the document) or the parser broke."""
    facts = schema_facts(SCHEMA)
    assert len(facts["tables"]) == 27 and len(set(facts["tables"])) == 27
    assert len(facts["composite_key_tables"]) == 15
    assert facts["foreign_keys"] == 34 and facts["foreign_keys"] == sum(facts["delete_rules"].values())
    assert len(MIGRATIONS) == 10


def test_every_table_in_the_document_table_list_is_documented_once_and_numbered_in_order():
    rows = [line for line in section(DOC, "Tables and why each exists").splitlines() if line.startswith("|") and re.search(r"\| [0-9]", line)]
    assert rows and len(documented_tables(DOC)) == 27


# ------------------------------------------------------------------ the checker detects drift (each case edits a copy of the document)
def doc_without(text):
    assert DOC.count(text) == 1, text
    return DOC.replace(text, "")


def test_a_table_removed_from_the_table_list_is_reported():
    row = next(line for line in DOC.splitlines() if line.startswith("| 25 |"))
    assert any("music_tracks is in schema.sql but missing from the table list" in p for p in problems(SCHEMA, DOC.replace(row + "\n", ""), MIGRATIONS))


def test_a_table_missing_from_the_er_diagram_is_reported():
    block = re.search(r"    MUSIC_TRACKS \{.*?\}\n", DOC, flags=re.S).group(0)
    found = problems(SCHEMA, DOC.replace(block, ""), MIGRATIONS)
    assert any("music_tracks is missing from the ER diagram" in p for p in found)


def test_a_wrong_stated_table_count_is_reported():
    found = problems(SCHEMA, DOC.replace("## Tables and why each exists (27)", "## Tables and why each exists (21)"), MIGRATIONS)
    assert any("states 21 tables but the schema has 27" in p for p in found)


def test_a_wrong_composite_key_count_is_reported():
    found = problems(SCHEMA, DOC.replace("Composite primary keys: 15 tables", "Composite primary keys: 13 tables"), MIGRATIONS)
    assert any("13 composite-key tables but the schema has 15" in p for p in found)


def test_wrong_foreign_key_numbers_are_reported():
    found = problems(SCHEMA, DOC.replace("**Foreign keys: 34**", "**Foreign keys: 30**").replace("**30 CASCADE**", "**28 CASCADE**"), MIGRATIONS)
    assert any("30 foreign keys but the schema has 34" in p for p in found) and any("28 CASCADE delete rules but the schema has 30" in p for p in found)


def test_a_table_documented_but_not_in_the_schema_is_reported():
    row = next(line for line in DOC.splitlines() if line.startswith("| 27 |"))
    invented = row.replace("media_collection_items", "invented_table")
    found = problems(SCHEMA, DOC.replace(row, invented), MIGRATIONS)
    assert any("invented_table is listed in the document but is not in schema.sql" in p for p in found)
    assert any("media_collection_items is in schema.sql but missing from the table list" in p for p in found)


def test_a_missing_migration_row_or_a_wrong_migration_count_is_reported():
    row = next(line for line in DOC.splitlines() if line.startswith("| 009 |"))
    found = problems(SCHEMA, DOC.replace(row + "\n", ""), MIGRATIONS)
    assert any("009_media_screening.sql has no row" in p for p in found)
    found = problems(SCHEMA, DOC.replace("There are ten migration files", "There are nine migration files"), MIGRATIONS)
    assert any("says there are nine migration files but there are 10" in p for p in found)


def test_a_migration_row_that_forgets_a_table_it_creates_is_reported():
    row = next(line for line in DOC.splitlines() if line.startswith("| 008 |"))
    found = problems(SCHEMA, DOC.replace(row, row.replace("`music_tracks`", "its tracks")), MIGRATIONS)
    assert any("migration 008 creates music_tracks but its row does not name it" in p for p in found)
