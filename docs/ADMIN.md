# Admin area: Stories (Stage 3, Milestone 1)

An administrator can create, read, update and delete **Stories** (the `missions` table) and choose the characters, vehicles and places each one links to. This is the
first part of the roadmap's Phase 3 (admin and content management). It is built and tested on the **test database only**; enabling it on the live site is a separate,
later decision (see "Not done" below).

## Who may use it

* Routes live under `/admin` and every one carries `@security.admin_required` (`app/security.py`). A signed-out visitor is sent to `/login` (303). A signed-in user who is
  not an administrator gets **403**. Only `users.role = 'admin'` passes.
* The role is read from the database on **every request** (`load_user`), so taking the role away applies to the very next request, with no session to clear.
* Every admin POST needs the CSRF token and a matching `Origin` (the same global check as the account forms). Admin pages are sent with `Cache-Control: no-store`.
* `tests/test_admin_authz.py` walks the URL map and fails if any `admin.*` route lacks the check, so a route added later cannot be forgotten. Signed-out visitors, ordinary
  accounts and administrators are tried on every route and method; the ordinary-account case also proves the database is unchanged.
* The only way to become an administrator is the bootstrap tool below. Sign-up always creates `user`, and a forged `role=admin` field is ignored (tested).

## First administrator (test database only)

```
python -m scripts.make_admin --test <username> --plan        # read-only: the target and the account's current role
python -m scripts.make_admin --test <username>               # promote, after you type the username to confirm
python -m scripts.make_admin --test <username> --revoke      # back to an ordinary user
```

The tool **fails closed**: `--test` is required and it only ever works on the `*_test` database. Without `--test`, with a testing configuration that does not name a `*_test`
database, or with an invalid username, it refuses **before opening any connection**; after connecting it checks that the server reports a `*_test` database before it reads
anything. `--yes` only skips the typed confirmation: it can never change the target. It uses the migration account, changes one row with one statement, and never reads or
prints a password hash. `tests/test_make_admin.py` proves the refusals by forbidding the connect call. Making an administrator on the live site is a separate, approved
procedure that this tool deliberately does not perform.

## Routes

