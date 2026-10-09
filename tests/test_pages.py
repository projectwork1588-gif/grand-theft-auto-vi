"""Server-rendered pages, backed by real MySQL data. Each page must show database content, labels and working links."""
import re

import pytest


def html(client, path, status=200):
    response = client.get(path)
    assert response.status_code == status, f"{path} -> {response.status_code}"
    return response.get_data(as_text=True)


def names(text, cls):
    """Text of elements with a given class, in page order (templates keep these on one line)."""
    return re.findall(rf'class="{cls}[^"]*">([^<]+)<', text)


# ------------------------------------------------------------------ homepage
def test_homepage_identity_sections_and_disclaimer(client):
    page = html(client, "/")
    assert "Welcome, gamers" in page and "Team Valkyrie presents" in page
    assert "<title>Grand Theft Auto VI | Team Valkyrie</title>" in page
    assert "Grand Theft Auto" in page and 'class="hero__vi"' in page
    for heading in ("The people of Leonida", "Six regions, one state", "Wheels, hulls and handlebars",
                    "Follow the links", "See it for yourself", "The archive in numbers"):
        assert heading in page, heading
    assert "An unofficial educational fan project by Team Valkyrie. Not affiliated with, endorsed by" in page
    assert "Coming November 19, 2026" in page


def test_homepage_content_comes_from_mysql(client):
    page = html(client, "/")
    for expected in ("Jason Duval", "Lucia Caminos", "Brian Heder", "Real Dimez",           # characters
                     "Vice City", "Leonida Keys", "Mount Kalaga",                           # regions
                     "Corvina GT", "Bruiser V8", "Meridian Sedan", "Ridgeback 4x4",         # one vehicle per category
                     "Ledger of Favours", "Ridge Run", "Last Call at Smokestack Row",         # the three newest stories
                     "Brian Heder</a>"):                                                    # official relationship
        assert expected in page, expected
    assert 'data-video="https://www.rockstargames.com/videoplayer?id=' in page
    assert "Fictional demo" in page and "Official" in page


def test_homepage_official_images_load_remotely_and_lazily(client):
    page = html(client, "/")
    assert page.count("https://www.rockstargames.com/VI/_next/static/media/") > 10
    assert 'fetchpriority="high"' in page and 'loading="lazy"' in page
    assert 'referrerpolicy="no-referrer"' in page
    assert "https://www.rockstargames.com/VI/media/artwork-wallpapers" in page


# ------------------------------------------------------------------ list pages render
@pytest.mark.parametrize("path,heading", [
    ("/characters", "Characters"), ("/vehicles", "Garage"), ("/regions", "Leonida"),
    ("/locations", "Locations"), ("/missions", "Stories"),
])
def test_catalogue_pages_render(client, path, heading):
    page = html(client, path)
    assert f"<h1>{heading}</h1>" in page
    assert 'aria-current="page"' in page  # the nav marks where you are
    assert "An unofficial educational fan project" in page


# ------------------------------------------------------------------ characters
def test_characters_search_filter_sort_pagination(client):
    everyone = names(html(client, "/characters"), "poster__name")
    assert len(everyone) == 11 and everyone[0] == "Boobie Ike"
    assert names(html(client, "/characters?q=lucia"), "poster__name") == ["Lucia Caminos"]
    assert names(html(client, "/characters?q=gator"), "poster__name") == ["Tomas Reyes-Hall"]
    demo = html(client, "/characters?status=demo")
    assert sorted(names(demo, "poster__name")) == ["Delia Marsh", "Nico Brandt", "Tomas Reyes-Hall"]
    assert names(html(client, "/characters?region=vice-city"), "poster__name") == ["Delia Marsh"]
    assert names(html(client, "/characters?sort=name_desc&per_page=2"), "poster__name") == ["Tomas Reyes-Hall", "Real Dimez"]
    page2 = html(client, "/characters?per_page=4&page=2&status=official")
    assert 'aria-label="Pagination"' in page2 and 'rel="prev"' in page2 and 'rel="next"' not in page2
    assert "status=official" in page2  # filters survive in the pager links
    assert "Showing 5&ndash;8 of 8" in page2


