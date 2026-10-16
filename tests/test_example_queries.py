"""Every example query in docs/queries.sql must run on the real schema and return rows."""
from pathlib import Path

import pytest

from scripts.sqlfile import split_statements

QUERIES = split_statements((Path(__file__).resolve().parent.parent / "docs" / "queries.sql").read_text(encoding="utf-8"))


def test_file_contains_eighteen_queries():
    assert len(QUERIES) == 18


@pytest.mark.parametrize("sql", QUERIES, ids=[f"query_{i}" for i in range(1, len(QUERIES) + 1)])
def test_query_runs_and_returns_rows(cur, sql):
    cur.execute(sql)
    assert cur.fetchall(), sql[:60]


def test_query_results_are_sensible(cur):
    cur.execute(QUERIES[2])  # vehicles per category
    assert sum(r["vehicles"] for r in cur.fetchall()) == 15
    cur.execute(QUERIES[5])  # port-gellhorn missions
    assert {r["title"] for r in cur.fetchall()} == {"Harbour Lights"}
    cur.execute(QUERIES[6])  # characters in no mission
    assert len(cur.fetchall()) == 8  # the eight official characters


def test_official_vehicle_image_query(cur):
    cur.execute(QUERIES[13])
    rows = cur.fetchall()
    assert sorted(r["images"] for r in rows) == [1, 2, 2, 4, 4, 4, 4] and {r["name"]: r["images"] for r in rows}["Vapid Ganado Retro Build"] == 1


def test_gate3a_cast_queries(cur):
    cur.execute(QUERIES[14])  # where Rockstar places each character
    assert [(r["full_name"], r["region"]) for r in cur.fetchall()] == [
        ("Brian Heder", "Leonida Keys"), ("Jason Duval", "Leonida Keys"), ("Boobie Ike", "Vice City")]
    cur.execute(QUERIES[15])  # the network edges
    assert len(cur.fetchall()) == 5
    cur.execute(QUERIES[16])  # connections per person, Raul has none
    rows = {r["full_name"]: r["connections"] for r in cur.fetchall()}
    assert rows["Raul Bautista"] == 0 and rows["Jason Duval"] == 3 and rows["Real Dimez"] == 1
    cur.execute(QUERIES[17])  # the original characters are still in the stories
    assert {r["full_name"] for r in cur.fetchall()} == {"Delia Marsh", "Nico Brandt", "Tomas Reyes-Hall"}
