"""The Garage concept (/garage-concept): a full-screen opening that cycles through the seven machines by itself, and the same MySQL-backed collection told in four chapters by default and as an honest ordered list when filtered."""
import re
from pathlib import Path

import pytest

from app import local_media, media_slots
from app.services import site

ROOT = Path(__file__).resolve().parent.parent
SLUGS = ["grotti-cheetah", "vapid-dominator-buggy", "shitzu-squalo", "vapid-stanier", "vapid-ganado", "dinka-enduro", "crest-kayak"]
CHAPTER_ORDER = ["grotti-cheetah", "vapid-stanier", "vapid-ganado", "vapid-dominator-buggy", "dinka-enduro", "shitzu-squalo", "crest-kayak"]


def html(client, path):
    response = client.get(path)
    assert response.status_code == 200, path
    return response.get_data(as_text=True)


def machines(page):
    return re.findall(r'class="gx-m gx-m--[a-z_]+ [^"]*" href="(/vehicles/[a-z-]+)"', page)


def names(page):
    return re.findall(r'<h3 class="gx-m__name">([^<]+)</h3>', page)


# ------------------------------------------------------------------ the default collection: four chapters
def test_the_default_collection_is_four_chapters_in_the_planned_order(client):
    page = html(client, "/garage-concept")
    assert re.findall(r'data-chapter="([a-z]+)"', page) == ["performance", "street", "beyond", "water"]
    assert re.findall(r'<h2 id="ch-[a-z]+">([^<]+)</h2>', page) == ["Performance", "Street &amp; Classics", "Beyond the Pavement", "On the Water"]
    assert machines(page) == [f"/vehicles/{s}" for s in CHAPTER_ORDER] and len(set(machines(page))) == 7
    assert page.count("gx-finale reveal") == 1                                       # the Kayak closes the page
    street = page.split('data-chapter="street"')[1].split('data-chapter="beyond"')[0]
    assert "gx-customs__grid" in street and street.count("gx-customs__cell gx-customs__cell--") == 4   # the mod shop is one mosaic inside Street & Classics


def test_each_chapter_is_set_differently_not_as_the_same_card_repeated(client):
    page = html(client, "/garage-concept")
    layouts = [("performance", "gx-perf"), ("street", "gx-street"), ("beyond", "gx-duo"), ("water", "gx-sea-row")]
    for key, cls in layouts:
        block = page.split(f'data-chapter="{key}"')[1].split("</section>")[0]
        assert cls in block, key
    roles = re.findall(r'class="gx-m gx-m--([a-z_]+) ', page)
    assert roles == ["feature", "lead", "second", "duo_a", "duo_b", "sea_a", "finale"]  # seven machines, seven roles


def test_the_mod_shop_keeps_rockstars_set_titles_and_invents_no_model(client):
    page = html(client, "/garage-concept")
    grid = page.split("gx-customs__grid")[1].split("</ul>")[0]
    assert re.findall(r"<figcaption>([^<]+)</figcaption>", grid) == ["Rideout Customs Mod Shop", "One-Eyed Willie&#39;s Mod Shop", "Classic Car Collection", "Classic Car Collection"]
    assert not re.search(r"Cheetah|Dominator|Squalo|Stanier|Ganado|Enduro|Kayak", grid)
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
        assert "data-chapter=" not in page and "gx-customs" not in page and "gx-finale" not in page and "data-sea" not in page, path
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
def test_the_opening_holds_all_seven_scenes_the_index_and_the_showcase_controls(client):
    page = html(client, "/garage-concept")
    stage = page.split("data-stage")[1].split("</section>")[0]
    assert stage.count("data-panel=") == 7 and stage.count("data-pick=") == 7 and stage.count('fetchpriority="high"') == 1
    assert re.findall(r'class="gx-scene gx-scene--([a-z]+)', stage) == ["br", "br", "br", "band", "band", "ml", "ml"]
    assert stage.count('class="gbtn gx-btn"') == 7 and stage.count("data-step=") == 2 and "data-ctl hidden" in stage
    assert page.count("<h1") == 1 and "<video" not in stage
    assert re.search(r'data-play-ui hidden', stage) and 'data-playpause aria-pressed="false" aria-label="Pause the showcase"' in stage      # the control exists only when script can run it
    assert 'class="gx-play__bar"' in stage and "data-count" in stage
    assert stage.count('class="gx-bloom"') == 2                                                  # the two long, low machines glow into their words
    assert "Seven machines of Leonida" in page


def test_the_showcase_clock_is_built_to_wait_and_never_to_scroll():
    js = (ROOT / "app" / "static" / "js" / "garage_concept.js").read_text(encoding="utf-8")
    assert "dwellSeconds >= 2 && dwellSeconds <= 30 ? dwellSeconds : 7" in js                    # seven seconds a scene; 2 to 30 only as a review switch
    for condition in ("userPaused", "document.hidden", "holding.pointer", "holding.focus", "visible", "heading === current", "IntersectionObserver", "visibilitychange", "tv:motion"):
        assert condition in js, condition
    assert "scrollTo(" not in js.replace("list.scrollTo", "") and "scrollIntoView" not in js and "window.scroll" not in js   # it never scrolls the page
    assert "saveData" in js                                                                      # and it does not run on data saver


