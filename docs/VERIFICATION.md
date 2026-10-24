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

## Phase 2 refinement, round 2 (2026-10-10)

The previous review rated the site 3 out of 10. This pass rebuilt the front end (layouts, copy, motion, media) and kept the Flask and MySQL design, routes, relationships and API unchanged.

### Test results (real MySQL 8.0.46 service, `gta6_vi_test` database only)

```
python -m pytest -q
272 passed in 230s
```

| File | Tests | Covers |
|------|-------|--------|
| `test_pages.py` | 68 | Every page, filters, search, sorting, pagination, labels, 400/404 pages; the editorial characters page, region explorer, showroom and leads markup; About and Credits; footer content; the local-loop route and its path rules; reel and loop markup with and without local files; a copy audit (no database or test terminology on any public page); no inline script, style or event handler |
| `test_media.py`, `test_migration.py`, `test_seed_data.py` | 32 | Four migrations, upgrade equals a fresh seed, 107 media rows, local paths limited to `clips/<slug>.mp4` and the reel marked pending review |
| `test_security_and_failures.py`, `test_site_integrity.py`, `test_web.py` | 63 | CSP, escaping, safe 503s, link crawl including About and Credits, one `h1`, alt text |
| Earlier files | 109 | API, connectivity, integrity, privileges, setup safety, SQL runner, example queries |

The suite grew from 259 to 272. Tests were rewritten only where the feedback deliberately changed behaviour (markup, wording, removed statistics, the footer, new routes). Local clips are never required: the test app points `MEDIA_ROOT` at an empty folder and a fixture builds stand-in files when a test needs them.

### Browser verification (built-in browser, test database, port 5057)

| Check | Result |
|-------|--------|
| Desktop 1280: hero, two leads, cast stage, region explorer (hover to switch), garage showroom, stories band, trailers and mosaic, closing band, footer | Looked at in screenshots |
| Desktop: characters page, Lucia profile (hero crop and clip loop), garage rows, regions features, story page, About | Looked at in screenshots |
| **Video:** the 9-second reel started, advanced through all eight people and the name list followed it; a character loop started from its Play button and ran | Verified by script and screenshot |
| **Reduced motion:** the preview browser itself had `prefers-reduced-motion` on, so the stage showed a still and a Play button, and the hero showed a still | Verified (this is the accessibility path) |
| Tablet 768: hero, no horizontal overflow on home, characters, profile, garage, vehicle, regions, region, places, story and About | Hero looked at; overflow verified by script |
| Phone 375: leads, cast stage, region explorer, garage, menu, no overflow | Looked at in screenshots; overflow verified by script |
| Intermediate 1024: regions features | Looked at in a screenshot |
| Trailer dialog | The dialog opens and the iframe is created with Rockstar's player address. **Rockstar's player rendered blank in the preview browser**, so playback was not confirmed there |

Screenshots were viewed during development and are **not** committed: they contain Rockstar's artwork.

### Problems found and fixed in this pass

| # | What failed | Cause and fix | How verified |
|---|-------------|---------------|--------------|
| 1 | Inline `style` attributes in a new template would be blocked by the CSP | Replaced with classes | A test now rejects any ` style="` attribute on every public page |
| 2 | Cast stage overflowed its column (stage 1057 px in a 726 px column) | A 16:9 box in a stretched grid row took its width from the row height. Set `width: 100%` and centred the list | Measured by script |
| 3 | Hero showed an empty gradient for the first second | First slide began at opacity 0. Gave it a negative animation delay | Screenshot |
| 4 | Title lockup sat on Lucia's face | Widened and left-anchored the picture so the pair sit right of the title; stronger bottom shade on narrow screens | Screenshots at 1280, 768, 375 |
| 5 | Lucia's head cut off in the wide profile banner | Added a "top" focus hint for that image | Screenshot |
| 6 | Waypoint dial covered the footer links | Hides while the footer is on screen | Screenshot |
| 7 | Trailer dialog could exceed short viewports | Frame width limited by viewport height | Script |
| 8 | Story page eyebrow read "Story · Story" | Type-aware eyebrow | Screenshot |
| 9 | A truncated `conftest.py` (null bytes) from a heredoc | Re-written as plain ASCII; test collection re-run | pytest |

