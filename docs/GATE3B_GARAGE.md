# Gate 3B: the Garage, "Machines of Leonida" (version 2)

Version 1 (commits `b4a9f35`, `c6459f2`) was rated 4/10 by the owner. Version 2 (`46d0718` onward) is a redesign of the Garage page and the vehicle pages. This note
records the audit, the direction, the behaviour and how to run and check it. Code: `app/templates/vehicles/`, `app/static/css/garage.css`, `app/static/js/garage.js`, the
Garage section of `app/services/site.py` and the end of `app/media_slots.py`. Nothing outside the Garage loads the new stylesheet or script.

## 1. Why version 1 failed
* The opening was one oversized close-up of the Cheetah with a small title: a big picture with text on it, not art direction.
* Below it, a database-administration look: a wide search bar, category chips, a sort menu and five similar cards.
* Every vehicle page was the same template (hero, one paragraph, facts plate, gallery, related cards).
* Developer wording took the space: "Every Machine Rockstar Has Shown", "Not published by Rockstar", "4 official images", "What the pictures are".
* Five vehicles and 17 pictures were all it knew; the gallery thumbnails looked empty in captures (lazy loading and capture timing).

## 2. Direction
A cinematic stage, then a varied mosaic with a customs-and-classics band, then an editorial page per vehicle. Team Valkyrie tokens only; each vehicle has a tint (`--tint`)
used for light and the lit line. Words sit opposite the vehicle (or above it for a long low car, with the summary beside the name); the picture is drawn at its own 16:9 above the
controller, never cropped at the sides; on tablets and phones the picture comes first and the words under it.
Three directions were compared: equal cards (what v1 was), one chapter per vehicle (hides the database), stage + mosaic + per-vehicle sets (chosen).

## 3. What each part does
* **Opening** (`.cine`): one machine at a time, seven in the lineup (click, tap, previous/next arrows, swipe, arrow keys, Home/End); the lit line takes the machine's tint; a counter and a
  live announcement; pictures are decoded before their panel shows; the picture and words move in from the side chosen; no auto-advance. Pointer depth and scroll lag only where the browser
  allows and the visitor has not asked for reduced motion.
* **Collection** (`.coll`): headline "Seven machines of Leonida" (counts the data), category pills, a compact search and a sort menu (applies when chosen); a result line only while filtering;
  rows from `site.garage_rows` (8+4, 4+4+4, 5+7, 7+5, …) so no row has a hole; whole-tile links with number, theme words, maker above model; the customs band shows only on the whole collection.
  All of it is a real GET against MySQL (`vehicles.list_vehicles`: official only, bound parameters, validated sort and page, pagination).
* **Vehicle pages**: entrance (picture + large name), the database description set large, credits (maker, type, source), then the showcase set to suit the pictures: Cheetah `mosaic`,
  Dominator Buggy `viewer` (previous/next, thumbnails, swipe, full-size viewer), Squalo `panorama`, Stanier `mosaic-flip`, Ganado `none` (one picture: nothing empty),
  Dinka and Kayak `scene` (the shared safehouse picture, cut differently, captioned with Rockstar's set title). The connected-world section appears only when the database records
  missions or places. Previous/next panels wrap round; the whole lineup follows.
* **Choosing a vehicle**: the picture grows into the vehicle's page (Chrome cross-document view transition; other browsers load the page). Off under reduced motion.
* **Honest copy**: one quiet credit line ("Screenshots © Rockstar Games… Rockstar has not published specifications"); no specification, price or performance claim anywhere.

## 4. Data and media
Migration `database/migrations/006_gate3b_garage.sql` (non-destructive, idempotent, mirrored in `database/seed.sql`): vehicles 14 (Dinka Enduro Motorcycle) and 15 (Crest Kayak), media
rows 108–114 (their pictures and four atmosphere pictures), `media_vehicles` links, plain editorial copy for the five existing official vehicles. No schema change. Research and sources:
`docs/MEDIA_INVENTORY.md` ("Garage research") and the review pack's `MEDIA_SOURCES.md`. No generated or downloaded media: every picture is a remote reference to Rockstar's server.
Applying it to the owner's development database (the owner runs this; nothing is dropped or deleted):

```powershell
.\.venv\Scripts\python.exe -m scripts.migrate_db --plan
.\.venv\Scripts\python.exe -m scripts.migrate_db
```

## 5. Checks
`tests/test_gate3b_garage.py` (arrangement, picture picks and alt text, the data, the opening, every control against MySQL, each vehicle's set, CSS scope), plus real-browser scripts in
`scripts/qa/`: `garage_interactions.mjs`, `garage_keyboard.mjs`, `garage_resilience.mjs` (console, no script, reduced motion, images blocked), `garage_stage_shots.mjs`,
`garage_review_shots.mjs`, `garage_record.mjs`, `capture_pages.mjs`, and the existing `sweep.mjs`.

```powershell
.\.venv\Scripts\python.exe -m pytest -q          # stop the preview server first
.\.venv\Scripts\python.exe -m flask --app wsgi run
# with the app on 5057 (Git Bash):
MSYS_NO_PATHCONV=1 node scripts/qa/cdp.mjs scripts/qa/garage_interactions.mjs
MSYS_NO_PATHCONV=1 node scripts/qa/cdp.mjs scripts/qa/garage_keyboard.mjs
MSYS_NO_PATHCONV=1 node scripts/qa/cdp.mjs scripts/qa/garage_resilience.mjs
SWEEP_ROUTES=/vehicles,/vehicles/crest-kayak MSYS_NO_PATHCONV=1 node scripts/qa/cdp.mjs scripts/qa/sweep.mjs
```

## 6. Limits
* Seven vehicles and 21 vehicle pictures (plus four atmosphere pictures): a filtered collection can hold one tile; pagination appears past nine vehicles (works; tested with `per_page=2`).
* Ganado, Dinka and Kayak each have one picture of their own; the Dinka and Kayak pages share one scene picture (cut differently).
* Rockstar publishes no specifications; the Garage states none. No official vehicle has a recorded mission or place yet.
* The picture-to-page transition is Chrome-only.
