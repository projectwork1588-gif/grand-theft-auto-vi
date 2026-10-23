"""The routes and the seed numbers the documents state must be the real ones. docs/ROUTES.md and the README's page table are compared with the application's own URL
map (every route is documented, nothing documented is missing, and the two redirects are redirects with the stated status), and the seed figures in docs/DATABASE.md are
compared with what database/seed.sql really loads into the *_test database (the `app` fixture rebuilds it from schema.sql and seed.sql, as for every test). Nothing is
written: counts are read-only queries on the test database."""
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
ROUTES_DOC = (ROOT / "docs" / "ROUTES.md").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
DATABASE_DOC = (ROOT / "docs" / "DATABASE.md").read_text(encoding="utf-8")
API_PREFIX = "/api/v1"
MEDIA_CLIPS = "/media/clips/<name>.mp4"          # how the documents write the one route /media/<path:filename>


def real_rules(app):
    return sorted({rule.rule for rule in app.url_map.iter_rules() if rule.endpoint != "static"})


def documented_paths(markdown_section):
    """Every backticked address in a section: `/x`, `POST /x`, and the comma lists inside one pair of backticks are split apart."""
    found = set()
    for token in re.findall(r"`([^`]+)`", markdown_section):
        for part in token.split(","):
            part = re.split(r"[?#]", re.sub(r"^(GET|POST)\s+", "", part.strip()))[0]      # the path only: not a query string or an anchor
            if part.startswith("/"):
                found.add(part)
    return found


def section(doc, heading):
    match = re.search(rf"^### {re.escape(heading)}[^\n]*\n(.*?)(?=^##+ |\Z)", doc, flags=re.S | re.M)
    assert match, heading
    return match.group(1)


# ------------------------------------------------------------------ ROUTES.md against the URL map
def test_every_page_route_is_documented_and_nothing_documented_is_missing(app):
    pages = {rule for rule in real_rules(app) if not rule.startswith(API_PREFIX + "/")}
    documented = documented_paths(section(ROUTES_DOC, "Pages (HTML, server-rendered from MySQL)"))
    documented = {"/media/<path:filename>" if path == MEDIA_CLIPS else path for path in documented}
    assert pages - documented == set(), "routes missing from docs/ROUTES.md"
    assert documented - pages == set(), "docs/ROUTES.md documents routes that do not exist"


def test_every_api_route_is_documented_and_nothing_documented_is_missing(app):
    api = {rule[len(API_PREFIX):] for rule in real_rules(app) if rule.startswith(API_PREFIX + "/")}
    documented = documented_paths(section(ROUTES_DOC, "JSON API (`/api/v1`)"))
    assert api - documented == set(), "API routes missing from docs/ROUTES.md"
    assert documented - api == set(), "docs/ROUTES.md documents API routes that do not exist"


def test_the_two_documented_redirects_are_redirects_with_the_stated_status(client):
    old_places = client.get("/locations")
    assert old_places.status_code == 302 and old_places.headers["Location"].endswith("/music")
    old_garage = client.get("/garage-concept?q=x")
    assert old_garage.status_code == 301 and old_garage.headers["Location"].endswith("/vehicles?q=x")
    assert "Redirect (302) to `/music`" in ROUTES_DOC and "Compatibility redirect** (301) to `/vehicles`" in ROUTES_DOC


def test_the_error_table_lists_every_branded_status():
    table = section(ROUTES_DOC, "Error handling")
    for code in ("400", "403", "404", "405", "413", "429", "500", "503"):
        assert re.search(rf"^\| {code} \|", table, flags=re.M), code


# ------------------------------------------------------------------ the README page table against the URL map
def readme_table_paths():
    table = re.search(r"## What you can do today\n(.*?)\n## ", README, flags=re.S).group(1)
    paths = set()
    for row in table.splitlines():
        cells = [cell.strip() for cell in row.split("|")]
        if len(cells) > 3 and cells[2].startswith("`"):
            paths |= documented_paths(cells[2])
    return paths


def test_every_address_in_the_readme_table_is_a_real_route(app):
    rules = set(real_rules(app))
    for path in readme_table_paths():
        if path == "/api/v1/...":
            assert any(rule.startswith(API_PREFIX + "/") for rule in rules)
        else:
            assert path in rules, f"README lists {path}, which is not a route"