| Route | Purpose |
|---|---|
| `GET /admin` | Dashboard: rows per table, stories by label and type, accounts by role, favourites per kind, most saved stories, stories with no links (aggregate SQL: `GROUP BY`, `UNION ALL`, `JOIN` + `ORDER BY ... LIMIT`, `NOT EXISTS`) |
| `GET /admin/stories` | List with `q`, `type`, `status`, `sort`, `page`, `per_page` (the same service as the public Stories page, every label shown) |
| `GET`/`POST /admin/stories/new` | Create |
| `GET`/`POST /admin/stories/<slug>/edit` | Update, including the links |
| `GET /admin/stories/<slug>/delete` | Confirmation page with the impact counts (link rows per kind and users' favourites of the story) |
| `POST /admin/stories/<slug>/delete` | Delete (a GET never deletes) |

All changes answer `303` back to the list (filtered to the story's title), so a refresh never repeats them. An administrator sees an **Admin** link on their favourites page; nobody else does.

## What can be edited, and what cannot

* **Fields:** title (3 to 120, unique), slug (set when the story is created, **read-only afterwards**), type, label (`fan` or `demo` only), summary (up to 255), synopsis
  (up to 3000), optional https source address and source note (up to 500 each).
* **Links:** characters (a role note, up to 80), vehicles (a use note, up to 160) and places (with one optional main place chosen from a labelled list of the ticked places), as plain checkboxes, text fields and one list: no JavaScript.
  The form posts slugs; the server turns them into ids. Updating replaces all the links of the story in one transaction.
* **Official content is read-only, at every level.** A story whose label is `official` (Rockstar-sourced; the table's `CHECK` requires a source address) is never created,
  changed, relinked or deleted here:
  1. the form offers only `fan` and `demo`, and a posted `official` is refused (400);
  2. the service refuses to load an official story for editing or deleting (403);
  3. the repository refuses it too, **even when called directly**: it locks the row, raises `NotEditable`, and refuses to write a status outside `fan`/`demo`;
  4. every individual `UPDATE`, `DELETE` and link `INSERT` repeats the writable condition in SQL, so the story stays unchanged even if the lock check were bypassed (tested by bypassing it);
  5. the database's own `CHECK` still stands.

  Linking a story to an official character, vehicle or place is allowed: the link row belongs to the story. The official records themselves are never written.

## Transactions

Every write is one `transaction()` (commit on success, roll back on any error) and goes through `app/repositories/admin_stories.py`.

* **Create:** insert the story, then its links, then commit.
* **Update:** lock the story row (`SELECT ... FOR UPDATE`), refuse it if not writable, update the fields, delete the old links, insert the new ones, commit.
* **Delete:** lock, refuse if not writable, delete the story; the link rows and users' favourites of it go with it (`ON DELETE CASCADE`).
* A taken title or slug (error 1062) becomes a field error (409); a character, vehicle or place removed after the form was drawn (1216 or 1452) becomes a clear 409. Both roll back
  everything, including links already deleted in the same update.
* Two administrators editing the same story: the last save wins. There is no "updated at" column, and adding one would need a migration, so it is not part of this milestone.
* `tests/test_admin_transactions.py` lets a real step run and then fails the next one (after the story insert, after the link delete, halfway through the link inserts, just before
  the commit) and compares before and after snapshots. It also proves the connection returns to a pool of one.
* `tests/test_db_transactions.py` still enforces that the application writes only inside `transaction()`. The admin repository is a deliberate third writer: it is held to an
  AST rule (every `cursor.execute` is inside a `with transaction() as cursor:` block, or in a helper that is only called from inside one), and the account repositories keep the
  original rule unchanged.

## Request size

The global 16 KiB request limit is **not** changed. The largest realistic story form (every one of the 11 characters, 15 vehicles and 8 places ticked, every note at its maximum,
a 3000-character synopsis with typographic punctuation) measures **about 13.5 KB** as a browser sends it (plain ASCII: 10.8 KB). That is why the synopsis is limited to 3000
characters. `tests/test_admin_validation.py` posts that form and expects it to be accepted, and posts an oversized body and expects `413`. Text in a non-Latin script is several
times larger once encoded (a CJK synopsis of 3000 characters would be about 67 KB), so such a form gets the normal `413` page; that is accepted for this English fan site.

## Audit

Every change writes one log line at INFO, for example `Admin 7 updated story the-quiet-water`: the user id, the action and the slug. No names, text or secrets. There is no audit
table (that would need a new migration, which this milestone does not need).

## Tests and how to run them (test database only)

```
.venv\Scripts\python.exe -m pytest tests/test_admin_authz.py tests/test_admin_stories_crud.py tests/test_admin_transactions.py tests/test_admin_validation.py tests/test_admin_official_protection.py tests/test_admin_stats.py tests/test_make_admin.py tests/test_db_transactions.py -q
.venv\Scripts\python.exe scripts\qa\run_admin_qa.py 5084            # browser QA: starts a TEST-configured server, proves the database is a *_test one first
```

Everything uses `TestingConfig` (`gta6_vi_test`): the fixtures and the helpers in `tests/account_helpers.py` prove the database name, the tests create their own stories (slug prefix `tt-`)
and remove them, and the seeded stories are never changed. To look at the pages in a browser, run a server with the testing configuration only
(`flask --app "app:create_app('testing')" run --port 5090`); a development-configuration server points at the real database.

## Not done (separate decisions)

* Enabling the admin area on the live site, and creating a first administrator there. Neither needs a schema change, but the live deployment still depends on migration 010 (accounts)
  and on knowing which earlier migrations the live database has.
* Editing characters, vehicles, places or media; relationship editors for characters; an audit table; optimistic locking.
