"""Every example query in docs/queries.sql must run on the real schema and return rows."""
from pathlib import Path

import pytest

from scripts.sqlfile import split_statements

QUERIES = split_statements((Path(__file__).resolve().parent.parent / "docs" / "queries.sql").read_text(encoding="utf-8"))


def test_file_contains_twenty_one_queries():
    assert len(QUERIES) == 21


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


# ---- queries 19 to 21 use CASE, window functions and CTEs. Each result is checked against separate, plain SQL, not against remembered seed numbers.
def test_query_19_case_columns_add_up_to_the_totals(cur):
    cur.execute(QUERIES[18])
    rows = cur.fetchall()
    cur.execute("SELECT COUNT(*) AS n FROM vehicles")
    assert sum(r["total"] for r in rows) == cur.fetchone()["n"]
    for row in rows:
        assert row["official"] + row["concept"] == row["total"], row
        cur.execute("SELECT COUNT(*) AS n FROM vehicles v JOIN vehicle_categories vc ON vc.category_id = v.category_id WHERE vc.name = %s AND v.content_status = 'official'", (row["category"],))
        assert cur.fetchone()["n"] == row["official"], row


def test_query_20_window_functions_rank_within_the_type_and_keep_a_running_total(cur):
    cur.execute(QUERIES[19])
    rows = cur.fetchall()
    for row in rows:
        better = sum(1 for other in rows if other["mission_type"] == row["mission_type"] and other["cast_size"] > row["cast_size"])
        assert row["rank_in_type"] == 1 + better, row                       # RANK(): ties share a rank, and the next rank skips
    ordered = sorted(rows, key=lambda r: r["title"])
    running = 0
    for row in ordered:
        running += row["cast_size"]
        assert row["running_cast_links"] == running, row                    # the running total follows the title order of the window
    cur.execute("SELECT COUNT(*) AS n FROM mission_characters")
    assert running == cur.fetchone()["n"]


def test_query_21_chained_ctes_count_story_place_links_per_region(cur):
    cur.execute(QUERIES[20])
    rows = cur.fetchall()
    cur.execute("SELECT COUNT(*) AS n FROM mission_locations")
    assert sum(int(r["place_links"]) for r in rows) == cur.fetchone()["n"]
    assert abs(sum(float(r["share_percent"]) for r in rows) - 100) <= 0.1 * len(rows)       # each share is rounded to one decimal
    for row in rows:
        cur.execute("SELECT COUNT(DISTINCT ml.mission_id) AS n FROM mission_locations ml JOIN locations l ON l.location_id = ml.location_id JOIN regions r ON r.region_id = l.region_id WHERE r.name = %s", (row["region"],))
        assert cur.fetchone()["n"] == row["stories"], row
