"""Admin writes are atomic: a failure at ANY step leaves the database exactly as it was. Each test lets a real step run against the *_test database and then fails
the next one, and compares a before/after snapshot of the story, its links and the favourites of it. Rows are written to the *_test database only."""
import mysql.connector
import pytest

from app import config, create_app
from app.repositories import admin_stories as repo
from tests import account_helpers as h
from tests import admin_helpers as a
from tests.admin_helpers import clean_stories  # noqa: F401  (a fixture)

pytestmark = pytest.mark.usefixtures("clean_accounts", "clean_stories")


@pytest.fixture()
def admin(app):
    client, _name = a.admin_client(app)
    return client


def fail_after(monkeypatch, step, keep_first_link_only=False):
    """Replace a repository step with one that does the real work (or only part of it) and then fails."""
    real = getattr(repo, step)

    def failing(cursor, *args, **kwargs):
        if keep_first_link_only:
            mission_id, links = args
            first = {kind: items[:1] for kind, items in links.items() if items}
            real(cursor, mission_id, first)
        else:
            real(cursor, *args, **kwargs)
        raise RuntimeError("injected failure")
    monkeypatch.setattr(repo, step, failing)


def noisy_story():
    return a.make_story(characters=a.CHARACTERS, vehicles=a.VEHICLES, places=a.PLACES, primary=a.PLACES[0])


def full_edit():
    return a.with_links(a.story_form(title="TT Changed " + a.new_slug(), summary="changed", synopsis="changed", mission_type="heist", content_status="fan"),
                        characters=a.CHARACTERS[:1], vehicles=a.VEHICLES[1:], places=a.PLACES[1:], primary=a.PLACES[1])


# ------------------------------------------------------------------ create
@pytest.mark.parametrize("step, partial", [("_insert_links", False), ("_insert_links", True), ("_before_commit", False)])
def test_a_failure_while_creating_leaves_no_story_and_no_links(admin, monkeypatch, step, partial):
    before = a.count_stories()
    fail_after(monkeypatch, step, keep_first_link_only=partial)
    data = a.with_links(a.story_form(), characters=a.CHARACTERS, vehicles=a.VEHICLES, places=a.PLACES, primary=a.PLACES[0])
    response = a.post(admin, "/admin/stories/new", data)
    assert response.status_code == 500
    assert a.story_row(data["slug"]) is None and a.count_stories() == before
    assert h.rows("SELECT COUNT(*) AS n FROM mission_characters mc LEFT JOIN missions m ON m.mission_id = mc.mission_id WHERE m.mission_id IS NULL")[0]["n"] == 0


# ------------------------------------------------------------------ update
@pytest.mark.parametrize("step, partial", [("_delete_links", False), ("_insert_links", False), ("_insert_links", True), ("_before_commit", False)])
def test_a_failure_while_updating_leaves_the_story_exactly_as_it_was(admin, monkeypatch, step, partial):
    slug = noisy_story()
    before = a.snapshot(slug)
    fail_after(monkeypatch, step, keep_first_link_only=partial)
    response = a.post(admin, f"/admin/stories/{slug}/edit", full_edit(), token_from=f"/admin/stories/{slug}/edit")
    assert response.status_code == 500
    assert a.snapshot(slug) == before


# ------------------------------------------------------------------ delete
def test_a_failure_while_deleting_keeps_the_story_its_links_and_its_favourites(admin, app, monkeypatch):
    slug = noisy_story()
    _client, name = h.signed_in_client(app)
    h.execute("INSERT INTO favourite_missions (user_id, mission_id) SELECT u.user_id, m.mission_id FROM users u, missions m WHERE u.username = %s AND m.slug = %s", (name, slug))
    before = a.snapshot(slug)
    assert before["favourites"] == 1
    monkeypatch.setattr(repo, "_before_commit", lambda cursor: (_ for _ in ()).throw(RuntimeError("injected failure")))
    response = a.post(admin, f"/admin/stories/{slug}/delete", {}, token_from=f"/admin/stories/{slug}/delete")
    assert response.status_code == 500
    assert a.snapshot(slug) == before


