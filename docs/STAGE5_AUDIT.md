# Stage 5 audit (read-only), 24 October 2026

Scope: the whole repository as it stands at the end of Stage 4B (`feature/stage4b-search`, `8ed0a61`), audited before any Stage 5 change. Nothing here was merged, deployed or
migrated; the production database `gta6_vi` was never opened. Everything that touched MySQL used the test configuration and `gta6_vi_test`. The only repository file written
during the audit was a temporary probe test (created, run and deleted; the working tree was clean afterwards). This file is the audit's one product.

## 1. Git state (verified, not assumed)

```
* 8ed0a61 (feature/stage4b-search = origin)  Stage 4B milestone 4
* 5e5114e                                    Stage 4B milestone 3 (palette)
* 43772b1                                    Stage 4B milestones 1-2 (search backend, API, page)
* 62d63d7 (feature/stage4a-polish = origin)  Stage 4A docs
* fcdc147                                    Stage 4A code
* 1dc28f2 (feature/admin-places-m2 = origin) Stage 3 milestone 2
* 449805a (docs/db-schema-sync, local only)  DATABASE.md sync
* 0944081 (feature/admin-stories-m1, local)  Stage 3 milestone 1
* a2cc94b (main = origin/main)               merge of PR #1 (wip/phase1-accounts-hardening = origin)
```

* One linear stack of 8 commits on top of `main`; nothing diverges. Every pushed branch is an ancestor of the next one, so no work exists only on this machine except the
  two Stage 3 branch labels (their commits are inside the pushed history) and two older local branches (`backup/regions-v1-d81584f`, `claude/kind-neumann-f075f6`, a worktree).
* `main` is unchanged since the PR #1 merge. **Stage 3, 4A and 4B are all unmerged.** Stage 5 work is on `feature/stage5-delivery`, created from `8ed0a61`.
* No branch was renamed, deleted or rewritten. No stashes, no tags.
* History scan: `.env` was never committed; the only secret-shaped match in all history is the placeholder `SECRET_KEY=replace-with-a-long-random-string` in `.env.example`.
  The repository packs to 1.7 MiB and holds no binary or large tracked file.

## 2. Verdict

The product is in good shape and the evidence below is mostly clean. **One genuine security defect was found and verified (M1)**, plus one regression in test tooling (M2) and
a set of verified documentation drifts (M3). The rest is hardening, deployment preparation and limits that are already documented.

## 3. Findings, separated by what has to happen

### Must fix (verified, small, inside the approved architecture)

| ID | Finding | Evidence |
|----|---------|----------|
| **M1** | **A `HEAD` request skips CSRF and performs the action.** Views decide "is this a submission?" with `request.method == "GET"`. Flask answers `HEAD` through every GET route, so `HEAD` falls into the submission branch, and the CSRF check only covers POST/PUT/PATCH/DELETE. On the admin delete routes this runs the delete. The stage 3 authz tests iterate `methods - {HEAD, OPTIONS}`, so it was never exercised. | Probe on the test database with a signed-in administrator: `HEAD /admin/stories/<slug>/delete` and `HEAD /admin/places/<slug>/delete` both answered 303 and the story and place were gone (stories 6 to 5, places 9 to 8), with no token. Also: five `HEAD /login` requests give 401 and the sixth onward 429 (they spend the sign-in throttle); `HEAD /register` runs the sign-up path. 9 views use the pattern (`account.py` x3, `admin.py` x6). Practical exploitability is limited by `SameSite=Lax` (a cross-site page cannot send a cookie-bearing HEAD), but it breaks the documented guarantee and is a defence-in-depth failure on a destructive action. |
| **M2** | **`scripts/qa/admin_qa.mjs` fails 7 checks since Stage 4A.** It asserts the 403 page's `h1` is "Forbidden"; Stage 4A made the `h1` "Restricted area" (the words "Error 403 - Forbidden" are still in the eyebrow and the title). The product is right and the unit tests pass; the browser script was not updated, and I did not run the admin journey in Stage 4A. | `run_admin_qa.py`: 97 pass, 7 fail, in both normal and reduced-motion runs; all 7 are `/Forbidden/.test(heading)`. |
| **M3** | **Verified documentation drift.** (a) `ARCHITECTURE.md` line 116 (dated refinement log) says "only the five vehicles"; seven are official since migration 006. (b) `ROUTES.md` "Planned" still lists `/search` (built in 4B) and "official vehicle imagery (needs a `media_vehicles` junction)" (built in migration 002). (c) `README.md` status and roadmap still call global search a later phase. (d) `VERIFICATION.md` stops at Phase 2 (244 tests): nothing records Stages 3 to 4B (1,749 tests). | Scripted check of 31 documents: every relative link and anchor resolves and every `python -m scripts.X` exists (no drift of that kind); the four items above were found by reading against the code and the URL map. |

