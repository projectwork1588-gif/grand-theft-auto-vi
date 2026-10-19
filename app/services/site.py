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


def _landing_portrait(slug):
    """The Characters landing tile: the profile's sequence, except where the person's artwork is already the large picture
    beside the tile (media_slots.LANDING_REST): then the tile starts and rests on a frame of their own clip
    (`<slug>-landing.mp4`, built by `scripts.make_loops --stills`). Until that exists it is the profile sequence as before."""
    if slug in media_slots.LANDING_REST:
        video, poster = f"clips/{slug}-landing.mp4", f"clips/{slug}-landing.jpg"
        if local_media.is_servable(video):
            shape = media_slots.PORTRAIT_SHAPE.get(slug, "square")
            return {"video": video, "poster": poster if local_media.is_servable(poster) else None, "shape": shape, "poster_at": 0}
    return _portrait(slug)


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


def frame_pos(slug, aspect, ax=0.5, ay=0.35, face=None):
    """The CSS object-position ("X% Y%") that keeps the face of media `slug` in a box of the given width over height.

    The face sits at (ax, ay) of the box where the crop allows it (ay is how far down the box the face is wanted: lower for
    a hero with a header above it). X is on a two-percent grid and Y on a five-percent grid; characters.css has a rule for
    every value on those grids, because the site's CSP forbids inline styles."""
    fx, fy = face or media_slots.IMAGE_FACE.get(slug, (0.5, 0.35))
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
    return {"media": media_rows.get(spec["media"]), "heads": spec["heads"], "head": media_slots.AVATAR_HEAD, "bg": spec.get("bg"), "duo": len(spec["heads"]) > 1}


def _local_still(name):
    """A frame cut from Rockstar's own clip by `scripts.make_loops --stills`, as a picture the `shot` macro can draw, or None
    until it has been built."""
    path = f"clips/{name}.jpg"
    if not local_media.is_servable(path):
        return None
    small = f"clips/{name}-800.jpg"
    return {"slug": name, "embed_url": None, "local": path, "local_small": small if local_media.is_servable(small) else None}


def _apply_local_stills(row, slug):
    """Swap in the built still frames where media_slots.LOCAL_STILL_PICKS names them; otherwise the official pictures chosen
    in CHARACTER_STAGE stay."""
    for role, (name, pos, shape) in media_slots.LOCAL_STILL_PICKS.get(slug, {}).items():
        still = _local_still(name)
        if not still:
            continue
        row[role] = still
        if role == "card":
            row["pos_card"] = row["pos_card_n"] = row["pos_result"] = pos
        else:
            row["pos_second"] = pos
            row["second_shape"] = shape


