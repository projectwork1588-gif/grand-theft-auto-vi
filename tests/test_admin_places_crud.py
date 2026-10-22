"""Create, read, update and delete Places as an administrator, with the region they belong to, and what each one does to the database and to the public pages. The delete
tests check the CONFIRMATION PAGE's numbers against the database before the delete and every consequence of it after (residents' homes cleared, link rows, favourites and
media links removed, nothing else touched). Every place here is the test's own ('tt-' slug); the seeded places are never changed. *_test database only."""
import pytest

from tests import account_helpers as h
from tests import admin_helpers as a
from tests.admin_helpers import clean_places, clean_stories  # noqa: F401  (fixtures)

pytestmark = pytest.mark.usefixtures("clean_accounts", "clean_stories", "clean_places")


@pytest.fixture()
def admin(app):
    client, _name = a.admin_client(app)
    return client


def post(admin, path, data, **kwargs):
    return a.post(admin, path, data, token_from="/admin/places/new", **kwargs)


# ------------------------------------------------------------------ create
def test_create_stores_the_place_in_the_chosen_region(admin):
    data = a.place_form(location_type="waterfront", region=a.REGIONS[1], source_url="https://example.org/ref", source_note="a note")
    assert post(admin, "/admin/places/new", data).status_code == 303
    row = a.place_row(data["slug"])
    assert (row["name"], row["region"], row["location_type"], row["content_status"], row["source_url"], row["source_note"]) == (
        data["name"], a.REGIONS[1], "waterfront", "demo", "https://example.org/ref", "a note")


def test_an_empty_slug_is_made_from_the_name(admin):
    data = a.place_form(slug="", name="TT Neon Pier")
    assert post(admin, "/admin/places/new", data).status_code == 303
    assert a.place_row("tt-neon-pier") is not None


def test_a_created_place_is_on_the_public_pages_and_in_its_region(admin, app):
    data = a.place_form(region=a.REGIONS[0])
    post(admin, "/admin/places/new", data)
    public = app.test_client()
    page = public.get(f"/locations/{data['slug']}")
    assert page.status_code == 200 and data["name"] in page.get_data(as_text=True)
    assert data["name"] in public.get(f"/api/v1/locations/{data['slug']}").get_data(as_text=True)
    assert data["name"] in public.get(f"/api/v1/locations?q=TT+Place&per_page=50&region={a.REGIONS[0]}").get_data(as_text=True)


def test_the_create_form_offers_every_region_and_every_type_but_never_official(admin):
    page = admin.get("/admin/places/new").get_data(as_text=True)
    regions = [r["slug"] for r in h.rows("SELECT slug FROM regions")]
    assert len(regions) == 6 and all(f'<option value="{slug}"' in page for slug in regions)
    assert all(f'<option value="{kind}"' in page for kind in a.PLACE_TYPES)
    assert 'value="official"' not in page and 'name="slug"' in page


# ------------------------------------------------------------------ read: the list
def test_the_list_shows_places_with_edit_and_delete_for_writable_ones_only(admin):
    mine = a.make_place(name="TT Listed Mine " + a.new_slug())
    official = a.make_place(status="official", name="TT Listed Official " + a.new_slug())
    page = admin.get("/admin/places?q=TT+Listed&per_page=50").get_data(as_text=True)
    assert f"/admin/places/{mine}/edit" in page and f"/admin/places/{mine}/delete" in page
    assert f"/admin/places/{official}/edit" not in page and f"/admin/places/{official}/delete" not in page
    assert "Read-only (official)" in page


