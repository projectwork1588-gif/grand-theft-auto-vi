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
# The landing tile of a person whose artwork is already the large picture beside it rests on a still frame of their own clip
# instead (slug -> a LOCAL_STILLS name), so the tile and the picture are not the same picture. The sequence is the profile's,
# with the artwork replaced: media/clips/<slug>-landing.mp4 and .jpg. The profile keeps its artwork sequence.
LANDING_REST = {"real-dimez": "real-dimez-duo"}
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


# ---------------------------------------------------------------------------------------------------------------------
# Garage (Gate 3B). Every official vehicle has its pictures chosen by hand: nothing here states a fact about a vehicle, it
# only says which of Rockstar's screenshots to use where, what is visibly in each one (for the caption and the alt text) and
# where the subject sits so every crop keeps it.
#
#   face   (x, y) the middle of the subject as fractions of the picture's width and height, for wide boxes
#   phone  the same, for the tall crops phones get (the front of a long car, not its middle)
#   alt    what the picture shows, in the words of someone describing it: no names, no specifications
GARAGE_FRAMES = {
    "vehicle-grotti-cheetah-01": {"face": (0.38, 0.70), "phone": (0.30, 0.70), "alt": "White coupe with red stripes parked in front of a curved car park at sunset"},
    "vehicle-grotti-cheetah-02": {"face": (0.70, 0.55), "phone": (0.78, 0.55), "alt": "Front of the white coupe with its headlights lit on a cobbled street at golden hour"},
    "vehicle-grotti-cheetah-03": {"face": (0.40, 0.55), "phone": (0.40, 0.55), "alt": "Rear three-quarter of the white coupe: striped engine cover, round tail lights and a wheel"},
    "vehicle-grotti-cheetah-04": {"face": (0.55, 0.50), "phone": (0.55, 0.50), "alt": "The coupe's red leather interior seen through the open driver's door"},
    "vehicle-vapid-dominator-buggy-01": {"face": (0.35, 0.52), "phone": (0.35, 0.52), "alt": "Mud-splattered buggy with roof lights ploughing along a wet forest trail"},
    "vehicle-vapid-dominator-buggy-02": {"face": (0.62, 0.62), "phone": (0.62, 0.62), "alt": "The buggy parked on gravel outside a workshop, on oversized tyres with a steel bumper"},
    "vehicle-vapid-dominator-buggy-03": {"face": (0.45, 0.55), "phone": (0.45, 0.55), "alt": "Close-up of the buggy's front: steel bar, yellow driving lights and a crossed headlight"},
    "vehicle-vapid-dominator-buggy-04": {"face": (0.55, 0.50), "phone": (0.55, 0.50), "alt": "The buggy's worn dashboard and steering wheel, flecked with mud"},
    "vehicle-shitzu-squalo-01": {"face": (0.25, 0.68), "phone": (0.30, 0.68), "alt": "White speedboat cutting across a bay with the lit skyline behind it at dusk"},
    "vehicle-shitzu-squalo-02": {"face": (0.50, 0.45), "phone": (0.50, 0.45), "alt": "The boat seen from above, leaving a white wake on dark water"},
    "vehicle-shitzu-squalo-03": {"face": (0.38, 0.52), "phone": (0.38, 0.52), "alt": "Close-up of the white hull and its Squalo lettering in bright sun"},
    "vehicle-shitzu-squalo-04": {"face": (0.65, 0.55), "phone": (0.65, 0.55), "alt": "Two people on the boat's deck above clear blue water, with a dolphin alongside"},
    "vehicle-vapid-stanier-01": {"face": (0.50, 0.65), "phone": (0.78, 0.62), "alt": "Yellow and white vintage sedan on a neon-lit street at night, headlights on"},
    "vehicle-vapid-stanier-02": {"face": (0.45, 0.45), "phone": (0.45, 0.45), "alt": "Two occupants seen through the sedan's windscreen, lit in purple and pink"},
    "vehicle-vapid-stanier-03": {"face": (0.50, 0.60), "phone": (0.50, 0.60), "alt": "Side of the sedan: a wheel, the chrome mirror and the Stanier script on the door"},
    "vehicle-vapid-stanier-04": {"face": (0.64, 0.45), "phone": (0.70, 0.45), "alt": "The sedan's tail fin and round red brake light under a night sky with palms"},
    "vehicle-vapid-ganado-01": {"face": (0.50, 0.65), "phone": (0.66, 0.66), "alt": "Yellow retro pickup with red racing stripes on a coast road, the sea behind it"},
    "vehicle-dinka-enduro-01": {"face": (0.55, 0.52), "phone": (0.55, 0.52), "alt": "Green trail bike with knobby tyres parked side-on against a teal corrugated shutter"},
    "vehicle-crest-kayak-01": {"face": (0.62, 0.50), "phone": (0.60, 0.50), "alt": "A paddler in an orange kayak on glowing water at sunset, a wooden pier behind"},
    "garage-jasons-safehouse": {"face": (0.50, 0.55), "phone": (0.40, 0.62), "alt": "A stilt house at the water's edge with a pickup, a motorcycle and a kayak outside it"},
    "garage-rideout-customs-01": {"face": (0.66, 0.62), "phone": (0.66, 0.62), "alt": "A gold-green lowrider with gold wheels, lit by a glowing orange ring"},
    "garage-one-eyed-willies-01": {"face": (0.62, 0.52), "phone": (0.62, 0.52), "alt": "A bright green 4x4 on oversized tyres in a burst of green light"},
    "garage-classic-cars-02": {"face": (0.60, 0.50), "phone": (0.60, 0.50), "alt": "The rear of a turquoise coupe with a dark stripe, a small wing and chrome wheels"},
    "garage-classic-cars-04": {"face": (0.50, 0.55), "phone": (0.50, 0.55), "alt": "A red and white race car with a number on its door, open cockpit, seen close up"},
}
# How each vehicle is presented (slugs of its media_assets rows; the vehicle's pages follow this, so each is art-directed on its own):
#   stage      the opening picture on the Garage page and the top of the vehicle's own page: a whole vehicle where the picture allows
#   card       its tile in the showroom (a different picture from the stage wherever the vehicle has more than one)
#   card_zoom  (zoom, x, y): for a vehicle with one picture, its tile is that picture drawn closer on (x, y), so it is not a copy
#   side       which side the words sit on, opposite the vehicle (left or right); vpos "top" puts them above a long, low car
#   theme      a few words for the mood of the picture (what it shows, not a claim about the vehicle)
#   story      the showcase on its page: "mosaic" (one large picture and two beside it), "mosaic-flip" (the same, mirrored),
#              "viewer" (one large picture, thumbnails, previous and next), "panorama" (one wide picture, two beneath it),
#              "context" (a vehicle's own set has no second picture: a smaller, labelled cut of a Rockstar scene it appears in, drawn around the vehicle), or "none" (a vehicle with one picture: the opening is all of it)
#   gallery    the showcase pictures, in order (never the stage picture)
#   context    the scene picture, where the vehicle sits in it (focus x, y as fractions), how close to draw it (zoom), the side the figure sits on, and its words
GARAGE_PICKS = {
    "grotti-cheetah": {"stage": "vehicle-grotti-cheetah-01", "card": "vehicle-grotti-cheetah-02", "side": "right", "vpos": "bottom", "theme": "Golden hour",
                       "story": "mosaic", "gallery": ["vehicle-grotti-cheetah-02", "vehicle-grotti-cheetah-03", "vehicle-grotti-cheetah-04"]},
    "vapid-dominator-buggy": {"stage": "vehicle-vapid-dominator-buggy-01", "card": "vehicle-vapid-dominator-buggy-02", "side": "right", "vpos": "bottom", "theme": "Mud and mist",
                              "story": "viewer", "gallery": ["vehicle-vapid-dominator-buggy-02", "vehicle-vapid-dominator-buggy-03", "vehicle-vapid-dominator-buggy-04"]},
    "shitzu-squalo": {"stage": "vehicle-shitzu-squalo-01", "card": "vehicle-shitzu-squalo-02", "side": "right", "vpos": "bottom", "theme": "Dusk on the bay",
                      "story": "panorama", "gallery": ["vehicle-shitzu-squalo-02", "vehicle-shitzu-squalo-03", "vehicle-shitzu-squalo-04"]},
    "vapid-stanier": {"stage": "vehicle-vapid-stanier-01", "card": "vehicle-vapid-stanier-04", "side": "left", "vpos": "top", "theme": "Neon night",
                      "story": "mosaic-flip", "gallery": ["vehicle-vapid-stanier-02", "vehicle-vapid-stanier-03", "vehicle-vapid-stanier-04"]},
    "vapid-ganado": {"stage": "vehicle-vapid-ganado-01", "card": "vehicle-vapid-ganado-01", "card_zoom": (1.5, 0.80, 0.66), "side": "left", "vpos": "top", "theme": "Coast road",
                     "story": "none", "gallery": []},
    "dinka-enduro": {"stage": "vehicle-dinka-enduro-01", "card": "vehicle-dinka-enduro-01", "card_zoom": (1.45, 0.50, 0.40), "side": "left", "vpos": "bottom", "theme": "Garage door",
                     "story": "context", "gallery": [],
                     "context": {"slug": "garage-jasons-safehouse", "focus": (0.485, 0.81), "zoom": 3.0, "flip": False, "title": "In its setting",
                                 "text": "Rockstar shows it parked beside a stilt house on the water, in its Jason's Safehouse Vehicles screenshots."}},
    "crest-kayak": {"stage": "vehicle-crest-kayak-01", "card": "vehicle-crest-kayak-01", "card_zoom": (1.4, 0.62, 0.40), "side": "left", "vpos": "bottom", "theme": "Sunset paddle",
                    "story": "context", "gallery": [],
                    "context": {"slug": "garage-jasons-safehouse", "focus": (0.615, 0.765), "zoom": 4, "flip": True, "title": "On the shore",
                                "text": "The same safehouse set shows the kayak pulled up on the shore beside the house."}},
}
# The Garage's pictures of machines Rockstar does not name: its own set titles are the captions, and nothing more is claimed.
GARAGE_MOMENTS = (
    ("garage-rideout-customs-01", "Rideout Customs Mod Shop"),
    ("garage-one-eyed-willies-01", "One-Eyed Willie's Mod Shop"),
    ("garage-classic-cars-02", "Classic Car Collection"),
    ("garage-classic-cars-04", "Classic Car Collection"),
)

