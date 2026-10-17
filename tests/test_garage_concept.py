"""The Garage concept (Stage A.2, /garage-concept): a full-screen opening and the same MySQL-backed collection, told in four chapters by default and as an honest ordered list when filtered."""
import re
from pathlib import Path

import pytest

from app import media_slots
from app.services import site

ROOT = Path(__file__).resolve().parent.parent
SLUGS = ["grotti-cheetah", "vapid-dominator-buggy", "shitzu-squalo", "vapid-stanier", "vapid-ganado", "dinka-enduro", "crest-kayak"]


def html(client, path):
    response = client.get(path)
    assert response.status_code == 200, path
    return response.get_data(as_text=True)


def machines(page):
    return re.findall(r'class="gx-m gx-m--[a-z]+" href="(/vehicles/[a-z-]+)"', page)


def names(page):
    return re.findall(r'<h3 class="gx-m__name">([^<]+)</h3>', page)


# ------------------------------------------------------------------ the default collection: four chapters
def test_the_default_collection_is_four_chapters_in_the_planned_order(client):
    page = html(client, "/garage-concept")
    assert re.findall(r'data-chapter="([a-z]+)"', page) == ["performance", "street", "beyond", "water"]
    assert re.findall(r'<h2 id="ch-[a-z]+">([^<]+)</h2>', page) == ["Performance", "Street &amp; Classics", "Beyond the Pavement", "On the Water"]
    assert machines(page) == [f"/vehicles/{s}" for s in ["grotti-cheetah", "vapid-stanier", "vapid-ganado", "vapid-dominator-buggy", "dinka-enduro", "shitzu-squalo", "crest-kayak"]]
    assert len(set(machines(page))) == 7
    assert page.count("gx-finale reveal") == 1 and page.count('class="gx-customs"') == 1       # the Kayak closes the page; the mod shop sits inside Street & Classics
    street = page.split('data-chapter="street"')[1].split('data-chapter="beyond"')[0]
    assert "gx-customs__strip" in street and street.count("gx-customs__cell ") == 4


def test_the_mod_shop_keeps_rockstars_set_titles_and_invents_no_model(client):
    page = html(client, "/garage-concept")
    strip = page.split("gx-customs__strip")[1].split("</ul>")[0]
    assert re.findall(r"<figcaption>([^<]+)</figcaption>", strip) == ["Rideout Customs Mod Shop", "One-Eyed Willie&#39;s Mod Shop", "Classic Car Collection", "Classic Car Collection"]
    assert not re.search(r"Cheetah|Dominator|Squalo|Stanier|Ganado|Enduro|Kayak", strip)
    assert "has not published" not in page and "not published" not in page


def test_chapters_keep_only_the_machines_the_database_has_and_nothing_is_lost():
    rows = [{"slug": s, "card": None, "category_slug": "x"} for s in ["grotti-cheetah", "vapid-stanier", "shitzu-squalo", "an-unlisted-machine"]]
    chapters = site._chapters(rows, {})
    assert [(c["key"], [m["slug"] for m in c["machines"]]) for c in chapters] == [
        ("performance", ["grotti-cheetah"]), ("street", ["vapid-stanier"]), ("water", ["shitzu-squalo"]), ("more", ["an-unlisted-machine"])]
    assert site._chapters([], {}) == []


def test_the_chapter_lines_are_visual_themes_not_claims():
    for chapter in media_slots.GARAGE_CHAPTERS:
        assert not re.search(r"horsepower|mph|km/h|top speed|fastest|rare|limited|category", chapter["line"], re.I)
    assert [c["slugs"] for c in media_slots.GARAGE_CHAPTERS] == [("grotti-cheetah",), ("vapid-stanier", "vapid-ganado"), ("vapid-dominator-buggy", "dinka-enduro"), ("shitzu-squalo", "crest-kayak")]


# ------------------------------------------------------------------ a filtered collection is an honest list
def test_any_filter_search_sort_or_page_gives_an_ordered_list_not_chapters(client):
    for path in ("/garage-concept?category=boat", "/garage-concept?q=vapid", "/garage-concept?sort=name_asc", "/garage-concept?per_page=3&page=2"):
        page = html(client, path)
        assert "data-chapter=" not in page and 'class="gx-customs"' not in page and "gx-finale" not in page, path
        assert 'class="container--wide gx-list"' in page, path


def test_the_list_keeps_the_databases_counts_and_ordering(client):
    assert sorted(names(html(client, "/garage-concept?category=boat"))) == ["Kayak", "Squalo"]
    assert names(html(client, "/garage-concept?q=kayak")) == ["Kayak"]
    asc = names(html(client, "/garage-concept?sort=name_asc"))
    assert len(asc) == 7 and names(html(client, "/garage-concept?sort=name_desc")) == list(reversed(asc))
    live = re.findall(r'<h3 class="tile__model">([^<]+)</h3>', html(client, "/vehicles?sort=name_desc"))
    assert names(html(client, "/garage-concept?sort=name_desc")) == live                          # the same order as the live Garage, machine for machine
    assert len(machines(html(client, "/garage-concept?per_page=3&page=2"))) == 3
    assert "<b>2</b> machines in <b>Boats</b>" in re.sub(r"\s+", " ", html(client, "/garage-concept?category=boat"))