### Not verified or still open

* **Trailer playback inside Rockstar's player** was not confirmed in the preview browser (blank player). Open the homepage in a normal browser and press play.
* **Real autoplay behaviour** of the cast reel was exercised only through the Play button, because the preview browser asks for reduced motion.
* **Other browsers and real phones** are untested. Widths were emulated.
* **The owner's development database has not been migrated.** `python -m scripts.migrate_db --plan`, then `python -m scripts.migrate_db`, applies migration 004. Until then that site shows the previous imagery and copy.
* **Rights:** Rockstar states no licence terms for its media. The local loops are never committed, but the owner should decide before the site is public. MySQL 8.4 LTS is untested. Image file names are build-hashed and may change.
* **Not pushed.** The sandbox cannot authenticate to GitHub. Run `git push -u origin main` from your machine.

---

## Phase 2 refinement, round 3 (2026-10-11)

### Test results (real MySQL 8.0.46 service, `gta6_vi_test` database only)

```
python -m pytest -q
(see the final run recorded below)
```

New regression checks, all in `tests/test_pages.py`:

| Check | What it guards |
|-------|----------------|
| `test_cast_controls_are_in_the_first_paint_and_never_hidden` | The reel and pause buttons are in the first HTML, not `hidden`, and the reel button starts pressed and active. |
| `test_cast_script_never_hides_the_reel_or_pause_controls` | The cast script never toggles `.hidden` on them (the original bug) and exposes state through `aria-pressed`. |
| `test_cast_playlist_uses_one_explicit_order_not_database_order` | The name list equals `CAST_ORDER`, and reel segment start times ascend in the same order. |
| `test_cast_order_is_stable_when_the_database_returns_rows_differently` | Feeds the page the database rows reversed and expects the same order. |
| `test_loop_builder_cuts_the_reel_in_the_same_order` | `scripts/make_loops.py` uses the same sequence. |
| `test_no_serif_or_italic_type_anywhere`, `test_no_text_is_set_below_the_readable_floor` | No serif face, no italic, nothing under 0.7rem. |
| `test_first_moment_*`, `test_native_moments_*`, `test_only_the_built_moments_appear`, `test_cinematic_*` | The first moment sits between the leads and the cast and falls back to an official still and the trailer overlay; with built files all three moments render native video (muted, preload none, phone cut, no loop, sound button, no third-party player) in the right order; only built moments appear; file names are strict; the builder uses the approved ranges, removes Trailer 2's bars and never deletes or touches sources. |
| `test_script_plays_one_moment_at_a_time_*`, `test_chapter_navigation_*`, `test_reel_*`, `test_hero_*` | One video at a time and sound only by choice; the chapter rail replaces the floating pill; the reel builder is natural speed with a brief artwork hold; the hero is one static Robbery card with no cycle and no Beach. |
| `test_trailers_and_screenshots_are_two_distinct_blocks` | One lead trailer, three cards, six screenshots with the first and last wide (no empty cells). |
| `test_stories_section_separates_team_stories_from_official_connections` | "Team Valkyrie original" on the stories, an Official badge on the connections, no numbered list. |

### Browser verification (built-in browser, test database, port 5057)

| Check | Result |
|-------|--------|
| Hero, leads heading and copy, cast stage (first load, after a switch), stories, trailers, screenshots, viewer, navigator list at 1280 | Looked at in screenshots |
| Phone 375: moment, cast stage and controls, stories, trailers, screenshots | Looked at in screenshots; no horizontal overflow (script) |
| Tablet 768: stories, trailers and the screenshot grid | Looked at in screenshots; no overflow (script) |
| Anchored headings: 6 sections plus the footage, at 1280 and 375 | Measured by script: headings 64 to 66 px below the header, footage flush with the top |
| Viewer: opened the second image, arrow key to the third, counter and caption updated, Escape closed it | Verified by script |
| **Footage:** the player was created, started from 18.5 s, reported "playing" and moved through the sequence; the full-bleed beach and night-highway shots were seen | Verified while the browser pane was visible |
| Footage, hidden pane | While the pane or tab is not visible the page deliberately does not start playback (document is hidden), which was observed and is the intended behaviour |

