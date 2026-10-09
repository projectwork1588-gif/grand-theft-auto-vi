"""View-models for the public pages: existing services plus related content and media.

Pages reuse the same services as the JSON API, so a page and its API endpoint can never disagree.
"""
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
    return result


def character_detail(slug):
    character, character_id = characters.get_character_with_id(slug)
    character["costars"] = characters_repo.costars_for(character_id)
    character["gallery"] = media.for_entity("character", character_id)
    character["cover"] = character["gallery"][0] if character["gallery"] else None
    return character


# ---------------------------------------------------------------- vehicles
def vehicle_index(args):
    result = vehicles.list_vehicles(args)
    result["categories"] = vehicles_repo.categories_with_counts()
    return result


def vehicle_detail(slug):
    return vehicles.get_vehicle(slug)


# ---------------------------------------------------------------- regions
def region_index(args):
    result = regions.list_regions(args)
    result["data"] = _in_rockstar_order(result["data"])
    _attach_covers("region", result["data"], regions_repo.ids_by_slug)
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
    return result


def mission_detail(slug):
    return missions.get_mission(slug)


# ---------------------------------------------------------------- homepage
def home():
    leads_and_cast = characters_repo.featured_official(8)
    covers = media.covers("character", [c["character_id"] for c in leads_and_cast])
    for c in leads_and_cast:
        c["cover"] = covers.get(c.pop("character_id"))

    region_cards = _in_rockstar_order(regions_repo.list_all())
    _attach_covers("region", region_cards, regions_repo.ids_by_slug)

    featured = media.by_slugs(
        media_slots.HERO_SLUGS + media_slots.VIDEO_SLUGS + media_slots.VIDEO_POSTER_SLUGS
        + media_slots.SCREENSHOT_SLUGS + media_slots.WALLPAPER_SLUGS)
    pick = lambda slugs: [featured[s] for s in slugs if s in featured]  # noqa: E731
    return {
        "characters": leads_and_cast,
        "regions": region_cards,
        "vehicles": vehicles_repo.featured(4),
        "missions": missions.list_missions({"per_page": "3", "sort": "newest"})["data"],
        "official_links": characters_repo.official_relationships(4),
        "stats": system_repo.table_counts(),
        "hero": pick(media_slots.HERO_SLUGS),
        "videos": [m for m in pick(media_slots.VIDEO_SLUGS) if media_urls.player_src(m["embed_url"])],
        "video_posters": pick(media_slots.VIDEO_POSTER_SLUGS),
        "screenshots": pick(media_slots.SCREENSHOT_SLUGS),
        "wallpapers": pick(media_slots.WALLPAPER_SLUGS),
        "links": media_slots.OFFICIAL_LINKS,
        "release_note": media_slots.RELEASE_NOTE,
    }
