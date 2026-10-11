# Design reset: defect review, audit, system and concepts

Status: **proposal only. No application code was changed for this document.** The owner chooses the direction before any front-end work resumes.

Everything below was measured or observed in this session: the live site at 981 to 1440 px and at phone widths, Rockstar's pages (`/VI`, `/VI/only-in-leonida`, `/VI/music`, `/VI/media`, `/VI/media/videos`), and the One Piece reference project cloned from GitHub and run locally.

---

## 1. Why the last rounds did not work

Three local rounds of polish treated symptoms. The measurements below show the causes are structural.

| Evidence (homepage, 1280 px) | Our site | One Piece reference | What it means |
|------------------------------|----------|---------------------|---------------|
| Distinct font sizes in use | **34**, in steps as small as 0.3 px (11.2, 11.52, 11.84, 12.16 ...) | 22, on a fluid scale | There is no type scale, only many local decisions |
| Distinct text style combinations | 59 | 46 | Fewer, reused styles read as a system |
| Corner radii | **10** different values (2, 10, 12, 13, 14, 16, 18, 24 px, 50 %, pill) | 5, almost all sharp | Cards do not look like one family |
| Accent colours in the UI | Pink, orange, gold, teal, violet | One (straw gold) | The eye has no single colour to follow |
| Spacing | Ad hoc `clamp()` values per section, from 112 to 205 px | Named scale `--space-3xs` to `--space-2xl` | Sections do not share a rhythm |
| Section patterns on one page | Ten (hero, duo, footage, stage, explorer, showroom, band, theatre, bento, closing) | A repeating chapter pattern | Every section is a new design problem |
| Test widths actually exercised | 375, 768, 1280 | n/a | A sideways-scroll bug lived at 901 to 1090 px unseen |

The honest conclusion: **more edits to the current stylesheet will not reach the bar.** The design needs a system first, then sections built from it.

## 2. The six critical defects

### 2.1 The full-screen trailer still feels like an embed

**Cause.** There is no way, with the material we are permitted to use, to make trailer footage a native `<video>`.

* Rockstar offers **no trailer download**. Its Videos page lists Trailer 1, Trailer 2 and An Extended Look as player tiles; the only download is a zip of the cover-art animation and eight 1 to 1.5 s character clips.
* Rockstar states **no licence** for reuse. Its fan-content policy covers non-commercial in-game material and says nothing about trailers.
* Rockstar's own "player" is a thin wrapper: its `videoplayer?id=...` page contains only `youtube-nocookie.com/embed/QdBZY2fkU-0?autoplay=0&enablejsapi=1`. Rockstar's site does not autoplay trailers either: it shows key art with a play disc and opens the embed on demand.
* The YouTube embed cannot be made interface-free by any supported setting. `controls=0` removes the control bar, but the title bar, the pause mark and the logo return on load, hover and pause, and YouTube's rules forbid covering or cropping them.
* An Extended Look is age-restricted on YouTube and cannot be embedded at all.

**What I got wrong.** Round 3 and its follow-up presented the embed as "footage". Whatever we layered over it, visitors still met a player. That was not a defect I could polish away, and I should have said so plainly instead of iterating.

**What can be done**: section 8.

### 2.2 The reel was slowed too far

**Cause.** The follow-up stretched 1.0 to 1.5 s clips to 2.6 s with motion interpolation (about 1.7 to 2.6 times slower), then held a frame. Interpolated slow motion looks floaty and loses the clip's rhythm. The request was a 2 to 3 s presentation, not slow motion.

**Proposal**: original speed, then the character's official artwork. Prototype built and measured: section 7.

### 2.3 The header and identity are generic

**Cause.** The identity is a small "VI" tile plus an all-caps "GRAND THEFT AUTO" with a grey subtitle. It borrows the game's name and says "fan guide" in the smallest text on the page. Nothing says *Team Valkyrie*, and the header has no persistent action or structure of its own. On the hero the subtitle sits on a bright sky at low contrast.

### 2.4 Typography, spacing and transitions have no system

See the measurements in section 1. In addition, sections are separated only by 128 px of empty space or by a hard change of background, so scrolling reads as a stack of unrelated pages.