def _cast_entries(include_media=True):
    """The eight official characters in CHARACTERS_ORDER, each with its pictures, crops, motion sequence and connections."""
    rows = {r["slug"]: r for r in characters_repo.featured_official(50)}
    ids = {slug: rows[slug]["character_id"] for slug in rows}
    wanted = set()
    for pick in media_slots.CHARACTER_STAGE.values():
        wanted.update(pick[k] for k in ("main", "hero", "card", "second") if pick[k])
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
            row["hero_duo"] = bool(pick.get("duo"))          # two people in the hero: on a narrow screen the picture is shown whole
            hero, card, second = pick["hero"], pick["card"], pick["second"]
            fx = media_slots.IMAGE_FACE.get(hero, (0.5, 0.35))[0]
            row["hero_side"] = pick.get("side") or ("right" if fx < 0.5 else "left")   # the words go on the side the person is not
            row["pos_hero"] = frame_pos(hero, 2.1, ay=0.38)
            row["pos_hero_n"] = frame_pos(hero, 0.75, ay=0.30)
            row["pos_card"] = frame_pos(card, 0.8)                      # the leads' tall spread picture
            row["pos_card_n"] = frame_pos(card, 0.8)
            row["pos_second"] = frame_pos(second, 4 / 3 if pick["shape"] == "wide" else 0.8) if second else None
            row["pos_next"] = frame_pos(hero, 2.2, ay=0.4)
            row["pos_next_n"] = frame_pos(hero, 2.0, ay=0.4)
            row["pos_result"] = frame_pos(card, 1.6)
        else:
            for key in ("main", "hero", "card", "second"):
                row[key] = None
        _apply_local_stills(row, slug)
        row["avatar"] = _avatar(slug, stage_media)
        row["portrait"] = _landing_portrait(slug)
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
    for key in ("number", "main", "hero", "card", "second", "second_shape", "pos_hero", "pos_hero_n", "pos_second", "hero_side", "hero_duo"):
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
    character["gallery"] = [] if slug in media_slots.NO_GALLERY else [m for m in gallery if m["slug"] not in used]
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
# The Garage (Gate 3B, second pass). The pictures and how each vehicle is presented are chosen by hand in media_slots.GARAGE_PICKS /
# GARAGE_FRAMES; everything else is the database: the vehicles, their categories, descriptions and sources, the missions and places
# they are tied to.
GARAGE_SORTS = (("featured", "Featured"), ("name_asc", "Name A to Z"), ("name_desc", "Name Z to A"), ("category", "Category"))
_ROW_CYCLE = ((8, 4), (4, 4, 4), (5, 7), (7, 5))
_ROW_TONE = {(8, 4): "tall", (4, 4, 4): "mid", (5, 7): "low", (7, 5): "low", (6, 6): "mid", (12,): "wide"}
_ROW_HEIGHT = {"tall": 540, "mid": 390, "low": 440, "wide": 420}
_GRID_WIDTH = 1328
_STAGE_SHAPE = {"stage": (1.6, 1.5)}
_HERO_SHAPE = {"hero": (1.7, 1.15)}
_THUMB_SHAPE = {"thumb": (1.6, 1.6)}
_CONTEXT_ASPECT = 1.45
_GALLERY_SHAPES = {"large": (1.5, 1.5), "wide": (2.3, 1.5), "small": (1.25, 1.5), "viewer": (16 / 9, 4 / 3), "thumb": (1.6, 1.6)}


def garage_rows(count):
    """The showroom's arrangement as rows of column spans out of 12: a large and a narrow, three equal, a narrow and a large, a large and a
    narrow, then round again. A last row with too few left becomes two halves, three thirds or one full-width panel, so no row has a hole."""
    if count == 2:
        return [[7, 5]]
    if count == 3:
        return [[4, 4, 4]]
    rows, left, i = [], count, 0
    while left > 0:
        row = _ROW_CYCLE[i % len(_ROW_CYCLE)]
        i += 1
        if left >= len(row):
            rows.append(list(row))
            left -= len(row)
        else:
            rows.append([12] if left == 1 else ([6, 6] if left == 2 else [4, 4, 4]))
            left = 0
    return rows


def _cell_shape(span, tone):
    """The box a showroom tile is drawn in (wide screens, then phones), so its picture is cut around its subject."""
    return {"card": ((span / 12 * _GRID_WIDTH - 20) / _ROW_HEIGHT[tone], 1.5)}


def _garage_picture(m, shapes, zoom=None, keep_height=False, face=None):
    """A frame ready for the `gshot` macro: the media row, what it shows, and one cut per named shape (where to place it on wide
    screens and on phones). `zoom` = (scale, x, y) draws it closer on (x, y)."""
    if not m:
        return None
    spec = media_slots.GARAGE_FRAMES.get(m["slug"], {})
    phone = face or spec.get("phone", spec.get("face", (0.5, 0.5)))      # a face given here (a chapter's own framing) is used for phones too
    face = face or spec.get("face", (0.5, 0.5))
    if zoom:
        face = phone = (zoom[1], zoom[2])
    # keep_height: a box that is wider than the picture cuts its top and bottom in step with where the subject sits (so a low subject loses more sky than road)
    cuts = {name: (frame_pos(m["slug"], a[0], ay=face[1] if keep_height else 0.5, face=face), frame_pos(m["slug"], a[1], ay=0.5, face=phone)) for name, a in shapes.items()}
    first = next(iter(cuts.values()))
    return {"m": m, "slug": m["slug"], "alt": spec.get("alt") or m["title"], "pos": first[0], "posn": first[1], "cuts": cuts,
            "zoom": f"{zoom[0]:.2f}".rstrip("0").rstrip(".") if zoom else None}


