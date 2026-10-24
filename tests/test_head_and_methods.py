"""HTTP methods and CSRF (Stage 5, finding M1). Flask answers HEAD through every GET route, and several views used to decide "is this a submission?" with
`request.method == "GET"`, so a HEAD request ran the submission branch: no CSRF check (the guard only covered POST/PUT/PATCH/DELETE), a real delete on the admin delete pages,
and a spent sign-in throttle. These tests pin the repaired behaviour: HEAD is exactly GET without a body, only POST submits, and every method that is not safe needs the token.
Reads and writes the *_test database only; the existing fixtures clean up."""
import re
from pathlib import Path

import pytest

from app import create_app
from tests import account_helpers as h
from tests import admin_helpers as a
from tests.admin_helpers import clean_places, clean_stories  # noqa: F401  (fixtures)

pytestmark = pytest.mark.usefixtures("clean_accounts", "clean_stories", "clean_places")

BLUEPRINTS = Path(__file__).resolve().parent.parent / "app" / "blueprints"
SAMPLE = {"/characters/<slug>": "jason-duval", "/vehicles/<slug>": "grotti-cheetah", "/regions/<slug>": "vice-city", "/locations/<slug>": "neon-row-district",
          "/missions/<slug>": "harbour-lights", "/api/v1/characters/<slug>": "jason-duval", "/api/v1/vehicles/<slug>": "grotti-cheetah", "/api/v1/regions/<slug>": "vice-city",
          "/api/v1/locations/<slug>": "neon-row-district", "/api/v1/missions/<slug>": "harbour-lights"}


# ------------------------------------------------------------------ the structure: the pattern cannot come back
def test_no_view_decides_what_to_do_by_asking_whether_the_method_is_get():
    """`request.method == "GET"` is the bug: HEAD is not GET but must behave like it. A view asks whether the request is a POST instead."""
    offenders = []
    for path in sorted(BLUEPRINTS.glob("*.py")):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if re.search(r"request\.method\s*(==|in)\s*[\"']GET[\"']|request\.method\s*==\s*\(?[\"']GET", line):
                offenders.append(f"{path.name}:{number}")
    assert offenders == []


def test_the_nine_views_that_take_a_form_ask_whether_the_request_is_a_post():
    seen = 0
    for name in ("account.py", "admin.py"):
        text = (BLUEPRINTS / name).read_text(encoding="utf-8")
        seen += len(re.findall(r'if request\.method != "POST":', text))
    assert seen == 9


# ------------------------------------------------------------------ HEAD is GET without a body, and changes nothing
def test_head_on_the_admin_delete_pages_deletes_nothing_for_an_administrator(app):
    client, _name = a.admin_client(app)
    story, place = a.make_story(), a.make_place()
    before = (a.count_stories(), a.count_places(), a.snapshot(story), a.place_snapshot(place))
    for path in (f"/admin/stories/{story}/delete", f"/admin/places/{place}/delete"):
        head, get = client.head(path), client.get(path)
        assert head.status_code == get.status_code == 200, path
        assert head.get_data() == b"" and get.get_data(as_text=True).strip()          # a HEAD answer has headers only
        assert head.headers["Content-Type"] == get.headers["Content-Type"]
    assert (a.count_stories(), a.count_places(), a.snapshot(story), a.place_snapshot(place)) == before


def test_head_on_every_admin_route_answers_what_get_answers_and_changes_nothing(app):
    client, _name = a.admin_client(app)
    story, place = a.make_story(), a.make_place()
    before = (a.count_stories(), a.count_places(), a.snapshot(story), a.place_snapshot(place))
    checked = 0
    for rule in app.url_map.iter_rules():
        if rule.endpoint.startswith("admin.") and "GET" in rule.methods:
            path = rule.rule.replace("<slug>", place if rule.rule.startswith("/admin/places") else story)
            head, get = client.head(path), client.get(path)
            assert head.status_code == get.status_code and head.status_code < 400, (path, head.status_code, get.status_code)
            checked += 1
    assert checked >= 9
    assert (a.count_stories(), a.count_places(), a.snapshot(story), a.place_snapshot(place)) == before


def test_head_for_a_visitor_and_an_ordinary_account_is_the_same_refusal_as_get(app):
    story = a.make_story()
    anonymous = app.test_client()
    ordinary, _ = h.signed_in_client(app)
    for client, expected in ((anonymous, 303), (ordinary, 403)):
        for path in ("/admin", "/admin/stories", "/admin/stories/new", f"/admin/stories/{story}/edit", f"/admin/stories/{story}/delete", "/admin/places/new"):
            assert client.head(path).status_code == client.get(path).status_code == expected, path
    assert a.story_row(story) is not None