def test_characters_filters_are_reflected_in_the_form(client):
    page = html(client, "/characters?q=lucia&status=official&sort=name_desc")
    assert 'value="lucia"' in page
    assert '<option value="official" selected>' in page and '<option value="name_desc" selected>' in page


def test_characters_empty_state_and_page_beyond_end(client):
    assert "No characters found" in html(client, "/characters?q=zzzzzz")
    assert "No characters found" in html(client, "/characters?page=99")


def test_character_detail_official_profile(client):
    page = html(client, "/characters/jason-duval")
    assert "<h1>Jason Duval</h1>" in page and "badge--official" in page
    assert "https://www.rockstargames.com/VI/only-in-leonida" in page            # source link
    assert 'href="/characters/brian-heder"' in page and 'href="/characters/lucia-caminos"' in page
    assert "We do not invent story for real GTA VI characters." in page         # honest empty state
    assert "Official images" in page and "data-lightbox" in page


def test_character_detail_demo_profile_with_related_content(client):
    page = html(client, "/characters/delia-marsh")
    assert "badge--demo" in page and "Fictional demo record" in page
    assert 'href="/missions/harbour-lights"' in page and 'href="/locations/bayfront-studio-lot"' in page
    assert "Seen alongside" in page and "Nico Brandt" in page and "3 shared missions" in page
    assert "Official images" not in page  # no official media for fictional characters


def test_character_detail_handles_missing_information(client):
    page = html(client, "/characters/cal-hampton")
    assert "Not stated" in page and "None stated" in page


# ------------------------------------------------------------------ vehicles
def test_garage_listing_filters_and_labels(client):
    page = html(client, "/vehicles")
    assert "Fictional demo vehicles" in page and "badge--demo" in page
    assert len(names(page, "bay-row__name")) == 8
    boats = html(client, "/vehicles?category=boat")
    assert sorted(names(boats, "bay-row__name")) == ["Swampfox Airboat", "Tidewalker Skiff"]
    assert 'aria-current="true"' in boats
    assert names(html(client, "/vehicles?q=zephyr"), "bay-row__name") == ["Zephyr 250"]
    assert names(html(client, "/vehicles?sort=name_desc&per_page=2"), "bay-row__name") == ["Zephyr 250", "Tidewalker Skiff"]
    assert 'aria-label="Pagination"' in html(client, "/vehicles?per_page=3")


def test_vehicle_detail_page(client):
    page = html(client, "/vehicles/swampfox-airboat")
    assert "<h1>Swampfox Airboat</h1>" in page and "Fictional demo vehicle" in page
    assert 'href="/missions/quiet-water"' in page and 'href="/locations/heron-reach-dock"' in page
    assert 'href="/vehicles/tidewalker-skiff"' in page and "vehicles.svg#boat" in page
    assert "no performance figures" in page


# ------------------------------------------------------------------ regions and locations
def test_regions_page_lists_all_six_official_regions(client):
    page = html(client, "/regions")
    for region in ("Vice City", "Leonida Keys", "Grassrivers", "Port Gellhorn", "Ambrosia", "Mount Kalaga"):
        assert f"<h2>{region}</h2>" in page, region
    assert page.count("badge--official") == 6
    assert "3 locations in the database" in page and "1 location in the database" in page


def test_region_detail_page(client):
    page = html(client, "/regions/vice-city")
    assert "<h1>Vice City</h1>" in page and "https://www.rockstargames.com/VI/only-in-leonida" in page
    assert 'href="/locations/sunset-pier-boardwalk"' in page and 'href="/characters/delia-marsh"' in page
    assert 'href="/missions/ledger-of-favours"' in page and "Elsewhere in Leonida" in page
    assert 'href="/regions/ambrosia"' in page and "Official images" in page


def test_locations_listing_filters(client):
    assert len(names(html(client, "/locations"), "index-row__name")) == 8
    assert names(html(client, "/locations?q=marina"), "index-row__name") == ["Coral Hook Marina"]
    assert len(names(html(client, "/locations?region=vice-city"), "index-row__name")) == 3
    assert len(names(html(client, "/locations?type=waterfront"), "index-row__name")) == 3
    assert names(html(client, "/locations?sort=name_desc&per_page=2"), "index-row__name") == ["Sunset Pier Boardwalk", "Smokestack Row"]
    assert "fictional demo records" in html(client, "/locations")


