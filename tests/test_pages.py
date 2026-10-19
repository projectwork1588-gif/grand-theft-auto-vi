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
    """Names on the editorial Characters page in page order: the two leads, then the six around them."""
    return re.findall(r'<h[34] class="(?:spread|person)__name"><a href="[^"]+">([^<]+)</a>', text)


def results(text):
    """Names in the Explore results list, in order."""
    return re.findall(r'class="result__name">([^<]+)<', text)


def garage_names(text):
    """The machines the Garage landing names, in page order: a stage's or a card's name (the whole collection is told in chapters, so its order is the chapters')."""
    return re.findall(r'<h3 class="gx-(?:m|f)__name">([^<]+)</h3>', text)


def garage_links(text):
    return re.findall(r'<a class="gx-(?:f|d|m) [^"]*" href="/vehicles/([a-z-]+)"', text)


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


def _cast_section(page):
    return page.split('id="cast"')[1].split("</section>")[0]


def test_homepage_cast_stage_plays_local_loops_when_they_exist(client, local_clips):
    page = html(client, "/")
    assert 'data-reel="/media/clips/leonida-reel.mp4"' in page
    assert 'data-reel-poster="/media/clips/leonida-reel.jpg"' in page
    stage = page.split("<video")[1].split("</video>")[0]
    assert "muted" in stage and "loop" in stage and "playsinline" in stage and 'preload="none"' in stage
    assert "autoplay" not in stage                                          # the script decides, honouring reduced motion
    cast = _cast_section(page)
    assert "data-clip" not in cast and cast.count("data-start=") == 8      # one reel, seeked by time, not eight files


def test_cast_reel_has_no_control_buttons_and_keeps_the_list(client, local_clips):
    """The reel runs by itself: no Play whole reel, Pause or Replay buttons, and the name list stays on the right."""
    cast = _cast_section(html(client, "/"))
    assert "cast__controls" not in cast and "data-play-reel" not in cast and "data-toggle" not in cast
    assert "Play whole reel" not in cast and "Replay" not in cast
    assert cast.count("data-cast-item") == 8 and 'class="cast__list"' in cast
    assert 'data-reel="/media/clips/leonida-reel.mp4"' in cast and "data-video-stage" in cast


def test_cast_script_runs_the_reel_by_itself_and_jumps_on_a_name():
    from pathlib import Path
    script = (Path(__file__).resolve().parent.parent / "app" / "static" / "js" / "site.js").read_text(encoding="utf-8")
    cast_code = script.split("function castStage()")[1].split("function cinemas()")[0]
    assert 'state.mode = "reel"' in cast_code and 'state.mode = "single"' not in cast_code   # always the whole reel
    assert "video.loop = state.mode ===" in cast_code and "startReel()" in cast_code          # it starts itself and loops
    assert "begin(seg.start)" in cast_code                                                    # a name jumps to that person


def test_cast_playlist_uses_one_explicit_order_not_database_order(client, local_clips):
    from app import media_slots
    cast = _cast_section(html(client, "/"))
    listed = re.findall(r'data-cast-item[^>]*data-slug="([a-z-]+)"', cast)
    assert listed == list(media_slots.CAST_ORDER)
    starts = [float(x) for x in re.findall(r'data-start="([0-9.]+)"', cast)]
    assert starts == sorted(starts) and len(starts) == 8                         # reel segments run in the same order


def test_cast_order_is_stable_when_the_database_returns_rows_differently(client, monkeypatch):
    from app import media_slots
    from app.repositories import characters as characters_repo
    original = characters_repo.featured_official
    monkeypatch.setattr(characters_repo, "featured_official", lambda limit=8: list(reversed(original(limit))))
    cast = _cast_section(html(client, "/"))
    assert re.findall(r'data-cast-item[^>]*data-slug="([a-z-]+)"', cast) == list(media_slots.CAST_ORDER)


def test_loop_builder_cuts_the_reel_in_the_same_order():
    from app import media_slots
    from scripts import make_loops
    slugs = [make_loops.SLUGS[stem][0] for stem in make_loops.SEQUENCE]
    assert slugs == list(media_slots.CAST_ORDER)


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
    assert re.search(rf"<h1[^>]*>{heading}</h1>", page)
    assert 'aria-current="page"' in page  # the nav marks where you are
    assert "An unofficial educational fan project" in page


# ------------------------------------------------------------------ characters
EIGHT = ["Jason Duval", "Lucia Caminos", "Cal Hampton", "Brian Heder", "Boobie Ike", "Dre&#39;Quan Priest", "Real Dimez",
         "Raul Bautista"]
ORIGINALS = ("Delia Marsh", "Nico Brandt", "Tomas Reyes-Hall")


def test_characters_page_is_editorial_when_unfiltered(client):
    page = html(client, "/characters")
    assert sorted(people(page)) == sorted(EIGHT)
    assert people(page)[:2] == ["Jason Duval", "Lucia Caminos"]               # the leads come first
    assert 'class="cast-open"' in page and 'class="tier"' in page and 'class="web"' in page
    assert page.index('class="cast-open"') < page.index('class="cast-nav"') < page.index('id="leads-title"') < page.index('id="crew-title"') < page.index('id="web-title"')
    assert 'class="results"' not in page                                       # the Explore results are a separate mode
    for name in ORIGINALS:                                                    # original characters are not part of the cast
        assert name not in page, name
    assert "/characters/delia-marsh" not in page and "Original characters" not in page


def test_jump_navigation_reaches_all_eight_people(client):
    page = html(client, "/characters")
    nav = page.split('data-cast-nav')[1].split("</nav>")[0]
    for slug in ("jason-duval", "lucia-caminos", "cal-hampton", "brian-heder", "boobie-ike", "dre-quan-priest", "real-dimez", "raul-bautista"):
        assert f'href="#{slug}"' in nav, slug
        assert f'id="{slug}"' in page, slug
    assert 'aria-label="Jump to a character"' in page and "data-open-explore" in nav


def test_explore_panel_is_secondary_and_closed_on_the_landing(client):
    page = html(client, "/characters")
    panel = page.split('<details class="explore"')[1].split("</details>")[0]
    assert not panel.startswith(' id="explore" open') and 'role="search"' in panel
    assert 'name="q"' in panel and 'name="region"' in panel and 'name="sort"' in panel and 'name="status"' not in panel
    for option in ("Name A to Z", "Name Z to A", "Newest first", "Vice City", "Leonida Keys"):
        assert option in panel, option


def test_characters_search_filter_sort_pagination(client):
    assert results(html(client, "/characters?q=lucia")) == ["Lucia Caminos"]
    assert results(html(client, "/characters?q=gator")) == []                       # an original character's alias finds nothing
    assert results(html(client, "/characters?region=vice-city")) == ["Boobie Ike"]
    assert results(html(client, "/characters?region=leonida-keys")) == ["Jason Duval", "Brian Heder"]      # the cast order
    assert results(html(client, "/characters?sort=name_desc&per_page=2")) == ["Real Dimez", "Raul Bautista"]
    everyone = results(html(client, "/characters?sort=name_asc&per_page=50"))
    assert len(everyone) == 8 and everyone[0] == "Boobie Ike"
    assert results(html(client, "/characters?sort=cast&per_page=50")) == EIGHT
    page2 = html(client, "/characters?per_page=3&page=3&sort=name_asc")
    assert 'aria-label="Pagination"' in page2 and 'rel="prev"' in page2 and 'rel="next"' not in page2
    assert "sort=name_asc" in page2                                           # filters survive in the pager links
    assert "7&ndash;8 of 8" in page2


