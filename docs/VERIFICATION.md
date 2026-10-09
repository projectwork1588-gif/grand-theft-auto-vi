# Phase 1 verification report (post-review)

Date: 2026-10-09. Scope: the eight verification tasks requested after ChatGPT's review. Phase 2 has **not** been started and the homepage was **not** redesigned.

## Status at a glance

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