# Garage concept: the pictures the collection's chapters use, chosen so a machine is not shown by the picture that opens the page
# wherever it has a second one. `main` is the large picture, `second` a close-up of another part of the same machine with `second_label`
# (what it shows, nothing more); a machine with one picture has `zoom` (scale, x, y) so the collection draws it closer than the opening does.
# `role` is how its chapter draws it: perf (a feature stage), street_a and street_b (a zigzag), duo_a and duo_b (a diptych), sea_a and finale
# (the water chapter's two stages); any other machine (and every filtered list) is drawn as a plain card.
GARAGE_SPREADS = {
    "grotti-cheetah": {"role": "perf", "main": "vehicle-grotti-cheetah-02", "second": "vehicle-grotti-cheetah-04", "second_label": "The cabin"},
    "vapid-stanier": {"role": "street_a", "main": "vehicle-vapid-stanier-02", "second": "vehicle-vapid-stanier-04", "second_label": "The tail fin"},
    "vapid-ganado": {"role": "street_b", "main": "vehicle-vapid-ganado-01", "zoom": (1.15, 0.58, 0.56)},
    "dinka-enduro": {"role": "duo_b", "main": "vehicle-dinka-enduro-01", "face": (0.53, 0.5)},
    "vapid-dominator-buggy": {"role": "duo_a", "main": "vehicle-vapid-dominator-buggy-02", "face": (0.58, 0.6)},
    "shitzu-squalo": {"role": "sea_a", "main": "vehicle-shitzu-squalo-02", "second": "vehicle-shitzu-squalo-04", "second_label": "On deck"},
    "crest-kayak": {"role": "finale", "main": "vehicle-crest-kayak-01"},
}
# The words the concept page prints about each machine (the opening and the collection use the same line). They describe what Rockstar's pictures show and
# nothing else: no specification, no price, no story. The database keeps its own, plainer summary for the vehicle's page.
GARAGE_COPY = {
    "grotti-cheetah": "White paint, red racing stripes and the last of the golden light.",
    "vapid-dominator-buggy": "Mud-flecked, steel-barred and sitting high on oversized tyres.",
    "shitzu-squalo": "White hull, dark water and the city lights coming on across the bay.",
    "vapid-stanier": "Yellow and white, all chrome and tail fin, rolling through the neon.",
    "vapid-ganado": "Red racing stripes on a yellow pickup, with the sea running alongside.",
    "dinka-enduro": "Green, lean and on knobby tyres, set against a teal garage door.",
    "crest-kayak": "An orange kayak on calm water, the sunset coming in low.",
}
# How each opening scene is composed. `plate` says where the words sit so they never cross the machine: br (lower right, the machine is on the
# left), ml (left, half way down: the machine is to the right) or wide (a long, low machine drawn whole in the right three quarters of the window,
# the words in the open column on its left).
GARAGE_SCENES = {
    "grotti-cheetah": {"plate": "br", "subject": ((0.11, 0.51, 0.65, 0.87),)},
    "vapid-dominator-buggy": {"plate": "br", "subject": ((0.02, 0.15, 0.62, 0.62), (0.02, 0.55, 0.50, 0.88))},
    "shitzu-squalo": {"plate": "br", "subject": ((0.05, 0.52, 0.58, 0.87),)},
    "vapid-stanier": {"plate": "tr", "subject": ((0.12, 0.17, 0.66, 0.92), (0.60, 0.36, 0.95, 0.90), (0.06, 0.38, 0.16, 0.86))},
    "vapid-ganado": {"plate": "tr", "subject": ((0.24, 0.24, 0.66, 0.90), (0.58, 0.36, 0.95, 0.84), (0.06, 0.44, 0.30, 0.86))},
    "dinka-enduro": {"plate": "ml", "px": 0, "subject": ((0.29, 0.03, 0.84, 0.95),)},      # px 0: the picture is held to the left of its frame, which moves the bike right and gives the words room
    "crest-kayak": {"plate": "ml", "subject": ((0.33, 0.05, 0.78, 0.60), (0.40, 0.45, 0.70, 0.66), (0.15, 0.62, 0.68, 0.96))},
}
# `subject` is where the machine sits in its opening picture (one or more boxes x0, y0, x1, y1, as fractions of the picture), measured by eye against a 5 percent grid. The tests use it to check, in a real
# browser, that the words never cross the machine and that the machine is not cut off, at the window sizes the opening is built for.
# The collection's four chapters: visual themes for the eye, not categories and not claims about the game. A machine the list does not name
# (one added to the database later) is shown after the chapters.
GARAGE_CHAPTERS = (
    {"key": "performance", "title": "Performance", "accent": "#ff7396", "slugs": ("grotti-cheetah",),
     "line": "White paint and red stripes in the last of the evening light."},
    {"key": "street", "title": "Street & Classics", "accent": "#ffbf47", "slugs": ("vapid-stanier", "vapid-ganado"),
     "line": "Chrome and tail fins under the neon, then a striped pickup on the coast road."},
    {"key": "beyond", "title": "Beyond the Pavement", "accent": "#c4d15a", "slugs": ("vapid-dominator-buggy", "dinka-enduro"),
     "line": "Mud and gravel on one side, a teal garage door on the other."},
    {"key": "water", "title": "On the Water", "accent": "#59d6ee", "slugs": ("shitzu-squalo", "crest-kayak"),
     "line": "A bay at dusk, then a paddle into the sunset."},
)

