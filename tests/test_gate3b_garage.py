"""Gate 3B: the Garage. The showroom is the database (official vehicles only, real search, category, sort and pagination),
the pictures are Rockstar's own screenshots chosen by hand, and nothing about a vehicle is stated that Rockstar has not."""
import re
from pathlib import Path

import pytest
from flask import render_template

from app import media_slots
from app.services import site

ROOT = Path(__file__).resolve().parent.parent
OFFICIAL = ["grotti-cheetah", "vapid-dominator-buggy", "shitzu-squalo", "vapid-stanier", "vapid-ganado"]


def html(client, path):
    response = client.get(path)
    assert response.status_code == 200, path
    return response.get_data(as_text=True)


# ------------------------------------------------------------------ the layout planner
@pytest.mark.parametrize("count", range(0, 14))
def test_every_row_of_the_showroom_grid_is_full(count):
    sizes = site.garage_layout(count)
    assert len(sizes) == count
    span = {"feature": 12, "half": 6, "wide": 7, "narrow": 5}
    row = 0
    for size in sizes:
        row += span[size]
        if row == 12:
            row = 0
        assert row < 12 or row == 0
    assert row == 0, (count, sizes)          # the last row ends exactly at the edge: no hole in the grid


def test_the_grid_varies_instead_of_repeating_one_card():
    sizes = site.garage_layout(5)
    assert sizes[0] == "feature" and len(set(sizes)) >= 3


# ------------------------------------------------------------------ the pictures
def test_every_vehicle_picture_is_described_and_positioned():
    for name, spec in media_slots.GARAGE_FRAMES.items():
        assert name.startswith("vehicle-") and len(spec["alt"]) > 20 and spec["alt"][0].isupper(), name
        assert all(0 <= v <= 1 for v in spec["face"] + spec["phone"]), name
        assert not re.search(r"horsepower|mph|km/h|top speed|rare|limited", spec["alt"], re.I), name     # a description, not a claim


def test_the_chosen_pictures_belong_to_their_vehicle():
    for slug, pick in media_slots.GARAGE_PICKS.items():
        for role in ("stage", "card"):
            assert pick[role] in media_slots.GARAGE_FRAMES, (slug, role)
            assert pick[role].startswith(f"vehicle-{slug}-"), (slug, role)        # never another vehicle's picture
        assert pick["side"] in ("left", "right") and pick["vpos"] in ("top", "bottom")


def test_every_picture_the_database_attaches_to_an_official_vehicle_is_described(app):
    from app.repositories import media, vehicles
    with app.app_context():
        ids = vehicles.ids_by_slug(OFFICIAL)
        for slug, vehicle_id in ids.items():
            frames = media.for_entity("vehicle", vehicle_id, limit=24)
            assert frames, slug
            for m in frames:
                assert m["slug"] in media_slots.GARAGE_FRAMES, (slug, m["slug"])


def test_every_cut_position_the_pages_use_is_in_the_stylesheet(client):
    css = (ROOT / "app" / "static" / "css" / "garage.css").read_text(encoding="utf-8")
    seen = set()
    for path in ["/vehicles"] + [f"/vehicles/{s}" for s in OFFICIAL]:
        page = html(client, path)
        seen |= set(re.findall(r'data-(px|py|pxn|pyn)="(\d+)"', page))
    assert seen
    for attr, value in seen:
        assert f'.gshot[data-{attr}="{value}"]' in css, (attr, value)


def test_the_pages_never_use_inline_styles(client):
    for path in ["/vehicles"] + [f"/vehicles/{s}" for s in OFFICIAL]:
        assert " style=" not in html(client, path), path        # the CSP forbids them


# ------------------------------------------------------------------ the opening
def test_the_opening_shows_one_machine_and_a_lineup_of_five(client):
    page = html(client, "/vehicles")
    stage = page.split('data-stage')[1].split("</section>")[0]
    assert stage.count("data-panel=") == 5 and stage.count("data-pick=") == 5
    panels = re.findall(r'<article class="stage__panel[^"]*" id="stage-([a-z-]+)" data-panel="[a-z-]+"( hidden)?>', stage)
    assert [p[0] for p in panels] == OFFICIAL
    assert [bool(p[1]) for p in panels] == [False, True, True, True, True]          # only the first is on show; the rest load on demand
    assert stage.count('fetchpriority="high"') == 1                                  # one picture is urgent
    assert 'aria-current="true"' in stage and "<h1" in page and page.count("<h1") == 1
    assert "autoplay" not in stage.lower() and "<video" not in stage                  # nothing starts moving by itself


def test_each_lineup_link_works_without_script(client):
    page = html(client, "/vehicles")
    for slug in OFFICIAL:
        assert f'href="/vehicles/{slug}" data-pick="{slug}"' in page


