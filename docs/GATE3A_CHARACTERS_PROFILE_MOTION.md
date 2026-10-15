# Gate 3A: Characters profile media and motion (final)

How "The story so far" shows each person's footage and pictures on the eight profile pages. The approved design is an
**overlap**: one large picture with a second picture layered in front of its lower-right.

## The layout

* **Large picture.** The person's motion portrait, in the shape the footage was shot in (the two leads 16:9, the other
  six square). Before and after playing it shows the person's main artwork (Jason on the motorcycle, Lucia at the pool,
  and so on).
* **Second picture.** In front of the large one, at its lower-right, extending a little past its right and bottom
  edges. A 4 px ring in the page colour, a soft shadow and rounded corners give it depth. It is 46% of the large
  picture's width on desktop, 44% on tablet and 42% on phones. It is 4:3 beside a 16:9 clip and 4:5 beside a square one,
  and it is cropped around the person (`SECOND_FOCUS` in `app/media_slots.py`).
* **Room for the overhang** is part of the layout (the block reserves it), so nothing clips or overflows.
* **Faces.** The second picture only covers the lower-right. Every person's face sits above or beside that region in
  both the artwork and the clips; checked on all eight at 390, 820, 1024 and 1440 px.
* **The gallery** below no longer repeats the two pictures.

The words sit on the left and the pictures on the right on every profile; the Characters landing is unchanged.

## The motion

Each profile sequence (`media/clips/<slug>-profile.mp4`) is built by `python -m scripts.make_loops --portraits`:

| Step | What happens |
|------|--------------|
| Still | The artwork, cropped to the clip's shape around the person. The `.jpg` is exactly the first frame of the video |
| Intro | 0.3 s dissolve from the artwork into the clip's first frame |
| Clip | The whole clip, 1.0x, 30 fps, never trimmed, sped up, slowed down or interpolated |
| Outro | 0.5 s dissolve back into the artwork while the clip's last frame is held |
| Rest | The artwork, held 2.0 s with a very slow 5% push-in |

Total: 3.8 s for a 1.0 s clip, 4.3 s for a 1.5 s clip. There is no black frame and no blurred extension. Very dark clips
(Boobie, Dre'Quan, Real Dimez, Lucia) are lifted gently (gamma at most 1.7).

The landing tiles keep their own sequences (`<slug>-portrait.mp4`: a frame of the clip as the still) with the same
0.5 s dissolve and 2 s hold.

### Checked, not assumed

`python -m scripts.qa.portrait_check` decodes the built sequences and measures:

* the first frame against the artwork (a mean difference of 0.6 to 2.0 out of 255: the still **is** the artwork);
* the clip's own first and last frames against the artwork (57 to 110: they are different pictures, which is why each
  end dissolves instead of cutting);
* the resting frame against the artwork (26 to 37: close, but not identical, because of the slow push-in);
* the darkest frame against the darkest of the artwork and the clip (never a dip, never a flash);
* that each dissolve is even and finishes (largest step no more than 1.35 times the median).

## Rebuilding

    python -m scripts.make_loops --portraits

It fetches Lucia's main artwork (`Lucia_Caminos_02`) once into the Git-ignored `media/source/art/` and writes the
landing and profile sets (about 14 MB). Until the files exist the pages fall back to the landing set, then to the older
per-person loops, and the layout is unchanged.
