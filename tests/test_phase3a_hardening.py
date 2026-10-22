"""Phase 3A: the read-only guard, strict TV_TRUSTED_PROXIES, deterministic test settings, the public health check, the startup log line, and the
view-transition guard on vehicle pages. Nothing here writes to a database except where a test says so (and then only to the *_test database)."""
import ast
import io
import json
import logging
import re
import shutil
import subprocess
import sys
from pathlib import Path

import mysql.connector
import pytest

from app import config, create_app
from app.db import is_read_only

ROOT = Path(__file__).resolve().parent.parent


# ------------------------------------------------------------------ 1. the read-only guard
@pytest.mark.parametrize("sql", [
    "SELECT 1",
    "  select * from characters where slug = %s",
    "-- a comment first\nSELECT 1",
    "/* a comment first */ SELECT 1",
    "# a comment first\nSELECT 1",
    "SELECT 1;",
    "WITH RECURSIVE r AS (SELECT 1 AS n) SELECT n FROM r",
    "(SELECT 1 AS a) UNION (SELECT 2)",
    "SHOW TABLES",
    "EXPLAIN SELECT 1",
    "DESCRIBE users",
    "SELECT * FROM users FOR UPDATE",                                          # a locking read does not write
    "SELECT REPLACE(name, 'a', 'b'), INSERT('abc', 1, 1, 'x') FROM characters",  # the string functions of the same names
    "SELECT created_at, updated_at, release_date, delete_flag FROM t",         # words that merely contain a verb
    "SELECT `delete`, `update`, `drop` FROM t",                                # quoted identifiers
    "SELECT * FROM t WHERE note = 'delete from x; drop table y' AND other = \"insert into z\"",   # text inside quotes
    "SELECT * FROM t WHERE note = 'it''s a delete'",
])
def test_the_guard_accepts_ordinary_reads(sql):
    assert is_read_only(sql), sql


@pytest.mark.parametrize("sql", [
    "INSERT INTO t VALUES (1)",
    "update t set a = 1",
    "DELETE FROM t",
    "REPLACE INTO t VALUES (1)",
    "-- a comment first\nINSERT INTO t VALUES (1)",                            # the confirmed comment-prefix bypasses
    "# a comment first\nDELETE FROM t",
    "/* a */ /* b */ UPDATE t SET a = 1",
    "-- one\n-- two\n/* three */ TRUNCATE t",
    "--\nINSERT INTO t VALUES (1)",
    "WITH x AS (SELECT 1) DELETE FROM t",                                      # the confirmed WITH ... DELETE bypass, and its relatives
    "WITH x AS (SELECT 1) UPDATE t SET a = 1",
    "WITH x AS (SELECT 1) INSERT INTO t SELECT * FROM x",
    "WITH x AS (SELECT 1) REPLACE INTO t SELECT * FROM x",
    "-- c\nWITH x AS (SELECT 1) DELETE FROM t",
    "SELECT 1; DROP TABLE t",                                                  # a second statement
    "SELECT 1; SELECT 2",
    "SELECT * FROM t INTO OUTFILE '/tmp/x'",
    "SELECT * FROM t INTO DUMPFILE '/tmp/x'",
    "/*!50000 DELETE FROM t */ SELECT 1",                                      # executable comments run as SQL in MySQL
    "SELECT /*! 1 */ 1",
    "SET autocommit = 1", "COMMIT", "ROLLBACK", "START TRANSACTION", "CALL p()", "DO SLEEP(1)", "LOCK TABLES t READ", "LOAD DATA INFILE 'x' INTO TABLE t",
    "CREATE TABLE t (a INT)", "ALTER TABLE t ADD b INT", "DROP TABLE t", "GRANT ALL ON *.* TO x", "RENAME TABLE a TO b",
    "", "   ", "-- only a comment", "not sql at all",
])
def test_the_guard_refuses_writes_however_they_are_dressed(sql):
    assert not is_read_only(sql), sql


def test_the_guard_does_not_pretend_to_be_more_than_it_is():
    """It reads the text of a statement. A function with side effects is still a SELECT to it, which is why db.py calls it a safety net and not a guarantee."""
    assert is_read_only("SELECT GET_LOCK('x', 0)")
    source = (ROOT / "app" / "db.py").read_text(encoding="utf-8")
    assert "not a security boundary" in source and "not a guarantee" in source


def _sql_strings(tree):
    """Every statement the application passes to query_all()/query_one() whose text can be worked out from the source."""
    def text(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.JoinedStr):
            return "".join(part.value if isinstance(part, ast.Constant) else "x" for part in node.values)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            left, right = text(node.left), text(node.right)
            return None if left is None or right is None else left + right
        return None
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "id", getattr(node.func, "attr", "")) in ("query_all", "query_one") and node.args:
            value = text(node.args[0])
            if value is not None:
                yield value


