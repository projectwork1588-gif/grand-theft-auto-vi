"""Run the admin (Stories) browser QA against a TEST-configured server on its own port.

    python scripts/qa/run_admin_qa.py [port]

What it does, in this order, and refuses to continue if any step fails:
  1. The testing config must name a *_test database, and a connection made with it must report a *_test database (SELECT DATABASE()).
  2. The chosen port must be free (a server already there could have another configuration).
  3. It starts the app with create_app("testing") (never the development or production config) in this process, and checks that the pool the server really uses
     reports a *_test database too.
  4. Only then does it make its test data (two accounts, one of them an administrator made with scripts/make_admin.py, which itself works on the test database only;
     an OFFICIAL story and an OFFICIAL place, inserted straight into the test database, to prove the browser cannot touch them; and the places the Places flows need)
     and run scripts/qa/admin_qa.mjs in a headless browser.
  5. It removes everything it made (accounts tt_*, stories tt-*, places tt-*, characters tt-*) afterwards.
Nothing here ever reads or writes the production database.
"""
import logging
import os
import socket
import subprocess
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

import mysql.connector                      # noqa: E402
from werkzeug.serving import make_server    # noqa: E402

from app import create_app                  # noqa: E402
from app.config import TestingConfig        # noqa: E402
from app.db import query_one                # noqa: E402
from scripts import make_admin              # noqa: E402
from tests import account_helpers as h      # noqa: E402
from tests import admin_helpers as ah       # noqa: E402

OFFICIAL_SLUG = "tt-qa-official"
OFFICIAL_PLACE, BLOCKED_PLACE, IMPACT_PLACE, IMPACT_STORY = "tt-qa-official-place", "tt-qa-blocked-place", "tt-qa-impact-place", "tt-qa-impact-story"


def database_name():
    connection = mysql.connector.connect(**TestingConfig.db_kwargs())
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT DATABASE()")
        return cursor.fetchone()[0]
    finally:
        connection.close()


def clean():
    """Remove the QA accounts, stories, places and characters (only ever on a database that proves it is a *_test one). Returns (accounts, stories, places) removed."""
    connection = mysql.connector.connect(**TestingConfig.db_kwargs())
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT DATABASE()")
        assert cursor.fetchone()[0].endswith("_test"), "refusing to delete: not a test database"
        cursor.execute("DELETE FROM characters WHERE slug LIKE %s", ("tt-%",))             # first: a resident's home is a foreign key to a place
        cursor.execute("DELETE FROM missions WHERE slug LIKE %s", ("tt-%",))
        stories = cursor.rowcount
        cursor.execute("DELETE FROM locations WHERE slug LIKE %s", ("tt-%",))
        places = cursor.rowcount
        cursor.execute("DELETE FROM users WHERE username LIKE %s", ("tt\\_%",))
        accounts = cursor.rowcount
        connection.commit()
        return accounts, stories, places
    finally:
        connection.close()


def make_test_data(app):
    """Two accounts (an administrator and an ordinary user), one official story and the places the Places flows need, all in the test database: an official place, a
    place an OFFICIAL character lives at (its delete is blocked) and a place with a demo resident, a story link, a favourite and a media link (its delete has consequences)."""
    admin_client, admin_name = h.signed_in_client(app)
    _user_client, user_name = h.signed_in_client(app)
    if make_admin.main(["--test", "--yes", admin_name]) != 0:
        sys.exit("refusing: could not make the QA administrator")
    h.execute("INSERT INTO missions (slug, title, mission_type, summary, synopsis, content_status, source_url) VALUES (%s, %s, 'side', 'official summary', 'official synopsis', 'official', %s)",
              (OFFICIAL_SLUG, "TT QA Official Story", "https://www.rockstargames.com/VI"))
    ah.make_place(OFFICIAL_PLACE, status="official", name="TT QA Official Place")
    ah.make_place(BLOCKED_PLACE, name="TT QA Blocked Place")
    ah.make_resident(BLOCKED_PLACE, status="official", slug="tt-qa-official-person")
    ah.make_place(IMPACT_PLACE, name="TT QA Impact Place")
    ah.make_resident(IMPACT_PLACE, slug="tt-qa-demo-person")
    ah.make_story(IMPACT_STORY, title="TT QA Impact Story")
    ah.link_story_to_place(IMPACT_STORY, IMPACT_PLACE)
    ah.save_place_as(user_name, IMPACT_PLACE)
    ah.link_media_to_place(IMPACT_PLACE)
    return admin_name, user_name


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5084
    if not TestingConfig.DB_NAME.endswith("_test"):
        sys.exit("refusing: the testing config does not name a *_test database")
    name = database_name()
    if not (name or "").endswith("_test"):
        sys.exit(f"refusing: the connection reports {name!r}, not a *_test database")
    with socket.socket() as probe:
        if probe.connect_ex(("127.0.0.1", port)) == 0:
            sys.exit(f"refusing: something is already listening on 127.0.0.1:{port} (it could be a server with another configuration); pick a free port")
    app = create_app("testing")
    with app.app_context():
        served = query_one("SELECT DATABASE() AS d")["d"]
    if not served.endswith("_test"):
        sys.exit(f"refusing: the server's own pool reports {served!r}, not a *_test database")
    print(f"database verified: {served} (server on 127.0.0.1:{port}, testing config)")
    clean()
    logging.getLogger("werkzeug").setLevel(logging.ERROR)          # keep the request log out of the QA report
    admin_name, user_name = make_test_data(app)
    server = make_server("127.0.0.1", port, app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        env = {**os.environ, "TL_BASE": f"http://127.0.0.1:{port}", "QA_SERVER_VERIFIED": "1", "QA_ADMIN": admin_name, "QA_USER": user_name, "QA_PASSWORD": h.PASSWORD,
               "QA_OFFICIAL_SLUG": OFFICIAL_SLUG, "QA_OFFICIAL_PLACE": OFFICIAL_PLACE, "QA_BLOCKED_PLACE": BLOCKED_PLACE, "QA_IMPACT_PLACE": IMPACT_PLACE,
               "QA_IMPACT_STORY": IMPACT_STORY}
        code = subprocess.call(["node", str(ROOT / "scripts" / "qa" / "cdp.mjs"), str(ROOT / "scripts" / "qa" / "admin_qa.mjs")], env=env, cwd=str(ROOT))
    finally:
        server.shutdown()
        accounts, stories, places = clean()
        print(f"removed {accounts} QA account(s), {stories} QA story/stories and {places} QA place(s) from {served}")
    sys.exit(code)


if __name__ == "__main__":
    main()
