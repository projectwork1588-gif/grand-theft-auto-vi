# Garage migration (006): back up, apply, check, undo

Migration `database/migrations/006_gate3b_garage.sql` brings the Garage's data up to seven official vehicles. **Nothing in this repository applies it for you**: it is run by you, on your development database, when you choose. Until then the Garage still works and shows what your database holds (five vehicles, "Five machines of Leonida"); it never claims seven.

## What it does, and what it cannot do

| It does | It never does |
| --- | --- |
| Adds two vehicles Rockstar names: Dinka Enduro Motorcycle (id 14, Motorcycles) and Crest Kayak (id 15, Boats) | Delete, drop or truncate anything (the runner refuses a file that contains those words, and a test checks the file) |
| Adds seven picture records (ids 108 to 114): remote references to Rockstar's own images, nothing copied into the project | Change the name, slug, category, label or source link of any existing vehicle |
| Links the Dinka and Kayak pictures (and the shared safehouse scene) to those two vehicles: four rows in `media_vehicles` | Touch characters, regions, locations, missions, users or the schema |
| Rewrites only the `summary` and `description` text of the five older vehicles (plain wording that states what Rockstar's pictures show) | Store a specification Rockstar has not published |

It is idempotent: running it again changes nothing (`tests/test_gate3b_migration.py` proves this, and that a database without it shows five machines and one with it shows seven).

## 1. Back up first (PowerShell, from the project folder)

`mysqldump` asks for the password itself, so it never goes into a command line, a file or your shell history. Use the migration account from your `.env` (default `valkyrie_migrator`) and your database name (default `gta6_vi`).

```powershell
mysqldump -u valkyrie_migrator -p --single-transaction --no-tablespaces --routines --default-character-set=utf8mb4 gta6_vi > backups\gta6_vi_before_006.sql
```

* Create the `backups` folder first if it does not exist. Backups are database dumps: they stay on your machine and are Git-ignored (do not add them to a commit).
* Check that the file is not empty: `(Get-Item backups\gta6_vi_before_006.sql).Length` should be well over 100 KB.
* If `mysqldump` is not on your PATH it is in `C:\Program Files\MySQL\MySQL Server 8.0\bin`.

## 2. See what would run (changes nothing)

```powershell
.\.venv\Scripts\python.exe -m scripts.migrate_db --plan
```

It lists the migrations and what your database already has. Nothing is written.

## 3. Apply

```powershell
.\.venv\Scripts\python.exe -m scripts.migrate_db
```

It asks you to type `YES`. Then run the checks.

## 4. Check it worked

Run these in MySQL (use your own account; the first two numbers are the point):

```sql
SELECT COUNT(*) FROM vehicles WHERE content_status = 'official';                 -- 7
SELECT vehicle_id, slug, name FROM vehicles WHERE vehicle_id IN (14, 15);         -- dinka-enduro, crest-kayak
SELECT media_id, vehicle_id FROM media_vehicles WHERE media_id >= 108;            -- (108,14) (109,15) (110,14) (110,15)
SELECT COUNT(*) FROM media_assets WHERE media_id BETWEEN 108 AND 114;             -- 7
```

Then start the site and open `/vehicles`: the headline reads "Seven machines of Leonida", the lineup has seven machines, the Boats filter shows the Squalo and the Kayak, the Motorcycles filter shows the Dinka, and `/vehicles/dinka-enduro` and `/vehicles/crest-kayak` open.

## 5. Undo

**The safe way: restore the backup.** This puts the whole database back exactly as it was.

```powershell
mysql -u valkyrie_migrator -p gta6_vi < backups\gta6_vi_before_006.sql
```

(The dump contains `DROP TABLE IF EXISTS` for each table it restores, which is what makes this a full restore. Only run it on the database you backed up.)

**A targeted undo** (only if you did not change anything else since, and only if you want just 006 removed). This is documentation, not a migration: it is deliberately not in `database/migrations/`, because migrations here never delete. Run it yourself, knowing it deletes rows:

```sql
DELETE FROM media_vehicles WHERE vehicle_id IN (14, 15) OR media_id >= 108;
DELETE FROM media_assets   WHERE media_id >= 108;
DELETE FROM vehicles       WHERE vehicle_id IN (14, 15);
```

The five older vehicles keep the new wording; to return those to the earlier text, restore the backup.

## For a fresh database

A new database built with `scripts/init_db` already includes everything in 006 (it is also at the end of `database/seed.sql`), so there is nothing to migrate. `tests/test_migration.py` proves a seeded database and a migrated one end up identical.
