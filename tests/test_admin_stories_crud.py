"""Create, read, update and delete Stories as an administrator, with their character, vehicle and place links, and what each one does to the database and to the
public pages. Every story here is the test's own ('tt-' slug); the seeded stories are never changed. Rows are written to the *_test database only."""
import pytest

from tests import account_helpers as h
from tests import admin_helpers as a
from tests.admin_helpers import clean_stories  # noqa: F401  (a fixture)

pytestmark = pytest.mark.usefixtures("clean_accounts", "clean_stories")


@pytest.fixture()
def admin(app):
    client, name = a.admin_client(app)
    return client


# ------------------------------------------------------------------ create
def test_create_stores_the_story_and_exactly_the_ticked_links(admin):
    data = a.with_links(a.story_form(), characters=a.CHARACTERS, vehicles=a.VEHICLES[:1], places=a.PLACES, primary=a.PLACES[1])
    response = a.post(admin, "/admin/stories/new", data)
    assert response.status_code == 303
    row = a.story_row(data["slug"])
    assert row and row["title"] == data["title"] and row["content_status"] == "demo" and row["mission_type"] == "side"
    links = a.links_of(data["slug"])
    assert links["characters"] == sorted((c, f"Role of {c}") for c in a.CHARACTERS)
    assert links["vehicles"] == [(a.VEHICLES[0], f"Use of {a.VEHICLES[0]}")]
    assert links["locations"] == sorted([(a.PLACES[0], False), (a.PLACES[1], True)])


def test_create_with_no_links_is_allowed(admin):
    data = a.story_form()
    assert a.post(admin, "/admin/stories/new", data).status_code == 303
    assert a.links_of(data["slug"]) == {"characters": [], "vehicles": [], "locations": []}


def test_an_empty_slug_is_made_from_the_title(admin):
    data = a.story_form(slug="", title="TT The Quiet Water")
    assert a.post(admin, "/admin/stories/new", data).status_code == 303
    row = h.rows("SELECT slug FROM missions WHERE title = %s", ("TT The Quiet Water",))[0]
    assert row["slug"] == "tt-the-quiet-water" and a.story_row("tt-the-quiet-water") is not None


def test_a_created_story_is_on_the_public_pages(admin, app):
    data = a.with_links(a.story_form(), characters=a.CHARACTERS[:1])
    a.post(admin, "/admin/stories/new", data)
    public = app.test_client()
    page = public.get(f"/missions/{data['slug']}")
    assert page.status_code == 200 and data["title"] in page.get_data(as_text=True)
    assert data["title"] in public.get(f"/api/v1/missions/{data['slug']}").get_data(as_text=True)


def test_the_create_form_offers_every_character_vehicle_and_place_as_plain_form_controls(admin):
    page = admin.get("/admin/stories/new").get_data(as_text=True)
    for slug in (a.CHARACTERS[0], a.VEHICLES[0], a.PLACES[0]):
        assert f'value="{slug}"' in page
    assert 'type="checkbox"' in page and 'name="primary_location"' in page
    assert 'value="official"' not in page                                   # the label choice never offers 'official'


# ------------------------------------------------------------------ read: the list
def test_the_list_shows_stories_with_edit_and_delete_for_writable_ones_only(admin):
    mine = a.make_story(title="TT Listed Mine " + a.new_slug())
    official = a.make_story(status="official", title="TT Listed Official " + a.new_slug())
    page = admin.get("/admin/stories?q=TT+Listed&per_page=50").get_data(as_text=True)
    assert f"/admin/stories/{mine}/edit" in page and f"/admin/stories/{mine}/delete" in page
    assert f"/admin/stories/{official}/edit" not in page and f"/admin/stories/{official}/delete" not in page
    assert "Read-only (official)" in page


def test_the_list_filters_sorts_and_paginates(admin):
    stamp = a.new_slug()
    titles = [f"TT Page {stamp} {letter}" for letter in "ABC"]
    for letter, title in zip("ABC", titles):
        a.make_story(title=title)
    base = f"/admin/stories?q={stamp}"
    asc = admin.get(base + "&sort=title_asc&per_page=2").get_data(as_text=True)
    assert titles[0] in asc and titles[1] in asc and titles[2] not in asc
    page2 = admin.get(base + "&sort=title_asc&per_page=2&page=2").get_data(as_text=True)
    assert titles[2] in page2 and titles[0] not in page2
    desc = admin.get(base + "&sort=title_desc&per_page=3").get_data(as_text=True)
    assert desc.index(titles[2]) < desc.index(titles[0])
    assert titles[0] in admin.get(base + "&status=demo").get_data(as_text=True)
    assert titles[0] not in admin.get(base + "&status=fan").get_data(as_text=True)
    assert admin.get("/admin/stories?sort=nonsense").status_code == 400