# ------------------------------------------------------------------ the database's own refusals
def test_a_duplicate_title_is_a_field_error_and_changes_nothing(admin):
    first = a.make_story(title="TT Duplicate " + a.new_slug())
    title = a.story_row(first)["title"]
    before, count = a.snapshot(first), a.count_stories()
    response = a.post(admin, "/admin/stories/new", a.with_links(a.story_form(title=title), characters=a.CHARACTERS))
    assert response.status_code == 409 and "A story with that title already exists." in response.get_data(as_text=True)
    assert a.count_stories() == count and a.snapshot(first) == before


def test_a_duplicate_slug_is_a_field_error_and_changes_nothing(admin):
    first = a.make_story()
    count = a.count_stories()
    response = a.post(admin, "/admin/stories/new", a.story_form(slug=first))
    assert response.status_code == 409 and "A story with that address already exists." in response.get_data(as_text=True)
    assert a.count_stories() == count


def test_renaming_a_story_to_a_taken_title_is_refused_and_changes_nothing(admin):
    other = a.make_story(title="TT Taken " + a.new_slug())
    mine = noisy_story()
    before = a.snapshot(mine)
    response = a.post(admin, f"/admin/stories/{mine}/edit", full_edit() | {"title": a.story_row(other)["title"]}, token_from=f"/admin/stories/{mine}/edit")
    assert response.status_code == 409
    assert a.snapshot(mine) == before


def test_a_record_removed_after_the_form_was_checked_rolls_the_whole_create_back(admin, monkeypatch):
    """The slug is valid when it is checked and gone when the link is written (the foreign key refuses it): the story insert is rolled back too."""
    from app.services import admin_stories as service
    real = service.repo.ids_by_slug
    monkeypatch.setattr(service.repo, "ids_by_slug", lambda kind, slugs: {s: 99999999 for s in real(kind, slugs)} if kind == "characters" else real(kind, slugs))
    count = a.count_stories()
    data = a.with_links(a.story_form(), characters=a.CHARACTERS[:1])
    response = a.post(admin, "/admin/stories/new", data)
    assert response.status_code == 409 and "no longer exists" in response.get_data(as_text=True)
    assert a.story_row(data["slug"]) is None and a.count_stories() == count


def test_a_record_removed_during_an_update_restores_the_links_that_were_just_deleted(admin, monkeypatch):
    from app.services import admin_stories as service
    slug = noisy_story()
    before = a.snapshot(slug)
    real = service.repo.ids_by_slug
    monkeypatch.setattr(service.repo, "ids_by_slug", lambda kind, slugs: {s: 99999999 for s in real(kind, slugs)} if kind == "vehicles" else real(kind, slugs))
    response = a.post(admin, f"/admin/stories/{slug}/edit", a.with_links(a.story_form(), characters=a.CHARACTERS[:1], vehicles=a.VEHICLES[:1]), token_from=f"/admin/stories/{slug}/edit")
    assert response.status_code == 409
    assert a.snapshot(slug) == before                            # the old links were deleted inside the transaction and came back with the rollback


# ------------------------------------------------------------------ the connection goes back to the pool
def test_after_a_failed_write_the_connection_is_back_in_a_pool_of_one(monkeypatch):
    monkeypatch.setattr(config.TestingConfig, "DB_POOL_SIZE", 1)
    one = create_app("testing")
    client, _name = a.admin_client(one)
    fail_after(monkeypatch, "_before_commit")
    assert a.post(client, "/admin/stories/new", a.story_form()).status_code == 500
    monkeypatch.undo()
    pool = one.extensions["db_pool"]
    connection = pool.get_connection()                         # raises PoolError if the failed request still held the only connection
    connection.close()
    assert client.get("/admin/stories").status_code == 200


def test_the_repository_functions_run_each_write_in_one_transaction_block(app):
    """A nested transaction() is refused, so a write function that opened a second block would fail: they must not."""
    from app.db import TransactionError, transaction
    with app.app_context():
        with transaction():
            with pytest.raises(TransactionError):
                repo.create_story(a.story_form(), {})
