# Grand Theft Auto VI | Team Valkyrie

> An unofficial educational fan project by Team Valkyrie. Not affiliated with, endorsed by, or sponsored by Rockstar Games or Take-Two Interactive.

A cinematic, database-driven GTA VI fan guide built for a Web Technologies and DBMS college project.
**Status: Phase 2 of 6 (cinematic public website).** Accounts, favourites, the admin area, the interactive atlas, the Intelligence Network and the full media theatre come in later phases.

## What you can do today

| Page | Address | What it shows |
|------|---------|---------------|
| Homepage | `/` | Cinematic hero (Welcome, Gamers / Team Valkyrie presents / Grand Theft Auto VI), the cast, six regions, garage highlights, story connections, official media preview. |
| Characters | `/characters`, `/characters/<slug>` | Poster wall with search, source and region filters, sorting and pagination. Profiles with biography, connections, missions, places and official images. |
| Garage | `/vehicles`, `/vehicles/<slug>` | Category chips, search, sorting. Detail pages with the missions and places each vehicle appears in. |
| Leonida | `/regions`, `/regions/<slug>` | The six regions on Rockstar's official page, each with its locations, people, stories and gallery. |
| Locations | `/locations`, `/locations/<slug>` | Searchable index filtered by region and type. |
| Stories | `/missions`, `/missions/<slug>` | Case-file archive with type filters. Cast, vehicles, places and related stories. |
| JSON API | `/api/v1/...` | Characters and regions (Phase 1, unchanged) plus vehicles, vehicle categories, missions and locations. |

Every page reads MySQL. Nothing about a character, vehicle, region, location or mission is written into HTML or JavaScript.

## Content honesty

Every record carries a `content_status`, shown as a badge on every card and page:

| Status | Meaning |
|--------|---------|
| **Official** | Stated on Rockstar's own website, with a source link. The eight named characters and six regions are official (checked against rockstargames.com/VI/only-in-leonida on 2026-10-09). |
| **Fan interpretation** | Community or team interpretation, not confirmed. None is seeded at present. |
| **Fictional demo** | Invented by Team Valkyrie to demonstrate the database: all vehicles, locations, missions and three characters. Demo stories deliberately use only demo characters, so we never invent story for the real cast. |

## Official media (nothing is copied)

Images and trailers are **remote references to Rockstar's own published media**:

* Trailer 1, Trailer 2 and "An Extended Look" play in **Rockstar's own embeddable player**, loaded only when a visitor presses play.
* Character artwork, region postcards and screenshots load from Rockstar's servers. They are never downloaded or committed.
* Every image has a built-in original fallback, so the site still looks right if Rockstar moves a file or you are offline.

See [docs/MEDIA_INVENTORY.md](docs/MEDIA_INVENTORY.md) for every asset, its source and its permission status. **Rockstar states no licence terms on its Media page**, so the owner should confirm the use is acceptable.

## Technology

HTML5, CSS3, vanilla JavaScript, Jinja2 | Python 3.14 + Flask 3.1 (blueprints, application factory) | MySQL (InnoDB) via `mysql-connector-python` | pytest. No frontend framework and no JavaScript libraries.

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

Open <http://127.0.0.1:5000/>.

### Upgrading a database you already set up in Phase 1

Phase 2 adds the official media records and one small table (`media_regions`). **Your existing data is never dropped.** The migration only creates that table if missing and inserts or refreshes the media rows.

```powershell
python -m scripts.migrate_db --plan     # READ-ONLY: shows what exists now and what would run
python -m scripts.migrate_db            # applies it after you type YES
```

Until you apply it, every page still works, but without the official images and trailers (original fallbacks are shown instead).

### What `setup_db` does (and never does)

| Object | Action |
|--------|--------|
| Databases `gta6_vi`, `gta6_vi_test` | Created only if missing. **Never dropped.** |
| Account `valkyrie_app` | The website's account: `SELECT, INSERT, UPDATE, DELETE` on the two project databases only. Cannot create, alter or drop anything. |
| Account `valkyrie_migrator` | Used only by the setup and migration scripts: adds `CREATE, DROP, ALTER, INDEX, REFERENCES` on the same two databases. |
| Existing accounts | Passwords are **not** changed. Grants are only added. |
| Tables | Loaded only into a database that has none of the project tables. If any exist, they are left untouched. |
| Other databases, tables, accounts, `root` | Never touched. |

Rebuilding existing tables is deliberate and guarded: `python -m scripts.setup_db --reset` (or `python -m scripts.init_db --reset`) lists the tables and row counts it would drop and requires a typed confirmation.

### Prefer to create the accounts yourself?

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
python -m pytest tests/test_pages.py -v
```

Tests use the Flask test client **and a real MySQL test database**. The suite refuses to run against any database whose name does not end in `_test`. It covers pages, filters, search, sorting, pagination, related-content queries, invalid routes, database failures, escaping, security headers, a full link crawl, the migration upgrade path and the privilege split.

## Project structure

```
GTA 6/
├── app/
│   ├── __init__.py            application factory, template helpers, security headers
│   ├── config.py              settings from environment variables
│   ├── db.py                  connection pool, query helpers, transaction()
│   ├── errors.py              JSON / HTML error handling
│   ├── media_urls.py          only Rockstar's official image and player URLs are ever rendered
│   ├── media_slots.py         which stored media rows the homepage features
│   ├── blueprints/            routes: main.py (home), pages.py (HTML), api.py (JSON)
│   ├── services/              validation, business rules, page view-models (site.py)
│   ├── repositories/          ALL SQL lives here
│   ├── templates/             Jinja2: base, _components, home, characters/, vehicles/, regions/, locations/, missions/
│   └── static/                css/ (site, components, pages), js/ (boot, site), img/vehicles.svg
├── database/                  schema.sql, seed.sql, migrations/001_phase2_media.sql
├── scripts/                   setup_db.py, init_db.py, migrate_db.py, make_env.py, schema_info.py, sqlfile.py
├── docs/                      ARCHITECTURE, DATABASE (+ER diagram), ROUTES, MEDIA_INVENTORY, VERIFICATION, queries.sql
├── media/                     reserved for original/licensed assets only (empty)
├── tests/                     pytest suite
├── .env.example  .gitignore  LICENSE  pytest.ini  requirements*.txt  wsgi.py
```

## Documentation

* [Architecture and design system](docs/ARCHITECTURE.md)
* [Database design and ER diagram](docs/DATABASE.md)
* [Example SQL queries](docs/queries.sql)
* [Routes and roadmap](docs/ROUTES.md)
* [Media inventory and rights](docs/MEDIA_INVENTORY.md)
* [Verification reports](docs/VERIFICATION.md)

## Roadmap

1. Foundation (done)
2. **Cinematic public website** (this phase)
3. Authentication, favourites and admin CRUD
4. Leonida Atlas, Intelligence Network, terminal commands, global search
5. Media Theatre and cinematic polish
6. Final testing and presentation

## Licence and rights

Original source code, including the vehicle silhouettes in `app/static/img/vehicles.svg`: MIT, see [LICENSE](LICENSE). Grand Theft Auto VI, its names, characters, logos, images and videos belong to Rockstar Games / Take-Two Interactive and are **not** covered by that licence. This repository contains no Rockstar media: official images and videos are referenced from Rockstar's own servers. See [docs/MEDIA_INVENTORY.md](docs/MEDIA_INVENTORY.md).
