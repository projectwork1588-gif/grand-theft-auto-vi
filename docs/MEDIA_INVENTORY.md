# Media inventory

Rules: nothing from Rockstar is downloaded or committed. Official media is **linked or embedded from the official source only
where permitted**. Watermarks and copyright notices are never removed. Anything uncertain is flagged for **human review**.
The database table `media_assets` mirrors this list (`usage_status`, `approval_status`).

| ID | Asset | Intended use | Source | Attribution | Usage status | Local path / embed URL | Human approval needed? |
|----|-------|--------------|--------|-------------|--------------|------------------------|------------------------|
| 1 | Grand Theft Auto VI Trailer 1 | Media Theatre: link to the official trailer | https://www.rockstargames.com/VI/trailer-1 | Copyright Rockstar Games / Take-Two Interactive | `link_only` | none (embed URL **not yet confirmed**) | **Yes** before any embed |
| 2 | Grand Theft Auto VI Trailer 2 | Media Theatre: link to the official trailer | https://www.rockstargames.com/VI/trailer-2 | Copyright Rockstar Games / Take-Two Interactive | `link_only` | none (embed URL **not yet confirmed**) | **Yes** before any embed |
| 3 | Official "Media & Artwork" page | Wallpaper gallery: link out to Rockstar's Media page | https://www.rockstargames.com/VI/media | Copyright Rockstar Games / Take-Two Interactive | `link_only` | none (specific file URLs **not yet confirmed**) | **Yes**, a human must confirm exact URLs and terms |

## Findings

* Checked 2026-10-09: the official site has pages `/VI/trailer-1`, `/VI/trailer-2` and `/VI/media`. The Media page offers videos (3 trailers and 9 clips), screenshots and artwork/wallpapers as downloads (zip bundles hosted by Rockstar). **It states no licence terms**, so a human must review before any use beyond linking. Nothing was downloaded. No embed URL was obtained, so none was invented.
* No local media files exist. `media/` is reserved for original or properly licensed assets, and Git ignores everything in it.
* Phase 5 will use attractive CSS/SVG fallbacks so the site works fully offline when embeds are unavailable.

## Adding a new asset (checklist)

1. Record source URL, licence or permission and attribution here **and** in `media_assets`.
2. Set `approval_status = 'pending_review'` until a human approves it.
3. Never commit large or unlicensed files. Prefer an official embed or link.
