"""Stage B: the seven vehicle detail pages. One system, seven identities; every word and picture comes from the database and the project's
own art direction, nothing is stated that Rockstar has not, and the page degrades by data instead of showing an empty frame."""
import re
from pathlib import Path

import pytest

from app import media_slots
from app.repositories import vehicles as vehicles_repo
from app.services import site

ROOT = Path(__file__).resolve().parent.parent
OFFICIAL = ["grotti-cheetah", "vapid-dominator-buggy", "shitzu-squalo", "vapid-stanier", "vapid-ganado", "dinka-enduro", "crest-kayak"]


def page(client, slug):
    response = client.get(f"/vehicles/{slug}")
    assert response.status_code == 200, slug
    return response.get_data(as_text=True)


@pytest.mark.parametrize("slug", OFFICIAL)
def test_every_page_has_the_shared_skeleton(client, slug):
    p = page(client, slug)
    assert p.count("<h1") == 1 and 'class="vd-back"' in p and 'href="/vehicles"' in p
    assert 'vehicle_detail.css' in p and 'vehicle_detail.js' in p
    assert re.search(r'class="vd-hero vd-hero--(br|ml|tr)"', p) and 'data-subject="' in p
    assert 'id="machine"' in p and 'class="vd-next"' in p
    assert "Rockstar" in p                                                  # attribution stays on the page


@pytest.mark.parametrize("slug", OFFICIAL)
def test_previous_and_next_walk_the_whole_garage_in_a_loop(app, client, slug):
    with app.app_context():
        order = [e["slug"] for e in site.vehicle_detail(slug)["rail"]]
    me = order.index(slug)
    p = page(client, slug)
    assert f'rel="next" data-vehicle="{order[(me + 1) % 7]}"' in p
    assert f'rel="prev" data-vehicle="{order[(me - 1) % 7]}"' in p
    assert len(order) == 7


def test_the_seven_pages_do_not_share_one_opening(client):
    heroes = set()
    for slug in OFFICIAL:
        heroes.add(re.search(r'<header class="vd-hero.*?static/media/([A-Za-z0-9_.~-]+\.jpg)', page(client, slug), re.S).group(1))
    assert len(heroes) == 7


def test_the_view_model_follows_the_art_direction_data(app):
    with app.app_context():
        for slug in OFFICIAL:
            v = site.vehicle_detail(slug)
            assert v["sequence"] == media_slots.GARAGE_DETAIL[slug]["sequence"], slug
            assert v["line"] == media_slots.GARAGE_COPY[slug]
            assert v["hero"] and v["previous"]["slug"] != slug and v["next"]["slug"] != slug


def test_a_missing_gallery_degrades_to_a_page_without_an_empty_frame(app, monkeypatch):
    monkeypatch.setitem(media_slots.GARAGE_DETAIL, "grotti-cheetah", {"sequence": "viewer"})
    monkeypatch.setitem(media_slots.GARAGE_PICKS, "grotti-cheetah", {**media_slots.GARAGE_PICKS["grotti-cheetah"], "gallery": []})
    with app.test_client() as c:
        html = c.get("/vehicles/grotti-cheetah").get_data(as_text=True)
    assert "<h1" in html and 'class="vd-next"' in html


def test_a_vehicle_without_art_direction_still_renders(app, monkeypatch):
    for table in (media_slots.GARAGE_DETAIL, media_slots.GARAGE_SCENES, media_slots.GARAGE_COPY):
        monkeypatch.delitem(table, "vapid-stanier", raising=False)
    with app.test_client() as c:
        response = c.get("/vehicles/vapid-stanier")
    assert response.status_code == 200 and "<h1" in response.get_data(as_text=True)


def test_hostile_database_values_are_escaped_and_unsafe_sources_are_not_linked(client, monkeypatch):
    original = vehicles_repo.get_by_slug
    monkeypatch.setattr(vehicles_repo, "get_by_slug",
                        lambda slug, *a, **k: dict(original(slug, *a, **k), description="<img src=x onerror=alert(1)>", summary="<script>alert(2)</script>",
                                                   source_url="javascript:alert(1)"))
    p = client.get("/vehicles/grotti-cheetah").get_data(as_text=True)
    assert "<img src=x onerror" not in p and "<script>alert(2)" not in p
    assert "javascript:alert" not in p


def test_a_https_source_is_linked_with_safe_rel(client):
    p = page(client, "grotti-cheetah")
    link = re.search(r'<a href="(https://[^"]+)"[^>]*>rockstargames\.com</a>', p)
    assert link and 'rel="noopener' in link.group(0)


def test_detail_pages_do_not_invent_numbers(client):
    for slug in OFFICIAL:
        text = re.sub(r"<[^>]+>", " ", page(client, slug))
        assert not re.search(r"\b\d+\s?(hp|bhp|mph|km/h|kph)\b", text, re.I), slug


def test_the_stylesheet_and_script_are_local_and_the_script_is_enhancement_only(client):
    css = (ROOT / "app/static/css/vehicle_detail.css").read_text(encoding="utf-8")
    js = (ROOT / "app/static/js/vehicle_detail.js").read_text(encoding="utf-8")
    assert "prefers-reduced-motion" in css and "html.motion-on" in css
    assert "eval(" not in js and "innerHTML" not in js and "document.write" not in js
    assert "@import" not in css and "http://" not in css


def test_the_detail_stylesheet_belongs_to_the_detail_pages_only(client):
    assert "vehicle_detail.css" not in client.get("/vehicles").get_data(as_text=True)
    assert "vehicle_detail.css" in page(client, "grotti-cheetah")


def test_an_unknown_slug_is_a_clean_404(client):
    assert client.get("/vehicles/not-a-machine").status_code == 404