### Should fix / decisions to take (need your approval because they touch the database layer, configuration or deployment)

| ID | Finding | Evidence and proposal |
|----|---------|-----------------------|
| S1 | **Connection pool exhaustion answers 503 immediately above 5 simultaneous requests.** The pool is 5 and a pool miss raises at once. With the threaded development server (unbounded threads), 15 concurrent searches gave 17 x 200 and 73 x 503; 40 gave 24 x 200 and 216 x 503. It is documented ("the pool needs at least as many connections as requests a worker runs at once") and fine for one-request-per-worker servers, but a threaded host would hit it. | Proposal: a short bounded wait (about 2 s) for a free connection before the 503, plus a documented pool/thread rule. A change to `app/db.py`: your call. |
| S2 | **MySQL cold-start timeout (section 5).** Not reproduced; cause not proven. | Needs your approval for the two controlled experiments in section 5 before any fix. |
| S3 | **No HSTS header.** The app sets CSP, nosniff, Referrer-Policy and Permissions-Policy but not `Strict-Transport-Security`; the session cookie is `Secure` only under the production config. Free hosts terminate TLS but do not add HSTS. | Proposal: send HSTS when running the production config over HTTPS. |
| S4 | **Deployment prerequisites are missing from the repository.** `requirements.txt` has no production WSGI server (the docs name gunicorn/waitress but neither is listed); there is no process file or container file; the database connection has no TLS options (`DB_SSL_CA`), which every managed MySQL below requires. | Proposal in section 7, no deployment. |
| S5 | **One test takes 14 minutes** (`test_garage_pointer.py::test_explore_button_responds_over_its_whole_surface_for_all_seven_machines`, 727 to 865 s in three runs) and the whole suite takes 31 to 36 minutes. | Proposal: mark it `slow` (still run before release), so a normal run is quick. Optional on my side. |
| S6 | **The live (local) `gta6_vi` state is unknown to me**: which of migrations 001 to 010 it has, whether 010 is applied, and whether the admin area should be enabled there. | Owner decision, in `docs/ACCOUNTS.md` and `docs/ADMIN.md`. I will not touch it. |

### Optional improvements

* O1 `robots.txt` (404 today). *Correction made during Stage 5:* the audit first also listed a missing favicon; that was wrong. `base.html` already declares one (`static/img/favicon.svg`); only the legacy `/favicon.ico` probe returns 404, which is harmless, so nothing is needed.
* O2 A rate limit on `/api/v1/search` (a public read costing about 6 ms; a decision, not a defect).
* O3 FULLTEXT for search (would need a migration; not needed at about 300 rows).
* O4 The About page's lead-in links ("Characters: ...") are 23 px tall; they sit in a sentence, so they are exempt from WCAG 2.5.8.
* O5 `Server: Werkzeug/3.1.9 Python/3.14.6` is sent by the development server only; a production server decides its own.
* O6 `Allow` header on 405 responses; `garage_transitions_qa` has a timing check that fails when the machine is busy (2 failures in 4 runs, 22/22 otherwise).
* O7 Run `pip-audit` (or equivalent) in CI; the installed versions (Flask 3.1.3, Werkzeug 3.1.9, mysql-connector-python 26.7.0) were not checked against an advisory database in this audit.
* O8 MySQL 8.4 LTS is the stated target and has never been tested (README).

### Known limitations (documented, accepted, no action proposed)