def test_head_on_every_public_route_answers_what_get_answers(app):
    client = app.test_client()
    checked = 0
    for rule in app.url_map.iter_rules():
        if rule.endpoint == "static" or "GET" not in rule.methods or rule.endpoint.startswith("admin."):
            continue
        path = SAMPLE.get(rule.rule) and rule.rule.replace("<slug>", SAMPLE[rule.rule]) or rule.rule.replace("<kind>", "characters").replace("<path:filename>", "clips/none.mp4").replace("<slug>", "x")
        head, get = client.head(path), client.get(path)
        assert head.status_code == get.status_code, (path, head.status_code, get.status_code)
        assert head.headers.get("Location") == get.headers.get("Location"), path
        assert head.get_data() == b"", path
        checked += 1
    assert checked >= 25


# ------------------------------------------------------------------ HEAD no longer spends a throttle
def test_head_requests_never_spend_the_sign_in_throttle(app):
    client = app.test_client()
    assert [client.head("/login").status_code for _ in range(20)] == [200] * 20
    wrong = h.post(client, "/login", {"username": "tt_nobody_here", "password": "not the password at all"})
    assert wrong.status_code == 401                                     # a real wrong password is the first failure, not the twenty-first
    assert [client.head("/login").status_code for _ in range(5)] == [200] * 5


def test_head_requests_never_spend_the_sign_up_throttle_or_create_anything(app):
    client = app.test_client()
    assert [client.head("/register").status_code for _ in range(20)] == [200] * 20
    assert h.register(client).status_code == 303


def test_head_on_the_password_page_never_spends_the_password_throttle(app):
    client, name = h.signed_in_client(app)
    assert [client.head("/account/password").status_code for _ in range(20)] == [200] * 20
    wrong = h.post(client, "/account/password", {"current_password": "definitely wrong", "new_password": "another long passphrase 42", "new_password_confirm": "another long passphrase 42"},
                   token_from="/account/password")
    assert wrong.status_code == 400 and h.user_row(name) is not None


# ------------------------------------------------------------------ every method that is not safe needs the token
def test_every_post_route_refuses_a_missing_token_a_wrong_token_and_a_foreign_origin(app):
    story, place = a.make_story(), a.make_place()
    client, _ = a.admin_client(app)
    token = h.token(client, "/admin/stories/new")
    before = (a.count_stories(), a.count_places(), a.snapshot(story), a.place_snapshot(place))
    checked = 0
    for rule in app.url_map.iter_rules():
        if "POST" not in rule.methods or rule.endpoint == "static":
            continue
        path = rule.rule.replace("<slug>", place if rule.rule.startswith("/admin/places") else story).replace("<kind>", "characters")
        assert client.post(path, data={"title": "x"}).status_code == 400, f"{path}: no token"
        assert client.post(path, data={"title": "x", "csrf_token": "wrong"}).status_code == 400, f"{path}: wrong token"
        assert client.post(path, data={"title": "x", "csrf_token": token}, headers={"Origin": "https://evil.example"}).status_code == 400, f"{path}: foreign origin"
        checked += 1
    assert checked >= 12
    assert (a.count_stories(), a.count_places(), a.snapshot(story), a.place_snapshot(place)) == before


@pytest.mark.parametrize("method", ["PUT", "PATCH", "DELETE", "TRACE"])
def test_methods_no_route_accepts_are_405_and_change_nothing(app, method):
    client, _ = a.admin_client(app)
    story, place = a.make_story(), a.make_place()
    before = (a.count_stories(), a.count_places())
    for path in ("/", "/login", "/admin", f"/admin/stories/{story}/delete", f"/admin/places/{place}/delete", "/api/v1/search?q=a", "/favourites/characters/jason-duval"):
        assert client.open(path, method=method).status_code == 405, (method, path)
    assert (a.count_stories(), a.count_places()) == before


def test_a_route_that_does_accept_put_patch_or_delete_would_be_guarded_too():
    """Defence in depth: nothing takes these methods today, but the guard must not depend on that. A throwaway route on a throwaway app proves it."""
    probe = create_app("testing")
    probe.add_url_rule("/__method_probe", "method_probe", lambda: "done", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
    client = probe.test_client()
    token = h.token(client, "/login")
    for method in ("POST", "PUT", "PATCH", "DELETE"):
        assert client.open("/__method_probe", method=method).status_code == 400, f"{method} without a token"
        assert client.open("/__method_probe", method=method, headers={"X-CSRF-Token": "nope"}).status_code == 400, f"{method} with a wrong token"
        assert client.open("/__method_probe", method=method, headers={"X-CSRF-Token": token, "Origin": "https://evil.example"}).status_code == 400, f"{method} from another site"
        assert client.open("/__method_probe", method=method, headers={"X-CSRF-Token": token}).status_code == 200, f"{method} with the token"
    for method in ("GET", "HEAD", "OPTIONS"):
        assert client.open("/__method_probe", method=method).status_code == 200, f"{method} is safe and needs no token"


def test_options_is_answered_with_allow_and_changes_nothing(app):
    client, _ = a.admin_client(app)
    story = a.make_story()
    before = (a.count_stories(), a.snapshot(story))
    response = client.options(f"/admin/stories/{story}/delete")
    assert response.status_code == 200 and set(response.headers["Allow"].replace(" ", "").split(",")) >= {"GET", "POST", "HEAD", "OPTIONS"}
    assert (a.count_stories(), a.snapshot(story)) == before
