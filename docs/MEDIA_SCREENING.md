# Media: "The Screening" (`/media`)

`/media` replaced Stories in the main menu. It is a cinematic screening of Rockstar's own Grand Theft Auto VI media: its four videos, nine clips, 99 screenshots, 25 pieces of artwork and the 63 screenshots of its two edition collections, set out in Rockstar's own order, under Rockstar's own titles, with every picture and video taken from Rockstar. Nothing on it is invented, and nothing is hosted by Team Valkyrie.

## What the page is

| Part | What it shows | Where it comes from |
| --- | --- | --- |
| Opening | The Launch Trailer's own poster, its date (15 October 2026) and runtime (1:29), a play control that opens Rockstar's own player, and a link to the trailer's page on Rockstar's site | `media_collection_items` (videos), `media_assets` |
| Reel 01, the films | Trailer 1, Trailer 2, An Extended Look and the Launch Trailer, oldest to newest, growing toward the newest; Rockstar's dates, runtimes and descriptions (the description Rockstar gives Trailers 1 and 2 is shown once) | same |
| Reel 02, Jason and Lucia | The first chapter: four pictures drawn large (a wide opening frame and a row of three), a "View all 13" pill beside the heading, and the other nine as thumbnails in a closed disclosure, all thirteen one viewer group | collection `screenshots` |
| Reel 03, the people | Two compositions in one chapter: the two leads side by side (the second set lower), each with a large picture, a row of three and its own "View all 10"; then the six around them as a three-column cast wall, each with its own "View all 4". Each name links to its page on this site | same |
| Reel 04, the places | Vice City large (one tall picture beside two), then the five other regions as small 2 × 2 collages with the place named under them (three across, then two wider), each with its own "View all 6" | same |
| Reel 05, key art | Four of the 25 pieces of Artwork & Wallpapers hung whole and matted at four scales (`SCREENING_ART_HANG`), "View all 25" beside the heading and the other pieces as closed thumbnails, under Rockstar's titles | collection `artwork-wallpapers` |
| Reel 06, clips | The nine clips as posters; each is a link to Rockstar's Videos page, where the clip plays | collection `clips` |
| Reel 07, the editions | Ultimate Edition Benefits (51 screenshots in 19 groups) and Vintage Vice City Pack (12 in 4): for each, four showroom frames (`SCREENING_SHOWROOM`), an index of every group that opens it in the viewer, and "View all" | two collections |
| Reel 08, downloads | Rockstar's five zips, linked on Rockstar's own server, with their sizes | `media_collections` |
| What is confirmed | What the page is and is not, with Rockstar's own Media pages linked | |

Counts on the page are counted from what the page draws, so they cannot disagree with it. The rail's numbers, the reel numbers and the text that mentions a count all come from the same data.

## Verified inventory (20 October 2026)

Read from Rockstar's own pages (https://www.rockstargames.com/VI/media, `/videos`, `/screenshots`, `/artwork-wallpapers`), from the data each page ships with: every item's title, picture address, size and Rockstar's own card id.

| Collection | Items | Notes |
| --- | --- | --- |
| Videos | 4 | Launch Trailer (15 Oct 2026, 1:29), An Extended Look (27 Aug 2026, 26:48), Trailer 2 (6 May 2025, 2:47), Trailer 1 (4 Dec 2023, 1:31); Rockstar's text for each |
| Clips | 9 | Official Cover Art Animation, Jason Duval, Lucia Caminos, Cal Hampton, Boobie Ike, Dre'Quan Priest, Real Dimez, Raul Bautista, Brian Heder |
| Screenshots | 99 | 15 subjects: Jason and Lucia 13, Jason Duval 10, Lucia Caminos 10, Vice City 12, Ambrosia 6, Leonida Keys 6, Port Gellhorn 6, Grassrivers 6, Mount Kalaga National Park 6, and Cal Hampton, Boobie Ike, Dre'Quan Priest, Real Dimez, Raul Bautista, Brian Heder 4 each |
| Ultimate Edition Benefits | 51 | 19 groups of 1 to 6 |
| Vintage Vice City Pack | 12 | 4 groups |
| Artwork & Wallpapers | 25 | Where Rockstar offers a version with logos, its title says so |

Rockstar's own order is not numeric (the first Jason Duval screenshot is "Jason Duval 07"); the page keeps Rockstar's order and Rockstar's titles.

