"""Place writes are atomic and the database's own rules (UNIQUE, FOREIGN KEY, SET NULL, CASCADE) are handled cleanly: a failure at ANY step leaves the place, its residents,
its story links, its favourites and its media links exactly as they were. Each test lets a real step run and then fails the next one, and compares a before/after snapshot.
*_test database only."""
import pytest

from app import config, create_app
from app.repositories import admin_locations as repo
from tests import account_helpers as h
from tests import admin_helpers as a
from tests.admin_helpers import clean_places, clean_stories  # noqa: F401  (fixtures)

pytestmark = pytest.mark.usefixtures("clean_accounts", "clean_stories", "clean_places")
MISSING_REGION = 60000                  # inside the SMALLINT UNSIGNED range of locations.region_id, and no region has it: a real race produces a foreign-key error (1452), not an out-of-range one


@pytest.fixture()
def admin(app):
    client, _name = a.admin_client(app)
    return client


def post(admin, path, data):
    return a.post(admin, path, data, token_from="/admin/places/new")


def fail_before_commit(monkeypatch):
    """Replace the last step of every write with one that fails: everything the transaction did before it must be undone."""
    monkeypatch.setattr(repo, "_before_commit", lambda cursor: (_ for _ in ()).throw(RuntimeError("injected failure")))


def busy_place(app):
    slug = a.make_place(region=a.REGIONS[0])
    a.make_resident(slug)
    a.make_resident(slug, status="fan")
    story = a.make_story()
    a.link_story_to_place(story, slug, primary=True)
    _c, name = h.signed_in_client(app)
    a.save_place_as(name, slug)
    a.link_media_to_place(slug)
    return slug


# ------------------------------------------------------------------ the three writes, each failing at its last step
def test_a_failure_while_creating_leaves_no_place(admin, monkeypatch):
    before = a.count_places()
    fail_before_commit(monkeypatch)
    data = a.place_form()
    assert post(admin, "/admin/places/new", data).status_code == 500
    assert a.place_row(data["slug"]) is None and a.count_places() == before


def test_a_failure_while_updating_leaves_the_place_exactly_as_it_was(admin, app, monkeypatch):
    slug = busy_place(app)
    before = a.place_snapshot(slug)
    fail_before_commit(monkeypatch)
    edit = a.place_form(name="TT Changed " + a.new_slug(), region=a.REGIONS[1], location_type="wilderness", content_status="fan", summary="changed", description="changed")
    assert post(admin, f"/admin/places/{slug}/edit", edit).status_code == 500
    assert a.place_snapshot(slug) == before


def test_a_failure_while_deleting_keeps_the_place_its_residents_homes_and_every_link(admin, app, monkeypatch):
    slug = busy_place(app)
    before = a.place_snapshot(slug)
    assert len(before["residents"]) == 2 and before["story_links"] and before["favourites"] == 1 and before["media_links"] == 1
    fail_before_commit(monkeypatch)
    assert post(admin, f"/admin/places/{slug}/delete", {}).status_code == 500
    assert a.place_snapshot(slug) == before                                     # the SET NULL and the CASCADEs that had already happened inside the transaction were undone


# ------------------------------------------------------------------ the database's own refusals
def test_a_duplicate_name_in_the_same_region_is_a_field_error_and_changes_nothing(admin):
    first = a.make_place(region=a.REGIONS[0], name="TT Twin " + a.new_slug())
    name = a.place_row(first)["name"]
    before, count = a.place_snapshot(first), a.count_places()
    response = post(admin, "/admin/places/new", a.place_form(name=name, region=a.REGIONS[0]))
    assert response.status_code == 409 and "A place with that name already exists in that region." in response.get_data(as_text=True)
    assert a.count_places() == count and a.place_snapshot(first) == before


def test_the_same_name_in_a_different_region_is_allowed(admin):
    """The key is (region, name), not the name alone: this is the composite UNIQUE key at work."""
    first = a.make_place(region=a.REGIONS[0], name="TT Shared Name " + a.new_slug())
    name = a.place_row(first)["name"]
    other = a.place_form(name=name, region=a.REGIONS[1])
    assert post(admin, "/admin/places/new", other).status_code == 303
    assert a.place_row(other["slug"])["region"] == a.REGIONS[1]