def test_every_scene_has_a_considered_composition():
    assert set(media_slots.GARAGE_SCENES) == set(SLUGS)
    assert {v["plate"] for v in media_slots.GARAGE_SCENES.values()} <= {"br", "bl", "ml", "band"}
    assert media_slots.GARAGE_SCENES["vapid-stanier"]["plate"] == "band" and media_slots.GARAGE_SCENES["vapid-ganado"]["plate"] == "band"
    assert media_slots.GARAGE_SCENES["dinka-enduro"]["plate"] == "ml"
    for scene in media_slots.GARAGE_SCENES.values():
        for box in scene["subject"]:
            x0, y0, x1, y1 = box
            assert 0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1


def test_machines_with_a_second_picture_are_not_shown_by_the_picture_that_opens_the_page():
    for slug in ("grotti-cheetah", "vapid-dominator-buggy", "shitzu-squalo", "vapid-stanier"):
        spread, pick = media_slots.GARAGE_SPREADS[slug], media_slots.GARAGE_PICKS[slug]
        assert spread["main"] != pick["stage"], slug
    for slug in ("grotti-cheetah", "shitzu-squalo"):
        spread = media_slots.GARAGE_SPREADS[slug]
        assert spread["second"] not in (spread["main"], media_slots.GARAGE_PICKS[slug]["stage"]) and spread["second_label"]
        assert not re.search(r"horsepower|mph|km/h|top speed", spread["second_label"], re.I)


# ------------------------------------------------------------------ the sea clip
def test_the_sea_clip_is_asked_for_only_by_script_and_has_a_still_beneath_it(client):
    page = html(client, "/garage-concept")
    if "data-sea" in page and "gx-sea__video" in page:
        video = re.search(r'<video[^>]*>', page).group(0)
        assert "muted" in video and "playsinline" in video and 'preload="none"' in video and " src=" not in video and "data-src=" in video
        assert "gx-sea__still" in page.split("data-sea")[1].split("</div>")[0]
        assert "autoplay" not in video                                                          # script decides, and only when motion is allowed
    assert "<video" not in html(client, "/vehicles")


def test_garage_clips_are_servable_from_their_own_folder_and_only_that():
    assert local_media.SAFE_NAME.match("clips/garage/on-the-water.mp4") and local_media.SAFE_NAME.match("clips/garage/on-the-water.jpg")
    for bad in ("clips/garage/../secret.mp4", "clips/garage/sub/x.mp4", "garage/on-the-water.mp4", "clips/garage/On-The-Water.mp4", "clips/garage/x.exe"):
        assert not local_media.SAFE_NAME.match(bad), bad


# ------------------------------------------------------------------ technical guards
def test_the_concept_uses_no_inline_styles_and_every_cut_it_uses_is_in_the_stylesheet(client):
    garage = (ROOT / "app" / "static" / "css" / "garage.css").read_text(encoding="utf-8")
    for path in ("/garage-concept", "/garage-concept?category=boat"):
        page = html(client, path)
        assert not re.search(r"<[^>]+\sstyle=", page)
        for attr in ("data-px", "data-py", "data-pxn", "data-pyn", "data-zoom", "data-zx", "data-zy"):
            for value in set(re.findall(rf'{attr}="([0-9.]+)"', page)):
                assert f'[{attr}="{value}"]' in garage, (attr, value)


def test_concept_styles_only_define_gx_selectors_and_never_catch_presses_over_a_link():
    css = (ROOT / "app" / "static" / "css" / "garage_concept.css").read_text(encoding="utf-8")
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    flat = re.sub(r"@media[^{]*\{|@supports[^{]*\{|@property[^{]*\{[^}]*\}|@keyframes[^{]*\{", "", css)
    selectors = [s.strip() for block in re.findall(r"([^{}]+)\{", flat) for s in block.split(",")]
    allowed = re.compile(r"^(html(\.motion-on|:not\(\.motion-on\))?\s+)?(\.gx[\w-]*|\[data-cat=\"[a-z]+\"\]|\[data-chapter=\"[a-z]+\"\]|\.gx\s)")
    stray = [s for s in selectors if s and not allowed.match(s) and not (s.startswith("html") and "gx-" in s) and not re.fullmatch(r"from|to|[0-9]+%", s)]
    assert not stray, stray[:5]
    assert re.search(r"\.gx-scene\.is-leaving \{[^}]*pointer-events: none", css)
    for decoration in (".gx-grade", ".gx-pic__veil"):
        assert re.search(re.escape(decoration) + r" \{[^}]*pointer-events: none", css), decoration
    assert re.search(r"\.gx-sea \{[^}]*", css) and "gx-sea__video" in css


def test_only_the_concept_page_loads_the_concept_assets(client):
    for path in ("/", "/characters", "/vehicles", "/vehicles/crest-kayak", "/about"):
        assert "garage_concept" not in html(client, path), path
    page = html(client, "/garage-concept")
    assert "garage_concept.css" in page and "garage_concept.js" in page
