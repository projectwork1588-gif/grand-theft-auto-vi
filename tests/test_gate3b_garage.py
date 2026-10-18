"""Gate 3B (second pass): the Garage. The collection is the database (official vehicles only, real search, category, sort and pagination),
the pictures are Rockstar's own screenshots chosen by hand, and nothing about a vehicle is stated that Rockstar has not."""
import re
from pathlib import Path

import pytest
from flask import render_template

from app import media_slots
from app.services import site

ROOT = Path(__file__).resolve().parent.parent
OFFICIAL = ["grotti-cheetah", "vapid-dominator-buggy", "shitzu-squalo", "vapid-stanier", "vapid-ganado", "dinka-enduro", "crest-kayak"]
NAMES = ["&#39;95 Grotti Cheetah", "&#39;67 Vapid Dominator Buggy", "Shitzu Squalo", "Vapid Stanier", "Vapid Ganado Retro Build",
         "Dinka Enduro Motorcycle", "Crest Kayak"]


def html(client, path):
    response = client.get(path)
    assert response.status_code == 200, path
    return response.get_data(as_text=True)


def tile_models(page):
    return re.findall(r'<h3 class="tile__model">([^<]+)</h3>', page)


def css():
    return (ROOT / "app" / "static" / "css" / "garage.css").read_text(encoding="utf-8")


# ------------------------------------------------------------------ the arrangement of the collection
@pytest.mark.parametrize("count", range(0, 16))
def test_every_row_of_the_collection_is_full_and_counts_add_up(count):
    rows = site.garage_rows(count)
    assert sum(len(r) for r in rows) == count
    for row in rows:
        assert sum(row) == 12, (count, rows)                  # each row ends exactly at the edge: no hole in the mosaic


def test_the_mosaic_varies_instead_of_repeating_one_card():
    rows = site.garage_rows(7)
    assert rows[0] == [8, 4] and len({tuple(r) for r in rows}) == 3


def test_the_name_is_split_into_maker_and_model():
    assert site.split_name("'95 Grotti Cheetah", "Grotti") == ("'95 Grotti", "Cheetah")
    assert site.split_name("Vapid Ganado Retro Build", "Vapid") == ("Vapid", "Ganado Retro Build")
    assert site.split_name("Crest Kayak", "Crest") == ("Crest", "Kayak")
    assert site.split_name("Mystery", None) == ("", "Mystery")
    assert site.split_name("Vapid", "Vapid") == ("", "Vapid")          # nothing left for the model: the name stays whole


# ------------------------------------------------------------------ the pictures
def test_every_vehicle_picture_is_described_and_positioned():
    for name, spec in media_slots.GARAGE_FRAMES.items():
        assert len(spec["alt"]) > 20 and spec["alt"][0].isupper(), name
        assert all(0 <= v <= 1 for v in spec["face"] + spec["phone"]), name
        assert not re.search(r"horsepower|mph|km/h|top speed|rare|limited", spec["alt"], re.I), name


def test_every_pick_is_described_and_belongs_to_its_vehicle():
    for slug, pick in media_slots.GARAGE_PICKS.items():
        for role in ("stage", "card"):
            assert pick[role] in media_slots.GARAGE_FRAMES and pick[role].startswith("vehicle-"), (slug, role)
            assert pick[role].split("vehicle-")[1].startswith(slug.split("-")[-1]) or slug in pick[role], (slug, role)
        assert pick["side"] in ("left", "right") and pick["vpos"] in ("top", "bottom")
        assert pick["story"] in ("mosaic", "mosaic-flip", "viewer", "panorama", "context", "none")
        assert pick["stage"] not in pick["gallery"]                      # the showcase never repeats the opening picture
        for g in pick["gallery"]:
            assert g in media_slots.GARAGE_FRAMES
    assert set(media_slots.GARAGE_PICKS) == set(OFFICIAL)


def test_vehicles_with_several_pictures_open_on_a_different_one_from_their_tile():
    for slug, pick in media_slots.GARAGE_PICKS.items():
        if pick["story"] in ("mosaic", "mosaic-flip", "viewer", "panorama"):
            assert pick["stage"] != pick["card"], slug
        elif pick["stage"] == pick["card"]:
            assert pick.get("card_zoom"), slug                               # one picture: the tile draws it closer, so it is not a copy


