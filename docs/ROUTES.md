# Routes and roadmap

## Implemented

### Pages (HTML, server-rendered from MySQL)

| Path | Page |
|------|------|
| `/` | Cinematic homepage: hero, cast, six regions, garage highlights, stories and official connections, media preview, live statistics |
| `/characters` | Poster wall. Query: `q`, `status`, `region`, `sort` (name_asc, name_desc, newest), `page`, `per_page` |
| `/characters/<slug>` | Profile: biography, source, connections, missions, places, co-stars, official images |
| `/vehicles` | Garage. Query: `q`, `category`, `status`, `sort` (name_asc, name_desc, category, newest), `page`, `per_page` |
| `/vehicles/<slug>` | Detail: missions, places, more in the category |
| `/regions` | The six regions in Rockstar's order |
| `/regions/<slug>` | Detail: locations, people based there, stories, gallery, other regions |
| `/locations` | Index. Query: `q`, `region`, `type`, `status`, `sort` (region, name_asc, name_desc, newest), `page`, `per_page` |
| `/locations/<slug>` | Detail: missions, residents, passers-by, neighbours |
| `/missions` | Archive. Query: `q`, `type`, `status`, `sort` (title_asc, title_desc, type, newest), `page`, `per_page` |
| `/missions/<slug>` | Case file: synopsis, cast, vehicles, locations, related stories |
| `/health` | JSON health check (200, or 503 when MySQL is down) |

### JSON API (`/api/v1`)

| Path | Notes |
|------|-------|
| `/characters`, `/characters/<slug>` | Phase 1, unchanged |
| `/regions`, `/regions/<slug>` | Phase 1, unchanged |
| `/vehicles`, `/vehicles/<slug>`, `/vehicle-categories` | New |
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
