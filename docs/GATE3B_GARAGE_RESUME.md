# Gate 3B: Garage v2 (cinematic transformation) — RESUME CHECKPOINT

Saved 2026-10-16 at the owner's request ("pause work and save a resume checkpoint"). This is a **pause**, not a completion or cancellation.
To resume, the owner will say: *"Claude, resume Team Valkyrie Garage Gate 3B from the saved checkpoint."* Then: read this file, inspect the real
repository and `git status`, reconcile, continue from the first unfinished task in section 6, finish, build the review ZIP and **stop for approval**.

## 1. Project context
"Grand Theft Auto VI | Team Valkyrie": an unofficial educational fan site (college Web Technologies + DBMS), at `D:\Projects\GTA 6`.
Flask app factory (blueprints → services → repositories), MySQL 8, vanilla HTML/CSS/JS + Jinja2, pytest against a real `*_test` database, local Git only
(the owner pushes). CSP forbids inline styles (so crops use `data-px/py/pxn/pyn/zoom` attributes and a grid of CSS rules). Motion policy in `site.js` sets
`html.motion-on` only when allowed (system reduced motion, data saver and the menu Motion switch all count). Design tokens in `tokens.css`, guarded by
`tests/test_design_tokens.py` (font sizes, radii, tracking, undefined custom properties; `garage.css` is covered).
Standing constraints: never hardcode, print, log or commit the MySQL root password; never commit `.env`, `.venv`, credentials, DB dumps or media;
no destructive DB operations; the owner pushes and runs dev-DB migrations; never invent details about Rockstar characters or vehicles; **no push**.

## 2. Current task
Garage v2 — the cinematic redesign of `/vehicles` and `/vehicles/<slug>`, after the owner rated Garage v1 **4/10** (functionality fine, visuals far below Home and
Characters). Target: 9.5+/10 subjective visual quality with excellent reliability. Do not self-award a score. Garage only.