def test_location_detail_page_labels_region_artwork_honestly(client):
    page = html(client, "/locations/pelican-quay-terminal")
    assert "Fictional demo location" in page and "official artwork of Port Gellhorn, not of this place" in page
    assert 'href="/regions/port-gellhorn"' in page and 'href="/missions/harbour-lights"' in page
    assert 'href="/characters/nico-brandt"' in page


# ------------------------------------------------------------------ missions
def test_missions_listing_and_type_filter(client):
    page = html(client, "/missions")
    assert "Fictional demo stories" in page and len(names(page, "dossier__title")) == 5
    assert names(html(client, "/missions?type=heist"), "dossier__title") == ["Last Call at Smokestack Row"]
    assert names(html(client, "/missions?sort=title_desc&per_page=2"), "dossier__title") == ["Ridge Run", "Quiet Water"]
    assert "3 characters &middot; 1 vehicles &middot; 2 locations" in page


def test_mission_detail_page(client):
    page = html(client, "/missions/harbour-lights")
    assert "<h1>Harbour Lights</h1>" in page and "Fictional demo story" in page
    assert 'href="/characters/delia-marsh"' in page and "Arranges the shipment" in page
    assert 'href="/vehicles/bruiser-v8"' in page and 'href="/locations/pelican-quay-terminal"' in page
    assert "Related stories" in page and "2 shared links" in page and "main setting" in page


# ------------------------------------------------------------------ invalid input and routes
@pytest.mark.parametrize("path", [
    "/characters?status=bogus", "/characters?sort=password", "/characters?page=0", "/characters?q=" + "x" * 81,
    "/vehicles?sort=price", "/vehicles?category=Bad Slug", "/missions?type=raid", "/locations?type=castle",
    "/locations?region=NOT-A-SLUG", "/regions?status=maybe",
])
def test_invalid_parameters_give_a_styled_400_page(client, path):
    response = client.get(path)
    page = response.get_data(as_text=True)
    assert response.status_code == 400 and "text/html" in response.content_type
    assert "Bad request" in page and "Back to the homepage" in page and 'class="link-list error-details"' in page


@pytest.mark.parametrize("path", [
    "/characters/nobody", "/vehicles/nothing", "/regions/atlantis", "/locations/nowhere", "/missions/none",
    "/characters/Jason-Duval", "/characters/jason_duval", "/characters/" + "a" * 300, "/characters/%2e%2e%2f", "/nope",
])
def test_unknown_routes_and_slugs_give_a_styled_404_page(client, path):
    response = client.get(path)
    assert response.status_code == 404 and "text/html" in response.content_type
    assert "Not Found" in response.get_data(as_text=True)


def test_malformed_search_text_is_safe(client):
    for payload in ("' OR '1'='1", "'; DROP TABLE characters; --", "%", "_", "<script>alert(1)</script>", "‮", "a%00b"):
        for path in ("/characters", "/vehicles", "/missions", "/locations"):
            response = client.get(path, query_string={"q": payload})
            assert response.status_code in (200, 400), (path, payload)
    assert len(names(html(client, "/characters"), "poster__name")) == 11  # nothing was damaged


def test_regions_follow_rockstars_order_on_pages_but_the_api_stays_alphabetical(client):
    expected = ["Vice City", "Leonida Keys", "Grassrivers", "Port Gellhorn", "Ambrosia", "Mount Kalaga"]
    page = html(client, "/regions")
    assert re.findall(r"<h2>([^<]+)</h2>", page.split('aria-label="Regions of Leonida"')[1].split("</section>")[0]) == expected
    home = html(client, "/")
    assert re.findall(r'class="region-panel__name display">([^<]+)<', home) == expected
    api_names = [r["name"] for r in client.get("/api/v1/regions").get_json()["data"]]
    assert api_names == sorted(api_names)  # Phase 1 API behaviour is unchanged


def test_pager_window_helper():
    from app.blueprints.main import page_window
    assert page_window(1, 1) == [1]
    assert page_window(1, 5) == [1, 2, 3, None, 5]
    assert page_window(5, 10) == [1, None, 3, 4, 5, 6, 7, None, 10]
    assert page_window(10, 10) == [1, None, 8, 9, 10]
