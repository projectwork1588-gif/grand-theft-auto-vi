"""Official-source places (content_status 'official') are read-only at EVERY level: the pages, the service, the repository, and each individual SQL statement. A place that an
OFFICIAL character lives at is never deleted either, because the foreign key's SET NULL would rewrite that official character. Direct calls are tested as well as requests.
*_test database only."""
import mysql.connector
import pytest
from werkzeug.datastructures import MultiDict
from werkzeug.exceptions import Conflict, Forbidden

from app.repositories import admin_locations as repo
from app.services import admin_places as service
from tests import account_helpers as h
from tests import admin_helpers as a
from tests.admin_helpers import clean_places, clean_stories  # noqa: F401  (fixtures)

pytestmark = pytest.mark.usefixtures("clean_accounts", "clean_stories", "clean_places")
ADMIN = {"user_id": 1, "role": "admin"}


@pytest.fixture()
def admin(app):
    client, _name = a.admin_client(app)
    return client


@pytest.fixture()
def official():
    slug = a.make_place(status="official")
    a.make_resident(slug)                                  # even a demo resident does not make an official place editable
    story = a.make_story()
    a.link_story_to_place(story, slug)
    return slug


def valid_fields(status="demo"):
    return {"slug": None, "region_id": 1, "name": "TT Replacement " + a.new_slug(), "location_type": "venue", "summary": "s", "description": "s", "content_status": status,
            "source_url": None, "source_note": None}


# ------------------------------------------------------------------ an official place, through the pages
def test_the_pages_refuse_to_edit_or_delete_an_official_place(admin, official):
    before = a.place_snapshot(official)
    assert admin.get(f"/admin/places/{official}/edit").status_code == 403
    assert admin.get(f"/admin/places/{official}/delete").status_code == 403
    assert a.post(admin, f"/admin/places/{official}/edit", a.place_form(name="TT Hijack " + a.new_slug()), token_from="/admin/places/new").status_code == 403
    assert a.post(admin, f"/admin/places/{official}/delete", {}, token_from="/admin/places/new").status_code == 403
    assert a.place_snapshot(official) == before


def test_a_form_can_not_create_an_official_place(admin):
    count = a.count_places()
    response = a.post(admin, "/admin/places/new", a.place_form(content_status="official", source_url="https://www.rockstargames.com/VI"), token_from="/admin/places/new")
    assert response.status_code == 400 and "cannot be created or changed here" in response.get_data(as_text=True)
    assert a.count_places() == count


def test_a_form_can_not_promote_a_place_to_official(admin):
    slug = a.make_place()
    before = a.place_snapshot(slug)
    response = a.post(admin, f"/admin/places/{slug}/edit", a.place_form(content_status="official"), token_from="/admin/places/new")
    assert response.status_code == 400
    assert a.place_snapshot(slug) == before and a.place_row(slug)["content_status"] == "demo"


def test_the_list_marks_official_places_read_only(admin, official):
    page = admin.get("/admin/places?status=official&per_page=50").get_data(as_text=True)
    assert f"/locations/{official}" in page and "Read-only (official)" in page
    assert f"/admin/places/{official}/edit" not in page


# ------------------------------------------------------------------ through the service (a direct call, no request)
def test_the_service_refuses_an_official_place(app, official):
    before = a.place_snapshot(official)
    form = MultiDict(a.place_form())
    with app.test_request_context():
        with pytest.raises(Forbidden):
            service.load_for_edit(official)
        with pytest.raises(Forbidden):
            service.load_for_delete(official)
        with pytest.raises(Forbidden):
            service.update(official, form, ADMIN)
        with pytest.raises(Forbidden):
            service.delete(official, ADMIN)
    assert a.place_snapshot(official) == before


# ------------------------------------------------------------------ through the repository (a direct call, no service, no request)
def test_the_repository_refuses_to_write_an_official_place(app, official):
    before = a.place_snapshot(official)
    with app.app_context():
        with pytest.raises(repo.NotEditable):
            repo.update_place(official, valid_fields())
        with pytest.raises(repo.NotEditable):
            repo.delete_place(official)
    assert a.place_snapshot(official) == before


def test_the_repository_refuses_an_official_status_on_create_and_on_update(app):
    slug = a.make_place()
    before, count = a.place_snapshot(slug), a.count_places()
    with app.app_context():
        with pytest.raises(ValueError):
            repo.create_place(dict(valid_fields("official"), slug="tt-official-attempt", source_url="https://www.rockstargames.com/VI"))
        with pytest.raises(ValueError):
            repo.update_place(slug, valid_fields("official"))
    assert a.count_places() == count and a.place_snapshot(slug) == before


