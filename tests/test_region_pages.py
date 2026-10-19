"""Leonida / Regions: the index and the six region pages. Official GTA VI only: every picture is one of Rockstar's own, every claim is the database's, and the places and
stories Team Valkyrie invented (content_status 'demo') are never presented as part of a region. They stay in the database, the API and the Locations and Stories pages, where
they are labelled as originals, so nothing that depends on them breaks."""
import re
from pathlib import Path

import pytest

from app import media_slots
from app.repositories import media as media_repo
from app.repositories import regions as regions_repo
from app.services import site

ROOT = Path(__file__).resolve().parent.parent
SLUGS = ["vice-city", "leonida-keys", "grassrivers", "port-gellhorn", "ambrosia", "mount-kalaga"]
NAMES = ["Vice City", "Leonida Keys", "Grassrivers", "Port Gellhorn", "Ambrosia", "Mount Kalaga"]
INVENTED_PLACES = ["Sunset Pier Boardwalk", "Neon Row District", "Bayfront Studio Lot", "Coral Hook Marina", "Heron Reach", "Pelican Quay", "Smokestack Row", "Kalaga Ridge Lookout"]
INVENTED_STORIES = ["Harbour Lights", "Quiet Water", "Last Call at Smokestack Row", "Ridge Run", "Ledger of Favours"]


def page(client, path):
    response = client.get(path)
    assert response.status_code == 200, path
    return response.get_data(as_text=True)


# ------------------------------------------------------------------ the index
def test_the_index_has_the_six_regions_in_rockstars_order_each_linked(client):
    p = page(client, "/regions")
    assert p.count("<h1") == 1 and "Six regions, one state" in p
    assert re.findall(r'<h2 class="rg-title rg-title--feature" id="f-[a-z-]+">([^<]+)</h2>', p) == NAMES
    for slug in SLUGS:
        assert f'href="/regions/{slug}"' in p and f'id="{slug}"' in p
    assert "regions.css" in p and "regions.js" in p


def test_the_index_has_a_working_jump_index_in_the_opening_and_a_compact_one_for_script(client):
    p = page(client, "/regions")
    opening = p.split('class="rg-index"')[1].split("</nav>")[0]
    assert re.findall(r'href="#([a-z-]+)" data-jump', opening) == SLUGS             # plain anchors: it works without script
    bar = p.split("data-jump-bar")[1].split("</nav>")[0]
    assert re.findall(r'href="#([a-z-]+)" data-jump', bar) == SLUGS and " hidden" in p.split("data-jump-bar")[1][:12]   # shown by script only
    js = (ROOT / "app" / "static" / "js" / "regions.js").read_text(encoding="utf-8")
    assert "innerHTML" not in js and "eval(" not in js and "[data-chapter]" not in js       # nothing that could clash with the site's own script


def test_the_index_states_what_is_confirmed_and_counts_only_rockstars_pictures(client):
    p = page(client, "/regions")
    assert "What is confirmed" in p and "Where Rockstar has not said, nothing is made up" in p
    assert "place to explore" not in p and "places to explore" not in p
    pictures = [int(n) for n in re.findall(r"(\d+) of Rockstar(?:&rsquo;|’|')s pictures", p)]
    assert pictures == [9, 6, 6, 4, 4, 7]                                                 # the database's own count per region


# ------------------------------------------------------------------ the six pages
@pytest.mark.parametrize("slug", SLUGS)
def test_every_region_page_has_the_shared_skeleton(client, slug):
    p = page(client, f"/regions/{slug}")
    assert p.count("<h1") == 1 and 'class="rg-title"' in p and f'data-region="{slug}"' in p
    assert '<header class="rgh">' in p and 'id="about"' in p and 'href="#about"' in p
    assert 'class="rg-crumb"' in p and 'href="/regions"' in p and 'aria-label="All regions"' in p
    assert "Rockstar" in p and "not affiliated with Rockstar Games" in p                # attribution and the disclaimer
    assert "regions.css" in p


