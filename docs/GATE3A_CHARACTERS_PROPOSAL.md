# Gate 3A: Characters page, audit and two concepts

Status: **proposal only. Nothing in the application has been changed.** Awaiting the owner's choice of concept.
Evidence: `review/gate3a/` (screenshots, two clickable prototypes, the data they use) and `Team-Valkyrie-Gate3A-Characters-Concepts.zip`.

## 1. Audit of the current page

Measured on the running site at 1440 and 390 px, every character page opened, and the database queried directly.

### The landing page (`/characters`)

| Finding | Evidence |
|---------|----------|
| **It is a database listing in a nicer coat.** Page banner, a filter form that is the first thing under the title, then three stacked blocks: two big cards, a 3-column grid of six portrait cards, and a plain table of "Original characters". | `audit/index-desktop.jpg` |
| **The filter form leads the page.** Search, Show, Region and Sort sit above the content they filter, so the first impression after the banner is a form. | same |
| **The banner crops the leads' faces.** The motel artwork is cut at the top, Jason's head is lost and the title sits across Lucia. The page opens on a crop, not on the pair. | same |
| **Two tiers exist but barely read as two.** The leads are two equal tall cards; the six others are the same card shape, smaller. No change of scale, rhythm or pace between the tiers. | same |
| **Repetition.** Six identical portrait cards: name, role, one line. Nothing tells you who connects to whom. | same |
| **Invented people are public.** Delia Marsh, Nico Brandt and Tomas Reyes-Hall are listed under "Original characters" with a "Concept" badge, and the status filter exposes "Fan view" and "Original concepts". | same |
| **Phones: a 6,100 px column of near-identical full-height cards.** | `audit/index-mobile.jpg` |

### A character page (`/characters/<slug>`)

| Finding | Evidence |
|---------|----------|
| **Narrow, left-heavy layout with a large empty right and bottom.** One 600 px column of text, a one-line "Connections" list on the right, then a gallery. | `audit/cal-desktop.jpg` |
| **The motion clip is the weakest thing on the page.** The loop is a 16:9 frame built for the reel (a square clip flush right over a blurred extension), so the profile shows half a frame of blur. A browser-default "Pause" button sits under it. | same |
| **Facts repeat.** The role appears in the eyebrow, in the hero and again as "Role"; "Official" and the source link follow. | same |
| **The same five artworks and four screenshots appear on both leads' pages** (shared media), so the two profiles feel like one. | `audit/jason-desktop.jpg` |
| **Stories, Places and "Seen alongside" are empty for every official character**, because every mission in the database belongs to the original characters. An official profile therefore has one or two connection rows and nothing else. | database |
| **Original characters have full profile pages** reached from the list, from regions (3 pages), locations (8 pages) and stories (5 pages), and through `/api/v1/characters`. | exposure map in section 6 |

### What the data can honestly support

* Eight official people. Text is short: summaries 45 to 82 characters, biographies 90 to 294 characters.
* Relationships recorded: Jason with Lucia, Brian and Cal; Boobie with Dre'Quan. **Real Dimez and Raul Bautista have none.**
* Images are good: every official person has landscape official artwork and two screenshots; Jason has 14 images and Lucia 15 (many shared).
* Motion: Rockstar's clips are **1 to 1.5 s long**; Jason and Lucia are 16:9 (3840 x 2160), the other six are **square** (2160 x 2160). Our per-person files are 2.6 to 3.1 s (the clip, then the artwork held).
* Nothing may be invented. Where the data is thin, **the pictures and the layout must carry the page**, not new prose.

## 2. Benchmark: Rockstar's People and Places

Read again this session (`/VI/only-in-leonida`) and against `docs/DESIGN_BENCHMARK.md`.

* One long editorial scroll (about 43,000 px). Each person gets a multi-screen spread: a **name in condensed caps**, a **one-line hook** in the accent colour, one paragraph, a **pull-quote**, a second short beat and an "Explore a place" link.
* **Large, uncropped screenshots** with generous dark margins; text sits in a narrow column opposite the image; pieces overlap.
* The two leads are **the opening act** (a full viewport each); the supporting cast follow at a calmer scale.
* Motion is per-person and brief; typography does the rest.

