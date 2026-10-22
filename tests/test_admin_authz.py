"""Admin authorization: who may reach /admin, and proof that no route can be added without the check. Negative cases first: a signed-out visitor and an ordinary
account must be turned away on every route and every method, and must change nothing in the database. The routes cover both Stories and Places. Rows are written to
the *_test database only."""
import pytest

from tests import account_helpers as h
from tests import admin_helpers as a
from tests.admin_helpers import clean_places, clean_stories  # noqa: F401  (fixtures)

pytestmark = pytest.mark.usefixtures("clean_accounts", "clean_stories", "clean_places")


def admin_rules(app):
    return [rule for rule in app.url_map.iter_rules() if rule.endpoint.startswith("admin.")]


def concrete(rule, slugs):
    """The rule's address with a slug that exists: a story's for the story routes, a place's for the place routes."""
    return rule.rule.replace("<slug>", slugs["places"] if rule.rule.startswith("/admin/places") else slugs["stories"])


def make_both():
    return {"stories": a.make_story(characters=a.CHARACTERS[:1], places=a.PLACES[:1], primary=a.PLACES[0]),
            "places": a.make_place()}


def methods(rule):
    return sorted(rule.methods - {"HEAD", "OPTIONS"})


# ------------------------------------------------------------------ the structure: nothing can be forgotten
def test_every_admin_route_carries_the_admin_check(app):
    rules = admin_rules(app)
    assert len(rules) >= 9
    unprotected = [rule.rule for rule in rules if not getattr(app.view_functions[rule.endpoint], "admin_protected", False)]
    assert unprotected == []


def test_the_admin_blueprint_only_has_routes_under_admin(app):
    assert all(rule.rule == "/admin" or rule.rule.startswith("/admin/") for rule in admin_rules(app))


def test_both_stories_and_places_routes_exist(app):
    paths = {rule.rule for rule in admin_rules(app)}
    assert {"/admin/stories", "/admin/stories/new", "/admin/places", "/admin/places/new"} <= paths
    assert {"/admin/places/<slug>/edit", "/admin/places/<slug>/delete", "/admin/stories/<slug>/edit", "/admin/stories/<slug>/delete"} <= paths


# ------------------------------------------------------------------ signed out
def test_signed_out_visitors_are_sent_to_sign_in_on_every_route_and_method(app):
    slugs = make_both()
    for rule in admin_rules(app):
        for method in methods(rule):
            client = app.test_client()
            if method == "GET":
                response = client.get(concrete(rule, slugs))
            else:
                response = a.post(client, concrete(rule, slugs), {"title": "x"}, token_from="/login")
            assert response.status_code == 303 and response.headers["Location"].endswith("/login"), (method, rule.rule, response.status_code)


def test_signed_out_posts_without_a_token_are_refused_before_anything_else(app):
    slugs = make_both()
    story_before, place_before = a.snapshot(slugs["stories"]), a.place_snapshot(slugs["places"])
    for rule in admin_rules(app):
        if "POST" in rule.methods:
            response = app.test_client().post(concrete(rule, slugs), data={"title": "x"})
            assert response.status_code == 400, rule.rule
    assert a.snapshot(slugs["stories"]) == story_before and a.place_snapshot(slugs["places"]) == place_before


# ------------------------------------------------------------------ signed in, but not an administrator
def test_an_ordinary_account_gets_403_on_every_route_and_method_and_changes_nothing(app):
    slugs = make_both()
    story_before, place_before = a.snapshot(slugs["stories"]), a.place_snapshot(slugs["places"])
    stories, places = a.count_stories(), a.count_places()
    client, _name = h.signed_in_client(app)
    for rule in admin_rules(app):
        for method in methods(rule):
            if method == "GET":
                response = client.get(concrete(rule, slugs))
            else:
                data = a.with_links(a.story_form(), characters=a.CHARACTERS[:1]) if "/stories" in rule.rule else a.place_form()
                response = a.post(client, concrete(rule, slugs), data, token_from="/account/favourites")
            assert response.status_code == 403, (method, rule.rule, response.status_code)
    assert a.snapshot(slugs["stories"]) == story_before and a.place_snapshot(slugs["places"]) == place_before
    assert a.count_stories() == stories and a.count_places() == places


def test_a_forbidden_page_does_not_reveal_anything_about_the_story_or_the_place(app):
    slugs = {"stories": a.make_story(title="TT Secret Title " + a.new_slug()), "places": a.make_place(name="TT Secret Place " + a.new_slug())}
    client, _name = h.signed_in_client(app)
    for path in (f"/admin/stories/{slugs['stories']}/edit", f"/admin/places/{slugs['places']}/edit", f"/admin/places/{slugs['places']}/delete"):
        page = client.get(path).get_data(as_text=True)
        assert "Secret Title" not in page and "Secret Place" not in page and "synopsis" not in page.lower().replace("<meta", "")


def test_posting_role_admin_at_sign_up_does_not_create_an_administrator(app):
    client = app.test_client()
    response = h.register(client, role="admin", is_admin="1")
    assert response.status_code == 303
    assert h.user_row(response.username)["role"] == "user"
    assert client.get("/admin").status_code == 403


# ------------------------------------------------------------------ administrators
def test_an_administrator_reaches_every_get_route(app):
    slugs = make_both()
    client, _name = a.admin_client(app)
    for rule in admin_rules(app):
        if "GET" in rule.methods:
            response = client.get(concrete(rule, slugs))
            assert response.status_code == 200, (rule.rule, response.status_code)


def test_admin_pages_are_never_stored_by_a_cache(app):
    client, _name = a.admin_client(app)
    for path in ("/admin", "/admin/stories", "/admin/stories/new", "/admin/places", "/admin/places/new"):
        assert client.get(path).headers["Cache-Control"] == "no-store", path


def test_taking_the_role_away_applies_to_the_very_next_request(app):
    client, name = a.admin_client(app)
    assert client.get("/admin").status_code == 200
    assert a.make_admin.main(["--test", "--yes", "--revoke", name]) == 0
    assert client.get("/admin").status_code == 403
    assert client.get("/admin/stories").status_code == 403
    assert client.get("/admin/places").status_code == 403


def test_an_unknown_story_or_place_is_404_for_an_administrator_and_not_a_hint_for_anyone_else(app):
    admin, _a = a.admin_client(app)
    for path in ("/admin/stories/tt-no-such-story/edit", "/admin/places/tt-no-such-place/edit", "/admin/places/tt-no-such-place/delete"):
        assert admin.get(path).status_code == 404, path
    assert admin.get("/admin/stories/Not_A_Slug/edit").status_code == 404
    assert admin.get("/admin/places/Not_A_Slug/edit").status_code == 404
    ordinary, _o = h.signed_in_client(app)
    assert ordinary.get("/admin/stories/tt-no-such-story/edit").status_code == 403
    assert ordinary.get("/admin/places/tt-no-such-place/edit").status_code == 403