def test_atmosphere_pictures_name_no_vehicle():
    for slug, caption in media_slots.GARAGE_MOMENTS:
        assert slug in media_slots.GARAGE_FRAMES
        assert not re.search(r"Cheetah|Dominator|Squalo|Stanier|Ganado|Enduro|Kayak", caption), caption        # Rockstar's set title, never a model


def test_every_picture_the_database_attaches_to_an_official_vehicle_is_described(app):
    from app.repositories import media, vehicles
    with app.app_context():
        for slug, vehicle_id in vehicles.ids_by_slug(OFFICIAL).items():
            frames = media.for_entity("vehicle", vehicle_id, limit=24)
            assert frames, slug
            for m in frames:
                assert m["slug"] in media_slots.GARAGE_FRAMES, (slug, m["slug"])


def test_every_cut_position_the_pages_use_is_in_the_stylesheet(client):
    sheet = css()
    seen = set()
    for path in ["/vehicles"] + [f"/vehicles/{s}" for s in OFFICIAL]:
        page = html(client, path)
        seen |= set(re.findall(r'data-(px|py|pxn|pyn|zoom)="([\d.]+)"', page))
    assert seen
    for attr, value in seen:
        assert f'.gshot[data-{attr}="{value}"]' in sheet, (attr, value)


def test_the_pages_never_use_inline_styles(client):
    for path in ["/vehicles"] + [f"/vehicles/{s}" for s in OFFICIAL]:
        assert " style=" not in html(client, path), path


# ------------------------------------------------------------------ the data: two more official vehicles, plain copy
def test_the_two_new_vehicles_are_official_and_sourced(app):
    from app.db import query_all
    with app.app_context():
        rows = {r["slug"]: r for r in query_all("SELECT slug, name, manufacturer, content_status, source_url, summary, description FROM vehicles WHERE vehicle_id > 13")}
    assert set(rows) == {"dinka-enduro", "crest-kayak"}
    for r in rows.values():
        assert r["content_status"] == "official" and r["source_url"].startswith("https://www.rockstargames.com/")
        assert not re.search(r"horsepower|top speed|mph|km/h|\d+ hp|price|rare", r["summary"] + r["description"], re.I), r["slug"]
    assert rows["dinka-enduro"]["name"] == "Dinka Enduro Motorcycle" and rows["crest-kayak"]["name"] == "Crest Kayak"


def test_the_api_serves_the_new_vehicles_unchanged_in_shape(client):
    data = client.get("/api/v1/vehicles?status=official&per_page=50").get_json()
    assert data["pagination"]["total"] == 7 and {v["slug"] for v in data["data"]} == set(OFFICIAL)
    one = client.get("/api/v1/vehicles/crest-kayak").get_json()
    assert one["name"] == "Crest Kayak" and one["category_slug"] == "boat" and one["content_status"] == "official"


# ------------------------------------------------------------------ the opening
def test_the_opening_shows_one_machine_and_a_lineup_of_seven(client):
    page = html(client, "/vehicles")
    stage = page.split("data-stage")[1].split("</section>")[0]
    assert stage.count("data-panel=") == 7 and stage.count("data-pick=") == 7
    panels = re.findall(r'<article class="scene[^"]*" id="scene-([a-z-]+)" data-panel="[a-z-]+" data-vehicle="[a-z-]+"( hidden)?>', stage)
    assert [p[0] for p in panels] == OFFICIAL
    assert [bool(p[1]) for p in panels] == [False] + [True] * 6        # only the first is on show; the rest load on demand
    assert stage.count('fetchpriority="high"') == 1
    assert 'aria-current="true"' in stage and page.count("<h1") == 1
    assert "<video" not in stage and "autoplay" not in stage.lower()
    assert "data-ctl hidden" in stage                                  # the arrows exist only when script can make them work


def test_each_lineup_link_works_without_script(client):
    page = html(client, "/vehicles")
    for slug in OFFICIAL:
        assert f'href="/vehicles/{slug}" data-pick="{slug}"' in page


