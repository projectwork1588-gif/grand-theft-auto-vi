"""Business rules for vehicles and categories."""
from werkzeug.exceptions import NotFound

from ..repositories import vehicles as repo
from . import validation as v

PER_PAGE = 9


def list_vehicles(args):
    problems = {}
    q = v.clean_text(args, "q", problems)
    category = v.clean_slug(args, "category", problems)
    status = v.clean_choice(args, "status", v.CONTENT_STATUSES, problems)
    sort = v.clean_choice(args, "sort", tuple(repo.SORT_ORDERS), problems, default="name_asc")
    page = v.clean_int(args, "page", problems, default=1, minimum=1, maximum=100000)
    per_page = v.clean_int(args, "per_page", problems, PER_PAGE, 1, v.MAX_PER_PAGE)
    v.raise_if_problems(problems)

    q_like = f"%{v.escape_like(q)}%" if q else None
    rows, total = repo.search(q_like, category, status, sort, per_page, (page - 1) * per_page)
    return {
        "data": rows,
        "pagination": v.pagination_meta(page, per_page, total),
        "filters": {"q": q, "category": category, "status": status, "sort": sort},
    }


def list_categories(args=None):
    problems = {}
    status = v.clean_choice(args or {}, "status", v.CONTENT_STATUSES, problems)
    v.raise_if_problems(problems)
    return {"data": repo.categories_with_counts(status)}


def get_vehicle_with_id(slug):
    """The public payload plus the internal id (kept server-side, used to attach media)."""
    v.require_slug(slug)
    vehicle = repo.get_by_slug(slug)
    if vehicle is None:
        raise NotFound("No vehicle with that slug.")
    vehicle_id = vehicle.pop("vehicle_id")
    category_id = vehicle.pop("category_id")
    vehicle["missions"] = repo.missions_for(vehicle_id)
    vehicle["locations"] = repo.locations_for(vehicle_id)
    vehicle["same_category"] = repo.same_category(category_id, vehicle_id)
    return vehicle, vehicle_id


def get_vehicle(slug):
    return get_vehicle_with_id(slug)[0]