def test_every_read_the_application_makes_passes_the_guard():
    found = []
    for path in (ROOT / "app").rglob("*.py"):
        if path.name == "db.py":
            continue
        found += [(path.name, sql) for sql in _sql_strings(ast.parse(path.read_text(encoding="utf-8")))]
    assert len(found) > 35, f"the scan found only {len(found)} statements: it is not looking in the right places"
    refused = [(name, sql[:70]) for name, sql in found if not is_read_only(sql)]
    assert refused == [], refused


def test_the_read_helpers_use_the_guard_before_touching_the_connection(app):
    from app.db import TransactionError, query_all
    with app.app_context():
        for sql in ("-- c\nDELETE FROM users", "WITH x AS (SELECT 1) DELETE FROM users", "SELECT 1; DELETE FROM users"):
            with pytest.raises(TransactionError, match="read-only"):
                query_all(sql)


# ------------------------------------------------------------------ 5. TV_TRUSTED_PROXIES
@pytest.mark.parametrize("raw, expected", [(None, 0), ("0", 0), ("1", 1), ("5", 5), (" 2 ", 2), ("007", 7), ("12", 12)])
def test_a_valid_proxy_count_is_read_as_a_number(raw, expected):
    assert config.parse_proxy_count(raw) == expected


@pytest.mark.parametrize("raw", ["", "  ", "abc", "1.5", "-1", "+2", "1 2", "two", "0x1", "١", "1e1", "None", "1,2", "9999"])
def test_a_malformed_proxy_count_is_not_turned_into_a_number(raw):
    assert not isinstance(config.parse_proxy_count(raw), int)


@pytest.mark.parametrize("raw", ["", "abc", "1.5", "-1", "+2", "None", "1,2"])
def test_a_malformed_proxy_count_stops_the_site_from_starting(monkeypatch, raw):
    monkeypatch.setattr(config.TestingConfig, "TRUSTED_PROXY_COUNT", config.parse_proxy_count(raw))
    with pytest.raises(RuntimeError, match="TV_TRUSTED_PROXIES must be a whole number"):
        config.get_config("testing")
    with pytest.raises(RuntimeError):
        create_app("testing")


def test_an_out_of_range_count_is_still_refused_and_a_valid_one_still_works(monkeypatch):
    for bad in (config.MAX_TRUSTED_PROXIES + 1, 999):
        monkeypatch.setattr(config.TestingConfig, "TRUSTED_PROXY_COUNT", bad)
        with pytest.raises(RuntimeError, match="between 0 and"):
            config.get_config("testing")
    for good in range(config.MAX_TRUSTED_PROXIES + 1):
        monkeypatch.setattr(config.TestingConfig, "TRUSTED_PROXY_COUNT", good)
        assert config.get_config("testing") is config.TestingConfig


def _python(code, **env):
    import os
    run_env = {**os.environ, **env, "PYTHONPATH": str(ROOT)}
    return subprocess.run([sys.executable, "-c", code], cwd=str(ROOT), env=run_env, capture_output=True, text=True, timeout=120)


@pytest.mark.parametrize("value, ok", [("abc", False), ("1.5", False), ("-1", False), ("2", True), ("0", True)])      # (a blank value is covered above: Windows drops blank variables)
def test_the_environment_variable_itself_is_checked(value, ok):
    result = _python("from app import config; print(config.get_config('development').TRUSTED_PROXY_COUNT)", TV_TRUSTED_PROXIES=value)
    assert (result.returncode == 0) == ok, result.stderr[-300:]
    if ok:
        assert result.stdout.strip() == value
    else:
        assert "TV_TRUSTED_PROXIES must be a whole number" in result.stderr


def test_not_setting_the_variable_means_no_proxies():
    import os
    env = {k: v for k, v in os.environ.items() if k != "TV_TRUSTED_PROXIES"}
    result = subprocess.run([sys.executable, "-c", "from app import config; print(config.get_config('development').TRUSTED_PROXY_COUNT)"], cwd=str(ROOT),
                            env={**env, "PYTHONPATH": str(ROOT)}, capture_output=True, text=True, timeout=120)
    assert result.returncode == 0 and result.stdout.strip() == "0"


# ------------------------------------------------------------------ 6. the test setting does not depend on the developer's .env
def test_the_testing_configuration_pins_autoplay_off():
    assert config.TestingConfig.AUTOPLAY_ALWAYS is False
    assert config.ProductionConfig.AUTOPLAY_ALWAYS is False