### 2.5 Header clipping: reproduced and diagnosed

Two separate things produced "clipped" headers. One is a capture artefact and one is a real defect.

| | Finding | Evidence |
|---|---------|----------|
| **A. Capture artefact (not a site defect)** | When the browser is emulated at a width larger than the review pane, the screenshot is cropped to the pane instead of scaled. At 1024 px the frame showed only the left 800 px, so the nav ended at "Characters Garage Le...". The DOM was intact: the brand ended at 281 px, the nav spanned 419 to 921 px, the 138 px gap and the "Watch" button were all present, with no wrapping. Some screenshots I sent were taken that way. | `review/design-reset-evidence/header-capture-cropped-at-1024-emulation.jpg` against `header-intact-at-700.jpg`, and the measured boxes |
| **B. Real defect: sideways scroll from 901 to 1090 px** | The homepage region explorer uses `aspect-ratio: 21/9` with `min-height: 440px`. When the container is narrower than 440 x 21/9 = 1027 px the box widens instead of shrinking, so the whole page overflows. Measured `scrollWidth - innerWidth`: 167 px at 901, 111 at 960, 73 at 1000, 50 at 1024 (an iPad landscape width), 15 at 1060, 0 from 1100. The fixed header does not move, so on scrolling sideways the content slides under it and "text appears clipped". | In-page measurement at 901, 960, 981, 1000, 1024, 1060, 1100 and 1440; offender `.regions__stage` |

Why it was missed: every earlier width test used 375, 768 or 1280. Passing tests never looked at 901 to 1090.

### 2.6 Repeated local changes did not lift overall quality

Each round fixed what the last review named and added new patterns beside the old ones (see the section count above). The page grew from 5 to 10 distinct layouts. A system, not another round, is the remedy.

## 3. Section-by-section audit of the current site

| Section | What is there | Problem | Verdict |
|---------|---------------|---------|---------|
| Header | Gradient-bordered VI tile, caps title, grey subtitle, five text links, "Watch" pill; mobile menu | Generic identity, weak hierarchy, no fan identity, low subtitle contrast on bright art | Rework |
| Hero | Rotating official art, "Welcome, gamers", tracked title, huge gradient VI, lede, two actions, release date | Strong image, but five text styles stacked; two of them are the project's required lines and compete with the title | Rework (keep the required lines, simplify the lockup) |
| Two leads | Two 4:5 portrait cards | The crops are good; cards are a different radius and treatment from everything below | Keep content, restyle |
| Footage | Full-screen YouTube embed | Section 2.1 | Replace |
| Cast stage | Stage plus eight names, reel controls | Concept is right and liked. Reel timing wrong (2.2). The control pair sits on the picture | Keep concept, rebuild timing, move controls off the picture |
| Regions | Wide explorer with six tabs | Good idea; causes the 901 to 1090 px overflow; tabs are tiny | Keep, fix box, enlarge tabs |
| Garage | Horizontal showroom | Works; third distinct card style | Restyle into the card family |
| Stories | Lead story, two rows, connections panel | Clear hierarchy now; a different panel style again | Restyle |
| Trailers and gallery | Theatre plus bento | Layout fine; poster cards use a fourth radius | Restyle |
| Closing | Full-width art with a heading | Plain; no ending | Rework (section 9 of the benchmark) |
| Section navigator | Corner pill "Jump to 03 The cast" | Understandable but it floats over content and duplicates the header | Replace with a quiet progress rail |
| Footer | Brand, links, one disclaimer | Correct; visually flat | Restyle |
| Characters index | Duo, portrait grid, list | Three patterns on one page | Rework into one pattern |
| Character, vehicle, region pages | Banner, two columns, bento | Consistent with each other, not with the home | Rework with the new system |
| Locations, stories lists | Numbered text rows | Read as database listings | Rework as cards with a short image strip |
| About, credits | Plain prose | Fine; typography will inherit the system | Keep |

## 4. Rockstar's principles against ours

