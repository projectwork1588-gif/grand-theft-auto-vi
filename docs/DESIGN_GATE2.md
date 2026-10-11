# Design reset, Gate 2: hero, leads, cinematic moment, region explorer

Status: **built and verified, awaiting the owner's visual approval.** Gate 3 has not been started.
Foundation: Concept A (Key Art Index), approved. Gate 1 (identity, tokens, header) approved with two tweaks, both applied here.

## Scope

Exactly four homepage sections were rebuilt. Nothing else on the homepage or elsewhere was redesigned.

| # | Section | Result |
|---|---------|--------|
| 1 | Hero | One framed card of official key art, a left-weighted scrim, the lockup bottom-left, the release date bottom-right, and the 180 px VI numeral. |
| 2 | Jason and Lucia | Two cards from one family: official still, role, condensed name, one line, one pill. |
| 3 | Cinematic moment | A full-width native-video slot. Without authorised footage it is an official still with a play control that opens Rockstar's player in a premium overlay. |
| 4 | Leonida region explorer | One stage card, six numbered tabs with a large touch target, an action pill per region. |

Not touched: the cast stage, garage, stories, trailers and gallery, the closing, the footer, the "Jump to ..." pill, every other page, every route, service, repository, the API and the database.

## Gate 1 tweaks (applied)

* **Solid header over bright artwork:** the scrolled header is now 98.5 % opaque with a stronger edge and a soft shadow (it was 94 %).
* **Mobile menu note:** the long disclaimer became one small, low-contrast line ("Unofficial fan project. Not affiliated with Rockstar Games or Take-Two Interactive.") with a link to Credits and legal. The full disclaimer remains in the footer and on the Credits page.
* Emblem and favicon were already approved (winged V in header, footer and menu; V-on-tile favicon).

## 1 Hero

* The card is inset in the page gutter (24 px corners), height from the viewport (560 to 880 px), so the header sits above it on the ground colour.
* Required identity lines are kept: "Welcome, gamers", "Team Valkyrie presents", "Grand Theft Auto VI".
* The VI numeral uses `--t-numeral` (104 to 180 px, fluid). The three official artworks still cross-fade slowly; reduced-motion visitors see the first.
* One scrim, left-weighted, replaces the former two. On phones the scrim is vertical and the card is taller so the pair is not under the lockup.
* The hero image requests widths from the same srcset as before (`sizes` is now `100vw` on wide screens, `180vw` on phones, so a phone gets a 960 px or 1280 px file, not 640).

## 2 Jason and Lucia

* A new shared card (`.key-card`, in `components.css`) that Gates 3 to 5 will reuse: 24 px corners, one scrim, a gold label, a condensed title, one line, one pill. Titles are real `h3` headings inside the link.
* 4:3 on desktop and tablet, 4:5 on phones. The label colour is on the left-weighted scrim, which fixes the unreadable gold label over Jason's bright sky.

## 3 Cinematic moment

**What was removed.** The YouTube IFrame API player that played muted behind a still. It could not be made free of YouTube's interface, and the owner asked us to stop disguising it. The page no longer loads any third-party script, so the content security policy no longer allows `www.youtube.com` scripts (a security gain).

**What it is now.**

| State | What the visitor sees | When |
|-------|-----------------------|------|
| **Fallback (today)** | Full-width official poster of Trailer 1 with a slow push, a caption block, and a "Watch Trailer 1" play control that opens Rockstar's own player in the overlay. | No `media/cinematic/cinematic.mp4` exists. |
| **Native video** | Muted, looping native `<video>` that starts when the section is on screen and pauses when it leaves; Pause and Enable sound buttons; a "Watch the full trailer" button. No iframe, no logo, no third-party interface. | `media/cinematic/cinematic.mp4` exists. |
| **Reduced motion or data saver** | The poster and a "Play the footage" button. Nothing plays until asked. | Native video present. |
| **Phone** | Plays `cinematic-mobile.mp4` if present; otherwise the poster and a "Play the footage" button. | Width 700 px or less. |
| **Slow connection (2G/3G)** | The poster and a "Play the footage" button. | Native video present. |