def test_each_statement_is_guarded_even_when_the_row_lock_check_is_bypassed(app, official, monkeypatch):
    """Defence in depth: replace the lock check by one that waves everything through. The UPDATE and the DELETE each carry the writable condition themselves, so the
    official place is still unchanged and the delete reports that it removed nothing and rolls back."""
    before = a.place_snapshot(official)
    monkeypatch.setattr(repo, "_lock_editable", lambda cursor, slug: cursor.execute("SELECT location_id FROM locations WHERE slug = %s", (slug,)) or cursor.fetchone()["location_id"])
    with app.app_context():
        repo.update_place(official, valid_fields())
        assert a.place_snapshot(official) == before
        with pytest.raises(repo.NotEditable):
            repo.delete_place(official)
    assert a.place_snapshot(official) == before


def test_the_database_still_refuses_an_official_place_without_a_source(app):
    with pytest.raises(mysql.connector.Error):
        h.execute("INSERT INTO locations (region_id, slug, name, location_type, summary, description, content_status, source_url) SELECT region_id, 'tt-no-source', 'TT No Source', 'venue', 's', 's', 'official', NULL FROM regions LIMIT 1")


# ------------------------------------------------------------------ a place an official character lives at
def official_home():
    slug = a.make_place(region=a.REGIONS[0])
    character = a.make_resident(slug, status="official")
    return slug, character


def test_the_delete_page_says_it_is_blocked_and_offers_no_delete_button(admin):
    slug, _character = official_home()
    page = admin.get(f"/admin/places/{slug}/delete").get_data(as_text=True)
    assert admin.get(f"/admin/places/{slug}/delete").status_code == 200
    assert "cannot be deleted" in page and "official record" in page and "Delete this place" not in page
    assert 'class="btn adm-danger"' not in page


def test_the_post_is_refused_with_409_and_nothing_changes(admin):
    slug, character = official_home()
    before = a.place_snapshot(slug)
    response = a.post(admin, f"/admin/places/{slug}/delete", {}, token_from="/admin/places/new")
    assert response.status_code == 409 and "official" in response.get_data(as_text=True)
    assert a.place_snapshot(slug) == before and before["residents"] == [(character, "official")]


def test_one_official_resident_among_demo_ones_still_blocks_the_delete(admin):
    slug, official_character = official_home()
    a.make_resident(slug)
    a.make_resident(slug, status="fan")
    before = a.place_snapshot(slug)
    assert a.post(admin, f"/admin/places/{slug}/delete", {}, token_from="/admin/places/new").status_code == 409
    assert a.place_snapshot(slug) == before and len(before["residents"]) == 3


def test_only_fan_and_demo_residents_do_not_block_and_keep_their_characters(admin):
    slug = a.make_place()
    demo, fan = a.make_resident(slug), a.make_resident(slug, status="fan")
    assert a.post(admin, f"/admin/places/{slug}/delete", {}, token_from="/admin/places/new").status_code == 303
    rows = h.rows("SELECT slug, home_location_id, content_status FROM characters WHERE slug IN (%s, %s)", (demo, fan))
    assert len(rows) == 2 and all(r["home_location_id"] is None for r in rows)


def test_the_service_and_the_repository_refuse_too(app):
    slug, character = official_home()
    before = a.place_snapshot(slug)
    with app.test_request_context():
        with pytest.raises(Conflict):
            service.delete(slug, ADMIN)
    with app.app_context():
        with pytest.raises(repo.InUseByOfficial):
            repo.delete_place(slug)
    assert a.place_snapshot(slug) == before


def test_the_delete_statement_itself_refuses_when_the_resident_check_is_bypassed(app, monkeypatch):
    """Defence in depth: let the Python check treat 'official' as writable. The DELETE's own NOT EXISTS still stops it, reports that nothing was removed and rolls back, so the
    official character keeps its home."""
    slug, character = official_home()
    before = a.place_snapshot(slug)
    monkeypatch.setattr(repo, "WRITABLE_STATUSES", ("fan", "demo", "official"))
    with app.app_context():
        with pytest.raises(repo.NotEditable):
            repo.delete_place(slug)
    assert a.place_snapshot(slug) == before
    assert h.rows("SELECT home_location_id FROM characters WHERE slug = %s", (character,))[0]["home_location_id"] == before["row"]["location_id"]
