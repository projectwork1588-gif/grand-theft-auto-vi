"""Input validation and request protection for the admin story forms: field limits at their boundaries, link rules, hostile input stored as plain text and shown
escaped, CSRF and origin checks, and the request size (the global 16 KiB limit is NOT raised: the largest realistic form is measured to fit). Rows are written to
the *_test database only."""
from urllib.parse import urlencode

import pytest

from tests import account_helpers as h
from tests import admin_helpers as a
from tests.admin_helpers import clean_stories  # noqa: F401  (a fixture)

pytestmark = pytest.mark.usefixtures("clean_accounts", "clean_stories")


@pytest.fixture()
def admin(app):
    client, _name = a.admin_client(app)
    return client


def create(admin, **overrides):
    return a.post(admin, "/admin/stories/new", a.story_form(**overrides))


def refused(response, field):
    page = response.get_data(as_text=True)
    return response.status_code == 400 and f'id="{field}-note"' in page and 'role="alert"' in page


# ------------------------------------------------------------------ field limits, at the boundary
@pytest.mark.parametrize("title", ["abc", "t" * 120])
def test_titles_at_the_limits_are_accepted(admin, title):
    assert create(admin, title=title).status_code == 303


@pytest.mark.parametrize("title", ["ab", "t" * 121, "   ", "", "bad" + chr(0) + "title", "bad" + chr(10) + "title"])
def test_titles_outside_the_limits_are_refused(admin, title):
    assert refused(create(admin, title=title), "title")


@pytest.mark.parametrize("field, limit", [("summary", 255), ("source_note", 500), ("synopsis", 3000)])
def test_text_limits_accept_the_maximum_and_refuse_one_more(admin, field, limit):
    assert create(admin, **{field: "x" * limit}).status_code == 303
    assert refused(create(admin, **{field: "x" * (limit + 1)}), field)


def test_summary_and_synopsis_are_required(admin):
    assert refused(create(admin, summary=""), "summary")
    assert refused(create(admin, synopsis="   "), "synopsis")


@pytest.mark.parametrize("slug", ["Bad_Slug", "-leading", "trailing-", "double--hyphen", "has space", "a" * 81, "ünï"])
def test_a_bad_slug_is_refused(admin, slug):
    assert refused(create(admin, slug=slug), "slug")


def test_the_longest_allowed_slug_is_accepted(admin):
    assert create(admin, slug="tt-" + "a" * 77).status_code == 303


@pytest.mark.parametrize("url", ["http://example.org", "javascript:alert(1)", "https://user@example.org", "https://", "ftp://example.org/x", "https://exa mple.org", "https://example.org/" + "p" * 500])
def test_a_bad_source_address_is_refused(admin, url):
    assert refused(create(admin, source_url=url), "source_url")


def test_a_plain_https_source_address_is_accepted(admin):
    data = a.story_form(source_url="https://example.org/a/source?x=1")
    assert a.post(admin, "/admin/stories/new", data).status_code == 303 and a.story_row(data["slug"])["source_url"] == "https://example.org/a/source?x=1"


@pytest.mark.parametrize("field, value", [("mission_type", "epic"), ("mission_type", ""), ("content_status", "fanfic"), ("content_status", "")])
def test_type_and_label_must_be_from_their_lists(admin, field, value):
    assert refused(create(admin, **{field: value}), field)


# ------------------------------------------------------------------ links
def test_an_unknown_link_is_refused(admin):
    data = a.with_links(a.story_form(), characters=["no-such-character"])
    assert refused(a.post(admin, "/admin/stories/new", data), "characters")


@pytest.mark.parametrize("bad", ["UPPER", "a" * 81, "has space", "semi;colon"])
def test_a_malformed_link_slug_is_refused(admin, bad):
    data = a.story_form()
    data["vehicles"] = [bad]
    assert refused(a.post(admin, "/admin/stories/new", data), "vehicles")


