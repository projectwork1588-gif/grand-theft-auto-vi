# Accounts and favourites

Visitors can browse the whole site without an account. An account (a username and a password; no email, no verification) lets a visitor **save** characters, vehicles, places and stories, see them on one page, and change the password.

## What it does

| Workflow | Route | Notes |
|---|---|---|
| Register | `GET/POST /register` | username + password + confirmation. 400 invalid, 409 username taken. Signs in on success |
| Sign in | `GET/POST /login` | username + password. One generic message (401) for a wrong password **and** an unknown username. 429 after too many failures |
| Sign out | `POST /logout` | POST only, CSRF-protected |
| Your favourites | `GET /account/favourites` | the four kinds, newest first, with a Remove button each. Needs sign-in |
| Change password | `GET/POST /account/password` | the **current password is verified first** (this is the UPDATE in the CRUD set). Needs sign-in |
| Save | `POST /favourites/<kind>/<slug>` | `kind` is `characters`, `vehicles`, `locations` or `missions`. Saving twice is harmless |
| Remove | `POST /favourites/<kind>/<slug>/remove` | HTML forms only send GET and POST, so removal is a POST sub-path |

The Save / Saved button is on the four detail pages (`/characters/<slug>`, `/vehicles/<slug>`, `/locations/<slug>`, `/missions/<slug>`). A signed-out visitor sees "Sign in to save" instead (no form, no cookie). The menu has an Account block (Sign in / Create an account, or Your favourites / Change password / Sign out) and the footer has one link. Everything works with plain forms and no JavaScript.