**The premium overlay.** The trailer dialog is shared by the hero, this section and the trailers block: a blurred indigo backdrop, the video's name in condensed caps above a rounded player, an honest credit line ("Official video, played in Rockstar's own player. © Rockstar Games"), and a close pill. The player inside is Rockstar's own page, loaded only after a click.

**Footage that is not Rockstar's was used to test it.** A synthetic colour-bar clip was generated outside the repository and served by a throwaway server, to prove the native slot in a real browser:

| Check | Result |
|-------|--------|
| Plays muted when the section is on screen | yes (`paused=false`, `muted=true`) |
| Pauses when scrolled away, resumes on return | yes |
| Enable sound (real mouse click) | unmutes, keeps playing, label becomes "Sound on"; clicking again mutes |
| Pause and Play buttons | work |
| Phone width with a lighter cut | plays `cinematic-mobile.mp4` |
| Reduced motion | does not autoplay; plays when asked |

**Rights.** There is no download and no stated licence for the trailers, so nothing from them is copied. Until the owner supplies authorised footage, the section works from an official still. The component is ready: build `media/cinematic/cinematic.mp4` (see `media/README.md`) and it takes over. A video that is not present is never requested.

## 4 Region explorer

* One stage card with the same left-weighted scrim; the region name at h1 size, the one-line summary, and an action pill.
* Six tabs: number plus a condensed name, each at least 76 px high, an action-colour rule under the active tab. Hovering, focusing or (on touch) the first tap previews; the second tap opens.
* Tabs are six across on wide screens, three across to 1000 px, two across on phones (so "Grassrivers" and "Port Gellhorn" never clip).
* The sideways-scroll fix from Gate 1 is preserved: the stage takes its height from the viewport and never sets its own width.

## Measured (homepage, 1280 px)

| | Before the reset | After Gate 1 | After Gate 2 |
|---|------------------|--------------|--------------|
| Distinct text sizes | 34 | 9 | 9 (12, 14, 17, 21, 26, 33, 60, 86, 180) |
| Font families | 3 | 2 | 2 |
| Corner radii | 10 | 3 | 3 (12, 24, pill) plus circles |
| Third-party scripts on the homepage | 1 (YouTube IFrame API) | 1 | **0** |

## Verification

* `pytest`: **316 passed.** Ten tests were rewritten for the new markup (not weakened: each still asserts its original intent), and new tests cover the hero card and identity, the leads cards, the fallback and native cinematic states, strict cinematic file names, the CSP, the region explorer and section order.
* Width sweep, real Chrome, 14 routes x 88 widths from 320 to 1920 px: no sideways scroll, no element past the viewport edge, header fits. One 1 px overflow at 320 px (a tab label) was found and fixed.
* Screenshots: `review/gate2/final/` at 1440, 820 and 390 px for each section, the explorer's second state, the trailer overlay, and the two Gate 1 tweaks. A review board and ZIP are in the project folder.

## Open items for the owner

1. **Footage.** Place authorised GTA VI footage in `media/source-videos/`; I will shortlist, compare and, once authorisation is confirmed, build `media/cinematic/`. Until then the fallback stands.
2. **"Jump to ..." pill and chapter numbers.** The pill still names the current section. Options for Gate 3: keep it as is, replace it with a quiet left rail of numerals on wide screens, or remove it and rely on the header. It was left alone because it is outside the four sections.
3. **Hero art cycle.** It cross-fades three official artworks every nine seconds. A single still would be calmer; this is a one-line change.
4. **Overlay wording.** The caption says the video plays in Rockstar's own player. If you prefer to name YouTube explicitly, say so.

Gate 3 starts only after this gate is approved.
