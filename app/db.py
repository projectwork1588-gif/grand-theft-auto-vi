"""Database access helpers: a lazily created connection pool and one connection per request.

Who owns what (the rules every caller follows):

* READS go through query_all() / query_one(). They refuse statements that start with a write verb, so a read can never leave an uncommitted write behind.
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


# A statement the read helpers refuse: it starts with a verb that writes, changes the schema, or controls a transaction.
_NOT_A_READ = re.compile(
    r"^\s*(?:/\*.*?\*/\s*)*(insert|update|delete|replace|create|alter|drop|truncate|rename|grant|revoke|lock|unlock|call|load|set|start|begin|commit|rollback|savepoint|release|do|handler)\b",
    re.IGNORECASE | re.DOTALL)


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
    """Run a read-only statement and return every row. Refuses anything that starts with a write verb (use transaction())."""
    if _NOT_A_READ.match(sql):
        raise TransactionError("query_all()/query_one() are read-only; run writes inside transaction()")
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