def test_the_list_filters_by_region_type_and_label_sorts_and_paginates(admin):
    stamp = a.new_slug()
    names = [f"TT Page {stamp} {letter}" for letter in "ABC"]
    a.make_place(name=names[0], region=a.REGIONS[0], kind="landmark")
    a.make_place(name=names[1], region=a.REGIONS[1], kind="landmark")
    a.make_place(name=names[2], region=a.REGIONS[0], kind="venue")
    base = f"/admin/places?q={stamp}"
    only_first_region = admin.get(base + f"&region={a.REGIONS[0]}").get_data(as_text=True)
    assert names[0] in only_first_region and names[2] in only_first_region and names[1] not in only_first_region
    landmarks = admin.get(base + "&type=landmark").get_data(as_text=True)
    assert names[0] in landmarks and names[1] in landmarks and names[2] not in landmarks
    assert names[0] in admin.get(base + "&status=demo").get_data(as_text=True) and names[0] not in admin.get(base + "&status=fan").get_data(as_text=True)
    first = admin.get(base + "&sort=name_asc&per_page=2").get_data(as_text=True)
    assert names[0] in first and names[1] in first and names[2] not in first
    assert names[2] in admin.get(base + "&sort=name_asc&per_page=2&page=2").get_data(as_text=True)
    desc = admin.get(base + "&sort=name_desc&per_page=3").get_data(as_text=True)
    assert desc.index(names[2]) < desc.index(names[0])
    assert admin.get("/admin/places?sort=nonsense").status_code == 400
    assert admin.get("/admin/places?region=Not_A_Slug").status_code == 400


# ------------------------------------------------------------------ update
def test_update_changes_the_fields_and_can_move_the_place_to_another_region(admin):
    slug = a.make_place(region=a.REGIONS[0], kind="city")
    edit = a.place_form(name="TT Renamed " + a.new_slug(), region=a.REGIONS[1], location_type="wilderness", content_status="fan", summary="New summary",
                        description="New description", source_url="https://example.org/s", source_note="n")
    assert post(admin, f"/admin/places/{slug}/edit", edit).status_code == 303
    row = a.place_row(slug)
    assert (row["name"], row["region"], row["location_type"], row["content_status"], row["summary"], row["description"], row["source_url"], row["source_note"]) == (
        edit["name"], a.REGIONS[1], "wilderness", "fan", "New summary", "New description", "https://example.org/s", "n")


def test_moving_a_place_keeps_its_residents_story_links_and_favourites(admin, app):
    story = a.make_story()
    slug = a.make_place(region=a.REGIONS[0])
    resident = a.make_resident(slug)
    a.link_story_to_place(story, slug, primary=True)
    _c, name = h.signed_in_client(app)
    a.save_place_as(name, slug)
    before = a.place_snapshot(slug)
    post(admin, f"/admin/places/{slug}/edit", a.place_form(name=before["row"]["name"], region=a.REGIONS[1]))
    after = a.place_snapshot(slug)
    assert after["row"]["region"] == a.REGIONS[1] and before["row"]["region"] == a.REGIONS[0]
    assert {k: v for k, v in after.items() if k != "row"} == {k: v for k, v in before.items() if k != "row"}
    assert after["residents"] == [(resident, "demo")]


def test_the_slug_cannot_be_changed_by_an_edit(admin):
    slug = a.make_place()
    post(admin, f"/admin/places/{slug}/edit", a.place_form(slug="tt-a-different-address"))
    assert a.place_row(slug) is not None and a.place_row("tt-a-different-address") is None


def test_the_edit_form_shows_the_current_values(admin):
    slug = a.make_place(region=a.REGIONS[1], kind="venue", name="TT Prefilled " + a.new_slug())
    page = admin.get(f"/admin/places/{slug}/edit").get_data(as_text=True)
    assert "TT Prefilled" in page and f"/locations/{slug}" in page
    assert f'<option value="{a.REGIONS[1]}" selected>' in page and '<option value="venue" selected>' in page and '<option value="demo" selected>' in page


# ------------------------------------------------------------------ delete: the confirmation page tells the truth
def busy_place(app):
    """A place with everything attached: two demo residents, a fan resident, two story links, two favourites and a media link."""
    slug = a.make_place(region=a.REGIONS[0])
    residents = [a.make_resident(slug), a.make_resident(slug), a.make_resident(slug, status="fan")]
    stories = [a.make_story(), a.make_story()]
    for story in stories:
        a.link_story_to_place(story, slug)
    names = [h.signed_in_client(app)[1] for _ in range(2)]
    for name in names:
        a.save_place_as(name, slug)
    a.link_media_to_place(slug)
    return slug, residents, stories


