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
CAST_ORDER = (       # the HOMEPAGE order. The Characters pages use CHARACTERS_ORDER below.
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

# The Characters section's one cast order (the owner's final order). The landing page, the jump bar, the numbering, the
# Explore default, the previous/next cards and the footer links all read this tuple and nothing else. It is a presentation
# order only: who is related to whom comes from character_relationships. (CAST_ORDER above belongs to the homepage reel.)
CHARACTERS_ORDER = (
    "jason-duval", "lucia-caminos", "cal-hampton", "brian-heder",
    "boobie-ike", "dre-quan-priest", "real-dimez", "raul-bautista",
)
CAST_LEADS = ("jason-duval", "lucia-caminos")

# Where the face (or, for a duo, the middle of the pair) sits in each picture, as fractions of its width and height, read
# from the pictures themselves. Every crop on the Characters pages is computed from these, so a head is never cut off.
IMAGE_FACE = {
    "shot-jason-duval-01": (0.66, 0.14), "shot-jason-duval-02": (0.37, 0.22), "shot-jason-duval-04": (0.31, 0.12),
    "shot-lucia-caminos-01": (0.60, 0.22), "shot-lucia-caminos-02": (0.48, 0.27), "shot-lucia-caminos-10": (0.54, 0.27),
    "shot-cal-hampton-01": (0.69, 0.15), "shot-cal-hampton-02": (0.49, 0.15),
    "shot-brian-heder-01": (0.52, 0.20), "shot-brian-heder-02": (0.58, 0.17),
    "shot-boobie-ike-01": (0.41, 0.15), "shot-boobie-ike-02": (0.32, 0.12),
    "shot-dequan-priest-01": (0.535, 0.10), "shot-dequan-priest-02": (0.73, 0.14),
    "shot-real-dimez-01": (0.47, 0.20), "art-real-dimez": (0.465, 0.17), "shot-real-dimez-02": (0.45, 0.20),
    "shot-raul-bautista-01": (0.62, 0.30), "shot-raul-bautista-02": (0.52, 0.16),
}
# Each person's pictures on the Characters pages (slugs of media_assets rows):
#   main   the artwork the motion sequence rests on, and so the large picture of "The story so far"
#   hero   the full-bleed picture opening the profile (never the same picture as `main`)
#   card   the large picture on the landing page (the two leads' spread, a supporting person's card)
#   second the smaller picture layered in front of `main` on the profile (None: the large picture stands alone)
#   shape  "wide" (4:3) or "tall" (4:5): the shape of that second picture
CHARACTER_STAGE = {
    "jason-duval": {"main": "shot-jason-duval-01", "hero": "shot-jason-duval-02", "card": "shot-jason-duval-02", "second": "shot-jason-duval-04", "shape": "wide"},
    "lucia-caminos": {"main": "shot-lucia-caminos-02", "hero": "shot-lucia-caminos-01", "card": "shot-lucia-caminos-01", "second": "shot-lucia-caminos-10", "shape": "wide"},
    "cal-hampton": {"main": "art-cal-hampton", "hero": "shot-cal-hampton-01", "card": "shot-cal-hampton-01", "second": "shot-cal-hampton-02", "shape": "tall"},
    "brian-heder": {"main": "art-brian-heder", "hero": "shot-brian-heder-02", "card": "shot-brian-heder-01", "second": "shot-brian-heder-01", "shape": "tall"},
    "boobie-ike": {"main": "art-boobie-ike", "hero": "shot-boobie-ike-01", "card": "shot-boobie-ike-02", "second": "shot-boobie-ike-02", "shape": "tall"},
    "dre-quan-priest": {"main": "art-dequan-priest", "hero": "shot-dequan-priest-02", "card": "shot-dequan-priest-02", "second": "shot-dequan-priest-02", "shape": "tall"},
    # Dre'Quan Priest and Real Dimez take their overlapping picture (and Real Dimez its landing picture) from LOCAL_STILLS when
    # those frames have been built; the entries here are what shows until then: Dre'Quan's tall cut of his pool-bar screenshot,
    # and for Real Dimez the artwork of both women and no overlap. The screenshot with Dre'Quan between the women is used
    # for neither person.
    "real-dimez": {"main": "art-real-dimez", "hero": "art-real-dimez", "card": "art-real-dimez", "second": None, "shape": "wide", "side": "left", "duo": True},
    "raul-bautista": {"main": "art-raul-bautista", "hero": "shot-raul-bautista-02", "card": "shot-raul-bautista-01", "second": "shot-raul-bautista-01", "shape": "tall"},
}
# Still frames cut from Rockstar's own character clips (python -m scripts.make_loops --stills), graded like the sequences that play
# on the same pages. `frame` is the 0-based frame of the clip (30 per second) and `crop` an optional (x, y, w, h) in the 2160 px
# source. Both women of Real Dimez are in every frame from 8 to 22 and nobody else is; the Dre'Quan frame is cut tall around him,
# in the recording studio, so it is a different scene from his pool-bar hero.
LOCAL_STILLS = {
    "real-dimez-duo": {"clip": "Real_Dimez_Video_Clip", "frame": 10},
    "dre-quan-priest-studio": {"clip": "DreQuan_Priest_Video_Clip", "frame": 13, "crop": (720, 0, 1296, 1620)},
}
# Where a profile uses one: role -> (still, position on the grid the pages use, shape of the overlapping picture)
LOCAL_STILL_PICKS = {
    "real-dimez": {"second": ("real-dimez-duo", "50% 0%", "wide")},
    "dre-quan-priest": {"second": ("dre-quan-priest-studio", "50% 0%", "tall")},
}
# Profiles that end after their connections: no "From the footage and artwork" gallery (Real Dimez, whose official pictures
# are few and mostly of other people). Jason and Lucia keep theirs.
NO_GALLERY = frozenset({"real-dimez"})
# Portraits (the relationship network, the connection cards on the profiles, the phone list): a head cut from Rockstar's own
# character artwork. `heads` are read by eye from the pictures at full resolution, one per face: (x, y, h) = the middle of the
# whole head (hair or hat to chin) as a fraction of the picture's width and height, and its height as a fraction of the
# picture's height (`bg` is the colour of the picture's top edge, which fills the circle above a head that sits at the very top of its picture; an optional fourth number zooms that one head in or out, to keep a neighbour out of the circle). Each head is scaled to the same share of its circle and centred in it, so the eyes sit in the upper
# middle and every portrait has the same weight. A duo gets one circle per member.
AVATAR_HEAD = 0.72        # share of the circle's height the head fills
AVATARS = {
    "jason-duval": {"media": "art-jason-lucia-01", "heads": [(0.556, 0.136, 0.17, 0.90)]},
    "lucia-caminos": {"media": "art-jason-lucia-02", "heads": [(0.400, 0.290, 0.175)]},
    "cal-hampton": {"media": "art-cal-hampton", "bg": "#83a3c7", "heads": [(0.490, 0.140, 0.26)]},
    "brian-heder": {"media": "art-brian-heder", "bg": "#7d7fc5", "heads": [(0.645, 0.155, 0.29)]},
    "boobie-ike": {"media": "art-boobie-ike", "bg": "#504e6b", "heads": [(0.505, 0.155, 0.20)]},
    "dre-quan-priest": {"media": "art-dequan-priest", "bg": "#6f61a0", "heads": [(0.595, 0.100, 0.155)]},
    "real-dimez": {"media": "art-real-dimez", "bg": "#8a80c5", "heads": [(0.330, 0.200, 0.215), (0.632, 0.118, 0.155)]},
    "raul-bautista": {"media": "art-raul-bautista", "bg": "#a0b987", "heads": [(0.540, 0.115, 0.185)]},
}
# Motion portraits on the Characters pages. Rockstar shot the two leads in 16:9 and the other six square, so each person
# is shown in the shape the footage was shot in, never stretched into a shape it was not (the old extended widescreen
# frame is kept only for the homepage reel). Built by `python -m scripts.make_loops --portraits`.
PORTRAIT_SHAPE = {"jason-duval": "wide", "lucia-caminos": "wide"}      # everyone else is "square"
# The partner banner: both protagonists' faces large and lit, taken from Rockstar's own Jason and Lucia screenshots.
CAST_TOGETHER = "shot-jason-and-lucia-01"
# Opening picture of the Characters page: both leads, faces whole, space on the left for the title.
CHARACTERS_OPENING = "art-jason-lucia-beach"
# Names for the groups the supporting cast falls into, keyed by the people in the group. Anything not listed gets a plain title.
CAST_GROUP_TITLES = {
    frozenset({"boobie-ike", "dre-quan-priest", "real-dimez"}): "Only Raw Records",
}
# Where each person sits on the relationship network (a 1200 x 560 canvas). Leads in the middle, the rest around them.
# People drawn in a column have their name beside the picture instead of under it, so no line ever crosses a name.
NETWORK_NAME_RIGHT = frozenset({"boobie-ike", "dre-quan-priest", "real-dimez"})
NETWORK_LAYOUT = {
    "jason-duval": (410, 250), "lucia-caminos": (790, 250), "brian-heder": (150, 110), "cal-hampton": (150, 390),
    "boobie-ike": (930, 100), "dre-quan-priest": (930, 285), "real-dimez": (930, 470), "raul-bautista": (560, 450),
}
