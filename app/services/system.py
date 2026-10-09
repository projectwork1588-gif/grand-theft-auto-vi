"""Health and homepage statistics."""
from ..repositories import system as repo


def health():
    info = repo.ping()
    return {"status": "ok", "database": "connected", "mysql_version": info["version"]}


def homepage_stats():
    return repo.table_counts()
