"""Favourites: save, list and remove for characters, vehicles, places and stories; ownership; duplicates; foreign keys; persistence; failures.
Runs against the real *_test MySQL database (see tests/account_helpers.py: every database touch first proves the name ends in _test)."""
import mysql.connector
import pytest

from app.repositories import favourites as repo
from tests import account_helpers as h

pytestmark = pytest.mark.usefixtures("clean_accounts")

# One public record of every kind, and one the public pages do not show (a fan/demo character or vehicle).
KINDS = {
    "characters": ("jason-duval", "Jason Duval", "character_id"),
    "vehicles": ("grotti-cheetah", "Cheetah", "vehicle_id"),
    "locations": ("bayfront-studio-lot", "Bayfront", "location_id"),
    "missions": ("harbour-lights", "Harbour", "mission_id"),
}
EVERY_KIND = pytest.mark.parametrize("kind", list(KINDS))


def entity_id(kind, slug):
    table = {"characters": "characters", "vehicles": "vehicles", "locations": "locations", "missions": "missions"}[kind]
    return h.rows(f"SELECT {KINDS[kind][2]} AS id FROM {table} WHERE slug = %s", (slug,))[0]["id"]


def save(client, kind, slug, **extra):
    return h.post(client, f"/favourites/{kind}/{slug}", extra, token_from="/account/favourites")


def remove(client, kind, slug, **extra):
    return h.post(client, f"/favourites/{kind}/{slug}/remove", extra, token_from="/account/favourites")


# ------------------------------------------------------------------ the control on each page
@EVERY_KIND
def test_a_signed_out_visitor_is_offered_sign_in_and_gets_no_cookie_or_form(client, kind):
    slug = KINDS[kind][0]
    response = client.get(f"/{kind}/{slug}")
    page = response.get_data(as_text=True)
    assert response.status_code == 200 and "Sign in to save" in page and 'href="/login"' in page
    assert f"/favourites/{kind}/{slug}" not in page and "Set-Cookie" not in response.headers


@EVERY_KIND
def test_a_signed_in_visitor_sees_save_then_saved_on_the_page(app, kind):
    slug = KINDS[kind][0]
    client, _ = h.signed_in_client(app)
    page = client.get(f"/{kind}/{slug}").get_data(as_text=True)
    assert f'action="/favourites/{kind}/{slug}"' in page and 'data-saved="false"' in page and 'aria-pressed="false"' in page
    assert save(client, kind, slug).status_code == 303
    page = client.get(f"/{kind}/{slug}").get_data(as_text=True)
    assert f'action="/favourites/{kind}/{slug}/remove"' in page and 'data-saved="true"' in page and 'aria-pressed="true"' in page


# ------------------------------------------------------------------ add, list, remove
@EVERY_KIND
def test_save_list_and_remove(app, kind):
    slug, label, column = KINDS[kind]
    client, name = h.signed_in_client(app)
    response = save(client, kind, slug)
    assert response.status_code == 303 and response.headers["Location"] == f"/{kind}/{slug}"
    assert h.favourites_of(name)[kind] == {entity_id(kind, slug)}
    listing = client.get("/account/favourites").get_data(as_text=True)
    assert f'href="/{kind}/{slug}"' in listing and f'action="/favourites/{kind}/{slug}/remove"' in listing
    assert remove(client, kind, slug).status_code == 303
    assert h.count_favourites(name) == 0
    assert f'href="/{kind}/{slug}"' not in client.get("/account/favourites").get_data(as_text=True)


@EVERY_KIND
def test_the_saved_message_is_shown_once_after_saving(app, kind):
    slug = KINDS[kind][0]
    client, _ = h.signed_in_client(app)
    save(client, kind, slug)
    first = client.get(f"/{kind}/{slug}").get_data(as_text=True)
    assert 'class="flash flash--success"' in first and "saved to your favourites" in first
    assert "saved to your favourites" not in client.get(f"/{kind}/{slug}").get_data(as_text=True)


def test_a_saved_record_of_each_kind_is_listed_under_its_own_heading(app):
    client, name = h.signed_in_client(app)
    for kind, (slug, _label, _column) in KINDS.items():
        save(client, kind, slug)
    assert h.count_favourites(name) == 4
    page = client.get("/account/favourites").get_data(as_text=True)
    for heading in ("Characters", "Vehicles", "Places", "Stories"):
        assert heading in page
    assert "4 saved" in page and "Nothing saved yet" not in page


def test_an_empty_list_says_so(app):
    client, _ = h.signed_in_client(app)
    page = client.get("/account/favourites").get_data(as_text=True)
    assert "Nothing saved yet" in page and page.count("No ") >= 4


@EVERY_KIND
def test_saving_twice_is_harmless_and_stores_one_row(app, kind):
    slug = KINDS[kind][0]
    client, name = h.signed_in_client(app)
    assert save(client, kind, slug).status_code == 303 and save(client, kind, slug).status_code == 303
    assert len(h.favourites_of(name)[kind]) == 1


def test_removing_something_not_saved_changes_nothing(app):
    client, name = h.signed_in_client(app)
    save(client, "characters", "jason-duval")
    assert remove(client, "vehicles", "grotti-cheetah").status_code == 303
    assert h.count_favourites(name) == 1