def test_a_duplicate_slug_is_a_field_error_and_changes_nothing(admin):
    first = a.make_place()
    count = a.count_places()
    response = post(admin, "/admin/places/new", a.place_form(slug=first))
    assert response.status_code == 409 and "A place with that address already exists." in response.get_data(as_text=True)
    assert a.count_places() == count


def test_renaming_to_a_taken_name_in_the_same_region_is_refused_and_changes_nothing(admin, app):
    other = a.make_place(region=a.REGIONS[0], name="TT Taken " + a.new_slug())
    mine = busy_place(app)
    before = a.place_snapshot(mine)
    response = post(admin, f"/admin/places/{mine}/edit", a.place_form(name=a.place_row(other)["name"], region=a.REGIONS[0]))
    assert response.status_code == 409
    assert a.place_snapshot(mine) == before


def test_moving_a_place_into_a_region_that_already_has_that_name_is_refused(admin):
    name = "TT Collide " + a.new_slug()
    a.make_place(region=a.REGIONS[1], name=name)
    mine = a.make_place(region=a.REGIONS[0], name=name)
    before = a.place_snapshot(mine)
    response = post(admin, f"/admin/places/{mine}/edit", a.place_form(name=name, region=a.REGIONS[1]))
    assert response.status_code == 409 and "already exists in that region" in response.get_data(as_text=True)
    assert a.place_snapshot(mine) == before and a.place_row(mine)["region"] == a.REGIONS[0]


def test_a_region_removed_after_the_form_was_checked_rolls_the_create_back(admin, monkeypatch):
    """The region is valid when it is looked up and gone when the place is written (the foreign key refuses it)."""
    from app.services import admin_places as service
    monkeypatch.setattr(service.repo, "region_id", lambda slug: MISSING_REGION)
    count = a.count_places()
    data = a.place_form()
    response = post(admin, "/admin/places/new", data)
    assert response.status_code == 409 and "no longer exists" in response.get_data(as_text=True)
    assert a.place_row(data["slug"]) is None and a.count_places() == count


def test_a_region_removed_during_an_update_leaves_the_place_as_it_was(admin, app, monkeypatch):
    from app.services import admin_places as service
    slug = busy_place(app)
    before = a.place_snapshot(slug)
    monkeypatch.setattr(service.repo, "region_id", lambda slug_: MISSING_REGION)
    response = post(admin, f"/admin/places/{slug}/edit", a.place_form(name="TT Moving " + a.new_slug(), region=a.REGIONS[1]))
    assert response.status_code == 409
    assert a.place_snapshot(slug) == before


def test_the_region_restrict_rule_still_protects_regions_that_have_places(app):
    """The web app never deletes a region, and the database would refuse: RESTRICT on locations.region_id."""
    import mysql.connector
    a.make_place(region=a.REGIONS[0])
    with pytest.raises(mysql.connector.Error):
        h.execute("DELETE FROM regions WHERE slug = %s", (a.REGIONS[0],))
    assert h.rows("SELECT COUNT(*) AS n FROM regions WHERE slug = %s", (a.REGIONS[0],))[0]["n"] == 1


# ------------------------------------------------------------------ the connection goes back to the pool
def test_after_a_failed_write_the_connection_is_back_in_a_pool_of_one(monkeypatch):
    monkeypatch.setattr(config.TestingConfig, "DB_POOL_SIZE", 1)
    one = create_app("testing")
    client, _name = a.admin_client(one)
    fail_before_commit(monkeypatch)
    assert a.post(client, "/admin/places/new", a.place_form(), token_from="/admin/places/new").status_code == 500
    monkeypatch.undo()
    pool = one.extensions["db_pool"]
    connection = pool.get_connection()                         # raises PoolError if the failed request still held the only connection
    connection.close()
    assert client.get("/admin/places").status_code == 200


def test_every_place_write_runs_in_its_own_transaction_block(app):
    """A nested transaction() is refused, so a write function that opened a second block would fail: they must not."""
    from app.db import TransactionError, transaction
    with app.app_context():
        with transaction():
            with pytest.raises(TransactionError):
                repo.create_place(dict(a.place_form(), region_id=1, name="x"))
