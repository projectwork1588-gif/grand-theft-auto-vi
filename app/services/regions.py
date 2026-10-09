"""Business rules for regions."""
from werkzeug.exceptions import NotFound

from ..repositories import regions as repo
from . import validation as v


def list_regions(args):
    problems = {}
    status = v.clean_choice(args, "status", v.CONTENT_STATUSES, problems)
    v.raise_if_problems(problems)
    return {"data": repo.list_all(status), "filters": {"status": status}}


def get_region(slug):
    region = repo.get_by_slug(slug)
    if region is None:
        raise NotFound("No region with that slug.")
    region_id = region.pop("region_id")
    region["locations"] = repo.locations_in(region_id)
    region["characters"] = repo.characters_based_in(region_id)
    return region
