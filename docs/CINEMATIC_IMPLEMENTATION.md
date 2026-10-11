# Cinematic implementation (on the approved Gate 2 foundation)

Status: **built, corrected once on the owner's review, awaiting visual approval.** Gate 3 and Phase 3 have not been started. The Gate 2 hero, Jason and Lucia cards, native-video foundation and Leonida explorer were kept, not redesigned.

## What was built

| Item | Result |
|------|--------|
| **Hero** | One static card of the Robbery artwork (official, no embedded logo). The Beach artwork and the cycle are gone from the homepage. Typography, title placement and navigation are unchanged. On phones the artwork fills the top of the card at a size where Lucia and Jason are both in frame, and the lockup sits below it. |
| **Moment 1, Dawn over Leonida** | Trailer 1, 19.167 to 27.43 s. Full-viewport band after Jason and Lucia. |
| **Moment 2, Sun, water, speed** | Trailer 2, 6.35 to 9.70 s and 138.15 to 143.65 s with the 0.4 s dissolve (the approved edit). A 2.22:1 band above the region explorer. |
| **Moment 3, Last light** | Trailer 2, 152.85 to 163.80 s (alternative 3b: the date holds on screen). A 2.22:1 band on black, after the trailers and before the closing. Its controls sit under the picture so the logo and date are never covered. |
| **Encodes** | Desktop H.264 High with AAC at CRF 23 and a bitrate cap; a lighter phone cut for each (4:5, 4:3, 4:3 with per-shot focal points); a 1920 px poster. Letterbox bars of Trailer 2 removed. |
| **Audio** | Original audio kept and loudness-normalised: the three moments were -14.3, -8.5 and -9.3 LUFS and are now all about -16.2 LUFS with true peaks at or below -3.4 dBTP. |
| **Playback** | Muted autoplay when a moment is at least 35 percent in view; paused when it leaves; plays once and holds its last frame, with Replay. |
| **One at a time** | The most visible eligible moment plays; the cast reel and the trailer overlay count too. |
| **Sound** | Muted until the visitor clicks Enable sound. The choice is remembered for the visit and faded in on later moments where the browser allows it. |
| **Fallbacks** | Reduced motion, data saver and 2G/3G show the poster and a Play button. Phones play the lighter cut. The first moment falls back to an official still and a "Watch Official Trailer" overlay when no video is built. |
| **Cast reel** | Natural speed (no interpolation), a 0.4 s dissolve into the official artwork, a brief hold: 2.6 to 3.1 s per person, 19.7 s in all, 1600 x 900. Names, roles and descriptions follow the manifest; choosing a person plays them once and holds. |
| **Chapter navigation** | A quiet rail of dots on screens 1100 px and wider (names only on hover or focus; it hides over the footer and at the opening screen). On phones a 3 px progress hairline, and an "On this page" list in the header menu. The floating "Jump to..." pill is gone. |
| **Visible wording** | "Watch Official Trailer"; attribution reduced to "(c) Rockstar Games" on the page. |

## Files

| Area | Files |
|------|-------|
| Build scripts | `scripts/make_cinematics.py` (new), `scripts/make_loops.py` (reel rebuilt) |
| Backend | `app/local_media.py` (three named slots), `app/media_slots.py` (hero slug, `CINEMATICS`), `app/services/site.py` (`cinemas`) |
| Frontend | `app/templates/home.html` (macro used three times, rail), `app/static/css/pages.css`, `app/static/css/site.css`, `app/static/js/site.js` |
| Media (Git-ignored) | `media/cinematic/moment-{1,2,3}.mp4`, `-mobile.mp4`, `.jpg`; `media/clips/` reel |
| Tests and docs | `tests/test_pages.py`, `tests/conftest.py`, `docs/*` |

No database change was needed, and no source recording was modified. Everything under `media/` stays out of Git.

## Sizes

| | Desktop | Phone | Poster |
|---|---|---|---|
| Moment 1 | 8.7 MB | 2.5 MB | 0.4 MB |
| Moment 2 | 6.3 MB | 2.4 MB | 0.2 MB |
| Moment 3 | 3.0 MB | 1.4 MB | 0.2 MB |
| **All three** | **18 MB** | **6.3 MB** | 0.8 MB |

