"""Input validation for query-string parameters. Pure Python, no database access."""
import re

CONTENT_STATUSES = ("official", "fan", "demo")
MISSION_TYPES = ("story", "side", "heist", "activity")  # mirrors the missions.mission_type ENUM
LOCATION_TYPES = ("city", "district", "landmark", "venue", "wilderness", "waterfront")  # locations.location_type ENUM
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MAX_QUERY_LENGTH = 80
MAX_PER_PAGE = 50
DEFAULT_PER_PAGE = 12


class ValidationError(Exception):
    """Raised with a dict of {parameter: problem} when input is not acceptable."""

    def __init__(self, problems):
        super().__init__("Invalid request parameters")
        self.problems = problems


def clean_text(args, name, problems, max_length=MAX_QUERY_LENGTH):
    value = args.get(name)
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    if len(value) > max_length:
        problems[name] = f"must be at most {max_length} characters"
        return None
    return value


def clean_choice(args, name, allowed, problems, default=None):
    value = args.get(name)
    if value is None or value == "":
        return default
    value = value.strip().lower()
    if value not in allowed:
        problems[name] = f"must be one of: {', '.join(allowed)}"
        return default
    return value


def clean_slug(args, name, problems):
    value = clean_text(args, name, problems, max_length=80)
    if value is not None and not SLUG_PATTERN.match(value):
        problems[name] = "must be a lowercase slug such as 'vice-city'"
        return None
    return value


def clean_int(args, name, problems, default, minimum, maximum):
    raw = args.get(name)
    if raw is None or raw == "":
        return default
    try:
        value = int(raw)
    except ValueError:
        problems[name] = "must be a whole number"
        return default
    if value < minimum or value > maximum:
        problems[name] = f"must be between {minimum} and {maximum}"
        return default
    return value


def escape_like(text):
    """Escape LIKE wildcards so a search for '50%' means a literal percent sign.

    The SQL uses ESCAPE '!' to match this function.
    """
    return text.replace("!", "!!").replace("%", "!%").replace("_", "!_")


def raise_if_problems(problems):
    if problems:
        raise ValidationError(problems)


def pagination_meta(page, per_page, total):
    pages = max(1, -(-total // per_page))  # ceiling division
    return {"page": page, "per_page": per_page, "total": total, "pages": pages}


def require_slug(slug):
    """Raise NotFound for anything that is not a lowercase slug. MySQL's collation ignores case, so
    without this 'Jason-Duval' would resolve to a second URL for the same record."""
    from werkzeug.exceptions import NotFound
    if not slug or len(slug) > 80 or not SLUG_PATTERN.match(slug):
        raise NotFound("No record with that address.")
    return slug