def test_previous_and_next_walk_all_six_regions_and_come_back_round(client):
    seen, slug = [], SLUGS[0]
    for _ in range(6):
        seen.append(slug)
        p = page(client, f"/regions/{slug}")
        after = re.search(r'rel="next" data-region-link="([a-z-]+)"', p).group(1)
        before = re.search(r'rel="prev" data-region-link="([a-z-]+)"', p).group(1)
        assert after != slug and before != slug and after in SLUGS and before in SLUGS
        slug = after
    assert seen == SLUGS and slug == SLUGS[0]                                           # Rockstar's order, and the seventh step is the first again


@pytest.mark.parametrize("slug", SLUGS)
def test_the_page_shows_all_of_the_regions_pictures_once_each_and_only_rockstars(app, client, slug):
    with app.app_context():
        region = site.region_detail(slug)
        shown = [m["slug"] for m in (region["hero"], region["postcard"], region["intro"]) if m] + [m["slug"] for m in region["pics"]]
        everything = [m["slug"] for m in media_repo.for_entity("region", regions_repo.ids_by_slug([slug])[slug], limit=24)]
    assert sorted(shown) == sorted(everything) and len(set(shown)) == len(shown)
    p = page(client, f"/regions/{slug}")
    images = re.findall(r'<img class="rshot[^"]*" src="([^"]+)"', p)
    assert images and all(src.startswith("https://www.rockstargames.com/") for src in images)     # official hosts only (image_src refuses any other)
    assert all('referrerpolicy="no-referrer"' in tag for tag in re.findall(r"<img [^>]*rshot[^>]*>", p))


@pytest.mark.parametrize("slug", SLUGS)
def test_every_picture_but_the_opening_opens_full_size_in_the_sites_viewer_with_its_title(app, client, slug):
    with app.app_context():
        expected = site.region_detail(slug)["picture_count"] - 1                      # every picture of the region but the one that opens the page
    p = page(client, f"/regions/{slug}")
    links = re.findall(r'<a class="rg-lb[^"]*" href="(https://www\.rockstargames\.com/[^"]+imwidth=2560)" data-lightbox data-caption="([^"]+)"', p)
    assert len(links) == p.count("data-lightbox") == expected >= 3
    assert all("official" in title.lower() or "postcard" in title.lower() for _, title in links)
    assert p.count("data-gallery") == 1 and p.index("data-gallery") < p.index('id="about"')      # one viewer group, so previous and next run through them all


def test_the_postcard_is_shown_as_rockstars_own_artwork(client):
    p = page(client, "/regions/port-gellhorn")
    assert "The postcard" in p and re.search(r"Rockstar(?:&rsquo;|&#39;|')s own artwork for Port Gellhorn", p) and "Port Gellhorn postcard (official artwork)" in p


def test_all_six_regions_share_one_structure_and_differ_in_their_photography(app, client):
    art = media_slots.REGION_ART
    counts = {"vice-city": 6, "leonida-keys": 3, "grassrivers": 3, "port-gellhorn": 2, "ambrosia": 2, "mount-kalaga": 4}      # the pictures after the opening, the one beside the text and the postcard
    heroes = set()
    for slug in SLUGS:
        p = page(client, f"/regions/{slug}")
        assert p.count('<header class="rgh">') == 1 and p.count('class="rga') >= 1 and p.count('class="rgs"') == 1 and p.count('class="rgn"') == 1, slug
        assert f'data-n="{counts[slug]}"' in p, slug
        assert ("rga--plain" in p) == (art[slug]["intro"] is None), slug                # only the two regions Rockstar has shown least stand without a picture beside the text
        heroes.add(art[slug]["hero"])
    assert len(heroes) == 6 and {s for s in SLUGS if art[s]["intro"] is None} == {"port-gellhorn", "ambrosia"}
    landing = page(client, "/regions")
    assert re.findall(r'<section class="rgf( rgf--flip)?" id="([a-z-]+)"', landing) == [("", "vice-city"), (" rgf--flip", "leonida-keys"), ("", "grassrivers"), (" rgf--flip", "port-gellhorn"), ("", "ambrosia"), (" rgf--flip", "mount-kalaga")]