def test_the_return_field_only_ever_chooses_between_two_fixed_destinations(app):
    client, _ = h.signed_in_client(app)
    assert save(client, "characters", "jason-duval", **{"return": "list"}).headers["Location"] == "/account/favourites"
    for hostile in ("https://evil.example/", "//evil.example", "/account/password", "javascript:alert(1)"):
        response = save(client, "characters", "jason-duval", **{"return": hostile})
        assert response.headers["Location"] == "/characters/jason-duval", hostile
    assert remove(client, "characters", "jason-duval", **{"return": "list"}).headers["Location"] == "/account/favourites"


# ------------------------------------------------------------------ who may do what
@EVERY_KIND
def test_signed_out_requests_are_sent_to_sign_in_and_store_nothing(app, kind):
    slug = KINDS[kind][0]
    client = app.test_client()
    for path in (f"/favourites/{kind}/{slug}", f"/favourites/{kind}/{slug}/remove"):
        response = h.post(client, path, {})
        assert response.status_code == 303 and response.headers["Location"].endswith("/login")
    assert client.get("/account/favourites").status_code == 303
    assert h.rows("SELECT COUNT(*) AS n FROM users u JOIN " + {"characters": "favourite_characters", "vehicles": "favourite_vehicles", "locations": "favourite_locations", "missions": "favourite_missions"}[kind] + " f ON f.user_id = u.user_id")[0]["n"] == 0


def test_each_user_sees_and_changes_only_their_own_favourites(app):
    alice, alice_name = h.signed_in_client(app)
    bob, bob_name = h.signed_in_client(app)
    save(alice, "characters", "jason-duval")
    save(alice, "vehicles", "grotti-cheetah")
    assert h.count_favourites(bob_name) == 0
    assert "jason-duval" not in bob.get("/account/favourites").get_data(as_text=True)
    assert 'data-saved="false"' in bob.get("/characters/jason-duval").get_data(as_text=True)
    # Bob "removes" Alice's favourite: the DELETE is always scoped to Bob, so Alice keeps hers.
    assert remove(bob, "characters", "jason-duval").status_code == 303
    assert h.count_favourites(alice_name) == 2


def test_a_forged_user_id_in_the_form_is_ignored(app):
    alice, alice_name = h.signed_in_client(app)
    bob, bob_name = h.signed_in_client(app)
    alice_id = h.user_row(alice_name)["user_id"]
    save(bob, "characters", "jason-duval", user_id=str(alice_id), username=alice_name)
    assert h.count_favourites(alice_name) == 0 and h.count_favourites(bob_name) == 1
    save(alice, "vehicles", "grotti-cheetah")
    remove(bob, "vehicles", "grotti-cheetah", user_id=str(alice_id))
    assert h.count_favourites(alice_name) == 1


def test_no_route_takes_a_user_id():
    from app import create_app
    app = create_app("testing")
    for rule in app.url_map.iter_rules():
        if rule.endpoint.startswith("account."):
            assert not any("user" in argument for argument in rule.arguments), rule.rule


def test_the_csrf_token_is_required_for_saving_and_removing(app):
    client, name = h.signed_in_client(app)
    assert client.post("/favourites/characters/jason-duval").status_code == 400
    assert client.post("/favourites/characters/jason-duval", data={"csrf_token": "forged"}).status_code == 400
    assert h.count_favourites(name) == 0
    save(client, "characters", "jason-duval")
    assert client.post("/favourites/characters/jason-duval/remove").status_code == 400
    assert h.count_favourites(name) == 1


# ------------------------------------------------------------------ which records, which addresses
@pytest.mark.parametrize("path", [
    "/favourites/people/jason-duval",                 # not a kind
    "/favourites/characters/no-such-person",         # no such record
    "/favourites/characters/Jason-Duval",            # not a lower-case slug
    "/favourites/characters/delia-marsh",            # a fan/demo character: not on the public pages, so not savable
    "/favourites/vehicles/corvina-gt",               # a demo vehicle: not part of the public garage
    "/favourites/characters/jason-duval'--",
    "/favourites/characters/1%20OR%201=1",
    "/favourites/locations/x;DROP%20TABLE%20users",
])
def test_unknown_or_unpublished_records_are_404_and_store_nothing(app, path):
    client, name = h.signed_in_client(app)
    assert h.post(client, path, {}, token_from="/account/favourites").status_code == 404
    assert h.post(client, path + "/remove", {}, token_from="/account/favourites").status_code == 404
    assert h.count_favourites(name) == 0
    assert h.rows("SELECT 1 FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = 'users'")


def test_a_record_removed_between_the_lookup_and_the_insert_is_a_404_not_a_crash(app, monkeypatch):
    client, name = h.signed_in_client(app)
    monkeypatch.setattr(repo, "find_public", lambda kind, slug: {"id": 99999999, "name": "Gone"})
    assert save(client, "characters", "jason-duval").status_code == 404                      # the foreign key refused it (error 1216 or 1452)
    assert h.count_favourites(name) == 0


