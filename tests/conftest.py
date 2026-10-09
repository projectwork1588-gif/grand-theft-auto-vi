"""Shared fixtures. Tests run against a REAL MySQL database named *_test (never the dev data)."""
import mysql.connector
import pytest

from app import create_app
from app.config import TestingConfig
from scripts.init_db import init_database


@pytest.fixture(scope="session")
def app():
    assert TestingConfig.DB_NAME.endswith("_test"), "tests must never run against the real database"
    init_database(TestingConfig, seed=True, reset=True)  # migration account; fresh, deterministic schema + seed
    return create_app("testing")


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def app_context(app):
    with app.app_context():
        yield


@pytest.fixture()
def conn():
    """Raw connection for integrity tests. Everything is rolled back, so the seed stays intact."""
    connection = mysql.connector.connect(**TestingConfig.db_kwargs())
    connection.autocommit = False
    yield connection
    connection.rollback()
    connection.close()


@pytest.fixture()
def cur(conn):
    cursor = conn.cursor(dictionary=True)
    yield cursor
    cursor.close()
