"""Editorial choices about which stored media rows the pages feature. These are slugs of rows in media_assets,
not content. If a slug is missing from the database (for example before the migrations are applied) the page
falls back to its original artwork."""

HERO_SLUGS = ("art-jason-lucia-beach", "art-jason-lucia-01", "art-jason-lucia-robbery")
# Trailer 2 leads. Each video has its own official poster image, in the same order.
VIDEO_SLUGS = ("official-trailer-2", "official-trailer-1", "official-an-extended-look")
VIDEO_POSTER_SLUGS = ("poster-trailer-2", "poster-trailer-1", "poster-extended-look")
SCREENSHOT_SLUGS = (
    "shot-vice-city-10", "shot-leonida-keys-01", "shot-jason-duval-01",
    "shot-lucia-caminos-03", "shot-mount-kalaga-04", "shot-port-gellhorn-06",
)
# Full-bleed backdrops for bands.
BACKDROP_SLUGS = ("shot-vice-city-11", "art-jason-lucia-robbery", "shot-grassrivers-05")
BACKDROP_STORIES = "shot-vice-city-11"
BACKDROP_CLOSING = "art-jason-lucia-robbery"

# One explicit playlist order for the cast. The homepage name list, the reel's segments and the loop builder
# (scripts/make_loops.py) all read this tuple, never the database's row order.
CAST_ORDER = (
    "jason-duval", "lucia-caminos", "cal-hampton", "boobie-ike",
    "dre-quan-priest", "real-dimez", "raul-bautista", "brian-heder",
)

# The cinematic moment between the leads and the cast. There is no downloadable trailer and no stated licence, so
# nothing of Rockstar's video is copied or hosted. The section always works from an official still and opens the
# trailer in Rockstar's own player on request. If the owner supplies footage that is authorised for reuse and builds
# media/cinematic/cinematic.mp4 (see local_media.cinematic), the same section plays it as native video instead.
CINEMATIC = {
    "title": "Trailer 1",
    "poster": "poster-trailer-1",
    "trailer": "official-trailer-1",
}

# The two leads are presented as a matched pair: Jason by day on a motorcycle, Lucia at night on hers.
CHARACTER_COVERS = {
    "jason-duval": "shot-jason-duval-01",
    "lucia-caminos": "shot-lucia-caminos-03",
}
# Scenic establishing shot for each region (used on the homepage explorer and the regions page).
REGION_STAGE = {
    "vice-city": "shot-vice-city-01",
    "leonida-keys": "shot-leonida-keys-01",
    "grassrivers": "shot-grassrivers-05",
    "port-gellhorn": "shot-port-gellhorn-06",
    "ambrosia": "shot-ambrosia-04",
    "mount-kalaga": "shot-mount-kalaga-04",
}
# Cinematic backdrop for the top of each catalogue page.
PAGE_HERO_SLUGS = {
    "characters": "art-jason-lucia-motel",
    "vehicles": "vehicle-grotti-cheetah-02",
    "regions": "shot-vice-city-10",
    "locations": "shot-port-gellhorn-06",
    "missions": "shot-vice-city-11",
}

# Official page links (verified 2026-10-09 and 2026-10-10).
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

# Framing hints: where the subject sits in a wide picture, so tall crops keep it in view.
FOCUS = {
    "shot-jason-duval-01": "right",
    "shot-lucia-caminos-03": "top",
    "shot-lucia-caminos-10": "center",
    "shot-vice-city-01": "top",
    "vehicle-grotti-cheetah-01": "bottom-left",
    "vehicle-grotti-cheetah-02": "center",
}