def test_the_database_itself_refuses_a_favourite_for_nothing_or_nobody(app):
    client, name = h.signed_in_client(app)
    user_id = h.user_row(name)["user_id"]
    with pytest.raises(mysql.connector.IntegrityError) as missing_entity:
        h.execute("INSERT INTO favourite_characters (user_id, character_id) VALUES (%s, 99999999)", (user_id,))
    with pytest.raises(mysql.connector.IntegrityError) as missing_user:
        h.execute("INSERT INTO favourite_characters (user_id, character_id) VALUES (99999999, 1)")
    assert missing_entity.value.errno in (1216, 1452) and missing_user.value.errno in (1216, 1452)


def test_the_composite_primary_key_blocks_a_duplicate_pair(app):
    client, name = h.signed_in_client(app)
    save(client, "characters", "jason-duval")
    user_id, character_id = h.user_row(name)["user_id"], entity_id("characters", "jason-duval")
    with pytest.raises(mysql.connector.IntegrityError) as duplicate:
        h.execute("INSERT INTO favourite_characters (user_id, character_id) VALUES (%s, %s)", (user_id, character_id))
    assert duplicate.value.errno == 1062


def test_deleting_an_account_deletes_its_favourites_and_nothing_else(app):
    first, first_name = h.signed_in_client(app)
    second, second_name = h.signed_in_client(app)
    save(first, "characters", "jason-duval")
    save(second, "characters", "jason-duval")
    h.execute("DELETE FROM users WHERE username = %s", (first_name,))
    assert h.count_favourites(first_name) == 0 and h.count_favourites(second_name) == 1
    assert h.rows("SELECT COUNT(*) AS n FROM characters WHERE slug = 'jason-duval'")[0]["n"] == 1


# ------------------------------------------------------------------ persistence
def test_favourites_survive_a_refresh_logout_and_a_later_login(app):
    client, name = h.signed_in_client(app)
    for kind, (slug, _label, _column) in KINDS.items():
        save(client, kind, slug)
    client.get("/account/favourites")                                                    # the first view also shows (and uses up) the one-time "saved" message
    before = client.get("/account/favourites").get_data(as_text=True)
    assert client.get("/account/favourites").get_data(as_text=True) == before            # a refresh shows exactly the same list
    h.logout(client)
    again = app.test_client()                                                            # a different browser, later
    assert h.login(again, name).status_code == 303
    after = again.get("/account/favourites").get_data(as_text=True)
    for kind, (slug, _label, _column) in KINDS.items():
        assert f'href="/{kind}/{slug}"' in after
    assert h.count_favourites(name) == 4


def test_a_saved_record_shows_as_saved_on_its_page_after_signing_in_again(app):
    client, name = h.signed_in_client(app)
    save(client, "vehicles", "grotti-cheetah")
    h.logout(client)
    h.login(client, name)
    assert 'data-saved="true"' in client.get("/vehicles/grotti-cheetah").get_data(as_text=True)


# ------------------------------------------------------------------ safe output and failures
def test_names_on_the_favourites_page_are_escaped(app, monkeypatch):
    client, _ = h.signed_in_client(app)
    monkeypatch.setattr(repo, "list_for_user", lambda kind, user_id: [{"slug": "x", "name": '<script>alert(1)</script><img src=x onerror=alert(2)>', "saved_at": None}] if kind == "characters" else [])
    page = client.get("/account/favourites").get_data(as_text=True)
    assert "<script>alert(1)</script>" not in page and "&lt;script&gt;alert(1)&lt;/script&gt;" in page and "<img src=x" not in page


def test_a_database_failure_while_saving_is_a_generic_503_and_stores_nothing(app, monkeypatch):
    client, name = h.signed_in_client(app)

    def broken(*args, **kwargs):
        raise mysql.connector.Error("boom: internal detail")
    monkeypatch.setattr(repo, "add", broken)
    response = save(client, "characters", "jason-duval")
    assert response.status_code == 503 and "internal detail" not in response.get_data(as_text=True)
    assert h.count_favourites(name) == 0


def test_a_failure_before_the_commit_rolls_the_favourite_back(app, monkeypatch):
    from contextlib import contextmanager
    from app.db import transaction

    @contextmanager
    def fails_before_commit():
        with transaction() as cursor:
            yield cursor
            raise mysql.connector.Error("failure just before the commit")
    client, name = h.signed_in_client(app)
    monkeypatch.setattr(repo, "transaction", fails_before_commit)
    assert save(client, "characters", "jason-duval").status_code == 503
    assert h.count_favourites(name) == 0


def test_the_kind_table_and_column_names_come_only_from_the_fixed_map():
    assert set(repo.KINDS) == {"characters", "vehicles", "locations", "missions"}
    columns = {"characters": "character_id", "vehicles": "vehicle_id", "locations": "location_id", "missions": "mission_id"}
    for kind, (table, column, entity, label, public, endpoint, single) in repo.KINDS.items():
        assert table == f"favourite_{kind}" and column == columns[kind] and entity == kind
        assert all(part.replace("_", "").isalnum() for part in (table, column, entity, label))      # plain identifiers only
