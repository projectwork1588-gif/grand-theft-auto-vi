# Routes and roadmap

## Implemented in Phase 1

| Method | Path | Returns | Notes |
|--------|------|---------|-------|
| GET | `/` | HTML | Simple homepage with live row counts from MySQL. |
| GET | `/health` | JSON | `200` when MySQL answers, `503` when it does not. |
| GET | `/api/v1/characters` | JSON | Query: `q`, `status` (official/fan/demo), `region` (slug), `sort` (name_asc/name_desc/newest), `page`, `per_page` (max 50). |
| GET | `/api/v1/characters/<slug>` | JSON | Adds relationships (both directions), missions, and locations reached through missions. |
| GET | `/api/v1/regions` | JSON | Query: `status`. Includes `location_count`. |
| GET | `/api/v1/regions/<slug>` | JSON | Adds locations and characters based there. |

Errors: `400` (invalid parameter, with a `details` object), `404`, `503` (database), `500`.

## Planned (not built)

| Phase | Routes |
|-------|--------|
| 2 Public website | `/characters`, `/characters/<slug>`, `/vehicles`, `/vehicles/<slug>`, `/missions`, `/missions/<slug>`, `/locations`, `/locations/<slug>`, cinematic homepage; `/api/v1/vehicles`, `/missions`, `/locations` |
| 3 Auth + admin | `/register`, `/login`, `/logout`, `/me/collection`, `POST /favourites/<type>/<slug>`, `/admin/...` CRUD, relationship editors, statistics |
| 4 Signature | `/atlas`, `/network`, `/api/v1/network/<type>/<slug>`, `POST /api/v1/terminal`, `/search`, `/trails` |
| 5 Media + polish | `/theatre`, wallpaper/screenshot galleries, animation and responsive pass |
| 6 Final | Integration and security testing, performance, documentation, viva preparation |

Optional features (radio, comparison, economy simulator, news, reviews, activity tracking) wait until all of the above is verified.
