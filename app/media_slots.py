"""Which stored media rows the homepage features. These are slugs of rows in media_assets, not content.

If a slug is missing from the database (for example before the migrations are applied) the homepage
shows its original fallback artwork instead.
"""
HERO_SLUGS = ("art-jason-lucia-beach", "art-jason-lucia-01", "art-jason-lucia-robbery")
# Trailer 2 leads the reel. Each video has its own official poster image, in the same order.
VIDEO_SLUGS = ("official-trailer-2", "official-trailer-1", "official-an-extended-look")
VIDEO_POSTER_SLUGS = ("poster-trailer-2", "poster-trailer-1", "poster-extended-look")
SCREENSHOT_SLUGS = (
    "shot-vice-city-01", "shot-lucia-caminos-01", "shot-leonida-keys-01",
    "shot-jason-duval-01", "shot-port-gellhorn-01", "shot-grassrivers-01",
)
# Full-bleed backdrops for the stories band and the closing band.
BACKDROP_SLUGS = ("shot-vice-city-03", "art-jason-lucia-robbery", "postcard-vice-city")
BACKDROP_STORIES = "shot-vice-city-03"
BACKDROP_CLOSING = "art-jason-lucia-robbery"

# Official page links used in the media preview (verified 2026-10-09 and 2026-10-10).
OFFICIAL_LINKS = {
    "site": "https://www.rockstargames.com/VI",
    "media": "https://www.rockstargames.com/VI/media",
    "videos": "https://www.rockstargames.com/VI/media/videos",
    "screenshots": "https://www.rockstargames.com/VI/media/screenshots",
    "wallpapers": "https://www.rockstargames.com/VI/media/artwork-wallpapers",
    "leonida": "https://www.rockstargames.com/VI/only-in-leonida",
    "editions": "https://www.rockstargames.com/VI/editions",
}
RELEASE_NOTE = "November 19, 2026"  # the date shown on rockstargames.com/VI

# Display order for regions: the order Rockstar lists them in on rockstargames.com/VI/only-in-leonida.
# (The API keeps its alphabetical order. Only the pages use this.)
REGION_ORDER = ("vice-city", "leonida-keys", "grassrivers", "port-gellhorn", "ambrosia", "mount-kalaga")

# Cinematic backdrop for the top of each catalogue page (slugs of official media rows).
PAGE_HERO_SLUGS = {
    "characters": "art-jason-lucia-motel",
    "vehicles": "vehicle-grotti-cheetah-02",
    "regions": "shot-vice-city-04",
    "locations": "shot-port-gellhorn-02",
    "missions": "shot-vice-city-02",
}
