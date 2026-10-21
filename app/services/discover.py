"""Home's two newer parts, built only from what the site already holds:

* the picture challenge ("How well do you know Leonida?"): Rockstar's own pictures, asked about by the name Rockstar files them under (a person, a place or a machine), with the
  site's own page for the answer as the reward. Nothing is invented: every picture is a media_assets row that Rockstar published, its answer is the title or link Rockstar gave
  it, and the facts shown after an answer are the same database rows the Characters, Leonida and Garage pages show.
* the official release block: the facts in media_slots.OFFICIAL_RELEASE, with the cover art, the Launch Trailer and its poster as rows of media_assets.
"""
from .. import media_slots, media_urls
from ..repositories import media, regions as regions_repo
from . import screening

PER_ANSWER = 3        # pictures kept for each answer, in Rockstar's order
MIN_ANSWERS = 4       # a question needs one right answer and three others of its kind
ROUNDS = 5

KINDS = ("people", "places", "machines")


def _path(row):
    """The part of a picture's address after Rockstar's image prefix (the page rebuilds the whole address, and checks the prefix again), or None."""
    url = (row or {}).get("embed_url")
    return url[len(media_urls.IMAGE_PREFIX):] if media_urls.is_official_image(url) else None


def _trim(text, limit=170):
    text = " ".join((text or "").split())
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].rstrip(",;:")
    return cut + "…"


def challenge(people, regions, vehicles, link):
    """The data for the picture challenge, or None if the database cannot ask enough questions.

    `people`: official characters (slug, full_name, role_title, summary); `regions`: (slug, name, summary); `vehicles`: (slug, name, manufacturer, summary);
    `link(kind, slug)`: the address of the site's own page, kind being character, region or vehicle."""
    pools = {k: {} for k in KINDS}
    answers = {k: {} for k in KINDS}
    by_character = {c["slug"]: c for c in people}
    by_region = {r["slug"]: r for r in regions}
    by_vehicle = {v["slug"]: v for v in vehicles}
    region_ids = regions_repo.ids_by_slug(list(by_region)) if by_region else {}

    def add(kind, slug, row):
        path = _path(row)
        if not path:
            return
        kept = pools[kind].setdefault(slug, [])
        if len(kept) < PER_ANSWER and path not in kept:
            kept.append(path)

    # people and places: Rockstar files every screenshot under the name or the place it shows
    for item in media.collection_items("screenshots"):
        target = media_slots.SCREENING_LINKS.get(screening.subject_of(item["title"]))
        if not target:
            continue
        kind, slug = target
        if kind == "character" and slug in by_character:
            add("people", slug, item)
        elif kind == "region" and slug in by_region:
            add("places", slug, item)
    # machines: pictures the database links to exactly one official vehicle
    for row in media.solo_vehicle_pictures():
        if row["vehicle_slug"] in by_vehicle:
            add("machines", row["vehicle_slug"], row)

    for slug in pools["people"]:
        c = by_character[slug]
        answers["people"][slug] = {"n": c["full_name"], "t": c["role_title"], "s": _trim(c["summary"]), "h": link("character", slug)}
    for slug in pools["places"]:
        r = by_region[slug]
        who = [{"n": b["full_name"], "t": _trim(b["home_location_name"], 110), "h": link("character", b["slug"])} for b in regions_repo.characters_based_in(region_ids[slug])] if slug in region_ids else []
        answers["places"][slug] = {"n": r["name"], "t": "Leonida", "s": _trim(r["summary"]), "h": link("region", slug), "b": who}
    for slug in pools["machines"]:
        v = by_vehicle[slug]
        answers["machines"][slug] = {"n": v["name"], "t": v.get("manufacturer") or "", "s": _trim(v["summary"]), "h": link("vehicle", slug)}

    usable = {k: [{"p": p, "a": slug} for slug, paths in pools[k].items() for p in paths] for k in KINDS if len(pools[k]) >= MIN_ANSWERS}
    if len(usable) < 2 or sum(len(v) for v in usable.values()) < ROUNDS:
        return None
    return {"prefix": media_urls.IMAGE_PREFIX, "rounds": ROUNDS, "pools": usable, "answers": {k: answers[k] for k in usable}}


def release():
    """The official release block: Rockstar's facts (media_slots.OFFICIAL_RELEASE) and its pictures; None-valued parts are left out by the template."""
    facts = dict(media_slots.OFFICIAL_RELEASE)
    rows = media.by_slugs([facts["art"], facts["video"], facts["poster"]])
    video = rows.get(facts["video"])
    if not (video and media_urls.player_src(video["embed_url"])):
        video = None
    item = next((i for i in media.collection_items("videos") if i["media_slug"] == facts["video"]), None)
    facts.update({
        "art": rows.get(facts["art"]) if media_urls.is_official_image((rows.get(facts["art"]) or {}).get("embed_url")) else None,
        "video": video,
        "poster": rows.get(facts["poster"]),
        "video_note": " · ".join(x for x in (screening.day(item["published_on"]) if item else None, screening.runtime_text(item["runtime_seconds"]) if item else None) if x),
    })
    return facts