# ---------------------------------------------------------------------------------------------------------------------
# Stage B: the seven vehicle pages. Nothing here states a fact about a vehicle: it says how each page is told and what each picture visibly shows.
#   sequence   how the page after its opening is told, chosen for the pictures Rockstar has shown of that machine:
#                stage_pair      a wide picture that bleeds off the window, then two together (three pictures)
#                panorama_pair   a full-width picture, then two together
#                viewer          one large picture with the others as thumbnails, previous and next
#                close           a machine with one picture: that picture drawn closer, in three crops (see GARAGE_CLOSE)
#                context         a smaller cut of the Rockstar scene the machine appears in (GARAGE_PICKS context), then the three crops
#   side       which edge the first picture of a stage_pair bleeds off
GARAGE_DETAIL = {
    "grotti-cheetah": {"sequence": "stage_pair", "side": "right"},
    "vapid-dominator-buggy": {"sequence": "viewer"},
    "shitzu-squalo": {"sequence": "panorama_pair"},
    "vapid-stanier": {"sequence": "stage_pair", "side": "left"},
    "vapid-ganado": {"sequence": "close"},
    "dinka-enduro": {"sequence": "context"},
    "crest-kayak": {"sequence": "context"},
}
# A machine with one picture is shown closer: crops of that same picture, each (label, x, y, zoom) where (x, y) is what the label names, as fractions of the picture.
# The labels name only what can be seen in them. The zoom is one of the values garage.css has a rule for.
GARAGE_CLOSE = {
    "vapid-ganado": (("The hood and its red stripes", 0.66, 0.50, 2.25), ("The grille and its four headlights", 0.79, 0.62, 2.5), ("Behind the wheel", 0.46, 0.29, 2.75)),
    "dinka-enduro": (("The round headlight and its forks", 0.53, 0.30, 2.5), ("The green tank and its Dinka mark", 0.64, 0.36, 2.5), ("The engine and its exhaust", 0.68, 0.55, 2.25)),
    "crest-kayak": (("The paddle catching the sun", 0.72, 0.18, 2.25), ("The paddler, back to us", 0.50, 0.36, 2.0), ("The orange hull and its Crest lettering", 0.42, 0.78, 2.5)),
}
# Short captions for the pictures a vehicle page shows (what each one shows, in plain words; the longer alt text above stays for screen readers).
GARAGE_CAPTIONS = {
    "vehicle-grotti-cheetah-02": "Headlights lit on a cobbled street at golden hour",
    "vehicle-grotti-cheetah-03": "The rear: striped engine cover and round tail lights",
    "vehicle-grotti-cheetah-04": "The red leather cabin, the door open",
    "vehicle-vapid-dominator-buggy-02": "Outside a workshop, on oversized tyres",
    "vehicle-vapid-dominator-buggy-03": "The steel bar and the yellow driving lights",
    "vehicle-vapid-dominator-buggy-04": "The worn dashboard, flecked with mud",
    "vehicle-shitzu-squalo-02": "From above: a white wake on dark water",
    "vehicle-shitzu-squalo-03": "The white hull and its black Squalo lettering",
    "vehicle-shitzu-squalo-04": "On deck, with a dolphin alongside",
    "vehicle-vapid-stanier-02": "Two occupants through the windscreen, lit purple and pink",
    "vehicle-vapid-stanier-03": "The Stanier script on the door, beside a chrome mirror and a wheel",
    "vehicle-vapid-stanier-04": "The tail fin and its round red brake light under a night sky",
}


