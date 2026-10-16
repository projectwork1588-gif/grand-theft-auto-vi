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


def _portrait(slug):
    """The motion sequence the Characters pages show (landing tiles and profiles alike), or None. Built by
    `scripts.make_loops --portraits`, each person in the shape the footage was shot in (the two leads 16:9, the rest
    square). It starts on the person's artwork (the still is that very frame), dissolves into the clip, plays it whole at
    true speed and dissolves back. Missing files fall back to the older per-person loop, used as it always was."""
    shape = media_slots.PORTRAIT_SHAPE.get(slug, "square")
    video = f"clips/{slug}-profile.mp4"
    if local_media.is_servable(video):
        poster = f"clips/{slug}-profile.jpg"
        return {"video": video, "poster": poster if local_media.is_servable(poster) else None, "shape": shape, "poster_at": 0}
    legacy = _local_clip(slug)
    if legacy:
        wide = media_slots.PORTRAIT_SHAPE.get(slug) == "wide"
        return {"video": legacy, "poster": _local_poster(slug), "shape": "wide" if wide else "legacy", "poster_at": 0.32}
    return None


# ---------------------------------------------------------------- characters (Gate 3A)
def _relationship_view(rows, me_slug, names):
    """Relationship rows from either direction as [{slug, name, type, text}] about the *other* person."""
    seen, out = set(), []
    for r in rows:
        other = r["slug"]
        if other == me_slug or other in seen:
            continue
        seen.add(other)
        out.append({"slug": other, "name": r["full_name"], "type": r["relationship_type"], "text": r["description"],
                    "direction": r["direction"]})
    return out


_IMAGE_ASPECT = 16 / 9


def frame_pos(slug, aspect, ax=0.5, ay=0.35):
    """The CSS object-position ("X% Y%") that keeps the face of media `slug` in a box of the given width over height.

    The face sits at (ax, ay) of the box where the crop allows it (ay is how far down the box the face is wanted: lower for
    a hero with a header above it). X is on a two-percent grid and Y on a five-percent grid; characters.css has a rule for
    every value on those grids, because the site's CSP forbids inline styles."""
    fx, fy = media_slots.IMAGE_FACE.get(slug, (0.5, 0.35))
    px = py = 0.5
    if aspect >= _IMAGE_ASPECT:                       # a box wider than the picture: it is cut at the top and bottom
        window = _IMAGE_ASPECT / aspect
        if window < 0.999:
            py = (fy - ay * window) / (1 - window)
    else:                                              # a narrower box: it is cut at the sides
        window = aspect / _IMAGE_ASPECT
        px = (fx - ax * window) / (1 - window)
    px, py = min(1.0, max(0.0, px)), min(1.0, max(0.0, py))
    return f"{int(round(px * 50)) * 2}% {int(round(py * 20)) * 5}%"


def _avatar(slug, media_rows):
    """What the relationship network and the connection cards need to draw a person's portrait circle."""
    spec = media_slots.AVATARS.get(slug)
    if not spec:
        return None
    return {"media": media_rows.get(spec["media"]), "faces": spec["faces"], "hh": spec["hh"], "duo": len(spec["faces"]) > 1}


def _cast_entries(include_media=True):
    """The eight official characters in CHARACTERS_ORDER, each with its pictures, crops, motion sequence and connections."""
    rows = {r["slug"]: r for r in characters_repo.featured_official(50)}
    ids = {slug: rows[slug]["character_id"] for slug in rows}
    wanted = set()
    for pick in media_slots.CHARACTER_STAGE.values():
        wanted.update(pick[k] for k in ("main", "hero", "card", "second"))
    wanted.update(spec["media"] for spec in media_slots.AVATARS.values())
    stage_media = media.by_slugs(wanted)
    cast = []
    for number, slug in enumerate((s for s in media_slots.CHARACTERS_ORDER if s in rows), start=1):
        row = dict(rows[slug])
        pick = media_slots.CHARACTER_STAGE.get(slug)
        row["number"] = number
        row["is_lead"] = slug in media_slots.CAST_LEADS
        if pick:
            for key in ("main", "hero", "card", "second"):
                row[key] = stage_media.get(pick[key])
            row["second_shape"] = pick["shape"]
            hero, card, second = pick["hero"], pick["card"], pick["second"]
            fx = media_slots.IMAGE_FACE.get(hero, (0.5, 0.35))[0]
            row["hero_side"] = "right" if fx < 0.5 else "left"          # the words go on the side the person is not
            row["pos_hero"] = frame_pos(hero, 2.1, ay=0.38)
            row["pos_hero_n"] = frame_pos(hero, 0.75, ay=0.30)
            row["pos_card"] = frame_pos(card, 0.8)                      # the leads' tall spread picture
            row["pos_card_n"] = frame_pos(card, 0.8)
            row["pos_second"] = frame_pos(second, 4 / 3 if pick["shape"] == "wide" else 0.8)
            row["pos_next"] = frame_pos(hero, 2.2, ay=0.4)
            row["pos_next_n"] = frame_pos(hero, 2.0, ay=0.4)
            row["pos_result"] = frame_pos(card, 1.6)
        else:
            for key in ("main", "hero", "card", "second"):
                row[key] = None
        row["avatar"] = _avatar(slug, stage_media)
        row["portrait"] = _portrait(slug)
        row["connections"] = _relationship_view(characters_repo.relationships_for(ids[slug]), slug, rows)
        row["regions"] = characters_repo.regions_for(ids[slug])
        cast.append(row)
    # a person with no spotlight picture of their own still gets their best cover
    missing = [c for c in cast if not c["main"]]
    if missing:
        covers = media.covers("character", [ids[c["slug"]] for c in missing])
        for c in missing:
            for key in ("main", "hero", "card", "second"):
                c[key] = c[key] or covers.get(ids[c["slug"]])
    return cast


