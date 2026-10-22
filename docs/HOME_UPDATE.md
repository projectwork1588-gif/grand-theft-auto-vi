# Home, Characters and Garage update, and a performance pass (21 October 2026)

Six improvements the owner approved, nothing else: the Home hero's camera, a replacement for the Home "Tales from the Waterfront" section, an official release block at the end of Home, a better Characters opening picture, calmer Garage scene changes, and measured performance work. It is not a redesign: every route, API, record and approved layout is unchanged.

## 1. The Home hero's camera (`pages.css`, `site.css`, `site.js`)

**What was slow.** Not a timer and not a loading delay: the artwork's camera. The three layers pushed in by 2.5 to 7 percent over 26 seconds each way, so a face in the pair moved at a median of **0.6 to 0.8 px/s** (17 px in 30 s), which reads as a still picture. The words then took about 2.4 s to settle.

**What it is now.** Two parts that never fight:

* an **arrival**: a 2.6 s decelerating pull from a slightly tighter frame (on `transform`), which gives life in the first second (a face in the pair moves about 29 px/s at the start, easing to rest);
* a **breath**: the slow push-in and back, 12 s each way (10 s on phones), with more depth between layers (sky 1.035, world 1.06, pair 1.095; travel 2, 6 and 12 px), on the separate `scale` and `translate` properties, so the two add up. Measured steady speed: about **2.7 px/s** (3 to 10 s), about four times the old camera and still calm.
* the words settle in about 1.5 s (`rise` .85 s, delays .05 to .7 s).

Not a global speed-up: only the camera and the lockup changed. The timings are the variables `--arrive`, `--dolly`, `--glow` and `--haze` on `.hero__stage`; `site.css` reads the same variables for a visitor who opts in to motion on a reduced-motion system, who now also gets the arrival.

Smoothness and loading: the three layers fade in together once decoded (`is-ready`, at the latest after 2.2 s; without script the stylesheet reveals them after 1.6 s), so the artwork no longer appears layer by layer; the layers are promoted to the GPU only while they move (`will-change` is dropped when the hero is off screen, in a hidden tab or behind a dialog); the camera is paused behind an open dialog (`html.has-modal`, set by `site.js` for both dialogs). Reduced motion: no camera, at rest, as before. An A/B of the reveal gate (7 interleaved runs each) found no systematic cost to first paint (median FCP 512 ms gated, 468 ms open; LCP 680 ms and 772 ms).

## 2. "Tales from the Waterfront" becomes a picture challenge (`home.html`, `home.css`, `home.js`, `services/discover.py`)

**Why not a connections explorer.** The owner suggested weighing a compact interconnected experience. The database was checked first: it holds **3** character-to-region links, **5** official character ties and **no** vehicle-to-region links. A network that connects people, places and machines would be almost empty unless connections were invented, which is not allowed, and the Characters page already has the relationship network. Rockstar's own *picture titles* are the rich verified data: 44 people, 42 place and 21 vehicle pictures, each filed under a name.

**What it is.** "How well do you know Leonida?": five of Rockstar's own pictures, one at a time. Name the person, the place or the machine from four answers; the reveal says what Rockstar files the picture under, a line from the same database rows the Characters, Leonida and Garage pages show, who Rockstar's own text places in that region (the `character_regions` notes), and a link to the site's own page for the answer. A result and Play again follow. It ties all three sections together, sends visitors to the detail pages, uses no new table, subsystem or dependency, and loads one picture at a time.