# ---------------------------------------------------------------- Leonida / Regions: one grammar, six photographic identities
# Art direction for /regions and /regions/<slug>. Every picture is one of Rockstar's own screenshots or postcards already linked to the region in the database; this only
# chooses which ones and where the camera rests. The pages share one structure (an opening, the description beside a picture, the screenshots in pairs, the postcard, the
# next region); a region's identity is its photography, its crop and its accent colour. Nothing here states a fact about a region. A slug that is not in the database is
# skipped, a region with fewer pictures simply has a shorter page, and any picture not named here still follows, so nothing Rockstar published is lost.
#   hero      the opening picture of the region page
#   intro     the picture set beside the description (None: the description stands alone, as it does for the two regions Rockstar has shown least)
#   story     the screenshots after them, in order
#   feature   the two pictures of the region's showcase on the landing page: the main one and a second
REGION_ART = {
    "vice-city": {"hero": "shot-vice-city-11", "intro": "shot-vice-city-03", "feature": ("shot-vice-city-01", "shot-vice-city-10"),
                  "story": ("shot-vice-city-01", "shot-vice-city-10", "shot-vice-city-08", "shot-vice-city-02", "shot-vice-city-04", "shot-vice-city-09")},
    "leonida-keys": {"hero": "shot-leonida-keys-01", "intro": "shot-leonida-keys-06", "feature": ("shot-leonida-keys-01", "shot-leonida-keys-05"),
                     "story": ("shot-leonida-keys-05", "shot-leonida-keys-02", "shot-leonida-keys-03")},
    "grassrivers": {"hero": "shot-grassrivers-05", "intro": "shot-grassrivers-03", "feature": ("shot-grassrivers-05", "shot-grassrivers-04"),
                    "story": ("shot-grassrivers-04", "shot-grassrivers-02", "shot-grassrivers-01")},
    "port-gellhorn": {"hero": "shot-port-gellhorn-06", "intro": None, "feature": ("shot-port-gellhorn-06", "shot-port-gellhorn-01"),
                      "story": ("shot-port-gellhorn-01", "shot-port-gellhorn-02")},
    "ambrosia": {"hero": "shot-ambrosia-04", "intro": None, "feature": ("shot-ambrosia-04", "shot-ambrosia-02"),
                 "story": ("shot-ambrosia-01", "shot-ambrosia-02")},
    "mount-kalaga": {"hero": "shot-mount-kalaga-04", "intro": "shot-mount-kalaga-03", "feature": ("shot-mount-kalaga-04", "shot-mount-kalaga-02"),
                     "story": ("shot-mount-kalaga-02", "shot-mount-kalaga-01", "shot-mount-kalaga-05", "shot-mount-kalaga-06")},
}


