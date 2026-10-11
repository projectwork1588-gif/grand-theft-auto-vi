# Design benchmark: Rockstar's official GTA VI site

Reviewed on 2026-10-11 in the built-in browser at 1440 and 390 px wide, scrolling each page from top to bottom, opening the trailers, and reading the DOM for structure, fonts and video use. Pages: `/VI`, `/VI/only-in-leonida`, `/VI/music`, `/VI/media`, `/VI/media/videos`. Nothing here copies Rockstar's code, copy or branding. These are observations and the principles we draw from them.

## 1. What Rockstar does exceptionally well

| Area | What it does | Evidence |
|------|--------------|----------|
| **One focus per screen** | The hero is a single framed key-art collage, the release date bottom-left, one pink pill ("Pre-Order Now"), platform marks bottom-right. On a phone the same pieces stack and centre. | `/VI` at 1440 and 390 px |
| **A consistent card system** | After the hero everything is a wide rounded art card with a tiny eyebrow, a condensed uppercase title, one line of copy and one pill button. Cards sit in a stack with small, even gaps. | Ultimate Edition, Vintage Vice City Pack, Music, Only in Leonida, Media cards |
| **A distinctive display voice** | A proprietary Art Deco family in four cuts (Regular, Medium, Bold, Condensed Bold). Titles are condensed caps; long copy is large and tinted. | `document.fonts`: ArtDecoRegular 400, Medium 500, Bold 700, CondensedBold 700 |
| **Restrained video** | The home page holds only two muted, non-looping `<video>` elements, unloaded until needed. Trailers are two large poster cards with a centred play disc, opening an overlay that is a plain YouTube embed (`youtube-nocookie.com/embed/QdBZY2fkU-0?autoplay=0&enablejsapi=1`). | DOM of `/VI`, `/VI/media/videos` |
| **Editorial depth where it matters** | "Only in Leonida" is a 43,000 px scroll: each character gets a multi-screen spread with a headline, biography, a caps pull-quote and per-character muted video drawn into canvases (25 `<video>` and 25 `<canvas>` elements). | DOM of `/VI/only-in-leonida` |
| **Always-available primary action** | A persistent "Pre-Order Now" pill sits top-right on every page; the header is otherwise only a mark and a menu. | all pages |
| **Quiet loading** | An outlined R★ on a navy gradient while the page loads, then a fade. | first paint of every page |
| **Music as a product page** | A sticky mini-player bar (previous, play, next, mute, playlist, share), station cards with a "Preview" button, a numbered singles list. | `/VI/music` |
| **Honest, short media page** | Tabs (Featured, Videos, Screenshots, Artwork), item counts, one zip per section, and a single line: "Download and share trailers, imagery, and more." | `/VI/media` |

## 2. Where our site fell short

| Gap | Our state before this pass | Severity |
|-----|----------------------------|----------|
| Footage presented as a player | Text pills ("Pause", "Sound on", "Watch the full trailer") over YouTube's player, whose own title bar and pause mark could appear | High |
| Reel pacing | About 1.1 s per person (9 s for eight) | High |
| Reel framing | Six of eight clips are square and sat centred between blurred side panels, so 44 percent of the frame was a blurred bar | High |
| Choosing a person | A separate file was fetched on demand, so it was not instant | Medium |
| Image sharpness | Tall 4:5 crops used the 1280 px candidate where about 1250 px of height-scaled image is needed; no candidate above 1920 although the service serves up to 3840; wide gallery tiles used a 640 candidate | Medium |
| Display voice | Manrope everywhere; titles on art looked like UI text | Medium |
| Card system | Bands, rows, rails and cards with different radii and gaps | Medium |
| Detail pages | The gallery lived in a narrow column under the text | Medium |
| Persistent action, loader, ending | None of the three | Low (planned, section 6) |

## 3. Principles we adopt

1. One focus per screen, and one action per card.
2. Art leads; text sits on it, short, in a fixed order: eyebrow, condensed caps title, one line, one button.
3. One card family: the same radius, the same gap, the same hover.
4. Condensed caps for names on art; a plain, large sans for reading.
5. Video is rare and earns its place: muted, lazy, paused when out of view, never autoplaying against a visitor's preference.
6. Ask the image service for the size the layout needs, not the size that is convenient.

## 4. What stays uniquely Team Valkyrie

* The sunset palette (aubergine, hot pink, orange, gold) and the VI mark in a gradient border, instead of Rockstar's navy and Art Deco.
* The honest labelling: Official, Fan view and Concept, with a source link on every official record.
* **The database.** Characters, regions, vehicles, places and stories come from MySQL with real relationships. Rockstar's site has no equivalent: our relationship panels and, later, the network view are our own.
* Original stories and places clearly marked as ours.
* The region explorer, the garage showroom and the cast stage interactions.