Nothing downloads until a moment is within one screen of the viewport (`preload="none"`, then `load()` on approach). Reel: about 7 MB, fetched when the cast section is near.

## Verification

* **Tests:** 319 passed (the complete suite).
* **Width sweep:** 14 routes at 88 widths from 320 to 1920 px, no horizontal overflow and no header problems.
* **Real browser, real videos, three sizes:** hero, leads, all three moments playing, the cast reel, the explorer, the finale's end state, the rail, the phone menu, and the reduced-motion poster (`review/gate25/final/`).
* **Behaviour checked with real mouse clicks:** one video at a time; Enable sound carries from Moment 1 to Moment 2 after a single click; pause and resume; a finished moment holds its last frame and Replay restarts it; reduced motion does not autoplay; phones load the mobile cuts.
* **A defect found and fixed during checks:** the browser fires `pause` just before `ended`, which briefly restarted a finished clip from frame zero; guarded so the last frame holds.

## Notes for the owner

1. **Chapter rail names** appear on hover or keyboard focus; the active dot is highlighted. The label can overlap a card edge briefly while hovered.
2. **Moment 3's date** is only visible in the last second and a half of the clip, which now plays to 163.8 s so it holds on screen.
3. **Closing band artwork** changed from Robbery to artwork 02, so the hero image is not repeated a few screens later.
4. **Loudness** was normalised to -16 LUFS; trailer masters are much louder, so the moments are quieter than the originals but consistent with each other.

Gate 3 and Phase 3 remain on hold.


---

## Correction pass (after the first review)

| Request | What changed |
|---------|--------------|
| Hero head clipped | The hero background had been extended 9 percent above the card (for a parallax) and the top of the artwork, including Jason's hair, was cut off. It now sits exactly in the card and no longer drifts, so the whole picture and its headroom show. |
| "Fan guide" wording | The lockup's second line is now just "Grand Theft Auto VI" (header, footer, menu). The accessible name changed to match. |
| Emblem | The header emblem is the cleaner Gate 1 cut: a bolder V with two feathers per wing (it was three). The favicon is unchanged. |
| First moment | Immersive: full viewport, nothing on top of it. It autoplays when scrolled into view and loops seamlessly. It was extended by about 2.3 s (the low-angle towers open it and the daytime lowrider street closes it) so the loop dissolves day into day. The loop is 9.75 s. |
| Controls and credit text | Removed from all three moments: no Replay, sound, trailer or credit text. The three sections are the picture only. |
| Sound | The loops are silent. Browsers refuse audible autoplay until a visitor has interacted, and a short excerpt of music on repeat is a poor default. For anyone who wants it, a click or tap on the picture (or the M key) fades the sound in, and the choice is remembered for the visit. There is no button. |
| Cast reel | The Play whole reel, Pause and Replay buttons are gone. The reel runs by itself from person 1 to 8 and loops (19.7 s). Choosing a name jumps to that person and the reel carries on. The name list stays on the right. |
| Region explorer | Advances by itself every 6.5 s from region 1 to 6 and around again, only while on screen, and waits while the visitor is hovering or focused in it. A quiet progress line under the active tab shows the timing. Manual selection is unchanged; reduced motion does not advance. |
| Trailers | Order is Trailer 1 (the large primary item), Trailer 2, An Extended Look. The hero's "Watch the trailer" now opens Trailer 1. The subtitle is a single plain line. |
| Screenshots | The helper sentence is gone. |

How the loops are built (`scripts/make_cinematics.py`): moments 1 and 2 dissolve their last 0.8 s into their first 0.8 s inside the file, so the loop point is an ordinary frame-to-frame step; moment 3 dips through black at the seam because it ends on a logo on black. The page only sets the `loop` attribute.

Defect found and fixed during this pass: when the first cinematic moment was still stopping, the cast reel declined to start and never retried; it now resumes when the other video has stopped.

Encodes after this pass: desktop 11.2, 6.1 and 2.8 MB (20 MB); phone 3.3, 2.3 and 1.3 MB (7 MB). Tests: 323 passed. Width sweep: clean.
