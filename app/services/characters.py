"""Business rules for characters: validate input, call repositories, shape the result."""
from werkzeug.exceptions import NotFound

from ..repositories import characters as repo
from . import validation as v


def list_characters(args, include_original=False):
    problems = {}
    q = v.clean_text(args, "q", problems)
    status = v.clean_choice(args, "status", v.CONTENT_STATUSES, problems)
    if status and status != "official" and not include_original:
        problems["status"] = "original characters are only listed with include=original"
    region = v.clean_slug(args, "region", problems)
    sort = v.clean_choice(args, "sort", tuple(repo.SORT_ORDERS), problems, default="name_asc")
    page = v.clean_int(args, "page", problems, default=1, minimum=1, maximum=100000)
    per_page = v.clean_int(args, "per_page", problems, v.DEFAULT_PER_PAGE, 1, v.MAX_PER_PAGE)
    v.raise_if_problems(problems)

    q_like = f"%{v.escape_like(q)}%" if q else None
    rows, total = repo.search(q_like, status, region, sort, per_page, (page - 1) * per_page, include_original)
    return {
        "data": rows,
        "pagination": v.pagination_meta(page, per_page, total),
        "filters": {"q": q, "status": status, "region": region, "sort": sort},
    }


def wants_original(args):
    """True when the caller asked for the documented ?include=original switch (API only)."""
    problems = {}
    value = v.clean_choice(args, "include", ("original",), problems)
    v.raise_if_problems(problems)
    return value == "original"


def get_character_with_id(slug, include_original=False):
    """The public payload plus the internal id (kept server-side, used to attach media and co-stars)."""
    v.require_slug(slug)
    character = repo.get_by_slug(slug, include_original)
    if character is None:
        raise NotFound("No character with that slug.")
    character_id = character.pop("character_id")  # internal key never reaches the API response
    character["relationships"] = repo.relationships_for(character_id, include_original)
    character["regions"] = repo.regions_for(character_id)
    character["missions"] = repo.missions_for(character_id)
    character["locations"] = repo.locations_for(character_id)
    return character, character_id


def get_character(slug, include_original=False):
    return get_character_with_id(slug, include_original)[0]
