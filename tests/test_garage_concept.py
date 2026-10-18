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
    """Every machine the collection links to, in page order (a stage, a half of the diptych, or a card of a filtered list)."""
    return re.findall(r'<a class="gx-(?:f|d|m) [^"]*" href="(/vehicles/[a-z-]+)"', page)


def names(page):
    return re.findall(r'<h3 class="gx-(?:m|f)__name">([^<]+)</h3>', page)


# ------------------------------------------------------------------ the default collection: four chapters
def test_the_default_collection_is_four_chapters_in_the_planned_order(client):
    page = html(client, "/garage-concept")
    assert re.findall(r'data-chapter="([a-z]+)"', page) == ["performance", "street", "beyond", "water"]
    assert re.findall(r'<h2 id="ch-[a-z]+">([^<]+)</h2>', page) == ["Performance", "Street &amp; Classics", "Beyond the Pavement", "On the Water"]
    assert machines(page) == [f"/vehicles/{s}" for s in CHAPTER_ORDER] and len(set(machines(page))) == 7
    assert page.count("gx-f--finale") == 1 and page.rindex("gx-f--finale") > page.rindex("gx-f--sea_a")      # the Kayak closes the page, after the Squalo
    street = page.split('data-chapter="street"')[1].split('data-chapter="beyond"')[0]
    assert "gx-customs__rail" in street and street.count('class="gx-customs__cell"') == 4                     # the mod shop is one strip inside Street & Classics


def test_each_chapter_is_set_differently_not_as_the_same_card_repeated(client):
    page = html(client, "/garage-concept")
    layouts = [("performance", "gx-f--perf"), ("street", "gx-f--street_a"), ("street", "gx-f--street_b"), ("beyond", "gx-duo"), ("water", "gx-f--sea_a"), ("water", "gx-f--finale")]
    for key, cls in layouts:
        block = page.split(f'data-chapter="{key}"')[1].split("</section>")[0]
        assert cls in block, (key, cls)
    # the zigzag: the first street machine's picture bleeds off the left edge, the second's off the right
    assert "gx-f--street_a gx-f--art-left" in page and "gx-f--street_b gx-f--art-right" in page
    stages = re.findall(r'<a class="gx-([fd]) gx-[fd]--([a-z_]+)', page)
    assert [r for _, r in stages] == ["perf", "street_a", "street_b", "a", "b", "sea_a", "finale"]               # seven machines, seven places


def test_a_machine_with_a_second_picture_shows_it_as_a_small_labelled_detail(client):
    page = html(client, "/garage-concept")
    assert re.findall(r'<span class="gx-f__label">([^<]+)</span>', page) == ["The cabin", "The tail fin", "On deck"]
    perf = page.split('data-chapter="performance"')[1].split("</section>")[0]
    assert perf.index("gx-f__art") < perf.index("gx-f__inset")                                                   # the exterior leads, the cabin supports it


def test_the_water_chapter_is_two_clean_stages_with_a_horizon_between_and_no_overlap(client):
    page = html(client, "/garage-concept")
    water = page.split('data-chapter="water"')[1].split("</section>")[0]
    assert water.index("gx-f--sea_a") < water.index("gx-sea__horizon") < water.index("gx-f--finale")          # the Squalo, a line of low sun, then the Kayak
    css = (ROOT / "app" / "static" / "css" / "garage_concept.css").read_text(encoding="utf-8")
    sea = css.split("/* ---- On the Water:")[1].split("/* a search, a category")[0]
    assert not re.search(r"margin-top:\s*calc\(-1|margin-top:\s*-", sea)                                      # nothing is pulled up over the stage before it


def test_the_water_chapter_is_stills_only_and_has_no_video(client):
    for path in ("/garage-concept", "/garage-concept?category=boat"):
        page = html(client, path)
        assert "<video" not in page and ".mp4" not in page, path
    css = (ROOT / "app" / "static" / "css" / "garage_concept.css").read_text(encoding="utf-8")
    js = (ROOT / "app" / "static" / "js" / "garage_concept.js").read_text(encoding="utf-8")
    assert "sticky" not in css and "gx-sea__video" not in css and "video" not in js.replace("Leaving for a vehicle", "")   # nothing pins the page or loads a clip


def test_the_mod_shop_keeps_rockstars_set_titles_and_invents_no_model(client):
    page = html(client, "/garage-concept")
    strip = page.split("gx-customs__track")[1].split("</ul>")[0]
    assert re.findall(r"<figcaption>([^<]+)</figcaption>", strip) == ["Rideout Customs Mod Shop", "One-Eyed Willie&#39;s Mod Shop", "Classic Car Collection", "Classic Car Collection"]
    assert not re.search(r"Cheetah|Dominator|Squalo|Stanier|Ganado|Enduro|Kayak", strip)
    assert "has not published" not in page and "not published" not in page