def test_a_ticked_character_needs_a_role_note_within_its_limit(admin):
    data = a.with_links(a.story_form(), characters=a.CHARACTERS[:1])
    data[f"characters_note__{a.CHARACTERS[0]}"] = ""
    assert refused(a.post(admin, "/admin/stories/new", data), f"characters_note__{a.CHARACTERS[0]}")
    data[f"characters_note__{a.CHARACTERS[0]}"] = "r" * 81
    assert refused(a.post(admin, "/admin/stories/new", data), f"characters_note__{a.CHARACTERS[0]}")
    data[f"characters_note__{a.CHARACTERS[0]}"] = "r" * 80
    assert a.post(admin, "/admin/stories/new", data).status_code == 303


def test_a_ticked_vehicle_needs_a_use_note_within_its_limit(admin):
    data = a.with_links(a.story_form(), vehicles=a.VEHICLES[:1])
    data[f"vehicles_note__{a.VEHICLES[0]}"] = "u" * 161
    assert refused(a.post(admin, "/admin/stories/new", data), f"vehicles_note__{a.VEHICLES[0]}")
    data[f"vehicles_note__{a.VEHICLES[0]}"] = "u" * 160
    assert a.post(admin, "/admin/stories/new", data).status_code == 303


def test_the_main_place_must_be_one_of_the_ticked_places(admin):
    data = a.with_links(a.story_form(), places=a.PLACES[:1], primary=a.PLACES[1])
    assert refused(a.post(admin, "/admin/stories/new", data), "primary_location")


def test_a_note_for_an_unticked_character_is_ignored(admin):
    data = a.story_form()
    data[f"characters_note__{a.CHARACTERS[0]}"] = "stray note"
    assert a.post(admin, "/admin/stories/new", data).status_code == 303
    assert a.links_of(data["slug"])["characters"] == []


def test_a_slug_posted_twice_is_linked_once(admin):
    data = a.with_links(a.story_form(), characters=[a.CHARACTERS[0], a.CHARACTERS[0]])
    assert a.post(admin, "/admin/stories/new", data).status_code == 303
    assert len(a.links_of(data["slug"])["characters"]) == 1


def test_after_a_problem_the_form_shows_what_was_typed_and_ticked(admin):
    data = a.with_links(a.story_form(title="TT Keep Me " + a.new_slug(), summary=""), characters=a.CHARACTERS[:1], places=a.PLACES, primary=a.PLACES[1])
    page = a.post(admin, "/admin/stories/new", data).get_data(as_text=True)
    assert data["title"] in page and f'id="characters__{a.CHARACTERS[0]}" name="characters" value="{a.CHARACTERS[0]}" checked' in page
    assert f'<option value="{a.PLACES[1]}" selected>' in page


# ------------------------------------------------------------------ hostile input
@pytest.mark.parametrize("text", ["'; DROP TABLE missions; --", "x' OR '1'='1", "50% off_ \\ ` \" '", "<script>alert(1)</script>", "<img src=x onerror=alert(1)>"])
def test_hostile_text_is_stored_as_plain_text_and_the_tables_survive(admin, app, text):
    count = a.count_stories()
    data = a.story_form(title="TT " + text, summary=text, synopsis=text, source_note=text)
    assert a.post(admin, "/admin/stories/new", data).status_code == 303
    row = a.story_row(data["slug"])
    assert row["title"] == "TT " + text and row["summary"] == text and row["synopsis"] == text
    assert a.count_stories() == count + 1


def test_text_is_escaped_on_the_admin_pages_and_on_the_public_page(admin, app):
    data = a.story_form(title="TT <b>bold</b> " + a.new_slug(), summary="<script>alert(1)</script>", synopsis="<img src=x onerror=alert(1)>")
    a.post(admin, "/admin/stories/new", data)
    slug = data["slug"]
    pages = [admin.get(f"/admin/stories/{slug}/edit").get_data(as_text=True), admin.get("/admin/stories?q=TT+%3Cb%3E&per_page=50").get_data(as_text=True),
             app.test_client().get(f"/missions/{slug}").get_data(as_text=True)]
    for page in pages:
        assert "<script>alert(1)</script>" not in page and "<img src=x onerror" not in page and "<b>bold</b>" not in page
    assert "&lt;b&gt;bold&lt;/b&gt;" in pages[0]


