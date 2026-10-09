"""Business rules for missions and the story archive."""
from werkzeug.exceptions import NotFound

from ..repositories import missions as repo
from . import validation as v

PER_PAGE = 8


def list_missions(args):
    problems = {}
    q = v.clean_text(args, "q", problems)
    mission_type = v.clean_choice(args, "type", v.MISSION_TYPES, problems)
    status = v.clean_choice(args, "status", v.CONTENT_STATUSES, problems)
    sort = v.clean_choice(args, "sort", tuple(repo.SORT_ORDERS), problems, default="title_asc")
    page = v.clean_int(args, "page", problems, default=1, minimum=1, maximum=100000)
    per_page = v.clean_int(args, "per_page", problems, PER_PAGE, 1, v.MAX_PER_PAGE)
    v.raise_if_problems(problems)

    q_like = f"%{v.escape_like(q)}%" if q else None
    rows, total = repo.search(q_like, mission_type, status, sort, per_page, (page - 1) * per_page)
    return {
        "data": rows,
        "pagination": v.pagination_meta(page, per_page, total),
        "filters": {"q": q, "type": mission_type, "status": status, "sort": sort},
    }


def get_mission(slug):
    v.require_slug(slug)
    mission = repo.get_by_slug(slug)
    if mission is None:
        raise NotFound("No mission with that slug.")
    mission_id = mission.pop("mission_id")
    mission["characters"] = repo.characters_for(mission_id)
    mission["vehicles"] = repo.vehicles_for(mission_id)
    mission["locations"] = repo.locations_for(mission_id)
    mission["related"] = repo.related(mission_id)
    return mission
