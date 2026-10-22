# Database design

MySQL 8.x, InnoDB, `utf8mb4`. Source of truth: [`database/schema.sql`](../database/schema.sql) and
[`database/seed.sql`](../database/seed.sql). The ER diagram is below (Mermaid renders on GitHub and in VS Code with a Mermaid extension).

## ER diagram

```mermaid
erDiagram
    REGIONS ||--o{ LOCATIONS : "contains"
    LOCATIONS |o--o{ CHARACTERS : "home of"
    CHARACTERS ||--o{ CHARACTER_RELATIONSHIPS : "from"
    CHARACTERS ||--o{ CHARACTER_RELATIONSHIPS : "to"
    CHARACTERS ||--o{ CHARACTER_REGIONS : "placed in"
    REGIONS ||--o{ CHARACTER_REGIONS : "places"
    VEHICLE_CATEGORIES ||--o{ VEHICLES : "groups"
    MISSIONS ||--o{ MISSION_CHARACTERS : "features"
    CHARACTERS ||--o{ MISSION_CHARACTERS : "appears in"
    MISSIONS ||--o{ MISSION_VEHICLES : "uses"
    VEHICLES ||--o{ MISSION_VEHICLES : "used in"
    MISSIONS ||--o{ MISSION_LOCATIONS : "takes place at"
    LOCATIONS ||--o{ MISSION_LOCATIONS : "hosts"
    USERS ||--o{ FAVOURITE_CHARACTERS : "saves"
    CHARACTERS ||--o{ FAVOURITE_CHARACTERS : "saved as"
    USERS ||--o{ FAVOURITE_VEHICLES : "saves"
    VEHICLES ||--o{ FAVOURITE_VEHICLES : "saved as"
    USERS ||--o{ FAVOURITE_MISSIONS : "saves"
    MISSIONS ||--o{ FAVOURITE_MISSIONS : "saved as"
    USERS ||--o{ FAVOURITE_LOCATIONS : "saves"
    LOCATIONS ||--o{ FAVOURITE_LOCATIONS : "saved as"
    MEDIA_ASSETS ||--o{ MEDIA_CHARACTERS : "shows"
    CHARACTERS ||--o{ MEDIA_CHARACTERS : "shown in"
    MEDIA_ASSETS ||--o{ MEDIA_LOCATIONS : "shows"
    LOCATIONS ||--o{ MEDIA_LOCATIONS : "shown in"
    MEDIA_ASSETS ||--o{ MEDIA_VEHICLES : "shows"
    VEHICLES ||--o{ MEDIA_VEHICLES : "shown in"
    MEDIA_ASSETS ||--o{ MEDIA_REGIONS : "shows"
    REGIONS ||--o{ MEDIA_REGIONS : "shown in"

    USERS { int user_id PK
            varchar username UK
            varchar email UK
            varchar password_hash
            enum role }
    REGIONS { smallint region_id PK
              varchar slug UK
              varchar name UK
              enum content_status
              varchar source_url }
    LOCATIONS { int location_id PK
                smallint region_id FK
                varchar slug UK
                varchar name
                enum location_type
                enum content_status }
    CHARACTERS { int character_id PK
                 varchar slug UK
                 varchar full_name
                 int home_location_id FK
                 enum content_status
                 varchar source_url }
    CHARACTER_RELATIONSHIPS { int from_character_id PK_FK
                              int to_character_id PK_FK
                              enum relationship_type }
    CHARACTER_REGIONS { int character_id PK_FK
                        smallint region_id PK_FK
                        varchar note
                        varchar source_url }
    VEHICLE_CATEGORIES { tinyint category_id PK
                         varchar slug UK
                         varchar name UK }
    VEHICLES { int vehicle_id PK
               tinyint category_id FK
               varchar slug UK
               varchar name UK
               enum content_status }
    MISSIONS { int mission_id PK
               varchar slug UK
               varchar title UK
               enum mission_type
               enum content_status }
    MISSION_CHARACTERS { int mission_id PK_FK
                         int character_id PK_FK
                         varchar role_in_mission }
    MISSION_VEHICLES { int mission_id PK_FK
                       int vehicle_id PK_FK
                       varchar usage_note }
    MISSION_LOCATIONS { int mission_id PK_FK
                        int location_id PK_FK
                        boolean is_primary }
    FAVOURITE_CHARACTERS { int user_id PK_FK
                           int character_id PK_FK }
    FAVOURITE_VEHICLES { int user_id PK_FK
                         int vehicle_id PK_FK }
    FAVOURITE_MISSIONS { int user_id PK_FK
                         int mission_id PK_FK }
    FAVOURITE_LOCATIONS { int user_id PK_FK
                          int location_id PK_FK }
    MEDIA_ASSETS { int media_id PK
                   varchar slug UK
                   enum media_type
                   enum usage_status
                   enum approval_status }
    MEDIA_CHARACTERS { int media_id PK_FK
                       int character_id PK_FK }
    MEDIA_LOCATIONS { int media_id PK_FK
                      int location_id PK_FK }
    MEDIA_REGIONS { int media_id PK_FK
                    smallint region_id PK_FK }
    MEDIA_VEHICLES { int media_id PK_FK
                     int vehicle_id PK_FK }
```