def test_the_page_transition_is_off_for_reduced_motion():
    css = (ROOT / "app" / "static" / "css" / "garage.css").read_text(encoding="utf-8")
    block = css.split("@media (prefers-reduced-motion: no-preference) {")[1].split(chr(10) + "}" + chr(10))[0]
    assert "@view-transition { navigation: auto; }" in block and "view-transition-name: vehicle-art" in block
    assert css.count("@view-transition") == 1 and css.index("@view-transition") > css.index("prefers-reduced-motion: no-preference")


def test_the_script_does_not_advance_the_opening_by_itself():
    js = (ROOT / "app" / "static" / "js" / "garage.js").read_text(encoding="utf-8")
    assert "setInterval" not in js and "autoplay" not in js.lower()
    assert "decode()" in js                                                            # a picture is ready before its panel is shown
    css = (ROOT / "app" / "static" / "css" / "garage.css").read_text(encoding="utf-8")
    assert "infinite" not in css                                                       # no loop anywhere


# ------------------------------------------------------------------ the showroom
def test_showroom_cards_use_the_planned_sizes_and_link_to_the_vehicle(client):
    page = html(client, "/vehicles")
    sizes = re.findall(r'class="gcard gcard--([a-z]+) reveal"', page)
    assert sizes == site.garage_layout(5)
    for slug in OFFICIAL:
        assert f'class="gcard__link" href="/vehicles/{slug}"' in page


def test_filters_keep_each_other_in_the_links(client):
    page = html(client, "/vehicles?q=vapid&sort=name_desc")
    href = re.search(r'href="([^"]*category=boat[^"]*)"', page).group(1)
    assert "q=vapid" in href and "sort=name_desc" in href and href.endswith("#showroom")
    all_link = re.search(r'<nav class="gcats"[^>]*>\s*<a href="([^"]+)"', page).group(1)
    assert "q=vapid" in all_link and "category=" not in all_link


def test_the_result_line_and_clear_link_describe_the_filters(client):
    page = html(client, "/vehicles?category=boat&q=squalo")
    line = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", page.split('class="gresult"')[1].split("</p>")[0]))
    assert "1 machine in Boats matching" in line and "Clear filters" in line
    assert "Clear filters" not in html(client, "/vehicles")


def test_every_sort_option_orders_the_cards(client):
    names = lambda path: re.findall(r'<h3 class="gcard__name">([^<]+)</h3>', html(client, path))
    featured = names("/vehicles")
    assert names("/vehicles?sort=featured") == featured
    assert names("/vehicles?sort=name_asc") == sorted(featured, key=lambda n: n.replace("&#39;", "'").lower()) or names("/vehicles?sort=name_asc")[0].startswith("&#39;67")
    assert names("/vehicles?sort=name_desc") == list(reversed(names("/vehicles?sort=name_asc")))
    assert sorted(names("/vehicles?sort=category")) == sorted(featured)
    page = html(client, "/vehicles?sort=name_desc")
    assert '<option value="name_desc" selected>' in page
    for value in ("featured", "name_asc", "name_desc", "category"):
        assert f'<option value="{value}"' in page


def test_search_is_a_real_query_not_a_filter_on_the_page(client):
    names = lambda path: re.findall(r'<h3 class="gcard__name">([^<]+)</h3>', html(client, path))
    assert names("/vehicles?q=grotti") == ["&#39;95 Grotti Cheetah"]
    assert names("/vehicles?q=retro") == ["Vapid Ganado Retro Build"]
    assert names("/vehicles?q=%25") == []                          # a percent sign is text, not a wildcard
    assert names("/vehicles?q=%27%3B+DROP+TABLE+vehicles%3B--") == []
    assert len(names("/vehicles")) == 5                           # and nothing was dropped


def test_an_empty_search_shows_a_clear_way_back(client):
    page = html(client, "/vehicles?q=zzzz&category=boat")
    assert "Nothing in the garage matches that" in page and "gcard__name" not in page
    assert 'href="/vehicles#showroom"' in page and "No machines" in page


def test_pagination_still_works_when_there_are_more_vehicles_than_a_page(client):
    page = html(client, "/vehicles?per_page=2&page=2")
    assert 'aria-label="Pagination"' in page and 'rel="prev"' in page and 'rel="next"' in page
    assert len(re.findall(r'class="gcard gcard--', page)) == 2


def test_a_bad_sort_or_page_is_refused_not_ignored(client):
    assert client.get("/vehicles?sort=cheapest").status_code == 400
    assert client.get("/vehicles?page=0").status_code == 400


def test_the_public_garage_never_lists_a_concept_vehicle(client):
    page = html(client, "/vehicles?status=demo&q=concept")
    assert "gcard__name" not in page or "Corvina" not in page
    assert "Corvina" not in html(client, "/vehicles")


