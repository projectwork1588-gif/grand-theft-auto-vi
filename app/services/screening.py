"""The Media page, "The Screening": Rockstar's own videos, clips, screenshots and artwork as recorded in the database (media_collections, media_collection_items).

Every title, date, runtime, description and count is Rockstar's own, copied from its Media pages by migration 009; nothing here is invented. Pictures are drawn only from Rockstar's own
image address and videos only through Rockstar's own player (app.media_urls); a link leaves the site only if it is https to Rockstar's site or its download host. A bad database
row therefore shows no picture and no link, and its text is escaped by the template.

The composition of a chapter is decided here, in plain functions that the tests can read: `subject_of` turns Rockstar's title into the chapter's name, `layout_rows` decides
how many pictures sit in each row."""
import re
from urllib.parse import urlparse

from .. import media_slots
from ..media_urls import is_official_image, player_src
from ..repositories import media as repo

LINK_HOSTS = ("www.rockstargames.com", "rockstargames.com")
DOWNLOAD_HOSTS = media_slots.SCREENING_ZIP_HOSTS
NUMBER_WORDS = {1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six", 7: "Seven", 8: "Eight", 9: "Nine", 10: "Ten", 12: "Twelve"}

# how many pictures a row holds. The rhythm of a chapter is this cycle, after its opening frame.
ROW_SIZES = {"stage": 1, "full": 1, "duo": 2, "stagger": 2, "stagger_r": 2, "trio": 3}
ROW_CYCLE = ("stagger", "trio", "duo", "stagger_r", "trio")
CLOSING = {1: "full", 2: "duo", 3: "trio"}


def https_link(url, hosts=LINK_HOSTS):
    """The address if it is an https link to one of `hosts`, otherwise None (the template then shows no link)."""
    if not url or len(url) > 500 or re.search(r'[\s"<>\\]', url):
        return None
    parts = urlparse(url)
    return url if parts.scheme == "https" and parts.hostname in hosts and not parts.username else None


def day(d):
    """A date the way the page says it: 15 October 2026 (no zero, and no platform-specific format code)."""
    return f"{d.day} {d:%B %Y}" if d else None


def runtime_text(seconds):
    """Rockstar writes a runtime as minutes:seconds (1:29, 26:48)."""
    return f"{seconds // 60}:{seconds % 60:02d}" if seconds else None


def number_word(n):
    return NUMBER_WORDS.get(n, str(n))


def series(parts):
    """"4 films, 187 pictures and 9 clips": the non-empty counts, in order, as one phrase."""
    words = [f"{n} {one if n == 1 else many}" for n, one, many in parts if n]
    return words[0] if len(words) == 1 else ", ".join(words[:-1]) + " and " + words[-1] if words else ""


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.replace("’", "").replace("'", "").lower()).strip("-")


def subject_of(title):
    """The chapter a screenshot belongs to: Rockstar's title without its trailing number ("Jason Duval 07" -> "Jason Duval")."""
    return re.sub(r"\s+\d+$", "", title).strip() or title


def layout_rows(items, lead=True):
    """Split a chapter's pictures into rows: an opening frame (when there are enough pictures), then a repeating rhythm of staggered pair, trio, even pair, mirrored pair, trio.
    A chapter that is too short for its next row closes with the row that fits. Returns [(kind, [items])] and uses every picture exactly once, in order."""
    n, rows, i = len(items), [], 0
    if lead and n >= 4:
        rows.append(("stage", items[:1]))
        i = 1
    if not lead and n <= 3:
        return [({1: "full", 2: "stagger", 3: "trio"}[n], list(items))] if n else []
    step = 0
    while i < n:
        kind = ROW_CYCLE[step % len(ROW_CYCLE)]
        step += 1
        size = ROW_SIZES[kind]
        if size > n - i:
            size = n - i
            kind = CLOSING[size]
        rows.append((kind, items[i:i + size]))
        i += size
    return rows


def featured_rows(items):
    """The few pictures a chapter shows large, in the first design's own grammar: a 21:9 opening frame, then a row of three (or two, or one) under it. Returns [(kind, [items])]."""
    if len(items) >= 4:
        return [("stage", items[:1]), ("trio", items[1:4])]
    if len(items) == 3:
        return [("stage", items[:1]), ("duo", items[1:3])]
    return [({1: "full", 2: "duo"}[len(items)], list(items))] if items else []


class _Anchors:
    """One unique, readable id for each picture, used by deep links ("#shot-jason-duval-07")."""

    def __init__(self):
        self.used = set()

    def make(self, prefix, title):
        base = f"{prefix}-{slugify(title)}"
        anchor, n = base, 1
        while anchor in self.used:
            n += 1
            anchor = f"{base}-{n}"
        self.used.add(anchor)
        return anchor


