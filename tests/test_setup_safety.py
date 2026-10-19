"""Safety behaviour of the setup scripts: planning is explainable and existing data is protected."""
import pytest

from app.config import TestingConfig
from scripts import setup_db
from scripts.init_db import DatabaseNotEmpty, init_database
from scripts.schema_info import schema_tables

DBS = ("gta6_vi", "gta6_vi_test")


def empty_state():
    return {"databases": {}, "users": {}, "other_databases": []}


def test_schema_table_list_comes_from_schema_sql():
    tables = schema_tables()
    assert len(tables) == 25 and "characters" in tables and "users" in tables


def test_plan_for_a_fresh_server_creates_everything():
    plan = setup_db.build_plan(empty_state(), DBS, "app", "mig", reset=False)
    text = "\n".join(plan.lines)
    assert "CREATE   database `gta6_vi`" in text and "CREATE   account 'mig'" in text
    assert plan.loads == list(DBS) and plan.drops == {}
    assert "DROP     " not in text  # nothing is dropped on a fresh server
    assert "SELECT, INSERT, UPDATE, DELETE ON `gta6_vi`.* TO 'app'@'localhost'" in text
    assert "SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, ALTER, INDEX, REFERENCES ON `gta6_vi`.* TO 'mig'@'localhost'" in text


def test_plan_never_drops_existing_tables_without_reset():
    state = empty_state()
    state["databases"]["gta6_vi"] = {"tables": {"characters": 11, "regions": 6}, "other_tables": ["my_notes"]}
    plan = setup_db.build_plan(state, DBS, "app", "mig", reset=False)
    text = "\n".join(plan.lines)
    assert plan.drops == {} and "gta6_vi" not in plan.loads
    assert "SKIP" in text and "17 rows" in text and "untouched" in text
    assert "['my_notes']" in text and "never touched" in text


def test_plan_flags_a_half_built_schema():
    state = empty_state()
    state["databases"]["gta6_vi"] = {"tables": {"regions": 0, "users": 0}, "other_tables": []}
    text = "\n".join(setup_db.build_plan(state, DBS, "app", "mig", reset=False).lines)
    assert "WARNING" in text and "2 of 25" in text and "--reset" in text


def test_plan_lists_exactly_what_reset_would_drop():
    state = empty_state()
    state["databases"]["gta6_vi"] = {"tables": {"characters": 11}, "other_tables": []}
    plan = setup_db.build_plan(state, DBS, "app", "mig", reset=True)
    assert plan.drops == {"gta6_vi": {"characters": 11}}
    assert any(line.startswith("DROP     1 project tables in `gta6_vi` holding 11 rows") for line in plan.lines)


def test_plan_does_not_change_existing_account_passwords():
    state = empty_state()
    state["users"]["app"] = ["GRANT USAGE ON *.* TO `app`@`localhost`"]
    text = "\n".join(setup_db.build_plan(state, DBS, "app", "mig", reset=False).lines)
    assert "KEEP     account 'app'" in text and "password NOT changed" in text
    assert "CREATE   account 'app'" not in text


def test_no_statement_in_setup_script_touches_root_or_alters_users():
    source = open(setup_db.__file__, encoding="utf-8").read().upper()
    for forbidden in ("ALTER USER", "DROP USER", "SET PASSWORD", "DROP DATABASE", "FLUSH PRIVILEGES", "GRANT OPTION"):
        assert forbidden not in source.split('"""', 2)[2], forbidden


@pytest.mark.parametrize("overrides,expected", [
    ({"DB_USER": "root"}, "must not be 'root'"),
    ({"MIGRATE_DB_USER": "valkyrie_app"}, "two different accounts"),
    ({"DB_USER": "bad name;"}, "letters, digits"),
])
def test_config_validation_rejects_unsafe_values(monkeypatch, overrides, expected):
    for key, value in overrides.items():
        monkeypatch.setattr(setup_db.DevelopmentConfig, key, value)
    problems = "\n".join(setup_db.validate_config(setup_db.DevelopmentConfig, setup_db.TestingConfig, need_passwords=False))
    assert expected in problems


def test_placeholder_passwords_are_rejected(monkeypatch):
    monkeypatch.setattr(setup_db.DevelopmentConfig, "DB_PASSWORD", "change_me")
    problems = setup_db.validate_config(setup_db.DevelopmentConfig, setup_db.TestingConfig, need_passwords=True)
    assert any("DB_PASSWORD" in p for p in problems)


def test_init_database_refuses_to_overwrite_existing_tables(app):
    with pytest.raises(DatabaseNotEmpty) as info:
        init_database(TestingConfig, seed=True)  # reset defaults to False
    assert "characters" in info.value.tables