def test_the_script_never_advances_the_opening_by_itself():
    js = (ROOT / "app" / "static" / "js" / "garage.js").read_text(encoding="utf-8")
    assert "setInterval" not in js and "autoplay" not in js.lower()
    assert "decode()" in js and "pageswap" in js
    assert "infinite" not in css()


def test_the_page_transition_and_depth_effects_are_off_for_reduced_motion():
    sheet = css()
    block = sheet.split("@view-transition")[0].rsplit("@media (prefers-reduced-motion: no-preference) {", 1)[1]
    assert block.strip() == "" and "view-transition-name: vehicle-art" in sheet.split("@view-transition")[1]
    assert "prefers-reduced-motion: no-preference" in sheet.split("translate: calc(var(--mx")[0].rsplit("@media", 1)[1]       # the pointer drift
    assert "prefers-reduced-motion: reduce" in sheet and ".scene, .viewer__slide { transition: opacity .25s linear" in sheet


# ------------------------------------------------------------------ the collection
def test_the_collection_uses_the_planned_arrangement_and_links_each_tile(client):
    page = html(client, "/vehicles")
    spans = re.findall(r'class="tile tile--s(\d+) reveal"', page)
    assert [int(s) for s in spans] == [s for row in site.garage_rows(7) for s in row]
    for slug in OFFICIAL:
        assert f'class="tile__link" href="/vehicles/{slug}"' in page
    assert tile_models(page)[:2] == ["Cheetah", "Dominator Buggy"]


def test_the_headline_counts_the_collection_and_does_not_overclaim(client):
    page = html(client, "/vehicles")
    assert "Seven machines of Leonida" in page
    for phrase in ("Every Machine", "Every machine", "What the pictures are", "Not published by Rockstar", "official image"):
        assert phrase not in page, phrase


def test_filters_keep_each_other_in_the_links(client):
    page = html(client, "/vehicles?q=vapid&sort=name_desc")
    href = re.search(r'href="([^"]*category=boat[^"]*)"', page).group(1)
    assert "q=vapid" in href and "sort=name_desc" in href and href.endswith("#showroom")
    all_link = re.search(r'<nav class="ctl__cats"[^>]*>\s*<a href="([^"]+)"', page).group(1)
    assert "q=vapid" in all_link and "category=" not in all_link


def test_the_result_line_only_appears_when_filtering(client):
    assert 'class="gresult" role="status" aria-live="polite" hidden' in html(client, "/vehicles")
    page = html(client, "/vehicles?category=boat&q=squalo")
    line = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", page.split('class="gresult"')[1].split("</p>")[0]))
    assert "1 machine in Boats matching" in line and "Clear" in line and " hidden" not in page.split('class="gresult"')[1].split(">")[0]


def test_every_sort_option_orders_the_tiles(client):
    featured = tile_models(html(client, "/vehicles"))
    assert tile_models(html(client, "/vehicles?sort=featured")) == featured
    asc = tile_models(html(client, "/vehicles?sort=name_asc"))
    assert tile_models(html(client, "/vehicles?sort=name_desc")) == list(reversed(asc))
    assert sorted(tile_models(html(client, "/vehicles?sort=category"))) == sorted(featured)
    page = html(client, "/vehicles?sort=name_desc")
    assert '<option value="name_desc" selected>' in page
    for value in ("featured", "name_asc", "name_desc", "category"):
        assert f'<option value="{value}"' in page


def test_search_is_a_real_query_not_a_filter_on_the_page(client):
    assert tile_models(html(client, "/vehicles?q=grotti")) == ["Cheetah"]
    assert tile_models(html(client, "/vehicles?q=kayak")) == ["Kayak"]
    assert tile_models(html(client, "/vehicles?q=%25")) == []                 # a percent sign is text, not a wildcard
    assert tile_models(html(client, "/vehicles?q=%27%3B+DROP+TABLE+vehicles%3B--")) == []
    assert len(tile_models(html(client, "/vehicles"))) == 7                   # and nothing was dropped
    assert len(tile_models(html(client, "/vehicles?category=boat"))) == 2     # the Squalo and the Kayak
    assert tile_models(html(client, "/vehicles?category=motorcycle")) == ["Enduro Motorcycle"]