Videos play through Rockstar's player (`rockstargames.com/videoplayer?id=...&embed`), whose ids are `76orsa95` (Launch Trailer), `rk721912` (An Extended Look), `cpys7u21` (Trailer 2) and `rkoCtr1r` (Trailer 1). Opened in a browser on 20 October 2026, the Launch Trailer's player loaded and showed its play control; the Extended Look's player showed Rockstar's own "Please Verify Your Age" form before playing, so its card says "Rockstar's player may ask you to confirm your age before this one plays" and keeps the link to Rockstar's own page beside it.

Rockstar's zip downloads (sizes by request on 20 October 2026): Clips 120,851,301 bytes, Screenshots 72,255,931, Ultimate Edition Benefits 84,798,839, Vintage Vice City Pack 20,634,035, Artwork & Wallpapers 235,479,862.

Re-check at any time, read-only: `python -m scripts.verify_media` (add `--test` for the test database, `--offline` to skip the per-picture requests). It compares every collection's count, titles, order and picture file names with Rockstar's pages as they are now and requests every stored picture address and zip. Run on 20 October 2026 against the test database: every check passed (191 picture addresses answered, five zip sizes matched).

### Reconciliation with what the database already held

Before migration 009 the database held 114 media rows. Of Rockstar's 187 current stills, 98 were already recorded (the same files: identical file names, which carry Rockstar's own content hash); 89 were not. All 109 stored picture addresses still answered, no stored address was duplicated, and the only rows whose type does not match Rockstar's own grouping are the three video posters Home uses (typed `artwork`), which are not in any Rockstar picture collection. Migration 009 adds the 89 missing pictures plus the Launch Trailer, its poster and the cover-art clip: 92 rows (ids 115 to 206), and records every one of the 200 items of the six collections.

## Local media (`media/`, git-ignored)

Inspected on 20 October 2026: 100 files, 2.91 GB. None of it is used by `/media`.

| Folder | Files | Size | What it is |
| --- | --- | --- | --- |
| `source-videos/trailers/` | 2 | 1.9 GB | `GTAVI_Trailer_1.mp4` (680 MB, 3840x2160, 90.0 s) and `GTAVI_Trailer_2.mp4` (1,253 MB, 166.7 s): Rockstar's trailer masters |
| `source/rockstar/` | 1 | 746 MB | `gta-vi-launch-trailer.mp4` (3840x2160, 89.2 s): the Launch Trailer master |
| `source/` and `source-videos/other-clips/` | 9 + 9 | 117 + 115 MB | The nine clips (1.0 to 1.5 s each; the cover-art animation 32.7 s), in two folders |
| `source/art/`, `source/hero-robbery.png` | 10 | 2.3 MB | Character art used to build the Characters motion portraits |
| `clips/`, `clips/garage/` | 44 | 29.6 MB | Loops, profiles and stills built here from the clips (derived, not Rockstar originals) |
| `cinematic/`, `hero/`, `hero/debug/` | 24 | 33.9 MB | Home's moments, hero layers and debugging images built here |

Provenance, established by comparing each file with Rockstar's live file: all nine clips and the cover-art animation are **byte-identical** (full SHA-256) to the files Rockstar serves; the three trailer masters have **exactly the same size** as Rockstar's files and identical first, middle and last 8 MB. The nine clips exist twice (nine exact SHA-256 duplicates, about 115 MB that could be reclaimed; nothing was deleted). Not present locally: the Extended Look master (about 14 GB at Rockstar), any of the 187 pictures (they are linked, never stored), and the zips.

Decisions: the trailers are never served here, they play in Rockstar's own player. The clips stay poster-and-link: each is only 1 to 1.5 s of 4K at 5 to 15 MB, Rockstar states no licence terms for its media, and `media/` is git-ignored so a fresh clone would not have them. Local files stay out of Git and out of the deployed application.

## Data model (migration 009)

`database/migrations/009_media_screening.sql` (mirrored in `schema.sql` and `seed.sql`) creates two tables and fills them. It is non-destructive and idempotent: no DROP, DELETE, TRUNCATE or ALTER, `ON DUPLICATE KEY UPDATE`, nothing existing is changed.

Three tables were considered:

