# Music (`/music`)

The Music page shows what Rockstar's own Music page shows for Grand Theft Auto VI: its radio stations, the score and the album. It replaced the Locations entry in the menu. Nothing on it is audio, and nothing on it is invented.

## What was verified, and where

Every fact is a database row marked `official`, with its `source_url`, a `source_note` and a `verified_on` date (19 October 2026). The primary source is Rockstar's page, https://www.rockstargames.com/VI/music, read as served HTML (its text, its image addresses and the station-preview data it ships to its player).

| Content | Source | Confidence |
| --- | --- | --- |
| Six stations, in Rockstar's order: Cocoteo FM, Back Country Radio, AfroBank FM, The Chamber, Flash FM, Dirty South Classics | https://www.rockstargames.com/VI/music (station cards and player data) | High. The page's alt text spells one "Afro Bank FM"; its player and image files say "AfroBank FM", which is used. |
| Each station's description and the names beside it ("with Robyn and Alex"), word for word | same page | High |
| The three songs listed for each station's preview (for example "EoO" by Bad Bunny on Cocoteo FM) | same page, the preview player's chapter list | High that Rockstar's preview names them. They are labelled "Heard in Rockstar's preview", never as a playlist. |
| Station logos and banners; the hero, radio and album backdrops; the album artwork; the score's picture; the Justice logo | same page, `/VI/_next/static/media/...` (hot-linked from Rockstar's own image address, never copied) | High |
| The score block: heading "Original Score Spotlight" (this site's own wording; Rockstar's page heads the block "Official Score by Justice", but its text describes one standalone single from the original score composers, so the heading here does not suggest Justice scored the whole game), the standalone single "Flower in a Hurricane" with Tame Impala, SZA and King Gizzard & The Lizard Wizard, and its Listen Now link (https://justice.lnk.to/flowerinahurricane) | same page | High |
| "Grand Theft Auto VI: The Album": 34 original tracks, "Coming November 19" (the page gives no year, so none is shown), the description, and the two buttons (pre-save, pre-order vinyl or CD) | same page | High |
| Label: Atlantic Records | https://www.gtavi-thealbum.com (header and copyright line) | High; named there, not on the Music page |
| Nine singles and their artists, each with a "Play full track" link on `gtavi-thealbum.lnk.to` | same page | High for the list as read on 19 October 2026. Rockstar's store page for the CD (https://store.rockstargames.com/merchandise/buy-gta-vi-album-cd) lists six, so the list changes; the page says so. Two of Rockstar's links start `http://` and are stored as `https://` (the same address; the http one redirects). |

Not used, on purpose: Rockstar's newswire articles about the stations and the album (their body text did not load as readable HTML), the shop section (a store, not music), the preview audio files (see below), and anything about which songs play in the game beyond Rockstar's own previews.

## What is not on the page, and why

- **Audio.** Rockstar's page plays station previews from audio files on its own server. Those files are not offered as an embed for other sites, so the page does not hot-link or host them. Each station links to Rockstar's page to hear its preview; each single links to the label's own "Play full track" page. No control on `/music` is a button: every control is a link that does what it says.
- **Genres, filters, search.** Rockstar gives no structured genre per station, only its description, so there is nothing true to filter on.
- **Original music, fan music.** None. Team Valkyrie's own places, stories and characters are not music and are not touched.

## Data model (migration 008)

`database/migrations/008_music.sql` (mirrored in `schema.sql` and `seed.sql`) creates four tables and fills them. It is non-destructive and idempotent (no DROP, DELETE or TRUNCATE; `ON DUPLICATE KEY UPDATE`).

| Table | Holds |
| --- | --- |
| `radio_stations` | slug, name, hosts, description, logo and banner addresses, order, `content_status`, source, note, `verified_on` |
| `station_preview_tracks` | the songs Rockstar's page lists for a station's preview (title, artists, order) |
| `music_releases` | the score and the album (title, description, release note, track count, label, artwork, up to two buttons, source) |
| `music_tracks` | the album's singles (title, artists, "Play full track" link, whether it is the score's single) |

`radio_stations`, `music_releases` and their checks require a `source_url` for any `official` row, the same rule as the other tables. Only `official` rows are read by the page.

Applying it to the real database is the owner's step (it has **not** been applied):

```bat
.venv\Scripts\python.exe -m scripts.migrate_db --only 008_music.sql --plan
.venv\Scripts\python.exe -m scripts.migrate_db --only 008_music.sql
```

Until it is applied, `/music` shows an honest "the music data is not loaded yet" message with that command, not an error.

## Routes and the old Locations section

- `/music` is the canonical route (`pages.music`, `site.music_page`, `services/music.py`, `repositories/music.py`, `templates/music/index.html`, `music.css`; no script).
- `/locations` is a 302 redirect to `/music`; its old filters mean nothing there and are dropped.
- Team Valkyrie's eight places, their pages (`/locations/<slug>`, still linked from the stories and characters that use them, and marked Stories in the menu), the eight `mission_locations` rows, the three characters' home places and `/api/v1/locations` are untouched. `site.location_index` still exists and is tested.

## Safety

A link leaves the site only if it is `https` to `rockstargames.com`, `www.gtavi-thealbum.com`, `gtavi-thealbum.lnk.to`, `gtavithealbum.lnk.to` or `justice.lnk.to` (`services/music.safe_link`), and opens in a new tab with `noopener noreferrer`. A picture is drawn only from Rockstar's own image address (`media_urls.is_official_image`). A bad database row therefore shows no link and no picture, and its text is escaped.
