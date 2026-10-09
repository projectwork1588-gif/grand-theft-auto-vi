"""Safe URL helpers for official media. Used by templates, so a bad database row can never inject a foreign URL.

Images and players are REMOTE references to Rockstar's own published media. Only the exact official
prefixes below are ever rendered. Anything else returns None and the template shows an original fallback.
"""
IMAGE_PREFIX = "https://www.rockstargames.com/VI/_next/static/media/"
PLAYER_PREFIX = "https://www.rockstargames.com/videoplayer?"
IMAGE_WIDTHS = (640, 1280, 1920)


def is_official_image(url):
    return bool(url) and url.startswith(IMAGE_PREFIX) and " " not in url and '"' not in url


def image_src(url, width=1280):
    """Resized official image URL (Rockstar's own image service takes an imwidth parameter)."""
    if not is_official_image(url):
        return None
    return f"{url}?akim=1&imdensity=1&imwidth={int(width)}"


def image_srcset(url, widths=IMAGE_WIDTHS):
    if not is_official_image(url):
        return None
    return ", ".join(f"{image_src(url, w)} {w}w" for w in widths)


def player_src(url, autoplay=False):
    """Rockstar's own embeddable player URL, or None if the stored value is not exactly that."""
    if not url or not url.startswith(PLAYER_PREFIX) or " " in url or '"' in url:
        return None
    if autoplay:
        return url.replace("autoplay=false", "autoplay=true")
    return url