def test_a_status_in_the_query_never_exposes_original_characters(client):
    for qs in ("?status=demo", "?status=official", "?include=original", "?q=delia", "?q=nico&status=demo"):
        page = html(client, "/characters" + qs)
        for name in ORIGINALS:
            assert name not in page, (qs, name)
        assert "/characters/delia-marsh" not in page and "/characters/tomas-reyes-hall" not in page, qs


def test_characters_filters_are_reflected_in_the_form(client):
    page = html(client, "/characters?q=lucia&region=vice-city&sort=name_desc")
    assert 'value="lucia"' in page
    assert '<option value="vice-city" selected>' in page and '<option value="name_desc" selected>' in page


def test_characters_empty_state_and_page_beyond_end(client):
    assert "No one by that name" in html(client, "/characters?q=zzzzzz")
    assert "No one by that name" in html(client, "/characters?q=lucia&page=99")
    page = html(client, "/characters?region=grassrivers")
    assert "Nobody is tied to that region yet" in page and "Jason and Brian in the Keys, Boobie in Vice City" in page


def test_character_detail_official_profile(client):
    page = html(client, "/characters/jason-duval")
    assert "<h1>Jason Duval</h1>" in page and "01 / 08" in page
    assert "https://www.rockstargames.com/VI/only-in-leonida" in page            # source link
    connections = page.split('class="p-connections"')[1].split("</section>")[0]
    assert 'href="/characters/brian-heder"' in connections and 'href="/characters/lucia-caminos"' in connections
    assert 'href="/characters/cal-hampton"' in connections
    assert 'href="/regions/leonida-keys"' in page                               # where Rockstar places him
    assert "From the footage and artwork" in page and "data-lightbox" in page
    assert "We do not invent" not in page and "No missions stored" not in page      # empty sections are simply left out
    nav = page.split('aria-label="All eight characters"')[1].split("</nav>")[0]
    assert nav.count('<li><a href="/characters/') == 8 and 'aria-current="page"' in nav


def test_every_official_profile_renders_with_its_connections_and_navigation(client):
    for number, slug in enumerate(("jason-duval", "lucia-caminos", "cal-hampton", "brian-heder", "boobie-ike", "dre-quan-priest",
                                   "real-dimez", "raul-bautista"), start=1):
        page = html(client, f"/characters/{slug}")
        assert f"{number:02d} / 08" in page, slug
        assert 'class="p-hero' in page and 'class="p-story' in page and 'class="p-next"' in page, slug
        assert 'rel="prev"' in page and 'rel="next"' in page, slug
        assert 'class="p-conn' in page or "has not stated any connections" in page, slug


def test_dre_quan_and_real_dimez_are_connected_on_both_profiles(client):
    dre = html(client, "/characters/dre-quan-priest").split('class="p-connections"')[1].split("</section>")[0]
    dimez = html(client, "/characters/real-dimez").split('class="p-connections"')[1].split("</section>")[0]
    assert 'href="/characters/real-dimez"' in dre and 'href="/characters/dre-quan-priest"' in dimez
    assert "Only Raw Records" in dre and "Only Raw Records" in dimez


def test_the_network_is_drawn_from_the_relationship_table(client, app_context):
    from app.repositories import characters as repo
    page = html(client, "/characters")
    svg = page.split('data-network')[1].split('class="web__list"')[0]
    rows = repo.official_relationships(limit=50)
    assert len(rows) == 5 and page.count('<g class="edge"') == 5
    for row in rows:
        assert f'data-from="{row["from_slug"]}" data-to="{row["to_slug"]}"' in svg, row
    assert len(re.findall(r'<a class="node[ "]', svg)) == 8 and "node--alone" in svg                   # Raul has no stated connection yet
    assert svg.count('class="av ') + svg.count('class="av"') == 8 and svg.count("av__ring") == 9      # eight portraits, the duo has two circles
    assert "Raul Bautista has no stated connection yet" in page


def test_original_character_profiles_are_not_public(client):
    for slug in ("delia-marsh", "nico-brandt", "tomas-reyes-hall"):
        response = client.get(f"/characters/{slug}")
        assert response.status_code == 404 and "text/html" in response.content_type, slug
        assert "Not Found" in response.get_data(as_text=True)


def test_character_detail_leaves_out_what_is_not_known(client):
    page = html(client, "/characters/cal-hampton")
    assert "Not stated" not in page and "None stated" not in page and "Known as" not in page


def test_character_profile_links_to_the_official_clip_without_local_files(client):
    page = html(client, "/characters/brian-heder")
    assert 'class="p-clip-link"' in page and "<video" not in page
    assert "https://www.rockstargames.com/VI/media/videos" in page
    assert "Watch Brian Heder" in page


def test_character_profile_plays_the_local_portrait_once_when_it_exists(client, local_clips):
    page = html(client, "/characters/brian-heder")
    assert re.search(r'data-portrait-video data-poster-at="[0-9.]+" data-src="/media/clips/brian-heder.mp4"', page) and "muted" in page
    assert "motion-portrait--legacy" in page                                         # only the older composite exists here
    assert 'poster="/media/clips/brian-heder.jpg"' in page and "data-motion-optin" in page
    # the still is its own picture under the clip, so a loaded video can never show its black first frame
    assert 'class="motion-portrait__poster" src="/media/clips/brian-heder.jpg"' in page
    assert " loop" not in page.split("data-portrait-video")[1].split("</video>")[0]        # Rockstar's clips are never looped
    video = page.split("<video")[1].split("</video>")[0]
    assert "<source" not in page and " src=" not in video.split(">")[0]                # the clip loads only when the script asks
    assert "p-clip-link" not in page


def test_landing_portraits_are_wired_for_the_motion_policy(client, local_clips):
    page = html(client, "/characters")
    assert page.count("data-portrait-video") == 8 and page.count("data-motion-optin") == 8
    assert 'preload="none"' in page and ' autoplay' not in page


# ------------------------------------------------------------------ vehicles
def test_garage_shows_only_official_vehicles_with_official_images(client):
    page = html(client, "/vehicles")
    assert sorted(garage_links(page)) == sorted(["grotti-cheetah", "vapid-dominator-buggy", "shitzu-squalo", "vapid-stanier", "vapid-ganado", "dinka-enduro", "crest-kayak"])
    for concept in ("Corvina GT", "Bruiser V8", "Meridian Sedan", "Swampfox Airboat", "Tidewalker Skiff", "Zephyr 250"):
        assert concept not in page, concept            # concept vehicles are not in the public garage
    assert "badge--demo" not in page and "Fictional demo" not in page and "vehicles.svg" not in page
    assert page.count("rockstargames.com/VI/_next/static/media/") >= 7 and "ULTIMATE_EDITION_GROTTI_CHEETAH" in page
    assert len(garage_links(page)) == 7 and "product" not in page.lower()