def test_the_strip_and_the_chapter_index_are_reachable_without_a_pointer(client):
    page = html(client, "/garage-concept")
    assert re.search(r'class="gx-customs__rail[^"]*" data-strip tabindex="0" role="region" aria-label="[^"]+"', page)
    assert page.count("data-strip-step=") == 2 and "data-strip-ctl hidden" in page                                # the buttons exist only when script can work them
    rail = page.split("data-chapter-rail")[1].split("</nav>")[0]
    assert re.findall(r'href="#chapter-([a-z]+)"', rail) == ["performance", "street", "beyond", "water"]
    assert "data-chapter-rail" not in html(client, "/garage-concept?category=boat")                              # a filtered list has no chapters to point at


def test_the_words_about_each_machine_describe_the_pictures_and_claim_nothing():
    assert set(media_slots.GARAGE_COPY) == set(SLUGS)
    for slug, line in media_slots.GARAGE_COPY.items():
        assert 25 < len(line) < 90 and line.endswith("."), slug
        assert not re.search(r"horsepower|\bhp\b|mph|km/h|top speed|fastest|price|\$|rare|limited|mission|available", line, re.I), slug
    assert "A Dominator rebuilt for mud and dirt." not in " ".join(media_slots.GARAGE_COPY.values())


def test_the_page_prints_the_editorial_lines_and_the_database_keeps_its_own_summary(client):
    page = html(client, "/garage-concept")
    for line in media_slots.GARAGE_COPY.values():
        assert line in page
    assert "A Dominator rebuilt for mud and dirt." not in page and "A green trail bike against a teal garage door." not in page and "A white speedboat on the bay at dusk." not in page


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
    assert re.findall(r'class="gx-scene gx-scene--([a-z]+)', stage) == ["br", "br", "br", "tr", "tr", "ml", "ml"]
    assert stage.count('class="gbtn gx-btn"') == 7 and stage.count("data-step=") == 2 and "data-ctl hidden" in stage
    assert page.count("<h1") == 1 and "<video" not in stage
    # no play or pause control anywhere in the opening (it just runs); progress is a ring on the lit number
    assert "data-playpause" not in page and "gx-pause" not in page and not re.search(r"(?i)(pause|resume) the showcase", page)
    assert "gx-play " not in stage and "data-count" not in stage and stage.count("gx-tick__ring") == 7
    assert stage.count('class="gx-bloom"') == 7                                                  # each scene has its own colours to glow with (shown for the two long, low machines, and on a nearly square window)
    assert len(re.findall(r'class="gx-bloom" aria-hidden="true">\s*<img[^>]*loading="lazy"', stage)) == 7                # none of them is fetched before it is shown
    assert "Seven machines of Leonida" in page


def test_the_showcase_clock_is_built_to_wait_and_never_to_scroll():
    js = (ROOT / "app" / "static" / "js" / "garage_concept.js").read_text(encoding="utf-8")
    assert "dwellSeconds >= 2 && dwellSeconds <= 30 ? dwellSeconds : 3" in js                    # three seconds a scene; 2 to 30 only as a review switch
    for condition in ("userPaused", "document.hidden", "holding.pointer", "holding.focus", "visible", "heading === current", "IntersectionObserver", "visibilitychange", "tv:motion"):
        assert condition in js, condition
    assert "scrollTo(" not in js.replace("list.scrollTo", "").replace("railEl.scrollTo", "") and "scrollIntoView" not in js and "window.scroll" not in js   # it never scrolls the page
    assert "saveData" in js                                                                      # and it does not run on data saver
    assert 'var interactive = ".gx-copy";' in js
    assert "playBtn" not in js and "data-playpause" not in js and "Pause the showcase" not in js    # the removed control leaves no dead code behind
    assert 'classList.toggle("is-paused", userPaused || document.hidden || !visible)' in js        # the camera stops with the clock                                                 # only the words and Explore hold the clock: a choice in the index never stops it


def test_every_scene_has_a_considered_composition():
    assert set(media_slots.GARAGE_SCENES) == set(SLUGS)
    assert {v["plate"] for v in media_slots.GARAGE_SCENES.values()} <= {"br", "bl", "ml", "tr"}
    assert media_slots.GARAGE_SCENES["vapid-stanier"]["plate"] == "tr" and media_slots.GARAGE_SCENES["vapid-ganado"]["plate"] == "tr"   # their words sit top right, in the sky above the hood
    assert media_slots.GARAGE_SCENES["dinka-enduro"]["plate"] == "ml"
    for scene in media_slots.GARAGE_SCENES.values():
        for box in scene["subject"]:
            x0, y0, x1, y1 = box
            assert 0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1


