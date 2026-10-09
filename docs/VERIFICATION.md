# Verification reports

## Phase 1: verified on the owner's computer (2026-10-09)

The owner ran the Phase 1 verification steps on their own Windows machine against the **locally installed MySQL 8.0.46 service** and reported:

| Check | Result |
|-------|--------|
| MySQL database setup (`scripts.setup_db`) | Completed successfully |
| Automated tests | **106 passed** |
| Flask homepage, JSON APIs and health check | Worked in the browser |

This closes the items that the historical report below lists as pending the owner's run (its tasks 1 and 6). MySQL 8.4 LTS is still untested.

## Phase 2: cinematic public website (2026-10-09)

### Test results (real MySQL 8.0.46 service, `gta6_vi_test` database only)

```
python -m pytest -q
244 passed in 92.39s
```

| File | Tests | Covers |
|------|-------|--------|
| `test_pages.py` | 45 | Homepage, every list and detail page, search, filters, sorting, pagination, labels, 400 and 404 pages, malformed input |
| `test_api_phase2.py` | 15 | Vehicles, categories, missions, locations, related-content joins, Phase 1 response shapes unchanged |
| `test_media.py` | 9 | URL allow-listing, cover selection, hostile URLs, missing media tables, error handling |
| `test_security_and_failures.py` | 53 | CSP and headers, no inline script or style, escaping of hostile data, safe 503 and 500 pages |
| `test_site_integrity.py` | 5 | Crawl of every internal link, static assets, HTML balance, one `h1`, alt text, labelled forms |
| `test_migration.py` | 7 | Migration is non-destructive, idempotent, equals a fresh seed, and works on a Phase 1-shaped database |
| Phase 1 files | 110 | Connectivity, integrity, seed, privileges, setup safety, APIs, SQL runner (updated for 19 tables and 57 media rows) |

The suite grew from 106 to 244 tests. No Phase 1 test was removed or weakened. Counts and media expectations were updated where the schema and seed legitimately changed.

### Browser verification (built-in browser, 2026-10-09)

| Check | Result |
|-------|--------|
| Homepage hero with official Jason and Lucia artwork, identity text and entrance animation | Verified by screenshot |
| Cast posters, region panels, garage rows, official connections, media mosaic, profile page | Verified by screenshot |
| Trailer dialog: opens Rockstar's player (`autoplay=true`), caption shows attribution, Escape removes the iframe and returns focus | Verified by script |
| Phone width (375px): no horizontal overflow on the homepage, characters, regions, vehicle, mission and locations pages | Verified by script |
| Mobile menu: opens, marks the current page, closes on Escape with focus returned | Verified by script |
| Official page links (7) and all 57 media URLs | HTTP 200 |
| Console | No errors (one warning, fixed) |

Screenshots were viewed during development but are **not committed**: they contain Rockstar's artwork, which must not enter the repository.

### Defects found and fixed during Phase 2

| # | Defect | Found by | Fix |
|---|--------|----------|-----|
| 1 | The migration runner never committed its INSERTs | `test_seed_and_migration_agree` | Explicit commit, rollback on error, verification on a new connection |
| 2 | Reduced-motion rule hid the hero slideshow completely | Browser check | Still first image for reduced-motion visitors |
| 3 | Pager helpers undefined inside imported macros | Page tests | Registered as template globals |
| 4 | `/characters/Jason-Duval` resolved because MySQL's collation ignores case | `test_unknown_routes_and_slugs...` | Strict lowercase slug validation before any query |
| 5 | A load-time check marked a still-loading hero image as broken | Browser check | Check runs after the load event |
| 6 | Redundant `allowfullscreen` console warning | Browser console | Removed |
| 7 | Regions listed alphabetically instead of in Rockstar's order | Visual review | Pages use Rockstar's order, the API stays alphabetical |

### Not yet done

* `python -m scripts.migrate_db` has **not** been run against the owner's development database `gta6_vi`. Their approval is requested. Until then that database lacks the official images and trailers, and pages show fallbacks. The test database does have everything.
* MySQL 8.4 LTS untested.
* Official image URLs are build-hashed and may change.
* Rockstar states no licence terms for its media: human review recommended.

## Phase 2 design refinement pass (2026-10-10)

### Test results (real MySQL 8.0.46 service, `gta6_vi_test` database only)

```
python -m pytest -q
259 passed in 92.59s
```