Stateless signed-cookie sessions cannot be revoked (they expire after 8 hours or on a password change); no email, so no password reset; the sign-in throttle is per
process; no CAPTCHA; no migration history table (a bare `migrate_db` re-runs everything, with a confirmation phrase); the website's database account has database-wide DML
(a narrower grant is documented, not applied); the cinematic loops are not in the repository (pages fall back to stills); and Rockstar states no licence terms for the media it
references (the owner's decision, in `docs/MEDIA_INVENTORY.md`).

## 4. Audit results by area

| Area | What was done | Result |
|------|---------------|--------|
| End-to-end journeys | `run_accounts_qa.py` (register, save on all four kinds, list, sign out, sign in, remove, change password, CSRF, layout) and `run_admin_qa.py` (access, dashboard, create with the keyboard, validation, edit, official-content lock, delete, CSRF, four widths), each on a TEST-configured server with its own guard. The public journeys (home, every section, search, palette, characters, garage, regions, music, media) were last run at `8ed0a61`: all pass; not repeated here. | Accounts 74/74. Admin 97/104; the 7 failures are M2. |
| Authentication and authorization | Anonymous request to every one of the 47 routes with every method (GET, POST), plus HEAD, OPTIONS, PUT, DELETE, PATCH, TRACE; POST without token, with a foreign Origin, with an oversize body; scrypt hashing; cookie flags. | No 5xx anywhere; all 12 token-less POSTs refused (400); oversize 413; foreign Origin 400; PUT/DELETE/PATCH/TRACE 405; cookie `HttpOnly`, `SameSite=Lax`, 8 h (`Secure` in production). **Defect M1 (HEAD).** |
| Security | 322 hostile requests (NUL, invalid UTF-8, 5,000-character values, SQL fragments, arrays, huge numbers) to 14 list/search endpoints; 19 path-handling probes (traversal, encoded dots, double slashes, backslash, absolute-form request, forwarded host); raw-socket checks; headers; history scan. | 0 server errors; no traversal; no open redirect (a `//evil.example` redirect seen in the test client was an artefact: the real server answers 404); redirects use the request's own host; CSP unchanged and strict. HSTS absent (S3). |
| Database integrity | Fresh seed of `gta6_vi_test`, then read-only queries over `information_schema` and every table. | 27 InnoDB tables, one collation (`utf8mb4_0900_ai_ci`), every table has a primary key, 34 foreign keys with **0 orphans** and all indexed, 11 CHECK constraints (an official row must cite a source; none violated), all slugs valid, every stored URL is https and on an allow-listed host, nothing markup-like in stored text. |
| Migrations | Read the 010 procedure and safety notes; the suite covers idempotency, conflicts, `--only`, seed/migration agreement (the slowest files). | Sound. Standing limits: no history table; 010 not applied to the live database; live state unknown (S6). |
| Documentation | Scripted scan of 31 documents (links, anchors, referenced files, commands) and a read of every status claim. | No broken links. Drift items M3. Historical design documents refer to files in the git-ignored `review/` folder (acceptable, they are dated records). |
| Accessibility | 18 pages x 7 widths (320 to 1920) in a real browser, plus the keyboard and reduced-motion probes from Stage 4A (re-run in 4B). | 140 measurements: 0 overflow, 0 missing alt, 0 broken images, 0 heading skips, 0 console/page/request/CSP errors, exactly one `h1` and one `main` everywhere, language, description and skip link on every page, no unlabelled form field, no clipped heading/button/chip text, smallest font 12 px. Only flags: links inside sentences under 24 px (exempt) and one deliberately hidden duplicate link (`aria-hidden`, `tabindex="-1"`). |
| Responsive layouts | Same sweep. | No sideways overflow at any width; the horizontally scrolling rails (cast, garage, media index) are intentional scroll containers. |
| Error handling | Routes, hostile input, branded 400/403/404/405/413/429/500/503 pages, JSON for `/api`, database-down 503 (tests), raw requests. | As designed; no stack trace, SQL or credential on any response. 405 has no `Allow` header (O6). |
| Search | 4B suites, plus concurrency. | Correct and fast (p95 5.9 ms warm). Concurrency finding S1. |

## 5. MySQL cold-start timeout (diagnosis only; test configuration; nothing changed)

**The symptom.** While starting the test server in Stage 4A, the first connection failed with `ConnectionTimeoutError 3024: Read Operation timed out`; a retry a moment later
worked, and the first handshake had measured 4.48 s against the application's `connection_timeout=5`.

**What the error is.** In `mysql-connector-python` 26.7.0 the 5 s `connection_timeout` is the socket timeout while connecting and during the handshake. I tested whether it
also limits queries: `SELECT SLEEP(6)` through a connection configured exactly like the application's succeeds (6.0 s). So the error can only come from a stall of more than 5 s
*during connect or authentication*, never from a slow query.

**Reproduction attempts (test account, `gta6_vi_test`, read-only):**

| Condition | Result |
|-----------|--------|
| First connection from a fresh process | 131 ms |
| 20 further new connections | 26 to 29 ms (median 27) |
| After 1, 3, 5 and 10 minutes idle | 41 to 68 ms |
| Client-side name lookups of `127.0.0.1` and `::1` | 0.2 to 44 ms |

**Not reproduced.** Conclusions from what was measured:

* DNS is not the cause: the host is `127.0.0.1`, MySQL special-cases loopback clients, and lookups here take milliseconds.
* The server's caching is not the cause: `caching_sha2_password` authentication is about 27 ms per connection.
* A hypothesis that fits the evidence but is **not proven**: the `mysqld` process had 720 MB of private memory but only 244 MB resident when I looked (about two thirds
  paged out or trimmed by Windows on an 8 GB machine). After a long idle period or a wake from sleep, the first handshake would then wait on page faults. Short idle gaps do not
  trigger it, which matches the failed reproduction.

**What I need from you before going further (nothing was done to the shared server):**

1. Approval for one controlled experiment: trim `mysqld`'s working set with the standard Windows call (`EmptyWorkingSet`, which only makes Windows page memory back in) and time the
   next connection. It touches the process that also serves the live database, momentarily and reversibly, which is why I am asking.
2. Or leave the machine idle for a long period and run the idle probe once more.

**Candidate mitigations, to be chosen only after the cause is confirmed** (none implemented): a longer timeout for connecting only (safe, since it does not limit queries);
one bounded retry on connect only; a warm-up connection at start-up so the first visitor does not pay. None of these changes what the 503 page says or leaks.

## 6. Free hosting options for a Flask + MySQL 8 site (assessment only)

What this site needs from a host: Python 3.11 or newer; **MySQL 8.0 specifically** (23 uses of the `utf8mb4_0900_ai_ci` collation, which MariaDB does not have, so MariaDB-based
hosts, including most cheap shared hosting, are out), CHECK constraints, `FIELD()`, `ON DUPLICATE KEY`; a production WSGI server (not yet in `requirements.txt`); HTTPS;
environment variables (`FLASK_ENV=production`, `SECRET_KEY`, `TV_PUBLIC_ORIGINS`, `TV_TRUSTED_PROXIES`); a database of well under 100 MB. The cinematic loops are not in the repository,
so no persistent disk is needed.

Sources are the providers' own pages where I could read them (PythonAnywhere help, Aiven documentation, TiDB documentation); the Render and Oracle details come from search
summaries and Render's own articles, and the Oracle terms conflict between sources, so those are marked unconfirmed. Free tiers change often: confirm on the day.

| Option | Fit | Findings |
|--------|-----|----------|
| **Render (free web service) + Aiven (free MySQL)** | **Best free combination** | Render: free web services sleep after 15 minutes idle and take up to about a minute to wake, 750 instance-hours a month, no persistent disk, no card needed; its free databases are PostgreSQL only (expiring after 30 days), so MySQL must come from elsewhere. Aiven free MySQL: 1 node, 1 CPU, 1 GB RAM, 1 GB disk, `max_connections` 76, no time limit, but it may be **powered off after inactivity** (with notice; you power it back on), no static IP, "for learning and prototyping". The first request after a sleep pays for both a wake-up and a fresh TLS database handshake, which makes the cold-start item above relevant. Needs the TLS option (S4). |
| **Oracle Cloud Always Free VM** (own MySQL 8 on the VM) | Best fidelity, most work | Same MySQL 8.0 as development, full control, no sleep. But: card at sign-up; the free capacity and idle-reclaim rules are described differently by different sources (unconfirmed); you run the OS, patches, backups, TLS certificates and MySQL yourself. |
| TiDB Cloud Starter (MySQL-compatible) | Possible, unproven | Free quota 5 GiB storage and 50 million request units a month, no card; TLS required; metered (a quota overrun denies new connections). It is MySQL-compatible, not MySQL: the collation, `FIELD()`, foreign-key behaviour and migrations would need a compatibility test run first. |
| PythonAnywhere free | **Not viable** | Free accounts created after 15 Jan 2026 have no MySQL; one web app that expires after one month; 512 MiB disk; outbound access limited to an allow-list (would block an external database). |
| Fly.io, Railway | Not free | Sources agree these no longer have a real free tier for new accounts (trial or credit based). |
| Koyeb | Unclear | Sources conflict about a free compute tier; not recommended without checking the live page. |

**Recommendation (for your decision, nothing deployed):** for a demonstration, Render + Aiven, with the limits accepted openly (a first visit after idle is slow, and the
Aiven service must be switched on again if it powers off). For maximum fidelity, an Oracle VM. Either way the code needs the small preparation in S4 first.

## 7. Proposed Stage 5 implementation plan

Branch `feature/stage5-delivery` (from `8ed0a61`), small commits, tests per milestone, one full-suite and one full browser run at the end.

| Milestone | Content | Approval needed? |
|-----------|---------|------------------|
| **5.1 Security fix (M1)** | Treat only POST as a submission in the 9 views; make the CSRF check cover every method that is not GET, HEAD or OPTIONS; HEAD then returns exactly what GET does with no side effect and no throttle use. Regression tests that cover **every route x every method including HEAD, OPTIONS, PUT, PATCH, DELETE and TRACE** (no state change, never 5xx), and that five `HEAD /login` calls leave the throttle untouched. Re-run the authz suites and the admin journey. | No (a fix inside the approved design). |
| **5.2 Test tooling (M2, S5)** | Update the 403 expectation in `admin_qa.mjs`; run the admin journey normal and reduced-motion; mark the 14-minute test `slow` and document how to run everything. | No. |
| **5.3 Documentation (M3)** | Fix the four verified drifts; add Stages 3 to 5 to `VERIFICATION.md` (with a test that its stated totals are not left stale if feasible); a doc-sync test for the `ROUTES.md` Planned table against the URL map. | No. |
| **5.4 Hardening (S3, O1, O6)** | HSTS under the production config over HTTPS; `robots.txt` (disallow `/search`, `/api/`, `/admin`; the favicon is already there, see O1); `Allow` header on 405. | No to HSTS/robots; say if you want O1/O6 left out. |
| **5.5 Database layer (S1, S2)** | Bounded wait for a pooled connection; for the cold start, only after the experiment in section 5 confirms the cause. | **Yes: it changes `app/db.py` behaviour, which you asked me to keep separate.** |
| **5.6 Deployment preparation (S4)** | A `requirements-prod.txt` with a WSGI server, optional `DB_SSL_CA`/TLS settings, a process file and a one-page deployment guide for the chosen host. No deployment, no database migration. | **Yes: new configuration surface, and the host choice.** |
| **5.7 Final verification** | Full suite once, full browser QA, the 140-measurement responsive sweep, the journeys, and a report with exact totals and any flakes with rerun evidence. | No. |

Approvals I am asking for: (1) go ahead with 5.1 to 5.4 and 5.7; (2) yes or no on 5.5, and which cold-start experiment (section 5) you allow; (3) yes or no on 5.6 and which host;
(4) your intended merge order for the stack (my suggestion: Stage 3 stack to `main` in one reviewed pull request after Stage 5, not one by one, because 3, 4A, 4B and 5 are a single linear history).