def test_an_empty_search_and_bad_input_are_handled(client):
    page = html(client, "/garage-concept?q=zzzz")
    assert "No machine matches that" in page and machines(page) == [] and 'href="/garage-concept#showroom"' in page
    assert client.get("/garage-concept?sort=cheapest").status_code == 400 and client.get("/garage-concept?page=0").status_code == 400


# ------------------------------------------------------------------ the opening
def test_the_opening_holds_all_seven_scenes_and_the_index(client):
    page = html(client, "/garage-concept")
    stage = page.split("data-stage")[1].split("</section>")[0]
    assert stage.count("data-panel=") == 7 and stage.count("data-pick=") == 7 and stage.count('fetchpriority="high"') == 1
    assert re.findall(r'class="gx-scene gx-scene--([a-z]+)', stage) == ["br", "br", "br", "band", "band", "ml", "ml"]
    assert stage.count('class="gbtn gx-btn"') == 7 and stage.count("data-step=") == 2 and "data-ctl hidden" in stage
    assert page.count("<h1") == 1 and "<video" not in stage and "autoplay" not in stage.lower()
    assert "Seven machines of Leonida" in page


def test_every_scene_has_a_considered_composition():
    assert set(media_slots.GARAGE_SCENES) == set(SLUGS)
    assert {v["plate"] for v in media_slots.GARAGE_SCENES.values()} <= {"br", "bl", "ml", "band"}
    # the long, low machines (which fill the width of the picture) have their words in a band beneath it, where nothing can cross the machine
    assert media_slots.GARAGE_SCENES["vapid-stanier"]["plate"] == "band" and media_slots.GARAGE_SCENES["vapid-ganado"]["plate"] == "band"
    assert media_slots.GARAGE_SCENES["dinka-enduro"]["plate"] == "ml"


def test_machines_with_a_second_picture_are_not_shown_by_the_picture_that_opens_the_page():
    for slug in ("grotti-cheetah", "vapid-dominator-buggy", "shitzu-squalo", "vapid-stanier"):
        spread, pick = media_slots.GARAGE_SPREADS[slug], media_slots.GARAGE_PICKS[slug]
        assert spread["main"] != pick["stage"] and spread["detail"] not in (spread["main"], pick["stage"])
        assert spread["detail_label"]
        assert not re.search(r"horsepower|mph|km/h|top speed", spread["detail_label"], re.I)


def test_a_tall_picture_keeps_its_name_beneath_it_so_it_never_crosses_the_machine(client):
    page = html(client, "/garage-concept")
    for slug in ("vapid-ganado", "dinka-enduro"):
        block = page.split(f'href="/vehicles/{slug}" data-vehicle="{slug}"')[1].split("</a>")[0]
        main = block.split("gx-pic--main")[1].split("gx-pic__veil")[0]
        assert "gx-m__name" not in main                                                       # the name is not inside the picture
        assert "gx-m__title--below" in block


# ------------------------------------------------------------------ technical guards
def test_the_concept_uses_no_inline_styles_and_every_cut_it_uses_is_in_the_stylesheet(client):
    for path in ("/garage-concept", "/garage-concept?category=boat"):
        page = html(client, path)
        assert not re.search(r"<[^>]+\sstyle=", page)
        garage = (ROOT / "app" / "static" / "css" / "garage.css").read_text(encoding="utf-8")
        for attr in ("data-px", "data-py", "data-pxn", "data-pyn", "data-zoom", "data-zx", "data-zy"):
            for value in set(re.findall(rf'{attr}="([0-9.]+)"', page)):
                assert f'[{attr}="{value}"]' in garage, (attr, value)


def test_concept_styles_only_define_gx_selectors_and_never_catch_presses_over_a_link():
    css = (ROOT / "app" / "static" / "css" / "garage_concept.css").read_text(encoding="utf-8")
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    flat = re.sub(r"@media[^{]*\{|@supports[^{]*\{|@property[^{]*\{[^}]*\}|@keyframes[^{]*\{", "", css)
    selectors = [s.strip() for block in re.findall(r"([^{}]+)\{", flat) for s in block.split(",")]
    allowed = re.compile(r"^(html(\.motion-on|:not\(\.motion-on\))?\s+)?(\.gx[\w-]*|\[data-cat=\"[a-z]+\"\]|\[data-chapter=\"[a-z]+\"\]|\.gx\s)")
    stray = [s for s in selectors if s and not allowed.match(s) and not (s.startswith("html") and "gx-" in s)]
    assert not stray, stray[:5]
    # a scene being replaced cannot be pressed, and every layer that only decorates is transparent to the pointer
    assert re.search(r"\.gx-scene\.is-leaving \{[^}]*pointer-events: none", css)
    for decoration in (".gx-grade", ".gx-pic__veil"):
        assert re.search(re.escape(decoration) + r" \{[^}]*pointer-events: none", css), decoration


def test_only_the_concept_page_loads_the_concept_assets(client):
    for path in ("/", "/characters", "/vehicles", "/vehicles/crest-kayak", "/about"):
        assert "garage_concept" not in html(client, path), path
    page = html(client, "/garage-concept")
    assert "garage_concept.css" in page and "garage_concept.js" in page
