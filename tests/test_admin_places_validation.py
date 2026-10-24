"""Input validation and request protection for the admin place forms: field limits at their boundaries, the region and type choices, hostile input stored as plain text and shown
escaped, CSRF and origin checks, a client-supplied id that must be ignored, and the request size (the global 16 KiB limit is NOT raised: the largest realistic place form is
measured to fit). Rows are written to the *_test database only."""
from urllib.parse import urlencode

import pytest

from tests import account_helpers as h
from tests import admin_helpers as a
from tests.admin_helpers import clean_places, clean_stories  # noqa: F401  (fixtures)

pytestmark = pytest.mark.usefixtures("clean_accounts", "clean_stories", "clean_places")


@pytest.fixture()
def admin(app):
    client, _name = a.admin_client(app)
    return client


def create(admin, **overrides):
    return a.post(admin, "/admin/places/new", a.place_form(**overrides), token_from="/admin/places/new")


def refused(response, field):
    page = response.get_data(as_text=True)
    return response.status_code == 400 and f'id="{field}-note"' in page and 'role="alert"' in page


# ------------------------------------------------------------------ field limits, at the boundary
@pytest.mark.parametrize("name", ["abc", "n" * 100])
def test_names_at_the_limits_are_accepted(admin, name):
    assert create(admin, name=name).status_code == 303


@pytest.mark.parametrize("name", ["ab", "n" * 101, "   ", "", "bad" + chr(0) + "name", "bad" + chr(10) + "name"])
def test_names_outside_the_limits_are_refused(admin, name):
    assert refused(create(admin, name=name), "name")


@pytest.mark.parametrize("field, limit", [("summary", 255), ("source_note", 500), ("description", 3000)])
def test_text_limits_accept_the_maximum_and_refuse_one_more(admin, field, limit):
    assert create(admin, **{field: "x" * limit}).status_code == 303
    assert refused(create(admin, **{field: "x" * (limit + 1)}), field)


def test_summary_and_description_are_required(admin):
    assert refused(create(admin, summary=""), "summary")
    assert refused(create(admin, description="   "), "description")


@pytest.mark.parametrize("slug", ["Bad_Slug", "-leading", "trailing-", "double--hyphen", "has space", "a" * 81, "ünï"])
def test_a_bad_slug_is_refused(admin, slug):
    assert refused(create(admin, slug=slug), "slug")


def test_the_longest_allowed_slug_is_accepted(admin):
    assert create(admin, slug="tt-" + "a" * 77).status_code == 303


@pytest.mark.parametrize("url", ["http://example.org", "javascript:alert(1)", "https://user@example.org", "https://", "ftp://example.org/x", "https://exa mple.org", "https://example.org/" + "p" * 500])
def test_a_bad_source_address_is_refused(admin, url):
    assert refused(create(admin, source_url=url), "source_url")


def test_a_plain_https_source_address_is_accepted(admin):
    data = a.place_form(source_url="https://example.org/a/source?x=1")
    assert a.post(admin, "/admin/places/new", data, token_from="/admin/places/new").status_code == 303 and a.place_row(data["slug"])["source_url"] == "https://example.org/a/source?x=1"


# ------------------------------------------------------------------ the region and the type
@pytest.mark.parametrize("region, ok", [("", False), ("no-such-region", False), ("Not_A_Slug", False), ("a" * 81, False), ("vice-city", True), ("mount-kalaga", True)])
def test_the_region_must_be_an_existing_one(admin, region, ok):
    response = create(admin, region=region)
    if ok:
        assert response.status_code == 303
    else:
        assert refused(response, "region")


@pytest.mark.parametrize("kind", a.PLACE_TYPES)
def test_every_location_type_is_accepted(admin, kind):
    assert create(admin, location_type=kind).status_code == 303


@pytest.mark.parametrize("field, value", [("location_type", "castle"), ("location_type", ""), ("content_status", "fanfic"), ("content_status", "")])
def test_type_and_label_must_be_from_their_lists(admin, field, value):
    assert refused(create(admin, **{field: value}), field)


def test_a_client_supplied_id_is_ignored(admin):
    """The form names the region by its slug. A posted region_id or location_id changes nothing: with no valid slug the form is refused, with one it is used."""
    count = a.count_places()
    data = a.place_form(region="")
    data["region_id"], data["location_id"] = "1", "1"
    assert refused(a.post(admin, "/admin/places/new", data, token_from="/admin/places/new"), "region")
    assert a.count_places() == count
    data = a.place_form(region=a.REGIONS[1])
    data["region_id"], data["location_id"], data["home_location_id"] = "1", "1", "1"
    assert a.post(admin, "/admin/places/new", data, token_from="/admin/places/new").status_code == 303
    row = a.place_row(data["slug"])
    assert row["region"] == a.REGIONS[1] and row["location_id"] != 1


def test_after_a_problem_the_form_shows_what_was_typed_and_chosen(admin):
    data = a.place_form(name="TT Keep Me " + a.new_slug(), summary="", region=a.REGIONS[1], location_type="waterfront", content_status="fan")
    page = a.post(admin, "/admin/places/new", data, token_from="/admin/places/new").get_data(as_text=True)
    assert data["name"] in page
    assert f'<option value="{a.REGIONS[1]}" selected>' in page and '<option value="waterfront" selected>' in page and '<option value="fan" selected>' in page