| Principle (observed) | Rockstar | Ours today | Adopt? |
|----------------------|----------|------------|--------|
| One focus per screen | Hero is one framed key-art block | Hero carries 8 competing elements | Yes |
| One card family | Same radius, gap, eyebrow, title, line, button on every feature | 10 radii, several card anatomies | Yes |
| Display voice | Art Deco condensed caps for names and titles | Caps only on cards since the last round; headings are sans | Yes, extend |
| Restrained video | Two muted lazy `<video>`; trailers on demand | A live embed as a centrepiece | Yes: remove the embed |
| Persistent action | Pre-order pill on every page | None | Plan |
| Quiet loading | Outlined mark on gradient | None | Plan |
| Editorial depth | Per-character spreads with copy, quote and footage | Profile pages are tidy but small | Partly: bigger banner, better rhythm |
| Honest media page | One line of usage text | Credits page | Keep ours |

From the One Piece reference the owner rated 7 out of 10, what to carry over is **discipline**, not styling: a numbered chapter system ("05 / DOSSIERS"), one accent colour, one display voice, large art, a named section indicator, and a native video of an owned clip in a clean frame. What does not transfer: its video is a user-supplied 7.7 s 1080p clip that the project owns, which is why it can be a plain `<video autoplay muted loop>`. We have no equivalent trailer clip.

## 5. The unified design system

The proposal is one system, used by every page. Tokens below are specifications; nothing is implemented.

### 5.1 Colour