* Data: `discover.challenge()` builds about 7 KB of JSON (24 people pictures over 8 people, 18 over 6 places, 15 over 7 machines) from `media.collection_items("screenshots")`, `media_slots.SCREENING_LINKS` and the new `media.solo_vehicle_pictures()` (pictures linked to exactly one official vehicle). Pictures are `media_assets` rows Rockstar published; each address is rebuilt in the page from Rockstar's image prefix and checked again.
* Safe: every name is set with `textContent`; the JSON block cannot be closed by a hostile name (`tojson`); only Rockstar's image prefix is ever used; an answer link is followed only if it is one of the site's own paths.
* Accessible: real buttons in a labelled group; right and wrong answers are marked in words ("Right", "Your pick") as well as colour; results are announced (`aria-live`); focus goes to Next picture after an answer and to the question after Next; the picture's alt does not give the answer away until it is revealed.
* Degrades: without script, three plain links; if no picture can be loaded, the challenge steps aside and shows the same three links; if the database cannot ask enough questions, the section is left out. Nothing is requested until the section is within a screen of the window.
* The Stories are not removed. Their routes, records, API and pages are untouched, and the section's last line links to them ("Team Valkyrie's original stories", labelled as fan fiction).

The old section's CSS (`.stories`, `.story-lead`, `.story-row`, `.ties`) was removed from `pages.css`; `.connections` stays because the Characters pages use it.

## 3. The official release block (`home.html`, `home.css`, `media_slots.OFFICIAL_RELEASE`, `discover.release()`)