Where we differ and must: our data has no quotes or hooks (we will not copy Rockstar's copy), we have far less text, and our site carries a **database layer** (relationships, joins, search) that Rockstar's does not.

## 3. Why the current page feels generic (diagnosis)

1. No change of scale: everything is a card of one size.
2. No composition: image always fills the card; text always bottom-left.
3. Controls before content: the form sits in front of the people.
4. Information without a story: connections are a list, not a visible fabric.
5. Images chosen by a query, not framed by a designer (heads cropped, a blurred half-frame).

## 4. The two concepts

Both keep the Team Valkyrie identity (sunset palette, Barlow Condensed caps, Manrope reading text, pink pill action), use only official pictures, and keep search and filters in a secondary **Explore** panel. Prototypes: `concept-a.html`, `concept-b.html`.

### Concept A: "Spreads" (editorial scroll)

An opening on Jason and Lucia, then one **spread** per person. The leads each get a near-full-viewport spread with a tall portrait crop, a second frame overlapping it, large name and the story text; a wide "Partners" band joins them. The six others are alternating (image left, image right) spreads at a calmer scale: wide artwork, a small overlapping screenshot, a square motion tile. A quiet dot rail shows where you are; an "Everyone at a glance" index and the **Explore and filter** panel close the page.

* Reading: **linear and cinematic**; closest to Rockstar's pacing but entirely our composition.
* Leads vs supporting: scale, a "The leads" / "Around them" split, a different layout family.
* Database: each spread's connection chips are real relationship rows (type and person).
* Motion: the person's clip plays **once** when its spread is in view, then rests on the held artwork (no looping of a 1-second clip); one video at a time using the existing coordination.
* Phone: each spread stacks (4:5 image, name, text, chips, pill); the second image is dropped; the index becomes a sticky name strip.

### Concept B: "Cast select" (interactive stage)

One screen that behaves like a character-select: a numbered **roster** on the left (the two leads marked and separated), a large feature picture in the middle, the story, connections and motion on the right, a **filmstrip** of that person's pictures underneath. Choosing a person swaps everything in place. Below the fold: **"Who knows who"**, a graph drawn from the relationship rows, with the unconnected people shown dimmed and labelled honestly, then a "The faces" mosaic.

* Reading: **exploratory and compact**; the whole cast is one decision away.
* Leads vs supporting: a divider and a LEAD tag in the roster, a larger feature.
* Database: the graph is a visual join of `character_relationships` (strongest academic story).
* Motion: the clip in the right panel plays when its person is selected, once.
* Phone: the roster becomes a horizontal chip row, the feature and text stack, the graph becomes a list of "A to B, type" rows.

### Comparison

| | A: Spreads | B: Cast select |
|---|---|---|
| First screen | Jason and Lucia, full bleed | A working cast stage |
| Feels like | A premium game-world feature | A game menu |
| Image presence | Very large, many pictures per person | One large picture at a time |
| Distinguishing the leads | Layout family and scale | A tag and a divider |
| Database visibility | Chips per person | A relationship graph |
| Phone | Excellent (natural stacking) | Good (roster chips, one stage) |
| Scroll length | Long (about 8,000 px desktop) | Short (about 3,000 px) |
| Risk | Length with thin text | Less cinematic; depends on JavaScript for the stage |

## 5. Recommendation: Concept A, with B's relationship graph as its closing section

* The brief asks for an **immersive editorial experience**, alternating image/text, strong cinematic opening and a premium phone layout. A is exactly that; B is a good tool but not an immersive page.
* The data is **thin in text but rich in pictures**. A gives every picture room; B shows one at a time.
* A degrades gracefully without JavaScript (it is plain stacked content); B's stage needs script.
* B's relationship graph is the best **academic** demonstration, and it fits as the final section of A ("Who knows who") without competing with the spreads.
* The detail pages then follow A's language: a cinematic hero, a two-column story with a square motion tile, a connections panel, a wide gallery with different compositions, and "next person" navigation.

## 6. Backend functionality that must be preserved (exactly)

**Routes and templates**
* `GET /characters` and `GET /characters/<slug>` (blueprint `pages`, `site.character_index`, `site.character_detail`); the templates may change, the routes and view-model keys may not break other pages.
* `GET /api/v1/characters` and `GET /api/v1/characters/<slug>` (JSON, validation errors, pagination envelope).

**Data and SQL (all parameterised, in `app/repositories/characters.py`)**
* `search()`: `LIKE` search over name, alias and role with `ESCAPE`; `status` and `region` filters (region via the `LEFT JOIN locations ... LEFT JOIN regions`); the three whitelisted sorts (`name_asc`, `name_desc`, `newest`); `COUNT(*)` for pagination; `LIMIT/OFFSET`.
* `get_by_slug()` with the home-location and region join.
* `relationships_for()` (`UNION ALL` of outgoing and incoming `character_relationships`).
* `missions_for()`, `locations_for()` (joins through `mission_characters`, `mission_locations`), `costars_for()` (self-join with `GROUP BY`).
* `featured_official()`, `official_relationships()`, `ids_by_slug()`.
* The media layer (`media_characters` links, `covers()`, `for_entity()`, `character_clips()`) and the local clip lookup (`media/clips/<slug>.mp4/.jpg`).

**Behaviour**
* Server-side search, filters, sort and pagination through query-string parameters (usable without JavaScript).
* Validation (`validation.py`) and 404 for an unknown slug; `?status=` accepted by the API.
* Every record keeps its `content_status`, `source_url` and `source_note`; official pages keep their visible source link.
* Foreign keys and all rows, including the three original characters, stay in the database.

**Tests** that must keep passing or be updated deliberately: the characters pages, the filter and pagination tests, the API tests, the design-token lint, the width sweep.

## 7. Removing the three invented characters from the public site

Measured today (every route requested): Delia Marsh, Nico Brandt and Tomas Reyes-Hall appear on **21 public pages** (plus their three API detail endpoints):

| Where | Pages |
|-------|-------|
| `/characters` list and its `status` filter | 1 (+ filter options Fan view and Original concepts) |
| Their own profile pages | 3 |
| Region pages ("characters based here") | 3 (Grassrivers, Port Gellhorn, Vice City) |
| Location pages ("residents", "seen here") | 8 |
| Story (mission) pages ("cast") | 5 |
| `/api/v1/characters` list (and `/api/v1/characters/<slug>` for each of the three) | 1 (+3) |
| Homepage | none (the cast is already official only) |

Proposed approach (no row is deleted, no foreign key changes):

1. A single rule at the repository layer: public character queries return `content_status = 'official'` only. The list, detail, regions, locations, stories and the co-stars query all go through it, so the names cannot leak by a missed template.
2. The three profile pages return 404 publicly.
3. The "Show" filter loses the Fan and Original options (it keeps Region and Sort).
4. The data stays queryable for the DBMS demonstration through the SQL files and a documented switch (below).

**Decisions needed from the owner**
* **A. Stories that name them.** Five story pages (Harbour Lights, Last Call Smokestack Row, Ledger of Favours, Quiet Water, Ridge Run) are the original characters' stories. Recommended: keep the stories (they are labelled as ours) and show their cast as **plain, unlinked names marked "Original character"**, so the stories still make sense; alternative: hide the cast block.
* **B. The JSON API.** Recommended: default to official only and allow an explicit `?include=original` for the academic demonstration, documented in `docs/ROUTES.md`; alternative: official only with no switch.
* **C. Data enrichment (optional).** Real Dimez and Raul Bautista have no relationship rows, although the biography text says Dre'Quan signed the duo. Adding one official relationship row (sourced from the existing text) would connect Real Dimez into the graph. Not required; needs a migration and the owner's approval.

## 8. Implementation plan once a concept is chosen

1. Public-visibility rule and tests (the removal above).
2. Landing page and the Explore panel (server-side form, usable without JavaScript).
3. Profile template with variable compositions.
4. Motion: per-person clip, played once per entry, through `window.tvMedia` (one video at a time, the motion policy, paused off screen).
5. Tests, width sweep, desktop/tablet/phone screenshots, and a review ZIP; stop for approval.

Not touched: the homepage hero, the three cinematic moments, the garage, regions, trailers, the database schema.
