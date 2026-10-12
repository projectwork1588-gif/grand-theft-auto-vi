# Gate 3A: Characters profile media and motion portraits (final correction pass)

Second correction pass on the Characters section. It is about how each person's footage and pictures are framed on
the profile pages and on the landing. Nothing outside the Characters templates, styles and the portrait builder
changed.

## What was found

* **Six of the eight clips are square (2160 x 2160); the two leads are 16:9 (3840 x 2160).** Every clip was being
  placed in a 1600 x 900 frame: the square flush right, a blurred copy of itself extending the left two thirds, black
  dips at both ends. On the profile the large picture was then cropped back to a square, so the person sat against
  the right edge with an artificial band beside them, and the poster did not match what played.
* **The poster was a different frame from the clip's start,** and a loaded video shows its own first frame (black), so
  the tile jumped between three different images.
* **The secondary picture was pulled up over the clip** with a negative margin and a 6 px border, so it read as
  attached to the corner of another picture rather than placed.

## What changed

| Area | Before | After |
|------|--------|-------|
| Footage shape | Everything in a widescreen composite with a blurred extension | Each person in the shape it was shot in: Jason and Lucia 16:9 whole, the other six square whole. Nothing is cropped, stretched or extended |
| Rest frame | The same artwork, centred on the widescreen frame | The artwork cropped to the clip's own shape around the person (focus per person, `PORTRAIT_FOCUS`). Real Dimez keeps both members in the square |
| Grade | Very dark night clips stayed very dark | Boobie, Dre'Quan, Real Dimez and Lucia are lifted gently while they play (gamma 1.4 to 1.7, never beyond) |
| Still and clip | Poster from a different moment, then a black first frame | The still is the exact frame at 0.4 s; the clip fades in over it at that frame, so there is nothing to notice. After the dissolve into the artwork it simply stays |
| Profile layout | Large picture with the second picture overlapping its corner | The clip alone beside the words (leads: words left, 16:9 clip right; everyone else: square clip left, words right, so the page zig-zags against the framed picture above). The second picture is the first, wide picture of the gallery below |
| Leads' heroes | Framing set last pass | Unchanged: heads whole at every width |

## Alternatives considered

A. The old overlap. B. The second picture stacked directly under the clip at the same width (a 21:9 strip for the
leads, 16:9 for the square clips). C. The clip alone, the second picture opening the gallery.
B was tidy but doubled the height of the right column and left the words stranded above empty space on the square
pages. C keeps every picture in a place with a job (the clip is the story's picture, the gallery is for stills) and
gives the supporting characters, who have only two screenshots, a proper two-picture gallery. See
`layout-options-*.jpg` in the review pack.

## Rebuilding

    python -m scripts.make_loops --portraits

writes `media/clips/<slug>-portrait.mp4` and `.jpg` for all eight (about 7 MB, Git-ignored). The homepage reel and the
older `<slug>.mp4`/`.jpg` are not touched; until the portraits exist the Characters pages fall back to those, as
before. The two shapes and the focus per person are in `scripts/make_loops.py` (`PORTRAIT_SIZE`, `PORTRAIT_FOCUS`)
and `app/media_slots.py` (`PORTRAIT_SHAPE`, `PORTRAIT_POSTER_AT`).

## Checked

Real-browser captures at 390, 600, 700, 820, 900, 1024, 1100, 1280 and 1440 px; the eight profiles and the landing at
desktop, tablet and phone; all clips played and paused; reduced-motion and the site's own motion switch; the width
sweep; the full test suite.