def test_a_like_wildcard_in_the_search_is_a_literal_character(admin):
    a.make_story(title="TT Fifty% Rule " + a.new_slug())
    assert "Fifty% Rule" in admin.get("/admin/stories?q=Fifty%25").get_data(as_text=True)
    assert "Fifty% Rule" not in admin.get("/admin/stories?q=Fifty_Rule").get_data(as_text=True)


# ------------------------------------------------------------------ CSRF and origin
def test_a_post_without_the_token_is_refused_and_creates_nothing(admin):
    count = a.count_stories()
    assert admin.post("/admin/stories/new", data=a.story_form()).status_code == 400
    assert admin.post("/admin/stories/new", data=a.story_form() | {"csrf_token": "wrong"}).status_code == 400
    assert a.count_stories() == count


def test_a_post_from_another_origin_is_refused(admin):
    count = a.count_stories()
    token = h.token(admin, "/admin/stories/new")
    response = admin.post("/admin/stories/new", data=a.story_form() | {"csrf_token": token}, headers={"Origin": "https://evil.example"})
    assert response.status_code == 400 and a.count_stories() == count


def test_a_token_from_another_session_is_refused(admin, app):
    other = app.test_client()
    foreign_token = h.token(other, "/login")
    assert admin.post("/admin/stories/new", data=a.story_form() | {"csrf_token": foreign_token}).status_code == 400


# ------------------------------------------------------------------ request size
def all_slugs():
    return {kind: [r["slug"] for r in h.rows(f"SELECT slug FROM {table} ORDER BY slug")] for kind, table in (("characters", "characters"), ("vehicles", "vehicles"), ("locations", "locations"))}


def largest_form():
    """Every character, vehicle and place ticked, every note at its maximum, the synopsis at its maximum with typographic punctuation."""
    slugs = all_slugs()
    text = ("The crew meets at dusk — argues about “the plan”, and nobody agrees; it’s café time. " * 40)
    data = a.story_form(title="TT " + "T" * 100, slug="tt-" + "s" * 77, summary=text[:255], synopsis=text[:3000], source_url="https://example.org/" + "p" * 470, source_note=text[:500])
    data["characters"], data["vehicles"], data["locations"], data["primary_location"] = slugs["characters"], slugs["vehicles"], slugs["locations"], slugs["locations"][0]
    for slug in slugs["characters"]:
        data[f"characters_note__{slug}"] = text[:80]
    for slug in slugs["vehicles"]:
        data[f"vehicles_note__{slug}"] = text[:160]
    return data


def test_the_largest_realistic_form_fits_the_global_limit_and_is_accepted(admin, app):
    assert app.config["MAX_CONTENT_LENGTH"] == 16 * 1024                      # the global protection is unchanged
    data = largest_form()
    token = h.token(admin, "/admin/stories/new")
    wire = urlencode({**data, "csrf_token": token}, doseq=True)
    assert len(wire.encode("ascii")) < 14 * 1024, len(wire)                    # measured: about 13.5 KB, so the limit does not need to change
    response = admin.post("/admin/stories/new", data={**data, "csrf_token": token})
    assert response.status_code == 303, response.get_data(as_text=True)[:400]
    links = a.links_of(data["slug"])
    slugs = all_slugs()
    assert [c for c, _n in links["characters"]] == sorted(slugs["characters"]) and len(links["vehicles"]) == len(slugs["vehicles"]) and len(links["locations"]) == len(slugs["locations"])


def test_a_body_over_the_limit_is_refused_with_413_before_it_is_read(admin):
    count = a.count_stories()
    token = h.token(admin, "/admin/stories/new")
    response = admin.post("/admin/stories/new", data=a.story_form(synopsis="x" * 17000) | {"csrf_token": token})
    assert response.status_code == 413
    assert a.count_stories() == count
