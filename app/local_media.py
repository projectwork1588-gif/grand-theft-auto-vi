"""Locally built media (media/clips/, media/cinematic/ and media/hero/). All three folders are Git-ignored.

clips/      loops and the cast reel, built by `scripts.fetch_clips` and `scripts.make_loops`.
cinematic/  the three homepage moments built by `scripts.make_cinematics`: moment-N.mp4, moment-N.jpg (poster) and
            moment-N-mobile.mp4 (a lighter phone cut), for N = 1, 2, 3. They exist only after that script has run.

hero/       the three parallax layers of the homepage hero (sky, mid, fg as .webp, plus -1280 copies), built by
            `scripts.make_hero_layers`. Without them the hero is the single official picture, as before.

A fresh clone has none of these and the site falls back to official posters and links. Only files directly inside
those folders with a safe name and an .mp4, .jpg or .webp extension are ever served.
"""
import json
import re
from pathlib import Path

from flask import current_app

SAFE_NAME = re.compile(r"^(?:clips|cinematic|hero)/[a-z0-9-]+\.(?:mp4|jpg|webp)$")
CINEMATIC_SLOTS = ("moment-1", "moment-2", "moment-3")
DEFAULT_ROOT = Path(__file__).resolve().parent.parent / "media"


def root():
    return Path(current_app.config.get("MEDIA_ROOT") or DEFAULT_ROOT)


def is_servable(relative):
    """True only for clips/, cinematic/ or hero/ <safe-name>.mp4, .jpg or .webp that exists on disk."""
    return bool(relative) and bool(SAFE_NAME.match(relative)) and (root() / relative).is_file()


def manifest():
    """Reel segment times written by scripts.make_loops, or None when the reel has not been built."""
    path = root() / "clips" / "manifest.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def cinematics():
    """The built cinematic moments as {slot: {video, mobile, poster}}; a slot is present only when its video exists.

    The poster and the lighter phone cut are optional; a missing one is None and the page copes."""
    found = {}
    for slot in CINEMATIC_SLOTS:
        video = f"cinematic/{slot}.mp4"
        if not is_servable(video):
            continue
        poster, mobile = f"cinematic/{slot}.jpg", f"cinematic/{slot}-mobile.mp4"
        found[slot] = {"video": video, "poster": poster if is_servable(poster) else None,
                       "mobile": mobile if is_servable(mobile) else None}
    return found


HERO_LAYERS = ("sky", "mid", "fg")


def hero_layers():
    """The built hero layers as {layer: {full, small}}, or None unless all three exist (a partial set is useless).

    `small` is the lighter copy for phones and is None when missing; the page then uses the full one."""
    found = {}
    for name in HERO_LAYERS:
        full, small = f"hero/{name}.webp", f"hero/{name}-1280.webp"
        if not is_servable(full):
            return None
        found[name] = {"full": full, "small": small if is_servable(small) else None}
    lit = "hero/fg-lit.webp"
    if is_servable(lit):                                   # the warmer copy of the pair is a nicety, not required
        small = "hero/fg-lit-1280.webp"
        found["lit"] = {"full": lit, "small": small if is_servable(small) else None}
    return found
