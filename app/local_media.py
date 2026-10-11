"""Locally built video (media/clips/ and media/cinematic/). Both folders are Git-ignored.

clips/      loops and the cast reel, built by `scripts.fetch_clips` and `scripts.make_loops`.
cinematic/  the one full-screen cinematic: cinematic.mp4, cinematic.jpg (poster) and an optional lighter
            cinematic-mobile.mp4. They exist only when the owner has supplied footage that is authorised for reuse.

A fresh clone has none of these and the site falls back to official posters and links. Only files directly inside
those two folders with a safe name and an .mp4 or .jpg extension are ever served.
"""
import json
import re
from pathlib import Path

from flask import current_app

SAFE_NAME = re.compile(r"^(?:clips|cinematic)/[a-z0-9-]+\.(?:mp4|jpg)$")
CINEMATIC = {"video": "cinematic/cinematic.mp4", "poster": "cinematic/cinematic.jpg", "mobile": "cinematic/cinematic-mobile.mp4"}
DEFAULT_ROOT = Path(__file__).resolve().parent.parent / "media"


def root():
    return Path(current_app.config.get("MEDIA_ROOT") or DEFAULT_ROOT)


def is_servable(relative):
    """True only for clips/ or cinematic/ <safe-name>.mp4 or .jpg that exist on disk."""
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


def cinematic():
    """The authorised cinematic as {video, poster, mobile} paths, or None until cinematic/cinematic.mp4 exists.

    The poster and the lighter phone cut are optional; a missing one is None and the page copes."""
    if not is_servable(CINEMATIC["video"]):
        return None
    return {key: (path if is_servable(path) else None) for key, path in CINEMATIC.items()}
