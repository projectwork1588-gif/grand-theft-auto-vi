# Architecture

## The big picture in plain English

A visitor's browser asks Flask for a page or a JSON answer. Flask hands the request through **three layers**, each with one job:

```
Browser
  |  HTTP request
  v
Blueprint (app/blueprints/)      "What was asked?"      reads the URL + query string, returns HTML or JSON
  v
Service   (app/services/)        "Is it allowed? How should it look?"   validates input, applies rules, shapes the result
  v
Repository(app/repositories/)    "Ask the database."    the ONLY place SQL is written (always parameterized)
  v
app/db.py -> connection pool -> MySQL (InnoDB)
```

Why three layers? You can explain each in a viva in one sentence, tests can target each layer, and a SQL mistake can only live in one folder.

Phase 2 added `services/site.py`, which builds the **page view-models**: it calls the same services as the API, then adds related content and media. A page and its API endpoint therefore read the same data.

## Key decisions

| Topic | Decision | Reason |
|-------|----------|--------|
| App creation | Application factory `create_app()` | Tests build their own app pointed at the test database. |
| Config | Environment variables via `.env` (`python-dotenv`) | No secrets in Git. |
| DB driver | `mysql-connector-python`, pure-Python mode, lazily created connection pool | Required stack. The app can start and show a clear 503 when MySQL is down. |
| SQL safety | Values are always bound parameters. User input never becomes SQL text. Sorting uses whitelist dictionaries. LIKE wildcards are escaped. IN lists are built from a count of `%s` marks. | Prevents SQL injection (tested). |
| Slugs | Pages and API require lowercase `a-z0-9-` slugs and return 404 otherwise, before touching the database | MySQL's collation ignores case, so `Jason-Duval` would otherwise be a second URL for the same record. |
| Errors | JSON for `/api/*`, a styled page otherwise. Database errors become a generic 503. | No SQL or credentials leak (tested). |
| Test safety | Config refuses to run tests on a database not ending in `_test`. | A test can never wipe real data. |
| Accounts | Website account is DML-only. A separate migration account does schema work. | Least privilege. |
| IDs in URLs/JSON | Public slugs. Internal numeric IDs are not exposed. | Cleaner URLs, less enumeration. |

## Frontend (Phase 2, refinement round 2)

**Stack:** HTML5, CSS3, vanilla JavaScript, Jinja2. No framework and no library. Two scripts: `boot.js` (one line, marks that JavaScript works) and `site.js` (progressive enhancement only). Every page works without JavaScript.

**What `site.js` adds:** the mobile menu, scroll reveals, a hero that drifts slower than the page, the chapter waypoint (a small dial that lists the sections of the homepage), the cast stage, the region explorer, the garage showroom controls, scroll-aware muted loops on profiles, the trailer and image dialogs, and image-failure fallbacks.

**Design system.** A late-afternoon Florida palette (near-black aubergine, hot pink, sunset orange, gold, a touch of Gulf teal). Type is Manrope for text and headings, Barlow Condensed for the VI mark and numerals, and Newsreader italic for one-line ledes. Fonts are bundled in `static/fonts/` (SIL OFL), so no request leaves the site for type. Headings are sentence case and tight, not all-caps. Tokens live in `static/css/site.css` (with header, footer and waypoint), reusable pieces in `components.css`, page layouts in `pages.css`. The Jinja files `_components.html` (labels, image frame, showroom slide, pager, provenance line, page hero), `base.html` and the page templates form the component layer.

**Distinct layouts, not one card grid repeated:**

| Section | Layout |
|---------|--------|
| Leads | Two matched 4:5 panels, same crop logic, same type |
| Cast | One stage with a numbered name list. A 9-second muted reel plays through and the list follows it; choosing a name holds on that person's loop |
| Regions | A full-width explorer: one large view at a time, six tabs underneath. Hover, focus or tap to preview, choose to enter. On the regions page, six alternating full-viewport features |
| Garage | A scroll-snapping showroom of wide slides (home) and alternating image and text rows (garage page) |
| Stories | Numbered rows over a blurred city backdrop, with a "who knows whom" column |
| Watch | One large trailer card and two smaller ones, then an asymmetric screenshot mosaic |
| Places | Numbered index list |

**Content labels.** Every record shows a quiet *Official*, *Fan view* or *Concept* label whose meaning is in its text, never colour alone. Detail pages end with a single provenance line (the source link for official records, "A Team Valkyrie original." for concept ones, with a link to the label guide on the About page). Lists no longer repeat a label on every row when the whole page is concept content: the page lede says it once.

**Accessibility.** Skip link, semantic landmarks, one `h1` per page, labelled search forms, visible focus rings, `aria-current` in the navigation, `role="status"` result counts, keyboard-operable dialogs, a keyboard-operable showroom and region explorer, 44px minimum targets, and `prefers-reduced-motion` support (a still hero, no slideshow, no reveal animation, **no autoplaying video**: the stage shows a still and a Play button).

