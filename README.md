# Grand Theft Auto VI | Team Valkyrie

> An unofficial educational fan project by Team Valkyrie. Not affiliated with, endorsed by, or sponsored by Rockstar Games or Take-Two Interactive.

A database-driven GTA VI information and discovery website built for a Web Technologies and DBMS college project.
**Status: Phase 1 of 6 (foundation).** The cinematic interface, accounts, admin tools and signature features come in later phases.

## Content honesty

Every record in the database carries a `content_status`:

| Status | Meaning |
|--------|---------|
| `official` | Confirmed by Rockstar Games. A source URL is **required** by a database constraint. |
| `fan` | Community or team interpretation, not confirmed. |
| `demo` | Fictional record invented by Team Valkyrie to demonstrate the database. |

Vehicles, missions and locations are demo data. The eight named characters and six regions are `official` (checked against rockstargames.com/VI/only-in-leonida on 2026-10-09). Nothing else is confirmed game content unless marked `official`.

## Technology

HTML5, CSS3, vanilla JavaScript, Jinja2 | Python 3.14 + Flask 3.1 (blueprints, application factory) | MySQL (InnoDB) via `mysql-connector-python` | pytest.

## Windows setup

Prerequisites: Python 3.11+, MySQL Server 8.x running as a service, and the MySQL admin (root) password. (Developed on Python 3.14.6 and MySQL 8.0.46. MySQL 8.4 LTS is the target and has not yet been tested.)

**Your MySQL admin password is typed only at a hidden prompt. It is never stored in `.env`, logged, or committed.**

Run from the project folder in PowerShell.

```powershell
# 1. Virtual environment and dependencies
python -m venv .venv
.\.venv\Scripts\Activate.ps1          # if blocked: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
pip install -r requirements-dev.txt

# 2. Configuration: creates .env with random secrets (values are not displayed)
python -m scripts.make_env

# 3. Database
python -m scripts.setup_db --plan      # READ-ONLY: shows what exists and exactly what would change
python -m scripts.setup_db             # applies the plan after you type YES

# 4. Tests
python -m pytest

# 5. Run the site
python -m flask --app wsgi run
```

Open <http://127.0.0.1:5000/>. Try <http://127.0.0.1:5000/api/v1/characters> and <http://127.0.0.1:5000/health>.

### What `setup_db` does (and never does)

| Object | Action |
|--------|--------|
| Databases `gta6_vi`, `gta6_vi_test` | Created only if missing. **Never dropped.** |
| Account `valkyrie_app` | The website's account: `SELECT, INSERT, UPDATE, DELETE` on the two project databases only. Cannot create, alter or drop anything. |
| Account `valkyrie_migrator` | Used only by the setup scripts: adds `CREATE, DROP, ALTER, INDEX, REFERENCES` on the same two databases. |
| Existing accounts | Passwords are **not** changed. Grants are only added. |
| Tables | Loaded only into a database that has none of the project tables. If any exist, they are left untouched. |
| Other databases, tables, accounts, `root` | Never touched. |

Rebuilding existing tables is deliberate and guarded: `python -m scripts.setup_db --reset` (or `python -m scripts.init_db --reset`) lists the tables and row counts it would drop and requires you to type a confirmation.

```powershell
python -m scripts.init_db                  # first-time load into an EMPTY database (refuses otherwise)
python -m scripts.init_db --reset          # drop + rebuild the project tables (typed confirmation)
python -m scripts.init_db --test --reset --yes   # test database only, no prompt
```

### Prefer to create the account yourself?

Run this as an admin in MySQL (use your own passwords, matching `DB_PASSWORD` and `MIGRATE_DB_PASSWORD` in `.env`), then run `python -m scripts.init_db` and `python -m scripts.init_db --test`:

```sql
CREATE DATABASE gta6_vi CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
CREATE DATABASE gta6_vi_test CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
CREATE USER 'valkyrie_app'@'localhost' IDENTIFIED BY 'choose-a-password';
CREATE USER 'valkyrie_migrator'@'localhost' IDENTIFIED BY 'choose-another-password';
GRANT SELECT, INSERT, UPDATE, DELETE ON gta6_vi.* TO 'valkyrie_app'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE ON gta6_vi_test.* TO 'valkyrie_app'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, ALTER, INDEX, REFERENCES ON gta6_vi.* TO 'valkyrie_migrator'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, ALTER, INDEX, REFERENCES ON gta6_vi_test.* TO 'valkyrie_migrator'@'localhost';
```

## Testing

```powershell
python -m pytest            # everything (needs MySQL; uses the *_test database only)
python -m pytest tests/test_integrity.py -v
```

Tests use the Flask test client **and a real MySQL test database**. The suite refuses to run against any database whose name does not end in `_test`.

## Project structure

```
GTA 6/
├── app/
│   ├── __init__.py            application factory
│   ├── config.py              settings from environment variables
│   ├── db.py                  connection pool, query helpers, transaction()
│   ├── errors.py              JSON / HTML error handling
│   ├── blueprints/            routes: main.py (pages), api.py (JSON)
│   ├── services/              validation and business rules
│   ├── repositories/          ALL SQL lives here
│   ├── templates/             Jinja2 (base, index, error)
│   └── static/css/main.css
├── database/                  schema.sql, seed.sql
├── scripts/                   setup_db.py (plan/apply), init_db.py, make_env.py, schema_info.py, sqlfile.py
├── docs/                      ARCHITECTURE, DATABASE (+ER diagram), ROUTES, MEDIA_INVENTORY, queries.sql
├── media/                     reserved for original/licensed assets only
├── tests/                     pytest suite
├── .env.example  .gitignore  LICENSE  pytest.ini  requirements*.txt  wsgi.py
```

## Documentation

* [Architecture](docs/ARCHITECTURE.md)
* [Database design and ER diagram](docs/DATABASE.md)
* [Example SQL queries](docs/queries.sql)
* [Routes and roadmap](docs/ROUTES.md)
* [Media inventory and rights](docs/MEDIA_INVENTORY.md)
* [Verification report](docs/VERIFICATION.md)

## Roadmap

1. **Foundation** (this phase)
2. Public website: cinematic homepage and catalogue pages
3. Authentication, favourites and admin CRUD
4. Leonida Atlas, Intelligence Network, terminal commands, global search
5. Media Theatre and cinematic polish
6. Final testing and presentation

## Licence and rights

Original source code: MIT, see [LICENSE](LICENSE). Grand Theft Auto VI, its names, characters, logos and media belong to Rockstar Games / Take-Two Interactive and are **not** covered by that licence. This repository contains no Rockstar media. See [docs/MEDIA_INVENTORY.md](docs/MEDIA_INVENTORY.md).