| Proposed | Decision | Why |
| --- | --- | --- |
| `media_collections` | **Kept** | Rockstar's section names, their source page, their zip and its size, and the date they were checked have no home in `media_assets` (one row per file); code configuration would hide verified facts where no script can check them |
| `media_collection_items` | **Kept** | `media_assets` has no order and no notion of a section; the order Rockstar lists items in, and Rockstar's own title for each, are needed. A video's date, runtime and description are columns here (null for pictures) |
| `media_video_details` | **Rejected** | It would hold three facts for four videos. As nullable columns of the item row they cost no join and no table, and nothing else needs them |

Stored on `media_collection_items`: collection, position (Rockstar's order), media row, Rockstar's title, and for a video its date, runtime, description and poster. The chapter a screenshot belongs to is not stored: it is Rockstar's title without the trailing number, worked out in `services/screening.subject_of`. The new media rows are linked to no character, region or vehicle, so the Characters, Regions and Garage pages are not changed by them.

Applying it to a real database is the owner's step, after a backup. It was applied to the real `gta6_vi` on 20 October 2026, after `backups/gta6_vi_before_009_20261020_215514.dump` (restore-tested on a throwaway server) and a rehearsal on the restored copy: 25 tables became 27 and `media_assets` went from 114 to 206 rows, the original 114 unchanged. For any other database, check first with `--plan` (read-only), then apply:

```bat
.venv\Scripts\python.exe -m scripts.migrate_db --only 009_media_screening.sql --plan
.venv\Scripts\python.exe -m scripts.migrate_db --only 009_media_screening.sql
```

On a database where it has not been applied, `/media` shows a short note that the data is not loaded yet, with that command, instead of an error. To undo, restore the backup; the migration deletes nothing and cannot be reversed by itself.

## Routes, files and what else changed

- `/media` is the one route (`pages.media`, `site.media_page`, `services/screening.py`, `repositories/media.py` additions, `templates/media/index.html`, `screening.css`, `screening.js`). `/media/<path>` stays the local-clip route; no sub-routes were added, so the two cannot collide.
- Art direction (chapter order, which subject links to which page, crop rest point, the clips Rockstar publishes square, the age-gated video) is in `media_slots.py` (`SCREENING_*`).
- The menu's Stories entry became Media (`blueprints/main.py`), which also changes the footer. Stories itself is untouched: `/missions`, `/missions/<slug>`, `/api/v1/missions`, its tables and records, and Home's Stories chapter. Place pages no longer mark a menu entry.
- There is no page-wide contact sheet any more: every chapter has its own closed disclosure of thumbnails and its own "View all", so a viewer never spans unrelated chapters. The programme bar is a single 40 px line of quiet, small labels with a hairline under the current one.
- `site.js`, `base.html` and every frozen page were edited for this page by nobody. The shared dialogs' Close button is drawn outside the dialog's own box, which the dialog clipped, so it was invisible on every page that uses them (Home included); the Media page's browser check found it. A separate follow-up session applied the site-wide fix in `components.css` (`dialog { overflow: visible }` plus a focus outline on `.dialog-close`) and told this session the owner had approved it, Home included; this work did not make or verify that approval, and the fix is outside this page's own files. Until then `screening.css` carried the same rule for `/media` only; that block was removed once the shared fix existed, and `scripts/qa/screening_qa.mjs` checks on this page that the Close button is the topmost element at its place for both dialogs.

## Safety

Every picture is drawn only from Rockstar's own image address (`media_urls.is_official_image`); a video only through Rockstar's own player address (`player_src`); a link leaves the site only if it is https to `rockstargames.com` (or, for a zip, Rockstar's download host `media-rockstargames-com.akamaized.net`), in a new tab with `noopener`. A bad database row therefore shows no picture, no player and no link, and its text is escaped.

## Performance

First load on a laptop-size window: 6 pictures (0.29 MB of images); no picture above 1920 wide, no thumbnail from behind a View all, no video file and no zip; HTML about 247 KB. Length: about 11.5 screens at 1920 × 1080 and 13.3 at 1440 × 900 (from 65,000 px for the first design), about 22 on a phone. Chapter pictures use four `srcset` widths and a matching `sizes`, are lazy, and reserve their space; every chapter's thumbnails are closed until opened (a chapter's sheet loads only its own thumbnails, on request); full-size (2560 wide) pictures load only in the viewer.

Wording note: the project's voice test (`tests/test_pages.py::test_public_pages_read_like_a_site_not_a_test_report`) bans the word "archive" in public copy, so the page calls itself a "screening" and "collection" rather than an "archive". If the owner wants "archive" on this page, that test has to be relaxed for it; it was not.
