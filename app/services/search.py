"""Business rules for site search: what a query may look like, which kinds of record are searched, how the results are ranked and linked.

Visibility is the pages' own: only official characters and vehicles have public pages, so only they can be found; places and stories (all Team Valkyrie's own, shown
as Concept) have public pages, so they can. Nothing here reads the request: the blueprints pass the arguments in."""
import re
import unicodedata

from flask import url_for

from ..repositories import search as repo
from . import validation as v

KINDS = ("page", "character", "vehicle", "region", "place", "story", "music")
KIND_LABELS = {"page": "Page", "character": "Character", "vehicle": "Vehicle", "region": "Region", "place": "Place", "story": "Story", "music": "Music"}
STATUS_LABELS = {"official": "Official", "fan": "Fan view", "demo": "Concept"}
MAX_TERMS = 5
MAX_RESULTS = 200             # the deepest result anyone can page to
API_DEFAULT_LIMIT = 8
API_MAX_LIMIT = 20
PAGE_PER_PAGE = 12

# The site's own pages, found by name or by what a visitor might type. (title, endpoint, one line, extra words)
PAGES = (
    ("Home", "main.index", "The front page", "start homepage trailer"),
    ("Characters", "pages.characters", "The eight characters Rockstar has named", "cast people jason lucia"),
    ("Garage", "pages.vehicles", "The seven vehicles Rockstar has shown", "vehicles cars bikes machines"),
    ("Leonida", "pages.regions", "The six regions of the state", "regions map places state"),
    ("Music", "pages.music", "Radio stations, the score and the album", "radio songs score album soundtrack"),
    ("Media", "pages.media", "The Screening: Rockstar's own videos, screenshots and artwork", "videos trailers screenshots artwork wallpapers gallery"),
    ("Stories", "pages.missions", "Original stories from Team Valkyrie", "missions tales heists"),
    ("About", "main.about", "What the project is and what the labels mean", "project labels official concept"),
    ("Credits", "main.credits", "Attribution, non-affiliation and licence", "legal rights licence fonts"),
)


# ------------------------------------------------------------------ the query
def fold(text):
    """Lower case without accents, so 'cafe' finds 'Café' the way the database's collation does."""
    return "".join(c for c in unicodedata.normalize("NFKD", text.casefold()) if not unicodedata.combining(c))


def normalise(raw):
    """Control characters become spaces, runs of white space become one space, the ends are trimmed."""
    return re.sub(r"\s+", " ", re.sub(r"[\x00-\x1f\x7f]", " ", raw)).strip()


def parse_query(args, problems):
    raw = args.get("q")
    if raw is None:
        return ""
    q = normalise(raw)
    if len(q) > v.MAX_QUERY_LENGTH:
        problems["q"] = f"must be at most {v.MAX_QUERY_LENGTH} characters"
        return ""
    if len(set(q.split())) > MAX_TERMS:
        problems["q"] = f"must be at most {MAX_TERMS} words"
        return ""
    return q


def like_parts(q):
    """The LIKE patterns the repository needs: one per word, and four for the whole phrase (exact, prefix, word prefix, contains). Wildcards in the text are escaped."""
    words = list(dict.fromkeys(q.split()))
    terms = [f"%{v.escape_like(word)}%" for word in words]
    escaped = v.escape_like(q)
    return terms, [q, f"{escaped}%", f"% {escaped}%", f"%{escaped}%"]


# ------------------------------------------------------------------ the site's own pages
def _page_rank(title, phrase):
    title = fold(title)
    if title == phrase:
        return 100
    if title.startswith(phrase):
        return 80
    if f" {phrase}" in title:
        return 60
    if phrase in title:
        return 40
    return 20


def _page_hits(q):
    words, phrase = [fold(w) for w in dict.fromkeys(q.split())], fold(q)
    hits = []
    for title, endpoint, detail, extra in PAGES:
        haystack = fold(f"{title} {detail} {extra}")
        if all(word in haystack for word in words):
            hits.append({"kind": "page", "slug": endpoint, "title": title, "detail": "Page", "summary": detail, "status": "official", "anchor": "",
                         "rank_": _page_rank(title, phrase)})
    return hits


