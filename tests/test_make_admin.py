"""scripts/make_admin.py works on the TEST database only and fails closed. The refusals that happen before the connection step are proved by forbidding the
connect call altogether: if the tool tried to connect, the test would fail. Real promotions use the *_test database only (the helper proves it)."""
import mysql.connector
import pytest

from app.config import TestingConfig
from scripts import make_admin
from tests import account_helpers as h
from tests import admin_helpers as a

@pytest.fixture()
def no_connection(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("the tool opened a database connection")
    monkeypatch.setattr(mysql.connector, "connect", forbidden)


# ------------------------------------------------------------------ refusals that must happen BEFORE any connection
@pytest.mark.parametrize("argv", [
    ["someone"],                                    # no --test
    ["someone", "--yes"],                           # --yes does not replace --test
    ["someone", "--revoke"],
    ["someone", "--plan"],
    ["someone", "--yes", "--revoke", "--plan"],
    ["--test", "Not Valid"],                        # not a username
    ["--test", ""],
    ["--test", "a;drop table users"],
])
def test_refusals_never_open_a_connection(no_connection, argv, capsys):
    assert make_admin.main(argv) == make_admin.REFUSED
    assert "REFUSED" in capsys.readouterr().err


@pytest.mark.parametrize("name", ["gta6_vi", "gta6_vi_prod", "", "production"])
def test_a_testing_configuration_without_a_test_database_name_is_refused_with_yes(no_connection, monkeypatch, name, capsys):
    monkeypatch.setattr(TestingConfig, "DB_NAME", name)
    assert make_admin.main(["--test", "--yes", "someone"]) == make_admin.REFUSED
    assert "ending in _test" in capsys.readouterr().err


def test_yes_never_changes_the_target(monkeypatch):
    """--yes only skips the typed confirmation: the target is always TestingConfig, whatever else is passed."""
    seen = {}

    class Stub:
        def cursor(self):
            return self

        def execute(self, sql, params=()):
            seen.setdefault("sql", []).append(sql)

        def fetchone(self):
            return ("gta6_vi_test",) if "DATABASE" in seen["sql"][-1] else None

        def close(self):
            pass

        def rollback(self):
            pass

    def fake_connect(**kwargs):
        seen["database"], seen["user"] = kwargs["database"], kwargs["user"]
        return Stub()
    monkeypatch.setattr(mysql.connector, "connect", fake_connect)
    make_admin.main(["--test", "--yes", "nobody"])
    assert seen["database"] == TestingConfig.DB_NAME == "gta6_vi_test" and seen["user"] == TestingConfig.MIGRATE_DB_USER


def test_a_server_that_reports_another_database_is_refused_before_any_account_is_read(monkeypatch, capsys):
    executed = []

    class Stub:
        def cursor(self):
            return self

        def execute(self, sql, params=()):
            executed.append(sql)

        def fetchone(self):
            return ("gta6_vi",)

        def close(self):
            pass

    monkeypatch.setattr(mysql.connector, "connect", lambda **kwargs: Stub())
    assert make_admin.main(["--test", "--yes", "someone"]) == make_admin.REFUSED
    assert executed == ["SELECT DATABASE()"]                      # nothing else ran: no read of users, no UPDATE
    assert "not a *_test database" in capsys.readouterr().err


# ------------------------------------------------------------------ the working path, on the test database
def role_of(name):
    return h.user_row(name)["role"]


@pytest.mark.usefixtures("clean_accounts")
def test_plan_shows_the_target_and_the_role_and_changes_nothing(app, capsys):
    _client, name = h.signed_in_client(app)
    assert make_admin.main(["--test", "--plan", name]) == 0
    out = capsys.readouterr().out
    assert "gta6_vi_test" in out and "currently has the role 'user'" in out and "nothing was changed" in out
    assert role_of(name) == "user"


@pytest.mark.usefixtures("clean_accounts")
def test_promote_and_revoke(app, capsys):
    _client, name = h.signed_in_client(app)
    assert make_admin.main(["--test", "--yes", name]) == 0 and role_of(name) == "admin"
    assert make_admin.main(["--test", "--yes", name]) == 0                       # already admin: a no-op
    assert "already has that role" in capsys.readouterr().out
    assert make_admin.main(["--test", "--yes", "--revoke", name]) == 0 and role_of(name) == "user"


@pytest.mark.usefixtures("clean_accounts")
def test_the_username_is_matched_exactly_and_an_unknown_one_is_refused(app, capsys):
    assert make_admin.main(["--test", "--yes", "tt_nobody_here"]) == make_admin.REFUSED
    assert "no account called" in capsys.readouterr().err


@pytest.mark.usefixtures("clean_accounts")
def test_the_typed_confirmation_must_match(app, monkeypatch):
    _client, name = h.signed_in_client(app)
    monkeypatch.setattr("builtins.input", lambda prompt="": "someone else")
    assert make_admin.main(["--test", name]) == make_admin.REFUSED and role_of(name) == "user"
    monkeypatch.setattr("builtins.input", lambda prompt="": name)
    assert make_admin.main(["--test", name]) == 0 and role_of(name) == "admin"


@pytest.mark.usefixtures("clean_accounts")
def test_it_changes_one_account_only_and_prints_no_hash(app, capsys):
    _c1, first = h.signed_in_client(app)
    _c2, second = h.signed_in_client(app)
    assert make_admin.main(["--test", "--yes", first]) == 0
    assert role_of(first) == "admin" and role_of(second) == "user"
    captured = capsys.readouterr()
    assert "scrypt" not in captured.out + captured.err and h.user_row(first)["password_hash"] not in captured.out + captured.err


@pytest.mark.usefixtures("clean_accounts")
def test_it_connects_with_the_migration_account_to_the_test_database(app, monkeypatch):
    _client, name = h.signed_in_client(app)
    real, seen = mysql.connector.connect, {}

    def spy(**kwargs):
        seen.update(user=kwargs["user"], database=kwargs["database"])
        return real(**kwargs)
    monkeypatch.setattr(mysql.connector, "connect", spy)
    assert make_admin.main(["--test", "--plan", name]) == 0
    assert seen == {"user": TestingConfig.MIGRATE_DB_USER, "database": "gta6_vi_test"}
