"""View-models for the public pages: existing services plus related content, media and editorial choices.

Pages reuse the same services as the JSON API, so a page and its API endpoint can never disagree.
The public Garage is the official vehicles only: those Rockstar names and shows in its own screenshots.
Concept vehicles stay in the database for the story archive but get no public page.
"""
from werkzeug.exceptions import NotFound

from .. import local_media, media_slots, media_urls
from ..repositories import characters as characters_repo
from ..repositories import media, missions as missions_repo, regions as regions_repo
from ..repositories import vehicles as vehicles_repo
from . import characters, locations, missions, regions, validation as v, vehicles


# ---------------------------------------------------------------- small helpers
def _in_rockstar_order(rows):
    """Regions in the order Rockstar lists them. Unknown slugs go last, alphabetically."""
    order = {slug: i for i, slug in enumerate(media_slots.REGION_ORDER)}
    return sorted(rows, key=lambda r: (order.get(r["slug"], len(order)), r["name"]))


def _in_cast_order(rows):
    """The cast in the one explicit playlist order. Anyone not listed goes last, alphabetically."""
    order = {slug: i for i, slug in enumerate(media_slots.CAST_ORDER)}
    return sorted(rows, key=lambda r: (order.get(r["slug"], len(order)), r["full_name"]))


def _page_cover(page):
    """Official backdrop image for the top of a catalogue page, or None (the page then uses its fallback)."""
    slug = media_slots.PAGE_HERO_SLUGS.get(page)
    return media.by_slugs([slug]).get(slug) if slug else None


def _attach_covers(kind, rows, ids_by_slug, overrides=None):
    """Give each row a `cover`. `overrides` maps an entity slug to the slug of a preferred media row."""
    ids = ids_by_slug([row["slug"] for row in rows])
    covers = media.covers(kind, ids.values())
    preferred = media.by_slugs(set((overrides or {}).values())) if overrides else {}
    for row in rows:
        chosen = preferred.get((overrides or {}).get(row["slug"]))
        row["cover"] = chosen or covers.get(ids.get(row["slug"]))
    return rows


def _local_clip(slug):
    """Relative path of this character's locally built loop, or None when the file has not been built."""
    path = f"clips/{slug}.mp4"
    return path if local_media.is_servable(path) else None


def _local_poster(slug):
    path = f"clips/{slug}.jpg"
    return path if local_media.is_servable(path) else None


# ---------------------------------------------------------------- characters
def character_index(args):
    result = characters.list_characters(args)
    _attach_covers("character", result["data"], characters_repo.ids_by_slug, media_slots.CHARACTER_COVERS)
    result["regions"] = regions_repo.list_all()
    result["hero_cover"] = _page_cover("characters")
    filtered = any(result["filters"].get(k) for k in ("q", "status", "region")) or result["pagination"]["page"] > 1
    result["editorial"] = not filtered and result["pagination"]["pages"] == 1
    rows = result["data"]
    result["leads"] = [r for r in rows if r["slug"] in media_slots.CHARACTER_COVERS and r["content_status"] == "official"]
    lead_slugs = {r["slug"] for r in result["leads"]}
    result["supporting"] = [r for r in rows if r["content_status"] == "official" and r["slug"] not in lead_slugs]
    result["concepts"] = [r for r in rows if r["content_status"] != "official"]
    return result


def character_detail(slug):
    character, character_id = characters.get_character_with_id(slug)
    character["costars"] = characters_repo.costars_for(character_id)
    character["gallery"] = media.for_entity("character", character_id)
    preferred_slug = media_slots.CHARACTER_COVERS.get(slug)
    preferred = media.by_slugs([preferred_slug]).get(preferred_slug) if preferred_slug else None
    character["cover"] = preferred or (character["gallery"][0] if character["gallery"] else None)
    if preferred:  # lead the gallery with the chosen image
        character["gallery"] = [preferred] + [m for m in character["gallery"] if m["slug"] != preferred["slug"]]
    clips = {c["character_slug"]: c for c in media.character_clips()}
    character["clip"] = clips.get(slug)
    character["clip_video"] = _local_clip(slug)
    character["clip_poster"] = _local_poster(slug)
    return character