def test_an_empty_search_shows_a_clear_way_back(client):
    page = html(client, "/vehicles?q=zzzz&category=boat")
    assert "No machine matches that" in page and "tile__model" not in page
    assert 'href="/vehicles#showroom"' in page and "No machines" in page


def test_pagination_still_works_when_there_are_more_vehicles_than_a_page(client):
    page = html(client, "/vehicles?per_page=2&page=2")
    assert 'aria-label="Pagination"' in page and 'rel="prev"' in page and 'rel="next"' in page
    assert len(re.findall(r'class="tile tile--s', page)) == 2


def test_a_bad_sort_or_page_is_refused_not_ignored(client):
    assert client.get("/vehicles?sort=cheapest").status_code == 400
    assert client.get("/vehicles?page=0").status_code == 400


def test_the_public_garage_never_lists_a_concept_vehicle(client):
    assert "Corvina" not in html(client, "/vehicles?status=demo&q=concept")
    assert "Corvina" not in html(client, "/vehicles")


def test_the_customs_band_names_no_model_and_shows_only_on_the_whole_collection(client):
    page = html(client, "/vehicles")
    band = page.split('class="customs"')[1].split("</section>")[0]
    assert band.count("<figure>") == 4 and "Rideout Customs Mod Shop" in band and "One-Eyed Willie" in band
    assert not re.search(r"Cheetah|Dominator|Squalo|Stanier|Ganado|Enduro|Kayak", band)
    assert 'class="customs"' not in html(client, "/vehicles?category=boat") and 'class="customs"' not in html(client, "/vehicles?q=vapid")


# ------------------------------------------------------------------ the vehicle pages
@pytest.mark.parametrize("slug", OFFICIAL)
def test_every_vehicle_page_has_its_own_entrance_and_never_repeats_it(client, slug):
    page = html(client, f"/vehicles/{slug}")
    opening = page.split('<header class="vd-hero')[1].split("</header>")[0]
    assert '<h1 class="plate vd-plate">' in opening and 'class="vd-crumb"' in opening and 'href="#machine"' in opening
    hero_file = re.search(r"static/media/([A-Za-z0-9_.~-]+\.jpg)", opening).group(1)
    body = page.split('id="machine"')[1].split('class="vd-next"')[0]
    if 'class="vd-seq vd-close"' in body:                                  # a machine with one picture is shown in crops of it, named as such: only there does the file come back
        before, rest = body.split('class="vd-seq vd-close"')
        assert hero_file not in before and hero_file not in rest.split("</section>")[1], slug
    else:
        assert hero_file not in body, slug                                 # the showcase never repeats the opening picture
    assert page.count('rel="prev"') == 1 and page.count('rel="next"') == 1 and page.count('data-vehicle="') >= 9 and 'aria-label="All machines"' in page


def test_each_vehicle_is_set_the_way_its_pictures_want_to_be_seen(client):
    stories = {slug: re.search(r'<article class="garage vd" data-vehicle="[a-z-]+" data-sequence="([a-z_]+)"', html(client, f"/vehicles/{slug}")).group(1) for slug in OFFICIAL}
    assert stories == {"grotti-cheetah": "stage_pair", "vapid-dominator-buggy": "viewer", "shitzu-squalo": "panorama_pair", "vapid-stanier": "stage_pair",
                       "vapid-ganado": "close", "dinka-enduro": "context", "crest-kayak": "context"}
    assert len(set(stories.values())) >= 5                                 # not one template with seven backgrounds
    sides = [re.search(r"vd-stage vd-stage--(left|right)", html(client, f"/vehicles/{slug}")).group(1) for slug in ("grotti-cheetah", "vapid-stanier")]
    assert sides == ["right", "left"]                                      # the two stage pages bleed off opposite edges