# ------------------------------------------------------------------ hostile input
@pytest.mark.parametrize("text", ["'; DROP TABLE locations; --", "x' OR '1'='1", "50% off_ \\ ` \" '", "<script>alert(1)</script>", "<img src=x onerror=alert(1)>"])
def test_hostile_text_is_stored_as_plain_text_and_the_tables_survive(admin, text):
    count = a.count_places()
    data = a.place_form(name="TT " + text, summary=text, description=text, source_note=text)
    assert a.post(admin, "/admin/places/new", data, token_from="/admin/places/new").status_code == 303
    row = a.place_row(data["slug"])
    assert row["name"] == "TT " + text and row["summary"] == text and row["description"] == text
    assert a.count_places() == count + 1


def test_text_is_escaped_on_the_admin_pages_and_on_the_public_page(admin, app):
    data = a.place_form(name="TT <b>bold</b> " + a.new_slug(), summary="<script>alert(1)</script>", description="<img src=x onerror=alert(1)>")
    a.post(admin, "/admin/places/new", data, token_from="/admin/places/new")
    slug = data["slug"]
    pages = [admin.get(f"/admin/places/{slug}/edit").get_data(as_text=True), admin.get("/admin/places?q=TT+%3Cb%3E&per_page=50").get_data(as_text=True),
             admin.get(f"/admin/places/{slug}/delete").get_data(as_text=True), app.test_client().get(f"/locations/{slug}").get_data(as_text=True)]
    for page in pages:
        assert "<script>alert(1)</script>" not in page and "<img src=x onerror" not in page and "<b>bold</b>" not in page
    assert "&lt;b&gt;bold&lt;/b&gt;" in pages[0]


def test_a_like_wildcard_in_the_search_is_a_literal_character(admin):
    a.make_place(name="TT Fifty% Rule " + a.new_slug())
    assert "Fifty% Rule" in admin.get("/admin/places?q=Fifty%25").get_data(as_text=True)
    assert "Fifty% Rule" not in admin.get("/admin/places?q=Fifty_Rule").get_data(as_text=True)


# ------------------------------------------------------------------ CSRF and origin
def test_a_post_without_the_token_is_refused_and_creates_nothing(admin):
    count = a.count_places()
    assert admin.post("/admin/places/new", data=a.place_form()).status_code == 400
    assert admin.post("/admin/places/new", data=a.place_form() | {"csrf_token": "wrong"}).status_code == 400
    assert a.count_places() == count


def test_a_post_from_another_origin_is_refused(admin):
    count = a.count_places()
    token = h.token(admin, "/admin/places/new")
    response = admin.post("/admin/places/new", data=a.place_form() | {"csrf_token": token}, headers={"Origin": "https://evil.example"})
    assert response.status_code == 400 and a.count_places() == count


def test_a_token_from_another_session_is_refused(admin, app):
    foreign_token = h.token(app.test_client(), "/login")
    assert admin.post("/admin/places/new", data=a.place_form() | {"csrf_token": foreign_token}).status_code == 400


def test_edit_and_delete_posts_without_a_token_change_nothing(admin):
    slug = a.make_place()
    before = a.place_snapshot(slug)
    assert admin.post(f"/admin/places/{slug}/edit", data=a.place_form()).status_code == 400
    assert admin.post(f"/admin/places/{slug}/delete", data={}).status_code == 400
    assert a.place_snapshot(slug) == before


# ------------------------------------------------------------------ request size
def largest_form():
    """Every field at its maximum, with typographic punctuation (several bytes per character once a browser encodes it)."""
    text = ("The crew meets at dusk — argues about “the plan”, and nobody agrees; it’s café time. " * 40)
    return a.place_form(name="TT " + "T" * 97, slug="tt-" + "s" * 77, summary=text[:255], description=text[:3000], source_url="https://example.org/" + "p" * 470, source_note=text[:500])


def test_the_largest_realistic_place_form_fits_the_global_limit_and_is_accepted(admin, app):
    assert app.config["MAX_CONTENT_LENGTH"] == 16 * 1024                      # the global protection is unchanged
    data = largest_form()
    token = h.token(admin, "/admin/places/new")
    wire = urlencode({**data, "csrf_token": token}, doseq=True)
    assert len(wire.encode("ascii")) < 12 * 1024, len(wire)                    # measured: well under the limit, so it does not need to change
    response = admin.post("/admin/places/new", data={**data, "csrf_token": token})
    assert response.status_code == 303, response.get_data(as_text=True)[:400]
    assert a.place_row(data["slug"]) is not None


def test_a_body_over_the_limit_is_refused_with_413_before_it_is_read(admin):
    count = a.count_places()
    token = h.token(admin, "/admin/places/new")
    response = admin.post("/admin/places/new", data=a.place_form(description="x" * 17000) | {"csrf_token": token})
    assert response.status_code == 413
    assert a.count_places() == count
