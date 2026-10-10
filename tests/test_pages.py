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


def people(text):
    """Character names on the characters page in page order: leads, then the crew, then original characters."""
    return names(text, "duo__name") + names(text, "portrait__name") + names(text, "original__name")


def garage_names(text):
    return re.findall(r'<h2 class="garage-row__name"><a href="[^"]+">([^<]+)</a>', text)


def visible_text(page):
    page = re.sub(r"<(script|style)\b.*?</\1>", "", page, flags=re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", page))


# ------------------------------------------------------------------ homepage
def test_homepage_identity_chapters_and_footer(client):
    page = html(client, "/")
    assert "Welcome, gamers" in page and "Team Valkyrie presents" in page
    assert "<title>Grand Theft Auto VI | Team Valkyrie</title>" in page
    assert 'class="hero__gta">Grand Theft Auto</span>' in page and 'class="hero__vi"' in page
    for heading in ("Two leads, one story", "Eight faces of Leonida", "Six regions, one state", "Machines of the coast",
                    "Tales from the waterfront", "The official trailers", "Leonida is waiting"):
        assert heading in page, heading
    assert "An unofficial educational fan project by Team Valkyrie." in page
    assert "Not affiliated with or endorsed by Rockstar Games or Take-Two Interactive." in page
    assert "Coming<strong>November 19, 2026</strong>" in page
    assert "as stated on" not in page


def test_homepage_content_comes_from_mysql(client):
    page = html(client, "/")
    for expected in ("Jason Duval", "Lucia Caminos", "Brian Heder", "Real Dimez",           # characters
                     "Vice City", "Leonida Keys", "Mount Kalaga",                           # regions
                     "Grotti Cheetah", "Shitzu Squalo", "Vapid Stanier", "Vapid Ganado Retro Build",   # official garage
                     "Ledger of Favours", "Ridge Run", "Last Call at Smokestack Row",         # the three newest stories
                     "Brian Heder</a>"):                                                    # official relationship
        assert expected in page, expected
    assert 'data-video="https://www.rockstargames.com/videoplayer?id=' in page
    assert "Fictional demo" not in page


def test_homepage_official_images_load_remotely_and_lazily(client):
    page = html(client, "/")
    assert page.count("https://www.rockstargames.com/VI/_next/static/media/") > 10
    assert 'fetchpriority="high"' in page and 'loading="lazy"' in page
    assert 'referrerpolicy="no-referrer"' in page
    assert "https://www.rockstargames.com/VI/media/artwork-wallpapers" in page


def test_homepage_without_local_clips_has_no_video_element_and_keeps_the_stills(client):
    page = html(client, "/")
    assert "<video" not in page and "data-reel" not in page
    assert 'data-cast-item' in page and 'class="cast__still"' in page         # the cast still works from official images


def test_homepage_cast_stage_plays_local_loops_when_they_exist(client, local_clips):
    page = html(client, "/")
    assert 'data-reel="/media/clips/leonida-reel.mp4"' in page
    assert 'data-reel-poster="/media/clips/leonida-reel.jpg"' in page
    stage = page.split("<video")[1].split("</video>")[0]
    assert "muted" in stage and "loop" in stage and "playsinline" in stage and 'preload="none"' in stage
    assert "autoplay" not in stage                                          # the script decides, honouring reduced motion
    assert page.count('data-clip="/media/clips/') == 8 and page.count("data-start=") == 8
    assert "data-play-reel" in page and "data-toggle" in page


def test_local_clip_route_serves_only_built_loops(client, local_clips):
    ok = client.get("/media/clips/jason-duval.mp4")
    assert ok.status_code == 200 and ok.headers["Content-Type"].startswith("video/mp4")
    assert client.get("/media/clips/jason-duval.jpg").status_code == 200
    for path in ("/media/clips/nope.mp4", "/media/clips/manifest.json", "/media/clips/jason-duval.exe",
                 "/media/clips/../clips/jason-duval.mp4", "/media/clips/%2e%2e/secret.mp4", "/media/jason-duval.mp4",
                 "/media/clips/JASON-DUVAL.mp4", "/media/clips/sub/jason-duval.mp4"):
        assert client.get(path).status_code == 404, path


def test_local_clip_route_is_empty_without_built_loops(client):
    assert client.get("/media/clips/jason-duval.mp4").status_code == 404


# ------------------------------------------------------------------ list pages render
@pytest.mark.parametrize("path,heading", [
    ("/characters", "The people of Leonida"), ("/vehicles", "Machines of Leonida"), ("/regions", "Six regions, one state"),
    ("/locations", "Places of Leonida"), ("/missions", "Tales from Leonida"),
])
def test_catalogue_pages_render(client, path, heading):
    page = html(client, path)
    assert f"<h1>{heading}</h1>" in page
    assert 'aria-current="page"' in page  # the nav marks where you are
    assert "An unofficial educational fan project" in page


# ------------------------------------------------------------------ characters
def test_characters_page_is_editorial_when_unfiltered(client):
    page = html(client, "/characters")
    assert names(page, "duo__name") == ["Jason Duval", "Lucia Caminos"]
    assert names(page, "portrait__name") == ["Boobie Ike", "Brian Heder", "Cal Hampton", "Dre&#39;Quan Priest",
                                             "Raul Bautista", "Real Dimez"]
    assert names(page, "original__name") == ["Delia Marsh", "Nico Brandt", "Tomas Reyes-Hall"]
    assert "Original characters" in page and "not part of Rockstar's game" in page


def test_characters_search_filter_sort_pagination(client):
    assert len(people(html(client, "/characters"))) == 11
    assert names(html(client, "/characters?q=lucia"), "portrait__name") == ["Lucia Caminos"]
    assert names(html(client, "/characters?q=gator"), "portrait__name") == ["Tomas Reyes-Hall"]
    demo = html(client, "/characters?status=demo")
    assert sorted(names(demo, "portrait__name")) == ["Delia Marsh", "Nico Brandt", "Tomas Reyes-Hall"]
    assert "badge--demo" in demo and ">Concept<" in demo
    assert names(html(client, "/characters?region=vice-city"), "portrait__name") == ["Delia Marsh"]
    assert names(html(client, "/characters?sort=name_desc&per_page=2"), "portrait__name") == ["Tomas Reyes-Hall", "Real Dimez"]
    page2 = html(client, "/characters?per_page=4&page=2&status=official")
    assert 'aria-label="Pagination"' in page2 and 'rel="prev"' in page2 and 'rel="next"' not in page2
    assert "status=official" in page2  # filters survive in the pager links
    assert "5&ndash;8 of 8" in page2
    assert ">Official<" in html(client, "/characters?status=official")


def test_characters_filters_are_reflected_in_the_form(client):
    page = html(client, "/characters?q=lucia&status=official&sort=name_desc")
    assert 'value="lucia"' in page
    assert '<option value="official" selected>' in page and '<option value="name_desc" selected>' in page


def test_characters_empty_state_and_page_beyond_end(client):
    assert "No one by that name" in html(client, "/characters?q=zzzzzz")
    assert "No one by that name" in html(client, "/characters?page=99")


def test_character_detail_official_profile(client):
    page = html(client, "/characters/jason-duval")
    assert "<h1>Jason Duval</h1>" in page and "badge--official" in page
    assert "https://www.rockstargames.com/VI/only-in-leonida" in page            # source link
    assert 'href="/characters/brian-heder"' in page and 'href="/characters/lucia-caminos"' in page
    assert "Gallery" in page and "data-lightbox" in page
    assert "We do not invent" not in page and "No missions stored" not in page      # empty sections are simply left out


def test_character_detail_demo_profile_with_related_content(client):
    page = html(client, "/characters/delia-marsh")
    assert "badge--demo" in page and "Concept" in page and "A Team Valkyrie original." in page
    assert 'href="/missions/harbour-lights"' in page and 'href="/locations/bayfront-studio-lot"' in page
    assert "Seen alongside" in page and "Nico Brandt" in page and "3 shared stories" in page
    assert "Gallery" not in page  # no official media for original characters


def test_character_detail_leaves_out_what_is_not_known(client):
    page = html(client, "/characters/cal-hampton")
    assert "Not stated" not in page and "None stated" not in page and "Known as" not in page


def test_character_profile_links_to_the_official_clip_without_local_files(client):
    page = html(client, "/characters/brian-heder")
    assert "In motion" in page and 'class="clip-link"' in page and "<video" not in page
    assert "https://www.rockstargames.com/VI/media/videos" in page
    assert "In motion" not in html(client, "/characters/delia-marsh")      # concept characters have no clip


def test_character_profile_plays_the_local_loop_when_it_exists(client, local_clips):
    page = html(client, "/characters/brian-heder")
    assert 'data-src="/media/clips/brian-heder.mp4"' in page and "data-loop" in page and "muted" in page
    assert 'poster="/media/clips/brian-heder.jpg"' in page and "data-loop-toggle" in page
    assert "<source" not in page and ' src="/media/clips/' not in page      # nothing loads until the script asks


# ------------------------------------------------------------------ vehicles
def test_garage_shows_only_official_vehicles_with_official_images(client):
    page = html(client, "/vehicles")
    assert garage_names(page) == ["&#39;95 Grotti Cheetah", "&#39;67 Vapid Dominator Buggy", "Shitzu Squalo",
                                  "Vapid Stanier", "Vapid Ganado Retro Build"]
    for concept in ("Corvina GT", "Bruiser V8", "Meridian Sedan", "Swampfox Airboat", "Tidewalker Skiff", "Zephyr 250"):
        assert concept not in page, concept            # concept vehicles are not in the public garage
    assert "badge--demo" not in page and "Fictional demo" not in page and "vehicles.svg" not in page
    assert page.count("rockstargames.com/VI/_next/static/media/") >= 5 and "ULTIMATE_EDITION_GROTTI_CHEETAH" in page
    assert page.count('class="garage-row ') == 5 and "product" not in page.lower()


def test_garage_filters_search_sorting_and_pagination(client):
    listed = lambda path: garage_names(html(client, path))
    assert listed("/vehicles?category=boat") == ["Shitzu Squalo"]
    assert listed("/vehicles?category=motorcycle") == []                      # empty categories give an empty state, not an error
    assert "Nothing in this category yet" in html(client, "/vehicles?category=motorcycle")
    assert listed("/vehicles?q=stanier") == ["Vapid Stanier"]
    assert listed("/vehicles?q=vapid&sort=name_desc") == ["Vapid Stanier", "Vapid Ganado Retro Build", "&#39;67 Vapid Dominator Buggy"]
    assert listed("/vehicles?status=demo") == listed("/vehicles")             # the public garage ignores attempts to list concept vehicles
    two = html(client, "/vehicles?per_page=2&page=2")
    assert 'aria-label="Pagination"' in two and 'rel="prev"' in two and 'rel="next"' in two
    page = html(client, "/vehicles")
    for chip in ("Sports", "Off-road", "Boats", "Sedans", "Muscle"):
        assert f">{chip} <small>1</small>" in page, chip
    assert "Motorcycles" not in page                                         # no official motorcycle, so no empty chip


def test_official_vehicle_detail_page(client):
    page = html(client, "/vehicles/shitzu-squalo")
    assert "<h1>Shitzu Squalo</h1>" in page and "badge--official" in page
    assert "https://www.rockstargames.com/VI/editions" in page                # source link
    assert "Gallery" in page and page.count("data-lightbox") == 4
    assert "More from the garage" in page and 'href="/vehicles/vapid-stanier"' in page
    assert "ULTIMATE_EDITION_SQUALO_01" in page and "Fictional" not in page
    assert "Specifications" not in page                                        # nothing is invented where Rockstar is silent


def test_concept_vehicles_have_no_public_page(client):
    for slug in ("corvina-gt", "swampfox-airboat", "bruiser-v8"):
        response = client.get(f"/vehicles/{slug}")
        assert response.status_code == 404, slug
        assert "not part of the public garage" in response.get_data(as_text=True)
        assert client.get(f"/api/v1/vehicles/{slug}").status_code == 200       # the API still serves the full database


# ------------------------------------------------------------------ regions and locations
def test_regions_page_lists_all_six_official_regions(client):
    page = html(client, "/regions")
    for region in ("Vice City", "Leonida Keys", "Grassrivers", "Port Gellhorn", "Ambrosia", "Mount Kalaga"):
        assert f"<h2>{region}</h2>" in page, region
    assert page.count('class="region-feature') >= 6 and "3 places to explore" in page and "1 place to explore" in page
    assert "in the database" not in page


def test_region_detail_page(client):
    page = html(client, "/regions/vice-city")
    assert "<h1>Vice City</h1>" in page and "https://www.rockstargames.com/VI/only-in-leonida" in page
    assert 'href="/locations/sunset-pier-boardwalk"' in page and 'href="/characters/delia-marsh"' in page
    assert 'href="/missions/ledger-of-favours"' in page and "Elsewhere in Leonida" in page
    assert 'href="/regions/ambrosia"' in page and "Gallery" in page


def test_locations_listing_filters(client):
    assert len(names(html(client, "/locations"), "place__name")) == 8
    assert names(html(client, "/locations?q=marina"), "place__name") == ["Coral Hook Marina"]
    assert len(names(html(client, "/locations?region=vice-city"), "place__name")) == 3
    assert len(names(html(client, "/locations?type=waterfront"), "place__name")) == 3
    assert names(html(client, "/locations?sort=name_desc&per_page=2"), "place__name") == ["Sunset Pier Boardwalk", "Smokestack Row"]
    assert "Rockstar has not published a place-by-place guide" in html(client, "/locations")


def test_location_detail_page_labels_region_artwork_honestly(client):
    page = html(client, "/locations/pelican-quay-terminal")
    assert "badge--demo" in page and "A Team Valkyrie original." in page
    assert "Rockstar artwork of Port Gellhorn, not of this exact place" in page
    assert 'href="/regions/port-gellhorn"' in page and 'href="/missions/harbour-lights"' in page
    assert 'href="/characters/nico-brandt"' in page


# ------------------------------------------------------------------ missions
def test_missions_listing_and_type_filter(client):
    page = html(client, "/missions")
    assert "Original stories from Team Valkyrie" in page and len(names(page, "story__title")) == 5
    assert names(html(client, "/missions?type=heist"), "story__title") == ["Last Call at Smokestack Row"]
    assert names(html(client, "/missions?sort=title_desc&per_page=2"), "story__title") == ["Ridge Run", "Quiet Water"]
    assert "3 characters &middot; 1 vehicle &middot; 2 places" in page


def test_mission_detail_page(client):
    page = html(client, "/missions/harbour-lights")
    assert "<h1>Harbour Lights</h1>" in page and "badge--demo" in page and "Fictional demo" not in page
    assert "A Team Valkyrie original." in page
    assert "Rockstar artwork of Port Gellhorn, not of this story" in page             # captioned region backdrop
    assert 'href="/characters/delia-marsh"' in page and "Arranges the shipment" in page
    assert "Bruiser V8" in page and 'href="/vehicles/bruiser-v8"' not in page         # concept vehicles are named, not linked
    assert 'href="/locations/pelican-quay-terminal"' in page
    assert "More stories" in page and "main setting" in page


# ------------------------------------------------------------------ about and credits
def test_about_page_explains_the_project_and_the_labels(client):
    page = html(client, "/about")
    assert "<h1>A fan guide to Leonida</h1>" in page and 'id="labels"' in page
    for label in ("badge--official", "badge--fan", "badge--demo"):
        assert label in page, label
    assert "Flask" in page and "MySQL" in page                         # the technical note lives here, and only here
    assert 'href="/credits"' in page


def test_credits_page_attributes_rockstar_and_states_the_non_affiliation(client):
    page = html(client, "/credits")
    assert "<h1>Credits and legal</h1>" in page
    assert "not affiliated with, endorsed by or connected to Rockstar Games or Take-Two Interactive" in page
    assert "rockstargames.com/VI" in page and "SIL Open Font License" in page and "MIT licence" in page


def test_footer_is_short_and_has_no_developer_links(client):
    for path in ("/", "/characters", "/about", "/credits"):
        page = html(client, path)
        footer = page.split('<footer class="site-footer">')[1].split("</footer>")[0]
        assert 'href="/about"' in footer and 'href="/credits"' in footer, path
        assert "/api/" not in footer and "/health" not in footer, path
        text = visible_text(footer).lower()
        for word in ("database", "mysql", "api", "health", "flask", "test"):
            assert word not in text, (path, word)
        assert footer.count("unofficial") == 1, path                 # the non-affiliation line appears once


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
    assert len(people(html(client, "/characters"))) == 11  # nothing was damaged


def test_regions_follow_rockstars_order_on_pages_but_the_api_stays_alphabetical(client):
    expected = ["Vice City", "Leonida Keys", "Grassrivers", "Port Gellhorn", "Ambrosia", "Mount Kalaga"]
    page = html(client, "/regions")
    assert re.findall(r"<h2>([^<]+)</h2>", page.split('aria-label="Regions of Leonida"')[1].split("</section>")[0]) == expected
    home = html(client, "/")
    assert re.findall(r'<h3 class="regions__name">([^<]+)</h3>', home) == expected
    api_names = [r["name"] for r in client.get("/api/v1/regions").get_json()["data"]]
    assert api_names == sorted(api_names)  # Phase 1 API behaviour is unchanged


def test_pager_window_helper():
    from app.blueprints.main import page_window
    assert page_window(1, 1) == [1]
    assert page_window(1, 5) == [1, 2, 3, None, 5]
    assert page_window(5, 10) == [1, None, 3, 4, 5, 6, 7, None, 10]
    assert page_window(10, 10) == [1, None, 8, 9, 10]


# ------------------------------------------------------------------ design refinement (Team Valkyrie feedback)
PUBLIC_PAGES = ("/", "/characters", "/characters/jason-duval", "/characters/delia-marsh", "/vehicles", "/vehicles/shitzu-squalo",
                "/regions", "/regions/vice-city", "/locations", "/locations/pelican-quay-terminal", "/missions",
                "/missions/harbour-lights", "/about", "/credits")


def test_hero_is_calm_and_keeps_the_required_identity(client):
    page = html(client, "/")
    hero = page.split('class="hero"')[1].split("</section>")[0]
    assert "Welcome, gamers" in hero and "Team Valkyrie presents" in hero
    assert 'class="hero__gta">Grand Theft Auto</span>' in hero and 'class="hero__vi"' in hero
    assert "as stated on Rockstar" not in page
    assert "Watch the trailer" in hero and "Start exploring" in hero


def test_brand_lockup_is_in_the_header_and_footer(client):
    page = html(client, "/characters")
    assert page.count('class="brand__mark"') == 2 and page.count("Fan guide by Team Valkyrie") == 2
    assert 'class="nav-cta"' in page and "/#media" in page


def test_labels_are_calm_and_blunt_wording_is_gone_everywhere(client):
    for path in PUBLIC_PAGES:
        page = html(client, path)
        assert "Fictional demo" not in page and "fictional demo" not in page, path
        assert "notice--demo" not in page and "invented by Team Valkyrie to demonstrate" not in page.lower(), path


def test_public_pages_read_like_a_site_not_a_test_report(client):
    """No database explanations, test terminology or defensive provenance repeated on every page."""
    banned = ("in the database", "from the database", "stored for", "No missions stored", "We do not invent", "archive",
              "demo data", "sample data", "test data", "placeholder", "lorem", "Counted from")
    for path in PUBLIC_PAGES:
        text = visible_text(html(client, path))
        for phrase in banned:
            assert phrase.lower() not in text.lower(), (path, phrase)
        if path != "/about":
            assert "MySQL" not in text and "Flask" not in text, path
        assert "API" not in text and "health check" not in text.lower(), path


def test_pages_use_no_inline_styles_or_scripts(client):
    for path in PUBLIC_PAGES:
        page = html(client, path)
        assert ' style="' not in page, path
        assert not re.search(r"<script(?![^>]*\bsrc=)", page), path
        assert not re.search(r"\son[a-z]+=", page), path


def test_homepage_garage_is_a_showroom_of_official_images(client):
    page = html(client, "/")
    garage = page.split('id="garage"')[1].split("</section>")[0]
    track = garage.split('class="showroom__track"')[1]
    assert len(re.findall(r'<a class="slide"', track)) == 5 and "<svg" not in track and "ULTIMATE_EDITION" in track
    assert "Corvina" not in garage
    assert "data-showroom-prev" in garage and "data-showroom-next" in garage and "data-showroom-progress" in garage


def test_homepage_regions_are_an_explorer_not_six_columns(client):
    page = html(client, "/")
    regions = page.split('id="leonida"')[1].split("</section>")[0]
    assert regions.count("data-region-view=") == 6 and regions.count("data-region-tab=") == 6
    assert 'class="regions__stage"' in regions and 'class="regions__tabs"' in regions
    assert regions.count("rockstargames.com/VI/_next/static/media/") >= 6        # every region shows official artwork


def test_homepage_leads_are_two_matched_panels(client):
    page = html(client, "/")
    leads = page.split('id="leads"')[1].split("</section>")[0]
    assert names(leads, "duo__name") == ["Jason Duval", "Lucia Caminos"]
    assert leads.count('class="duo__panel') == 2 and leads.count('class="media duo__media"') == 2


def test_media_section_uses_official_posters_and_the_official_player(client):
    page = html(client, "/")
    media = page.split('id="media"')[1].split("</section>")[0]
    assert media.count('class="video-card"') == 3 and "GTAVI_Trailer2_poster" in media
    assert 'class="mosaic"' in media and media.count("data-lightbox") >= 4
    assert "clip-card" not in page                       # the old row of eight small clip thumbnails is gone


def test_closing_band_replaces_the_plain_statistics_block(client):
    page = html(client, "/")
    assert "Leonida is waiting" in page and 'class="stat-row"' not in page and "The archive in numbers" not in page


def test_catalogue_pages_have_cinematic_official_backdrops(client):
    for path, fragment in (("/characters", "Jason_and_Lucia_Motel"), ("/vehicles", "GROTTI_CHEETAH_02"), ("/regions", "Vice_City_10"),
                           ("/locations", "Port_Gellhorn_06"), ("/missions", "Vice_City_11")):
        assert fragment in html(client, path), path
