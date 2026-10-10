"""Official media: URL safety, repository queries, and graceful fallbacks when media is missing or hostile."""
import mysql.connector
import pytest

from app import media_urls
from app.repositories import characters as characters_repo
from app.repositories import media, regions as regions_repo

GOOD_IMG = "https://www.rockstargames.com/VI/_next/static/media/Cal_Hampton_landscape.17k7bnt3myg.2.jpg"
GOOD_PLAYER = "https://www.rockstargames.com/videoplayer?id=cpys7u21&embed&autoplay=false&locale=en_us"


# ------------------------------------------------------------------ pure URL helpers
def test_image_helpers_accept_only_the_official_prefix():
    assert media_urls.image_src(GOOD_IMG, 640).endswith("?akim=1&imdensity=1&imwidth=640")
    assert media_urls.image_srcset(GOOD_IMG).count("w,") == 2 and "1920w" in media_urls.image_srcset(GOOD_IMG)
    for bad in (None, "", "http://www.rockstargames.com/VI/_next/static/media/x.jpg",
                "https://evil.example/VI/_next/static/media/x.jpg", "https://www.rockstargames.com/other/x.jpg",
                "javascript:alert(1)", "data:image/png;base64,AAAA", GOOD_IMG + '" onerror="x', GOOD_IMG + " x"):
        assert media_urls.image_src(bad) is None, bad
        assert media_urls.image_srcset(bad) is None, bad


def test_player_helper_accepts_only_rockstars_player():
    assert media_urls.player_src(GOOD_PLAYER) == GOOD_PLAYER
    assert "autoplay=true" in media_urls.player_src(GOOD_PLAYER, autoplay=True)
    for bad in (None, "", "https://www.youtube.com/embed/abc", "https://evil.example/videoplayer?id=1",
                "http://www.rockstargames.com/videoplayer?id=1", "javascript:alert(1)", GOOD_PLAYER + '"><script>'):
        assert media_urls.player_src(bad) is None, bad


# ------------------------------------------------------------------ repository queries (real MySQL)
def test_covers_prefer_solo_images_then_artwork(app_context):
    ids = characters_repo.ids_by_slug(["jason-duval", "lucia-caminos", "cal-hampton", "delia-marsh"])
    covers = media.covers("character", ids.values())
    assert covers[ids["jason-duval"]]["slug"] == "shot-jason-duval-01"      # solo shot, not the joint artwork
    assert covers[ids["lucia-caminos"]]["slug"] == "shot-lucia-caminos-01"
    assert covers[ids["cal-hampton"]]["slug"] == "art-cal-hampton"          # artwork preferred
    assert ids["delia-marsh"] not in covers                                 # fictional characters get no official image


def test_region_covers_and_galleries(app_context):
    ids = regions_repo.ids_by_slug(["vice-city", "mount-kalaga"])
    covers = media.covers("region", ids.values())
    assert covers[ids["vice-city"]]["slug"] == "postcard-vice-city"
    assert covers[ids["mount-kalaga"]]["slug"] == "postcard-mount-kalaga"
    gallery = media.for_entity("region", ids["vice-city"])
    slugs = [m["slug"] for m in gallery]
    assert slugs[:5] == ["postcard-vice-city"] + [f"shot-vice-city-0{i}" for i in (1, 2, 3, 4)]
    assert len(slugs) > 5  # the later official shots follow the original five
    assert all(m["embed_url"].startswith(media_urls.IMAGE_PREFIX) for m in gallery)


def test_by_slugs_and_videos(app_context):
    found = media.by_slugs(["official-trailer-2", "shot-vice-city-01", "no-such-row"])
    assert set(found) == {"official-trailer-2", "shot-vice-city-01"}
    assert [v["slug"] for v in media.videos()] == ["official-trailer-1", "official-trailer-2", "official-an-extended-look"]
    assert media.covers("character", []) == {} and media.by_slugs([]) == {}


def test_only_displayable_media_is_returned(app_context):
    # The hub row is a plain link (no embed URL), so it is never offered as displayable media.
    assert media.by_slugs(["official-media-artwork-hub"]) == {}
    jason = characters_repo.ids_by_slug(["jason-duval"])["jason-duval"]
    assert len(media.for_entity("character", jason, limit=3)) == 3  # the limit is honoured


# ------------------------------------------------------------------ pages degrade gracefully
def test_hostile_media_urls_are_never_rendered(client, monkeypatch):
    evil = {"slug": "x", "title": "Evil", "media_type": "artwork", "source_url": "https://evil.example/",
            "attribution": "x", "embed_url": "https://evil.example/pic.jpg", "media_id": 1}
    monkeypatch.setattr(media, "covers", lambda kind, ids: {i: evil for i in ids})
    monkeypatch.setattr(media, "for_entity", lambda kind, entity_id, limit=12: [evil, evil])
    monkeypatch.setattr(media, "by_slugs", lambda slugs: {s: dict(evil, slug=s, embed_url="javascript:alert(1)") for s in slugs})
    for path in ("/", "/characters", "/characters/jason-duval", "/regions", "/regions/vice-city", "/locations/sunset-pier-boardwalk"):
        response = client.get(path)
        page = response.get_data(as_text=True)
        assert response.status_code == 200, path
        assert "evil.example/pic.jpg" not in page and "javascript:alert" not in page, path
        assert "media__fallback" in page, path  # original fallback artwork is used instead


def test_missing_media_tables_do_not_break_pages(client, monkeypatch):
    def boom(*args, **kwargs):
        raise mysql.connector.errors.ProgrammingError("Table 'media_regions' doesn't exist", errno=1146)

    monkeypatch.setattr(media, "query_all", boom)
    for path in ("/", "/characters", "/characters/jason-duval", "/regions", "/regions/vice-city", "/locations/coral-hook-marina"):
        response = client.get(path)
        page = response.get_data(as_text=True)
        assert response.status_code == 200, path
        assert "rockstargames.com/VI/_next/static/media" not in page, path  # no remote images without media rows
    home = client.get("/").get_data(as_text=True)
    assert "rockstargames.com/VI/trailer-1" in home                    # link-only fallback for videos
    assert "Jason Duval" in home and "Vice City" in home               # content from the main tables still shows


def test_other_media_errors_are_not_swallowed(client, monkeypatch):
    def boom(*args, **kwargs):
        raise mysql.connector.errors.InterfaceError("connection lost")

    monkeypatch.setattr(media, "query_all", boom)
    assert client.get("/characters").status_code == 503