def split_name(name, maker):
    """A vehicle's name as (the part up to and including its maker, the model): "'95 Grotti Cheetah" -> ("'95 Grotti", "Cheetah"). The model is
    set large on the Garage pages. A name that does not contain its maker is all model."""
    if maker:
        at = name.find(maker)
        if at >= 0 and name[at + len(maker):].strip():
            return name[:at + len(maker)].strip(), name[at + len(maker):].strip()
    return "", name


def _context_picture(m, focus, zoom, aspect):
    """A picture drawn close around one subject: `focus` (x, y) is where the subject sits in the picture, `zoom` how far in. The box is cut
    around the subject as usual (frame_pos), then drawn `zoom` times larger about an origin (data-zx, data-zy on a 2 percent grid) chosen so
    the subject ends up in the middle of the box."""
    spec = media_slots.GARAGE_FRAMES.get(m["slug"], {})
    fx, fy = focus
    pos = frame_pos(m["slug"], aspect, ay=0.5, face=focus)
    px, py = (int(v.strip("%")) / 100 for v in pos.split())
    if aspect < _IMAGE_ASPECT:
        window = aspect / _IMAGE_ASPECT
        bx, by = (fx - (1 - window) * px) / window, fy
    else:
        window = _IMAGE_ASPECT / aspect
        bx, by = fx, (fy - (1 - window) * py) / window
    # the origin that puts the subject in the middle of the box after the zoom: (1 - z) * o + z * b = 0.5 (kept inside the picture)
    origin = lambda b: min(1.0, max(0.0, (0.5 - zoom * b) / (1 - zoom)))
    grid = lambda v: min(100, max(0, int(round(v * 50)) * 2))
    return {"m": m, "slug": m["slug"], "alt": spec.get("alt") or m["title"], "pos": pos, "posn": pos, "cuts": {}, "zoom": f"{zoom:.2f}".rstrip("0").rstrip("."),
            "zx": grid(origin(bx)), "zy": grid(origin(by))}


def _all_official():
    return vehicles.list_vehicles({"status": "official", "sort": "featured", "per_page": "50"})["data"]


def _garage_entries(rows, shapes_for=None):
    """Each vehicle with the pictures the Garage pages draw it with. `shapes_for(index)` gives the box of its showroom tile."""
    ids = vehicles_repo.ids_by_slug([r["slug"] for r in rows])
    counts = media.counts("vehicle", ids.values())
    wanted = set()
    for r in rows:
        pick = media_slots.GARAGE_PICKS.get(r["slug"], {})
        wanted.update(pick[k] for k in ("stage", "card") if pick.get(k))
    frames = media.by_slugs(wanted)
    covers = media.covers("vehicle", ids.values())
    order = [r["slug"] for r in _all_official()]
    entries = []
    for index, r in enumerate(rows):
        pick = media_slots.GARAGE_PICKS.get(r["slug"], {})
        fallback = covers.get(ids.get(r["slug"]))
        card = frames.get(pick.get("card")) or fallback
        stage = frames.get(pick.get("stage")) or fallback
        shapes = shapes_for(index) if shapes_for else {"card": (1.5, 1.5)}
        make_line, model_line = split_name(r["name"], r.get("manufacturer"))
        entries.append({**r, "make_line": make_line, "model_line": model_line, "number": (order.index(r["slug"]) + 1) if r["slug"] in order else index + 1, "images": counts.get(ids.get(r["slug"]), 0),
                        "card": _garage_picture(card, shapes, pick.get("card_zoom")), "stage": _garage_picture(stage, _STAGE_SHAPE),
                        "thumb": _garage_picture(stage, _THUMB_SHAPE), "side": pick.get("side", "left"), "vpos": pick.get("vpos", "bottom"),
                        "theme": pick.get("theme", "")})
    return entries


