"""Database access helpers: a lazily created connection pool and one connection per request.

Who owns what (the rules every caller follows):

* READS go through query_all() / query_one(). They refuse anything that does not look like a single read statement (is_read_only: a text check that also
  catches a write hidden behind a comment or inside WITH ... DELETE). That is a safety net against mistakes, not a guarantee about arbitrary SQL.
  The connection is not in autocommit mode, so a SELECT opens an implicit transaction (a read snapshot) that stays open until the connection is reset.
* WRITES go through transaction(), and only there. transaction() OWNS the unit of work: it starts it, commits it on success, rolls it back on any error.
  It never runs inside another transaction() (nesting raises TransactionError) and it never ends a transaction it did not open unless that transaction
  is provably read-only: before opening its own, it ends the implicit read snapshot left by query_all()/query_one() (which cannot hold a write).
* get_db() is the raw connection, for code that manages its own statements (the test suite, diagnostics). Using it marks the request: if a transaction is
  open after raw use, transaction() cannot know what is in it, so it raises TransactionError instead of rolling it back. Commit or roll back first.

Repositories never build SQL from user input; values are always placeholders.
"""
import re
import threading
import uuid
from contextlib import contextmanager
from functools import lru_cache

import mysql.connector
from flask import current_app, g
from mysql.connector import pooling

_pool_lock = threading.Lock()


def _get_pool(app):
    """Create the pool on first use so the app can start (and show a clear error) without MySQL."""
    with _pool_lock:
        pool = app.extensions.get("db_pool")
        if pool is None:
            config = app.config["DB_CONFIG"]
            pool = pooling.MySQLConnectionPool(
                pool_name=f"valkyrie_{uuid.uuid4().hex[:8]}",
                pool_size=app.config["DB_POOL_SIZE"],
                **config.db_kwargs(),
            )
            app.extensions["db_pool"] = pool
        return pool


class TransactionError(RuntimeError):
    """The transaction rules above were broken (a nested transaction(), a write through a read helper, or an unknown open transaction)."""


# ---- the read-only check used by query_all()/query_one()
# A SAFETY NET AGAINST MISTAKES, not a security boundary. It looks at the statement's text: after comments and quoted text are removed, the statement must be
# ONE statement that starts with a read verb and must not contain a word that writes anywhere in it (that is what catches 'WITH x AS (...) DELETE FROM ...'
# and a write hidden behind a leading comment). It cannot know what a stored function or an unusual construct does, and the website's database account can
# still write: the real protections are that values are always placeholders, identifiers come from fixed maps, and nothing builds SQL from user input.
_READ_VERBS = frozenset({"select", "with", "show", "explain", "describe", "desc", "values", "table"})
# Words that write or change the schema. insert( and replace( with a bracket are the string functions, not statements.
_WRITE_WORD = re.compile(r"\b(?:insert(?!\s*\()|update|delete|replace(?!\s*\()|truncate|drop|alter|create|rename|grant|revoke)\b", re.IGNORECASE)
_LOCKING_READ = re.compile(r"\bfor\s+(?:update|share)\b", re.IGNORECASE)
_INTO_FILE = re.compile(r"\binto\s+(?:outfile|dumpfile)\b", re.IGNORECASE)
_FIRST_WORD = re.compile(r"[\s(]*([a-z]+)", re.IGNORECASE)