def _cast_groups(cast):
    """The supporting cast in groups the data supports: people tied to a lead, then connected clusters among the rest
    (titled where the source names them), then anyone with no stated connection. Within a group the people keep the
    canonical order."""
    supporting = [c for c in cast if not c["is_lead"]]
    by_slug = {c["slug"]: c for c in supporting}
    lead_slugs = set(media_slots.CAST_LEADS)
    groups, used = [], set()
    # people with a stated tie to one of the leads
    tied = [c for c in supporting if any(k["slug"] in lead_slugs for k in c["connections"])]
    if tied:
        names = {k["name"] for c in tied for k in c["connections"] if k["slug"] in lead_slugs}
        title = f"Around {next(iter(names))}" if len(names) == 1 else "Around the leads"
        groups.append({"title": title, "kicker": "Tied to a lead", "people": tied})
        used.update(c["slug"] for c in tied)
    # clusters among the others
    remaining = [c for c in supporting if c["slug"] not in used]
    adjacency = {c["slug"]: {k["slug"] for k in c["connections"] if k["slug"] in by_slug} for c in remaining}
    seen = set()
    for c in remaining:
        if c["slug"] in seen or not adjacency[c["slug"]]:
            continue
        stack, component = [c["slug"]], set()
        while stack:
            cur = stack.pop()
            if cur in component:
                continue
            component.add(cur)
            stack.extend(adjacency.get(cur, ()))
        seen |= component
        members = [x for x in remaining if x["slug"] in component]
        title = media_slots.CAST_GROUP_TITLES.get(frozenset(component), "Connected")
        groups.append({"title": title, "kicker": "Connected to each other", "people": members})
        used.update(component)
    alone = [c for c in supporting if c["slug"] not in used]
    for c in alone:
        groups.append({"title": None, "kicker": "No stated connections yet", "people": [c], "single": True})
    # where each card's picture is cut so the person stays in it, from the shape of the card it fills
    for g in groups:
        n = len(g["people"])
        for i, c in enumerate(g["people"]):
            aspect = 16 / 9 if n == 1 else (1.6 if n == 2 else (0.84 if i == 0 else 1.25))
            c["pos_card"] = frame_pos(media_slots.CHARACTER_STAGE[c["slug"]]["card"], aspect)
            c["pos_card_n"] = frame_pos(media_slots.CHARACTER_STAGE[c["slug"]]["card"], 1.7)
    return groups


def _network(cast):
    """Nodes and edges for the relationship network, straight from the official character_relationships rows."""
    by_slug = {c["slug"]: c for c in cast}
    edges = []
    for r in characters_repo.official_relationships(50):
        if r["from_slug"] in by_slug and r["to_slug"] in by_slug:
            edges.append({"from": r["from_slug"], "to": r["to_slug"], "type": r["relationship_type"], "text": r["description"],
                          "from_name": r["from_name"], "to_name": r["to_name"]})
    linked = {e["from"] for e in edges} | {e["to"] for e in edges}
    nodes = []
    fallback = list(media_slots.NETWORK_LAYOUT.values())
    for i, c in enumerate(cast):
        x, y = media_slots.NETWORK_LAYOUT.get(c["slug"], fallback[i % len(fallback)])
        duo = bool(c["avatar"] and c["avatar"]["duo"])
        nodes.append({"slug": c["slug"], "name": c["full_name"], "role": c["role_title"], "x": x, "y": y, "lead": c["is_lead"],
                      "linked": c["slug"] in linked, "avatar": c["avatar"], "duo": duo,
                      "d": 88 if c["is_lead"] else (80 if duo else 68),
                      "side": "right" if c["slug"] in media_slots.NETWORK_NAME_RIGHT else "below"})
    for e in edges:
        a = next(n for n in nodes if n["slug"] == e["from"])
        b = next(n for n in nodes if n["slug"] == e["to"])
        e.update(x1=a["x"], y1=a["y"], x2=b["x"], y2=b["y"], mx=(a["x"] + b["x"]) / 2, my=(a["y"] + b["y"]) / 2,
                 from_avatar=a["avatar"], to_avatar=b["avatar"])
    return {"nodes": nodes, "edges": edges, "unlinked": [n["name"] for n in nodes if not n["linked"]]}