# Where the subject of each Leonida / Regions picture is, as fractions of the picture (across, down), found by looking at every one of Rockstar's pictures. Every one is 16:9,
# so a box of any other shape shows a window of it; the page centres that window on this point (clamped to the picture) for each shape it draws the picture in. A picture
# that is not listed rests at its centre. A picture whose defining detail is not where its centre of interest is (a sign at one edge, a building at the other) may name a second
# point for the narrow boxes. Nothing here states a fact about a region.
REGION_FOCUS = {
    "shot-vice-city-01": (0.50, 0.52), "shot-vice-city-02": (0.83, 0.45), "shot-vice-city-03": (0.54, 0.50), "shot-vice-city-04": (0.50, 0.30),
    "shot-vice-city-08": (0.58, 0.45), "shot-vice-city-09": (0.45, 0.62), "shot-vice-city-10": (0.38, 0.45), "shot-vice-city-11": (0.42, 0.40),
    "shot-leonida-keys-01": (0.66, 0.58), "shot-leonida-keys-02": (0.48, 0.45), "shot-leonida-keys-03": (0.50, 0.45), "shot-leonida-keys-05": (0.50, 0.55),
    "shot-leonida-keys-06": (0.58, 0.45),
    "shot-grassrivers-01": (0.57, 0.45), "shot-grassrivers-02": (0.66, 0.48), "shot-grassrivers-03": (0.27, 0.62), "shot-grassrivers-04": (0.50, 0.55),
    "shot-grassrivers-05": (0.66, 0.50),
    "shot-port-gellhorn-01": {"*": (0.50, 0.45), "narrow": (0.24, 0.32), "side": (0.24, 0.32), "about": (0.24, 0.32)},
    "shot-port-gellhorn-02": {"*": (0.50, 0.40), "narrow": (0.38, 0.40), "side": (0.38, 0.40), "about": (0.38, 0.40)},
    "shot-port-gellhorn-06": (0.40, 0.60),
    "shot-ambrosia-01": (0.60, 0.55), "shot-ambrosia-02": (0.75, 0.55), "shot-ambrosia-04": (0.32, 0.52),
    "shot-mount-kalaga-01": (0.52, 0.45), "shot-mount-kalaga-02": (0.48, 0.38), "shot-mount-kalaga-03": (0.20, 0.55), "shot-mount-kalaga-04": (0.58, 0.60),
    "shot-mount-kalaga-05": (0.50, 0.55), "shot-mount-kalaga-06": (0.52, 0.65),
}
# The boxes the pages draw a picture in, width over height: (wide screens, tablets and phones). A box is a shape, not a size, so the focal point holds at every width.
REGION_BOXES = {
    "hero": (1.15, 1.45),     # the opening: the panel's picture beside the words / the picture above them
    "main": (1.6, 1.5),       # a showcase's main picture
    "side": (0.8, 0.8),       # a showcase's second picture, a narrow one beside it
    "wide": (1.6, 1.5),       # a gallery picture in a wide slot
    "narrow": (0.875, 1.5),   # a gallery picture in a narrow slot
    "pano": (2.33, 1.5),      # an odd last gallery picture across the page
    "about": (0.8, 1.33),     # the picture beside the description
    "thumb": (1.6, 1.6),      # the strip of six
    "stage": (3.0, 1.15),     # the next region
    "tile": (1.5, 1.85),      # the six choices in the landing opening
}