| Token | Value | Use |
|-------|-------|-----|
| `--ground` | `#12102a` | Page background (indigo, nearer Rockstar's navy than our aubergine, but ours) |
| `--ground-2` | `#1a1740` | Raised areas, header when solid |
| `--card` | `#1d1a45` | Card fallback behind art |
| `--ink` | `#f6f1ea` | Headings and body |
| `--ink-2` | `#cfc8dc` | Secondary text (about 9:1 on ground) |
| `--ink-3` | `#9a93b3` | Captions, meta (about 5.9:1, never below 12 px) |
| `--action` | `#ff5f96` | **The only action colour**: buttons, links on hover, the active chapter |
| `--label` | `#ffd47c` | **The only label colour**: eyebrows and chapter numbers |
| `--official` | `#3de0c8` | Status only: the Official badge and the official relationship lines |
| `--line` | `rgba(255,255,255,.12)` | Hairlines |

The sunset gradient is reserved for the VI numeral and one rule under the footer. Orange and violet leave the UI.

### 5.2 Type

Two families only: **Barlow Condensed 700** (uppercase) for display, titles and numerals, and **Manrope 400/600/800** for everything read. No third face, no italics.

| Token | Size | Use |
|-------|------|-----|
| `--t-micro` | 12 px caps, tracking .2em | Eyebrows, badges (never smaller) |
| `--t-small` | 14 px | Meta, captions |
| `--t-body` | 17 px / 1.6 | Reading text |
| `--t-lead` | 21 px / 1.5 | One-line summaries on art |
| `--t-h3` | 33 px | Card titles in text lists |
| `--t-h2` | clamp 41 to 65 px | Section titles |
| `--t-h1` | clamp 52 to 104 px | Page titles, condensed caps |
| `--t-display` | clamp 64 to 140 px | Hero only |

Nine sizes in total, on a 1.25 ratio. Anything outside the scale fails review. Line-heights and letter-spacings are tokens too (`caps-tight .01em`, `caps-label .2em`).

### 5.3 Space and shape

* Spacing scale: 8, 16, 24, 32, 48, 72, 112. Section rhythm is always `--s7` (112 px) with a hairline, never a background change.
* Card gap 16 px; page gutter `clamp(20px, 4vw, 56px)`; content max width 1480 px.
* Radii: **24 px** for cards, **12 px** for tiles, pills 999. Nothing else.

### 5.4 Imagery

* Feature cards are 21:9 (hero and features), 4:3 (pairs), 4:5 (portrait on phones), 16:9 (media).
* Every card has one scrim: a left-weighted gradient (82 % to 15 %) plus a bottom gradient. Text never sits on bare art.
* Request images at 1.5 to 2 times the rendered width, using the service's 640 to 3840 px range; never upscale; the `sizes` hint follows the layout, including height-scaled crops.
* A focus hint per image replaces ad hoc `object-position`.
* No blurred "extension" bars. Square clips are paired with artwork (section 7).

### 5.5 Motion

* Durations 160, 320 and 640 ms; one easing `cubic-bezier(.2,.7,.2,1)`.
* Entrances: opacity and 8 px of travel, once. No parallax except the hero at 0.2.
* Any video: muted, lazy, paused when out of view, never autoplays under reduced motion or data saver, always has a still and a visible control.
* Page transitions: none, apart from the optional loader (section 9 of the benchmark).

### 5.6 Navigation

* Header 72 px. Left: the Team Valkyrie lockup. Right: a text pill ("Trailers") and a menu button. A menu overlay at every width, as on Rockstar's site, listing the five sections plus About and Credits. This removes the 901 to 1090 px header-fit problem for good.
* The header turns solid after the first screen; it never overlaps text with only a gradient (a flaw visible in the concept previews).
* Chapters: numbered `01 / THE LEADS` eyebrows on every home section, and on wide screens a thin left rail with the numerals (replacing the corner pill).
* Footer: three short columns and the single non-affiliation line.

### 5.7 Voice

Short, plain, no database or test language, no repeated provenance. Official and original labels stay, with one provenance line per page.

## 6. Three homepage concepts

Static previews are in `review/design-concepts/` (open `concept-a.html`, `-b.html`, `-c.html` through the preview server) with screenshots in `review/design-concepts/screens/`. They use real project content and official art. They are not wired to Flask.

### Concept A: "Key Art Index" (the Rockstar-grade card system, in our palette)

* One framed hero card; every later section is the same card family (art, eyebrow, condensed title, one line, one pill).
* Identity: a Valkyrie wing-V emblem and a two-line lockup, "TEAM VALKYRIE" over "GRAND THEFT AUTO VI FAN GUIDE".
* Strengths: closest to the bar the owner named; lowest technical risk; maps one to one onto the existing templates and services; easy to keep consistent across 12 page types.
* Risks: could read as derivative if the identity and the chapter numbering are not pushed.
* Effort: medium.

### Concept B: "Night Drive" (immersive chapters)

* Full-screen scenes with oversized outline numerals and a sunset horizon rule that fills as you scroll; the header becomes a ticker ("01 Welcome to Leonida").
* Strengths: the most memorable; closest in spirit to the One Piece chapter system the owner rated.
* Risks: depends on pinned or scroll-driven scenes that need careful fallbacks; hardest to keep legible on phones; most JavaScript; high chance of another overrun.
* Effort: high.

### Concept C: "Case Board" (a relationship-first file)

* The hero is a live board of official characters with their real MySQL relationships as lines; dossiers show role, ties and source, and label what Rockstar has not stated ("Not stated by Rockstar").
* Strengths: showcases the database and relationships, which no fan site has; strongest academic value; honest about missing data.
* Risks: reads as a tool rather than a cinematic guide; weaker emotional pull; leans on a graph view that is Phase 4 scope.
* Effort: medium to high.

### Recommendation

**Build Concept A as the foundation, borrowing two things.**

1. From One Piece and Concept B: the numbered chapter eyebrows and the quiet left rail, which are cheap and are the thing the owner already responded to.
2. From Concept C: the relationship board as the home's "Who knows whom" card now, and as the full view in Phase 4.

Why: it is the only direction that fixes the root causes (no system, no card family, too many patterns) without adding risk, it reuses every template and test, and it is the quickest to judge by eye. B has the highest ceiling but is the riskiest after three misses; C is the best Phase 4 feature but a poor first impression.

## 7. The character reel at original speed

Prototype (outside the app): `review/design-concepts/reel-natural-speed-prototype.mp4` and its contact sheet.

* Each person: the official clip at **1.0 times speed** (1.0 or 1.5 s), a 0.4 s dissolve into the character's **official artwork**, held 1.6 s with a 5 percent push-in. **2.6 s each, 3.1 s for the two with 1.5 s clips**.
* Whole reel 19.7 s, 4.0 MB, 0.3 s dissolves between people.
* No interpolation, no black or blurred bars in the art beat (the artwork is full-frame 16:9; the square clip sits flush right as before, but only for about a second).
* Selecting a person plays their 2.6 s once and rests on the artwork, so the "held frame" is real art and not a frozen video frame.

## 8. Cinematic playback: what is and is not possible

| Route | Native feel | Licensed? | Verdict |
|-------|-------------|-----------|---------|
| Local `<video>` of a trailer excerpt | Perfect (the One Piece behaviour) | **No. No download and no stated licence** | Not without written permission |
| YouTube embed as a page background | Poor: title bar, pause mark and logo return, cannot be covered | Yes (it is Rockstar's own embed) | Keep only behind a click |
| Rockstar's player | The same embed | Yes | Same |
| The cover-art animation from Rockstar's zip | Native | Offered for download, no licence stated | It is a title sequence with an ESRB card, not footage; do not use |
| Eight character clips (local, from the zip) | Native | Offered for download, no licence stated | Use, as now, for the cast only |
| **Official artwork with motion design** | Native, instant | Same position as the rest of our official images | Use for the hero and the leads |

**Recommended solution.**

1. **Remove the embed as a centrepiece.** Do what Rockstar's site does: a key-art card with a play disc that opens the trailer in a theatre overlay. Honest, fast and robust.
2. **Cinematic feel without trailer footage:** a slow, art-directed motion treatment of official stills (a push and a light sweep over the hero art), plus the cast clips. Native, quick, and entirely within what we can show.
3. **Make the slot permission-ready.** Build the hero's cinematic slot as a component with a poster and an optional local MP4. If Take-Two grants permission, the clip drops in with no redesign.
4. **Ask.** Rockstar's policy page directs licensing requests to `copyright@take2games.com`. A short written request for a muted, credited, under-ten-second excerpt for a non-commercial student project is reasonable. The owner decides whether to send it; I will not contact anyone. Until a reply arrives the site must not depend on it.

## 9. Implementation sequence

Gated so that no gate starts without the owner's approval of the previous one, and the Flask, MySQL, API and test foundations stay put.

| Gate | Work | Preserves | Acceptance (owner reviews screenshots) |
|------|------|-----------|-----------------------------------------|
| G0 | Owner chooses concept, identity, palette, the footage route | n/a | A written decision |
| G1 | Tokens (colour, type, space, radius, motion), header lockup and menu overlay, footer, chapter rail, base components | All routes, services, tests | Style tile and header at 375, 768, 1024, 1280, 1440; automated checks that no font size or radius is outside the scale |
| G2 | Home rebuilt from the components: hero, leads, cast with the new reel, regions, garage, stories, trailers and gallery, closing | Services, API, repositories, tests (markup tests updated) | Full-page captures at the same five widths; the sweep below |
| G3 | Inner pages from the same components | Detail data, filters, pagination | Same |
| G4 | Cinematic slot with still and overlay; native-video drop-in kept ready | Security policy narrows (the YouTube script allowance is removed if the embed is overlay-only) | Footage behaviour recorded |
| G5 | Quality pass: copy, contrast, hover, loader and pre-order link if approved | Everything | Sign-off |

### Process changes so this does not repeat

* **A width sweep as a test.** A headless-browser script visits every public route at 320 to 1920 px in steps of 20 and fails on any horizontal overflow, any clipped header and any text below 12 px. It runs with the suite; screenshots are saved for human review.
* **Screenshots taken without emulation artefacts** (a real window, or scaled capture), reviewed at five widths per gate.
* **No "done" without the owner's eyes on the same captures.** Passing tests prove behaviour, not design.
* **Token lint:** a test that fails on any font size, radius or colour not in the system.

## 10. Decisions needed from the owner

1. Which concept: A (recommended), B, C, or A with named borrowings.
2. The identity: approve the emblem and lockup direction, or ask for alternatives.
3. The footage route: confirm the overlay-and-art approach, and whether to send a permission request.
4. Reel: confirm 2.6 to 3.1 s per person with the artwork beat.
5. Whether to keep a section navigator (rail) or drop it.
6. The loader and the pre-order link: now (at G5) or later.

## 11. What I will not do without approval

Change application code, change the database, push, or contact Take-Two or Rockstar.
