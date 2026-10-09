"""Unit tests for the SQL file splitter (no database needed)."""
from scripts.sqlfile import split_statements


def test_splits_simple_statements():
    assert split_statements("SELECT 1; SELECT 2;") == ["SELECT 1", "SELECT 2"]


def test_semicolon_inside_string_is_kept():
    sql = "INSERT INTO t VALUES ('a;b'); SELECT 1;"
    assert split_statements(sql) == ["INSERT INTO t VALUES ('a;b')", "SELECT 1"]


def test_doubled_quote_escape():
    sql = "INSERT INTO t VALUES ('Dre''Quan; Priest'); SELECT 2;"
    assert split_statements(sql) == ["INSERT INTO t VALUES ('Dre''Quan; Priest')", "SELECT 2"]


def test_comments_are_removed_even_with_apostrophes_and_semicolons():
    sql = "-- Rockstar's data; not real\nSELECT 1; /* a ; b */ SELECT 2; # note's\n"
    assert split_statements(sql) == ["SELECT 1", "SELECT 2"]


def test_last_statement_without_semicolon():
    assert split_statements("SELECT 1; SELECT 2") == ["SELECT 1", "SELECT 2"]


def test_double_dash_without_space_is_not_a_comment():
    assert split_statements("SELECT 5--3;") == ["SELECT 5--3"]