## 3. Original requirements (the owner's master prompt, condensed but complete in intent)
**Why v1 failed (owner's audit):** (A) weak cinematic identity: oversized Cheetah close-up, little title presence, text over a picture rather than art direction;
(B) a generic catalogue (search, chips, ordinary cards); (C) every detail page the same template (hero, paragraph, facts plate, gallery, related cards);
(D) developer-like explanations ("Not published by Rockstar", "official images: 4", "What the pictures are", repeated status text) taking visual space, and the headline
"Every Machine Rockstar Has Shown" too broad for a curated collection; (E) only five vehicles / 17 screenshots made the limit obvious: research Rockstar's official media
for more, never invent; (F) empty-looking thumbnail rectangles in gallery captures: find out whether lazy loading, capture timing or a real defect.
**Direction:** "The Garage — Machines of Leonida": AAA game-promotion site + automotive photography campaign + immersive editorial storytelling. Not a dealership, not e-commerce.
Keep Team Valkyrie typography, dark palette, branding; borrow the quality principles (not layouts) of Home and Characters.
**Opening:** art-directed hero; full silhouette visible where the source allows; bold readable title; no text over a roof or front wing; designed mobile framing; deliberate CTA;
a premium showroom-controller-style vehicle selector (keyboard and touch; smooth transitions; **no auto-advance**; no fake 3D / rotation); choose the strongest *composition*,
not the biggest crop.
**Showroom:** a visual journey with rhythm and hierarchy, not five interchangeable cards and not five giant sections; contrasting photographic environments (neon city, luxury,
off-road, water, vintage cruising) as themes only, never new categories or gameplay claims; integrate real MySQL-backed search, category, sort and pagination elegantly
(not an admin-style filter wall); keyboard access, result states, empty state.
**Vehicle pages:** each an editorial feature with vehicle-specific art direction (not one template, five backgrounds); the verified description presented large; image
storytelling that adapts to the number of pictures (one-picture vehicles get a minimal beautiful composition, no apologetic paragraph, no empty gallery); keep next/previous and
full-size viewing where applicable; compact verified facts (maker, category, source, reliable associations) — no giant facts plate, **never** fabricate price, horsepower, top speed,
availability or ratings; related-vehicle navigation polished (no oversized clipped type).
**Media:** research https://www.rockstargames.com/VI media/screenshots/trailers; identify vehicles correctly; keep exact provenance; unidentified vehicles only as atmosphere, never named;
no AI/fan/GTA V material; derivatives Git-ignored; best material, not most.
**Motion:** a few exceptional interactions, all compatible with reduced motion, efficient on college laptops and phones, no framework dependencies.
**Tone:** concise, atmospheric, truthful; provenance kept but discreet; no claim that the collection is every GTA VI vehicle.
**Engineering:** keep Flask/MySQL behaviour (routes, search/sort/pagination, categories, media relations, source labels, APIs, parameterised SQL, errors, security); no unnecessary schema
change (a needed one must be a safe, tested, reversible migration); scoped shared CSS/JS; do not modify Home, Characters, Leonida, Locations, Stories.
**QA:** every vehicle at 390, 820, 1024, 1440, 1920 plus the 88-width sweep; real-browser tests of selector, gallery, search, filters, sort, keyboard, touch, reduced motion, image-failure
fallbacks, page transitions; performance (layout shift, loading, decode, duplicate requests); compare critically with Home and Characters; fix obvious defects before submitting.
**Deliverables:** concise design audit; chosen direction and why; before/after full landing screenshots; desktop + mobile screenshots of every vehicle page; hero comparison with every
vehicle selected; showroom and interactive-state screenshots; playable recordings of significant motion; evidence of gallery/thumbnail loading; media-source and image-selection summary;
responsive, accessibility and performance results; full pytest results; ONE organised review ZIP; exact PowerShell instructions for any media generation, migration and server start;
commit locally, **do not push**; keep generated media and review artifacts Git-ignored.
**Stop condition:** finish Garage Gate 3B only; do not touch Home/Characters; do not start Leonida/Locations/Stories; present the website and ZIP and wait for the owner's rating.

## 4. Completed work (all committed unless section 5 says otherwise)
* **Audit** of v1 and the owner's list (above). Problem F answered: the "empty thumbnails" were lazy-loaded `<img>` thumbnails not yet requested at capture time (and full-page
  captures of large images painting late). Fixed twice over: thumbnails are never lazy (`lazy=false`), and `scripts/qa/capture_pages.mjs` now takes full-page shots in a window as tall as the page.
