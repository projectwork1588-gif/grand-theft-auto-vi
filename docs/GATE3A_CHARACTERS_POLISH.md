# Gate 3A: Characters final polish

A correction pass on the approved Characters direction (cinematic editorial, jump bar, network, profiles). Nothing
about the structure, the data, the API or the backend changed; this pass is pictures, framing, spacing and previews.

## What was wrong and what changed

| # | Defect | Cause | Fix |
|---|--------|-------|-----|
| 1 | Lucia's main spread looked dark and soft | Two causes. The picture was the dim night still (`Lucia_Caminos_03`, mean brightness 67/255, face small). And the `sizes` hint described the 595 px box, not the 1322 px the 16:9 picture is really drawn at, so the browser took the 640 px file and stretched it 2x | Main picture is now `Lucia_Caminos_02` (daylight, mean brightness 139, face large and lit, source 3840 x 2160). `sizes` now describes the drawn width, so desktop gets the 1920 px file (2560 px on dense screens). No filter, no sharpening, no brightening. The neon car still (`_10`) stays as the second picture |
| 2 | Partner banner: the man was hard to recognise | `Jason_and_Lucia_03` shows him in profile behind Lucia, and his long hair and beard do not match the short-haired Jason of the other official stills | Banner is `Jason_and_Lucia_01`: both faces large and lit, Jason matches `Jason_Duval_01`/`_04` and Rockstar's own Beach artwork (same pose, gun, shoulder tattoo). Cropped so both heads are whole; the words moved to the open side so they never touch a face |
| 3 | Large empty areas around Boobie, Dre'Quan, Real Dimez and Raul | A staggered two-column grid with different heights, plus a feature card spanning the tablet width | "Only Raw Records" is now one feature (Boobie) that is exactly as tall as the two stacked rows beside it (Dre'Quan, Real Dimez). The Cal and Brian cards are equal and top-aligned. Group gaps are about half. Tablet and phone have their own arrangement. The supporting block is about 25% shorter on desktop and tablet |
| 4 | Jason and Lucia profile heroes: head under the header or cropped | The art started at the top of the page, behind the header, with a vertical position that cut the head | The art now starts below the header and fades into it, so the head always has room. Each lead has framing for desktop, tablet and phone, set by where the face actually is in the picture (`pos_hero`, `pos_t`, `pos_m` in `media_slots.py`). Titles sit on the open side |
| 5 | "In Motion" tiles were dark or black | The poster was the clip's frame at 0.5 s (very dark scenes for five people), and a loaded video shows its own first frame, which is black (the sequences dip through black) | Posters are now the frame at 0.55 s, lifted towards a readable brightness (gamma capped at 1.9, never applied to a bright clip). The still is its own picture under the clip; the clip fades in only once it is really playing; after it ends the tile rests on the held artwork rather than the final black frame. The caption moved below the tile and the Play button is a small round icon in the corner the subject is not in |

## Rebuilding the posters

The stills live in the Git-ignored `media/clips/`. To regenerate only the posters from the sequences you already have:

    python -m scripts.make_loops --posters

(the full `python -m scripts.make_loops` rebuild also produces them). Until you do, the page works with the old, darker
posters; the bright-still-under-the-clip behaviour still applies.

## Not touched

Homepage hero poster, the three cinematic moments, Garage, Leonida region explorer, Flask services, repositories,
API, schema, seed and migrations. Original-character handling, search, filters, sorting, jump bar and the network
keep working exactly as before (the network now centres each lead's face in its circle).

## Checks

* 376 tests pass (7 new in this pass).
* Width sweep: 14 routes at 88 widths, 320 to 1920 px: no horizontal overflow, no header problems.
* Real-browser captures at 390, 600, 700, 820, 900, 1024, 1100, 1280 and 1440 px for the landing, both lead profiles and
  the supporting cast; all eight profiles at desktop, tablet and phone.
* Image sharpness audit: every picture is drawn from a file at least as wide as the pixels it fills (the opening is
  capped by the largest size the site requests on 2x screens).
* Link check: every same-origin link and picture on the landing and the eight profiles answers 200; every jump anchor
  has a target.
* Motion: the poster is up for the first 0.3 s, the clip then fades in, plays once, rests on the artwork, one at a time;
  with motion switched off the still and a small Play button remain.