def test_the_readme_describes_places_as_pages_not_as_an_index(app):
    row = next(line for line in README.splitlines() if line.startswith("| Places |"))
    assert "`/locations/<slug>`" in row and "redirects (302) to `/music`" in row and "Searchable" not in row
    assert "/locations" in real_rules(app) and "/locations/<slug>" in real_rules(app)


def test_the_readme_lists_every_document_the_repository_has_for_the_features_it_describes():
    for name in ("ACCOUNTS", "ADMIN", "MUSIC", "MEDIA_SCREENING", "MEDIA_INVENTORY", "ROUTES", "ARCHITECTURE", "DATABASE"):
        assert (ROOT / "docs" / f"{name}.md").exists() and f"docs/{name}.md" in README, name


# ------------------------------------------------------------------ DATABASE.md seed figures against the real seed
@pytest.fixture()
def count(app, app_context):
    from app.db import query_one

    def run(sql):
        return list(query_one(sql).values())[0]
    return run


def seed_row(label):
    return next(line for line in DATABASE_DOC.splitlines() if line.startswith(f"| {label} |"))


def test_the_vehicle_figures_are_the_seeds(count):
    assert count("SELECT COUNT(*) FROM vehicles WHERE content_status = 'official'") == 7
    assert count("SELECT COUNT(*) FROM vehicles WHERE content_status = 'demo'") == 8
    official = next(line for line in DATABASE_DOC.splitlines() if line.startswith("| Vehicles |") and "Grotti Cheetah" in line)
    assert "(7:" in official and "Dinka Enduro Motorcycle" in official and "Crest Kayak" in official
    assert "8 concept vehicles" in DATABASE_DOC


def test_the_character_region_and_relationship_figures_are_the_seeds(count):
    assert count("SELECT COUNT(*) FROM characters WHERE content_status = 'official'") == 8
    assert count("SELECT COUNT(*) FROM characters WHERE content_status = 'demo'") == 3
    assert count("SELECT COUNT(*) FROM regions WHERE content_status = 'official'") == 6
    assert count("SELECT COUNT(*) FROM character_relationships WHERE content_status = 'official'") == 5
    assert count("SELECT COUNT(*) FROM character_relationships WHERE content_status = 'demo'") == 3
    assert "(5; the last from migration 005)" in seed_row("Relationships")


def test_the_media_figures_are_the_seeds(count):
    row = seed_row("Media")
    stated = {   # the phrase DATABASE.md uses -> what the seed really holds
        "206 rows": count("SELECT COUNT(*) FROM media_assets"),
        "3 trailer": count("SELECT COUNT(*) FROM media_assets WHERE media_type = 'trailer'"),
        "11 video": count("SELECT COUNT(*) FROM media_assets WHERE media_type = 'video'"),
        "29 artwork": count("SELECT COUNT(*) FROM media_assets WHERE media_type = 'artwork'"),
        "162 screenshot": count("SELECT COUNT(*) FROM media_assets WHERE media_type = 'screenshot'"),
        "1 wallpaper": count("SELECT COUNT(*) FROM media_assets WHERE media_type = 'wallpaper'"),
        "59 character": count("SELECT COUNT(*) FROM media_characters"),
        "36 region": count("SELECT COUNT(*) FROM media_regions"),
        "21 vehicle": count("SELECT COUNT(*) FROM media_vehicles"),
        "6 collections": count("SELECT COUNT(*) FROM media_collections"),
        "200 ordered items": count("SELECT COUNT(*) FROM media_collection_items"),
    }
    for phrase, actual in stated.items():
        assert actual == int(phrase.split()[0]), f"the seed has {actual} for {phrase!r}"
        assert phrase.replace("6 collections", "Six collections") in row, f"docs/DATABASE.md does not state {phrase!r} in the Media row"


def test_the_music_figures_are_the_seeds(count):
    row = seed_row("Music")
    assert count("SELECT COUNT(*) FROM radio_stations") == 6 and "6 radio stations" in row
    assert count("SELECT COUNT(*) FROM station_preview_tracks") == 18 and "18 preview tracks" in row
    assert count("SELECT COUNT(*) FROM music_releases") == 2 and "2 releases" in row
    assert count("SELECT COUNT(*) FROM music_tracks") == 9 and "9 tracks" in row