@pytest.mark.parametrize("value", ["1", "true", "yes", "on", "0", ""])
def test_a_developers_autoplay_switch_never_reaches_tests_or_production(value):
    code = ("from app import config; t, d, p = config.TestingConfig, config.DevelopmentConfig, config.ProductionConfig;"
            "print(t.AUTOPLAY_ALWAYS, d.AUTOPLAY_ALWAYS, p.AUTOPLAY_ALWAYS)")
    result = _python(code, TV_AUTOPLAY_ALWAYS=value)
    assert result.returncode == 0, result.stderr[-300:]
    testing, development, production = result.stdout.split()
    assert testing == "False" and production == "False"
    assert development == str(value in ("1", "true", "yes", "on"))              # the development convenience itself still works


def test_pages_served_by_a_test_configured_app_never_carry_the_autoplay_override():
    code = ("from app import create_app; page = create_app('testing').test_client().get('/vehicles').get_data(as_text=True);"
            "print('data-autoplay=\"always\"' in page)")
    result = _python(code, TV_AUTOPLAY_ALWAYS="1")
    assert result.returncode == 0, result.stderr[-300:]
    assert result.stdout.strip() == "False"


# ------------------------------------------------------------------ 7. the public health check
def test_the_healthy_response_contains_nothing_about_the_server(client):
    response = client.get("/health")
    body = response.get_json()
    assert response.status_code == 200 and body == {"status": "ok", "database": "connected"}
    text = response.get_data(as_text=True).lower()
    for word in ("version", "mysql", "8.", "host", "user", "127.0.0.1", "password"):
        assert word not in text, word


def test_the_unhealthy_response_exposes_no_internals_but_the_log_keeps_the_reason(app, monkeypatch, caplog):
    from app.services import system

    def refuse():
        raise mysql.connector.Error("2003: Can't connect to MySQL server on 'secret-host:3306' as 'valkyrie_app' (password hunter2)")
    monkeypatch.setattr(system.repo, "ping", refuse)
    with caplog.at_level(logging.WARNING):
        response = app.test_client().get("/health")
    assert response.status_code == 503 and response.get_json() == {"status": "error", "database": "unreachable"}
    for secret in ("secret-host", "hunter2", "valkyrie_app", "3306", "MySQL", "2003"):
        assert secret not in response.get_data(as_text=True)
    assert "Health check: the database could not be reached" in caplog.text and "secret-host" in caplog.text      # server side only


def test_the_health_query_no_longer_asks_for_the_version():
    source = (ROOT / "app" / "repositories" / "system.py").read_text(encoding="utf-8")
    assert "VERSION()" not in source and "mysql_version" not in (ROOT / "app" / "services" / "system.py").read_text(encoding="utf-8")


# ------------------------------------------------------------------ 3. the startup log line
class Capture:
    def __enter__(self):
        self.logger = logging.getLogger("app")
        self.old_level, self.stream = self.logger.level, io.StringIO()
        self.handler = logging.StreamHandler(self.stream)
        self.logger.addHandler(self.handler)
        return self

    def __exit__(self, *exc):
        self.logger.removeHandler(self.handler)
        self.logger.setLevel(self.old_level)

    @property
    def text(self):
        return self.stream.getvalue()


def test_the_startup_line_is_emitted_by_default_and_says_which_configuration():
    with Capture() as log:
        log.logger.setLevel(logging.NOTSET)                                      # as in a fresh process: nobody has configured the logger
        create_app("testing")
    assert "Starting with TestingConfig" in log.text and "secure session cookie: no" in log.text and "public origins configured: 0" in log.text


def test_the_startup_line_contains_no_secret_or_connection_detail(monkeypatch):
    monkeypatch.setattr(config.TestingConfig, "PUBLIC_ORIGINS", ("https://valkyrie.example.org",))
    with Capture() as log:
        log.logger.setLevel(logging.NOTSET)
        create_app("testing")
    line = log.text
    assert "public origins configured: 1" in line and "valkyrie.example.org" not in line
    for secret in (config.TestingConfig.SECRET_KEY, config.TestingConfig.DB_PASSWORD, config.TestingConfig.MIGRATE_DB_PASSWORD, config.TestingConfig.DB_USER,
                   config.TestingConfig.DB_NAME, config.TestingConfig.DB_HOST):
        if secret:
            assert str(secret) not in line, "the startup line must not repeat configuration values"


def test_an_operators_own_log_level_is_respected():
    with Capture() as log:
        log.logger.setLevel(logging.ERROR)
        create_app("testing")
        level_after = log.logger.level                       # read before the context manager puts the old level back
    assert log.text == "" and level_after == logging.ERROR


