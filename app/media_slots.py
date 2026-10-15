"""Editorial choices about which stored media rows the pages feature. These are slugs of rows in media_assets,
not content. If a slug is missing from the database (for example before the migrations are applied) the page
falls back to its original artwork."""

# One static hero, chosen by the owner: the Robbery artwork (no embedded logo). No cycle.
HERO_SLUGS = ("art-jason-lucia-robbery",)
# Trailer 1 leads, then Trailer 2, then An Extended Look. Each video has its own official poster, in the same order.
VIDEO_SLUGS = ("official-trailer-1", "official-trailer-2", "official-an-extended-look")
VIDEO_POSTER_SLUGS = ("poster-trailer-1", "poster-trailer-2", "poster-extended-look")
SCREENSHOT_SLUGS = (
    "shot-vice-city-10", "shot-leonida-keys-01", "shot-jason-duval-01",
    "shot-lucia-caminos-03", "shot-mount-kalaga-04", "shot-port-gellhorn-06",
)
# Full-bleed backdrops for bands.
BACKDROP_SLUGS = ("shot-vice-city-11", "art-jason-lucia-02", "shot-grassrivers-05")
BACKDROP_STORIES = "shot-vice-city-11"
BACKDROP_CLOSING = "art-jason-lucia-02"   # not the hero artwork

# One explicit playlist order for the cast. The homepage name list, the reel's segments and the loop builder
# (scripts/make_loops.py) all read this tuple, never the database's row order.
CAST_ORDER = (
    "jason-duval", "lucia-caminos", "cal-hampton", "boobie-ike",
    "dre-quan-priest", "real-dimez", "raul-bautista", "brian-heder",
)

# The three cinematic moments (native HTML5 video, built by scripts/make_cinematics.py from the owner's own recordings).
# Slot ids match the files in media/cinematic/. Only the first has an official-still fallback (an official poster with a
# play control that opens Rockstar's own player); the other two appear only when their video has been built.
CINEMATICS = {
    "moment-1": {"title": "Dawn over Leonida", "poster": "poster-trailer-1", "trailer": "official-trailer-1"},
    "moment-2": {"title": "Sun, water, speed", "poster": None, "trailer": "official-trailer-2"},
    "moment-3": {"title": "Last light", "poster": None, "trailer": "official-trailer-2"},
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

# The Characters pages (Gate 3A). Slugs of media_assets rows, chosen by eye from the contact sheet: whole faces, and the
# person on the side the text is not. main = the spread / hero picture, second = the smaller overlapping frame,
# pos / pos2 = where the subject sits (CSS object-position) so a tall crop keeps the face.
CHARACTER_STAGE = {
    # pos = the spread / card crop; pos_hero, pos_t, pos_m = the full-bleed hero on desktop, tablet and phone (the head is
    # kept whole and clear of the title); face = where the face sits in the picture, for the network and thumbnails.
    "jason-duval": {"main": "shot-jason-duval-01", "second": "shot-jason-duval-04", "pos": "78% 40%", "pos2": "30% 40%",
                    "pos_hero": "78% 0%", "pos_t": "74% 0%", "pos_m": "71% 0%", "hero_side": "left", "face": (0.66, 0.16)},
    "lucia-caminos": {"main": "shot-lucia-caminos-02", "second": "shot-lucia-caminos-10", "pos": "45% 30%", "pos2": "50% 30%",
                      "pos_hero": "20% 0%", "pos_t": "30% 0%", "pos_m": "37% 0%", "hero_side": "left", "face": (0.47, 0.36)},
    "cal-hampton": {"main": "art-cal-hampton", "second": "shot-cal-hampton-01", "pos": "50% 30%", "pos2": "50% 40%"},
    "boobie-ike": {"main": "art-boobie-ike", "second": "shot-boobie-ike-01", "pos": "50% 30%", "pos2": "50% 40%"},
    "dre-quan-priest": {"main": "art-dequan-priest", "second": "shot-dequan-priest-02", "pos": "60% 40%", "pos2": "60% 40%"},
    "real-dimez": {"main": "art-real-dimez", "second": "shot-real-dimez-01", "pos": "40% 40%", "pos2": "50% 30%"},
    "raul-bautista": {"main": "art-raul-bautista", "second": "shot-raul-bautista-01", "pos": "50% 30%", "pos2": "50% 30%"},
    "brian-heder": {"main": "art-brian-heder", "second": "shot-brian-heder-01", "pos": "65% 40%", "pos2": "60% 40%"},
}
CAST_LEADS = ("jason-duval", "lucia-caminos")
# Where the person sits across each second picture (0 = left edge, 1 = right edge). The second picture overlaps the large
# one on the profile pages as a 4:3 (beside a 16:9 clip) or 4:5 (beside a square clip) crop, centred on this point.
SECOND_FOCUS = {
    "jason-duval": 0.43, "lucia-caminos": 0.50, "cal-hampton": 0.71, "boobie-ike": 0.56,
    "dre-quan-priest": 0.83, "real-dimez": 0.50, "raul-bautista": 0.83, "brian-heder": 0.55,
}
# Motion portraits on the Characters pages. Rockstar shot the two leads in 16:9 and the other six square, so each person
# is shown in the shape the footage was shot in, never stretched into a shape it was not (the old extended widescreen
# frame is kept only for the homepage reel). Built by `python -m scripts.make_loops --portraits`.
PORTRAIT_SHAPE = {"jason-duval": "wide", "lucia-caminos": "wide"}      # everyone else is "square"
PORTRAIT_POSTER_AT = 0.4          # seconds: the still is this exact frame, so the clip takes over without a visible change
# The partner banner: both protagonists' faces large and lit, taken from Rockstar's own Jason and Lucia screenshots.
CAST_TOGETHER = "shot-jason-and-lucia-01"
# Opening picture of the Characters page: both leads, faces whole, space on the left for the title.
CHARACTERS_OPENING = "art-jason-lucia-beach"
# Names for the groups the supporting cast falls into, keyed by the people in the group. Anything not listed gets a plain title.
CAST_GROUP_TITLES = {
    frozenset({"boobie-ike", "dre-quan-priest", "real-dimez"}): "Only Raw Records",
}
# Where each person sits on the relationship network (a 1200 x 560 canvas). Leads in the middle, the rest around them.
NETWORK_LAYOUT = {
    "jason-duval": (410, 250), "lucia-caminos": (790, 250), "brian-heder": (150, 110), "cal-hampton": (150, 390),
    "boobie-ike": (880, 100), "dre-quan-priest": (1060, 250), "real-dimez": (900, 420), "raul-bautista": (560, 450),
}
