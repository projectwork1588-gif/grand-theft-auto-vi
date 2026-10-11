# Design reset, Gate 1: identity, tokens, typography, header, overflow fix

Status: **built and verified, awaiting the owner's approval.** Gate 2 (the homepage) has not been started.
Direction approved by the owner: Concept A (Key Art Index) as the foundation. See [DESIGN_RESET.md](DESIGN_RESET.md).

## What this gate changes

| Area | Change |
|------|--------|
| Brand identity | New Team Valkyrie emblem (a V with folded wings) and a two-line lockup, "TEAM VALKYRIE" over "GRAND THEFT AUTO VI FAN GUIDE". Served as `app/static/img/emblem.svg`, with a favicon. |
| Design tokens | New `app/static/css/tokens.css`: colour, type scale, tracking, spacing, radii, motion. The old token names still resolve (mapped onto the new ones) until each page is rebuilt. |
| Typography | Barlow Condensed caps for display and titles, Manrope for everything read. Nine sizes. Every font size, letter-spacing and radius in the three stylesheets was moved onto the scale. |
| Header | 72 px (64 px on phones). Lockup left; a "Trailers" pill and a Menu button right. The menu is a full-screen numbered index at every width. Solid after the first screen; always solid on inner pages. |
| Responsive overflow | The homepage no longer scrolls sideways between 901 and 1090 px (or at 320 and 340 px). |
| Accessibility | White text on the pink action colour was 2.9:1. It is now dark text at 6.5:1 on every primary button. |
| Guard rails | `tests/test_design_tokens.py` fails on any font size, letter-spacing or radius outside the system. `scripts/qa/sweep.mjs` is a real-browser width sweep (below). |

## What this gate deliberately does not change

* The homepage's sections and layouts, the cast stage, regions explorer, garage, stories, trailers, gallery and closing. They inherit the new tokens and type but are not redesigned until Gate 2.
* Any Flask route, service, repository, the API, the database or its seed data.
* The section navigator ("Jump to ..."). Its fate is decided with the homepage in Gate 2, as the owner asked.
* The pre-order section, the cinematic closing artwork and the loader. They stay in the plan for after the core system is approved.

## Measured result (homepage, 1280 px)

| | Before | After |
|---|--------|-------|
| Distinct text sizes | 34 | **9** (12, 14, 17, 21, 26, 33 and three fluid display sizes) |
| Text style combinations | 59 | **28** |
| Font families in use | 3 (including an Arial fallback) | **2** |
| Corner radii | 10 | **3** (12, 24, pill) plus circles |
| Pages that scroll sideways in 320 to 1920 px | 1 (the homepage, 901 to 1090 px) | **0** (see the sweep result below) |
| Automated tests | 301 | **309**, all passing |

## Identity

Three options were drawn (`review/gate1/emblem-options.jpg`). **Option 1, the winged V, is implemented.**

| Option | Verdict |
|--------|---------|
| 1. Wing V | Says "Valkyrie" without lettering, reads from 36 px up, and is not any publisher's mark. Implemented. |
| 2. Crest | A diamond frame with a V. Clean but generic. |
| 3. Monogram | A T and V ligature. Names the team, least ownable. |

Where it appears: header (52 x 35 px, 44 x 30 on phones), footer, menu, favicon. It is a single self-contained SVG, so replacing it means replacing one file.

**For the owner to judge.** The emblem is small by design in the header. At 36 px the lower feathers soften. If you want it bolder, the next step is a heavier feather weight, not a bigger mark.

## Tokens

Colour: ground `#12102A`, ground 2 `#1A1740`, card `#1D1A45`, text `#F6F1EA` (16.5:1), text 2 `#CFC8DC` (11.4:1), text 3 `#9A93B3` (6.4:1), action `#FF5F96` (the only action colour), label `#FFD47C` (the only label colour), official `#3DE0C8` (status only). Text on the action colour is `#12102A` (6.5:1).

Type: micro 12, small 14, body 17, lead 21, h4 26, h3 33, h2 41 to 65, h1 52 to 104, display 64 to 140. Tracking: tight, caps, ui, label, brand.