def vehicle_index(args):
    forced = {"sort": "featured", **args.to_dict(), "status": "official"}
    result = vehicles.list_vehicles(forced)
    result["filters"].pop("status", None)
    rows = garage_rows(len(result["data"]))
    cells = [(span, _ROW_TONE[tuple(row)]) for row in rows for span in row]
    entries = _garage_entries(result["data"], lambda i: _cell_shape(*cells[i]))
    result["data"] = entries
    result["showroom"], k = [], 0
    for row in rows:
        result["showroom"].append({"tone": _ROW_TONE[tuple(row)], "cells": [{"span": span, "v": entries[k + j]} for j, span in enumerate(row)]})
        k += len(row)
    # the opening always shows the whole garage, whatever the showroom below is filtered to
    everyone = _all_official()
    result["stage"] = _garage_entries(everyone)
    result["total_all"] = len(everyone)
    result["categories"] = [c for c in vehicles_repo.categories_with_counts("official") if c["vehicle_count"]]
    result["sorts"] = GARAGE_SORTS
    f = result["filters"]
    result["active"] = bool(f.get("q") or f.get("category") or f.get("sort") not in (None, "featured"))
    result["category_name"] = next((c["name"] for c in result["categories"] if c["slug"] == f.get("category")), None)
    # the customs and classics band belongs to the whole garage, not to a search or a category
    plain = not (f.get("q") or f.get("category")) and result["pagination"]["page"] == 1
    result["moments"] = _garage_moments() if plain and len(rows) >= 2 else []
    result["moments_after"] = min(1, len(rows) - 1)
    return result


# ---------------------------------------------------------------- the concept: a full-screen opening and a collection told in four chapters
_ROLE_SHAPES = {   # (wide screens, phones): the box each picture is cut for, width over height (a stage's box changes with the window, so these are the usual shape)
    "perf": {"main": (1.6, 1.6), "second": (1.5, 1.5)},
    "street_a": {"main": (1.7, 1.6), "second": (1.5, 1.5)},
    "street_b": {"main": (1.7, 1.6), "second": (1.5, 1.5)},
    "duo_a": {"main": (1.3, 1.25), "second": (1.5, 1.6)},
    "duo_b": {"main": (1.15, 1.25), "second": (1.5, 1.6)},
    "sea_a": {"main": (1.78, 1.2), "second": (1.5, 1.6)},
    "finale": {"main": (1.78, 1.1), "second": (1.5, 1.6)},
    "second": {"main": (1.78, 1.6), "second": (1.6, 1.6)},      # the plain card of a filtered list or a machine no chapter names
}
_SCENE_SHAPE = {"stage": (1.6, 1.4)}
_MOMENT_SHAPES = {"strip": (1.78, 1.6)}


def _concept_entry(entry, frames, role=None):
    """One machine as the collection draws it: its main picture cut for its role, and a close-up of another part of it where Rockstar has one."""
    pick = media_slots.GARAGE_SPREADS.get(entry["slug"], {})
    role = role or pick.get("role", "second")
    main = frames.get(pick.get("main"))
    second = frames.get(pick.get("second"))
    shapes = _ROLE_SHAPES[role]
    return {**entry, "role": role, "cat": entry.get("category_slug") or "", "summary": media_slots.GARAGE_COPY.get(entry["slug"], entry.get("summary", "")),
            "main": _garage_picture(main, {"main": shapes["main"]}, pick.get("zoom"), face=pick.get("face")) if main else entry["card"],
            "second": _garage_picture(second, {"second": shapes["second"]}) if second else None,
            "second_label": pick.get("second_label", "")}