After a POST the server answers `303 See Other` to a page it chooses itself (the record's own page, or the favourites list when the button was pressed there). No route accepts a user id, a role or a redirect address from the request.

## CRUD and DBMS map

| Operation | Where | SQL |
|---|---|---|
| **Create** | register; save a favourite | `INSERT INTO users (username, password_hash)`; `INSERT INTO favourite_<kind> ... ON DUPLICATE KEY UPDATE user_id = user_id` |
| **Read** | sign in; the favourites page; the Save/Saved state | `SELECT ... FROM users WHERE username = %s`; `SELECT ... FROM favourite_<kind> f JOIN <entity> e ... WHERE f.user_id = %s` |
| **Update** | change password | `UPDATE users SET password_hash = %s WHERE user_id = %s` |
| **Delete** | remove a favourite | `DELETE FROM favourite_<kind> WHERE user_id = %s AND <id> = %s` |

So the site now has all four CRUD operations on real tables. (Deleting an account is **not** a feature; the cascade that would follow one is covered by tests.)

* **Keys and relations:** `users` 1 : N each `favourite_*` table; each favourite table is the M : N join between `users` and one entity table, with the composite primary key `(user_id, <entity>_id)` (a duplicate pair is impossible) and two foreign keys with `ON DELETE CASCADE ON UPDATE CASCADE`.
* **Uniqueness:** `uq_users_username`. The column's collation (`utf8mb4_0900_ai_ci`) is case- and accent-insensitive, so `Jason` and `jason` collide. The application also stores usernames in lower case. A taken username is detected from the index (MySQL error 1062), not by a check-then-insert, so two simultaneous sign-ups cannot both succeed.
* **Transactions:** every write goes through `app.db.transaction()` (start, commit, roll back on any error). The connection is not in autocommit mode, so a write outside it would be discarded when the connection returns to the pool. Each write here is one statement, so the transaction is the commit boundary and the rollback guard; the multi-row atomicity in this feature comes from InnoDB itself (for example a cascade).
* **Visibility:** only records the public pages show can be saved or listed (official characters and vehicles; all places and stories). The same rule is applied in SQL when listing.
* **Dynamic SQL:** the table and column names in `repositories/favourites.py` come from the fixed `KINDS` map, never from the request. Every value is a `%s` placeholder.

## Security design

| Concern | What is done | Where |
|---|---|---|
| Password storage | Werkzeug **scrypt** (`scrypt:32768:8:1`, random salt per password). Never stored or logged in plain text. The stored value is about 160 characters in `VARCHAR(255)` | `services/accounts.py` |
| Password rules | 10 to 128 characters, no NUL, not equal to the username. The maximum stops huge inputs being used to burn server time | `services/accounts.py` |
| Username | trimmed, lower-cased, `^[a-z0-9_]{3,30}$` | `services/accounts.py` |
| Sign-in errors | one message for a wrong password and an unknown username; an unknown username still costs one hash check, so timing does not reveal which names exist | `authenticate()` |
| Sessions | Flask's signed cookie `tv_session`: `HttpOnly`, `SameSite=Lax`, `Secure` in production, **8 hours at most** (checked on the cookie and again from the sign-in time). It holds the user id, the sign-in time, a password stamp and the CSRF token | `config.py`, `security.py` |
| Fixation | a successful sign-in or password change starts a **new** session (the old one, with its CSRF token, is discarded) | `security.sign_in` |
| Sign out | clears the session. See the limitation below | `security.sign_out` |
| Password change | the password stamp (an HMAC of the stored hash with the secret key) is kept in the session, so **changing the password signs every other browser out** | `security.password_stamp` |
| CSRF | synchronizer token: random per session, in a hidden field of every form (or an `X-CSRF-Token` header), compared in constant time on **every** POST/PUT/PATCH/DELETE, including register and sign in; a cross-site `Origin` is refused too; `SameSite=Lax` is the second layer. 400 on failure | `security.protect_csrf` |
| Authorization | the user is `g.user`, loaded from the session; every favourite statement names that user. A forged `user_id` field is ignored | `blueprints/account.py`, `repositories/favourites.py` |
| Production secret | `get_config("production")` refuses to start unless `SECRET_KEY` is set, is at least 32 characters and is not a known development or placeholder value. Without `SECRET_KEY`, development and tests use a random key per process, so no well-known key exists | `config.check_secret_key` |
| Caching | account pages send `Cache-Control: no-store`; other pages for a signed-in visitor send `private`; anonymous browsing never sets a cookie | `security.add_cache_headers` |
| Output | Jinja autoescaping; the CSP is unchanged (no inline script or style, `form-action 'self'`) | templates |

### Throttles (login, change-password, sign-up)

`security.Throttle` counts events in a sliding window held **in memory**.

| Counter | Key | Limit | Window |
|---|---|---|---|
| Failed sign-ins | `user:<address>:<username>` | 5 (`LOGIN_MAX_FAILURES`) | 10 min (`LOGIN_WINDOW_SECONDS`) |
| Failed sign-ins, whole address | `addr:<address>` | 20 (`LOGIN_MAX_FAILURES_PER_ADDRESS`) | 10 min |
| Wrong "current password" on the change-password form | the same two keys | as above | as above |
| Accounts created (a success or a "taken" answer; invalid forms cost nothing and are not counted) | `reg:<address>` | 10 (`REGISTER_MAX_PER_WINDOW`) | 1 hour (`REGISTER_WINDOW_SECONDS`) |

The next attempt past a limit answers `429` with `Retry-After`, even with the right password. A success clears that username's sign-in count.

How the table stays bounded (Phase 2C; the earlier version emptied the whole table when it filled up, which an attacker could use to reset their own counters):

* **Keys cannot be chosen by an attacker.** The username in a key is trimmed, lower-cased and must match `^[a-z0-9_]{3,30}$`; anything else (any length, any characters) shares one `*invalid*` bucket per address. The address is cut to 64 characters. Since one address is blocked after 20 failures, it can create at most about 22 keys per window.
* **Expiry.** A key is forgotten when all its events have left its window. Each key remembers its own window (minutes for sign-ins, an hour for sign-ups).
* **Caps.** At most 100 events per key and 10 000 keys in the table. At the cap, expired keys go first; if it is still full, the 1 % of keys with the **fewest** events (oldest first) are evicted. Counters are never cleared wholesale, so a key that reached its limit stays blocked while others are flooded.
* **Request size.** Every form is tiny, so a body over 16 KiB (`MAX_CONTENT_LENGTH`) is refused with `413` before it is read.

Limits, stated plainly:

* The table is **per process**. With several worker processes (or after a restart) each has its own counts, so the real limit is higher (about `N x`). It does **not** coordinate multiple workers. A shared store (Redis, or a table) would be needed for that.
* A flood from more than 10 000 distinct addresses in one window could still evict real counters, starting with those that have the fewest events. A distributed attack is not stopped by an in-process counter.
* The address is `request.remote_addr`. Forwarded headers are **not** read unless you set `TV_TRUSTED_PROXIES` (next section); behind a proxy without it, every visitor looks like the proxy and shares one allowance.
* It slows guessing and bulk sign-up; it is not a substitute for strong passwords, and a shared address (a college network behind one NAT) shares one allowance.

### Hosts, origins and proxies (CSRF and the client address)

Every POST must carry the CSRF token **and**, if the browser sends an `Origin` header, that origin must be allowed:

* `TV_PUBLIC_ORIGINS` (comma-separated, `scheme://host[:port]`, for example `https://valkyrie.example.org`): when set, **only** these origins may submit forms. The request's `Host` header is not consulted, so a forged Host cannot make another origin acceptable. **Required in production, and https only.** Scheme, host and port must all match; `null` never matches.
* Not set (development, tests): the request's own `scheme://host` is the reference.
* No `Origin` header: the token alone decides.
* `TV_TRUSTED_PROXIES` (default `0`): how many reverse proxies sit in front. Only when it is greater than 0 is Werkzeug `ProxyFix` enabled, reading `X-Forwarded-For` and `X-Forwarded-Proto` from the right-hand end of the list; `X-Forwarded-Host`, `-Port` and `-Prefix` are never read. The proxy must **overwrite** (not append to) any `X-Forwarded-*` header a client sent, and the number must be exactly the number of proxies you control. A wrong number lets clients choose their own address, which defeats the throttles.

### Production settings

`get_config("production")` (used by `create_app()` when `FLASK_ENV=production`) refuses to start, with a message that never contains the value, unless:

* `SECRET_KEY` is set, at least 32 characters, at least 10 distinct characters, and not a known placeholder (the example value in `.env.example` is rejected). Generate one with `python -c "import secrets; print(secrets.token_hex(32))"` (256 random bits from the operating system) and keep it out of Git. Changing it signs everyone out. Use the same value in every worker.
* `TV_PUBLIC_ORIGINS` is set and every entry is https.
* `DB_NAME` does not end in `_test` and is not the test database.
* `TV_TRUSTED_PROXIES` is between 0 and 5.

There is no quiet fall-back to development: `FLASK_ENV` must be `development`, `production` or `testing`. A typo (`prod`) or an empty value stops the site from starting. **Not set at all means development** (so a local run needs no setup); a deployment must therefore set `FLASK_ENV=production`, and the log line `Starting with ProductionConfig` confirms it. Production also marks the cookie `Secure`, so it needs HTTPS: over plain http the browser drops the cookie and sign-in appears broken.

### Transaction ownership (`app/db.py`)

* **Reads** use `query_all` / `query_one`. They refuse any statement that starts with a write verb (`INSERT`, `UPDATE`, `DELETE`, `SET`, `COMMIT`, ...), so a read can never leave an uncommitted write behind. The connection is not in autocommit mode, so a read opens an implicit read snapshot.
* **Writes** use `transaction()` only, which owns the unit of work: it commits on success and rolls back on any error.
* `transaction()` **cannot nest**: a second call inside the first raises `TransactionError` before touching the connection, so the outer block's work is neither committed early nor discarded. The outer block may catch the error and go on.
* Before starting, it ends the read snapshot left by earlier reads (the connector would otherwise refuse with "Transaction already in progress"). That is safe because the read helpers cannot hold a write.
* `get_db()` (the raw connection) is for tests and diagnostics. If it was used in the request and a transaction is open afterwards, `transaction()` cannot know what the transaction holds, so it raises `TransactionError` instead of rolling it back. Commit or roll back first.
* `tests/test_db_transactions.py` checks all of this, and scans `app/` to show that only `db.py` touches the raw connection and every `cursor.execute` outside it sits directly under `with transaction() as cursor:`.

## Known limitations

* **Sign out clears the browser's cookie but cannot revoke a stolen copy of it.** Sessions are stateless signed cookies (no sessions table, by decision). A copy stays valid until the 8 hours pass or the password is changed (which invalidates it, see above).
* No email, so **no password reset**: a forgotten password cannot be recovered. No account deletion feature and no admin screens. The `role` column exists; registration always creates `user`, and nothing reads it.
* Sign-up is limited per client address (above), not per person: an attacker with many addresses can still create many accounts. No CAPTCHA, no email check.
* The database account the site uses keeps `SELECT, INSERT, UPDATE, DELETE` on the whole database (unchanged). A narrower, per-table grant is possible; see "Least privilege" below.

## Least privilege (recommendation, not applied)

The features need only: `SELECT` everywhere; `INSERT` and `UPDATE (password_hash)` on `users`; `INSERT` and `DELETE` on the four `favourite_*` tables. A DBA could grant exactly that instead of database-wide DML. `tests/test_privileges.py` pins the present grants, so it would be updated together with such a change. Not applied here.

## Migration 010

`database/migrations/010_account_email_optional.sql`: `ALTER TABLE users MODIFY email VARCHAR(254) NULL;`. The column and its UNIQUE index stay (MySQL allows many NULLs under UNIQUE; any email that is stored must still be different). Non-destructive and safe to run twice. `database/schema.sql` carries the same definition for new databases.

**Test database** (what the tests do): `python -m scripts.migrate_db --test --only 010_account_email_optional.sql --plan`, then without `--plan` (add `--yes` to skip the prompt on a `*_test` database).

**Production rollout (separate approval, not done):**

1. Back up the database `gta6_vi` (for example `mysqldump --single-transaction gta6_vi > backup.sql`, kept outside the repository).
2. `python -m scripts.migrate_db --only 010_account_email_optional.sql --plan` and read the output (it must list one `ALTER TABLE users MODIFY email`).
3. `python -m scripts.migrate_db --only 010_account_email_optional.sql`, type `YES`. **Never run `python -m scripts.migrate_db` without `--only` on `gta6_vi`**: there is no migration history, so it would run all ten files again (see Migration safety).
4. Check: `SELECT is_nullable FROM information_schema.columns WHERE table_schema = 'gta6_vi' AND table_name = 'users' AND column_name = 'email';` returns `YES`.
5. Set in the production environment: `FLASK_ENV=production`, a real `SECRET_KEY` (generate with `python -c "import secrets; print(secrets.token_hex(32))"`), `TV_PUBLIC_ORIGINS=https://<your public host>` and `TV_TRUSTED_PROXIES=<number of proxies in front, or 0>`; serve over HTTPS (the session cookie is `Secure` there). The site will not start if any of the first three is missing or wrong.
6. Deploy the code, then one sign-up / save / sign-out check with a throwaway account that is deleted afterwards.

## Migration safety

* `--only <file>` selects **exactly one** file: the name must match a file in `database/migrations/` exactly (no path, no pattern, no abbreviation, no empty string), and the plan lists only that file. `--only 010_account_email_optional.sql --plan` runs the read-only prerequisite checks first.
* **Without `--only`, every migration runs again.** There is no migration history, so nothing is "pending": all files are re-run in order. They are written to be repeatable, but a repeat still takes locks and re-writes the rows each file owns. The all-files run therefore prints a warning and needs the longer phrase `YES ALL` (a targeted run needs `YES`; one phrase does not confirm the other). `--yes` only skips the prompt on a `*_test` database.
* `scripts/migration_checks.py` now checks 010 before it is applied: `users` exists; `users.email` exists and is exactly `varchar(254)` (any other type would make the ALTER change the type too, so that blocks it); it reports whether the column is already nullable, that the unique index `uq_users_email` stays, and how many accounts exist (a count only). After applying, it reads the result back on a new connection.
* **Rollback of 010:** the migration is a relaxation. Once any account has no email (every account created by the sign-up form), `MODIFY email ... NOT NULL` fails; undoing 010 then needs a decision about those accounts. Take a backup before applying it to a real database.
* Tests apply 010 only to the `*_test` database, with the runner's `--test` flag; the production database is changed only by a separately approved rollout.

## Tests

`tests/test_accounts.py`, `tests/test_favourites.py`, `tests/test_account_security.py`, `tests/test_account_migration.py` and, from Phase 2C, `tests/test_throttle_hardening.py`, `tests/test_db_transactions.py`, `tests/test_deployment_config.py` (with `tests/account_helpers.py`). They commit real rows to the **`*_test`** database, so every database touch first proves the name ends in `_test` (`tests/account_helpers.test_connection`, the `clean_accounts` fixture) and removes only the `tt_*` accounts it made. `scripts/qa/run_accounts_qa.py` does the same before the browser check (`scripts/qa/accounts_qa.mjs`) and starts its own server with the testing configuration on a separate port.
