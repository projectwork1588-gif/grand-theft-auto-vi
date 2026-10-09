"""Database access helpers: a lazily created connection pool and one connection per request.

Repositories call get_db() and run parameterized SQL. They never build SQL from
user input. Code that changes several tables should use transaction().
"""
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


def get_db():
    """Return this request's connection (created on first use)."""
    if "db" not in g:
        g.db = _get_pool(current_app).get_connection()
    return g.db


def close_db(_error=None):
    """Return the connection to the pool at the end of every request."""
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def query_all(sql, params=None):
    cursor = get_db().cursor(dictionary=True)
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
    """Run several statements as one unit: commit on success, roll back on any error.

    with transaction() as cursor:
        cursor.execute("INSERT ...", params)
        cursor.execute("INSERT ...", params)
    """
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    try:
        connection.start_transaction()
        yield cursor
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()


def init_app(app):
    app.teardown_appcontext(close_db)


DatabaseError = mysql.connector.Error
