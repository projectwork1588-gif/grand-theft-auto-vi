"""The Garage concept (Stage A prototype, /garage-concept): the same MySQL-backed collection laid out as spreads, and an opening built from bays."""
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


def cards(page):
    return re.findall(r'class="gx-card" href="(/vehicles/[a-z-]+)"', page)


@pytest.mark.parametrize("count", range(0, 16))
def test_every_count_of_machines_is_laid_out_without_an_orphan(count):
    plan = site.spread_plan(count)
    assert sum(plan) == count and all(n in (1, 2) for n in plan)
    assert count < 2 or plan[0] != 2 or count == 2          # a pair opens only a two-machine result
    if count >= 3:
        assert plan[:2] == [1, 2]                            # a feature, then a pair, then round again


def test_seven_machines_make_five_spreads_and_the_last_is_the_finale():
    assert site.spread_plan(7) == [1, 2, 1, 2, 1]


def test_the_concept_page_lists_all_seven_machines_in_order_and_links_each_once(client):
    page = html(client, "/garage-concept")
    assert cards(page) == [f"/vehicles/{s}" for s in SLUGS]
    stage = page.split("data-stage")[1].split("</section>")[0]
    assert stage.count("data-panel=") == 7 and stage.count("data-pick=") == 7 and stage.count('fetchpriority="high"') == 1
    assert page.count("<h1") == 1 and 'name="robots" content="noindex"' in page
    assert "Seven machines of Leonida" in page and page.count('class="gx-reel"') == 1


def test_the_concept_collection_is_the_same_database_query_as_the_live_garage(client):
    live = re.findall(r'<h3 class="tile__model">([^<]+)</h3>', html(client, "/vehicles?category=boat"))
    concept = re.findall(r'<h3 class="gx-card__name">([^<]+)</h3>', html(client, "/garage-concept?category=boat"))
    assert sorted(live) == sorted(concept) == ["Kayak", "Squalo"]
    assert re.findall(r'<h3 class="gx-card__name">([^<]+)</h3>', html(client, "/garage-concept?q=kayak")) == ["Kayak"]
    assert re.findall(r'<h3 class="gx-card__name">([^<]+)</h3>', html(client, "/garage-concept?q=zzzz")) == []
    assert "No machine matches that" in html(client, "/garage-concept?q=zzzz")
    names = re.findall(r'<h3 class="gx-card__name">([^<]+)</h3>', html(client, "/garage-concept?sort=name_asc"))
    assert re.findall(r'<h3 class="gx-card__name">([^<]+)</h3>', html(client, "/garage-concept?sort=name_desc")) == list(reversed(names))
    assert len(cards(html(client, "/garage-concept?per_page=3&page=2"))) == 3
    assert client.get("/garage-concept?sort=cheapest").status_code == 400 and client.get("/garage-concept?page=0").status_code == 400


def test_a_single_result_closes_the_page_as_the_finale_and_a_pair_has_no_reel(client):
    sports = html(client, "/garage-concept?category=sports")
    assert 'gx-spread--finale' in sports and 'class="gx-reel"' not in sports
    boats = html(client, "/garage-concept?category=boat")
    assert 'gx-spread--pair' in boats and 'gx-spread--finale' not in boats


def test_machines_with_a_second_picture_are_not_shown_by_the_picture_that_opens_the_page():
    for slug in ("grotti-cheetah", "vapid-dominator-buggy", "shitzu-squalo", "vapid-stanier"):
        spread, pick = media_slots.GARAGE_SPREADS[slug], media_slots.GARAGE_PICKS[slug]
        assert spread["main"] != pick["stage"] and spread["detail"] not in (spread["main"], pick["stage"])
        assert spread["detail_label"]


def test_one_picture_machines_are_drawn_closer_not_repeated_whole():
    for slug in ("vapid-ganado", "dinka-enduro", "crest-kayak"):
        spread = media_slots.GARAGE_SPREADS[slug]
        assert "detail" not in spread and spread["zoom"][0] > 1


def test_the_concept_never_states_a_specification_or_a_not_published_notice(client):
    page = html(client, "/garage-concept")
    assert "has not published" not in page and "not published" not in page
    assert not re.search(r"horsepower|mph|km/h|top speed", page, re.I)


def test_the_concept_uses_no_inline_styles_and_every_cut_it_uses_is_in_the_stylesheet(client):
    page = html(client, "/garage-concept")
    assert not re.search(r"<[^>]+\sstyle=", page)
    garage = (ROOT / "app" / "static" / "css" / "garage.css").read_text(encoding="utf-8")
    for attr in ("data-px", "data-py", "data-pxn", "data-pyn", "data-zoom", "data-zx", "data-zy"):
        for value in set(re.findall(rf'{attr}="([0-9.]+)"', page)):
            assert f'[{attr}="{value}"]' in garage, (attr, value)


def test_concept_styles_only_define_gx_selectors():
    css = (ROOT / "app" / "static" / "css" / "garage_concept.css").read_text(encoding="utf-8")
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    flat = re.sub(r"@media[^{]*\{|@supports[^{]*\{|@property[^{]*\{[^}]*\}|@keyframes[^{]*\{", "", css)
    selectors = [s.strip() for block in re.findall(r"([^{}]+)\{", flat) for s in block.split(",")]
    allowed = re.compile(r"^(html(\.motion-on|:not\(\.motion-on\))?\s+)?(\.gx[\w-]*|\[data-cat=\"[a-z]+\"\]|\.gx\s)")
    stray = [s for s in selectors if s and not allowed.match(s) and not s.startswith("html ")]
    assert not stray, stray[:5]


def test_only_the_concept_page_loads_the_concept_assets(client):
    for path in ("/", "/characters", "/vehicles", "/vehicles/crest-kayak", "/about"):
        page = html(client, path)
        assert "garage_concept" not in page, path
    assert "garage_concept.css" in html(client, "/garage-concept") and "garage_concept.js" in html(client, "/garage-concept")
