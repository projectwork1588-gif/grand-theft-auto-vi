"""The Garage as one journey: /vehicles is the cinematic landing, the old prototype address goes there, every machine's Explore action opens its own page,
and each of those pages leads back to the Garage and on to the next machine. Nothing in the site points at the prototype address any more."""
import re

import pytest

SLUGS = ["grotti-cheetah", "vapid-dominator-buggy", "shitzu-squalo", "vapid-stanier", "vapid-ganado", "dinka-enduro", "crest-kayak"]
NAMES = {"grotti-cheetah": "&#39;95 Grotti Cheetah", "vapid-dominator-buggy": "&#39;67 Vapid Dominator Buggy", "shitzu-squalo": "Shitzu Squalo",
         "vapid-stanier": "Vapid Stanier", "vapid-ganado": "Vapid Ganado Retro Build", "dinka-enduro": "Dinka Enduro Motorcycle", "crest-kayak": "Crest Kayak"}


def html(client, path):
    response = client.get(path)
    assert response.status_code == 200, path
    return response.get_data(as_text=True)


# ------------------------------------------------------------------ the old address
@pytest.mark.parametrize("query", ["", "?q=vapid", "?q=vapid&sort=name_desc", "?category=boat", "?per_page=3&page=2", "?sort=category&q=a%26b"])
def test_the_prototype_address_redirects_to_the_garage_and_keeps_its_query(client, query):
    response = client.get("/garage-concept" + query)
    assert response.status_code == 301
    location = response.headers["Location"]
    assert location.endswith("/vehicles" + query) and "garage-concept" not in location


def test_the_redirect_lands_on_the_same_page_as_the_garage(client):
    followed = client.get("/garage-concept?q=kayak", follow_redirects=True)
    assert followed.status_code == 200 and followed.get_data(as_text=True) == html(client, "/vehicles?q=kayak")
    assert client.post("/garage-concept").status_code == 405                       # a read-only route, like the Garage itself


# ------------------------------------------------------------------ the landing is the real Garage
def test_the_garage_is_the_cinematic_landing_and_may_be_indexed(client):
    page = html(client, "/vehicles")
    assert "data-stage" in page and "garage_concept.css" in page and "garage_concept.js" in page
    assert 'name="robots"' not in page and "noindex" not in page
    assert "js/garage.js" not in page                                              # the old opening's script is no longer served


def test_nothing_in_the_site_points_at_the_prototype_address(client):
    paths = ["/", "/about", "/characters", "/vehicles", "/vehicles?q=vapid", "/vehicles?category=boat", "/vehicles?q=zzzz", "/vehicles?per_page=2&page=2"]
    paths += [f"/vehicles/{slug}" for slug in SLUGS]
    for path in paths:
        assert "/garage-concept" not in html(client, path), path


def test_every_link_of_the_filters_stays_on_the_garage(client):
    page = html(client, "/vehicles?q=vapid&sort=name_desc")
    assert "/vehicles#showroom" in re.findall(r'<form[^>]*action="([^"]+)"', page)
    hrefs = re.findall(r'class="gx-catlink"[^>]*href="([^"]+)"', page) + re.findall(r'class="gresult__clear" href="([^"]+)"', page)
    assert hrefs
    for href in hrefs:
        assert href.startswith("/vehicles") and href.endswith("#showroom"), href


# ------------------------------------------------------------------ every machine's way in
def test_every_explore_action_opens_that_machines_page(client):
    stage = html(client, "/vehicles").split("data-stage")[1].split("</section>")[0]
    for slug in SLUGS:
        assert f'<a class="gbtn gx-btn" href="/vehicles/{slug}" aria-label="Explore the {NAMES[slug]}">' in stage, slug
        assert f'href="/vehicles/{slug}" data-pick="{slug}"' in stage, slug
    assert len(re.findall(r'class="gbtn gx-btn"', stage)) == 7


def test_every_link_to_a_machine_from_the_collection_is_a_real_page_with_the_matching_name(client):
    linked = set(re.findall(r'href="/vehicles/([a-z-]+)"', html(client, "/vehicles")))
    assert linked == set(SLUGS)
    for slug in SLUGS:
        detail = html(client, f"/vehicles/{slug}")
        assert f'data-vehicle="{slug}"' in detail
        assert re.search(r"<title>([^<]+)</title>", detail).group(1).startswith(NAMES[slug]), slug      # the page's title is the machine's own name


def test_the_filtered_list_links_each_card_to_its_page(client):
    for query, expected in (("?category=boat", {"shitzu-squalo", "crest-kayak"}), ("?q=vapid", {"vapid-dominator-buggy", "vapid-stanier", "vapid-ganado"})):
        cards = set(re.findall(r'<a class="gx-m [^"]*" href="/vehicles/([a-z-]+)"', html(client, "/vehicles" + query)))
        assert cards == expected, query


# ------------------------------------------------------------------ the way back and on
@pytest.mark.parametrize("slug", SLUGS)
def test_each_page_leads_back_to_the_garage(client, slug):
    page = html(client, f"/vehicles/{slug}")
    assert re.search(r'class="vd-back" href="/vehicles"', page) and 'aria-label="All machines"' in page
    assert re.search(r'class="vd-crumb"[^>]*>\s*<a href="/vehicles">The Garage</a>', page)


def test_previous_and_next_walk_every_machine_and_come_back_round(client):
    seen, slug = [], SLUGS[0]
    for _ in range(7):
        seen.append(slug)
        page = html(client, f"/vehicles/{slug}")
        after = re.search(r'rel="next" data-vehicle="([a-z-]+)"', page).group(1)
        before = re.search(r'rel="prev" data-vehicle="([a-z-]+)"', page).group(1)
        assert after in SLUGS and before in SLUGS and after != slug and before != slug
        slug = after
    assert sorted(seen) == sorted(SLUGS) and slug == SLUGS[0]                      # all seven, once each, and the eighth step is the first again


def test_every_machine_link_on_a_page_leads_to_a_page_that_exists(client):
    for slug in SLUGS:
        for target in set(re.findall(r'href="/vehicles/([a-z-]+)"', html(client, f"/vehicles/{slug}"))):
            assert target in SLUGS, (slug, target)
            assert client.get(f"/vehicles/{target}").status_code == 200


# ------------------------------------------------------------------ the rest of the site
def test_home_and_about_open_the_garage(client):
    assert 'href="/vehicles"' in html(client, "/") and 'href="/vehicles"' in html(client, "/about")


def test_the_menu_marks_the_garage_on_the_landing_and_on_a_machines_page(client):
    for path in ("/vehicles", "/vehicles/crest-kayak"):
        page = html(client, path)
        assert re.search(r'<a[^>]*href="/vehicles"[^>]*aria-current="page"|<a[^>]*aria-current="page"[^>]*href="/vehicles"', page), path


def test_the_other_routes_are_unchanged(client):
    for path in ("/", "/characters", "/characters/jason-duval", "/regions", "/locations", "/missions", "/about", "/credits"):
        assert client.get(path).status_code == 200, path
    assert client.get("/vehicles/not-a-machine").status_code == 404
