"""The dashboard's numbers equal what the database says. The expected values come from separate, plain SQL run through the guarded test connection, so this
checks the aggregate queries (GROUP BY, UNION ALL, JOIN with ORDER BY and LIMIT, NOT EXISTS) rather than repeating them. *_test database only."""
import pytest

from app.repositories import admin_stats
from tests import account_helpers as h
from tests import admin_helpers as a
from tests.admin_helpers import clean_stories  # noqa: F401  (a fixture)

pytestmark = pytest.mark.usefixtures("clean_accounts", "clean_stories")


def favourite(name, slug):
    h.execute("INSERT INTO favourite_missions (user_id, mission_id) SELECT u.user_id, m.mission_id FROM users u, missions m WHERE u.username = %s AND m.slug = %s", (name, slug))


def test_row_counts_match_each_table(app):
    with app.app_context():
        counted = {row["name"]: row["n"] for row in admin_stats.table_counts()}
    assert set(counted) == set(admin_stats.COUNTED_TABLES)
    for table, n in counted.items():
        assert n == h.rows(f"SELECT COUNT(*) AS n FROM {table}")[0]["n"], table


def test_stories_by_label_and_type_match_a_plain_count(app):
    a.make_story(status="fan")
    a.make_story(status="demo")
    with app.app_context():
        grouped = {(r["content_status"], r["mission_type"]): r["n"] for r in admin_stats.stories_by_status_and_type()}
    for (status, kind), n in grouped.items():
        assert n == h.rows("SELECT COUNT(*) AS n FROM missions WHERE content_status = %s AND mission_type = %s", (status, kind))[0]["n"]
    assert sum(grouped.values()) == a.count_stories()


def test_accounts_by_role_and_favourites_by_kind(app):
    _client, name = a.admin_client(app)
    slug = a.make_story()
    favourite(name, slug)
    with app.app_context():
        roles = {r["role"]: r["n"] for r in admin_stats.users_by_role()}
        kinds = {r["kind"]: r["n"] for r in admin_stats.favourites_by_kind()}
    assert roles.get("admin", 0) == h.rows("SELECT COUNT(*) AS n FROM users WHERE role = 'admin'")[0]["n"] >= 1
    assert kinds["stories"] == h.rows("SELECT COUNT(*) AS n FROM favourite_missions")[0]["n"] >= 1
    assert kinds["characters"] == h.rows("SELECT COUNT(*) AS n FROM favourite_characters")[0]["n"]


def test_the_most_saved_stories_are_ordered_by_how_many_users_saved_them(app):
    popular, quiet = a.make_story(title="TT Popular " + a.new_slug()), a.make_story(title="TT Quiet " + a.new_slug())
    names = [h.signed_in_client(app)[1] for _ in range(3)]
    for name in names:
        favourite(name, popular)
    favourite(names[0], quiet)
    with app.app_context():
        top = admin_stats.top_favourited_stories(50)
    order = [row["slug"] for row in top]
    assert order.index(popular) < order.index(quiet)
    assert {row["slug"]: row["saved"] for row in top}[popular] == 3 and {row["slug"]: row["saved"] for row in top}[quiet] == 1


def test_stories_without_links_lists_only_stories_with_no_link_at_all(app):
    bare, linked = a.make_story(), a.make_story(characters=a.CHARACTERS[:1])
    with app.app_context():
        slugs = {row["slug"] for row in admin_stats.stories_without_links(500)}
    assert bare in slugs and linked not in slugs


def test_the_dashboard_page_shows_the_numbers(app):
    client, _name = a.admin_client(app)
    page = client.get("/admin").get_data(as_text=True)
    assert page.count("<table") == 4 and "Rows per table" in page and "Most saved stories" in page
    missions = h.rows("SELECT COUNT(*) AS n FROM missions")[0]["n"]
    assert f"<th scope=\"row\">missions</th><td>{missions}</td>" in page
