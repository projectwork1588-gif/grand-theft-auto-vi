# Architecture (Phase 1)

## The big picture in plain English

A visitor's browser asks Flask for a page or a JSON answer. Flask hands the request through **three layers**, each with one job:

```
Browser
  |  HTTP request
  v
Blueprint (app/blueprints/)      "What was asked?"      reads the URL + query string, returns HTML or JSON
  v
Service   (app/services/)        "Is it allowed? How should it look?"   validates input, applies rules, shapes the result
  v
Repository(app/repositories/)    "Ask the database."    the ONLY place SQL is written (always parameterized)
  v
app/db.py -> connection pool -> MySQL (InnoDB)
```

Why three layers? You can explain each in a viva in one sentence, tests can target each layer, and a SQL
mistake can only live in one folder.

## Key decisions

| Topic | Decision | Reason |
|-------|----------|--------|
| App creation | Application factory `create_app()` | Tests build their own app pointed at the test database. |
| Config | Environment variables via `.env` (`python-dotenv`) | No secrets in Git. |
| DB driver | `mysql-connector-python`, pure-Python mode, connection pool created lazily | Required stack. Pure mode avoids binary-wheel surprises. Lazy pool lets the app start and report a clear 503 when MySQL is down. |
| SQL safety | Values are always bound parameters. User input never becomes SQL text. Sorting uses a whitelist dictionary (`SORT_ORDERS`). LIKE wildcards are escaped. | Prevents SQL injection (tested). |
| Errors | JSON errors for `/api/*`, HTML for pages. Database errors become a generic 503 that never leaks SQL or credentials. | Safe and consistent. |
| Test safety | Config refuses to run tests on a database not ending in `_test`. | A test can never wipe real data. |
| MySQL account | App uses a dedicated non-root user with rights on only the project databases. | Least privilege. |
| IDs in URLs/JSON | Public slugs (`/characters/lucia-caminos`), internal numeric IDs are not exposed | Cleaner URLs, less enumeration. |

## Folder structure

See the tree in the README. Phase 1 contains no authentication, so there are no sessions, CSRF tokens or admin routes yet.
`SECRET_KEY` is read now so Phase 3 can use it.

## Issues found while reviewing the brief

1. **MySQL version:** the machine has 8.0.46, the brief says 8.4 LTS. Not run on 8.4 (see `DATABASE.md`).
2. **MySQL rule discovered by running the schema:** a `CHECK` cannot use a column whose foreign key has `ON UPDATE CASCADE` (error 3823). Fixed on `character_relationships`.
3. **Official data (corrected after verification):** the first pass could only reach the homepage and wrongly classed five regions as `fan`. Reading https://www.rockstargames.com/VI/only-in-leonida confirmed all six regions and eight characters (including Real Dimez). They are now `official`. See `docs/VERIFICATION.md`.
4. **Privilege separation (done):** the website account is DML-only. A separate `valkyrie_migrator` account holds the DDL rights needed by the setup scripts.
5. **CSRF (Phase 3):** no extra library is planned. A per-session token checked on every POST is small enough to hand-write and explain. Decision to confirm with the reviewer.
6. **Password hashing (Phase 3):** Werkzeug's `generate_password_hash` (scrypt, already installed with Flask), so no new dependency.