| File | Tests | Covers |
|------|-------|--------|
| `test_pages.py` | 55 | Every page, filters, search, sorting, pagination, labels, 400/404 pages, and the design feedback (hero text removed, brand lockup, calm labels, official-only garage, clip cards, closing band, page backdrops) |
| `test_api_phase2.py` | 15 | Vehicles (13 in the API, 5 official), categories with `status`, missions, locations, Phase 1 shapes unchanged |
| `test_media.py` | 9 | URL allow-listing, covers, hostile URLs, missing tables |
| `test_security_and_failures.py` | 53 | CSP, no inline script or style, escaping, safe 503 and 500 pages |
| `test_site_integrity.py` | 5 | Link crawl, assets, HTML balance, one `h1`, alt text |
| `test_migration.py` | 7 | Three migrations: non-destructive, idempotent, upgrade equals a fresh seed, official rows untouched |
| Earlier files | 115 | Connectivity, integrity, seed (now 85 media rows, 13 vehicles), privileges, setup safety, SQL runner, example queries (14) |

The suite grew from 244 to 259. No test was removed or weakened. Expectations changed only where the feedback deliberately changed behaviour (the garage, the label wording, the removed silhouette sprite).

### Browser verification (built-in browser)

| Check | Result |
|-------|--------|
| Desktop (1280 px): hero, cast, garage mosaic, stories band, media reel with posters and clip rail, closing band, footer | Verified by screenshot |
| Desktop: garage list, vehicle page, character profile with clip card, concept story page | Verified by screenshot |
| **Tablet (768 px):** hero, regions (two columns), garage (wide feature plus 2 by 2), stacked trailers | Verified by screenshot |
| Tablet: no horizontal overflow on characters, character profile, garage, vehicle, regions, story and locations pages | Verified by script |
| Phone (375 px): no overflow on the homepage, garage, vehicle, character and stories pages | Verified by script |
| Phone hero and mobile menu | Verified by screenshot and script |
| Trailer dialog opens Rockstar's player and closes cleanly | Verified (earlier pass, code unchanged) |

Screenshots were viewed during development and are **not** committed: they contain Rockstar's artwork.

### Official sources checked