def _chapters(rows, frames):
    """The default collection told in the four chapters of media_slots.GARAGE_CHAPTERS. A chapter keeps only the machines the database has (so a
    garage with five vehicles shows its chapters shorter, never with a gap), and a machine no chapter names comes after them, in the database's order."""
    by_slug = {r["slug"]: r for r in rows}
    chapters, placed = [], set()
    for chapter in media_slots.GARAGE_CHAPTERS:
        machines = [_concept_entry(by_slug[slug], frames) for slug in chapter["slugs"] if slug in by_slug]
        placed.update(m["slug"] for m in machines)
        if machines:
            chapters.append({**chapter, "machines": machines})
    leftovers = [_concept_entry(r, frames, "second") for r in rows if r["slug"] not in placed]
    if leftovers:
        chapters.append({"key": "more", "title": "More machines", "accent": "#ff9a9a", "slugs": (), "line": "", "machines": leftovers})
    return chapters


def vehicle_concept(args):
    """The Garage as the concept page shows it. The opening always holds the whole garage. The collection is the same MySQL-backed query as the live
    page (search, category, sort and paging); with no filter it is told in four chapters (visual themes, not categories), and with any filter, search,
    other sort or page it is an honest ordered list, so counts, ordering and empty states always mean what they say."""
    result = vehicle_index(args)
    rows = result["data"]
    # the opening: each scene is cut for its own composition (a long low machine is drawn whole beside its words)
    for r in result["stage"]:
        scene = media_slots.GARAGE_SCENES.get(r["slug"], {})
        r["plate"] = scene.get("plate", "br")
        r["summary"] = media_slots.GARAGE_COPY.get(r["slug"], r.get("summary", ""))
        r["subject"] = ";".join(",".join(f"{v:.2f}" for v in box) for box in scene["subject"]) if scene.get("subject") else ""
        if r["stage"]:
            r["stage"] = _garage_picture(r["stage"]["m"], _SCENE_SHAPE, keep_height=True)
            if "px" in scene:                           # a scene may hold its picture to one side of its frame (a percent, on the stylesheet's 2 percent grid)
                wide, phone = r["stage"]["cuts"]["stage"]
                r["stage"]["cuts"]["stage"] = (f"{scene['px']}% {wide.split()[1]}", phone)
                r["stage"]["pos"] = r["stage"]["cuts"]["stage"][0]
    wanted = set()
    for r in rows:
        pick = media_slots.GARAGE_SPREADS.get(r["slug"], {})
        wanted.update(pick[k] for k in ("main", "second") if pick.get(k))
    wanted.update(slug for slug, _ in media_slots.GARAGE_MOMENTS)
    frames = media.by_slugs(wanted)
    curated = not result["active"] and result["pagination"]["page"] == 1 and len(rows) == result["total_all"]
    result["curated"] = curated
    result["chapters"], result["list"] = [], []
    if curated:
        result["chapters"] = _chapters(rows, frames)
        moments = []
        for slug, caption in media_slots.GARAGE_MOMENTS:
            picture = _garage_picture(frames.get(slug), _MOMENT_SHAPES)
            if picture:
                moments.append({**picture, "caption": caption})
        result["moments"] = moments
    else:
        result["list"] = [_concept_entry(r, frames, "second") for r in rows]
        result["moments"] = []
    return result


def _garage_moments():
    frames = media.by_slugs({slug for slug, _ in media_slots.GARAGE_MOMENTS})
    out = []
    for slug, caption in media_slots.GARAGE_MOMENTS:
        picture = _garage_picture(frames.get(slug), {"wide": (1.7, 1.4), "tall": (0.9, 1.5), "small": (1.5, 1.4)})
        if picture:
            out.append({**picture, "caption": caption})
    return out


# ---------------------------------------------------------------- the vehicle pages (Stage B)
_DETAIL_SHAPES = {"stage": (1.6, 1.6), "half": (1.3, 1.3), "pano": (2.4, 1.3), "viewer": (16 / 9, 4 / 3), "thumb": (1.6, 1.6)}
_CLOSE_ASPECT = 1.2          # the box of each crop in "in close", width over height
_CONTEXT_STAGE_ASPECT = 2.2  # the box of the smaller cut of a Rockstar scene