def test_the_delete_page_counts_exactly_what_would_happen(admin, app):
    slug, residents, _stories = busy_place(app)
    page = admin.get(f"/admin/places/{slug}/delete").get_data(as_text=True)
    snap = a.place_snapshot(slug)
    assert f"{len(snap['residents'])} characters will have no home place" in page and len(snap["residents"]) == 3
    assert "2 story links" in page and "2 saved favourites" in page and "1 media link " in page
    assert all(f"TT Person {r[3:]}" in page for r in residents)                       # the residents are named
    assert a.place_snapshot(slug) == snap                                              # looking at the page changed nothing


def test_the_delete_does_what_the_page_said_and_nothing_else(admin, app):
    slug, residents, stories = busy_place(app)
    other = a.make_place()
    other_resident = a.make_resident(other)
    other_before = a.place_snapshot(other)
    region_count = h.rows("SELECT COUNT(*) AS n FROM regions")[0]["n"]
    characters = h.rows("SELECT COUNT(*) AS n FROM characters")[0]["n"]
    missions = h.rows("SELECT COUNT(*) AS n FROM missions")[0]["n"]
    media = h.rows("SELECT COUNT(*) AS n FROM media_assets")[0]["n"]
    admin.get(f"/admin/places/{slug}/delete")
    assert a.place_row(slug) is not None                                               # a GET never deletes
    assert post(admin, f"/admin/places/{slug}/delete", {}).status_code == 303
    assert a.place_row(slug) is None
    # SET NULL: the residents are still there, without a home
    homes = h.rows("SELECT slug, home_location_id FROM characters WHERE slug IN (%s, %s, %s)", tuple(residents))
    assert len(homes) == 3 and all(r["home_location_id"] is None for r in homes)
    # CASCADE: the story links, favourites and media links of the place are gone; the stories themselves are not
    assert h.rows("SELECT COUNT(*) AS n FROM mission_locations ml LEFT JOIN locations l ON l.location_id = ml.location_id WHERE l.location_id IS NULL")[0]["n"] == 0
    assert all(a.story_row(s) is not None for s in stories)
    # nothing else moved
    assert h.rows("SELECT COUNT(*) AS n FROM regions")[0]["n"] == region_count
    assert h.rows("SELECT COUNT(*) AS n FROM characters")[0]["n"] == characters and h.rows("SELECT COUNT(*) AS n FROM missions")[0]["n"] == missions
    assert h.rows("SELECT COUNT(*) AS n FROM media_assets")[0]["n"] == media
    assert a.place_snapshot(other) == other_before and a.place_snapshot(other)["residents"] == [(other_resident, "demo")]
    assert app.test_client().get(f"/locations/{slug}").status_code == 404


def test_deleting_an_unknown_place_is_404(admin):
    assert post(admin, "/admin/places/tt-nothing-here/delete", {}).status_code == 404


def test_a_place_with_nothing_attached_deletes_cleanly(admin):
    slug = a.make_place()
    page = admin.get(f"/admin/places/{slug}/delete").get_data(as_text=True)
    assert "0 characters will have no home place" in page and "0 story links" in page
    assert post(admin, f"/admin/places/{slug}/delete", {}).status_code == 303 and a.place_row(slug) is None


def test_stories_that_linked_a_deleted_place_still_open(admin, app):
    story, slug = a.make_story(places=a.PLACES[:1], primary=a.PLACES[0]), a.make_place()
    a.link_story_to_place(story, slug)
    post(admin, f"/admin/places/{slug}/delete", {})
    page = app.test_client().get(f"/missions/{story}")
    assert page.status_code == 200
    assert a.links_of(story)["locations"] == [(a.PLACES[0], True)]                       # its other link is untouched
