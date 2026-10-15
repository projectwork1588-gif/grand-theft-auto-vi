# Gate 3A: Characters motion audit and final pass

## What was measured

All of it in a real browser with the real generated files (`scripts/qa/motion_timeline.mjs` listens to the video element,
`scripts/qa/portrait_check.py` decodes the frames, `scripts/qa/motion_scenarios.mjs` drives the situations).

### The landing was a different system from the profiles

| | Landing tiles (before) | Profiles |
|--|--|--|
| File | `<slug>-portrait.mp4` | `<slug>-profile.mp4` |
| Starts on | a frame of the clip (0.4 s in) | the artwork |
| Lead-in | none: the clip is already moving | 0.3 s dissolve |
| Whole clip visible | 0.5 s (the dissolve began at 0.5 s of a 1.0 s clip) | 1.0 s, then its last frame is held under a 0.5 s dissolve |
| Artwork hold | 2.0 to 2.5 s | 2.0 s |
| Length | 3.0 s (3.5 s for 1.5 s clips) | 3.8 s (4.3 s) |
| Picture size | 120 px square thumbnails (232 px wide for the leads) | 400 to 660 px |
| Controller | the landing script that also restarted a finished clip | the same script |

### Root cause of "too fast", as measured

Three things, not one. None of them was playback speed: the playback rate measured 1.00 between frames on every tile,
before and after, at 30 fps.

1. **The sequence.** A 1.0 s clip had only 0.5 s of clean footage on the landing before it started to dissolve, and no
   lead-in. Jason has the same 1.0 s clip and the same file length but is shown in a 232 px wide frame, which is why he
   read as fine.
2. **The size.** Six 120 px thumbnails make a one-second move look hurried. The profile shows the same footage at four
   times the width.
3. **A controller bug.** When a finished clip was seeked back to its resting frame, the pause that follows made the
   controller start it again: Cal Hampton played twice, Real Dimez twice (6.0 s of wall time), Dre'Quan Priest three
   times (6.4 s) in the first measurement. Starting before the file was buffered added "waiting" stalls.

### What changed

* One file per person feeds the landing tile and the profile. The landing's own build is gone.
* The supporting cards show the in-game screenshot large with the sequence layered over it (the same overlap language
  as the profiles) at 160 to 250 px, so the artwork the tile rests on is not a copy of the picture beside it.
* The controller finishes a sequence once (also on the `pause` that precedes `ended`), starts a tile only after it has
  been at least half in view for 380 ms and the whole file is buffered, lets only one run, never replays a finished
  tile, and sends an interrupted one back to its artwork so no half-dissolved frame is left.
* A refused autoplay marks the tile and shows its Play button.
* Files are slightly smaller (compression 27): all eight total about 9 MB.

## Results per person (decoded and played in Chrome)

See `MOTION_REPORT.md` in the review pack for the table.

## Honest limits

* A few cold starts in headless Chrome show a 0.1 to 0.2 s decoder wait; the resting frame and the playback rate are
  not affected.
* Dre'Quan Priest's second picture is cropped by the source: his head touches its top edge.
* The playback measurements come from headless Chrome with software decoding; on a real laptop they should be at least
  as smooth.
