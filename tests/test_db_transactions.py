"""Phase 2C: who owns a transaction. transaction() may not nest, may not end a transaction it did not open (unless it is only the read snapshot left by
the read helpers), and the read helpers cannot write. Real rows are committed to the *_test database only (tests/account_helpers.py proves the name first)."""
import ast
import re
from pathlib import Path

import pytest

from app.db import TransactionError, get_db, query_all, query_one, transaction
from tests import account_helpers as h

pytestmark = pytest.mark.usefixtures("clean_accounts")
APP = Path(__file__).resolve().parent.parent / "app"
INSERT_USER = "INSERT INTO users (username, password_hash) VALUES (%s, 'x')"


def test_a_transaction_after_reads_commits_and_the_reads_were_only_a_snapshot(app):
    name = h.new_username()
    with app.app_context():
        assert query_one("SELECT COUNT(*) AS n FROM users") is not None
        assert query_all("SELECT slug FROM characters LIMIT 1")
        with transaction() as cursor:
            cursor.execute(INSERT_USER, (name,))
        assert query_one("SELECT user_id FROM users WHERE username = %s", (name,))
    assert h.user_row(name) is not None


def test_a_nested_transaction_is_refused_and_does_not_discard_the_outer_write(app):
    outer, inner = h.new_username(), h.new_username()
    with app.app_context():
        with transaction() as cursor:
            cursor.execute(INSERT_USER, (outer,))
            with pytest.raises(TransactionError, match="nested"):
                with transaction() as other:
                    other.execute(INSERT_USER, (inner,))
        # the outer block caught the refusal and went on: its write is committed
    assert h.user_row(outer) is not None and h.user_row(inner) is None


def test_a_refused_nested_call_leaves_the_outer_block_able_to_roll_back_as_usual(app):
    outer = h.new_username()
    with app.app_context():
        with pytest.raises(RuntimeError, match="boom"):
            with transaction() as cursor:
                cursor.execute(INSERT_USER, (outer,))
                try:
                    with transaction():
                        pass
                except TransactionError:
                    pass
                raise RuntimeError("boom")
    assert h.user_row(outer) is None


def test_the_ownership_flag_is_cleared_after_every_block(app):
    first, second, third = (h.new_username() for _ in range(3))
    with app.app_context():
        with pytest.raises(RuntimeError):
            with transaction() as cursor:
                cursor.execute(INSERT_USER, (first,))
                raise RuntimeError("fails")
        with transaction() as cursor:                                         # a block after a failed block works
            cursor.execute(INSERT_USER, (second,))
        with transaction() as cursor:
            cursor.execute(INSERT_USER, (third,))
    assert h.user_row(first) is None and h.user_row(second) and h.user_row(third)


@pytest.mark.parametrize("sql", [
    "INSERT INTO users (username, password_hash) VALUES ('tt_via_read', 'x')",
    "  update users set role = 'admin'",
    "DELETE FROM users",
    "/* a comment first */ DROP TABLE users",
    "TRUNCATE users",
    "set autocommit = 1",
    "COMMIT",
    "rollback",
    "ALTER TABLE users ADD COLUMN x INT",
    "REPLACE INTO users (username, password_hash) VALUES ('tt_replace', 'x')",
])
def test_the_read_helpers_refuse_anything_that_writes(app, sql):
    with app.app_context():
        with pytest.raises(TransactionError, match="read-only"):
            query_all(sql)
        with pytest.raises(TransactionError):
            query_one(sql)
    assert h.rows("SELECT COUNT(*) AS n FROM users WHERE username IN ('tt_via_read', 'tt_replace')")[0]["n"] == 0
    assert h.rows("SELECT COUNT(*) AS n FROM users WHERE role = 'admin'")[0]["n"] == 0


@pytest.mark.parametrize("sql", ["SELECT 1 AS one", "  select 1 as one", "WITH t AS (SELECT 1 AS one) SELECT one FROM t", "(SELECT 1 AS one) UNION (SELECT 2)", "SHOW TABLES", "/* c */ SELECT 1 AS one"])
def test_the_read_helpers_accept_reads(app, sql):
    with app.app_context():
        assert query_all(sql)


def test_a_raw_write_is_never_rolled_back_by_a_later_transaction(app):
    """Someone used get_db() directly and has an uncommitted write. transaction() must not quietly throw it away: it refuses, and the write survives."""
    raw, later = h.new_username(), h.new_username()
    with app.app_context():
        cursor = get_db().cursor()
        cursor.execute(INSERT_USER, (raw,))
        cursor.close()
        assert get_db().in_transaction, "the premise of this test: the connection holds an uncommitted write"
        with pytest.raises(TransactionError, match="get_db"):
            with transaction() as other:
                other.execute(INSERT_USER, (later,))
        get_db().commit()                                                      # the owner of the raw write decides; here it keeps it
    assert h.user_row(raw) is not None and h.user_row(later) is None


def test_after_the_raw_work_is_committed_a_transaction_works_again(app):
    raw, later = h.new_username(), h.new_username()
    with app.app_context():
        cursor = get_db().cursor()
        cursor.execute(INSERT_USER, (raw,))
        cursor.close()
        get_db().commit()
        with transaction() as cursor:
            cursor.execute(INSERT_USER, (later,))
    assert h.user_row(raw) and h.user_row(later)