def test_the_stylesheet_uses_one_hero_one_title_scale_and_no_effects_that_compete_with_the_pictures():
    css = (ROOT / "app" / "static" / "css" / "regions.css").read_text(encoding="utf-8")
    assert css.count("\n.rgh {") == 1 and ".rgh--" not in css and ".rgf--neon" not in css and ".rgs--" not in css
    for effect in ("mask-image", "skew", "blur(", "repeating-linear-gradient", "mix-blend-mode"):
        assert effect not in css.replace("backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px);", ""), effect       # only the compact index blurs what is behind it
    assert "clip-path: polygon(11% 0, 100% 0, 100% 100%, 0 100%)" in css                    # the one slant, shared by all six
    assert "animation-timeline" not in css


# ------------------------------------------------------------------ wording that Rockstar's own pages support (migration 007)
def test_no_region_is_described_as_the_territory_of_a_character_unless_rockstars_text_says_so(client):
    texts = {}
    for slug in SLUGS:
        body = client.get(f"/api/v1/regions/{slug}").get_json()
        d = body.get("data", body)
        texts[slug] = d["summary"] + " " + d["description"]
    for slug in ("grassrivers", "port-gellhorn"):
        assert "Real Dimez" not in texts[slug] and "Raul" not in texts[slug] and "turf" not in texts[slug] and "heist" not in texts[slug], slug
    assert "Boobie Ike" in texts["vice-city"] and "Jason" in texts["leonida-keys"] and "Brian Heder" in texts["leonida-keys"]       # Rockstar's own text places these


def test_migration_007_changes_only_the_wording_of_two_regions_and_the_seed_mirrors_it():
    sql = (ROOT / "database" / "migrations" / "007_region_wording.sql").read_text(encoding="utf-8")
    statements = [line for line in sql.splitlines() if line.startswith("UPDATE")]
    assert len(statements) == 2 and all(line.startswith("UPDATE regions SET summary = ") and "WHERE slug = '" in line and "content_status = 'official'" in line for line in statements)
    assert {re.search(r"WHERE slug = '([a-z-]+)'", line).group(1) for line in statements} == {"grassrivers", "port-gellhorn"}
    assert not re.search(r"\b(DROP|DELETE|TRUNCATE|INSERT|ALTER)\b", re.sub(r"--.*", "", sql), re.I)
    seed = (ROOT / "database" / "seed.sql").read_text(encoding="utf-8")
    assert all(line in seed for line in statements)                                       # a fresh database built from the seed ends in the same state


# ------------------------------------------------------------------ official content only
@pytest.mark.parametrize("path", ["/regions"] + [f"/regions/{s}" for s in SLUGS])
def test_no_invented_place_or_story_appears_on_any_region_page(client, path):
    p = page(client, path)
    for name in INVENTED_PLACES + INVENTED_STORIES:
        assert name not in p, (path, name)
    assert 'href="/locations/' not in p and 'href="/missions/' not in p and "badge--demo" not in p and "Team Valkyrie original" not in p


def test_the_invented_records_are_left_in_the_database_and_the_api_and_still_labelled(client):
    body = client.get("/api/v1/regions/vice-city").get_json()
    api = body.get("data", body)
    assert [l["name"] for l in api["locations"]] and all(l["content_status"] == "demo" for l in api["locations"])        # nothing was deleted or hidden from the API
    assert client.get("/locations/sunset-pier-boardwalk").status_code == 200 and client.get("/missions/harbour-lights").status_code == 200
    assert "A Team Valkyrie original" in page(client, "/locations/sunset-pier-boardwalk")