# ------------------------------------------------------------------ results
def _url(hit):
    kind, slug = hit["kind"], hit["slug"]
    if kind == "page":
        return url_for(slug)
    if kind == "character":
        return url_for("pages.character_detail", slug=slug)
    if kind == "vehicle":
        return url_for("pages.vehicle_detail", slug=slug)
    if kind == "region":
        return url_for("pages.region_detail", slug=slug)
    if kind == "place":
        return url_for("pages.location_detail", slug=slug)
    if kind == "story":
        return url_for("pages.mission_detail", slug=slug)
    return url_for("pages.music", _anchor=hit["anchor"] or None)


def _present(hit):
    status = hit["status"]
    return {
        "kind": hit["kind"], "kind_label": KIND_LABELS[hit["kind"]], "title": hit["title"], "detail": hit["detail"] or "", "summary": (hit["summary"] or "")[:160],
        "url": _url(hit), "status": status, "status_label": None if hit["kind"] == "page" else STATUS_LABELS.get(status, status),
    }


def _kinds(kind):
    return KINDS if kind == "all" else (kind,)


def _find(q, kind, limit, offset):
    """The merged, ranked rows for a query: the database's rows for the record kinds plus the site's own pages."""
    terms, phrase_params = like_parts(q)
    kinds = _kinds(kind)
    record_kinds = tuple(k for k in kinds if k != "page")
    rows = repo.search(record_kinds, terms, phrase_params, offset + limit, 0)
    pages = _page_hits(q) if "page" in kinds else []
    order = {name: position for position, name in enumerate(repo.KIND_ORDER)}
    merged = sorted(pages, key=lambda h: (-h["rank_"], h["title"])) + rows
    merged.sort(key=lambda h: (-h["rank_"], -1 if h["kind"] == "page" else order[h["kind"]]))     # stable: titles keep the database's order inside a kind
    return merged[offset:offset + limit]


def api_search(args):
    """GET /api/v1/search?q=&type=&limit=: the few best matches, for the command palette. One database query."""
    problems = {}
    q = parse_query(args, problems)
    kind = v.clean_choice(args, "type", ("all",) + KINDS, problems, default="all")
    limit = v.clean_int(args, "limit", problems, API_DEFAULT_LIMIT, 1, API_MAX_LIMIT)
    if not q and "q" not in problems:
        problems["q"] = "is required"
    v.raise_if_problems(problems)
    hits = _find(q, kind, limit, 0)
    return {"query": q, "type": kind, "results": [_present(h) for h in hits]}


def page_search(args):
    """GET /search: the full results page, with how many each kind has, paged. An empty query is the help state: no database work."""
    problems = {}
    q = parse_query(args, problems)
    kind = v.clean_choice(args, "type", ("all",) + KINDS, problems, default="all")
    per_page = v.clean_int(args, "per_page", problems, PAGE_PER_PAGE, 1, v.MAX_PER_PAGE)
    page = v.clean_int(args, "page", problems, 1, 1, 100000)
    if (page - 1) * per_page >= MAX_RESULTS and "page" not in problems:
        problems["page"] = f"a search shows at most {MAX_RESULTS} results"
    v.raise_if_problems(problems)
    empty = {"query": q, "type": kind, "results": [], "counts": {}, "total": 0, "pagination": v.pagination_meta(1, per_page, 0), "kinds": KINDS,
             "kind_labels": KIND_LABELS, "searched": False}
    if not q:
        return empty
    terms, _ = like_parts(q)
    counts = repo.counts(tuple(k for k in KINDS if k != "page"), terms)
    page_hits = _page_hits(q)
    counts["page"] = len(page_hits)
    counts = {k: counts.get(k, 0) for k in KINDS}
    total = min(sum(counts.values()) if kind == "all" else counts[kind], MAX_RESULTS)
    hits = _find(q, kind, per_page, (page - 1) * per_page) if total else []
    return {"query": q, "type": kind, "results": [_present(h) for h in hits], "counts": counts, "total": total,
            "pagination": v.pagination_meta(page, per_page, total), "kinds": KINDS, "kind_labels": KIND_LABELS, "searched": True}