**Performance.** Responsive `srcset` images at 640, 1280 and 1920 pixels, lazy loading except the hero, no render-blocking JavaScript, no video until a visitor presses play or scrolls the stage into view (and not at all with reduced motion or data saver), one preloaded font file, and a total of about 6 MB of local loops loaded on demand.

## Local video

`scripts/fetch_clips.py` reads Rockstar's published character clips (1 to 1.5 seconds each, 4K) out of its downloads archive with HTTP range requests, so only the eight clips are transferred. `scripts/make_loops.py` turns them into muted 1280 by 720 loops (forward then backward, so they repeat without a jump), a poster for each and one 9-second reel with a `manifest.json` of segment times. `app/local_media.py` serves only `clips/<safe-name>.mp4` or `.jpg` that exist on disk. The folder is Git-ignored. Without the files, every page falls back to official stills.

## Security headers

Every response carries a Content-Security-Policy: styles, fonts and video only from this site, images only from `www.rockstargames.com`, frames only from `www.rockstargames.com` and `www.youtube-nocookie.com` (the trailer overlay, opened only on request), scripts from this site only (since Design Reset Gate 2 no third-party script loads on the homepage), no objects, no framing by other sites. `Referrer-Policy` stays `strict-origin-when-cross-origin`, which YouTube's embed needs (a missing referrer gives player error 153). There are no inline scripts, inline styles or event-handler attributes (tested on every page; the scripts set styles through the CSSOM, which the policy allows). All dynamic text is escaped by Jinja (tested with hostile database values). External links use `rel="noopener noreferrer"`.

## Media architecture

See `docs/MEDIA_INVENTORY.md`. In short: official images and Rockstar's own video player are referenced remotely and only from exact allow-listed prefixes (`app/media_urls.py`). Original fallbacks sit under every image. Missing media never breaks a page.

## Phase 1 review items

1. **Destructive SQL:** `schema.sql` still starts with `DROP TABLE IF EXISTS` for the project's own tables, but no script runs it on a populated database without `--reset` plus a typed confirmation. Phase 2 changes go through a non-destructive migration.
2. **Test isolation:** unchanged. Tests run only against the `*_test` database, and the suite refuses any other name.
3. **Secrets:** `.env` is generated with random values by `scripts.make_env` and is Git-ignored. For production, set `SECRET_KEY` and the database passwords through the host's environment, serve over HTTPS, run behind a production WSGI server (not `flask run`), and add `Strict-Transport-Security`.
4. **Verification record:** `docs/VERIFICATION.md` now records the owner's successful local verification.
5. **Classifications:** unchanged and enforced by a database CHECK (an `official` row must have a `source_url`).

## Issues found while building Phase 2

1. **Migration did not commit.** `migrate_db` ran its INSERTs but never committed, so they were rolled back on close while its own "after" check, run in the same session, looked fine. A test that compares an upgraded database with a freshly seeded one caught it. It now commits and verifies on a new connection.
2. **Reduced motion hid the hero.** A blanket "shorten all animations" rule made the slideshow jump to its final, invisible frame. Reduced-motion visitors now get a still first image.
3. **Imported Jinja macros cannot see context values**, so the pager's helpers had to be template globals.
4. **Case-insensitive slugs** (see Key decisions).
5. **An early image check marked a loading image as broken** because `srcset` had not resolved yet. The check now runs after the page load event.

## Remaining decisions for the owner

* CSRF approach for Phase 3 (a small hand-written session token is planned).
* Whether the use of Rockstar's published media is acceptable without stated licence terms.
* Whether to add `media_vehicles` so official vehicle imagery can be shown without misleading demo records.

## Design refinement pass (Team Valkyrie feedback)

| Feedback | What changed |
|----------|--------------|
| Heavy, awkward hero | Lighter overlays, a tracked "Grand Theft Auto" line over a large gradient VI, the lede cut to one line, and a circular play control. The extra glow layer was removed. The release date sits quietly bottom right and the "as stated on Rockstar's official site" line is gone. |
| Weak brand and header | A gradient-bordered VI mark with a tracked wordmark and a "Team Valkyrie - Fan guide" subline, a transparent-to-solid header, and a Trailers pill. |
| Blunt "fictional demo" wording | Calm labels, one provenance line, no notice boxes, and natural copy for every concept record (migration 003). |
| Weak garage | Only the five vehicles Rockstar names and shows are public, each with real screenshots. The silhouette art was deleted. |
| Plain statistics | Replaced by a full-bleed closing band over official artwork with four large numerals. |
| Typography | Anton replaced by Barlow Condensed at lighter weights, smaller section titles, more generous spacing and a stronger type scale. |
| Official clips and video | Official trailer posters, the on-demand Rockstar player, and one poster-and-link clip card per character. No autoplay background video, for performance reasons (see the media inventory). |
| Responsiveness | Reviewed at phone, tablet and desktop widths. Tablet layouts are explicit: two-column regions, a wide feature plus a 2 by 2 garage grid, and stacked trailers. |

## Round 2 refinement (the 3 out of 10 review)