def test_an_official_place_or_story_would_be_shown_when_the_database_has_one(client, monkeypatch):
    real = regions_repo.locations_in
    monkeypatch.setattr(regions_repo, "locations_in", lambda rid: real(rid) + [{"slug": "x-place", "name": "An Official Place", "location_type": "landmark", "summary": "s", "content_status": "official"}])
    from app.repositories import missions as missions_repo
    real_m = missions_repo.in_region
    monkeypatch.setattr(missions_repo, "in_region", lambda rid: real_m(rid) + [{"slug": "x-story", "title": "An Official Story", "mission_type": "story", "content_status": "official"}])
    p = page(client, "/regions/vice-city")
    assert "An Official Place" in p and 'href="/locations/x-place"' in p and "An Official Story" in p and 'href="/missions/x-story"' in p
    assert "Sunset Pier Boardwalk" not in p and "Harbour Lights" not in p


def test_characters_are_listed_only_where_the_database_places_them(client):
    assert 'href="/characters/boobie-ike"' in page(client, "/regions/vice-city")
    keys = page(client, "/regions/leonida-keys")
    assert 'href="/characters/jason-duval"' in keys and 'href="/characters/brian-heder"' in keys
    for slug in ("grassrivers", "port-gellhorn", "ambrosia", "mount-kalaga"):
        assert 'href="/characters/' not in page(client, f"/regions/{slug}").split('id="about"')[1].split('class="rgn"')[0], slug
    assert 'href="/characters/delia-marsh"' not in keys


# ------------------------------------------------------------------ robustness
def test_hostile_database_values_are_escaped_and_an_unsafe_source_is_not_linked(client, monkeypatch):
    real = regions_repo.get_by_slug
    monkeypatch.setattr(regions_repo, "get_by_slug", lambda slug: dict(real(slug), description="<img src=x onerror=alert(1)>", summary="<script>alert(2)</script>", source_url="javascript:alert(1)", source_note="<b>n</b>"))
    p = page(client, "/regions/ambrosia")
    assert "<img src=x onerror" not in p and "<script>alert(2)" not in p and "<b>n</b>" not in p and "javascript:alert" not in p
    assert "&lt;img src=x onerror=alert(1)&gt;" in p


def test_a_region_without_pictures_still_renders_without_empty_frames(client, monkeypatch):
    monkeypatch.setattr(media_repo, "for_entity", lambda *a, **k: [])
    p = page(client, "/regions/ambrosia")
    assert p.count("<h1") == 1 and 'class="rgs"' not in p and "<img class=\"rshot" not in p.split('class="rgn"')[0] and 'id="about"' in p


def test_an_unknown_region_is_a_clean_404(client):
    assert client.get("/regions/atlantis").status_code == 404 and client.get("/regions/ATLANTIS").status_code in (400, 404)


def test_the_stylesheet_gives_reduced_motion_its_due(client):
    css = (ROOT / "app" / "static" / "css" / "regions.css").read_text(encoding="utf-8")
    assert "prefers-reduced-motion: reduce" in css and "html.motion-on .rgh__art .rshot" in css and "@import" not in css
    assert "animation: rg-push" in css and css.count("html.motion-on") >= 4              # the camera exists only under the site's own motion class


def test_home_and_the_navigation_still_lead_to_the_regions(client):
    home = page(client, "/")
    for slug in SLUGS:
        assert f'href="/regions/{slug}"' in home
    assert re.search(r'<a[^>]*aria-current="page"[^>]*href="/regions"|<a[^>]*href="/regions"[^>]*aria-current="page"', page(client, "/regions/ambrosia"))


# ------------------------------------------------------------------ framing: every picture is cut around its subject, never stretched, and the viewer still opens the whole of it
def _visible(box, px, py):
    """The window (x0, x1, y0, y1), as fractions of a 16:9 picture, that a box of this width over height shows at object-position px, py (percent)."""
    ratio = 16 / 9
    if box >= ratio:
        window = ratio / box
        y0 = py / 100 * (1 - window)
        return 0.0, 1.0, y0, y0 + window
    window = box / ratio
    x0 = px / 100 * (1 - window)
    return x0, x0 + window, 0.0, 1.0