def _still(row, prefix, anchors):
    """One picture, or None if its address is not one of Rockstar's own."""
    if not is_official_image(row["embed_url"]):
        return None
    focus = media_slots.SCREENING_FOCUS.get(row["title"], media_slots.SCREENING_REST)
    return {"title": row["title"], "url": row["embed_url"], "anchor": anchors.make(prefix, row["title"]), "position": row["position"],
            "px": round(focus[0] * 100 / 5) * 5, "py": round(focus[1] * 100 / 5) * 5, "slug": row["media_slug"]}


def _chapters(items, order, links, kind_prefix):
    """Group consecutive screenshots by subject. `order` lists the subjects wanted first; any other subject follows in Rockstar's order."""
    bysubject, first = {}, {}
    for it in items:
        s = subject_of(it["title"])
        bysubject.setdefault(s, []).append(it)
        first.setdefault(s, it["position"])
    wanted = [s for s in order if s in bysubject]
    chapters = []
    for s in wanted:
        chapters.append(_chapter(s, bysubject.pop(s), links, kind_prefix))
    return chapters, bysubject


def _chapter(subject, pictures, links, prefix=None, featured=False):
    """A chapter of screenshots. With `featured`, only the first few pictures are drawn large and the others (`rest`) wait behind "View all"; they are still every one in the chapter's one
    viewer group, in Rockstar's order."""
    target = links.get(subject)
    shown = pictures[:media_slots.SCREENING_FEATURED_COUNT] if featured else pictures
    return {"subject": subject, "id": prefix + "-" + slugify(subject) if prefix else slugify(subject), "count": len(pictures), "pictures": pictures,
            "rows": featured_rows(shown) if featured else layout_rows(pictures), "rest": pictures[len(shown):], "link": target,
            "top": pictures[:media_slots.SCREENING_FEATURED_COUNT]}


def _video(row):
    player = player_src(row["embed_url"], True)
    poster = row["poster_url"] if is_official_image(row["poster_url"]) else None
    return {"title": row["title"], "date": row["published_on"], "date_text": day(row["published_on"]), "year": row["published_on"].year if row["published_on"] else None,
            "runtime": runtime_text(row["runtime_seconds"]), "seconds": row["runtime_seconds"], "description": row["description"], "poster": poster, "player": player,
            "source": https_link(row["source_url"]), "slug": row["media_slug"], "age_gate": row["media_slug"] in media_slots.SCREENING_AGE_GATED}


def _entity_links(people, places):
    """subject -> (endpoint, slug, label) for the people and regions that have an official page here."""
    out = {}
    for subject, (kind, slug) in media_slots.SCREENING_LINKS.items():
        known = (people if kind == "character" else places).get(slug)
        if known:
            out[subject] = {"endpoint": "pages.character_detail" if kind == "character" else "pages.region_detail", "slug": slug, "label": known}
    return out


