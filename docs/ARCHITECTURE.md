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

## Frontend (Phase 2)

**Stack:** HTML5, CSS3, vanilla JavaScript, Jinja2. No framework and no library. Two small scripts: `boot.js` (one line, marks that JavaScript works) and `site.js` (about 120 lines). Every page works without JavaScript. The script only adds the mobile menu, scroll reveals, the trailer and image dialogs, and image-failure fallbacks.

**Design system.** A late-afternoon Florida palette (deep aubergine, soft pink, sunset orange, a touch of Gulf teal). Type is Barlow Condensed for display and Inter for reading, with system fallbacks. The sunset gradient appears only as a brand device: the hero sky, image fallbacks and the numerals. Tokens live in `static/css/site.css` (with the header and footer), reusable pieces in `components.css`, page layouts in `pages.css`. The Jinja files `_components.html` (labels, image frame, vehicle tile, pager, provenance line, page hero), `base.html` and the page templates form the component layer.

**Distinct layouts, not one card grid repeated:**

| Section | Layout |
|---------|--------|
| Cast | Two large lead panels, then a horizontally scrolling poster rail; the catalogue is a poster wall with some double-width posters |
| Regions | Expanding panels (homepage), alternating full-bleed features (regions page) |
| Garage | A photo mosaic: one large feature tile and four smaller ones, all official screenshots |
| Stories | Numbered case-file rows |
| Locations | Numbered index list |

**Content labels.** Every record shows a quiet *Official*, *Fan view* or *Concept* label whose meaning is in its text, never colour alone. Detail pages end with a single provenance line (the source link for official records, or "Created by Team Valkyrie for this project. Not part of the game." for concept ones). The large "fictional demo" notice boxes of the first Phase 2 pass were removed, and the stored copy for concept records was rewritten so it reads naturally.

**Accessibility.** Skip link, semantic landmarks, one `h1` per page, labelled search forms, visible focus rings, `aria-current` in the navigation, `role="status"` result counts, keyboard-operable dialogs, 44px minimum targets, and full support for `prefers-reduced-motion` (a still hero, no slideshow, no reveal animation).

**Performance.** Responsive `srcset` images at 640, 1280 and 1920 pixels, lazy loading except the hero, no render-blocking JavaScript, no video until a visitor presses play, and system-font fallbacks so text shows before the web font arrives.

## Security headers

Every response carries a Content-Security-Policy: scripts and styles only from this site (plus Google Fonts for CSS and font files), images and frames only from `www.rockstargames.com`, no objects, no framing by other sites. There are no inline scripts, inline styles or event-handler attributes (tested on every page). All dynamic text is escaped by Jinja (tested with hostile database values). External links use `rel="noopener noreferrer"`.

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