def test_vehicle_pages_state_only_what_is_recorded_and_do_not_apologise(client):
    for slug in OFFICIAL:
        page = html(client, f"/vehicles/{slug}")
        assert not re.search(r"horsepower|top speed|0-60|\bmph\b|\bkm/h\b|\bbhp\b|\$\d", page, re.I), slug
        assert "Not published by Rockstar" not in page and "Specifications" not in page and "has published one official image" not in page
        assert "Where it appears" not in page                              # no mission or place is recorded for these, so none is shown
        assert 'href="https://www.rockstargames.com/' in page and "Rockstar has not published specifications" not in page   # provenance stays (source link, credit); the explanation is not repeated on every page


def test_a_vehicle_with_one_picture_is_shown_in_crops_named_for_what_they_show(client):
    page = html(client, "/vehicles/vapid-ganado")
    assert 'data-sequence="close"' in page and "data-viewer" not in page and 'class="vd-stage ' not in page and "vd-duo" not in page
    close = page.split('class="vd-seq vd-close"')[1].split("</section>")[0]
    assert re.findall(r"</span>([^<]+)</figcaption>", close) == ["The hood and its red stripes", "The grille and its four headlights", "Behind the wheel"]
    assert close.count('data-zoom="') == 3 and close.count('data-zx="') == 3 and close.count("data-lightbox") == 1      # three crops of the one picture, one link to the whole picture
    assert "In close" in close and "The whole picture" in close


def test_the_viewer_markup_works_without_script(client):
    page = html(client, "/vehicles/vapid-dominator-buggy")
    thumbs = re.findall(r'<a href="(https://www\.rockstargames\.com/[^"]+)" data-thumb', page)
    assert len(thumbs) == 3 and all("imwidth=2560" in t for t in thumbs)
    slides = page.split('class="vd-viewer__slides"')[1].split("</ul>")[0]
    assert slides.count(" hidden") == 2
    thumbnails = page.split('class="vd-viewer__thumbs"')[1].split("</ul>")[0]
    assert "loading=" not in thumbnails and thumbnails.count("<img") == 3          # the thumbnails are never lazy, so none is ever an empty frame
    assert re.search(r"data-captions='\[&#34;|data-captions='\[\"", page) or "data-captions=" in page


def test_dinka_and_kayak_show_a_smaller_labelled_cut_of_the_scene_then_crops_of_their_own_picture(client):
    pages = {slug: html(client, f"/vehicles/{slug}") for slug in ("dinka-enduro", "crest-kayak")}
    for slug, page in pages.items():
        ctx = page.split('class="vd-seq vd-seq--context"')[1].split("</section>")[0]
        assert "own screenshots" in ctx and "The whole scene" in ctx and "data-lightbox" in ctx      # labelled, with the full picture a click away
        assert 'data-zoom="' in ctx and 'data-zx="' in ctx and 'data-zy="' in ctx                                # drawn close around the vehicle
        assert "ULTIMATE_EDITION_SAFEHOUSE_VEHICLES_01" in ctx
        assert page.count("vd-close__art") >= 3                                                                  # then three crops of the machine's own picture
    assert 'vd-stage--right vd-stage--scene' in pages["dinka-enduro"] and 'vd-stage--left vd-stage--scene' in pages["crest-kayak"]
    zooms = {slug: re.search(r'data-zx="(\d+)" data-zy="(\d+)"', p.split('class="vd-seq vd-seq--context"')[1]).groups() for slug, p in pages.items()}
    assert zooms["dinka-enduro"] != zooms["crest-kayak"]                                                       # not the same part of the picture twice


def test_context_cut_keeps_the_vehicle_in_view():
    """The zoom origin puts the vehicle near the middle of its box after zooming."""
    from app.services import site
    for slug, pick in media_slots.GARAGE_PICKS.items():
        ctx = pick.get("context")
        if not ctx:
            continue
        pic = site._context_picture({"slug": ctx["slug"], "title": "t", "embed_url": "x"}, ctx["focus"], ctx["zoom"], 1.45)
        z, zx, zy = float(pic["zoom"]), pic["zx"] / 100, pic["zy"] / 100
        px, py = (int(v.strip("%")) / 100 for v in pic["pos"].split())
        window = 1.45 / (16 / 9)
        bx, by = (ctx["focus"][0] - (1 - window) * px) / window, ctx["focus"][1]
        for box, origin in ((bx, zx), (by, zy)):
            shown = (1 - z) * origin + z * box                      # where the vehicle lands after the zoom, as a fraction of the box
            assert 0.35 <= shown <= 0.65, (slug, shown)                # the vehicle lands near the middle of the box