def _bare_sql(sql):
    """The statement with comments and quoted text (strings, identifiers in backticks) replaced by a space; None if it holds an executable comment
    (/*! ... */ runs as SQL in MySQL, so such a statement is never accepted as a read)."""
    out, i, n = [], 0, len(sql)
    while i < n:
        c = sql[i]
        if c in "'\"`":
            quote = c
            i += 1
            while i < n:
                if sql[i] == "\\" and quote != "`":
                    i += 2
                    continue
                if sql[i] == quote:
                    if i + 1 < n and sql[i + 1] == quote:        # a doubled quote is a quote inside the text
                        i += 2
                        continue
                    break
                i += 1
            i += 1
            out.append(" ")
        elif sql.startswith("/*!", i):
            return None
        elif sql.startswith("/*", i):
            end = sql.find("*/", i + 2)
            i = n if end == -1 else end + 2
            out.append(" ")
        elif c == "#" or (sql.startswith("--", i) and (i + 2 >= n or sql[i + 2] in " \t\r\n\x0b\x0c")):
            end = sql.find("\n", i)
            i = n if end == -1 else end + 1
            out.append(" ")
        else:
            out.append(c)
            i += 1
    return "".join(out)


@lru_cache(maxsize=2048)
def is_read_only(sql):
    """True when `sql` looks like a single read statement (see the note above: a text check, not a guarantee)."""
    body = _bare_sql(sql)
    if body is None:
        return False
    body = _LOCKING_READ.sub(" ", body).strip()
    if body.endswith(";"):
        body = body[:-1]
    if ";" in body:                                          # a second statement
        return False
    first = _FIRST_WORD.match(body)
    if not first or first.group(1).lower() not in _READ_VERBS:
        return False
    return not (_WRITE_WORD.search(body) or _INTO_FILE.search(body))


def _connection():
    """This request's connection (created on first use). Used by the helpers in this module; it does not mark the request."""
    if "db" not in g:
        g.db = _get_pool(current_app).get_connection()
    return g.db


def get_db():
    """The raw connection, for code that manages its own statements. Marks the request, so that transaction() will refuse (and not roll back) a
    transaction that may hold work it did not do. Application code uses query_all(), query_one() and transaction() instead."""
    g.db_raw = True
    return _connection()


def close_db(_error=None):
    """Return the connection to the pool at the end of every request."""
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def query_all(sql, params=None):
    """Run a read statement and return every row. Refuses what does not look like a single read (is_read_only); writes belong in transaction()."""
    if not is_read_only(sql):
        raise TransactionError("query_all()/query_one() are read-only (a single read statement); run writes inside transaction()")
    cursor = _connection().cursor(dictionary=True)
    try:
        cursor.execute(sql, params or ())
        return cursor.fetchall()
    finally:
        cursor.close()


def query_one(sql, params=None):
    rows = query_all(sql, params)
    return rows[0] if rows else None


@contextmanager
def transaction():
    """Run statements as one unit of work: commit on success, roll back on any error. This is the only way the application writes.

    with transaction() as cursor:
        cursor.execute("INSERT ...", params)
        cursor.execute("INSERT ...", params)

    Ownership: the block owns everything between its start and its end.
    * Not re-entrant: a transaction() inside a transaction() raises TransactionError BEFORE touching the connection, so the outer block's work is untouched
      (the outer block may catch the error and still commit).
    * Earlier reads (query_all/query_one, e.g. the signed-in user) left an implicit read snapshot, and the connector refuses to start a transaction while
      one is open ("Transaction already in progress"). That snapshot cannot contain a write (the read helpers refuse writes), so it is ended first.
    * If get_db() was used in this request and a transaction is open, it may hold someone's uncommitted write. It is NOT rolled back: TransactionError.
    """
    connection = _connection()
    if g.get("db_transaction"):
        raise TransactionError("transaction() cannot be nested; do all the writes in the outermost block")
    if connection.in_transaction:
        if g.get("db_raw"):
            raise TransactionError("a transaction is open after get_db() was used in this request; commit or roll it back before transaction()")
        connection.rollback()                 # only the read snapshot of query_all()/query_one() can be open here: nothing to lose
    cursor = connection.cursor(dictionary=True)
    g.db_transaction = True
    try:
        connection.start_transaction()
        yield cursor
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        g.db_transaction = False
        g.db_raw = False                      # the connection is clean again (committed or rolled back)
        cursor.close()


def init_app(app):
    app.teardown_appcontext(close_db)


DatabaseError = mysql.connector.Error