def page(people=None, places=None):
    """Everything the Media page draws. `people` and `places` are {slug: name} for the official characters and the regions that exist on this site (so a link is never dead)."""
    collections = {c["slug"]: c for c in repo.collections()}
    if not collections:
        return {"empty": True}
    links = _entity_links(people or {}, places or {})
    anchors = _Anchors()
    data = {"empty": False, "collections": collections}

    # ---- videos: the opening is the Launch Trailer (or the newest), the films run oldest to newest
    films = sorted((_video(r) for r in repo.collection_items("videos")), key=lambda v: (v["date"] is None, v["date"]))
    films = [f for f in films if f["player"] and f["poster"]]
    opening = next((f for f in films if f["slug"] == media_slots.SCREENING_OPENING_VIDEO), films[-1] if films else None)
    seen = set()
    for f in films:
        f["repeat"] = f["description"] in seen          # Rockstar gives Trailers 1 and 2 the same text: it is shown once
        if f["description"]:
            seen.add(f["description"])
    data["opening"], data["films"] = opening, films

    # ---- screenshots: the pair, the people, the places, then anything else Rockstar lists
    shots = [s for s in (_still(r, "shot", anchors) for r in repo.collection_items("screenshots")) if s]
    pair_pics = [s for s in shots if subject_of(s["title"]) == media_slots.SCREENING_PAIR]
    pair = _chapter(media_slots.SCREENING_PAIR, pair_pics, links, "pair", featured=True) if pair_pics else None
    people_ch, rest = _chapters([s for s in shots if subject_of(s["title"]) in media_slots.SCREENING_PEOPLE], media_slots.SCREENING_PEOPLE, links, "people")
    places_ch, rest2 = _chapters([s for s in shots if subject_of(s["title"]) in media_slots.SCREENING_PLACES], media_slots.SCREENING_PLACES, links, "place")
    named = {media_slots.SCREENING_PAIR, *media_slots.SCREENING_PEOPLE, *media_slots.SCREENING_PLACES}
    others = [s for s in shots if subject_of(s["title"]) not in named]
    other_ch, _ = _chapters(others, [subject_of(s["title"]) for s in others], links, "more")
    data.update(pair=pair, people=people_ch, places=places_ch, more=other_ch, shots=shots)

    # ---- artwork and wallpapers, uncropped, in Rockstar's order
    art = [a for a in (_still(r, "art", anchors) for r in repo.collection_items("artwork-wallpapers")) if a]
    data["art"] = art
    hang = [a for title in media_slots.SCREENING_ART_HANG for a in art if a["title"] == title]
    data["art_hang"] = (hang + [a for a in art if a not in hang])[:media_slots.SCREENING_FEATURED_COUNT]

    # ---- clips: a poster and a link to Rockstar's own page (the clips play there)
    clips = []
    for r in repo.collection_items("clips"):
        poster = r["embed_url"] if is_official_image(r["embed_url"]) else None
        link = https_link(r["source_url"])
        if poster and link:
            clips.append({"title": r["title"], "poster": poster, "link": link, "square": r["title"] in media_slots.SCREENING_SQUARE_CLIPS})
    data["clips"] = clips

    # ---- the two editions' collections, in Rockstar's own order, grouped by what each picture shows
    editions = []
    for slug in ("ultimate-edition-benefits", "vintage-vice-city-pack"):
        coll = collections.get(slug)
        if not coll:
            continue
        pictures = [s for s in (_still(r, "shot", anchors) for r in repo.collection_items(slug)) if s]
        if not pictures:
            continue                                                   # an edition with nothing to show leaves its frames out
        order = []
        for p in pictures:
            if subject_of(p["title"]) not in order:
                order.append(subject_of(p["title"]))
        groups, _ = _chapters(pictures, order, {}, slug)
        by_slug = {slugify(g["subject"]): g for g in groups}
        frames = [by_slug[slugify(n)] for n in media_slots.SCREENING_SHOWROOM.get(slug, ()) if slugify(n) in by_slug]
        frames = (frames + [g for g in groups if g not in frames])[:media_slots.SCREENING_FEATURED_COUNT]
        editions.append({"slug": slug, "title": coll["title"], "count": len(pictures), "groups": groups, "source": https_link(coll["source_url"]), "pictures": pictures,
                         "checked": day(coll["verified_on"]), "showroom": frames})
    data["editions"] = editions

    # ---- downloads: Rockstar's own zip for each collection that has one
    shown = {"videos": len(films), "clips": len(clips), "screenshots": len(shots), "artwork-wallpapers": len(art), **{e["slug"]: e["count"] for e in editions}}
    downloads = []
    for c in collections.values():
        link = https_link(c["download_url"], DOWNLOAD_HOSTS)
        if link and shown.get(c["slug"]):                    # a zip is offered only for a collection this page shows, and counted as the page shows it
            downloads.append({"title": c["title"], "count": shown[c["slug"]], "url": link, "bytes": c["download_bytes"],
                              "size": f"{c['download_bytes'] / 1048576:.0f} MB" if c["download_bytes"] else None, "kind": c["kind"]})
    data["downloads"] = downloads

    # ---- every still, counted from the chapters
    stills = len(shots) + sum(e["count"] for e in editions) + len(art)

    # ---- counts: what the page shows, derived from what it shows
    n_people = sum(c["count"] for c in people_ch)
    n_places = sum(c["count"] for c in places_ch)
    n_editions = sum(e["count"] for e in editions)
    data["counts"] = {"films": len(films), "pair": pair["count"] if pair else 0, "people": n_people, "places": n_places, "art": len(art), "clips": len(clips),
                      "editions": n_editions, "downloads": len(downloads), "stills": stills, "screenshots": len(shots)}
    data["checked"] = day(max((c["verified_on"] for c in collections.values() if c.get("verified_on")), default=None))
    c = data["counts"]
    rail = [("films", f"The {number_word(c['films']).lower()} films" if c["films"] else None, c["films"]),
            ("pair", media_slots.SCREENING_PAIR, c["pair"]),
            ("people", "The people", c["people"]),
            ("places", "The places", c["places"]),
            ("art", "Key art", c["art"]),
            ("clips", "Clips", c["clips"]),
            ("editions", "The editions", c["editions"]),
            ("downloads", "Downloads", c["downloads"])]
    data["rail"] = [{"id": i, "label": label, "count": n} for i, label, n in rail if label and n]
    data["rail_no"] = {r["id"]: f"{k:02d}" for k, r in enumerate(data["rail"], 1)}      # the reel numbers the headings and the rail share
    data["films_word"] = number_word(c["films"])
    data["lede_counts"] = series([(c["films"], "film", "films"), (c["stills"], "picture", "pictures"), (c["clips"], "clip", "clips")])
    data["inventory"] = series([(c["films"], "video", "videos"), (c["clips"], "clip", "clips"), (c["screenshots"], "screenshot", "screenshots"),
                                (c["art"], "piece of artwork", "pieces of artwork"), (c["editions"], "edition screenshot", "edition screenshots")])
    return data
