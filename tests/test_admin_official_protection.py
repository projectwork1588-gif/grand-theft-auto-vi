"""Official-source stories (content_status 'official': Rockstar-sourced, a source address required by the table's own CHECK) are read-only at EVERY level: the
pages, the service, the repository, and each individual SQL statement. Direct calls are tested as well as requests. Rows are written to the *_test database only."""
import mysql.connector
import pytest
from werkzeug.datastructures import MultiDict
from werkzeug.exceptions import Forbidden

from app.repositories import admin_stories as repo
from app.services import admin_stories as service
from tests import account_helpers as h
from tests import admin_helpers as a
from tests.admin_helpers import clean_stories  # noqa: F401  (a fixture)

pytestmark = pytest.mark.usefixtures("clean_accounts", "clean_stories")
ADMIN = {"user_id": 1, "role": "admin"}


@pytest.fixture()
def admin(app):
    client, _name = a.admin_client(app)
    return client


@pytest.fixture()
def official():
    return a.make_story(status="official", characters=a.CHARACTERS, vehicles=a.VEHICLES[:1], places=a.PLACES, primary=a.PLACES[0])


def valid_fields(status="demo"):
    return {"slug": None, "title": "TT Replacement " + a.new_slug(), "mission_type": "heist", "summary": "s", "synopsis": "s", "content_status": status, "source_url": None, "source_note": None}


# ------------------------------------------------------------------ through the pages
def test_the_pages_refuse_to_edit_or_delete_an_official_story(admin, official):
    before = a.snapshot(official)
    assert admin.get(f"/admin/stories/{official}/edit").status_code == 403
    assert admin.get(f"/admin/stories/{official}/delete").status_code == 403
    edit = a.with_links(a.story_form(title="TT Hijack " + a.new_slug()), characters=a.CHARACTERS[:1])
    assert a.post(admin, f"/admin/stories/{official}/edit", edit, token_from="/admin/stories/new").status_code == 403
    assert a.post(admin, f"/admin/stories/{official}/delete", {}, token_from="/admin/stories/new").status_code == 403
    assert a.snapshot(official) == before


def test_a_form_can_not_create_an_official_story(admin):
    count = a.count_stories()
    response = a.post(admin, "/admin/stories/new", a.story_form(content_status="official", source_url="https://www.rockstargames.com/VI"))
    assert response.status_code == 400 and "cannot be created or changed here" in response.get_data(as_text=True)
    assert a.count_stories() == count


def test_a_form_can_not_promote_a_story_to_official(admin):
    slug = a.make_story()
    before = a.snapshot(slug)
    response = a.post(admin, f"/admin/stories/{slug}/edit", a.story_form(content_status="official"), token_from=f"/admin/stories/{slug}/edit")
    assert response.status_code == 400
    assert a.snapshot(slug) == before and a.story_row(slug)["content_status"] == "demo"


# ------------------------------------------------------------------ through the service (a direct call, no request)
def test_the_service_refuses_an_official_story(app, official):
    before = a.snapshot(official)
    form = MultiDict(a.with_links(a.story_form(), characters=a.CHARACTERS[:1]))
    with app.test_request_context():
        with pytest.raises(Forbidden):
            service.load_for_edit(official)
        with pytest.raises(Forbidden):
            service.load_for_delete(official)
        with pytest.raises(Forbidden):
            service.update(official, form, ADMIN)
        with pytest.raises(Forbidden):
            service.delete(official, ADMIN)
    assert a.snapshot(official) == before


# ------------------------------------------------------------------ through the repository (a direct call, no service, no request)
def test_the_repository_refuses_to_write_an_official_story(app, official):
    before = a.snapshot(official)
    with app.app_context():
        with pytest.raises(repo.NotEditable):
            repo.update_story(official, valid_fields(), {"characters": [], "vehicles": [], "locations": []})
        with pytest.raises(repo.NotEditable):
            repo.delete_story(official)
    assert a.snapshot(official) == before


def test_the_repository_refuses_an_official_status_on_create_and_on_update(app):
    slug = a.make_story()
    before, count = a.snapshot(slug), a.count_stories()
    with app.app_context():
        with pytest.raises(ValueError):
            repo.create_story(dict(valid_fields("official"), slug="tt-official-attempt", source_url="https://www.rockstargames.com/VI"), {})
        with pytest.raises(ValueError):
            repo.update_story(slug, valid_fields("official"), {})
    assert a.count_stories() == count and a.snapshot(slug) == before


def test_each_statement_is_guarded_even_when_the_row_lock_check_is_bypassed(app, official, monkeypatch):
    """Defence in depth: replace the lock check by one that waves everything through. The UPDATE, the link DELETEs and the link INSERTs each carry the writable
    condition themselves, so the official story is still unchanged; the DELETE of the story itself reports that it removed nothing and rolls back."""
    before = a.snapshot(official)
    monkeypatch.setattr(repo, "_lock_editable", lambda cursor, slug: cursor.execute("SELECT mission_id FROM missions WHERE slug = %s", (slug,)) or cursor.fetchone()["mission_id"])
    with app.app_context():
        repo.update_story(official, valid_fields(), {"characters": [(1, "forced role")], "vehicles": [], "locations": []})
        assert a.snapshot(official) == before
        with pytest.raises(repo.NotEditable):
            repo.delete_story(official)
    assert a.snapshot(official) == before


def test_the_database_still_refuses_an_official_story_without_a_source(app):
    with pytest.raises(mysql.connector.Error):
        h.execute("INSERT INTO missions (slug, title, mission_type, summary, synopsis, content_status, source_url) VALUES ('tt-no-source', 'TT No Source', 'side', 's', 's', 'official', NULL)")


# ------------------------------------------------------------------ the list
def test_the_list_marks_official_stories_read_only(admin, official):
    page = admin.get("/admin/stories?status=official&per_page=50").get_data(as_text=True)
    assert f"/missions/{official}" in page and "Read-only (official)" in page
    assert f"/admin/stories/{official}/edit" not in page
