"""Every example query in docs/queries.sql must run on the real schema and return rows."""
from pathlib import Path

import pytest

from scripts.sqlfile import split_statements

QUERIES = split_statements((Path(__file__).resolve().parent.parent / "docs" / "queries.sql").read_text(encoding="utf-8"))


def test_file_contains_fourteen_queries():
    assert len(QUERIES) == 14


@pytest.mark.parametrize("sql", QUERIES, ids=[f"query_{i}" for i in range(1, len(QUERIES) + 1)])
def test_query_runs_and_returns_rows(cur, sql):
    cur.execute(sql)
    assert cur.fetchall(), sql[:60]


def test_query_results_are_sensible(cur):
    cur.execute(QUERIES[2])  # vehicles per category
    assert sum(r["vehicles"] for r in cur.fetchall()) == 13
    cur.execute(QUERIES[5])  # port-gellhorn missions
    assert {r["title"] for r in cur.fetchall()} == {"Harbour Lights"}
    cur.execute(QUERIES[6])  # characters in no mission
    assert len(cur.fetchall()) == 8  # the eight official characters


def test_official_vehicle_image_query(cur):
    cur.execute(QUERIES[13])
    rows = cur.fetchall()
    assert [r["images"] for r in rows] == [4, 4, 4, 4, 1] and rows[-1]["name"] == "Vapid Ganado Retro Build"