def test_production_reports_a_secure_cookie_in_the_startup_line(monkeypatch):
    """The line an operator looks for after a deployment. get_config('production') is satisfied with test values; no database is contacted."""
    monkeypatch.setattr(config.ProductionConfig, "SECRET_KEY", "5f3a9c1e7b2d4a60" * 4)
    monkeypatch.setattr(config.ProductionConfig, "PUBLIC_ORIGINS", ("https://valkyrie.example.org",))
    monkeypatch.setattr(config.ProductionConfig, "DB_NAME", "gta6_vi")
    with Capture() as log:
        log.logger.setLevel(logging.NOTSET)
        production = create_app("production")                                    # building the app does not open a database connection
    assert "Starting with ProductionConfig" in log.text and "secure session cookie: yes" in log.text and "public origins configured: 1" in log.text
    assert "5f3a9c1e" not in log.text and production.config["SESSION_COOKIE_SECURE"] is True


# ------------------------------------------------------------------ 2. view transitions on a vehicle page
JS = (ROOT / "app" / "static" / "js" / "vehicle_detail.js").read_text(encoding="utf-8").replace("\r\n", "\n")
HANDLER = re.search(r'window\.addEventListener\("pageswap", function \(e\) \{.*?\n  \}\);\n\}\)\(\);', JS, re.S)


def test_the_page_leave_handler_skips_a_transition_to_the_same_address():
    assert HANDLER, "the pageswap handler was not found"
    body = HANDLER.group(0)
    guard = body.index("pathname === location.pathname")
    assert "skipTransition()" in body[guard:guard + 120] and "return;" in body[guard:guard + 140]
    assert guard < body.index('.vd-next__stage')                                    # the guard comes before any picture is named
    assert body.count('style.viewTransitionName = "vehicle-art"') == 1               # the transition to another machine is still prepared


@pytest.mark.skipif(shutil.which("node") is None, reason="node is needed to run the handler")
def test_the_handler_behaves_as_intended_when_run():
    """The handler's own source, run in Node with a small stand-in for the page."""
    script = """
    const handlers = []; let skipped = 0; const names = {};
    const art = { style: {} }, hero = { style: {} };
    const next = { href: 'http://x/vehicles/other-machine', querySelector: () => art };
    global.window = { addEventListener: (type, fn) => handlers.push([type, fn]) };
    global.location = { pathname: '/vehicles/this-machine', href: 'http://x/vehicles/this-machine' };
    global.document = { querySelector: (sel) => sel === '.vd-next__stage' ? next : sel === '.vd-hero__art' ? hero : null };
    const fn = %s;
    fn(window);
    const handler = handlers[0][1];
    const run = (url, hasTransition = true) => { art.style = {}; hero.style = {}; skipped = 0;
      handler({ viewTransition: hasTransition ? { skipTransition: () => { skipped++; } } : null, activation: { entry: { url } } });
      return { skipped, art: art.style.viewTransitionName || null, hero: hero.style.viewTransitionName || null }; };
    console.log(JSON.stringify({
      same: run('http://x/vehicles/this-machine'),
      next: run('http://x/vehicles/other-machine'),
      elsewhere: run('http://x/characters/jason-duval'),
      none: run('http://x/vehicles/this-machine', false),
    }));
    """ % ("function (w) { " + HANDLER.group(0).replace("window.addEventListener", "w.addEventListener").rsplit("})();", 1)[0] + " }")
    result = subprocess.run(["node", "-e", script], capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stderr[-400:]
    out = json.loads(result.stdout)
    assert out["same"] == {"skipped": 1, "art": None, "hero": None}                  # a reload or a form that sends you back here: skipped, nothing renamed
    assert out["next"] == {"skipped": 0, "art": "vehicle-art", "hero": "none"}       # to the next machine: its picture grows into the page, as before
    assert out["elsewhere"] == {"skipped": 0, "art": None, "hero": None}             # anywhere else: left to the browser, as before
    assert out["none"] == {"skipped": 0, "art": None, "hero": None}                  # no transition offered: nothing to do


def test_status_messages_keep_their_display_time_for_visitors_who_ask_for_reduced_motion():
    """site.css sets animation-delay: 0s !important on everything under reduced motion; without an override the message is hidden the moment it appears
    (found by running the account QA with reduced motion on)."""
    site = (ROOT / "app" / "static" / "css" / "site.css").read_text(encoding="utf-8")
    account = (ROOT / "app" / "static" / "css" / "account.css").read_text(encoding="utf-8")
    assert "animation-delay: 0s !important" in site                                    # the premise: the global rule exists
    block = re.search(r"@media \(prefers-reduced-motion: reduce\) \{\s*\.flash-stack \.flash \{([^}]*)\}", account)
    assert block and re.search(r"animation-delay:\s*7s\s*!important", block.group(1))
    assert re.search(r"\.flash \{[^}]*animation: flash-out [^;]*7s forwards", account)  # and the normal rule still times it at 7 seconds


def test_the_other_pages_with_transitions_are_not_touched():
    for name in ("garage.js", "garage_concept.js"):
        text = (ROOT / "app" / "static" / "js" / name).read_text(encoding="utf-8")
        assert "skipTransition" not in text, name                                    # the landing and the old Garage keep their own behaviour