A compact section between the finale and the closing: Rockstar's official key art (shown whole, credited), "Coming November 19, 2026", the two platforms Rockstar lists, a button to Rockstar's own pre-order page, a button to its editions page, the editions and pre-order bonuses it lists, and the Launch Trailer (opens in Rockstar's own player on a press; no frame is loaded before). A line says it is an unofficial fan project that sells nothing and that the facts were checked on 21 October 2026.

**Verified on 21 October 2026 on https://www.rockstargames.com/VI and /VI/editions** (read with a plain fetch and, for the button, in the built-in browser):

| Fact | Source |
| --- | --- |
| "Coming November 19, 2026" | /VI hero |
| Platforms: PlayStation 5, Xbox Series X\|S ("Plays Best On PlayStation 5" is also shown there; not repeated here) | /VI hero |
| "Pre-Order Now" is a **button** that opens Rockstar's own pre-order chooser, **not a link**: there is no address of its own | /VI (four buttons, no `href`; the page ships a `PreorderDrawer` component) |
| Editions: Ultimate Edition (digital) and Standard Edition (digital or code in box) | /VI/editions |
| Two items marked "PRE-ORDER BONUS": the Vintage Vice City Pack and a free month of GTA+ | /VI/editions |
| The Launch Trailer, 15 October 2026, 1:29 | Rockstar's Videos page (database row) |

**The call to action** therefore links to https://www.rockstargames.com/VI (the page that carries Rockstar's Pre-Order Now), is labelled "Pre-order on Rockstar's site", and a note says why ("it has no address of its own, so this link takes you to that page"). Nothing claims that pre-orders are open in any country; the drawer's contents were not observable in the automated browser and are not described. There is no checkout, no form, no price and no payment field. Every fact is one reviewed setting, `media_slots.OFFICIAL_RELEASE`, with its source in the comment above it; change a fact there, never in the template.

## 4. The Characters opening picture (`media_slots.CHARACTERS_OPENING`)

**History:** `art-jason-lucia-beach` (illustrated key art) was replaced first by `rs-jason-and-lucia-12` (a dark screenshot), which the owner also rejected; the opening is now **`rs-jason-and-lucia-11`**, Rockstar's screenshot "Jason and Lucia 11" (both leads in an open car in sunlight, faces large and whole). The text below describes the selection; 11 replaced 12 on the owner's second review (see "Phase 1 polish" at the end).

How it was chosen: all 24 rows that show Jason and Lucia were inventoried; the pool that no curated page uses is `rs-jason-and-lucia-05` to `13` (linked to no character, region or vehicle). Screenshots 09, 11 and 12 were rendered in place at 1440, 1920, 820 and 390 px. **12** was chosen on the stated criterion, the best composition for the existing hero crop: the figures sit on the right, both faces are whole and well lit, and the left is clean dark space for the title (11 is a strong, sunlit alternative but puts a windshield frame behind the title; 09 loses Lucia on a phone). Configuration is one line (`CHARACTERS_OPENING`) and the framing another (`CHARACTERS_OPENING_POS`: x% y% for a wide window, and for a tablet or phone, where only about 46 percent of the picture's width is visible, so the phone framing, 64 percent, keeps both faces).

**Provenance:** the row's source is Rockstar's own Screenshots page (https://www.rockstargames.com/VI/media/screenshots), it is item 12 of that collection under that title, `approved` and `embed_permitted`, and `scripts/verify_media.py` (read-only, live) matches it to Rockstar's page. **Reuse:** the file name was searched in the rendered HTML of all 36 pages of the site (every list, character, vehicle, region, story and place page): it appears only on `/characters` (its new opening) and `/media` (Rockstar's complete picture archive, which by design shows all 187 pictures). It is in no `media_characters`, `media_regions`, `media_vehicles` or `media_locations` row and in no other slot of `media_slots.py`. A test pins all of this.

## 5. The Garage's scene changes (`garage_concept.js`, `garage_concept.css`)

**What it was.** A new scene's picture was revealed by animating a `clip-path` frame that started at its own number in the right-hand index and grew to the window: the "box opening". The hold was 2.8 s, the camera's push lasted 4.2 s (so it never finished), and the old scene was hidden on a fixed timer, so a quick second choice during a change left two scenes stacked in DOM order.

**What it is (superseded by "Phase 1 polish" below for the numbers).** A cross-fade: the new scene's picture fades in over the old one (a CSS transition on the scene itself) while the old scene stays beneath it, still moving, until it is covered. The hold (`?dwell=2` to `30` still works), the arrival, the camera's push and the words' timing are listed in the table in "Phase 1 polish". The index number lights at the press and the ring and the scene start together. Rapid input: because the fade is a transition on the scene, a choice made while another scene is still arriving simply carries on from where the picture is; the newest scene is always on top (`--zi`); the scenes it covers are removed when its fade has actually finished (its `transitionend`, or at once if it was already fully in, with a short timer only as a fallback), not on a fixed timer, because a slow device can start a fade late; a change of mind (A, B, then A before B arrives) leaves nothing pending. The seven machines, their order, media, arrows, swipe, keyboard (arrows, Home, End) and reduced-motion behaviour are unchanged.

## 6. Performance

**Method.** Probes (developer tooling kept outside the repository) in a real Chrome (GPU enabled, cache off, one warm-up navigation first because the first navigation in a fresh Chrome stalls about 5 s in this harness), the same server code on both sides: the committed code (`41f1ede`, exported with `git archive`) against the working tree, same database and media, **3 interleaved runs per side**, medians reported. Frame pacing uses `requestAnimationFrame` deltas at rest and during a steady scroll. These are measurements of this machine (a software-assisted headless Chrome on localhost), not promises for every device.

| | Before | After | |
| --- | --- | --- | --- |
| Home, first load (1440): bytes / images | 1,745 KB / 1,482 KB | 1,256 KB / 957 KB | **-28% / -35%** |
| Home, first load (phone) | 1,686 KB / 1,422 KB | 1,197 KB / 898 KB | **-29% / -37%** |
| Characters, first load (1440): requests / bytes / images | 31 / 2,836 KB / 2,545 KB | 24 / 1,320 KB / 1,026 KB | **-23% / -53% / -60%** |
| Characters, first load (phone) | 29 / 2,821 KB / 2,531 KB | 22 / 1,278 KB / 983 KB | **-24% / -55% / -61%** |
| Garage opening at rest: frames over 20 ms (1440) | 8.3% | 0.4% | **-95%** |
| Garage opening at rest (phone) | 12.2% | 0.8% | **-93%** |
| Garage, janky frames during a scene change | 7.4 to 9.7% (p95 33 ms) | 1.9 to 2.7% (p95 16.8 ms) | **about 4 times fewer** |
| Garage, scene changes in 24 s | 9 | 3 | calmer |
| Hero camera, steady speed of a face in the pair | 0.6 to 0.8 px/s | 2.7 px/s, 29 px/s at arrival | |
| Layout shift (Home, Garage) | 0.001 / 0.005 | 0 / 0.0001 | |

**Root causes found and fixed (not arbitrary timing changes):**

1. **Posters for videos nobody had reached.** Every `<video poster="...">` is fetched at once. On Home that was 4 pictures (about 930 KB) for the three cinematic sections and the reel; on Characters 8 portrait posters (about 1.6 MB). Each video is fully transparent until it is live and a still picture (lazy, or the cast stage's own) sits behind it, so the attribute added only cost. It was removed from the three templates. Nothing else changes visually.
2. **Blur that showed nothing.** The dialog backdrop (96 to 98.5 percent opaque) and the solid header (98.5 percent) both applied `backdrop-filter`, recomputed on every frame in which anything behind them moved: the hero's camera behind a trailer opened from the hero, and every scroll frame under the header. Both are now plain backgrounds (the same look).
3. **Ambient motion behind a dialog.** While a trailer or the picture viewer is open, the hero, Characters and Garage cameras are paused (`html.has-modal`).
4. **Standing GPU layers.** The hero's layers are promoted only while moving.
5. **The Garage's `clip-path` reveal and fixed-timer cleanup** (section 5).
6. **Late display font.** The display face (Barlow Condensed 700) is preloaded like the body face, so first headlines no longer swap late.
7. **Trailer dialog.** The player gets a loading state (a shimmer and "Loading the official player..."), a slow state after 9 s that offers Rockstar's Videos page, and the connection to Rockstar's host is warmed only when a visitor reaches for a trailer (pointer, focus or touch). Nothing is contacted by a page nobody interacts with, and the frame is still created only on a press and removed on close.

**Investigated and left alone (with evidence):**

* **The local cinematic videos.** All three play at 30 fps with **0 dropped and 0 corrupted frames** and steady 16.7 ms main-thread frames while playing (1080p H.264, 2.2 to 9.6 Mbps, `faststart`, separate phone versions). No optimised derivative was created because none was shown to be needed; the source masters were not touched. (`imageio-ffmpeg` is available if one is ever required.)
* **Occasional long frames while scrolling past the video sections** (0.8 to 3.6 s in about 1 run in 5, in this headless environment, also present in the baseline at 784 ms). Chrome's Long Animation Frames data attributes every one to *rendering* (no script, no style or layout time), so they are not caused by the site's scripts; they could not be traced further here and may be specific to this machine's rendering path.
* **YouTube and Rockstar's player.** The trailers play in Rockstar's own player inside a dialog: its buffering, codec and decoder choices belong to Rockstar, YouTube and the visitor's network and hardware, and cannot be measured or fixed from here. What this site controls was improved (nothing loads until pressed, a warmed connection, a loading and a slow state, no animation or blur competing behind the frame).
* Animations already use `transform`, `opacity`, `scale` and `translate`; the only layout-property keyframe is the Media opening's overlay bars (approved, absolutely positioned, one time).

## Tests and browser checks

`tests/test_home_release.py` (new), updated `tests/test_pages.py` and `tests/test_media_screening.py`, and `home.css` added to the design-token check. Browser checks: `scripts/qa/home_release_qa.mjs` (the challenge, the release block, the trailer dialog, the hero), `scripts/qa/garage_transitions_qa.mjs` (response time, pacing, cross-fade frame by frame, seven forward and backward, rapid input, keyboard, reduced motion), `scripts/qa/characters_hero_qa.mjs` (the opening picture at six sizes and pixel densities: the right Rockstar file, high priority, sharp, no overflow, a phone not sent the largest file). The Home script runs at the six standard sizes, in normal and reduced motion; the Garage script runs at desktop width and includes reduced motion. Run both against a server that does not set `TV_AUTOPLAY_ALWAYS`.

## Phase 1 polish (21 October 2026, after the owner's browser review)

Two changes only, after the owner rejected the Characters opening picture again and found the Garage too slow to move from one vehicle to the next.

### The Characters opening picture, again: `rs-jason-and-lucia-11`

The dark screenshot 12 was rejected too, so the opening is now **Rockstar's "Jason and Lucia 11"** (https://www.rockstargames.com/VI/media/screenshots, item 11, `rs-jason-and-lucia-11`): both leads in an open car in sunlight, faces large, whole and clearly lit, a sunlit sea behind them. It is a genuinely different look from both rejected pictures (the illustrated beach art and the dark screenshot 12).

* **Chosen after rendering** 06, 09, 11, 12 and 13 in the page at 1440, 1920, 820 and 390 px (and phone crops computed for each). 09 loses Lucia on a phone, 06 makes her small and dark, 13 (the embrace at sunset) is striking but the heading would cross Jason's body; 11 keeps both faces whole at every size.
* **Quality:** Rockstar serves true 3840 x 2160 originals. The hero used to offer at most 2560 px, so on a large or high-density screen the browser stretched it; the hero (and only the hero) now also offers the 3840 px file (`shot(..., wide=true)`). Measured in the page: 1440 x 900 at 1x loads the 1920 file, 1920 x 1080 the 2560 file, a high-density tablet the 3840 file. A phone is now told how much of the picture it really shows (`sizes="(max-width: 760px) max(100vw, 101vh), ..."`), so it loads the 1920 file (about 190 KB) instead of the largest one.
* **Framing:** `CHARACTERS_OPENING_POS = ("100% 20%", "66% 10%")`: on a wide window the right of the picture is kept; on a phone, where only about 46 percent of the picture's width is visible, the 33 to 78 percent slice keeps both faces whole. No overlay, size or crop other than `object-position` was changed; the layout, heading, copy and cast are untouched.
* **Provenance and reuse:** the row is `approved` and `embed_permitted`, linked to no character, region, vehicle or location, in no other slot of `media_slots.py`, and appears (checked in the rendered HTML of all 36 pages) only on `/characters` and on `/media`, Rockstar's complete picture archive. The runners-up are 13 (rs-jason-and-lucia-13) and 09.

### The Garage's scene changes: faster, same crossfade

The owner liked the look and the smooth crossfade but moving from vehicle 01 to 02 took too long. The separate timings, before and after (measured in a real Chrome, 7 choices, medians):

| | Phase 1 (before) | Now |
| --- | --- | --- |
| Crossfade (the picture arriving) | 1,100 ms | **350 ms**, easing `cubic-bezier(.2, .6, .3, 1)` (starts at once, lands softly) |
| Picture first visibly changes after a press | about 100 ms | **about 30 ms** |
| Picture fully in | about 1,100 ms | **about 315 ms** |
| New words: start / all in | 500 to 740 ms in / about 1,300 ms | 100 to 280 ms in / **about 530 ms** |
| Old words fade out | 350 ms | 180 ms |
| Index number lights | at the press | at the press (about 5 ms) |
| Index line grows / accent colour changes | 600 ms / 1,100 ms | 350 ms / 350 ms |
| Automatic hold | 6,500 ms | **5,000 ms** (measured: a change every 5.02 s; the very first version was 2.8 s, which felt too fast) |
| Camera push | 7,600 ms (hold + fade) | **7,000 ms** on its own clock (`PUSH`), at least the hold plus the fade, so it carries on through the whole stay |

Unchanged: the opacity cross-fade (no `clip-path`, no box), the camera's size and drift per vehicle (subtle), the clean-up when a scene's fade really ends, `--zi` stacking, the seven vehicles and their content, the arrows, swipe, keyboard (arrows, Home, End) and reduced-motion behaviour (the plain short fade, and the timings given back to a visitor who opts in). A choice made during another change simply carries on from where the picture is.