## Tables and why each exists (21)

| # | Table | Why it exists | Key points |
|---|-------|---------------|-----------|
| 1 | `users` | Accounts (username + password) for saving favourites; see `docs/ACCOUNTS.md`. | PK `user_id`. `username` UNIQUE. `email` UNIQUE and **nullable** (migration 010: sign-up asks for no email). `role` is `user` or `admin` (sign-up always creates `user`). Stores only a password **hash** (Werkzeug scrypt). |
| 2 | `regions` | Large areas of Leonida. | UNIQUE `slug`, `name`. |
| 3 | `locations` | Places inside a region. | FK `region_id` (RESTRICT). UNIQUE `(region_id, name)`. |
| 4 | `characters` | People in the world. | Optional FK `home_location_id` (ON DELETE SET NULL). |
| 5 | `character_relationships` | Many-to-many **between characters** (partner, ally, rival ...). | Composite PK `(from, to)`, `CHECK from <> to`, both FKs ON DELETE CASCADE. |
| 6 | `vehicle_categories` | Lookup table so a category name is stored once (3NF) and can be grouped/counted. | UNIQUE `slug`, `name`. |
| 7 | `vehicles` | Vehicle catalogue. | FK `category_id` (RESTRICT). No performance stats, because none are confirmed. |
| 8 | `missions` | Mission and story records. | `mission_type` enum. |
| 9 | `mission_characters` | Many-to-many mission <-> character. | Composite PK, plus `role_in_mission` (data that belongs to the *pair*). |
| 10 | `mission_vehicles` | Many-to-many mission <-> vehicle. | Composite PK, plus `usage_note`. |
| 11 | `mission_locations` | Many-to-many mission <-> location. | Composite PK, plus `is_primary`. |
| 12-15 | `favourite_characters`, `favourite_vehicles`, `favourite_missions`, `favourite_locations` | A user's saved records. | Composite PK `(user_id, entity_id)` makes a duplicate favourite impossible. Both FKs CASCADE. |
| 16 | `media_assets` | Database half of the media inventory. Records where an asset lives and its permission state. Never contains copied Rockstar media. | `usage_status`, `approval_status`, `CHECK` that some location (link/embed/local path) exists. |
| 17 | `media_characters` | Many-to-many media <-> character. | Composite PK. |
| 18 | `media_locations` | Many-to-many media <-> location. | Composite PK. |
| 19 | `media_regions` | **Added in Phase 2.** Many-to-many media <-> region. Official region imagery belongs to regions. Linking it to the fictional demo locations would be misleading. | Composite PK, both FKs ON DELETE CASCADE. Created by `database/migrations/001_phase2_media.sql` and also part of `schema.sql`. |
| 20 | `media_vehicles` | **Added in the Phase 2 refinement.** Many-to-many media <-> vehicle. Official vehicle screenshots belong to the five vehicles Rockstar names. A concept vehicle never gets one (a test enforces it). | Composite PK, both FKs ON DELETE CASCADE. Created by `database/migrations/002_phase2_garage.sql` and also part of `schema.sql`. |
| 21 | `character_regions` | **Added in Gate 3A.** Many-to-many character <-> region, only where Rockstar's own text places a person in a region (three rows: Jason Duval and Brian Heder in the Leonida Keys, Boobie Ike in Vice City). Carries the `note` (what the source says) and its `source_url`. Official characters have no invented home place, so this is how a region filter works for them. | Composite PK, both FKs ON DELETE CASCADE, `source_url` NOT NULL. Created by `database/migrations/005_gate3a_cast.sql` and also part of `schema.sql`. |