# ------------------------------------------------------------------ update
def test_update_changes_the_fields_and_replaces_the_links(admin):
    slug = a.make_story(characters=a.CHARACTERS[:1], vehicles=a.VEHICLES[:1], places=a.PLACES[:1], primary=a.PLACES[0])
    edit = a.with_links(a.story_form(title="TT Renamed " + a.new_slug(), summary="New summary", synopsis="New synopsis", mission_type="heist", content_status="fan",
                                     source_url="https://example.org/source", source_note="a note"),
                        characters=a.CHARACTERS[1:], places=a.PLACES, primary=a.PLACES[1])
    response = a.post(admin, f"/admin/stories/{slug}/edit", edit, token_from=f"/admin/stories/{slug}/edit")
    assert response.status_code == 303
    row = a.story_row(slug)
    assert (row["title"], row["summary"], row["synopsis"], row["mission_type"], row["content_status"], row["source_url"], row["source_note"]) == (
        edit["title"], "New summary", "New synopsis", "heist", "fan", "https://example.org/source", "a note")
    links = a.links_of(slug)
    assert links["characters"] == [(a.CHARACTERS[1], f"Role of {a.CHARACTERS[1]}")]      # the old character is gone, the new one is there
    assert links["vehicles"] == []                                                       # unticked: removed
    assert links["locations"] == sorted([(a.PLACES[0], False), (a.PLACES[1], True)])


def test_the_slug_cannot_be_changed_by_an_edit(admin):
    slug = a.make_story()
    edit = a.story_form(slug="tt-a-different-address")
    a.post(admin, f"/admin/stories/{slug}/edit", edit, token_from=f"/admin/stories/{slug}/edit")
    assert a.story_row(slug) is not None and a.story_row("tt-a-different-address") is None


def test_the_edit_form_shows_the_current_values_and_ticks(admin):
    slug = a.make_story(characters=a.CHARACTERS[:1], places=a.PLACES[:1], primary=a.PLACES[0], title="TT Prefilled " + a.new_slug())
    page = admin.get(f"/admin/stories/{slug}/edit").get_data(as_text=True)
    assert "TT Prefilled" in page and f"/missions/{slug}" in page
    assert f'id="characters__{a.CHARACTERS[0]}" name="characters" value="{a.CHARACTERS[0]}" checked' in page
    assert f'<option value="{a.PLACES[0]}" selected>' in page                      # the main place is the selected option of the 'Main place' list


# ------------------------------------------------------------------ delete
def test_the_delete_page_counts_exactly_what_would_go(admin, app):
    slug = a.make_story(characters=a.CHARACTERS, vehicles=a.VEHICLES[:1], places=a.PLACES[:1], primary=a.PLACES[0])
    user_client, name = h.signed_in_client(app)
    h.execute("INSERT INTO favourite_missions (user_id, mission_id) SELECT u.user_id, m.mission_id FROM users u, missions m WHERE u.username = %s AND m.slug = %s", (name, slug))
    page = admin.get(f"/admin/stories/{slug}/delete").get_data(as_text=True)
    assert "2 character links" in page and "1 vehicle link" in page and "1 place link" in page and "1 saved favourite" in page
    assert a.story_row(slug) is not None                                    # looking at the page deleted nothing


def test_a_get_never_deletes_and_the_post_deletes_with_its_cascade_only(admin, app):
    doomed = a.make_story(characters=a.CHARACTERS, vehicles=a.VEHICLES[:1], places=a.PLACES[:1], primary=a.PLACES[0])
    keeper = a.make_story(characters=a.CHARACTERS[:1])
    user_client, name = h.signed_in_client(app)
    for slug in (doomed, keeper):
        h.execute("INSERT INTO favourite_missions (user_id, mission_id) SELECT u.user_id, m.mission_id FROM users u, missions m WHERE u.username = %s AND m.slug = %s", (name, slug))
    kept = a.snapshot(keeper)
    admin.get(f"/admin/stories/{doomed}/delete")
    assert a.story_row(doomed) is not None
    response = a.post(admin, f"/admin/stories/{doomed}/delete", {}, token_from=f"/admin/stories/{doomed}/delete")
    assert response.status_code == 303
    assert a.story_row(doomed) is None and a.links_of(doomed) == {"characters": [], "vehicles": [], "locations": []}
    assert a.snapshot(keeper) == kept                                       # another story, its links and its favourite are untouched
    assert h.rows("SELECT COUNT(*) AS n FROM characters WHERE slug = %s", (a.CHARACTERS[0],))[0]["n"] == 1      # the linked records themselves are not touched
    assert app.test_client().get(f"/missions/{doomed}").status_code == 404


def test_deleting_an_unknown_story_is_404(admin):
    assert a.post(admin, "/admin/stories/tt-nothing-here/delete", {}, token_from="/admin/stories/new").status_code == 404