def test_machines_with_a_second_picture_are_not_shown_by_the_picture_that_opens_the_page():
    for slug in ("grotti-cheetah", "vapid-dominator-buggy", "shitzu-squalo", "vapid-stanier"):
        spread, pick = media_slots.GARAGE_SPREADS[slug], media_slots.GARAGE_PICKS[slug]
        assert spread["main"] != pick["stage"], slug
    for slug in ("grotti-cheetah", "vapid-stanier", "shitzu-squalo"):
        spread = media_slots.GARAGE_SPREADS[slug]
        assert spread["second"] not in (spread["main"], media_slots.GARAGE_PICKS[slug]["stage"]) and spread["second_label"]
        assert not re.search(r"horsepower|mph|km/h|top speed", spread["second_label"], re.I)


# ------------------------------------------------------------------ generated clips
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
    flat = re.sub(r"@media[^{]*\{|@container[^{]*\{|@supports[^{]*\{|@property[^{]*\{[^}]*\}|@keyframes[^{]*\{", "", css)
    selectors = [s.strip() for block in re.findall(r"([^{}]+)\{", flat) for s in block.split(",")]
    allowed = re.compile(r"^(html(\.motion-on|:not\(\.motion-on\))?\s+)?(\.gx[\w-]*|\[data-cat=\"[a-z]+\"\]|\[data-chapter=\"[a-z]+\"\]|\.gx\s)")
    stray = [s for s in selectors if s and not allowed.match(s) and not (s.startswith("html") and "gx-" in s) and not re.fullmatch(r"from|to|[0-9]+%", s)]
    assert not stray, stray[:5]
    assert re.search(r"\.gx-scene\.is-leaving \{[^}]*pointer-events: none", css)
    assert ".gx-pause" not in css and "gx-drift" not in css                                         # no leftovers of the removed control or the old settle
    assert "@keyframes gx-push" in css and "html.motion-on .gx-scene.is-active .gx-art .gshot, html.motion-on .gx-scene.is-leaving .gx-art .gshot" in css   # the camera runs under the arriving scene and the one leaving
    assert not re.search(r"@keyframes gx-push \{[^}]*(width|height|top|left|margin|padding)", css)  # it only transforms: nothing is laid out again
    assert not re.search(r"is-leaving \.gx-art \.gshot \{[^}]*transform: none", css)                # and the scene being replaced is never snapped back
    for decoration in (".gx-grade", ".gx-f__shade", ".gx-tick__ring"):
        assert re.search(re.escape(decoration) + r" \{[^}]*pointer-events: none", css), decoration


def test_only_the_concept_page_loads_the_concept_assets(client):
    for path in ("/", "/characters", "/vehicles", "/vehicles/crest-kayak", "/about"):
        assert "garage_concept" not in html(client, path), path
    page = html(client, "/garage-concept")
    assert "garage_concept.css" in page and "garage_concept.js" in page


def test_every_scene_has_its_own_small_camera_move_that_cannot_bare_an_edge():
    css = (ROOT / "app" / "static" / "css" / "garage_concept.css").read_text(encoding="utf-8")
    for slug in SLUGS:
        rule = re.search(r'\.gx-scene\[data-vehicle="' + slug + r'"\] \.gx-art \.gshot \{([^}]*)\}', css)
        assert rule, slug
        values = {k: float(v) for k, v in re.findall(r"--(fx|fy|zf|dx|dy):\s*(-?[0-9.]+)%?", rule.group(1))}
        assert set(values) == {"fx", "fy", "zf", "dx", "dy"}, slug
        assert 20 <= values["fx"] <= 80 and 20 <= values["fy"] <= 80, slug                           # centred on the machine, never at an edge
        assert 1.02 <= values["zf"] <= 1.07, slug                                                    # a push of two to seven percent: restrained
        # the drift must stay inside the margin the push opens up on the side it bares: (zoom - 1) times the distance from the centre to that edge
        margin_x = (values["zf"] - 1) * 100 * min(values["fx"], 100 - values["fx"]) / 100
        margin_y = (values["zf"] - 1) * 100 * min(values["fy"], 100 - values["fy"]) / 100
        assert abs(values["dx"]) <= margin_x and abs(values["dy"]) <= margin_y, slug
    assert css.count("animation: gx-push 5s") == 1 and "gx-open .7s" in css                        # one camera, over a little longer than a scene's three seconds and its opening
