"""Business rules for locations."""
from werkzeug.exceptions import NotFound

from ..repositories import locations as repo
from . import validation as v

PER_PAGE = 12


def list_locations(args):
    problems = {}
    q = v.clean_text(args, "q", problems)
    region = v.clean_slug(args, "region", problems)
    location_type = v.clean_choice(args, "type", v.LOCATION_TYPES, problems)
    status = v.clean_choice(args, "status", v.CONTENT_STATUSES, problems)
    sort = v.clean_choice(args, "sort", tuple(repo.SORT_ORDERS), problems, default="region")
    page = v.clean_int(args, "page", problems, default=1, minimum=1, maximum=100000)
    per_page = v.clean_int(args, "per_page", problems, PER_PAGE, 1, v.MAX_PER_PAGE)
    v.raise_if_problems(problems)

    q_like = f"%{v.escape_like(q)}%" if q else None
    rows, total = repo.search(q_like, region, location_type, status, sort, per_page, (page - 1) * per_page)
    return {
        "data": rows,
        "pagination": v.pagination_meta(page, per_page, total),
        "filters": {"q": q, "region": region, "type": location_type, "status": status, "sort": sort},
    }


def get_location(slug):
    v.require_slug(slug)
    location = repo.get_by_slug(slug)
    if location is None:
        raise NotFound("No location with that slug.")
    location_id = location.pop("location_id")
    region_id = location.pop("region_id")
    location["residents"] = repo.residents(location_id)
    location["characters_in_missions"] = repo.characters_in_missions_here(location_id)
    location["missions"] = repo.missions_here(location_id)
    location["neighbours"] = repo.neighbours(region_id, location_id)
    return location