# ---------------------------------------------------------------- vehicles (public garage = official only)
def vehicle_index(args):
    forced = {"sort": "featured", **args.to_dict(), "status": "official"}
    result = vehicles.list_vehicles(forced)
    result["filters"].pop("status", None)
    _attach_covers("vehicle", result["data"], vehicles_repo.ids_by_slug)
    result["categories"] = [c for c in vehicles_repo.categories_with_counts("official") if c["vehicle_count"]]
    result["hero_cover"] = _page_cover("vehicles")
    return result


def vehicle_detail(slug):
    vehicle, vehicle_id = vehicles.get_vehicle_with_id(slug)
    if vehicle["content_status"] != "official":
        raise NotFound("That vehicle is not part of the public garage.")
    vehicle["gallery"] = media.for_entity("vehicle", vehicle_id)
    vehicle["cover"] = vehicle["gallery"][0] if vehicle["gallery"] else None
    others = vehicles.list_vehicles({"status": "official", "sort": "featured", "per_page": "12"})["data"]
    vehicle["more"] = _attach_covers("vehicle", [o for o in others if o["slug"] != slug], vehicles_repo.ids_by_slug)
    return vehicle


# ---------------------------------------------------------------- regions
def region_index(args):
    result = regions.list_regions(args)
    result["data"] = _in_rockstar_order(result["data"])
    _attach_covers("region", result["data"], regions_repo.ids_by_slug, media_slots.REGION_STAGE)
    result["hero_cover"] = _page_cover("regions")
    return result


def region_detail(slug):
    region, region_id = regions.get_region_with_id(slug)
    region["missions"] = missions_repo.in_region(region_id)
    stage_slug = media_slots.REGION_STAGE.get(slug)
    stage = media.by_slugs([stage_slug]).get(stage_slug) if stage_slug else None
    gallery = media.for_entity("region", region_id, limit=16)
    if stage:
        gallery = [stage] + [m for m in gallery if m["slug"] != stage["slug"]]
    region["gallery"] = gallery
    region["cover"] = gallery[0] if gallery else None
    others = _in_rockstar_order(regions_repo.list_all())
    region["other_regions"] = [r for r in others if r["slug"] != slug]
    _attach_covers("region", region["other_regions"], regions_repo.ids_by_slug, media_slots.REGION_STAGE)
    return region


# ---------------------------------------------------------------- locations
def location_index(args):
    result = locations.list_locations(args)
    result["regions"] = regions_repo.list_all()
    result["location_types"] = v.LOCATION_TYPES
    result["hero_cover"] = _page_cover("locations")
    return result


def location_detail(slug):
    location = locations.get_location(slug)
    # Official region imagery gives the location context, labelled as the region's own artwork.
    region_ids = regions_repo.ids_by_slug([location["region_slug"]])
    stage_slug = media_slots.REGION_STAGE.get(location["region_slug"])
    stage = media.by_slugs([stage_slug]).get(stage_slug) if stage_slug else None
    covers = media.covers("region", region_ids.values())
    location["region_cover"] = stage or covers.get(region_ids.get(location["region_slug"]))
    return location


# ---------------------------------------------------------------- missions
def mission_index(args):
    result = missions.list_missions(args)
    result["mission_types"] = v.MISSION_TYPES
    result["hero_cover"] = _page_cover("missions")
    return result


def mission_detail(slug):
    mission = missions.get_mission(slug)
    # The story's main setting lends its region's official artwork as a captioned backdrop.
    setting = next((l for l in mission["locations"] if l["is_primary"]), mission["locations"][0] if mission["locations"] else None)
    mission["backdrop"] = None
    if setting:
        stage_slug = media_slots.REGION_STAGE.get(setting["region_slug"])
        stage = media.by_slugs([stage_slug]).get(stage_slug) if stage_slug else None
        ids = regions_repo.ids_by_slug([setting["region_slug"]])
        mission["backdrop"] = stage or media.covers("region", ids.values()).get(ids.get(setting["region_slug"]))
        mission["backdrop_region"] = setting["region_name"]
    return mission


