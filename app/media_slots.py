"""Which stored media rows the homepage features. These are slugs of rows in media_assets, not content.

If a slug is missing from the database (for example before migration 001 is applied) the homepage
shows its original fallback artwork instead.
"""
HERO_SLUGS = ("art-jason-lucia-beach", "art-jason-lucia-01", "art-jason-lucia-robbery")
VIDEO_SLUGS = ("official-trailer-1", "official-trailer-2", "official-an-extended-look")
VIDEO_POSTER_SLUGS = ("shot-jason-and-lucia-01", "shot-jason-and-lucia-02", "shot-jason-and-lucia-03")
SCREENSHOT_SLUGS = (
    "shot-vice-city-01", "shot-lucia-caminos-01", "shot-leonida-keys-01",
    "shot-jason-duval-01", "shot-port-gellhorn-01", "shot-grassrivers-01",
)
WALLPAPER_SLUGS = ("art-jason-lucia-motel", "postcard-vice-city", "postcard-mount-kalaga")

# Official page links used in the media preview (verified 2026-10-09).
OFFICIAL_LINKS = {
    "site": "https://www.rockstargames.com/VI",
    "media": "https://www.rockstargames.com/VI/media",
    "videos": "https://www.rockstargames.com/VI/media/videos",
    "screenshots": "https://www.rockstargames.com/VI/media/screenshots",
    "wallpapers": "https://www.rockstargames.com/VI/media/artwork-wallpapers",
    "leonida": "https://www.rockstargames.com/VI/only-in-leonida",
}
RELEASE_NOTE = "Coming November 19, 2026"  # wording shown on rockstargames.com/VI on 2026-10-09

# Display order for regions: the order Rockstar lists them in on rockstargames.com/VI/only-in-leonida.
# (The API keeps its alphabetical order. Only the pages use this.)
REGION_ORDER = ("vice-city", "leonida-keys", "grassrivers", "port-gellhorn", "ambrosia", "mount-kalaga")
