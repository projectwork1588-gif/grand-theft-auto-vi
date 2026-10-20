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
| `/regions` | Leonida: an opening with the six regions to choose from, then one showcase for each region in Rockstar's order (the same composition each time, turned over on every second region: the words on one side, the region's own picture and a second beside it), a compact index that follows the reader (script only), and a closing note on what is confirmed. Template `regions/index.html`, service `site.region_index`, `regions.css`, `regions.js`; the art direction is `media_slots.REGION_ART`. Counts and shows only Rockstar's pictures and the people its text places in a region; Team Valkyrie's invented places are never counted or shown here |
| `/regions/<slug>` | One region, in one shared structure: an opening (the picture on a slant, the words beside it, a slow camera that is off for reduced motion, a numeral switcher for the six regions); the database description with its official source beside a picture of the region (alone for the two regions Rockstar has shown least); the details recorded; official people placed there; Rockstar's screenshots in pairs (a wide one beside a narrow one, then the other way about, an odd last one as a panorama), all opening full size in one viewer; Rockstar's postcard with the credit; then the next region with all six as pictures. What differs between regions is the photography, where the camera rests on it and one accent colour. Places and stories are shown only if they are `official` in the database (today none are: Team Valkyrie's invented ones stay in the database, the API and the Locations and Stories pages, labelled as originals). Template `regions/detail.html`, service `site.region_detail`. Wording of two regions was corrected by migration 007 (`python -m scripts.migrate_db --only 007_region_wording.sql`, after a backup) because Rockstar's pages do not say which character belongs to which region |
| `/music` | Music: the radio stations, the score and the album Rockstar shows on its own Music page, from the database (migration 008), each with its source; no audio, links to Rockstar's own pages. Template `music/index.html`, service `site.music_page` / `services/music.py`. See `docs/MUSIC.md` |
| `/media` | Media, "The Screening": a cinematic presentation of Rockstar's own videos, clips, screenshots, artwork and edition screenshots, in Rockstar's order and under Rockstar's titles. A full-bleed opening on the Launch Trailer, the four films as a crescendo timeline, then chapters in Rockstar's order (Jason and Lucia, the people, the places, key art, clips, the two editions), each with its own composition, about four pictures drawn large, a "View all N" pill beside its heading and the rest as closed thumbnails in the same viewer group, and an ending with the five zip downloads. Deep links: `/media#people`, `/media#places` (a chapter) and `/media#shot-jason-duval-07` (a picture, even one behind View all). From the database (migration 009). Template `media/index.html`, service `site.media_page` / `services/screening.py`, `screening.css`, `screening.js`. See `docs/MEDIA_SCREENING.md` |
| `/locations` | Redirect (302) to `/music`; the old Places index and its filters are retired. The places themselves are Team Valkyrie's own and are kept |
| `/locations/<slug>` | Detail: missions, residents, passers-by, neighbours |
| `/missions` | Stories (no longer in the main menu; Home, place pages and vehicle pages still link to it). Query: `q`, `type`, `status`, `sort` (title_asc, title_desc, type, newest), `page`, `per_page` |
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
