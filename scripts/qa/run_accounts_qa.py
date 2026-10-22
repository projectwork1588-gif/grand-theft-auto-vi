"""Run the accounts browser QA against a TEST-configured server on its own port.

    python scripts/qa/run_accounts_qa.py [port]

What it does, in this order, and refuses to continue if any step fails:
  1. The testing config must name a *_test database, and a connection made with it must report a *_test database (SELECT DATABASE()).
  2. It starts the app with create_app("testing") (never the development or production config) in this process, on 127.0.0.1:<port> (default 5083),
     and checks that the pool the server really uses reports a *_test database too.
  3. Only then does it run scripts/qa/accounts_qa.mjs in a headless browser (the script creates accounts).
  4. It removes the QA accounts (usernames starting tt_) afterwards.
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


def database_name():
    connection = mysql.connector.connect(**TestingConfig.db_kwargs())
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT DATABASE()")
        return cursor.fetchone()[0]
    finally:
        connection.close()


def remove_qa_accounts():
    connection = mysql.connector.connect(**TestingConfig.db_kwargs())
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT DATABASE()")
        assert cursor.fetchone()[0].endswith("_test"), "refusing to delete: not a test database"
        cursor.execute("DELETE FROM users WHERE username LIKE %s", ("tt\\_%",))
        connection.commit()
        return cursor.rowcount
    finally:
        connection.close()


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5083
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
    remove_qa_accounts()
    logging.getLogger("werkzeug").setLevel(logging.ERROR)          # keep the request log out of the QA report
    server = make_server("127.0.0.1", port, app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        env = {**os.environ, "TL_BASE": f"http://127.0.0.1:{port}", "QA_SERVER_VERIFIED": "1"}
        code = subprocess.call(["node", str(ROOT / "scripts" / "qa" / "cdp.mjs"), str(ROOT / "scripts" / "qa" / "accounts_qa.mjs")], env=env, cwd=str(ROOT))
    finally:
        server.shutdown()
        print(f"removed {remove_qa_accounts()} QA account(s) from {served}")
    sys.exit(code)


if __name__ == "__main__":
    main()