Space: 8, 16, 24, 32, 48, 72, 112. Section rhythm 72 to 112 px. Shape: card 24, tile 12, pill. Motion: 160, 320, 640 ms, one easing.

The style tile (`review/gate1/style-tile.html`, screenshots `tile-desktop.jpg`, `tile-mobile.jpg`) renders these with the real stylesheets.

## The header and menu

* The lockup is a link home. The "Trailers" pill goes to the trailers section of the homepage. The menu button is always present, at every width.
* The menu is a numbered index (01 Characters ... 05 Stories), a "Watch the trailers" action, About and Credits, and the non-affiliation line. The current section is marked.
* Keyboard: Escape closes and returns focus to the button; Tab stays inside the menu while it is open; page scroll is locked while open.
* Without JavaScript the header is static and the menu is a plain list under it.
* Small screens: 640 px and below show "GRAND THEFT AUTO VI" under the name and hide the pill (it is in the menu); 480 px and below make the menu button icon-only; 359 px and below drop the second line. The width sweep confirms the header fits at every width from 320 px.

## The overflow fix

**Root cause.** `.regions__stage` combined `aspect-ratio: 21 / 9` with `min-height: 440px`. The minimum height implied a minimum width of about 1027 px, so below that the box widened instead of shrinking and pushed the whole page sideways (167 px at 901 px, 50 px at the 1024 px iPad landscape width). The fixed header did not move, so the content slid under it and looked clipped.

**Fix.** The stage takes its height from the viewport (`clamp(420px, 40vw, 600px)`) and never sets its width; grid tracks use `minmax(0, 1fr)` so the explorer cannot widen its container. The phone layout keeps its own aspect ratio.

**Not a bug.** Earlier screenshots that showed a truncated nav at 1024 px were a capture artefact (an emulated width wider than the review pane). Gate 1 screenshots are taken in a real headless browser at the true size.

## Verification

* `pytest`: 309 passed (the old lockup test was replaced; two tests added for the menu and the emblem files; six design-token guards added).
* Width sweep, real Chrome, 88 widths from 320 to 1920 px, for the homepage, each index page, one detail page of each kind, About, Credits and the 404 page. It checks for sideways page scroll, any element past the viewport edge outside a deliberate scroller, and a header that does not fit. Re-run with:

```bash
python -m flask --app "app:create_app('testing')" run --port 5057   # in one terminal
node scripts/qa/cdp.mjs scripts/qa/sweep.mjs                        # in another (Node 22+, Chrome or Edge)
```

* Screenshots in `review/gate1/` (Git-ignored): `t1-desktop-*`, `t1-tablet-*`, `t1-mobile-*` for the homepage top, the open menu, an inner page, a detail page and the solid header; `t1-1024-regions-fixed.jpg`; `t1-320-*`; `tile-*`; `emblem-options.jpg`.

## Interim states the owner will see (all belong to Gate 2 or 3)

* **The homepage hero's "VI" numeral is smaller than before.** It now follows the display size (up to 140 px) instead of a one-off 240 px. Gate 2 rebuilds the hero.
* **Some small gold labels over bright photographs are hard to read** (for example "Protagonist" over Jason's sky on the lead cards). Gate 2's card family adds the one left-weighted scrim that fixes this.
* **Section backgrounds still use near-black scrims** in a few places; they were recoloured to the new ground but each is replaced when its section is rebuilt.
* **The "Jump to ..." pill and the section layouts are as before.**

## Decisions for the owner at this gate

1. **Emblem:** approve option 1, ask for a bolder variant, or choose option 2 or 3.
2. **Lockup:** "TEAM VALKYRIE" over "GRAND THEFT AUTO VI FAN GUIDE", or the reverse emphasis.
3. **Menu at every width:** approve, or restore the five links inline on screens wider than 1180 px.
4. **Dark text on the pink action colour:** approve (it is the only way to pass contrast without darkening the pink).
5. **Display scale:** keep 140 px as the largest size, or allow a 180 px hero numeral for Gate 2.

Gate 2 starts only after these are answered.
