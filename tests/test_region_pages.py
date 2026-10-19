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
    assert re.search(r'class="rg-hero rg-hero--(bl|tl)"', p) and 'id="about"' in p and 'href="#about"' in p
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
        shown = [m["slug"] for m in (region["hero"], region["postcard"]) if m] + [m["slug"] for g in region["groups"] for m in g]
        everything = [m["slug"] for m in media_repo.for_entity("region", regions_repo.ids_by_slug([slug])[slug], limit=24)]
    assert sorted(shown) == sorted(everything) and len(set(shown)) == len(shown)
    p = page(client, f"/regions/{slug}")
    images = re.findall(r'<img class="rshot[^"]*" src="([^"]+)"', p)
    assert images and all(src.startswith("https://www.rockstargames.com/") for src in images)     # official hosts only (image_src refuses any other)
    assert all('referrerpolicy="no-referrer"' in tag for tag in re.findall(r"<img [^>]*rshot[^>]*>", p))


@pytest.mark.parametrize("slug", SLUGS)
def test_every_picture_opens_full_size_in_the_sites_viewer_with_its_title(client, slug):
    p = page(client, f"/regions/{slug}")
    gallery = p.split("data-gallery")[1].split("</section>")[0]
    links = re.findall(r'<a href="(https://www\.rockstargames\.com/[^"]+imwidth=2560)" data-lightbox data-caption="([^"]+)"', gallery)
    assert len(links) == gallery.count("data-lightbox") >= 3
    assert all("official" in title.lower() or "postcard" in title.lower() for _, title in links)


def test_the_postcard_is_shown_as_rockstars_own_artwork(client):
    p = page(client, "/regions/port-gellhorn")
    assert "The postcard" in p and "Rockstar's own artwork for Port Gellhorn" in p and "Port Gellhorn postcard (official artwork)" in p


def test_each_region_is_composed_differently_not_one_template_with_six_backgrounds(app):
    with app.app_context():
        shapes = {slug: [len(g) for g in site.region_detail(slug)["groups"]] for slug in SLUGS}
    assert shapes["vice-city"] == [1, 2, 3, 1] and shapes["port-gellhorn"] == [2] and shapes["ambrosia"] == [1, 1]
    assert len({tuple(v) for v in shapes.values()}) >= 5
    assert {media_slots.REGION_ART[s]["plate"] for s in SLUGS} == {"tl", "bl"}


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
        assert 'href="/characters/' not in page(client, f"/regions/{slug}").split('id="about"')[1].split("rg-next")[0], slug
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
    assert p.count("<h1") == 1 and "rg-pics" not in p and "<img class=\"rshot" not in p.split('class="rg-next"')[0] and 'id="about"' in p


def test_an_unknown_region_is_a_clean_404(client):
    assert client.get("/regions/atlantis").status_code == 404 and client.get("/regions/ATLANTIS").status_code in (400, 404)


def test_the_stylesheet_gives_reduced_motion_its_due(client):
    css = (ROOT / "app" / "static" / "css" / "regions.css").read_text(encoding="utf-8")
    assert "prefers-reduced-motion: reduce" in css and "html.motion-on .rg-hero__art .rshot" in css and "@import" not in css
    assert "animation: rg-push" in css and css.count("html.motion-on") >= 4              # the camera exists only under the site's own motion class


def test_home_and_the_navigation_still_lead_to_the_regions(client):
    home = page(client, "/")
    for slug in SLUGS:
        assert f'href="/regions/{slug}"' in home
    assert re.search(r'<a[^>]*aria-current="page"[^>]*href="/regions"|<a[^>]*href="/regions"[^>]*aria-current="page"', page(client, "/regions/ambrosia"))