def character_index(args):
    """The Characters landing page: editorial by default, a results list when the Explore panel is used.

    Only official characters are ever listed here; a status in the query string is ignored. Explore lists in the cast
    order unless the visitor chooses another sort."""
    clean = {k: v for k, v in args.items() if k in ("q", "region", "sort", "page", "per_page")}
    clean.setdefault("sort", "cast")
    result = characters.list_characters(clean)
    result["regions"] = regions_repo.list_all()
    exploring = bool(result["filters"].get("q") or result["filters"].get("region") or args.get("sort") or result["pagination"]["page"] > 1)
    result["mode"] = "results" if exploring else "editorial"
    cast = _cast_entries()
    result["cast"] = cast
    result["leads"] = [c for c in cast if c["is_lead"]]
    result["groups"] = _cast_groups(cast)
    result["network"] = _network(cast)
    result["opening"] = media.by_slugs([media_slots.CHARACTERS_OPENING]).get(media_slots.CHARACTERS_OPENING)
    result["together"] = media.by_slugs([media_slots.CAST_TOGETHER]).get(media_slots.CAST_TOGETHER)
    if result["mode"] == "results":
        by_slug = {c["slug"]: c for c in cast}
        for row in result["data"]:
            entry = by_slug.get(row["slug"])
            row["cover"] = entry["card"] if entry else None
            row["pos"] = entry["pos_result"] if entry else "50% 40%"
            row["number"] = entry["number"] if entry else None
    return result


def character_detail(slug):
    character, character_id = characters.get_character_with_id(slug)
    cast = _cast_entries()
    entry = next((c for c in cast if c["slug"] == slug), None)
    for key in ("number", "main", "hero", "card", "second", "second_shape", "pos_hero", "pos_hero_n", "pos_second", "hero_side"):
        character[key] = entry.get(key) if entry else None
    character["number"] = entry["number"] if entry else None
    character["is_lead"] = slug in media_slots.CAST_LEADS
    character["shape"] = "wide" if character["is_lead"] else "square"       # the motion footage's own shape
    character["hero_side"] = character["hero_side"] or "left"
    character["pos_hero"] = character["pos_hero"] or "50% 40%"
    character["pos_hero_n"] = character["pos_hero_n"] or "50% 40%"
    character["pos_second"] = character["pos_second"] or "50% 50%"
    character["second_shape"] = character["second_shape"] or "tall"
    character["cover"] = character["hero"] or character["main"]
    gallery = media.for_entity("character", character_id, limit=14)
    used = {m["slug"] for m in (character["main"], character["hero"], character["second"]) if m}
    character["gallery"] = [m for m in gallery if m["slug"] not in used]
    character["costars"] = characters_repo.costars_for(character_id)
    clips = {c["character_slug"]: c for c in media.character_clips()}
    character["clip"] = clips.get(slug)
    character["portrait"] = _portrait(slug)
    # connections with a face, and the people either side of them in the cast (the order is circular)
    by_slug = {c["slug"]: c for c in cast}
    character["connections"] = []
    for r in character["relationships"]:
        other = by_slug.get(r["slug"])
        character["connections"].append({"slug": r["slug"], "name": r["full_name"], "type": r["relationship_type"], "text": r["description"],
                                         "avatar": other["avatar"] if other else None, "role": other["role_title"] if other else ""})
    order = [c["slug"] for c in cast]
    if slug in order:
        i = order.index(slug)
        character["prev"] = by_slug[order[(i - 1) % len(order)]]
        character["next"] = by_slug[order[(i + 1) % len(order)]]
    else:
        character["prev"] = character["next"] = None
    character["cast_nav"] = cast
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
        "official_links": characters_repo.official_relationships(4, exclude=(("dre-quan-priest", "real-dimez"),)),  # the approved four
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