def test_garage_filters_search_sorting_and_pagination(client):
    listed = lambda path: garage_names(html(client, path))
    assert listed("/vehicles?category=boat") == ["Squalo", "Kayak"]
    assert listed("/vehicles?category=muscle") == ["Ganado Retro Build"]
    assert "No machine matches that" in html(client, "/vehicles?q=nothingatall")
    assert listed("/vehicles?q=stanier") == ["Stanier"]
    assert listed("/vehicles?q=vapid&sort=name_desc") == ["Stanier", "Ganado Retro Build", "Dominator Buggy"]
    assert listed("/vehicles?status=demo") == listed("/vehicles")             # the public garage ignores attempts to list concept vehicles
    two = html(client, "/vehicles?per_page=2&page=2")
    assert 'aria-label="Pagination"' in two and 'rel="prev"' in two and 'rel="next"' in two
    page = html(client, "/vehicles")
    for chip in ("Sports", "Off-road", "Sedans", "Muscle"):
        assert f">{chip}<small>1</small>" in page, chip
    assert ">Boats<small>2</small>" in page and ">Motorcycles<small>1</small>" in page


def test_official_vehicle_detail_page(client):
    page = html(client, "/vehicles/shitzu-squalo")
    assert '<h1 class="plate vd-plate">' in page and "badge--official" not in page
    assert "https://www.rockstargames.com/VI/editions" in page                # source link
    assert page.count("data-lightbox") == 3                                    # the four pictures, less the one that opens the page
    assert 'href="/vehicles/vapid-stanier"' in page and "All machines" in page
    assert "ULTIMATE_EDITION_SQUALO_01" in page and "Fictional" not in page
    assert not re.search(r"horsepower|top speed|0-60|mph|km/h|bhp", page, re.I)      # and nothing is invented


def test_concept_vehicles_have_no_public_page(client):
    for slug in ("corvina-gt", "swampfox-airboat", "bruiser-v8"):
        response = client.get(f"/vehicles/{slug}")
        assert response.status_code == 404, slug
        assert "not part of the public garage" in response.get_data(as_text=True)
        assert client.get(f"/api/v1/vehicles/{slug}").status_code == 200       # the API still serves the full database


# ------------------------------------------------------------------ regions and locations
def test_regions_page_lists_all_six_official_regions(client):
    page = html(client, "/regions")
    features = re.findall(r'<h2 class="rg-title rg-title--feature" id="f-[a-z-]+">([^<]+)</h2>', page)
    assert features == ["Vice City", "Leonida Keys", "Grassrivers", "Port Gellhorn", "Ambrosia", "Mount Kalaga"]
    assert page.count('class="rgf rgf--') == 6 and "place to explore" not in page and "places to explore" not in page    # the invented places are no part of Leonida here
    assert "in the database" not in page


def test_region_detail_page(client):
    page = html(client, "/regions/vice-city")
    assert re.search(r'<h1 class="rg-title">Vice City</h1>', page) and "https://www.rockstargames.com/VI/only-in-leonida" in page
    assert 'href="/characters/boobie-ike"' in page and 'href="/characters/delia-marsh"' not in page      # original characters are not placed here
    assert 'href="/locations/' not in page and 'href="/missions/' not in page                          # invented places and stories are not presented as Vice City
    assert 'href="/regions/leonida-keys"' in page and 'rel="prev"' in page and re.search(r"Rockstar(?:&rsquo;|&#39;|')s own pictures", page)


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
    assert 'href="/characters/nico-brandt"' not in page                                # an original character is named, not linked
    assert "Nico Brandt" in page and "Original character" in page


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
    assert 'href="/characters/delia-marsh"' not in page and "Delia Marsh" in page and "Arranges the shipment" in page
    assert "Original character" in page                                               # named, clearly identified, not linked
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
    "/characters?sort=password", "/characters?region=NOT-A-SLUG", "/characters?page=0", "/characters?q=" + "x" * 81,
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
    assert len(people(html(client, "/characters"))) == 8   # nothing was damaged