* **Media research** (`docs/MEDIA_INVENTORY.md`, section "Garage research"): all 166 pictures on Rockstar's screenshots page reviewed as thumbnails; both trailers sampled every 2 s
  (vehicles unnamed/small: no frame used). Two more vehicles Rockstar names, **Dinka Enduro Motorcycle** and **Crest Kayak** (titles in its "Jason's Safehouse Vehicles" set), plus four
  atmosphere pictures (Rideout Customs, One-Eyed Willie's, Classic Car Collection 02 and 04) and the safehouse scene. Review-only research files are in `review/gate3c/research/` (Git-ignored).
* **Migration 006** `database/migrations/006_gate3b_garage.sql` (non-destructive, idempotent; mirrored at the end of `database/seed.sql`; listed in `tests/test_migration.py`):
  vehicles 14 (Dinka Enduro Motorcycle, motorcycle) and 15 (Crest Kayak, boat), media rows 108–114, `media_vehicles` links, plain editorial `summary/description` copy for the five existing official
  vehicles. Counts now: 15 vehicles (7 official), 114 media rows. Seed/API/example-query tests updated for the new counts.
* **Garage v2 front end**: `app/templates/vehicles/{_garage,index,detail}.html`, `app/static/css/garage.css`, `app/static/js/garage.js`.
  * Opening (`.cine`): one machine at a time, whole vehicle drawn at its own 16:9 proportions above a "console", large model name with the maker small above (`nameplate`, `split_name`),
    outlined numeral, per-vehicle tint, theme words, "Explore" button, lineup rail with a lit line + hover preview, previous/next arrows + counter, swipe, arrow keys, Home/End, pointer depth,
    scroll lag; no auto-advance; pictures decoded before a panel shows; direction-aware crossfade; stacked layout under 900 px (picture, then words, then a scrolling rail).
  * Collection (`.coll`): headline counts the vehicles ("Seven machines of Leonida"), a quiet control row (category pills, compact search, sort) with a result line only when filtering, a varied mosaic
    (`garage_rows`: 8+4, 4+4+4, 5+7, 7+5 …), a "Customs and classics" band between rows (four unnamed Rockstar mod-shop/classic pictures), whole-tile links, empty state, pagination, quiet credit line.
  * Vehicle pages: full-bleed entrance (vehicle-specific side/top placement, tint, numeral), description set large, compact credits (maker, type, source), and a **different showcase per vehicle**:
    Cheetah `mosaic`, Dominator Buggy `viewer`, Squalo `panorama`, Stanier `mosaic-flip`, Ganado `none` (one picture, nothing empty), Dinka and Kayak `scene` (the shared safehouse picture with
    Rockstar's set title); previous/next panels with wrap-around and the whole lineup; connected-world section only when the database records missions/places.
  * Choosing a vehicle: Chrome cross-document view transition (off for reduced motion); reduced motion keeps only a 0.25 s plain fade.
  * Performance work: removed `mask-image` and `filter` (software-rendered frame times dropped from ~33–50 ms to a steady 16.7 ms on picture switches), `will-change` on the active scene.
  * Single-picture vehicles (Ganado, Dinka, Kayak) draw their tile closer on the subject via `card_zoom` + `data-zoom` so the tile is not a copy of the opening.
* **Service layer** `app/services/site.py` (garage section) and `app/media_slots.py` (end of file: `GARAGE_FRAMES`, `GARAGE_PICKS`, `GARAGE_MOMENTS`), `app/repositories/media.py` (`counts()`).
* **Tests**: `tests/test_gate3b_garage.py` rewritten for v2 (rows, picture picks, DB data, opening, controls, vehicle pages, CSS scope); `tests/test_pages.py`, `test_design_tokens.py`, `test_migration.py`,
  `test_api_phase2.py`, `test_example_queries.py`, `test_seed_data.py` updated.
* **Real-browser QA scripts** (`scripts/qa/`, all passing at last run): `garage_interactions.mjs`, `garage_keyboard.mjs`, `garage_resilience.mjs` (console errors, no-script, reduced motion, images
  blocked), `garage_stage_shots.mjs`, `garage_review_shots.mjs`, `garage_record.mjs`, `capture_pages.mjs`, `sweep.mjs`.
* **Results at last full runs** (before the final CSS tweaks below): full `pytest` **479 passed**; interactions, keyboard, resilience: **all passed**; width sweep 18 routes x 88 widths clean;
  Characters motion/cast-navigation checks passed earlier in this task.
* v1 (rated 4/10) is in commits `b4a9f35` and `c6459f2`; v2 is `46d0718` and the checkpoint commit made at this pause.

## 5. Work in progress / uncommitted state at the pause
* The last edits before the pause (in the checkpoint commit): `garage.css` — the opening picture now sits **above the console** (`--console: 168px`; `.scene__art { inset: auto 0 var(--console) 0; … }`),
  laptop-width (900–1199 px) smaller name sizes, `.scene--top` height rule recalculated; `tests/test_design_tokens.py` allows `--console`; `scripts/qa/garage_{record,review_shots,stage_shots}.mjs` tweaks.
  After these edits only `tests/test_design_tokens.py` + `tests/test_gate3b_garage.py` (66 tests) were re-run (passed). **The full pytest, the browser scripts, the sweep and all review screenshots must be
  re-run** because they pre-date the console change (visual check of the new opening at 1024 and 1440 px looked right).
* The review pack was being regenerated when the pause came (the landing capture was killed mid-run): `review/gate3c/pack/` is **partial** (Git-ignored): before/after boards and hero sheets exist from an
  earlier state; `screenshots/landing/` and `screenshots/opening-each-machine/` were deleted for regeneration and are missing. Recordings and filmstrips were also deleted for regeneration.

## 6. Next actions on resume (in order)
1. `git status`, `git log --oneline -5`; confirm branch `main`, the v2 commits, and a clean tree. Start the preview server (`gta6-preview-seeded-test-db`, port 5057); stop it before pytest (MySQL metadata locks).
2. Run the full `pytest`; fix anything the console change broke (CSS-only, so likely nothing).
3. Re-run the browser scripts (`garage_interactions`, `garage_keyboard`, `garage_resilience`) and the sweep; fix regressions.
4. **Visual critique round** of the final state at 390, 820, 1024, 1440, 1920: opening for each of the 7 machines (stage shots), the collection, all seven vehicle pages. Known candidates to judge:
   Dominator Buggy name close to the vehicle at 1440; the Dinka and Kayak pages both use the same safehouse scene (consider a different crop/zoom for one, `scene` tuple in `GARAGE_PICKS`);
   remaining headroom on the Kayak/Dinka tiles; tablet (820) opening spacing.
5. Regenerate the review pack in `review/gate3c/pack/`: landing (1920, 1440, 1280, 1024, 820, 390, 320, full + first screen), all seven vehicle pages (1440, 820, 390), opening for each machine
   (1920, 1440, 1024, 820, 390), states (`garage_review_shots.mjs`), recordings (`garage_record.mjs`) and filmstrips, before/after boards (v1 screenshots are in
   `review/gate3b/Team-Valkyrie-Garage-Gate3B-Review/screenshots/`), hero-every-vehicle sheets, evidence files in `test-evidence/` (pytest, interactions, keyboard, resilience, sweep, frame timing
   `review/gate3c/fps.mjs`, network/layout shift `review/gate3c/perf3.mjs`).
6. Write in the pack: `REPORT.md` (audit, chosen direction and why, what changed, interactive features, DB changes (migration 006), media decisions and limits, accessibility/performance results, regression results,
   an honest self-assessment WITHOUT a score), `MEDIA_SOURCES.md` (every picture used: Rockstar title, file name, which page/role, identification confidence), `README.txt`, exact PowerShell commands
   (below). Update `docs/GATE3B_GARAGE.md` for v2 (it still describes v1).
7. Build ONE ZIP: `review/gate3c/Team-Valkyrie-Garage-Gate3B-v2-Review.zip` (PowerShell `Compress-Archive`; `review/` is Git-ignored). Commit any final code/doc changes locally (end commit messages with
   `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`). Update the memory file `project-gta6-round2-state.md`. **Do not push.**
8. Final report to the owner, then **STOP** and wait for the rating. Do not start Leonida, Locations or Stories; do not touch Home or Characters.

## 7. Design decisions (keep)
* Direction "Machines of Leonida": cinematic stage + console, mosaic collection with a customs band, a different editorial set per vehicle. Team Valkyrie tokens only (no new fonts/colours);
  each vehicle has a `--tint` used for light and the lit line only, never body text.
* Stage/entrance picture is drawn at 16:9 above the console, never cropped at the sides; words sit opposite the vehicle (`side`), above it for long low cars (`vpos: top`, with the summary beside the name).
* Hero picks (`GARAGE_PICKS`): Cheetah stage `…cheetah-01` (whole car, car park at golden hour), card `…-02`; Dominator Buggy stage `…-01` (trail, whole buggy), card `…-02`;
  Squalo stage `…-01` (skyline at dusk), card `…-02` (aerial); Stanier stage `…-01` (whole car, neon), card `…-04` (tail-light close-up); Ganado `…-01` (only picture; tile zoomed);
  Dinka Enduro and Crest Kayak: their own pictures (tiles zoomed), plus the shared safehouse scene on their pages.
* Atmosphere-only pictures (never named): Rideout Customs 01, One-Eyed Willie's 01, Classic Car Collection 02 and 04, captioned only with Rockstar's set titles.
* No specifications anywhere; one quiet credit line ("Screenshots © Rockstar Games… Rockstar has not published specifications"); no "Every machine…" claims; headline counts the vehicles.
* No auto-advance; reduced motion keeps a 0.25 s fade only; view transition and pointer/scroll effects are `prefers-reduced-motion: no-preference` only.
* Constraints: do not edit Home, Characters, Leonida, Locations, Stories, the media registry beyond migration 006, or shared CSS/JS (`pages.css` only lost the unused `.garage-rows`/`.more-grid` rules).

## 8. Technical state
* Branch `main` (local only, never pushed). Commits: `b4a9f35` v1, `c6459f2` v1 docs, `46d0718` v2, plus the checkpoint commit "chore(garage): checkpoint…" made at this pause (see `git log`).
* Key files: `app/media_slots.py` (end), `app/services/site.py` (garage section: `garage_rows`, `split_name`, `_garage_picture`, `_garage_entries`, `vehicle_index`, `vehicle_detail`, `_garage_moments`),
  `app/repositories/media.py` (`counts`), `app/templates/vehicles/*.html`, `app/static/css/garage.css`, `app/static/js/garage.js`, `database/migrations/006_gate3b_garage.sql`, `database/seed.sql`,
  `docs/MEDIA_INVENTORY.md`, `docs/GATE3B_GARAGE.md` (v1 text), this file, `tests/test_gate3b_garage.py`, `scripts/qa/*`.
* Known state/errors: none known in code. The dev database (not the test DB) still has only the original five official vehicles until the owner runs migration 006 (below); the preview server and pytest use the seeded `*_test` database.
* Commands (PowerShell, from the project folder):
  * Tests: `.\.venv\Scripts\python.exe -m pytest -q` (stop the preview server first).
  * Server: `.\.venv\Scripts\python.exe -m flask --app wsgi run` (open `/vehicles`).
  * Migration for the owner's dev DB: `.\.venv\Scripts\python.exe -m scripts.migrate_db --plan` then `.\.venv\Scripts\python.exe -m scripts.migrate_db` (non-destructive; owner runs it).
  * QA (Git Bash, preview server on 5057): `MSYS_NO_PATHCONV=1 node scripts/qa/cdp.mjs scripts/qa/garage_interactions.mjs` (likewise `garage_keyboard.mjs`, `garage_resilience.mjs`;
    `SWEEP_ROUTES=… node scripts/qa/cdp.mjs scripts/qa/sweep.mjs`; `CAP_OUT=… CAP_ROUTES=… CAP_WIDTHS=… CAP_MODE=full,first node scripts/qa/cdp.mjs scripts/qa/capture_pages.mjs`).
  * Preview server: `preview_start gta6-preview-seeded-test-db` (port 5057).

## 9. Media dependencies
The Garage uses **no generated or downloaded media**: every picture is a remote reference to Rockstar's own server (registry rows, migrations 002 and 006). Nothing in `media/` is needed for Garage.
Git-ignored local files worth keeping (not required to run the site): `review/gate3b/` (v1 pack and ZIP), `review/gate3c/` (research thumbnails/sheets, v2 partial pack), `media/clips/*` (Characters sequences and
Real Dimez/Dre'Quan stills; regenerate with `python -m scripts.make_loops --portraits` and `--stills`). If research files are lost: re-fetch the screenshots page and re-run
`review/gate3c/research/triage.py` (needs Pillow).

## 10. Protected sections
Home and Characters are **frozen** (Characters approved after Gate 3A). Do not modify them. Also leave Leonida, Locations, Stories and Media untouched.

## 11. Stop condition
Finish Garage Gate 3B only, produce the review ZIP, give the report, and **wait for the owner's approval/rating** before touching anything else.