Before and after screenshots were saved to a Git-ignored `review/round3/` folder. They contain Rockstar's artwork and are not committed.

### Problems found and fixed in this pass

| # | What failed | Cause and fix | How verified |
|---|-------------|---------------|--------------|
| 1 | YouTube showed "Video player configuration error 153" when the player was opened directly | It requires a referring page. It is created only inside the site, which keeps `strict-origin-when-cross-origin` | Played in a page |
| 2 | The player showed the video's own thumbnail and play button instead of the footage | The page treated a cued player (clock at 18.5) as playing. The player is now shown only when its state is really "playing" | Scripted state check and screenshot |
| 3 | First play call after load was ignored | Called too early. The video is now cued at the exact start and played from the cued event | Scripted state check |
| 4 | Anchored sections landed 86 px below the top with 150 px of padding above the heading | The scroll offset was positive. Now negative, so the heading is 66 px below the header | Measured |
| 5 | An old test expected the mosaic markup, and a 0.68rem label broke the new readable-floor test | Test updated; label raised to 0.72rem | pytest |

### Not verified or still open

* **The footage is not a local file and not under a licence.** It plays from Rockstar's own YouTube upload through YouTube's embedded player. Rockstar offers no download of the trailers, so a local clip would be an unauthorised copy. YouTube's interface (a pause mark when paused) cannot be fully hidden, and the sequence is a stretch of Rockstar's own edit rather than one unbroken take.
* **An Extended Look could not be used or reviewed:** YouTube marks it age-restricted, which blocks embedding.
* **Resolution** of the stream is chosen by YouTube for the screen and connection. It reported 720p at the 1280-wide test window; the source quality was not independently measured.
* Autoplay with a real, visible window on a phone was not exercised; the reduced-motion path (a still and a button) was.
* **The owner's development database is unchanged** and needs no migration for this round.
* **Not pushed:** the sandbox cannot authenticate to GitHub.

---

## Phase 2 refinement, round 3 follow-up (2026-10-11)

### Test results (real MySQL 8.0.46 service, `gta6_vi_test` database only)

```
python -m pytest -q
(see the final run recorded in the report)
```

New regression checks (all in `tests/test_pages.py`): reel timing (3 to 5 s a person, contiguous, ordered), the loop builder's constants, the locally built manifest when it exists, the cast script seeks one buffered reel and holds, an explicit choice is never overridden by the automatic start, the footage has no text pills and one clear sound control, the player stays hidden until settled and is never cropped, condensed caps on display titles, image `sizes` and the 2560 candidate, and full-width detail galleries with no empty cells.

### Browser verification (built-in browser, test database, port 5057)

| Check | Result |
|-------|--------|
| Reel from the initial state: "Play whole reel" pressed on load; started at 0 s and ran through; the highlighted name followed the footage (Cal at 8.8 s to 9.8 s, Boobie Ike from 10.5 s) | Verified by script and screenshot |
| Choosing a person: the caption and name changed at once, the video sought to that person (Real Dimez 17.5 s), played to 20.92 s and held; the button read "Replay" | Verified by script |
| Replay restarted from 17.5 s; "Play whole reel" restarted from 0 s; choosing Cal Hampton seeked to 7.0 s and left the reel button unpressed | Verified by script |
| Footage: with autoplay off (the pane asks for reduced motion) the section shows the still and a "Play the footage" pill; pressing it created the player, which played from 18.5 s; after about 3 s of playback the footage dissolved in with no YouTube interface visible; "Enable sound" and a pause icon were the only controls | Verified by screenshot and script |
| Detail pages: Jason Duval gallery (12 images in two runs of six), vehicle gallery, garage page, the caps titles and the card radii | Looked at in screenshots |
| Image sizes: duo panels now request the 1920 candidate (about 1305 px of image for a 561 by 701 panel) | Measured by script |

