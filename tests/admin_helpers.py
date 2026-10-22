"""Helpers for the admin (Stories) tests. Every database touch goes through tests/account_helpers.py, whose test_connection() proves that the connection it
opened is really on a *_test database. The admin tests never change the seeded stories (other tests in the same session read them): they create their own,
all with a 'tt-' slug, and remove them again."""
import uuid

import pytest

from scripts import make_admin
from tests import account_helpers as h

SEED_STORY = "harbour-lights"                 # a seeded demo story: read-only for these tests
CHARACTERS = ("jason-duval", "lucia-caminos")
VEHICLES = ("grotti-cheetah", "vapid-stanier")
PLACES = ("bayfront-studio-lot", "coral-hook-marina")
LINK_TABLES = ("mission_characters", "mission_vehicles", "mission_locations", "favourite_missions")


def new_slug():
    return "tt-" + uuid.uuid4().hex[:10]


def new_title():
    return "TT story " + uuid.uuid4().hex[:10]


def wipe_test_stories(app):
    assert app.config["DB_CONFIG"].DB_NAME.endswith("_test")
    h.rows("SELECT 1")                                        # opens a connection through the guard, which proves the database is a *_test one
    h.execute("DELETE FROM missions WHERE slug LIKE %s", ("tt-%",))      # the link rows and favourites of those stories cascade


@pytest.fixture()
def clean_stories(app):
    wipe_test_stories(app)
    yield
    wipe_test_stories(app)


def promote(username):
    """Make a test account an administrator with the real bootstrap tool (test database only)."""
    assert make_admin.main(["--test", "--yes", username]) == 0


def admin_client(app):
    client, name = h.signed_in_client(app)
    promote(name)
    return client, name


def story_form(**overrides):
    data = {"title": new_title(), "slug": new_slug(), "mission_type": "side", "content_status": "demo", "summary": "A short test summary.",
            "synopsis": "A test synopsis that is long enough to be a real one.", "source_url": "", "source_note": ""}
    data.update(overrides)
    return data


def with_links(data, characters=(), vehicles=(), places=(), primary=""):
    """Add ticked links (and a note for each character and vehicle) to a form dict."""
    data = dict(data)
    data["characters"] = list(characters)
    data["vehicles"] = list(vehicles)
    data["locations"] = list(places)
    for slug in characters:
        data[f"characters_note__{slug}"] = f"Role of {slug}"
    for slug in vehicles:
        data[f"vehicles_note__{slug}"] = f"Use of {slug}"
    data["primary_location"] = primary
    return data


def post(client, path, data, token_from="/admin/stories/new", **kwargs):
    return h.post(client, path, data, token_from=token_from, **kwargs)


def story_row(slug):
    found = h.rows("SELECT mission_id, slug, title, mission_type, summary, synopsis, content_status, source_url, source_note FROM missions WHERE slug = %s", (slug,))
    return found[0] if found else None


def links_of(slug):
    """Everything linked to a story, as plain sorted lists, for comparing before and after."""
    out = {}
    out["characters"] = sorted((r["slug"], r["role_in_mission"]) for r in h.rows(
        "SELECT c.slug, mc.role_in_mission FROM mission_characters mc JOIN missions m ON m.mission_id = mc.mission_id JOIN characters c ON c.character_id = mc.character_id WHERE m.slug = %s", (slug,)))
    out["vehicles"] = sorted((r["slug"], r["usage_note"]) for r in h.rows(
        "SELECT v.slug, mv.usage_note FROM mission_vehicles mv JOIN missions m ON m.mission_id = mv.mission_id JOIN vehicles v ON v.vehicle_id = mv.vehicle_id WHERE m.slug = %s", (slug,)))
    out["locations"] = sorted((r["slug"], bool(r["is_primary"])) for r in h.rows(
        "SELECT l.slug, ml.is_primary FROM mission_locations ml JOIN missions m ON m.mission_id = ml.mission_id JOIN locations l ON l.location_id = ml.location_id WHERE m.slug = %s", (slug,)))
    return out


def snapshot(slug):
    """The story row, its links and the number of favourites of it: if two snapshots are equal, nothing about the story changed."""
    favourites = h.rows("SELECT COUNT(*) AS n FROM favourite_missions f JOIN missions m ON m.mission_id = f.mission_id WHERE m.slug = %s", (slug,))[0]["n"]
    row = story_row(slug)
    return {"row": row, "links": links_of(slug), "favourites": favourites} if row else None


def count_stories():
    return h.rows("SELECT COUNT(*) AS n FROM missions")[0]["n"]


def make_story(slug=None, status="demo", title=None, characters=(), vehicles=(), places=(), primary=None):
    """Insert a story (and links) straight into the test database, bypassing the admin code. An 'official' one gets the source address its CHECK requires."""
    slug = slug or new_slug()
    title = title or new_title()
    source = "https://www.rockstargames.com/VI" if status == "official" else None
    h.execute("INSERT INTO missions (slug, title, mission_type, summary, synopsis, content_status, source_url) VALUES (%s, %s, 'side', 'summary', 'synopsis', %s, %s)",
              (slug, title, status, source))
    mission_id = h.rows("SELECT mission_id FROM missions WHERE slug = %s", (slug,))[0]["mission_id"]
    for entity in characters:
        h.execute("INSERT INTO mission_characters (mission_id, character_id, role_in_mission) SELECT %s, character_id, 'seed role' FROM characters WHERE slug = %s", (mission_id, entity))
    for entity in vehicles:
        h.execute("INSERT INTO mission_vehicles (mission_id, vehicle_id, usage_note) SELECT %s, vehicle_id, 'seed use' FROM vehicles WHERE slug = %s", (mission_id, entity))
    for entity in places:
        h.execute("INSERT INTO mission_locations (mission_id, location_id, is_primary) SELECT %s, location_id, %s FROM locations WHERE slug = %s", (mission_id, entity == primary, entity))
    return slug