## 5. What is achievable with our stack and assets

| Idea | Achievable? | Notes |
|------|-------------|-------|
| Condensed caps display titles | Yes | Barlow Condensed is already bundled |
| Unified card radius, gap and hover | Yes | Two CSS tokens |
| Larger, correctly sized images | Yes | Rockstar's image service serves 640 to 3840 px |
| Slowed, held character reel with dissolves | Yes | Built from Rockstar's own downloadable clips with ffmpeg, stays local and Git-ignored |
| Native, chrome-free trailer background | **No** | Rockstar offers no trailer download and states no licence; the only compliant route is YouTube's embedded player (the same one Rockstar uses). See `docs/MEDIA_INVENTORY.md` |
| Per-character scroll-driven video spreads | **No** | Needs full-length official footage and a proprietary rendering approach. We use the eight short clips |
| Persistent pre-order action | Yes, as a link | There is no stable pre-order URL (it is a retailer chooser), so it can only link to `rockstargames.com/VI` |

## 6. Defects found and what was done

| # | Defect | Correction | Status |
|---|--------|-----------|--------|
| 1 | Footage looked like a player | Text pills removed. Player pre-rolls hidden behind an official still so YouTube's title bar fades first. Footage dissolves in only when playing and on screen. One clear "Enable sound" pill, an icon pause button, and a credit line with "Watch the full trailer". The still returns on pause | Done |
| 2 | Reel too fast | Rebuilt: about 2.6 s of slowed, motion-interpolated clip plus a held frame with a slow push-in, 4.0 s per person, 0.5 s dissolves, 28.5 s total | Done |
| 3 | Blurred bars | Square clips now sit flush right with a feathered extension; the caption sits on the left | Done |
| 4 | Not instant | One reel file, buffered when the stage is a screen away, keyframes at each person; choosing seeks and plays, then holds; Replay and Play whole reel are always present | Done |
| 5 | Soft images | `sizes` corrected per layout, 960 and 2560 candidates added, lightbox opens 2560 | Done |
| 6 | Display voice | Condensed caps for names on art and page banners | Done |
| 7 | Card system | `--r-card` and `--r-tile` radii; consistent gaps | Done |
| 8 | Narrow galleries on detail pages | Full-width gallery that fills rows exactly | Done |
| 9 | An automatic start overrode a visitor's first choice | Any explicit choice now wins (found while testing) | Done |
| 10 | The reel could show one person's footage under another's caption when frame callbacks were throttled | Three independent checks (frame loop, `timeupdate`, a timer) and a snap-back to the end of the person's segment | Done |

## 7. Future additions, prioritised (planned, not built)

Ranked by academic value, visual quality and effort. A score of 5 is best; effort is low, medium or high.

| Rank | Addition | Academic | Visual | Effort | Recommendation |
|------|----------|----------|--------|--------|----------------|
| 1 | **Interactive character relationship network** | 5 | 4 | Medium | Build in Phase 4. A force-directed SVG graph fed by `GET /api/v1/characters` plus `character_relationships`, with a new endpoint returning nodes and edges (`from`, `to`, `relationship_type`, `description`, `content_status`). Official edges are teal, concept edges outlined; selecting a node highlights its neighbours and links to the profile. It shows many-to-many relationships, a self-referencing foreign key and a read-only graph query in one view, and no other fan site has it. Add `docs/queries.sql` entries for degree and shortest path |
| 2 | **Compact pre-order call to action** | 1 | 3 | Low | A small pill in the header linking to `rockstargames.com/VI`. Rockstar's own pre-order is a retailer chooser with no stable URL, so we link to its page and say so. Label it as Rockstar's, never as ours, and keep it out of the hero so the fan identity stays clear. An hour of work |
| 3 | **Spectacular closing section** | 1 | 5 | Low to medium | Replace the closing band with a full-viewport official key-art finale (the Jason and Lucia robbery art or the Vice City sunset still), a slow parallax and the release date, then the footer. Reuse existing media rows. Respect reduced motion |
| 4 | **Team Valkyrie loading transition** | 1 | 3 | Low | A 600 ms intro: the VI mark's gradient border draws, then a sunset wipe lifts. Once per session (`sessionStorage`), skipped for reduced motion and on return visits, never blocking content. Pure CSS plus one small script |

Not recommended now: a music page or a sticky player (no licensed audio), and per-character scroll-driven video (no suitable footage).

## 8. Limits of this review

* The preview browser only paints while its pane is visible, so some screenshots were retaken; Rockstar's lazy images did not always load in time. Section order and structure were confirmed from the DOM.
* Rockstar's fonts and artwork were inspected, not reproduced.