Before and after screenshots are in the Git-ignored `review/round3-followup/` folder.

### Problems found and fixed in this pass

| # | What failed | Cause and fix | How verified |
|---|-------------|---------------|--------------|
| 1 | The first time the stage scrolled into view it restarted the reel over the visitor's choice | The automatic start did not know about an explicit click. Any explicit choice now sets a flag the automatic start checks | Scripted, and a regression test |
| 2 | Under throttled frame callbacks the video ran past the end of a person's segment, showing the next person under the wrong caption | The hold depended on one frame loop. Now enforced from the frame loop, `timeupdate` and a timer, and snaps back | Scripted before and after |
| 3 | A black flash when the reel started | The video was shown on the first `playing` event, before a frame was presented. It now waits for the first presented frame | Screenshot |
| 4 | A player created while its frame was hidden could sit idle | `tick()` asks again every 2 s while playback is wanted | Scripted |
| 5 | Selecting a person fetched a separate file | One reel is buffered once and seeked | Measured |

### Not verified or still open

* **A native, interface-free trailer background is not achievable compliantly.** The trailers have no download and no licence, and Rockstar's own player is the same YouTube embed. The strongest compliant result is what is built. YouTube's interface shows a pause mark if the visitor pauses (the page puts its own still back instead) and cannot be removed.
* Autoplay with a real, visible window on a phone was not exercised; the reduced-motion path was.
* **Sound** was not audibly checked; the control was verified to toggle the player's mute state.
* Rockstar's own pages could only be reviewed while the pane was visible; some lazy images were not loaded in the screenshots.
* The owner's development database is unchanged and needs nothing for this round.

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


## Stages 3 to 5: admin, polish, search, final checks (October 2026)

Figures below were measured on the project's own machine: Windows, MySQL 8.0.46, headless Chrome, the `gta6_vi_test` database only. The production database was never opened.
A complete run of the suite takes 31 to 36 minutes (one test, `test_garage_pointer.py`, takes 12 to 14 minutes by itself).

| Point | Result |
|-------|--------|
| Stage 3: administrator area for Stories and Places | `tests/test_admin_*.py`; browser journey `scripts/qa/run_admin_qa.py`, 104 checks per run (normal and reduced motion) |
| Stage 4A (accessibility and error pages), `62d63d7` | 659 targeted tests; 40-page probe (20 pages at desktop and phone width): 0 broken images, missing alt text, heading skips, failed requests, console errors or overflow |
| Stage 4B (search and command palette), `8ed0a61` | **Full suite: 1,749 passed, 0 failed, 0 errors, no skips, no warnings, 36 min 10 s.** An earlier run of the same code before one label was renamed had 1 failure (a text collision with an existing guard), fixed without changing that test |
| Stage 4B browser suites, all 0 failures | palette 67, `/search` page 50, home 53, characters hero 36, music 48, regions 246, vehicle detail 227, screening 112, cast navigation 52 |
| Stage 5 audit, `96987fd` | `docs/STAGE5_AUDIT.md`: 140 page-and-width measurements, 322 hostile requests, every route with every method, database integrity, documentation links |
| Stage 5.1: HEAD requests (finding M1) | `tests/test_head_and_methods.py`, 16 tests: 8 failed on the old code, 16 pass on the new; with the 22 other files that touch accounts, throttles, favourites, admin and security, 627 passed |
| Stage 5.2: admin browser script | `run_admin_qa.py` 97/104 before, 104/104 after (normal and reduced motion); `run_accounts_qa.py` 74/74 |
| Stage 5.4: HTTP headers | `tests/test_http_headers.py`, 36 tests (405 `Allow`, HSTS, `robots.txt`); removing the code makes 17 of them fail |
| Stage 5, final full suite and browser QA | recorded here when the final run has finished |

Known flake, reported separately from failures: `scripts/qa/garage_transitions_qa.mjs` has one timing check (the picture must start changing within 250 ms) that fails when the machine is busy (2 failures in 4 runs, 22/22 on the others) with no garage code involved.