# ------------------------------------------------------------------ the vehicle pages
@pytest.mark.parametrize("slug", OFFICIAL)
def test_every_vehicle_page_has_its_own_opening_and_never_repeats_it(client, slug):
    page = html(client, f"/vehicles/{slug}")
    hero = page.split('<header class="vhero')[1].split("</header>")[0]
    hero_file = re.search(r"static/media/([A-Za-z0-9_.~-]+\.jpg)", hero).group(1)
    assert '<h1 class="vhero__name">' in hero
    showcase = page.split('class="vover"')[1].split('class="vmore"')[0]
    assert hero_file not in showcase, slug                                 # the showcase never repeats the opening picture
    assert page.count('class="gtile"') == 4 and f'href="/vehicles/{slug}"' not in page.split('class="vmore"')[1]


def test_vehicle_pages_state_only_what_is_recorded(client):
    for slug in OFFICIAL:
        page = html(client, f"/vehicles/{slug}")
        assert "Not published by Rockstar" in page and "badge--official" in page
        assert not re.search(r"horsepower|top speed|0-60|\bmph\b|\bkm/h\b|\bbhp\b|\$\d", page, re.I), slug
        assert "Where it appears" not in page                              # no mission or place is recorded for these, so none is shown


def test_a_vehicle_with_four_pictures_gets_a_viewer_and_one_with_one_does_not(client):
    squalo = html(client, "/vehicles/shitzu-squalo")
    assert "data-viewer" in squalo and squalo.count("data-slide") == 3 and squalo.count("data-thumb") == 3
    assert 'aria-label="Previous image"' in squalo and 'aria-label="Next image"' in squalo and 'aria-label="View this image larger"' in squalo
    ganado = html(client, "/vehicles/vapid-ganado")
    assert "data-viewer" not in ganado and "showcase--none" in ganado and "one official image" in ganado


def test_the_viewer_markup_works_without_script(client):
    page = html(client, "/vehicles/vapid-stanier")
    thumbs = re.findall(r'<a href="(https://www\.rockstargames\.com/[^"]+)" data-thumb', page)
    assert len(thumbs) == 3 and all("imwidth=2560" in t for t in thumbs)       # each thumbnail links to the full picture
    slides = page.split('class="viewer__slides"')[1].split("</ul>")[0]
    assert slides.count(" hidden") == 2                                          # only the first is shown before script runs


def test_connected_world_lists_missions_and_places_with_their_labels(client, app):
    """No official vehicle is tied to a mission yet, so the section is hidden; given data it shows it, labelled."""
    with app.test_request_context("/vehicles/vapid-stanier"):
        vehicle = site.vehicle_detail("vapid-stanier")
        vehicle["missions"] = [{"slug": "ridge-run", "title": "Ridge Run", "mission_type": "activity", "content_status": "demo", "usage_note": "Time-trial car"}]
        vehicle["locations"] = [{"slug": "kalaga-ridge-lookout", "name": "Kalaga Ridge Lookout", "content_status": "official", "region_slug": "mount-kalaga", "region_name": "Mount Kalaga"}]
        page = render_template("vehicles/detail.html", vehicle=vehicle)
    assert "The connected world" in page and "Ridge Run" in page and "Time-trial car" in page and "Kalaga Ridge Lookout" in page
    assert page.count("badge--demo") == 1                                         # the Team Valkyrie story is labelled, the official place is not


def test_more_machines_are_readable_cards_not_oversized_headings():
    css = (ROOT / "app" / "static" / "css" / "garage.css").read_text(encoding="utf-8")
    name = re.search(r"\.gtile__name \{([^}]*)\}", css).group(1)
    assert "var(--t-h4)" in name and "--t-h1" not in name and "--t-display" not in name
    assert re.search(r"\.gtile__art \{[^}]*aspect-ratio: 16 / 10", css)


# ------------------------------------------------------------------ nothing else is touched
def test_garage_styles_only_define_garage_selectors():
    css = re.sub(r"/\*.*?\*/", "", (ROOT / "app" / "static" / "css" / "garage.css").read_text(encoding="utf-8"), flags=re.S)
    own = ("garage", "stage", "lineup", "gshot", "gbtn", "ggrid", "gcard", "gtile", "gtools", "gcats", "gresult", "gempty", "gnote", "showroom",
           "vhero", "vcrumb", "vover", "vplate", "showcase", "viewer", "single", "vworld", "vmore")
    for selector in re.findall(r"(?:^|\})\s*([^{}@]+?)\s*\{", css):
        for part in selector.split(","):
            part = part.strip().replace("html.motion-on ", "")
            if part in ("from", "to") or part.startswith("::view-transition"):      # keyframe steps, the page-change transition
                continue
            first = re.search(r"[.#]([a-z_-]+)", part)
            assert first and first.group(1).split("__")[0].split("--")[0] in own, part.strip()


def test_other_sections_do_not_load_the_garage_assets(client):
    for path in ("/", "/characters", "/characters/jason-duval", "/regions", "/locations", "/missions", "/about"):
        page = html(client, path)
        assert "garage.css" not in page and "garage.js" not in page, path


def test_the_homepage_vehicle_showcase_is_unchanged_in_structure(client):
    page = html(client, "/")
    assert 'class="slide"' in page and "showroom__item" in page