| Feedback | What changed |
|----------|--------------|
| Awkward Lucia crop, unbalanced leads | Two matched panels. Lucia now uses the official `lucia-caminos-03` still (face and jacket, the LIQUOR sign behind her) and Jason `jason-duval-01`, both at 4:5 and checked side by side at phone, tablet and desktop widths. A "top" focus hint keeps her head in the wide page banner. |
| Six cramped region columns | Replaced by a single wide explorer with tabs, and on the regions page six full-width alternating features. |
| Garage looked like product cards | A showroom: wide slides you swipe, drag or step through, a progress bar, and alternating image-and-text rows on the garage page. |
| Static posters only | A local 9-second muted reel and per-character loops built from Rockstar's own clips, with scroll-aware pause and resume, reduced-motion and data-saver handling, poster and still fallbacks, and a Pause control. Trailers stay on Rockstar's player. |
| Small repeated clip thumbnails | Removed. The cast stage shows the clip large, and each profile has an "In motion" player. |
| Footer pitched the database and linked the API | A short footer: brand, section links, About and Credits, and one line of non-affiliation. The technical note moved to the About page. |
| Robotic and defensive copy | Every page rewritten: no database explanations, no test terminology, no repeated provenance. Editorial copy for characters, regions and vehicles in migration 004. |
| All-caps headings and endless card grids | Sentence-case headings, lists with numbers and rhythm, and a different layout per section. |
| Interactions | Reel stage, region explorer, showroom, chapter waypoint and a hero that drifts. |

## Known limits

* The character clips are only 1 to 1.5 seconds long, so the "reel" is a quick sequence and each loop repeats. Rockstar's trailers cannot be background video: its player has no mute or loop control and the files are 4K and over a gigabyte.
* The loops are Rockstar's content and Rockstar states no licence terms for them. They are never committed and the reel row is marked `permission_required` / `pending_review` in the media table.
* Rockstar's player rendered blank inside the preview browser used for review, so trailer playback was not confirmed there. The iframe is created with the official player address.

## Round 3 refinement (owner review of round 2)

| Feedback | What changed |
|----------|--------------|
| Cursive, italic serif subtitles | Newsreader and every italic removed (the font file too, 146 KB). Manrope throughout: 800 for headings, 400 to 500 for text, a `subtitle` class for second lines, no text under 0.7rem, secondary text at 6:1 or better on the night background. |
| A signature cinematic moment | A full-screen, no-heading section between the leads and the cast. Nine seconds of Trailer 1 played from Rockstar's own upload in YouTube's embedded player (the trailers have no download and no stated licence, so nothing is copied). Candidate comparison and the rights position are in `docs/MEDIA_INVENTORY.md`. |
| "Play whole reel" showed only after switching | Both cast controls are in the markup from the first paint and are never hidden. The script changes their state (`aria-pressed`, label) only. Choosing a person, pressing "Play whole reel" or replaying the same person all start from the beginning, even when autoplay is off. |
| Playlist order depended on the database | `media_slots.CAST_ORDER` is the single order for the name list, the reel's segments and `scripts/make_loops.py`. Tests shuffle the database rows and check all three. |
| Awkward trailers and screenshots | A `theatre` (one lead trailer, two side cards that match its height) and a `bento` of six screenshots in four-column rows (2+1+1 and 1+1+2) that cannot leave a gap. The viewer has previous, next, a counter, arrow keys and Escape. |
| Stories read like a database result | A lead story with larger type, two more as plain rows, every one labelled "Team Valkyrie original", and a separate "Official" panel for Rockstar's character connections. The background image sits under a 93 percent shade. |
| Navigation and hidden headings | The corner dial is now a labelled control ("Jump to | 03 The cast") with the section names in its list. Anchored sections land with the heading 66 px below the header, and the full-bleed footage lands flush with the top. It steps aside for the footer. |
| "Rockstar's first two playable protagonists" | "Jason Duval and Lucia Caminos are the two leads of Grand Theft Auto VI." |

## Round 3 follow-up (benchmark against Rockstar's site)

See `docs/DESIGN_BENCHMARK.md` for the review, the gap analysis and the plan. What changed in code:

| Area | Change |
|------|--------|
| Footage | `signatureMoment()`: pre-roll hidden, reveal after real playback, dissolve in, still returns on pause, one sound pill and an icon pause. CSP unchanged from round 3 |
| Reel | `scripts/make_loops.py` builds one 28.5 s reel (4 s a person, dissolves) with a keyframe at each person; `castStage()` buffers it once and seeks. A chosen person plays once and holds; Replay and Play whole reel are always present |
| Hold safety | The end of a person's segment is enforced from the frame loop, `timeupdate` and a timer, and snaps back if it overshoots |
| Images | `IMAGE_WIDTHS` is now 640, 960, 1280, 1920, 2560; `sizes` follow the real layout, including height-scaled crops (`98vw` for the 4:5 panels, `max(100vw, 178vh)` for the footage poster); lightbox opens 2560 |
| Display type | Names on cards and page banners use Barlow Condensed in caps. Body and large section headings stay Manrope |
| Cards and galleries | `--r-card` and `--r-tile`; a `bento` macro fills rows exactly (runs of six, or an even grid below six) and is used on detail pages |