def _scene_picture(m, scene):
    """A vehicle's opening picture, cut for its composition exactly as the Garage's opening cuts it (so the page opens on the same picture the visitor chose)."""
    picture = _garage_picture(m, _SCENE_SHAPE, keep_height=True)
    if picture and "px" in scene:                                    # a scene may hold its picture to one side of its frame
        wide, phone = picture["cuts"]["stage"]
        picture["cuts"]["stage"] = (f"{scene['px']}% {wide.split()[1]}", phone)
        picture["pos"] = picture["cuts"]["stage"][0]
    return picture


def _captioned(m, caption=None):
    """A gallery picture with its short caption and the full-size picture's address (the page links to it)."""
    picture = _garage_picture(m, _DETAIL_SHAPES)
    picture["caption"] = caption or media_slots.GARAGE_CAPTIONS.get(m["slug"]) or picture["alt"]
    return picture


def vehicle_detail(slug):
    vehicle, vehicle_id = vehicles.get_vehicle_with_id(slug)
    if vehicle["content_status"] != "official":
        raise NotFound("That vehicle is not part of the public garage.")
    pick = media_slots.GARAGE_PICKS.get(slug, {})
    detail = media_slots.GARAGE_DETAIL.get(slug, {})
    scene = media_slots.GARAGE_SCENES.get(slug, {})
    frames = media.for_entity("vehicle", vehicle_id, limit=24)
    by_slug = {m["slug"]: m for m in frames}
    hero = by_slug.get(pick.get("stage")) or (frames[0] if frames else None)
    vehicle["hero"] = _scene_picture(hero, scene)
    vehicle["plate"] = scene.get("plate", "br")
    vehicle["subject"] = ";".join(",".join(f"{v:.2f}" for v in box) for box in scene["subject"]) if scene.get("subject") else ""
    vehicle["line"] = media_slots.GARAGE_COPY.get(slug, vehicle["summary"])
    vehicle["side"], vehicle["vpos"] = pick.get("side", "left"), pick.get("vpos", "bottom")
    vehicle["theme"] = pick.get("theme", "")
    vehicle["make_line"], vehicle["model_line"] = split_name(vehicle["name"], vehicle.get("manufacturer"))
    vehicle["images"] = len(frames)
    # the showcase never repeats the picture that opens the page
    wanted = [by_slug[g] for g in pick.get("gallery", []) if g in by_slug and by_slug[g] is not hero]
    ctx = pick.get("context")
    rest = wanted or [m for m in frames if not hero or (m["slug"] != hero["slug"] and m["slug"] != (ctx or {}).get("slug"))]
    vehicle["gallery"] = [_captioned(m) for m in rest]
    # how the rest of the page is told: chosen for the pictures that exist, never forced
    sequence = detail.get("sequence")
    n = len(vehicle["gallery"])
    if sequence in ("stage_pair", "panorama_pair") and n < 3:
        sequence = "viewer" if n >= 2 else None
    if sequence == "viewer" and n < 2:
        sequence = None
    if sequence is None and n >= 3:
        sequence = "stage_pair"
    vehicle["side"] = detail.get("side", "right")
    vehicle["context"] = None
    if sequence == "context":
        row = media.by_slugs([ctx["slug"]]).get(ctx["slug"]) if ctx else None
        if row:
            vehicle["context"] = {**_context_picture(row, ctx["focus"], ctx["zoom"], _CONTEXT_STAGE_ASPECT), "title": ctx["title"], "text": ctx["text"], "flip": ctx["flip"]}
    # a machine with one picture is drawn closer: crops of that same picture, each named for what it shows
    vehicle["close"] = []
    if hero and sequence in ("close", "context"):
        for label, x, y, zoom in media_slots.GARAGE_CLOSE.get(slug, ()):
            crop = _context_picture(hero, (x, y), zoom, _CLOSE_ASPECT)
            crop["label"] = label
            vehicle["close"].append(crop)
    if sequence == "context" and not vehicle["context"] and not vehicle["close"]:
        sequence = None
    if sequence == "close" and not vehicle["close"]:
        sequence = None
    vehicle["sequence"] = sequence
    vehicle["story"] = sequence or "none"
    entries = _garage_entries(_all_official(), lambda i: {"card": (1.9, 1.5)})
    me = next((i for i, e in enumerate(entries) if e["slug"] == slug), 0)
    vehicle["rail"] = entries
    vehicle["number"] = entries[me]["number"] if entries else 1
    vehicle["total"] = len(entries)
    vehicle["previous"] = entries[(me - 1) % len(entries)] if len(entries) > 1 else None
    vehicle["next"] = entries[(me + 1) % len(entries)] if len(entries) > 1 else None
    for e in (vehicle["previous"], vehicle["next"]):
        if e:
            e["line"] = media_slots.GARAGE_COPY.get(e["slug"], e.get("summary", ""))
    vehicle["cover"] = frames[0] if frames else None
    return vehicle