### Decision: four favourite tables instead of one "polymorphic" table
A single `favourites(user_id, entity_type, entity_id)` table cannot have a real foreign key, so MySQL could not stop a
favourite pointing at a deleted or non-existent record. Four small tables keep full referential integrity,
and the SQL stays simple to explain.

### Decision: `content_status` on every core table
`official` (confirmed by Rockstar, **`source_url` required by a CHECK constraint**), `fan` (community interpretation)
or `demo` (fictional record by Team Valkyrie). This makes the "never mislead visitors" rule something the database
enforces, not just a convention.

## Relationship types demonstrated

* **One-to-many:** regions -> locations, vehicle_categories -> vehicles, locations -> characters (home).
* **Many-to-many:** characters <-> characters, missions <-> characters / vehicles / locations, users <-> each entity (favourites), media <-> characters / locations.
* **Composite primary keys:** 13 tables (`character_relationships`, `character_regions`, 3 mission junctions, 4 favourites, 4 media junctions).
* **Cascade rules:** deleting a character removes its junction rows (CASCADE) but only blanks `home_location_id` on
  characters when a location is deleted (SET NULL). Deleting a region or category that is still in use is **blocked** (RESTRICT).

## Normalization (3NF)

* Every table has a primary key and atomic columns (no comma-separated lists).
* Attributes depend on the whole key: `role_in_mission` depends on the *pair* (mission, character), so it lives on the junction table.
* No transitive dependencies: a vehicle stores `category_id`, not the category name and description. A location stores `region_id`, not the region name.
* Deliberate, documented trade-off: `source_url` / `source_note` repeat per row. They are facts about *that record's provenance*, not about a shared entity.

## Indexes

Primary and unique keys create indexes automatically. Additional ones: `ix_characters_full_name`
(sorting), `ix_characters_status`, `ix_missions_type`, `ix_media_assets_type`, and a reverse-lookup index on the second column of every junction
table (so "which missions feature this character?" does not scan the table). Foreign-key columns are always indexed.
Search currently uses `LIKE '%text%'`, which cannot use a normal index. That is acceptable at this data size and FULLTEXT is a Phase 4 option.

## Transactions

* `scripts/init_db.py` loads the seed inside one transaction (all-or-nothing).
* `app/db.py` provides `transaction()` for multi-table writes (admin relationship editing in Phase 3). `tests/test_db_connection.py` proves it commits on success and rolls back on error.

## Seed data honesty