def test_every_picture_has_a_focal_point_and_the_art_direction_names_only_pictures_that_have_one():
    named = {name for art in media_slots.REGION_ART.values() for name in ((art["hero"], art["intro"]) + art["story"] + art["feature"]) if name}
    assert named <= set(media_slots.REGION_FOCUS), sorted(named - set(media_slots.REGION_FOCUS))
    for slug, focus in media_slots.REGION_FOCUS.items():
        points = focus.values() if isinstance(focus, dict) else [focus]
        assert all(0 <= x <= 1 and 0 <= y <= 1 for x, y in points), slug


@pytest.mark.parametrize("slug", sorted(media_slots.REGION_FOCUS))
def test_the_subject_stays_in_view_in_every_box_the_picture_is_drawn_in(app, slug):
    from app.services.site import _with_cuts
    focus = media_slots.REGION_FOCUS[slug]
    m = _with_cuts({"slug": slug})
    for name, (wide, narrow) in media_slots.REGION_BOXES.items():
        point = (focus.get(name, focus["*"]) if isinstance(focus, dict) else focus)
        px, py, pxn, pyn = m["cut"][name]
        for box, (x, y) in ((wide, (px, py)), (narrow, (pxn, pyn))):
            x0, x1, y0, y1 = _visible(box, x, y)
            assert x0 - 0.03 <= point[0] <= x1 + 0.03 and y0 - 0.03 <= point[1] <= y1 + 0.03, (slug, name, box, point, (x0, x1, y0, y1))
            assert all(v % 5 == 0 and 0 <= v <= 100 for v in (px, py, pxn, pyn))                 # on the grid the stylesheet has rules for


def test_the_stylesheet_has_a_rule_for_every_position_the_service_can_give(client):
    css = (ROOT / "app" / "static" / "css" / "regions.css").read_text(encoding="utf-8")
    for attr in ("px", "py", "pxn", "pyn"):
        for v in range(0, 101, 5):
            assert f'.rshot[data-{attr}="{v}"] {{ --{attr}: {v}%; }}' in css, (attr, v)
    for slug in SLUGS:
        p = page(client, f"/regions/{slug}")
        used = set(re.findall(r'data-p[xy]n?="(\d+)"', p))
        assert used and all(int(v) % 5 == 0 for v in used), slug


@pytest.mark.parametrize("slug", SLUGS)
def test_pictures_carry_their_crop_as_data_and_the_viewer_gets_the_whole_picture(client, slug):
    p = page(client, f"/regions/{slug}")
    imgs = re.findall(r"<img [^>]*class=\"rshot[^>]*>", p)
    assert imgs and sum('data-px="' in tag for tag in imgs) >= len(imgs) - 1       # every picture but, at most, the postcard (a full 16:9 card) is framed
    for href in re.findall(r'<a class="rg-lb[^"]*" href="([^"]+)"', p):
        assert "imwidth=2560" in href and "object" not in href and "crop" not in href      # the viewer's link is the picture itself, at its largest, uncropped
    assert 'style="' not in p.split("<body")[1]                                         # the CSP forbids inline styles


def test_the_two_pictures_whose_defining_detail_is_at_an_edge_name_a_second_point():
    focus = media_slots.REGION_FOCUS
    assert isinstance(focus["shot-port-gellhorn-01"], dict) and focus["shot-port-gellhorn-01"]["narrow"][0] < 0.3        # the Starlet Motel sign, not the middle of the road
    assert isinstance(focus["shot-port-gellhorn-02"], dict) and focus["shot-port-gellhorn-02"]["narrow"][0] < 0.5       # the man in the foreground, not the pair
