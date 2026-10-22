"""Health and homepage statistics."""
from ..repositories import system as repo


def health():
    repo.ping()                    # raises if the database cannot be reached
    return {"status": "ok", "database": "connected"}      # nothing about the server: no version, host, user or error text


def homepage_stats():
    return repo.table_counts()
