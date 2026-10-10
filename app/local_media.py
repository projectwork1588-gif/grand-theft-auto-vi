"""Locally built video loops (media/clips/). They exist only after `scripts.fetch_clips` and `scripts.make_loops`.

The folder is Git-ignored, so a fresh clone has none and the site falls back to official posters and links.
Only files directly inside media/clips/ with a safe name and an .mp4, .jpg or .json extension are ever served.
"""
import json
import re
from pathlib import Path

from flask import current_app

SAFE_NAME = re.compile(r"^clips/[a-z0-9-]+\.(?:mp4|jpg)$")
DEFAULT_ROOT = Path(__file__).resolve().parent.parent / "media"


def root():
    return Path(current_app.config.get("MEDIA_ROOT") or DEFAULT_ROOT)


def is_servable(relative):
    """True only for clips/<safe-name>.mp4 or .jpg that exist on disk."""
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