| Entity | Seeded | Status |
|--------|--------|--------|
| Characters | Jason Duval, Lucia Caminos, Cal Hampton, Boobie Ike, Dre'Quan Priest, Raul Bautista, Brian Heder, Real Dimez (8) | `official`: all eight are listed on https://www.rockstargames.com/VI/only-in-leonida (checked 2026-10-09). Descriptions are our own short paraphrases |
| Characters | 3 fictional characters | `demo` |
| Regions | Vice City, Leonida Keys, Grassrivers, Port Gellhorn, Ambrosia, Mount Kalaga (6) | `official`: all six are listed on the same Rockstar page. We store only what it states |
| Locations, vehicles, missions | all | `demo` |
| Relationships | Jason-Lucia, Brian-Jason, Cal-Jason, Boobie Ike-Dre'Quan | `official` (stated on that page). The other three are `demo` |
| Vehicles | '95 Grotti Cheetah, '67 Vapid Dominator Buggy, Shitzu Squalo, Vapid Stanier, Vapid Ganado Retro Build (5), each with Rockstar's own screenshots | `official` (names from rockstargames.com/VI/editions and the screenshots page). No specifications are stored because Rockstar has published none |
| Vehicles | 8 concept vehicles used by the story archive | `demo` (shown as Concept, no public page) |
| Media | 107 rows: 3 official videos (Rockstar's own player), 1 link to the official Media page, 3 trailer posters, 8 character clip rows (each with a poster and, once built, a local loop path), 91 official images (artwork, region postcards, screenshots, vehicle screenshots) and 1 local reel row. 59 character, 36 region and 17 vehicle links. See `docs/MEDIA_INVENTORY.md` | Remote references only. `approved` for display by the Phase 2 media brief. Rockstar states no licence terms, so human review is recommended. Fictional records get no official media |

**Correction history:** the first Phase 1 seed marked five regions as `fan` and omitted Real Dimez because only secondary sources had been reachable. A direct check of Rockstar's Leonida page confirmed them, so they were reclassified.

Demo missions deliberately contain **only demo characters**, so the project never invents story for real GTA VI characters.

## Phase 2 migrations (non-destructive)

Phase 1 databases (including the owner's) lack `media_regions` and the official media rows. `database/migrations/001_phase2_media.sql`:

* `CREATE TABLE IF NOT EXISTS media_regions` (no drop),
* upserts `media_assets` rows with fixed ids (`INSERT ... AS new ON DUPLICATE KEY UPDATE`),
* adds links with `INSERT IGNORE`.

It contains no `DROP`, `DELETE` or `TRUNCATE`, and `scripts.migrate_db` refuses to run a file that does. Run `python -m scripts.migrate_db --plan` first (read-only). Tests prove it is idempotent, that it changes no content table, and that an upgraded database equals a freshly seeded one.
Until it is applied the website still works: media lookups tolerate the missing table and pages show original fallbacks.

**Migration 002 (`002_phase2_garage.sql`)** creates `media_vehicles`, upserts the five official vehicles (ids 9 to 13, source-linked to Rockstar's pages), and adds 28 media rows: three trailer posters, eight character clip cards (poster image plus a link to Rockstar's Videos page) and 17 vehicle screenshots.

**Migration 003 (`003_concept_copy.sql`)** contains only `UPDATE` statements that rewrite the text of concept characters, locations, stories, vehicles and relationships so it reads naturally, with a `WHERE content_status = 'demo'` guard on every statement. A test restores the old wording, applies the migration and proves that no official row changed and that the result equals a fresh seed.

**Migration 004 (`004_leonida_in_motion.sql`)** adds 21 official screenshots (ids 86 to 106) and their region and character links, sets `local_path` on the eight clip rows (`clips/<slug>.mp4`, a relative path into the Git-ignored `media/` folder), adds the reel row (id 107, `permission_required` / `pending_review`) and rewrites the editorial text of the official characters, regions and vehicles. It never changes a name, slug, label or source link. Every statement is an upsert or an `UPDATE`; there is no `DROP`, `DELETE` or `TRUNCATE`.

**Migration 005 (`005_gate3a_cast.sql`)** (Gate 3A, Characters) is additive only. It runs `CREATE TABLE IF NOT EXISTS character_regions`, then two `INSERT ... WHERE NOT EXISTS` statements: the three region placements Rockstar's text supports, and the one relationship between Dre'Quan Priest and Real Dimez (`associate`, official, sourced: Rockstar's page says he signed Real Dimez to Only Raw Records). No existing row is changed, no character is removed. The public pages and the API default to official characters; the three original characters stay in `characters` for the stories and the DBMS demonstration. Until the migration is applied the site still works (the region lookups tolerate the missing table); run `python -m scripts.migrate_db --plan` and then `python -m scripts.migrate_db` on your development database.

The public Garage lists only `content_status = 'official'` vehicles. The eight concept vehicles remain in the database because the story archive links them to missions (many-to-many), but they have no public page, and the JSON API still serves the whole table.

## Accounts and privileges

| Account | Used by | Privileges (project databases only) |
|---------|---------|-------------------------------------|
| `valkyrie_app` | the running website and the test suite's queries | `SELECT, INSERT, UPDATE, DELETE` |
| `valkyrie_migrator` | `scripts.setup_db` / `scripts.init_db` (schema load) | the above plus `CREATE, DROP, ALTER, INDEX, REFERENCES` |
| MySQL admin (root) | `scripts.setup_db` only, via a hidden prompt, once | not stored anywhere |

`tests/test_privileges.py` proves the website account is refused `DROP`, `CREATE`, `ALTER`, `TRUNCATE`, `CREATE USER`, `DROP DATABASE` and reading `mysql.user`, and that the migration account cannot create databases or users.
`REFERENCES` is required by MySQL to create foreign keys (discovered by testing: the load fails without it).

## Reproducible setup

```powershell
python -m scripts.make_env              # local .env with random secrets
python -m scripts.setup_db --plan       # read-only preview
python -m scripts.setup_db              # apply (type YES). Never drops existing tables
python -m scripts.setup_db --reset      # also rebuild existing project tables (type RESET)
python -m scripts.init_db --reset       # rebuild only the development tables
```

Example queries (all executed by the test suite): [`queries.sql`](queries.sql).

## Known verification gap

Tested on **MySQL 8.0.46**. The project specifies 8.4 LTS. The schema uses only features present in both,
but it has **not** been run on 8.4. MySQL reports foreign-key failures as error 1451/1452 on some builds and 1216/1217 on
others, so tests accept either pair.