def test_a_raw_read_that_leaves_a_snapshot_is_also_refused_not_silently_ended(app):
    """After get_db() the helper cannot tell a read snapshot from a write, so it errs on the side of refusing."""
    name = h.new_username()
    with app.app_context():
        cursor = get_db().cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        cursor.fetchall()
        cursor.close()
        if get_db().in_transaction:
            with pytest.raises(TransactionError):
                with transaction():
                    pass
            get_db().rollback()
        with transaction() as cursor:
            cursor.execute(INSERT_USER, (name,))
    assert h.user_row(name) is not None


def test_a_database_error_inside_a_block_rolls_back_and_re_raises(app):
    import mysql.connector
    name = h.new_username()
    with app.app_context():
        with pytest.raises(mysql.connector.Error):
            with transaction() as cursor:
                cursor.execute(INSERT_USER, (name,))
                cursor.execute("INSERT INTO favourite_characters (user_id, character_id) VALUES (99999999, 1)")
    assert h.user_row(name) is None


# ------------------------------------------------------------------ the rules hold for the whole application (static)
def app_sources():
    return {path.relative_to(APP).as_posix(): path.read_text(encoding="utf-8") for path in APP.rglob("*.py")}


def test_application_code_never_uses_the_raw_connection_or_a_cursor_of_its_own():
    offenders = [name for name, text in app_sources().items() if name != "db.py" and re.search(r"\bget_db\(|\.cursor\(|\.commit\(|\.rollback\(|\.autocommit\b", text)]
    assert offenders == [], offenders


# The application's writers. The account repositories keep the original, strict line rule exactly as it was. The admin repository (Stories) is a deliberate, reviewed
# addition and is held to a precise, stricter rule: every execute is inside a transaction block, directly or through a helper that is only called from inside one.
ACCOUNT_WRITERS = {"repositories/users.py", "repositories/favourites.py"}
ADMIN_WRITERS = {"repositories/admin_stories.py", "repositories/admin_locations.py"}


def transaction_rule_violations(source):
    """Every `cursor.execute(...)` in `source` must be inside a `with transaction() as cursor:` block, or inside a function that takes `cursor` as a parameter AND is
    only ever called from inside such a block. Returns the list of violations (empty when the rule holds)."""
    tree = ast.parse(source)
    parents = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}

    def ancestors(node):
        while node in parents:
            node = parents[node]
            yield node

    def in_block(node):
        for owner in ancestors(node):
            if isinstance(owner, ast.With):
                for item in owner.items:
                    call, var = item.context_expr, item.optional_vars
                    if isinstance(call, ast.Call) and getattr(call.func, "id", "") == "transaction" and isinstance(var, ast.Name) and var.id == "cursor":
                        return True
        return False

    violations, helpers = [], set()
    for node in ast.walk(tree):
        is_execute = (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in ("execute", "executemany")
                      and isinstance(node.func.value, ast.Name) and node.func.value.id == "cursor")
        if is_execute and not in_block(node):
            function = next((o for o in ancestors(node) if isinstance(o, ast.FunctionDef)), None)
            if function is not None and any(arg.arg == "cursor" for arg in function.args.args):
                helpers.add(function.name)
            else:
                violations.append(f"line {node.lineno}: cursor.{node.func.attr} outside a transaction block")
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in helpers and not in_block(node):
            violations.append(f"line {node.lineno}: {node.func.id}() is called outside a transaction block")
    return violations


def test_every_statement_that_writes_is_inside_a_transaction_block():
    writers, sources = {}, app_sources()
    for name, text in sources.items():
        lines = text.splitlines()
        for number, line in enumerate(lines):
            if "cursor.execute(" in line and name != "db.py":
                writers.setdefault(name, []).append(any("with transaction() as cursor" in lines[j] for j in range(max(0, number - 2), number)))
    assert set(writers) == ACCOUNT_WRITERS | ADMIN_WRITERS
    assert all(all(flags) for name, flags in writers.items() if name in ACCOUNT_WRITERS), writers          # the original rule, unchanged, for the account repositories
    for name in ADMIN_WRITERS:
        assert transaction_rule_violations(sources[name]) == [], name


def test_the_transaction_rule_checker_catches_what_it_is_meant_to_catch():
    """The checker is itself tested: a write outside a block, or a helper called from outside one, must be reported; correct code must pass."""
    good = ("def helper(cursor, x):\n    cursor.execute('INSERT', x)\n\n\n"
            "def write():\n    with transaction() as cursor:\n        helper(cursor, 1)\n        cursor.execute('UPDATE')\n")
    loose = "def write(cursor):\n    cursor.execute('INSERT')\n\n\ndef caller():\n    write(None)\n"
    loose_helper_call = ("def helper(cursor):\n    cursor.execute('INSERT')\n\n\ndef caller(cursor):\n    helper(cursor)\n")
    bare = "def write(connection):\n    cursor = connection.cursor()\n    cursor.execute('INSERT')\n"
    assert transaction_rule_violations(good) == []
    assert any("outside a transaction block" in v for v in transaction_rule_violations(bare))
    assert any("helper() is called outside a transaction block" in v for v in transaction_rule_violations(loose_helper_call))
    assert any("write() is called outside a transaction block" in v for v in transaction_rule_violations(loose))
    assert transaction_rule_violations("def helper(cursor):\n    cursor.execute('INSERT')\n") == []      # a helper nobody calls from outside a block may exist on its own


def test_no_write_sql_exists_outside_the_writer_repositories():
    pattern = re.compile(r"[\"'](\s*)(INSERT\s+INTO|UPDATE\s+\w+\s+SET|DELETE\s+FROM|REPLACE\s+INTO)\b", re.IGNORECASE)
    offenders = [name for name, text in app_sources().items() if pattern.search(text) and name not in ACCOUNT_WRITERS | ADMIN_WRITERS]
    assert offenders == [], offenders