# ---------------------------------------------------------------- regions
def _official(rows):
    """Only what is Rockstar's. The database also holds places and stories invented by Team Valkyrie (content_status 'demo'); the Regions pages never present
    them as part of Leonida (they stay in the database, the API and the Locations and Stories pages, where they are labelled as originals)."""
    return [r for r in rows if r.get("content_status") == "official"]


def region_index(args):
    result = regions.list_regions(args)
    result["data"] = _in_rockstar_order(result["data"])
    _attach_covers("region", result["data"], regions_repo.ids_by_slug, media_slots.REGION_STAGE)
    ids = regions_repo.ids_by_slug([r["slug"] for r in result["data"]])
    pictures = media.counts("region", ids.values())
    for number, r in enumerate(result["data"], 1):
        r["number"] = number
        r["pictures"] = pictures.get(ids.get(r["slug"]), 0)
        r["people"] = [c["full_name"] for c in regions_repo.characters_based_in(ids[r["slug"]])]
        r["location_count"] = 0   # invented places are not Rockstar's, so the index never counts them
    result["total"] = len(result["data"])
    result["hero_cover"] = _page_cover("regions")
    return result


def region_detail(slug):
    region, region_id = regions.get_region_with_id(slug)
    region["locations"] = _official(region["locations"])
    region["missions"] = _official(missions_repo.in_region(region_id))
    art = media_slots.REGION_ART.get(slug, {})
    frames = media.for_entity("region", region_id, limit=24)
    by_slug = {m["slug"]: m for m in frames}
    stage = by_slug.get(art.get("hero")) or by_slug.get(media_slots.REGION_STAGE.get(slug)) or (frames[0] if frames else None)
    postcard = next((m for m in frames if m["media_type"] == "artwork" and m is not stage), None)
    region["hero"], region["postcard"] = stage, postcard
    region["plate"] = art.get("plate", "bl")
    # the pictures after the opening and the postcard, grouped as the art direction says; any picture it does not name follows, so nothing Rockstar published for the region is lost
    used = {m["slug"] for m in (stage, postcard) if m}
    groups = []
    for names in art.get("story", ()):
        group = [by_slug[n] for n in names if n in by_slug and n not in used]
        used.update(m["slug"] for m in group)
        if group:
            groups.append(group)
    rest = [m for m in frames if m["slug"] not in used]
    if rest:
        groups.append(rest[:3])
        groups.extend([m] for m in rest[3:])
    region["groups"] = groups
    region["picture_count"] = len(frames)
    region["shots"] = sum(1 for m in frames if m["media_type"] == "screenshot")
    ordered = _in_rockstar_order(regions_repo.list_all())
    _attach_covers("region", ordered, regions_repo.ids_by_slug, media_slots.REGION_STAGE)
    me = next((i for i, r in enumerate(ordered) if r["slug"] == slug), 0)
    for i, r in enumerate(ordered, 1):
        r["number"] = i
    region["number"], region["total"] = me + 1, len(ordered)
    region["all_regions"] = ordered
    region["previous"] = ordered[(me - 1) % len(ordered)] if len(ordered) > 1 else None
    region["next"] = ordered[(me + 1) % len(ordered)] if len(ordered) > 1 else None
    region["other_regions"] = [r for r in ordered if r["slug"] != slug]
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
