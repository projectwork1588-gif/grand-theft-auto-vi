"""View-models for the public pages: existing services plus related content and media.

Pages reuse the same services as the JSON API, so a page and its API endpoint can never disagree.
The public Garage is the official vehicles only: those Rockstar names and shows in its own screenshots.
Concept vehicles stay in the database for the story archive but get no public page.
"""
from werkzeug.exceptions import NotFound

from .. import media_slots, media_urls
from ..repositories import characters as characters_repo
from ..repositories import media, missions as missions_repo, regions as regions_repo
from ..repositories import system as system_repo
from ..repositories import vehicles as vehicles_repo
from . import characters, locations, missions, regions, validation as v, vehicles


def _in_rockstar_order(rows):
    """Regions in the order Rockstar lists them. Unknown slugs go last, alphabetically."""
    order = {slug: i for i, slug in enumerate(media_slots.REGION_ORDER)}
    return sorted(rows, key=lambda r: (order.get(r["slug"], len(order)), r["name"]))


def _page_cover(page):
    """Official backdrop image for the top of a catalogue page, or None (the page then uses its fallback)."""
    slug = media_slots.PAGE_HERO_SLUGS.get(page)
    return media.by_slugs([slug]).get(slug) if slug else None


def _attach_covers(kind, rows, ids_by_slug):
    ids = ids_by_slug([row["slug"] for row in rows])
    covers = media.covers(kind, ids.values())
    for row in rows:
        row["cover"] = covers.get(ids.get(row["slug"]))
    return rows


# ---------------------------------------------------------------- characters
def character_index(args):
    result = characters.list_characters(args)
    _attach_covers("character", result["data"], characters_repo.ids_by_slug)
    result["regions"] = regions_repo.list_all()
    result["hero_cover"] = _page_cover("characters")
    return result


def character_detail(slug):
    character, character_id = characters.get_character_with_id(slug)
    character["costars"] = characters_repo.costars_for(character_id)
    character["gallery"] = media.for_entity("character", character_id)
    character["cover"] = character["gallery"][0] if character["gallery"] else None
    clips = {c["character_slug"]: c for c in media.character_clips()}
    character["clip"] = clips.get(slug)
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
    _attach_covers("region", result["data"], regions_repo.ids_by_slug)
    result["hero_cover"] = _page_cover("regions")
    return result


def region_detail(slug):
    region, region_id = regions.get_region_with_id(slug)
    region["missions"] = missions_repo.in_region(region_id)
    region["gallery"] = media.for_entity("region", region_id)
    region["cover"] = region["gallery"][0] if region["gallery"] else None
    others = _in_rockstar_order(regions_repo.list_all())
    region["other_regions"] = [r for r in others if r["slug"] != slug]
    _attach_covers("region", region["other_regions"], regions_repo.ids_by_slug)
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
    covers = media.covers("region", region_ids.values())
    location["region_cover"] = covers.get(region_ids.get(location["region_slug"]))
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
        ids = regions_repo.ids_by_slug([setting["region_slug"]])
        mission["backdrop"] = media.covers("region", ids.values()).get(ids.get(setting["region_slug"]))
        mission["backdrop_region"] = setting["region_name"]
    return mission


# ---------------------------------------------------------------- homepage
def home():
    leads_and_cast = characters_repo.featured_official(8)
    covers = media.covers("character", [c["character_id"] for c in leads_and_cast])
    for c in leads_and_cast:
        c["cover"] = covers.get(c.pop("character_id"))

    region_cards = _in_rockstar_order(regions_repo.list_all())
    _attach_covers("region", region_cards, regions_repo.ids_by_slug)

    garage = vehicles.list_vehicles({"status": "official", "sort": "featured", "per_page": "6"})
    _attach_covers("vehicle", garage["data"], vehicles_repo.ids_by_slug)

    featured = media.by_slugs(
        media_slots.HERO_SLUGS + media_slots.VIDEO_SLUGS + media_slots.VIDEO_POSTER_SLUGS
        + media_slots.SCREENSHOT_SLUGS + media_slots.BACKDROP_SLUGS)
    pick = lambda slugs: [featured[s] for s in slugs if s in featured]  # noqa: E731

    counts = system_repo.table_counts()
    return {
        "characters": leads_and_cast,
        "regions": region_cards,
        "vehicles": garage["data"],
        "missions": missions.list_missions({"per_page": "3", "sort": "newest"})["data"],
        "official_links": characters_repo.official_relationships(4),
        "stats": [
            {"label": "Characters", "count": counts["characters"]},
            {"label": "Regions", "count": counts["regions"]},
            {"label": "Vehicles", "count": garage["pagination"]["total"]},
            {"label": "Official media", "count": counts["media_assets"]},
        ],
        "hero": pick(media_slots.HERO_SLUGS),
        "videos": [m for m in pick(media_slots.VIDEO_SLUGS) if media_urls.player_src(m["embed_url"])],
        "video_posters": {m["slug"]: m for m in pick(media_slots.VIDEO_POSTER_SLUGS)},
        "screenshots": pick(media_slots.SCREENSHOT_SLUGS),
        "backdrops": {m["slug"]: m for m in pick(media_slots.BACKDROP_SLUGS)},
        "clips": media.character_clips(),
        "links": media_slots.OFFICIAL_LINKS,
        "release_note": media_slots.RELEASE_NOTE,
    }