def test_the_sticky_curtain_is_only_for_a_single_picture_vehicle_and_off_for_reduced_motion():
    sheet = css()
    block = sheet.split(".story--none .vopen { position: sticky")[0].rsplit("@media", 1)[1]
    assert "prefers-reduced-motion: no-preference" in block and "min-width: 900px" in block


def test_the_collection_copy_does_not_name_a_vehicle_the_database_may_lack(client):
    page = html(client, "/vehicles")
    lede = re.search(r'class="coll__lede">([^<]+)<', page).group(1)
    assert "kayak" not in lede.lower() and "motorcycle" not in lede.lower()


def test_connected_world_lists_missions_and_places_with_their_labels(client, app):
    with app.test_request_context("/vehicles/vapid-stanier"):
        vehicle = site.vehicle_detail("vapid-stanier")
        vehicle["missions"] = [{"slug": "ridge-run", "title": "Ridge Run", "mission_type": "activity", "content_status": "demo", "usage_note": "Time-trial car"}]
        vehicle["locations"] = [{"slug": "kalaga-ridge-lookout", "name": "Kalaga Ridge Lookout", "content_status": "official", "region_slug": "mount-kalaga", "region_name": "Mount Kalaga"}]
        page = render_template("vehicles/detail.html", vehicle=vehicle)
    assert "The connected world" in page and "Ridge Run" in page and "Time-trial car" in page and "Kalaga Ridge Lookout" in page
    assert page.count("badge--demo") == 1


def test_next_and_previous_wrap_round_the_collection(client):
    first = html(client, "/vehicles/grotti-cheetah")
    assert 'rel="prev" data-vehicle="crest-kayak"' in first and 'rel="next" data-vehicle="vapid-dominator-buggy"' in first
    last = html(client, "/vehicles/crest-kayak")
    assert 'rel="next" data-vehicle="grotti-cheetah"' in last


def test_related_panels_are_readable_not_oversized_headings():
    sheet = css()
    name = re.search(r"\.neighbour__name \{([^}]*)\}", sheet).group(1)
    assert "var(--t-h3)" in name and "--t-h1" not in name and "--t-display" not in name
    tile = re.search(r"\.tile__model \{([^}]*)\}", sheet).group(1)
    assert "var(--t-h3)" in tile


# ------------------------------------------------------------------ nothing else is touched
def test_garage_styles_only_define_garage_selectors():
    text = re.sub(r"/\*.*?\*/", "", css(), flags=re.S)
    own = ("garage", "cine", "scene", "rail", "gshot", "gbtn", "plate", "coll", "ctl", "gresult", "mosaic", "mrow", "tile", "customs", "gempty", "credit",
           "vopen", "vcrumb", "vintro", "vcredits", "vshow", "mos", "pano", "vctx", "vbody", "viewer", "vworld", "vnext", "neighbour", "story", "vehicle")
    for selector in re.findall(r"(?:^|\})\s*([^{}@]+?)\s*\{", text):
        for part in selector.split(","):
            part = part.strip().replace("html.motion-on ", "")
            if part in ("from", "to") or part.startswith("::view-transition") or part.startswith("[data-vehicle"):
                continue
            first = re.search(r"[.#]([a-z_-]+)", part)
            assert first and first.group(1).split("__")[0].split("--")[0] in own, part


def test_other_sections_do_not_load_the_garage_assets(client):
    for path in ("/", "/characters", "/characters/jason-duval", "/regions", "/locations", "/missions", "/about"):
        page = html(client, path)
        assert "garage.css" not in page and "garage.js" not in page, path


def test_the_homepage_vehicle_showcase_still_renders(client):
    page = html(client, "/")
    assert 'class="slide"' in page and "showroom__item" in page