* /VI/editions: named vehicles. Several look like vehicles but are stores or services (Stock 305, Electric Fang, Rideout Customs, One-Eyed Willie's), so they were **not** added.
* /VI/media/screenshots: the vehicle image sets. The images were looked at to confirm each shows the named vehicle.
* /VI/media/videos: eight character clips, trailer posters, and the video files. The files are 4K and large (Trailer 2 is about 1.2 GB), so no autoplay background video was built.
* All 28 new image URLs returned HTTP 200 with the expected content type.

### Problems found and fixed in this pass

| # | What failed | Category | Cause and fix | How verified |
|---|-------------|----------|---------------|--------------|
| 1 | Page tests found "Fictional demo mission invented by Team Valkyrie..." on pages | Content | The blunt wording was stored in the **database copy**, not only the templates. Rewrote the copy in the seed and added migration 003 (UPDATE only) | Tests assert the old wording appears nowhere on public pages. The upgrade test restores the old text, migrates, and compares with a fresh seed |
| 2 | Closing band showed no artwork | Code (CSS) | The image frame inside the band collapsed to zero height | Fixed the frame to fill the band. Seen in a screenshot |
| 3 | The large garage tile showed the car park, not the car | Design | Wrong focal point | Adjusted the crop. Seen in a screenshot |
| 4 | `tests/test_pages.py` was emptied | Tooling | My script opened the file for writing, then failed on a Windows text-encoding error | Restored the file from Git and re-applied the edits. All 55 tests present and passing |
| 5 | SQL error in a new seed test | Code (test) | `character` is a reserved word in MySQL | Renamed the alias |
| 6 | A test regex and two counts were wrong | Code (test) | Escape and prefix mistakes in my own tests | Corrected and re-run |
| 7 | A meaningless `or True` assertion in a draft migration test | Code (test) | Would have passed whatever happened | Replaced with a real check that official rows are unchanged, and searched the suite for any other `or True` |
| 8 | Garage tests, table counts, FK counts, the migration file list | Expected change | The new vehicles, `media_vehicles` and migrations changed totals on purpose | Expectations updated and new tests added |

### Not yet done

* **The owner's development database has not been migrated.** `python -m scripts.migrate_db --plan` then `python -m scripts.migrate_db` applies migrations 001 to 003. Until then that site shows fallbacks and an empty garage.
* MySQL 8.4 LTS untested. Rockstar states no licence terms for its media. Image file names are build-hashed and may change.

---

## Phase 1 post-review verification (historical record)

Date: 2026-10-09. Scope: the eight verification tasks requested after ChatGPT's review. Phase 2 has **not** been started and the homepage was **not** redesigned.

### Status at a glance (as of that report)

| # | Task | Status |
|---|------|--------|
| 1 | Verify setup against the locally installed MySQL 8.0.46 service | **NOT DONE: needs the owner to run two commands (see "Run on your service")** |
| 2 | Handle the MySQL password safely | Done: never stored, logged or committed; hidden prompt only |
| 3 | Inspect and explain what setup will create/modify/delete before running | Done: read-only `--plan` mode added, and the script now refuses destructive actions by default |
| 4 | Separate app privileges from setup privileges | Done and tested on a scratch MySQL 8.0.46 server |
| 5 | Verify official character/region data and fix classifications | Done: corrections made (details below) |
| 6 | Run tests against the local test database | Partly done: 106/106 pass on a **scratch** server. **Not yet run on the owner's service** |
| 7 | `.env` ignored by Git, no credentials in tracked files | Done (verified in a throwaway Git repo) |
| 8 | Do not begin Phase 2 | Respected |

## Run on your service (owner action required)

Nothing below has been run against your MySQL80 service yet. Your service was only inspected (it is running, and `root` without a password is refused). Run these in a PowerShell terminal in the project folder. **You** type the password at the hidden prompt.

```powershell
.\.venv\Scripts\python.exe -m scripts.setup_db --plan
```

This is read-only. It shows the databases, accounts and tables that exist and exactly what would change. Paste the output back for review. If it looks right:

```powershell
.\.venv\Scripts\python.exe -m scripts.make_env
.\.venv\Scripts\python.exe -m scripts.setup_db
.\.venv\Scripts\python.exe -m pytest
```

`make_env` writes a local `.env` with random passwords for the two application accounts. It does not display them and does not contain your MySQL admin password.

## What the setup script will and will not do

* **Creates (only if missing):** databases `gta6_vi`, `gta6_vi_test`; accounts `valkyrie_app`@localhost and `valkyrie_migrator`@localhost.
* **Grants:** app = SELECT, INSERT, UPDATE, DELETE. Migrator = those plus CREATE, DROP, ALTER, INDEX, REFERENCES. Both limited to the two project databases.
* **Never:** drops a database, alters or drops an account, changes any password (including root), touches other databases, tables or accounts, or drops tables unless `--reset` is given and `RESET` is typed after a list of tables and row counts.
* A source-code test (`test_no_statement_in_setup_script_touches_root_or_alters_users`) fails if the script ever contains `ALTER USER`, `DROP USER`, `SET PASSWORD`, `DROP DATABASE`, `FLUSH PRIVILEGES` or `GRANT OPTION`.

## Findings from this verification round

1. **Defect fixed: `REFERENCES` privilege.** A first draft that removed it from the migration account failed with `1142 REFERENCES command denied`. MySQL needs it to create foreign keys.
2. **Defect fixed: half-built schema.** MySQL DDL cannot be rolled back, so a failed load left 2 of 18 tables. The protections correctly refused to touch it, but the plan now reports `WARNING ... 2 of 18 ... use --reset`, and recovery with `--reset` was demonstrated.
3. **Behaviour change:** `init_db` previously dropped tables unconditionally. It now refuses when project tables exist unless `--reset` and a typed confirmation (database name) are given. `--yes` is honoured only for databases ending in `_test`.
4. **Privilege split:** `tests/test_privileges.py` proves the website account is refused DROP, CREATE, ALTER, TRUNCATE, CREATE USER, DROP DATABASE and reading `mysql.user`, and still reads and writes rows.
5. **Transcript exposure:** the MySQL password was pasted into the chat, so it exists in this conversation's transcript. It was not written to any file or command. Rotating it afterwards is advisable.
6. **Terminal limitation:** an attempt to open the app's Terminal panel for a hidden password prompt timed out (shell never reached a prompt). Nothing was typed or run. This is why the local-service steps are listed as owner actions.

## Source-data corrections (task 5)

Checked on 2026-10-09 by reading https://www.rockstargames.com/VI, https://www.rockstargames.com/VI/only-in-leonida, https://www.rockstargames.com/VI/leonida-keys, https://www.rockstargames.com/VI/only-in-leonida/lucia and https://www.rockstargames.com/VI/media. (A guessed `/VI/characters` page returned 404.)

| Item | Phase 1 report said | Official page shows | Fix |
|------|--------------------|---------------------|-----|
| Leonida Keys, Grassrivers, Port Gellhorn, Ambrosia, Mount Kalaga | `fan` (only secondary sources) | All five are listed as explorable regions | Reclassified `official`, sourced to `/VI/only-in-leonida` |
| Real Dimez | missing | Listed as a character (duo Bae-Luxe and Roxy) | Added as `official` |
| Cal Hampton, Boobie Ike, Dre'Quan Priest, Raul Bautista, Brian Heder | `official`, sourced to Game Informer | Listed on Rockstar's own page | Source changed to the official page |
| Official character biographies | withheld | Descriptions exist on the page | Added short **paraphrases** (not copied text) |
| Relationships | Jason-Lucia only | Brian-Jason, Cal-Jason, Boobie Ike-Dre'Quan stated | Added three `official` relationships |
| Media rows | all pointed at `/VI` | `/VI/trailer-1`, `/VI/trailer-2`, `/VI/media` exist | URLs corrected; still `link_only` and `pending_review` |
| Ambrosia's associated character | n/a | Two fetches of the page disagreed (Brian vs Raul) | No association stated |

Not verified: embed URLs for the trailers, licence terms for the downloads (the Media page states none), and the exact on-page wording behind each paraphrase (the fetch tool returns summaries). Vehicles, missions and locations remain `demo`; nothing official exists in those categories in the seed.

## Commands run and results (scratch MySQL 8.0.46, port 3399, separate data directory)

| Command | Result |
|---------|--------|
| `python -m scripts.setup_db --plan` | Plan printed, nothing changed; bystander database listed as "never touched" |
| `python -m scripts.setup_db --yes` | Failed on `REFERENCES` (finding 1), left 2 tables (finding 2) |
| `python -m scripts.setup_db --reset` (answer `RESET`) | Dropped 2 empty tables per database, rebuilt: 38 schema + 11 seed statements OK in both databases |
| `python -m scripts.setup_db --plan` (after) | `SKIP ... 18 project tables (80 rows)`, no DROP |
| `python -m scripts.setup_db --yes` (again) | `left untouched` for both databases |
| `python -m scripts.init_db` (no flags) | `REFUSED`, exit code 2 |
| `python -m scripts.init_db --reset` with a wrong confirmation | Cancelled, exit code 2, nothing changed |
| SQL check as scratch admin | 11 characters present; bystander table value 42 intact |
| `python -m pytest -q` | **106 passed** in 39 s |

Test breakdown: 81 earlier tests (updated for corrected data), plus 2 new seed-source tests, `test_privileges.py` (11) and `test_setup_safety.py` (12) = 106.

## Git and credential checks (task 7)

Run in a throwaway copy of the project with `git init` (the project folder itself is not a repository):

* `git check-ignore -v .env` -> ignored by `.gitignore:2`.
* A fake `media/big_trailer.mp4` is ignored by `.gitignore:26`.
* `git ls-files`: 56 files; `.env` is not tracked; only `.env.example`, `media/.gitkeep`, `media/README.md` appear under those names.
* Credential scan of tracked files: only placeholders (`change_me`, `change_me_too`, `replace-with-a-long-random-string`), code identifiers (`getpass`), and the fake string `hunter2` used in a test to prove error messages do not leak secrets. No scratch passwords and no real credentials.
* The real project folder has no `.env` yet.
* Minor: Git warns about LF/CRLF conversion on Windows. Harmless; a `.gitattributes` could silence it.

## Remaining blockers and limits

1. **Local service verification is pending** (owner must run the commands above and paste the `--plan` output).
2. **MySQL 8.4 LTS** still untested (the installed server is 8.0.46).
3. Tests have run only against the scratch server so far, so the "tests on your local test database" requirement is open until step 1 is done.
4. Trailer embed URLs and download licence terms need human review before Phase 5.
5. The `valkyrie_app` account also has rights on the test database so the suite can run; a separate test-only account is possible if desired.
