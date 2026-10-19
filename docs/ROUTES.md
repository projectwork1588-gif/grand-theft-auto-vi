# Routes and roadmap

## Implemented

### Pages (HTML, server-rendered from MySQL)

| Path | Page |
|------|------|
| `/` | Cinematic homepage: hero, the two leads, cast stage, region explorer, garage showroom, stories and official connections, trailers and screenshots |
| `/characters` | **Official cast only** (Gate 3A). An editorial page: opening, jump bar, the two leads, the six around them, the relationship network. The Explore panel (query: `q`, `region`, `sort` (**cast** (the default on the pages), name_asc, name_desc, newest), `page`, `per_page`) switches the page to a results list. A `status` in the query is ignored, so original characters can never appear here |
| `/characters/<slug>` | Official profile: hero, story with the motion portrait, connections with faces, gallery, previous and next. An original character's slug is a styled 404 |
| `/vehicles` | The Garage: a cinematic landing (an opening that cycles through the seven machines, then the collection told in chapters, the mod-shop strip and the Kayak finale). **Official vehicles only.** Query: `q`, `category`, `sort` (featured, name_asc, name_desc, category), `page`, `per_page`; with any filter, search, other sort or page the collection is an ordered list, exactly as the database returned it. Template `vehicles/concept.html`, service `site.vehicle_concept`. Development-only query: `autoplay=0` stops the opening's clock, `dwell=2..30` sets its hold in seconds |
| `/garage-concept` | **Compatibility redirect** (301) to `/vehicles`, keeping the query string. The Garage's former prototype address; kept so earlier links still work |
| `/vehicles/<slug>` | One machine's page (Stage B): a full-window opening, the database description, a sequence chosen for its pictures (stage pair, viewer, panorama pair, close crops or a labelled scene cut), previous and next, and a way back to `/vehicles`. Template `vehicles/detail.html`, service `site.vehicle_detail`. Concept vehicles return a styled 404 here (they have no public page) |
| `/regions` | Leonida: an opening with an index of the six regions, then each region in Rockstar's order, **each composed on its own terms** (a neon wall of tall pictures, a wide horizon, a feathered overgrowth, a hard diagonal, a dusk with the name cut by the horizon, a frame with a great deal of room), with a compact index that follows the reader (script only) and a note on what is confirmed. Template `regions/index.html`, service `site.region_index`, `regions.css`, `regions.js`; the art direction is `media_slots.REGION_ART`. Counts and shows only Rockstar's pictures and the people its text places in a region; Team Valkyrie's invented places are never counted or shown here |
| `/regions/<slug>` | One region, opened and told its own way: a split window, a wide horizon, a haze, a hard cut, a dusk or a frame (slow camera, off for reduced motion); the database description with its official source beside a picture of the region; the details recorded; official people placed there; Rockstar's screenshots as a contact sheet, a reel, an overgrowth, a diagonal cut, a diptych or a curtain, all opening full size in one viewer; Rockstar's postcard; then the next region with all six as pictures. Places and stories are shown only if they are `official` in the database (today none are: Team Valkyrie's invented ones stay in the database, the API and the Locations and Stories pages, labelled as originals). Template `regions/detail.html`, service `site.region_detail`. Wording of two regions was corrected by migration 007 (`python -m scripts.migrate_db --only 007_region_wording.sql`, after a backup) because Rockstar's pages do not say which character belongs to which region |
| `/locations` | Index. Query: `q`, `region`, `type`, `status`, `sort` (region, name_asc, name_desc, newest), `page`, `per_page` |
| `/locations/<slug>` | Detail: missions, residents, passers-by, neighbours |
| `/missions` | Stories. Query: `q`, `type`, `status`, `sort` (title_asc, title_desc, type, newest), `page`, `per_page` |
| `/missions/<slug>` | Story: synopsis, people, vehicles, places, more stories |
| `/about` | What the project is, what the labels mean, how it was made |
| `/credits` | Attribution, non-affiliation, fonts and licence |
| `/media/clips/<name>.mp4` or `.jpg` | Locally built loops only. A safe-name pattern and an existing file are required; anything else is a 404 |
| `/health` | JSON health check (200, or 503 when MySQL is down). Not linked from the site |

### JSON API (`/api/v1`)

| Path | Notes |
|------|-------|
| `/characters`, `/characters/<slug>` | Phase 1 shape, one behaviour change (Gate 3A): **official characters by default**. `?sort=cast` lists the eight in the Characters section's final presentation order (the default stays alphabetical for the API); `?include=original` is the documented switch that also returns the three original demo characters (for the DBMS demonstration); `?status=demo` needs it (otherwise 400). The detail payload gained a `regions` list (where Rockstar's own text places the person); no field was removed |
| `/regions`, `/regions/<slug>` | Phase 1, unchanged |
| `/vehicles`, `/vehicles/<slug>`, `/vehicle-categories` | New. The API serves the whole table (15 vehicles). Use `?status=official` for the public garage. `sort=featured` gives editorial order. `/vehicle-categories?status=official` counts official vehicles only |
| `/missions`, `/missions/<slug>` | New. Lists include cast, vehicle and location counts |
| `/locations`, `/locations/<slug>` | New |

Pages and API endpoints share the same services, so they cannot disagree.

### Error handling

| Code | Pages | API |
|------|-------|-----|
| 400 | Styled page listing the invalid parameters | JSON `error.details` |
| 404 | Styled page (unknown route, unknown slug, or a slug that is not lowercase `a-z0-9-`) | JSON error |
| 503 | "Database unavailable", with no SQL or credentials shown | JSON error |
| 500 | Generic message | JSON error |

## Planned (not built)

| Phase | Routes |
|-------|--------|
| 3 Auth + admin | `/register`, `/login`, `/logout`, `/me/collection`, `POST /favourites/<type>/<slug>`, `/admin/...` CRUD, relationship editors, statistics |
| 4 Signature | `/atlas` (reuses `/regions/<slug>` and `/locations/<slug>`), `/network`, `POST /api/v1/terminal`, `/search`, `/trails` |
| 5 Media + polish | `/theatre`, wallpaper and screenshot galleries, official vehicle imagery (needs a `media_vehicles` junction), animation pass |
| 6 Final | Integration and security testing, performance, documentation, viva preparation |

Optional features (radio, comparison, economy simulator, news, reviews, activity tracking) wait until all of the above is verified.