def test_regions_follow_rockstars_order_on_pages_but_the_api_stays_alphabetical(client):
    expected = ["Vice City", "Leonida Keys", "Grassrivers", "Port Gellhorn", "Ambrosia", "Mount Kalaga"]
    page = html(client, "/regions")
    assert re.findall(r'<h2 class="rg-title rg-title--feature" id="f-[a-z-]+">([^<]+)</h2>', page) == expected
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
PUBLIC_PAGES = ("/", "/characters", "/characters/jason-duval", "/characters/cal-hampton", "/vehicles", "/vehicles/shitzu-squalo",
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
    assert page.count('class="brand__emblem"') == 2 and page.count('class="brand__title">Team Valkyrie<') == 2
    assert page.count('<span class="brand__sub">Grand Theft Auto VI</span>') == 2
    assert "fan guide" not in page.split('id="main"')[0].lower().replace("a fan-made guide", "")   # no small "fan guide" wording
    assert 'class="header-pill"' in page and "/#media" in page


def test_menu_lists_every_section_and_the_project_pages(client):
    page = html(client, "/characters")
    menu = page.split('id="site-menu"')[1].split("</nav>")[0]
    for label in ("Characters", "Garage", "Leonida", "Locations", "Stories", "About the project", "Credits and legal", "Watch the trailers"):
        assert label in menu, label
    assert 'aria-current="page"' in menu and "Not affiliated with" in menu
    assert 'aria-controls="site-menu"' in page and 'aria-expanded="false"' in page
    assert "/static/img/emblem.svg" in page and "/static/img/favicon.svg" in page and "css/tokens.css" in page


def test_header_has_inline_navigation_with_the_current_section_marked(client):
    page = html(client, "/vehicles")
    header = page.split('class="header-nav"')[1].split("</nav>")[0]
    for label in ("Characters", "Garage", "Leonida", "Locations", "Stories"):
        assert f">{label}</a>" in header, label
    assert header.count('aria-current="page"') == 1 and '<a href="/vehicles" aria-current="page">Garage</a>' in header
    # one primary navigation landmark for assistive technology: the overlay menu has its own label
    assert page.count('aria-label="Primary"') == 1 and 'aria-label="Site menu"' in page


def test_emblem_and_favicon_are_served(client):
    for name in ("emblem.svg", "favicon.svg"):
        response = client.get(f"/static/img/{name}")
        assert response.status_code == 200 and "svg" in response.headers["Content-Type"]


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
    track = garage.split('class="showroom__track"')[1].split("</ul>")[0]
    assert len(re.findall(r'<a class="slide"', track)) == 5 and "<svg" not in track and "ULTIMATE_EDITION" in track
    assert "Corvina" not in garage
    assert "data-showroom-prev" in garage and "data-showroom-next" in garage and "data-showroom-progress" in garage


def test_homepage_regions_are_an_explorer_not_six_columns(client):
    page = html(client, "/")
    regions = page.split('id="leonida"')[1].split("</section>")[0]
    assert regions.count("data-region-view=") == 6 and regions.count("data-region-tab=") == 6
    assert 'class="regions__stage"' in regions and 'class="regions__tabs"' in regions
    assert regions.count("rockstargames.com/VI/_next/static/media/") >= 6        # every region shows official artwork


def test_homepage_leads_are_two_matched_cards(client):
    page = html(client, "/")
    leads = page.split('id="leads"')[1].split("</section>")[0]
    assert names(leads, "key-card__title") == ["Jason Duval", "Lucia Caminos"]
    assert leads.count('class="key-card leads__card') == 2 and leads.count('class="key-card__eyebrow"') == 2
    assert leads.count('<span class="pill">Read the profile</span>') == 2
    assert 'href="/characters/jason-duval"' in leads and 'href="/characters/lucia-caminos"' in leads


def test_media_section_uses_official_posters_and_the_official_player(client):
    page = html(client, "/")
    media = page.split('id="media"')[1].split("</section>")[0]
    assert media.count('class="video-card"') == 3 and "GTAVI_Trailer2_poster" in media
    assert 'class="bento"' in media and media.count("data-lightbox") >= 4
    assert "clip-card" not in page                       # the old row of eight small clip thumbnails is gone


def test_closing_band_replaces_the_plain_statistics_block(client):
    page = html(client, "/")
    assert "Leonida is waiting" in page and 'class="stat-row"' not in page and "The archive in numbers" not in page


def test_catalogue_pages_have_cinematic_official_backdrops(client):
    for path, fragment in (("/characters", "Jason_and_Lucia_Beach_landscape"), ("/vehicles", "GROTTI_CHEETAH_02"), ("/regions", "Vice_City_10"),
                           ("/locations", "Port_Gellhorn_06"), ("/missions", "Vice_City_11")):
        assert fragment in html(client, path), path


# ------------------------------------------------------------------ round 3: type, the signature moment, media, stories
def _css():
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent / "app" / "static" / "css"
    return {p.name: p.read_text(encoding="utf-8") for p in root.glob("*.css")}


def _script():
    from pathlib import Path
    return (Path(__file__).resolve().parent.parent / "app" / "static" / "js" / "site.js").read_text(encoding="utf-8")


def test_no_serif_or_italic_type_anywhere():
    from pathlib import Path
    for name, text in _css().items():
        assert "Newsreader" not in text and "font-serif" not in text, name
        assert "font-style: italic" not in text and "font-style:italic" not in text, name
    fonts = Path(__file__).resolve().parent.parent / "app" / "static" / "fonts"
    assert not [f.name for f in fonts.iterdir() if "newsreader" in f.name.lower()]


def test_no_text_is_set_below_the_readable_floor():
    for name, text in _css().items():
        for declaration in re.findall(r"font(?:-size)?:\s*[^;{}]*", text):
            for size in re.findall(r"(?<![\d.])(0?\.\d+)rem", declaration):
                assert float(size) >= 0.7, (name, declaration)


def test_subtitles_use_the_sans_subtitle_class(client):
    page = html(client, "/")
    assert 'class="serif"' not in page and 'class="subtitle"' in page


def test_copy_names_jason_and_lucia_as_the_two_leads(client):
    page = html(client, "/")
    assert "Jason Duval and Lucia Caminos are the two leads of Grand Theft Auto VI." in page
    assert "playable protagonists" not in page and "first two" not in page


def test_first_cinematic_moment_sits_between_the_leads_and_the_cast(client):
    page = html(client, "/")
    assert page.index('id="leads"') < page.index('id="moment"') < page.index('id="cast"')
    moment = page.split('id="moment"')[1].split("</section>")[0]
    assert not re.search(r"<h[1-6]", moment) and "<button" not in moment           # the picture only: no heading, no buttons
    assert "<iframe" not in page.split("<dialog")[0] and "youtube" not in moment.lower().replace("rockstar", "")
    assert "cinema__poster" in moment and "rockstargames.com/VI/_next/static/media/" in moment   # an official still
    assert "Rockstar Games" not in moment and "Watch Official Trailer" not in moment            # no credit or link on top
    assert "<video" not in moment and "data-cinema-video" not in moment           # no native video until it is built
    assert 'id="world"' not in page and 'id="finale"' not in page                 # the other two need their own video


def test_policy_allows_only_the_trailer_frame_and_no_third_party_scripts(client):
    csp = client.get("/").headers["Content-Security-Policy"]
    assert "frame-src https://www.rockstargames.com https://www.youtube-nocookie.com;" in csp
    assert "script-src 'self';" in csp and "youtube.com;" not in csp.split("script-src")[1].split(";")[0]
    assert "unsafe-inline" not in csp and "unsafe-eval" not in csp
    assert "img-src 'self' https://www.rockstargames.com data:;" in csp and "media-src 'self';" in csp


def test_first_moment_needs_a_real_still_and_a_real_trailer(monkeypatch, client):
    from app import media_slots, media_urls
    assert media_urls.youtube_id("QdBZY2fkU-0") == "QdBZY2fkU-0"
    for bad in (None, "", "short", "x" * 12, 'QdBZY2fkU-0"><script>', "../../etc/passwd"):
        assert media_urls.youtube_id(bad) is None, bad
    monkeypatch.setitem(media_slots.CINEMATICS["moment-1"], "trailer", "no-such-video")
    assert 'id="moment"' not in html(client, "/")                                  # nothing to play: the section is left out


def test_cinematic_slots_match_the_files_the_builder_writes():
    from app import local_media, media_slots
    from scripts import make_cinematics
    assert tuple(media_slots.CINEMATICS) == local_media.CINEMATIC_SLOTS == tuple(make_cinematics.MOMENTS)
    first = media_slots.CINEMATICS["moment-1"]
    assert first["trailer"] in media_slots.VIDEO_SLUGS and first["poster"] in media_slots.VIDEO_POSTER_SLUGS
    for slot in media_slots.CINEMATICS.values():
        assert slot["trailer"] in media_slots.VIDEO_SLUGS and slot["title"]


def test_script_plays_one_moment_at_a_time_silently_and_obeys_the_motion_policy():
    code = _script().split("function cinemas()")[1].split("function regionExplorer()")[0]
    assert "automatic = function () { return motionAllowed() && !slow; }" in code and "document.hidden" in code
    assert "IntersectionObserver" in code and "0.35" in code                       # muted autoplay at 35 percent in view
    assert "best" in code and "p === best" in code and "tvMedia" in code          # the most visible wins; the reel and overlay count
    assert "p.video.muted = true" in code and "withSound = soundOn && activated()" in code   # silent unless the visitor asked
    assert "toggleSound" in code and "sessionStorage" in code and "ramp(" in code  # the sound button or M, remembered, faded
    assert "p.refused = true" in code and "setMotion(true)" in code                # a refused play() becomes a plain Play button
    assert "window.setInterval" in code and "pageshow" in code and "visibilitychange" in code   # it reconciles; no missed event sticks
    assert "Replay" not in code and '"ended"' not in code                          # it loops: nothing ends, nothing to replay
    assert "createElement" not in code                                              # the buttons are real markup, never built here
    assert "youtube" not in code.lower() and "iframe" not in code.lower()          # no third-party player on the page


def test_motion_policy_is_one_remembered_choice_with_a_server_switch(client):
    script = _script()
    head = script.split("// ---- Header turns solid")[0]
    assert "tv-motion" in head and "function motionAllowed()" in head and "tv:motion" in head
    assert "reduceMotion && !autoplayAlways" in head and "saveData" in head       # the system setting is honoured by default
    assert 'getAttribute("data-autoplay") === "always"' in head
    from app.config import Config
    assert Config.AUTOPLAY_ALWAYS in (True, False)
    page = html(client, "/")
    assert "data-motion-toggle" in page and "data-motion-row" in page            # the menu switch
    assert page.count("data-motion-optin") >= 2                                   # explorer and garage always offer a Play pill


def test_trailers_and_screenshots_are_two_distinct_blocks(client):
    page = html(client, "/")
    media = page.split('id="media"')[1].split("</section>")[0]
    assert 'class="theatre"' in media and media.count("theatre__item--lead") == 1
    assert media.count('class="video-card"') == 3
    gallery = media.split('class="bento"')[1].split("</ul>")[0]
    items = re.findall(r'<li class="bento__item( bento__item--wide)?', gallery)
    assert len(items) == 6 and items[0] and items[-1] and not any(items[1:-1])    # 4-column rows: 2+1+1 and 1+1+2, no gaps
    assert "data-gallery" in media and media.count("data-lightbox") == 6
    assert "mosaic" not in page


def test_lightbox_has_previous_next_and_a_counter(client):
    page = html(client, "/")
    dialog = page.split('id="image-dialog"')[1].split("</dialog>")[0]
    assert "data-lb-prev" in dialog and "data-lb-next" in dialog and "data-count" in dialog


def test_stories_section_separates_team_stories_from_official_connections(client):
    page = html(client, "/")
    stories = page.split('id="stories"')[1].split("</section>")[0]
    assert "story-lead" in stories and stories.count("Team Valkyrie original") >= 3
    assert "story__num" not in stories and "story-list" not in stories              # no numbered database-style list
    aside = stories.split("<aside")[1]
    assert "badge--official" in aside and "Who knows whom" in aside and "Concept" not in aside


def test_chapter_navigation_is_a_quiet_rail_and_a_hairline(client):
    page = html(client, "/")
    assert 'class="chapter-rail"' in page and "data-rail-list" in page and 'class="progress-hairline"' in page
    assert "Jump to" not in page and 'class="waypoint"' not in page              # the floating pill is gone
    for name in ("Welcome", "The leads", "Dawn over Leonida", "The cast", "Leonida", "The garage", "Stories", "Trailers"):
        assert f'data-chapter="{name}"' in page, name
    css = _css()["site.css"]
    assert ".chapter-rail__label" in css and "opacity: 0" in css                  # names only on hover or focus
    code = _script().split("function chapterNav()")[1].split("function castStage()")[0]
    assert "On this page" in code and "aria-current" in code                      # the same list is in the header menu


def test_credits_mention_the_footage_and_only_the_fonts_in_use(client):
    page = html(client, "/credits")
    assert "Trailer 1" in page and "YouTube" in page and "Manrope and Barlow Condensed" in page
    assert "Newsreader" not in page


def test_reel_gives_every_person_a_natural_beat(client, local_clips):
    cast = _cast_section(html(client, "/"))
    starts = [float(x) for x in re.findall(r'data-start="([0-9.]+)"', cast)]
    ends = [float(x) for x in re.findall(r'data-end="([0-9.]+)"', cast)]
    assert len(starts) == len(ends) == 8
    for a, b in zip(starts, ends):
        assert 2.4 <= b - a <= 3.5, (a, b)                                    # about 2.6 to 3.1 seconds each
    assert all(ends[i] <= starts[i + 1] + 0.001 for i in range(7))           # segments are contiguous and ordered


def test_reel_builder_is_natural_speed_with_a_brief_artwork_hold():
    from scripts import make_loops
    assert make_loops.SPEED == 1.0                                               # no slow motion, no interpolation
    assert 1.2 <= make_loops.ART_HOLD <= 2.2 and 0 < make_loops.CLIP_TO_ART <= 0.6
    assert 0 < make_loops.REEL_DISSOLVE <= 0.5
    assert "minterpolate" not in open(make_loops.__file__, encoding="utf-8").read().split("def build_segment")[1]
    for clip_seconds in (1.0, 1.5):                                              # the clips Rockstar publishes
        total = clip_seconds - make_loops.CLIP_TO_ART + make_loops.ART_LEN
        assert 2.4 <= total <= 3.4, total                                        # about 2.6 to 3.1 s per person


def test_locally_built_reel_matches_the_rules_when_it_exists():
    import json
    from pathlib import Path
    from app import media_slots
    path = Path(__file__).resolve().parent.parent / "media" / "clips" / "manifest.json"
    if not path.is_file():
        pytest.skip("loops are not built on this machine")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if "speed" not in manifest:
        pytest.skip("the reel on this machine was built by an older version")
    assert manifest["speed"] == 1.0
    assert [s["slug"] for s in manifest["segments"]] == list(media_slots.CAST_ORDER)
    for seg in manifest["segments"]:
        assert 2.2 <= seg["end"] - seg["start"] <= 3.4, seg
    assert 17 <= manifest["duration"] <= 25


def test_cast_script_seeks_one_buffered_reel_and_holds_a_chosen_person():
    code = _script().split("function castStage()")[1].split("function cinema()")[0]
    assert "video.src = reelSrc" in code and 'video.preload = "auto"' in code     # buffered once, early
    assert "data-clip" not in code                                                # no per-person download on choosing
    assert "HOLD_BEFORE_END" in code and "video.pause()" in code                  # a chosen person plays once, then holds
    assert '"Replay"' in code                                                     # replay is a first-class state


def test_native_moments_are_silent_loops_with_two_small_icon_buttons(client, local_cinematic):
    page = html(client, "/")
    for anchor, slot in (("moment", "moment-1"), ("world", "moment-2"), ("finale", "moment-3")):
        section = page.split(f'id="{anchor}"')[1].split("</section>")[0]
        video = section.split("<video")[1].split(">")[0]
        assert "data-cinema-video" in video and "muted" in video and "playsinline" in video and " loop" in video, slot
        assert 'preload="none"' in video and f'poster="/media/cinematic/{slot}.jpg"' in video, slot
        assert f'<source src="/media/cinematic/{slot}-mobile.mp4" media="(max-width: 700px)"' in section, slot
        assert f'<source src="/media/cinematic/{slot}.mp4" type="video/mp4">' in section, slot
        assert "cinema__bar" not in section and "Rockstar Games" not in section and "Enable sound" not in section, slot
        assert section.count("<button") == 2 and "data-cinema-toggle" in section and "data-cinema-sound" in section, slot   # pause and sound
        assert 'class="cinema__tools" data-cinema-tools hidden' in section, slot    # a speaker and a hidden fallback, shown by the script
    assert page.index('id="leads"') < page.index('id="moment"') < page.index('id="cast"') < page.index('id="world"') < page.index('id="leonida"')
    assert page.index('id="media"') < page.index('id="finale"') < page.index('class="section band closing"')
    assert "<iframe" not in page.split("<dialog")[0]


def test_native_moments_reveal_only_once_playing_and_survive_a_bad_file():
    code = _script().split("function cinemas()")[1].split("function regionExplorer()")[0]
    assert '"playing"' in code and "is-live" in code                              # the poster stays until frames are moving
    assert '"error"' in code and "p.failed = true" in code                        # a broken file leaves the poster
    assert 'p.video.preload = "auto"' in code and "p.video.load()" in code        # nothing downloads until it is wanted


def test_display_titles_use_the_condensed_face_and_body_stays_sans():
    css = _css()
    wanted = {
        "components.css": (".key-card__title",),
        "pages.css": (".hero__vi", ".regions__name", ".cast__name", ".page-hero h1"),
        "garage.css": (".plate__model", ".tile__model", ".neighbour__name"),
    }
    for sheet, selectors in wanted.items():
        for selector in selectors:
            rule = re.search(r"^" + re.escape(selector) + r" \{([^}]*)\}", css[sheet], re.M)
            assert rule, selector
            assert re.search(r"var\(--font-(?:mark|display)\)", rule.group(1)), selector


def test_images_ask_for_what_the_layout_needs(client):
    from app import media_urls
    assert media_urls.IMAGE_WIDTHS[-1] >= 2560
    page = html(client, "/")
    assert "2560w" in page                                                         # high-density screens can get 2560
    leads = page.split('id="leads"')[1].split("</section>")[0]
    assert 'sizes="(min-width: 900px) 67vw, 222vw"' in leads                     # 4:3 and 4:5 crops are sized by height
    assert 'sizes="max(100vw, 178vh)"' in page.split('id="moment"')[1].split("</section>")[0]
    assert 'sizes="(min-width: 760px) 100vw, 180vw"' in page.split('id="top"')[1].split("</section>")[0]


def test_detail_galleries_are_full_width_and_leave_no_empty_cells(client):
    for path, minimum in (("/characters/jason-duval", 2),):
        page = html(client, path)
        assert 'class="container gallery-page"' in page or 'class="p-gallery"' in page, path
        gallery = page.split('class="bento bento--')[1].split("</ul>")[0]
        n = gallery.count('<li class="bento__item')
        wide = gallery.count("bento__item--wide")
        mode = gallery.split('"')[0]
        assert n >= minimum, (path, n)
        if mode == "quad":
            assert n % 6 == 0 and wide == (n // 6) * 2, (path, n, wide)           # whole rows of 2+1+1 and 1+1+2
        elif mode == "five":
            assert n == 5 and wide == 1
        else:
            assert wide == 0
        assert 'class="gallery"' not in page, path


def test_an_explicit_cast_choice_is_never_overridden_by_the_automatic_start():
    """Regression: the first time the stage scrolled into view it restarted the reel over the visitor's choice."""
    code = _script().split("function castStage()")[1].split("function cinema()")[0]
    assert code.count("state.started = true") >= 4                               # automatic start, person, pause, reel
    assert "!state.started" in code                                              # the automatic start checks it



# ------------------------------------------------------------------ design reset, Gate 2: hero, leads, cinematic, regions
@pytest.fixture()
def local_cinematic(app, tmp_path):
    """A media folder with tiny stand-ins for the three moments, their posters and phone cuts."""
    folder = tmp_path / "cinematic"
    folder.mkdir()
    for slot in ("moment-1", "moment-2", "moment-3"):
        (folder / f"{slot}.mp4").write_bytes(b"ftypmp42")
        (folder / f"{slot}-mobile.mp4").write_bytes(b"ftypmp42")
        (folder / f"{slot}.jpg").write_bytes(b"JFIF")
    previous = app.config["MEDIA_ROOT"]
    app.config["MEDIA_ROOT"] = str(tmp_path)
    yield tmp_path
    app.config["MEDIA_ROOT"] = previous


@pytest.fixture()
def local_hero(app, tmp_path):
    """A media folder with tiny stand-ins for the three hero layers and their phone copies."""
    folder = tmp_path / "hero"
    folder.mkdir()
    for name in ("sky", "mid", "fg", "fg-lit"):
        (folder / f"{name}.webp").write_bytes(b"RIFFxxxxWEBP")
        (folder / f"{name}-1280.webp").write_bytes(b"RIFFxxxxWEBP")
    previous = app.config["MEDIA_ROOT"]
    app.config["MEDIA_ROOT"] = str(tmp_path)
    yield tmp_path
    app.config["MEDIA_ROOT"] = previous


def test_hero_is_the_single_picture_until_the_layers_are_built(client):
    page = html(client, "/")
    hero = page.split('id="top"')[1].split("</section>")[0]
    assert "hero__stage" not in hero and "hero__layer" not in hero and "hero__slide" in hero


def test_hero_becomes_a_layered_motion_poster_when_the_layers_exist(client, local_hero):
    page = html(client, "/")
    hero = page.split('id="top"')[1].split("</section>")[0]
    assert 'data-hero-stage' in hero and "hero__slide" not in hero
    order = [hero.index(f"hero__layer--{n}") for n in ("sky", "mid", "fg")]
    assert order == sorted(order) and hero.index("hero__haze") < hero.index("hero__layer--mid") < hero.index("hero__glow") < hero.index("hero__layer--fg")
    for n in ("sky", "mid", "fg"):
        assert f'/media/hero/{n}.webp' in hero and f'/media/hero/{n}-1280.webp 1280w' in hero
    assert hero.count("<img") == 4 and 'aria-hidden="true"' in hero.split("hero__layer--lit")[1][:60]   # the light pass is a decoration
    # the lockup, buttons and release line are untouched
    for needle in ("Welcome, gamers", "Team Valkyrie presents", 'aria-label="Six"', "Start exploring", "Watch the trailer", "hero__release"):
        assert needle in hero, needle
    assert client.get("/media/hero/fg.webp").status_code == 200
    for bad in ("/media/hero/fg.png", "/media/hero/../clips/x.mp4", "/media/hero/sub/fg.webp", "/media/hero/Fg.webp"):
        assert client.get(bad).status_code == 404, bad


def test_a_partial_set_of_hero_layers_is_ignored(app, tmp_path):
    from app import local_media
    previous = app.config["MEDIA_ROOT"]
    try:
        app.config["MEDIA_ROOT"] = str(tmp_path)
        (tmp_path / "hero").mkdir()
        (tmp_path / "hero" / "sky.webp").write_bytes(b"RIFFxxxxWEBP")
        (tmp_path / "hero" / "fg.webp").write_bytes(b"RIFFxxxxWEBP")
        with app.app_context():
            assert local_media.hero_layers() is None                              # no mid: the single picture stays
            (tmp_path / "hero" / "mid.webp").write_bytes(b"RIFFxxxxWEBP")
            layers = local_media.hero_layers()
            assert set(layers) == {"sky", "mid", "fg"} and layers["sky"]["small"] is None       # the warm copy is optional
            (tmp_path / "hero" / "fg-lit.webp").write_bytes(b"RIFFxxxxWEBP")
            assert set(local_media.hero_layers()) == {"sky", "mid", "fg", "lit"}
    finally:
        app.config["MEDIA_ROOT"] = previous


def test_hero_motion_is_gated_paused_off_screen_and_simpler_on_phones():
    css = _css()["pages.css"]
    assert ".motion-on .hero__stage .hero__layer {" in css                          # nothing moves unless motion is allowed
    assert "@keyframes heroDolly" in css and "alternate" in css                     # eases out and back: no snap at the turn
    assert ".hero__stage.is-paused *" in css and ".hero__stage.is-hidden *" in css
    phone = css.split("@media (max-width: 760px) {")[-1]
    assert "animation: none" in phone and ".hero__layer--lit { display: none; }" in phone     # phones: push-in and depth only
    reduced = _css()["site.css"]
    assert "html.motion-on .hero__stage .hero__layer" in reduced                    # the reduced-motion blanket does not flatten it once allowed
    code = _script().split("function heroStage()")[1].split("// ---- Hero: the picture drifts")[0]
    assert "IntersectionObserver" in code and "is-paused" in code and "visibilitychange" in code


def test_hero_layer_builder_is_self_contained_and_never_touches_the_source():
    import inspect
    from scripts import make_hero_layers as mh
    source = inspect.getsource(mh)
    assert "unlink" not in source and "rmtree" not in source and "os.remove" not in source
    assert mh.OUT_DIR.name == "hero" and (mh.W, mh.H) == (1920, 1080)
    assert "media" in str(mh.SOURCE_CANDIDATES[0]) and "source" in str(mh.SOURCE_CANDIDATES[0])


def test_hero_is_one_static_robbery_card_that_keeps_the_required_identity(client):
    page = html(client, "/")
    hero = page.split('id="top"')[1].split("</section>")[0]
    assert 'class="hero__card"' in hero and "hero__bg" in hero and "hero__shade" in hero
    assert "Welcome, gamers" in hero and "Team Valkyrie presents" in hero
    assert 'class="hero__gta">Grand Theft Auto</span>' in hero and 'class="hero__vi"' in hero
    assert "Start exploring" in hero and "Watch the trailer" in hero and "hero__release" in hero
    assert hero.count("<h1") == 1
    assert hero.count("hero__slide") == 1 and "hero__slide--cycle" not in hero    # one image, no cycle
    assert "Jason_and_Lucia_Robbery" in hero                                      # the owner's chosen artwork
    assert "Jason_and_Lucia_Beach" not in page                                    # Beach is gone from the homepage


def test_first_moment_falls_back_to_the_still_without_footage(client):
    page = html(client, "/")
    moment = page.split('id="moment"')[1].split("</section>")[0]
    assert "has-video" not in page and "<button" not in moment and "cinema__play" not in page
    assert "Played in Rockstar" not in page and "Watch Official Trailer" not in moment


def test_cinematic_files_are_served_with_strict_names(client, local_cinematic):
    ok = client.get("/media/cinematic/moment-1.mp4")
    assert ok.status_code == 200 and ok.headers["Content-Type"].startswith("video/mp4")
    assert client.get("/media/cinematic/moment-1.jpg").status_code == 200
    assert client.get("/media/cinematic/moment-2-mobile.mp4").status_code == 200
    for bad in ("/media/cinematic/Moment-1.mp4", "/media/cinematic/moment-1.php", "/media/cinematic/../clips/x.mp4",
                "/media/cinematic/sub/moment-1.mp4", "/media/cinematic/moment-1.json", "/media/source-videos/trailers/a.mp4"):
        assert client.get(bad).status_code == 404, bad


def test_cinematic_lookup_needs_the_video_and_tolerates_missing_extras(app, tmp_path):
    from app import local_media
    previous = app.config["MEDIA_ROOT"]
    try:
        app.config["MEDIA_ROOT"] = str(tmp_path)
        with app.app_context():
            assert local_media.cinematics() == {}
            (tmp_path / "cinematic").mkdir()
            (tmp_path / "cinematic" / "moment-2.jpg").write_bytes(b"JFIF")
            assert local_media.cinematics() == {}                                 # a poster alone is not a moment
            (tmp_path / "cinematic" / "moment-2.mp4").write_bytes(b"ftypmp42")
            (tmp_path / "cinematic" / "stray.mp4").write_bytes(b"ftypmp42")        # not a known slot: ignored
            found = local_media.cinematics()
            assert list(found) == ["moment-2"]
            assert found["moment-2"]["video"] == "cinematic/moment-2.mp4" and found["moment-2"]["poster"] == "cinematic/moment-2.jpg"
            assert found["moment-2"]["mobile"] is None
    finally:
        app.config["MEDIA_ROOT"] = previous


def test_region_explorer_is_one_stage_six_tabs_and_real_links(client):
    page = html(client, "/")
    regions = page.split('id="leonida"')[1].split("</section>")[0]
    assert regions.count("data-region-view=") == 6 and regions.count("data-region-tab=") == 6
    assert regions.count('class="pill"') == 6                                      # one way in per region
    assert re.findall(r'class="regions__num">Region (\d\d) / 06<', regions) == ["01", "02", "03", "04", "05", "06"]
    for slug in ("vice-city", "leonida-keys", "grassrivers", "port-gellhorn", "ambrosia", "mount-kalaga"):
        assert f'href="/regions/{slug}"' in regions, slug


def test_section_order_and_untouched_sections_survive_gate_2(client):
    page = html(client, "/")
    order = [page.index(f'id="{name}"') for name in ("top", "leads", "moment", "cast", "leonida", "garage", "stories", "media")]
    assert order == sorted(order)
    assert page.count("data-cast-item") == 8 and 'data-showroom' in page and 'class="theatre"' in page


def test_only_the_built_moments_appear(client, app, tmp_path):
    previous = app.config["MEDIA_ROOT"]
    folder = tmp_path / "cinematic"
    folder.mkdir()
    (folder / "moment-3.mp4").write_bytes(b"ftypmp42")
    try:
        app.config["MEDIA_ROOT"] = str(tmp_path)
        page = html(client, "/")
        assert 'id="finale"' in page and 'id="world"' not in page
        assert 'id="moment"' in page and "data-cinema-video" not in page.split('id="moment"')[1].split("</section>")[0]
    finally:
        app.config["MEDIA_ROOT"] = previous


def test_cinematic_builder_loops_seamlessly_and_never_touches_the_sources():
    import inspect
    from scripts import make_cinematics as mc
    m1, m2, m3 = (mc.MOMENTS[k] for k in ("moment-1", "moment-2", "moment-3"))
    assert m1["parts"] == [(mc.TRAILER_1, 18.40, 10.55)]                         # extended: towers first, lowriders last
    assert m2["parts"] == [(mc.TRAILER_2, 6.35, 3.35), (mc.TRAILER_2, 138.15, 5.50)] and m2["dissolve"] == 0.4
    assert m3["parts"] == [(mc.TRAILER_2, 152.85, 10.95)]
    assert m2["bars"] and m3["bars"] and not m1["bars"]                          # Trailer 2 is letterboxed, Trailer 1 is not
    assert (m1["loop"], m2["loop"], m3["loop"]) == ("crossfade", "crossfade", "dip")
    assert mc.LOUDNESS["I"] == -16.0 and mc.OUT_DIR.name == "cinematic"
    assert abs(mc.loop_length(m1) - (10.55 - mc.SEAM)) < 1e-6 and mc.loop_length(m3) == 10.95
    source = inspect.getsource(mc)
    assert "unlink" not in source and "rmtree" not in source                      # it only ever writes into media/cinematic
    graph = mc.video_graph(m2, "desktop")
    assert "xfade=transition=fade:duration=0.4:offset=2.950" in graph and "crop=3840:1728:0:216" in graph
    assert f"xfade=transition=fade:duration={mc.SEAM}:offset=0[seam]" in graph      # the loop seam is baked in
    assert "fade=t=out" in mc.video_graph(m3, "desktop") and "fade=t=in:st=0" in mc.video_graph(m3, "desktop")


def test_cinematic_loop_audio_is_whole_and_aligned_to_the_picture():
    """The seam used to be acrossfade between two branches of one asplit, which produced no audio at all: the last
    SEAM seconds of every crossfade loop were silent while the picture played on."""
    from scripts import make_cinematics as mc
    m1 = mc.MOMENTS["moment-1"]
    graph = mc.audio_graph(m1, "")
    assert "acrossfade" not in graph                                              # the failing construction is gone
    assert "afade=t=out:st=0:d=0.8:curve=qsin" in graph and "afade=t=in:st=0:d=0.8:curve=qsin" in graph   # equal power
    assert "amix=inputs=2:duration=longest:normalize=0[aseam]" in graph
    assert mc.predicted_mid_frames(m1) == 269                                     # frames 24..292 of the 30 fps picture
    cut = mc.SEAM + 269 / mc.FPS                                                  # the sound is cut where the picture is
    assert f"atrim=start={mc.SEAM}:end={cut:.4f}" in graph and f"atrim=start={cut:.4f}:end={cut + mc.SEAM:.4f}" in graph
    assert "concat=n=2:v=0:a=1[a]" in graph
    # a measured frame count (xfade and trim rounding) moves the cut with the picture
    assert f"end={mc.SEAM + 230 / mc.FPS:.4f}" in mc.audio_graph(m1, "", 230)
    # the clip is read a little past its end so the seam is never short of sound
    assert mc.input_args(m1)[3] == f"{10.55 + mc.AUDIO_TAIL:.3f}"
    # dip loops (the finale) keep their own fade-through-silence and are untouched
    assert "afade=t=out" in mc.audio_graph(mc.MOMENTS["moment-3"], "") and "amix" not in mc.audio_graph(mc.MOMENTS["moment-3"], "")


def test_cinematic_moments_show_only_a_speaker_and_a_fallback_that_stays_hidden(client, local_cinematic):
    page = html(client, "/")
    for anchor in ("moment", "world", "finale"):
        section = page.split(f'id="{anchor}"')[1].split("</section>")[0]
        assert section.count("<button") == 2
        speaker = section.split("data-cinema-sound")[1].split("</button>")[0]
        assert 'aria-label="Sound"' in section and 'aria-pressed="false"' in section and "i-sound-off" in speaker
        fallback = section.split("data-cinema-toggle")[1].split("</button>")[0]
        assert 'aria-label="Play footage"' in section and " hidden" in section.split("data-cinema-toggle")[1][:80]   # hidden until blocked
        assert "Pause" not in section and "i-pause" not in section and "Replay" not in section                      # no pause control exists
    code = _script().split("function cinemas()")[1].split("function regionExplorer()")[0]
    assert "Pause footage" not in code and "userPaused" not in code and "is-tools" not in code
    assert "p.toggleBtn.hidden = !(suppressed && !playing)" in code                # the fallback shows only when blocked
    assert 'name === "NotAllowedError"' in code and 'name === "AbortError"' in code  # only a real refusal; a pause-interrupt retries
    assert '["pointerdown", "keydown", "touchend"]' in code                          # one more try after the first gesture
    css = _css()["components.css"]
    assert ".cinema__tool[hidden]" in css and "@media (pointer: coarse)" in css and "min-width: 44px" in css
    assert ".cinema__tool--toggle.is-held" not in css and ".cinema.is-tools" not in css


def test_hero_art_is_not_repeated_in_the_closing_band(client):
    page = html(client, "/")
    closing = page.split('class="section band closing"')[1]
    assert "Jason_and_Lucia_Robbery" not in closing


def test_trailers_are_ordered_trailer_1_trailer_2_extended_look(client):
    page = html(client, "/")
    media = page.split('id="media"')[1].split("</section>")[0]
    titles = re.findall(r'<span class="video-card__title"><b>([^<]+)</b>', media)
    assert len(titles) == 3 and "Trailer 1" in titles[0] and "Trailer 2" in titles[1] and "Extended Look" in titles[2], titles
    lead = media.split("theatre__item--lead")[1].split("</div>")[0]
    assert "Trailer 1" in lead                                                    # Trailer 1 is the primary item
    assert "GTAVI_Trailer1_poster" in lead or "Trailer1" in lead or "trailer-1" in lead.lower()


def test_screenshots_have_no_helper_text(client):
    page = html(client, "/")
    assert "Select one to view it larger" not in page and "Official screenshots from Rockstar" not in page
    assert 'class="gallery-block__head' in page and ">Screenshots<" in page


def test_region_explorer_advances_by_itself_and_stays_manual(client):
    code = _script().split("function regionExplorer()")[1].split("function showroom()")[0]
    assert "INTERVAL = 7000" in code and "motionAllowed()" in code                # a calm pace; no advance unless motion is allowed
    assert "mouseenter" in code and "focusin" in code and "holding" in code       # it waits while the visitor is pointing at it
    assert "IntersectionObserver" in code and "document.hidden" in code           # and only while it is on screen
    assert 'tab.addEventListener("click"' in code                                  # manual selection stays
    css = _css()["pages.css"]
    assert "@keyframes regionTick" in css and ".regions.is-auto" in css           # a quiet progress line under the active tab


def test_hero_artwork_is_not_clipped_at_the_top():
    css = _css()["pages.css"]
    assert re.search(r"\.hero__bg \{ position: absolute; inset: 0;", css)          # the whole picture, headroom included
    assert "heroBg.style.setProperty" not in _script()                          # no parallax that would push it off


def test_garage_advances_one_vehicle_at_a_time_and_waits_for_the_visitor():
    code = _script().split("function showroom()")[1].split("function loops()")[0]
    assert "INTERVAL = 7000" in code and "motionAllowed()" in code               # one vehicle every seven seconds
    assert "pointermove" in code and "focusin" in code and "holding" in code     # a moving pointer and keyboard focus hold it
    assert "focus-visible" in code and "leaveTimer" in code                      # a pointer that only rests lets go
    assert "IntersectionObserver" in code and "document.hidden" in code          # only while on screen
    assert "touched()" in code and "cancelGlide" in code                         # a manual move restarts the clock
    assert "is-wrapping" in code and "function glide(" in code                   # fades back to the first; a slow eased glide
    assert 'scrollTo({ left: 0, behavior: "auto" })' in code                      # no long sweep back across the track


def test_lucia_card_is_lifted_without_losing_the_night_look(client):
    page = html(client, "/")
    assert "leads__card--lucia-caminos" in page and "leads__card--jason-duval" in page
    css = _css()["pages.css"]
    assert ".leads__card--lucia-caminos .media__img { filter: brightness(" in css