# ---------------------------------------------------------------- homepage
def home():
    official = characters_repo.featured_official(8)
    covers = media.covers("character", [c["character_id"] for c in official])
    preferred = media.by_slugs(set(media_slots.CHARACTER_COVERS.values()))
    for c in official:
        chosen = preferred.get(media_slots.CHARACTER_COVERS.get(c["slug"]))
        c["cover"] = chosen or covers.get(c["character_id"])
        c.pop("character_id")
        c["clip"] = _local_clip(c["slug"])
        c["clip_poster"] = _local_poster(c["slug"])

    leads = [c for c in official if c["slug"] in ("jason-duval", "lucia-caminos")]
    cast = _in_cast_order(official)

    reel = None
    manifest = local_media.manifest()
    if manifest and local_media.is_servable("clips/leonida-reel.mp4"):
        reel = {
            "video": "clips/leonida-reel.mp4",
            "poster": "clips/leonida-reel.jpg" if local_media.is_servable("clips/leonida-reel.jpg") else None,
            "duration": manifest["duration"],
            "segments": manifest["segments"],
        }

    if reel:
        times = {seg["slug"]: seg for seg in reel["segments"]}
        for c in cast:
            if c["slug"] in times:
                c["start"], c["end"] = times[c["slug"]]["start"], times[c["slug"]]["end"]


    region_cards = _in_rockstar_order(regions_repo.list_all())
    _attach_covers("region", region_cards, regions_repo.ids_by_slug, media_slots.REGION_STAGE)

    garage = vehicles.list_vehicles({"status": "official", "sort": "featured", "per_page": "6"})
    _attach_covers("vehicle", garage["data"], vehicles_repo.ids_by_slug)

    featured = media.by_slugs(
        media_slots.HERO_SLUGS + media_slots.VIDEO_SLUGS + media_slots.VIDEO_POSTER_SLUGS
        + media_slots.SCREENSHOT_SLUGS + media_slots.BACKDROP_SLUGS)
    pick = lambda slugs: [featured[s] for s in slugs if s in featured]  # noqa: E731
    featured_all = featured

    all_videos = [m for m in pick(media_slots.VIDEO_SLUGS) if media_urls.player_src(m["embed_url"])]
    natives = local_media.cinematics()
    cinemas = {}
    for slot, spec in media_slots.CINEMATICS.items():
        native = natives.get(slot)
        trailer = next((m for m in all_videos if m["slug"] == spec["trailer"]), None)
        poster = featured_all.get(spec["poster"]) if spec.get("poster") else None
        if spec.get("poster") and not poster:
            poster = featured_all.get("shot-grassrivers-05")
        # A slot shows when its video was built, or (the first slot only) as an official still with a trailer link.
        if native or (poster and trailer):
            cinemas[slot] = {**spec, "slot": slot, "native": native, "poster": poster, "trailer": trailer}

    return {
        "cinemas": cinemas,
        "leads": leads,
        "cast": cast,
        "reel": reel,
        "regions": region_cards,
        "vehicles": garage["data"],
        "missions": missions.list_missions({"per_page": "3", "sort": "newest"})["data"],
        "official_links": characters_repo.official_relationships(4),
        "hero": pick(media_slots.HERO_SLUGS),
        "hero_layers": local_media.hero_layers(),
        "videos": [m for m in pick(media_slots.VIDEO_SLUGS) if media_urls.player_src(m["embed_url"])],
        "video_posters": {m["slug"]: m for m in pick(media_slots.VIDEO_POSTER_SLUGS)},
        "screenshots": pick(media_slots.SCREENSHOT_SLUGS),
        "backdrops": {m["slug"]: m for m in featured.values() if m["slug"] in media_slots.BACKDROP_SLUGS},
        "clips": media.character_clips(),
        "links": media_slots.OFFICIAL_LINKS,
        "release_note": media_slots.RELEASE_NOTE,
    }
