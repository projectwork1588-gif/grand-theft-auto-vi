# Garage migration (006): back up, check, apply only this file, verify, undo

Migration `database/migrations/006_gate3b_garage.sql` brings the Garage's data up to seven official vehicles. **Nothing in this repository applies it for you**: you run it on your development database when you choose. Until then the Garage still works and shows what your database holds (five vehicles, "Five machines of Leonida"); it never claims seven.

Run every command below from the **project folder** in **Windows Command Prompt** (`cmd.exe`), not PowerShell. PowerShell 5.1 rewrites text sent through `>` and `<` (UTF-16, extra bytes) and corrupts a dump; Command Prompt passes the bytes through untouched, and `mysqldump --result-file` writes the file itself, so the shell never touches it at all.

## What it does, and what it cannot do

| It does | It never does |
| --- | --- |
| Adds two vehicles Rockstar names: Dinka Enduro Motorcycle (id 14, Motorcycles) and Crest Kayak (id 15, Boats) | Delete, drop or truncate anything (the runner refuses a file that contains those words, and a test checks the file) |
| Adds seven picture records (ids 108 to 114): remote references to Rockstar's own images, nothing copied into the project | Change the name, slug, category, label or source link of any existing vehicle |
| Links the Dinka and Kayak pictures (and the shared safehouse scene) to those two vehicles: four rows in `media_vehicles` | Touch characters, regions, locations, missions, users or the schema |
| Rewrites only the `summary` and `description` text of the five older official vehicles (ids 9 to 13) | Store a specification Rockstar has not published |

It is idempotent: running it again changes nothing.

## 1. Back up first

`mysqldump` asks for the password itself, so it is never typed into a command line, a file or your history. Use the account in your `.env` (default `valkyrie_migrator`; any account that can read the database works) and your database name (default `gta6_vi`).

```bat
if not exist backups mkdir backups
"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe" -u valkyrie_migrator -p --single-transaction --no-tablespaces --routines --default-character-set=utf8mb4 --result-file=backups\gta6_vi_before_006.dump gta6_vi
```

* The backup is `backups\gta6_vi_before_006.dump`. Both `backups\` and `*.dump` are Git-ignored, so it cannot be committed by accident; keep it on your machine only.
* If `mysqldump` is already on your PATH you can type just `mysqldump` instead of the long path.
* Check it is a real dump (size well over 100 KB, ends with "Dump completed"):

```bat
dir backups\gta6_vi_before_006.dump
powershell -NoProfile -Command "Get-Content -Tail 2 backups\gta6_vi_before_006.dump"
```

## 2. See what would run, and what it would touch (changes nothing)

```bat
.venv\Scripts\python.exe -m scripts.migrate_db --only 006_gate3b_garage.sql --plan
```

`--only` takes **one exact file name** from `database/migrations/`. A path, a folder, a different case or an unknown name is refused before the database is even contacted, and without `--only` the runner behaves exactly as before (all six files). The plan lists just that file and runs read-only checks:

* the tables and columns 006 writes to exist (`vehicles`, `vehicle_categories`, `media_assets`, `media_vehicles`), and the foreign keys between them are in place;
* categories 5 and 6 are `boat` and `motorcycle`;
* the five official vehicles from migration 002 (ids 9 to 13) are there, and which of them will have their wording set;
* vehicle ids 14 and 15 and media ids 108 to 114 are free, or already hold exactly what 006 would put there (a second run);
* the slugs `dinka-enduro`, `crest-kayak` and the media slugs, and the names, do not belong to anything else;
* no other link in `media_vehicles` is attached to the migration's pictures or vehicles.

Lines starting `ok` are fine. A line starting **`STOP`** is a conflict or a missing prerequisite: the plan exits with status 1 and **applying is refused**, so nothing of yours is overwritten. Send me the `STOP` lines rather than forcing anything. (If a prerequisite table is missing, the older migrations were never applied; run the plain `python -m scripts.migrate_db --plan` to see them.)

## 3. Apply only 006

```bat
.venv\Scripts\python.exe -m scripts.migrate_db --only 006_gate3b_garage.sql
```

It repeats the checks, then asks you to type `YES` (anything else cancels). Only then is `006_gate3b_garage.sql` executed; migrations 001 to 005 are not re-run. At the end it prints a line such as `After 006: 7 official vehicles (expected 7), vehicles 14 and 15 present: 2/2, media 108 to 114: 7/7, links: 4/4 - OK`.

## 4. Verify

```bat
"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u valkyrie_migrator -p gta6_vi -e "SELECT COUNT(*) AS official_vehicles FROM vehicles WHERE content_status = 'official'; SELECT vehicle_id, slug, name, category_id FROM vehicles WHERE vehicle_id IN (14, 15); SELECT media_id, vehicle_id FROM media_vehicles WHERE media_id >= 108; SELECT COUNT(*) AS media_108_to_114 FROM media_assets WHERE media_id BETWEEN 108 AND 114;"
```

Expected: `official_vehicles` 7; `dinka-enduro` (category 6) and `crest-kayak` (category 5); links (108,14), (109,15), (110,14), (110,15); `media_108_to_114` 7. Then start the site and open `/vehicles`: "Seven machines of Leonida", seven machines in the lineup, the Boats filter shows the Squalo and the Kayak, the Motorcycles filter shows the Dinka, and `/vehicles/dinka-enduro` and `/vehicles/crest-kayak` open.

## 5. Undo

**The safe way: restore the backup.** It puts the whole database back exactly as it was. The dump drops and recreates each table, so run it only on the database you backed up (if the migration account is not allowed to drop tables, use your MySQL administrator account; the password is always typed at the prompt).

```bat
"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u valkyrie_migrator -p --default-character-set=utf8mb4 gta6_vi < backups\gta6_vi_before_006.dump
```

**A targeted undo** (only if nothing else changed since, and you want just 006 removed). This is documentation, not a migration: it is deliberately not in `database/migrations/`, because migrations here never delete. It deletes rows, so run it yourself, knowingly:

```sql
DELETE FROM media_vehicles WHERE vehicle_id IN (14, 15) OR media_id >= 108;
DELETE FROM media_assets   WHERE media_id >= 108;
DELETE FROM vehicles       WHERE vehicle_id IN (14, 15);
```

The five older vehicles keep the new wording; to return those to the earlier text, restore the backup.

## For a fresh database

A new database built with `scripts/init_db` already includes everything in 006 (it is also at the end of `database/seed.sql`), so there is nothing to migrate.

## What the tests prove (test database only)

`tests/test_migrate_only.py` and `tests/test_gate3b_migration.py`: unknown names and paths are refused without connecting; `--only` plans and applies exactly one file (an edit that migration 003 would undo survives it, and the default run still undoes it); each conflict above blocks the plan and the apply and leaves every row untouched; the checker's expectations equal what the migration really stores; before 006 the Garage shows five machines, after it seven.
