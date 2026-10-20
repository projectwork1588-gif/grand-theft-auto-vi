"""The Media page, "The Screening" (/media): Rockstar's own videos, clips, screenshots and artwork as its Media pages list them (checked 20 October 2026), from the database
(media_collections, media_collection_items). Nothing is invented: every title, date, runtime, count and download comes from a database row, every picture is Rockstar's own, every
video plays in Rockstar's own player, and every link leaves the site only for Rockstar. The Stories system stays where it was; only the menu entry changed."""
import hashlib
import re
from pathlib import Path

import mysql.connector
import pytest

from app import media_slots
from app.config import TestingConfig
from app.db import query_all, query_one
from app.repositories import media as media_repo
from app.services import screening
from scripts import migrate_db
from scripts.init_db import init_database
from tests.test_migration import as_migrator

ROOT = Path(__file__).resolve().parent.parent
IMG = "https://www.rockstargames.com/VI/_next/static/media/"
COUNTS = {"videos": 4, "clips": 9, "screenshots": 99, "ultimate-edition-benefits": 51, "vintage-vice-city-pack": 12, "artwork-wallpapers": 25}
SUBJECTS = {"Jason and Lucia": 13, "Jason Duval": 10, "Lucia Caminos": 10, "Ambrosia": 6, "Vice City": 12, "Leonida Keys": 6, "Port Gellhorn": 6, "Grassrivers": 6, "Cal Hampton": 4,
            "Boobie Ike": 4, "Dre'Quan Priest": 4, "Real Dimez": 4, "Raul Bautista": 4, "Brian Heder": 4, "Mount Kalaga National Park": 6}
FILMS = [("Grand Theft Auto VI Trailer 1", "2023-12-04", 91, "rkoCtr1r"), ("Grand Theft Auto VI Trailer 2", "2025-05-06", 167, "cpys7u21"),
         ("Grand Theft Auto VI: An Extended Look", "2026-08-27", 1608, "rk721912"), ("Grand Theft Auto VI Launch Trailer", "2026-10-15", 89, "76orsa95")]
ZIPS = {"clips": 120851301, "screenshots": 72255931, "ultimate-edition-benefits": 84798839, "vintage-vice-city-pack": 20634035, "artwork-wallpapers": 235479862}
DOWNLOAD_HOST = "media-rockstargames-com.akamaized.net"


def page(client, path="/media"):
    response = client.get(path)
    assert response.status_code == 200, path
    return response.get_data(as_text=True)


def main_of(p):
    return p.split("<main")[1].split("</main>")[0]


def items(app, slug):
    with app.app_context():
        return media_repo.collection_items(slug)


# ------------------------------------------------------------------ the data: Rockstar's collections, counted from Rockstar's own pages
def test_every_collection_has_exactly_the_items_rockstar_lists(app):
    with app.app_context():
        got = {c["slug"]: c["item_count"] for c in media_repo.collections()}
    assert got == COUNTS
    for slug, n in COUNTS.items():
        rows = items(app, slug)
        assert len(rows) == n and [r["position"] for r in rows] == list(range(1, n + 1)), slug          # complete, in Rockstar's order, no gap and no repeat


def test_every_collection_is_official_sourced_and_dated(app):
    with app.app_context():
        for c in query_all("SELECT * FROM media_collections"):
            assert c["content_status"] == "official" and c["source_url"].startswith("https://www.rockstargames.com/VI/media") and str(c["verified_on"]) == "2026-10-20", c["slug"]
            assert c["source_note"], c["slug"]
        assert {c["slug"]: c["download_bytes"] for c in query_all("SELECT slug, download_bytes FROM media_collections WHERE download_url IS NOT NULL")} == ZIPS
        assert all(c["download_url"].startswith("https://" + DOWNLOAD_HOST + "/VI/downloads/") for c in query_all("SELECT download_url FROM media_collections WHERE download_url IS NOT NULL"))


def test_no_picture_or_video_is_listed_twice_and_every_item_is_real_approved_official_media(app):
    with app.app_context():
        assert query_one("SELECT COUNT(*) n FROM (SELECT media_id FROM media_collection_items GROUP BY media_id HAVING COUNT(*) > 1) x")["n"] == 0
        assert query_one("SELECT COUNT(*) n FROM media_collection_items i LEFT JOIN media_assets m ON m.media_id = i.media_id WHERE m.media_id IS NULL OR m.approval_status <> 'approved'")["n"] == 0
        urls = [r["embed_url"] for r in query_all("SELECT m.embed_url FROM media_collection_items i JOIN media_assets m ON m.media_id = i.media_id JOIN media_collections c ON c.collection_id = i.collection_id WHERE c.kind <> 'video'")]
        assert len(urls) == 196 and len(set(urls)) == 196 and all(u.startswith(IMG) for u in urls)         # no address is recorded twice
        stems = [re.sub(r"\.[0-9a-z_~.-]+\.(jpg|png|webp)$", "", u.rsplit("/", 1)[1]) for u in urls]
        assert len(set(stems)) == len(stems)                                                                  # nor the same file under another hash


def test_the_new_rows_are_linked_to_no_character_region_or_vehicle_so_the_frozen_pages_do_not_change(app):
    with app.app_context():
        assert query_one("SELECT COUNT(*) n FROM media_assets")["n"] == 206
        assert query_one("SELECT COUNT(*) n FROM media_characters")["n"] == 59 and query_one("SELECT COUNT(*) n FROM media_regions")["n"] == 36
        assert query_one("SELECT COUNT(*) n FROM media_vehicles")["n"] == 21 and query_one("SELECT COUNT(*) n FROM media_locations")["n"] == 0
        assert query_one("SELECT COUNT(*) n FROM media_assets a WHERE a.media_id >= 115 AND (EXISTS (SELECT 1 FROM media_characters x WHERE x.media_id = a.media_id) OR EXISTS (SELECT 1 FROM media_regions x WHERE x.media_id = a.media_id) OR EXISTS (SELECT 1 FROM media_vehicles x WHERE x.media_id = a.media_id))")["n"] == 0


def test_the_videos_carry_rockstars_own_titles_dates_runtimes_players_and_posters(app):
    rows = {r["title"]: r for r in items(app, "videos")}
    assert set(rows) == {f[0] for f in FILMS}
    for title, date, seconds, player in FILMS:
        r = rows[title]
        assert str(r["published_on"]) == date and r["runtime_seconds"] == seconds, title
        assert r["embed_url"] == f"https://www.rockstargames.com/videoplayer?id={player}&embed&autoplay=false&locale=en_us", title
        assert r["poster_url"].startswith(IMG) and r["source_url"].startswith("https://www.rockstargames.com/VI/"), title
    assert rows["Grand Theft Auto VI Trailer 1"]["description"] == rows["Grand Theft Auto VI Trailer 2"]["description"]                 # Rockstar gives both the same text
    assert rows["Grand Theft Auto VI Launch Trailer"]["description"].startswith("Check out the Launch Trailer, featuring the debut of")
    assert rows["Grand Theft Auto VI: An Extended Look"]["description"].startswith("Captured entirely from in-game footage on the PlayStation 5")


def test_screenshots_fall_under_rockstars_fifteen_subjects_with_rockstars_counts(app):
    counts = {}
    for r in items(app, "screenshots"):
        s = screening.subject_of(r["title"])
        counts[s] = counts.get(s, 0) + 1
    assert counts == SUBJECTS and sum(counts.values()) == 99


def test_where_rockstar_gives_only_a_title_only_a_title_is_stored(app):
    for slug in ("screenshots", "ultimate-edition-benefits", "vintage-vice-city-pack", "artwork-wallpapers", "clips"):
        for r in items(app, slug):
            assert r["description"] is None and r["published_on"] is None and r["runtime_seconds"] is None and r["poster_url"] is None, (slug, r["title"])


# ------------------------------------------------------------------ the page
def test_the_page_opens_on_the_launch_trailer_with_a_real_play_control(client):
    p = page(client)
    assert p.count("<h1") == 1 and ">The Screening</h1>" in p and "<title>Media | Team Valkyrie</title>" in p
    opening = p.split('class="sc-open"')[1].split("</header>")[0]
    assert 'data-video="https://www.rockstargames.com/videoplayer?id=76orsa95&amp;embed&amp;autoplay=true&amp;locale=en_us"' in opening
    assert "Play the Launch Trailer" in opening and "15 October 2026" in opening and "1:29" in opening and "<video" not in opening and "<iframe" not in p
    assert opening.count("fetchpriority=\"high\"") == 1 and p.count('fetchpriority="high"') == 1                       # one picture is urgent; the rest wait their turn
    assert 'href="https://www.rockstargames.com/VI/launch-trailer"' in opening


def test_the_films_run_oldest_to_newest_with_rockstars_dates_and_runtimes(client):
    films = page(client).split('id="films"')[1].split("</section>")[0]
    titles = re.findall(r'<h3 class="sc-h3 sc-film__title">([^<]+)</h3>', films)
    assert titles == [f[0] for f in FILMS]
    for _, date, seconds, player in FILMS:
        assert f'<time datetime="{date}">' in films and f"id={player}&amp;embed" in films
    for text in ("4 December 2023", "6 May 2025", "27 August 2026", "15 October 2026", "1:31", "2:47", "26:48", "1:29"):
        assert text in films
    assert films.count("Jason and Lucia have always known the deck is stacked against them") == 1                       # the shared description appears once
    assert "same description as the one before it" in films and films.count("sc-film__poster") == 4
    assert films.count("may ask you to confirm your age") == 1 and films.index("may ask you to confirm your age") > films.index("An Extended Look")     # only the one video whose player asked


def test_every_screenshot_and_artwork_is_on_the_page_once_under_rockstars_title(client):
    p = main_of(page(client))
    tiles = re.findall(r'<a class="sc-(?:tile [^"]*|sheet__tile)" id="([^"]+)" href="([^"]+)" data-lightbox data-caption="([^"]*)"', p)     # drawn large, or one of a chapter's thumbnails behind "View all"
    assert len(tiles) == 187 and len({t[0] for t in tiles}) == 187 and len({t[1] for t in tiles}) == 187
    assert all(t[1].startswith(IMG) and t[1].endswith("imwidth=2560") for t in tiles)
    assert sum(1 for t in tiles if t[0].startswith("art-")) == 25 and sum(1 for t in tiles if t[0].startswith("shot-")) == 162
    for title in ("Jason Duval 07", "Lucia Caminos 09", "Vice City 11", "Official Cover Art", "The Album Cover Art", "Jason and Lucia Lock and Load (With Logos)"):
        assert f'data-caption="{title}"' in p, title


def test_the_first_chapter_shows_four_pictures_large_then_view_all_and_keeps_the_other_nine_in_the_same_viewer_group(client):
    pair = page(client).split('id="pair"')[1].split("</section>")[0]
    assert [r for r in re.findall(r'class="sc-row sc-row--(\w+)', pair)] == ["stage", "trio"]
    large = re.findall(r'<a class="sc-tile [^"]*" id="([^"]+)"', pair)
    thumbs = re.findall(r'<a class="sc-sheet__tile" id="([^"]+)"', pair)
    assert len(large) == 4 and len(thumbs) == 9 and large[0] == "shot-jason-and-lucia-01"                                    # the first four in Rockstar's order are the ones drawn large
    assert pair.count("data-gallery") == 1 and pair.count("data-lightbox") == 13                                              # one viewer group holds all thirteen, the large ones first
    assert re.search(r'<a class="sc-btn" href="[^"]+" data-open="shot-jason-and-lucia-01">View all 13<', pair)
    details = re.search(r'<details class="sc-more">', pair)
    assert details and "<details class=\"sc-more\" open" not in pair and "The other 9 as thumbnails" in pair                # closed: the thumbnails are in the page but not drawn
    assert pair.count('loading="lazy"') >= 9 and all("imwidth=360" in u for u in re.findall(r'<a class="sc-sheet__tile"[^>]*><img[^>]*src="([^"]+)"', pair))


def test_the_chapters_carry_rockstars_names_and_counts_and_link_to_the_pages_of_this_site(client):
    p = main_of(page(client))
    people = p.split('id="people"')[1].split('id="places"')[0]
    places = p.split('id="places"')[1].split('id="art"')[0]
    for name, n in SUBJECTS.items():
        if name in ("Jason and Lucia",):
            continue
        part = people if name in media_slots.SCREENING_PEOPLE else places
        assert f">{name.replace(chr(39), '&#39;')}</h3>" in part, name
        assert f"<span>{n} screenshots</span>" in part, name
    for slug in ("jason-duval", "lucia-caminos", "cal-hampton", "boobie-ike", "dre-quan-priest", "real-dimez", "raul-bautista", "brian-heder"):
        assert f'href="/characters/{slug}"' in people, slug
    for slug in ("vice-city", "leonida-keys", "grassrivers", "port-gellhorn", "ambrosia", "mount-kalaga"):
        assert f'href="/regions/{slug}"' in places, slug


def test_clips_are_posters_that_link_to_rockstars_own_page_and_the_editions_keep_rockstars_names(client):
    p = main_of(page(client))
    clips = p.split('id="clips"')[1].split('id="editions"')[0]
    assert clips.count('class="sc-clip ') == 9 and clips.count('href="https://www.rockstargames.com/VI/media/videos"') == 9
    for title in ("Official Cover Art Animation", "Jason Duval Video Clip", "Lucia Caminos Video Clip", "Brian Heder Video Clip"):
        assert title in clips
    assert "<video" not in clips and "<button" not in clips and ".mp4" not in clips
    editions = p.split('id="editions"')[1].split('id="downloads"')[0]
    assert ">Ultimate Edition Benefits</h3>" in editions and ">Vintage Vice City Pack</h3>" in editions
    assert "51 screenshots in 19 groups" in editions and "12 screenshots in 4 groups" in editions


def test_downloads_link_straight_to_rockstars_zip_files_with_their_sizes(client):
    d = page(client).split('id="downloads"')[1].split("</section>")[0]
    links = re.findall(r'<a href="([^"]+)" rel="noopener noreferrer">', d)
    assert sorted(links) == sorted(["https://media-rockstargames-com.akamaized.net/VI/downloads/" + f for f in (
        "videos/GTAVI_Videos.zip", "screenshots/GTAVI_Screenshots.zip", "screenshots/GTAVI_Ultimate_Edition_Benefits.zip", "screenshots/GTAVI_Vintage_Vice_City_Pack.zip", "artwork_wallpapers/GTAVI_Artwork_Wallpapers.zip")])
    for text in ("ZIP, 115 MB", "ZIP, 69 MB", "ZIP, 81 MB", "ZIP, 20 MB", "ZIP, 225 MB", "99 pictures", "9 clips"):
        assert text in d


def test_the_counts_on_the_page_come_from_the_data_and_agree_with_each_other(client):
    p = page(client)
    rail = dict(re.findall(r'data-rail-link="(\w+)"><b>\d+</b><span>[^<]*</span><i>(\d+)</i>', p))
    assert rail == {"films": "4", "pair": "13", "people": "44", "places": "42", "art": "25", "clips": "9", "editions": "63", "downloads": "5"}
    assert 13 + 44 + 42 == 99 and "4 films, 187 pictures and 9 clips" in p
    assert "4 videos, 9 clips, 99 screenshots, 25 pieces of artwork and 63 edition screenshots" in p and "checked on 20 October 2026" in p
    assert re.findall(r"Reel (\d+)", p) == ["01", "02", "03", "04", "05", "06", "07", "08"]                                 # the reel numbers are those of the rail
    pills = [int(n) for n in re.findall(r'class="sc-btn[^"]*"[^>]*>View all (\d+)<', p)]
    assert sorted(pills) == sorted([13, 10, 10, 4, 4, 4, 4, 4, 4, 12, 6, 6, 6, 6, 6, 25, 51, 12])                      # every chapter's View all carries that chapter's own count
    assert sum(pills) == 187                                                                                        # and together they are every one of the 187 pictures


def section(p, ident):
    return p.split('id="' + ident + '"', 1)[1].split("</section>")[0]


def test_each_chapter_has_its_own_composition_and_none_is_the_same_generic_grid(client):
    p = page(client)
    people, places, art, editions = section(p, "people"), section(p, "places"), section(p, "art"), section(p, "editions")
    assert people.count('<article class="sc-lead"') == 2 and people.count('<article class="sc-cell"') == 6 and "sc-leads" in people and "sc-cast" in people            # the two leads side by side, the six around them
    assert "sc-tri" in places and places.count('<article class="sc-reg sc-reg--') == 5 and places.count('class="sc-collage"') == 5   # Vice City large, five regions as collages
    assert art.count('class="sc-mat sc-mat--') == 4 and "sc-hang" in art                                          # four matted pieces
    assert editions.count('class="sc-showroom"') == 2 and editions.count('class="sc-frame') == 8 and editions.count('class="sc-index"') == 2                      # four frames and an index for each edition
    assert "sc-contact" not in p and "sc-wall" not in p                                                                                   # no page-wide contact sheet, no art wall


def test_every_chapter_has_a_view_all_beside_its_heading_and_a_closed_sheet_of_its_thumbnails(client):
    p = page(client)
    for ident, n_sheets in (("people", 8), ("places", 6), ("art", 1), ("editions", 2)):
        s = section(p, ident)
        assert s.count('data-open="') >= n_sheets and s.count('<details class="sc-more">') == n_sheets, ident
        assert "<details open" not in s                                                                                                   # the thumbnails are closed (nothing is downloaded until asked for)
    assert 'sc-head sc-head--bar' in section(p, "pair") and 'sc-head sc-head--bar' in section(p, "art")
    for opener in re.findall(r'data-open="([^"]+)"', p):
        assert p.count('id="' + opener + '"') == 1, opener                                                                                 # every opener points at exactly one real picture link


def test_every_picture_id_is_unique_and_is_in_exactly_one_viewer_group_with_its_chapter(client):
    p = main_of(page(client))
    ids = re.findall(r'<a [^>]*id="((?:shot|art)-[^"]+)"[^>]*data-lightbox', p)
    assert len(ids) == 187 and len(set(ids)) == 187
    groups = p.count("data-gallery")
    assert groups == 18 and p.count("data-lightbox") == 187                                                                               # one group per chapter, no picture outside a group


def test_every_picture_is_rockstars_own_and_only_the_opening_is_loaded_early(client):
    p = main_of(page(client))
    srcs = re.findall(r'<img [^>]*src="([^"]+)"', p)
    assert len(srcs) > 250 and all(s.startswith(IMG) for s in srcs)
    eager = [m for m in re.findall(r"<img [^>]*>", p) if "loading=" not in m]
    assert len(eager) == 1 and "fetchpriority" in eager[0]
    assert all('alt="' in m for m in re.findall(r"<img [^>]*>", p))
    assert "style=" not in p and "<audio" not in p and "<script" not in p                                                    # no inline style or script, no audio


def test_every_link_that_leaves_the_site_is_https_to_rockstar_and_opens_safely(client):
    p = main_of(page(client))
    for tag in re.findall(r"<a [^>]*>", p):
        href = re.search(r'href="([^"]+)"', tag).group(1)
        if "data-lightbox" in tag or "data-open" in tag or href.startswith(("/", "#")):
            continue
        assert href.startswith(("https://www.rockstargames.com/", "https://" + DOWNLOAD_HOST + "/")), href
        assert "noopener" in tag, tag
        if DOWNLOAD_HOST not in href:
            assert 'target="_blank"' in tag, tag


def test_the_menu_says_media_not_stories_and_marks_media_on_the_page(client):
    p = page(client)
    header = p.split('class="header-nav"')[1].split("</nav>")[0]
    assert '<a href="/media" aria-current="page">Media</a>' in header and ">Stories</a>" not in header and header.count("<a ") == 5
    menu = p.split('id="site-menu"')[1].split("</nav>")[0]
    assert ">Media</a>" in menu and ">Stories</a>" not in menu
    footer = p.split("footer-nav")[1].split("</nav>")[0]
    assert ">Media</a>" in footer and ">Stories</a>" not in footer


def test_the_other_pages_still_mark_their_own_entry_and_none_marks_media(client):
    for path, label in (("/characters", "Characters"), ("/vehicles", "Garage"), ("/regions", "Leonida"), ("/music", "Music")):
        header = page(client, path).split('class="header-nav"')[1].split("</nav>")[0]
        assert f'aria-current="page">{label}</a>' in header and 'href="/media" aria-current' not in header, path


# ------------------------------------------------------------------ Stories: still there, only out of the menu
def test_the_stories_routes_records_and_api_are_untouched(client, app):
    assert client.get("/missions").status_code == 200
    for slug in ("harbour-lights", "quiet-water", "last-call-smokestack-row", "ridge-run", "ledger-of-favours"):
        assert client.get(f"/missions/{slug}").status_code == 200
    body = client.get("/api/v1/missions").get_json()
    assert body["pagination"]["total"] == 5 and client.get("/api/v1/missions/harbour-lights").status_code == 200
    with app.app_context():
        assert query_one("SELECT COUNT(*) n FROM missions")["n"] == 5 and query_one("SELECT COUNT(*) n FROM mission_characters")["n"] == 10
        assert query_one("SELECT COUNT(*) n FROM mission_locations")["n"] == 8 and query_one("SELECT COUNT(*) n FROM mission_vehicles")["n"] == 8
    assert client.get("/locations").status_code == 302 and client.get("/locations/neon-row-district").status_code == 200       # the temporary redirect and the place pages stay


def test_the_home_page_still_has_its_stories_chapter(client):
    home = page(client, "/")
    assert 'id="stories"' in home and "Read all stories" in home and 'href="/missions"' in home


def test_the_old_local_clip_route_and_the_new_page_do_not_collide(client):
    assert client.get("/media/clips/not-there.mp4").status_code == 404
    assert client.get("/media/").status_code in (404, 308)
    assert client.get("/media").status_code == 200


# ------------------------------------------------------------------ safety: a bad row never becomes a picture, a link or markup
def _row(title, embed, position=1, **extra):
    row = {"position": position, "title": title, "published_on": None, "runtime_seconds": None, "description": None, "media_id": position, "media_slug": f"x-{position}", "media_type": "screenshot",
           "source_url": "https://www.rockstargames.com/VI/media/screenshots", "embed_url": embed, "poster_url": None, "poster_slug": None}
    row.update(extra)
    return row


def test_hostile_values_are_escaped_and_unsafe_pictures_players_and_links_are_dropped(app, client, monkeypatch):
    evil_title = '"><img src=x onerror=alert(1)><script>alert(2)</script> 01'
    fake = {
        "screenshots": [_row(evil_title, IMG + "ok.1234.jpg", 1), _row("Vice City 02", "https://evil.example/x.jpg", 2), _row("Vice City 03", IMG + "a b.jpg", 3),
                        _row("Vice City 04", "javascript:alert(3)", 4)],
        "videos": [_row("Evil film", "https://evil.example/player?id=1", 1, published_on=None, poster_url=IMG + "p.1.jpg"), _row("Poster-less film", "https://www.rockstargames.com/videoplayer?id=abc&embed&autoplay=false&locale=en_us", 2)],
        "clips": [_row("Evil clip", IMG + "c.1.jpg", 1, source_url="javascript:alert(4)"), _row("Good clip", IMG + "c.2.jpg", 2, source_url="https://www.rockstargames.com/VI/media/videos")],
        "artwork-wallpapers": [], "ultimate-edition-benefits": [], "vintage-vice-city-pack": [],
    }
    monkeypatch.setattr(media_repo, "collection_items", lambda slug: fake.get(slug, []))
    p = page(client)
    for bad in ("<script>alert", "<img src=x onerror", "evil.example", "javascript:alert", "a b.jpg", "Evil film", "Poster-less film", "Evil clip"):
        assert bad not in p, bad
    assert "&lt;script&gt;alert(2)&lt;/script&gt;" in p and "Good clip" in p
    assert 'data-caption="&#34;&gt;&lt;img src=x onerror=alert(1)&gt;&lt;script&gt;alert(2)&lt;/script&gt; 01"' in p


def test_a_database_without_the_media_tables_gives_an_honest_empty_page_not_an_error(client, monkeypatch):
    def missing(*args, **kwargs):
        raise mysql.connector.errors.ProgrammingError("Table 'media_collections' doesn't exist", errno=1146)
    monkeypatch.setattr(media_repo, "query_all", missing)
    p = page(client)
    assert p.count("<h1") == 1 and "migrate_db --only 009_media_screening.sql" in p and "sc-tile" not in p and "<iframe" not in p
    assert 'aria-current="page">Media</a>' in p


def test_a_collection_with_no_items_simply_leaves_its_section_out(client, monkeypatch):
    real = media_repo.collection_items
    monkeypatch.setattr(media_repo, "collection_items", lambda slug: [] if slug == "clips" else real(slug))
    p = page(client)
    assert 'id="clips"' not in p and 'data-rail-link="clips"' not in p
    assert "4 films and 187 pictures, as Rockstar lists them" in p and "0 clips" not in p and "9 clips" not in p
    assert 'id="art"' in p and 'data-rail-link="art"' in p


# ------------------------------------------------------------------ the service's own rules
@pytest.mark.parametrize("title,subject", [("Jason Duval 07", "Jason Duval"), ("Vice City 11", "Vice City"), ("Ultimate Edition 02", "Ultimate Edition"), ("’95 Grotti Cheetah 01", "’95 Grotti Cheetah"),
                                           ("Dre'Quan Priest 04", "Dre'Quan Priest"), ("Mount Kalaga National Park 06", "Mount Kalaga National Park"), ("Official Cover Art", "Official Cover Art"),
                                           ("Jason and Lucia Lock and Load (With Logos)", "Jason and Lucia Lock and Load (With Logos)"), ("PTT YOUNGIN$ Illegal Goods Store 01", "PTT YOUNGIN$ Illegal Goods Store")])
def test_subject_of_removes_only_the_trailing_number(title, subject):
    assert screening.subject_of(title) == subject


@pytest.mark.parametrize("n", range(0, 40))
def test_layout_rows_uses_every_picture_once_in_order_with_no_empty_row(n):
    pics = list(range(n))
    rows = screening.layout_rows(pics)
    flat = [p for _, ps in rows for p in ps]
    assert flat == pics
    for kind, ps in rows:
        assert kind in screening.ROW_SIZES and 1 <= len(ps) <= screening.ROW_SIZES[kind]
    if n >= 4:
        assert rows[0][0] == "stage" and len(rows[0][1]) == 1
    assert [p for _, ps in screening.layout_rows(pics, lead=False) for p in ps] == pics


def test_layout_rows_gives_the_known_chapters_their_rhythm():
    assert [(k, len(p)) for k, p in screening.layout_rows(list(range(13)))] == [("stage", 1), ("stagger", 2), ("trio", 3), ("duo", 2), ("stagger_r", 2), ("trio", 3)]
    assert [(k, len(p)) for k, p in screening.layout_rows(list(range(4)))] == [("stage", 1), ("stagger", 2), ("full", 1)]
    assert [k for k, _ in screening.layout_rows([1, 2, 3], lead=False)] == ["trio"] and [k for k, _ in screening.layout_rows([1], lead=False)] == ["full"]


def test_text_helpers():
    import datetime
    assert screening.runtime_text(89) == "1:29" and screening.runtime_text(1608) == "26:48" and screening.runtime_text(None) is None and screening.runtime_text(0) is None
    assert screening.day(datetime.date(2026, 10, 15)) == "15 October 2026" and screening.day(datetime.date(2023, 12, 4)) == "4 December 2023" and screening.day(None) is None
    assert screening.number_word(4) == "Four" and screening.number_word(11) == "11"
    assert screening.slugify("Jason Duval 07") == "jason-duval-07" and screening.slugify("Dre’Quan Priest 02") == "drequan-priest-02"


@pytest.mark.parametrize("bad", ["http://www.rockstargames.com/VI/media", "https://evil.example/x", "https://www.rockstargames.com.evil.example/", "https://user@www.rockstargames.com/",
                                 "javascript:alert(1)", "//www.rockstargames.com/", "https://www.rockstargames.com/a b", 'https://www.rockstargames.com/"x', "", None, "https://" + DOWNLOAD_HOST + "/x.zip"])
def test_https_link_refuses_anything_but_an_https_link_to_rockstar(bad):
    assert screening.https_link(bad) is None


def test_https_link_accepts_rockstar_and_its_download_host_only_where_told():
    assert screening.https_link("https://www.rockstargames.com/VI/media") == "https://www.rockstargames.com/VI/media"
    assert screening.https_link("https://" + DOWNLOAD_HOST + "/VI/downloads/videos/GTAVI_Videos.zip", screening.DOWNLOAD_HOSTS)


# ------------------------------------------------------------------ the files
def test_the_stylesheet_is_tokens_only_and_every_motion_respects_the_site_policy():
    css = (ROOT / "app" / "static" / "css" / "screening.css").read_text(encoding="utf-8")
    assert "prefers-reduced-motion: reduce" in css and "@import" not in css and "url(" not in css
    code = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    assert re.findall(r"@keyframes (\S+)", css) == ["sc-rise", "sc-letterbox", "sc-settle"]
    for selector, body in re.findall(r"([^{}]+)\{([^{}]*)\}", code):
        if re.search(r"(?<![-\w])animation\s*:", body) and "none" not in body:
            assert "html.motion-on" in selector, selector


def test_the_script_does_only_its_three_jobs_and_reaches_nowhere_else():
    js = (ROOT / "app" / "static" / "js" / "screening.js").read_text(encoding="utf-8")
    assert "http" not in js and "XMLHttpRequest" not in js and "fetch(" not in js and "eval(" not in js and "innerHTML" not in js
    assert "DOMContentLoaded" in js and "replaceState" in js and "aria-current" in js


# ------------------------------------------------------------------ migration 009
def test_migration_009_is_non_destructive_additive_and_the_seed_and_schema_mirror_it():
    path = ROOT / "database" / "migrations" / "009_media_screening.sql"
    sql = path.read_text(encoding="utf-8")
    code = re.sub(r"--.*", "", sql)
    migrate_db.check_non_destructive(path)                                                       # no DROP, DELETE or TRUNCATE
    assert not re.search(r"\bALTER\b", code, re.I) and not re.search(r"\bUPDATE\s+\w+\s+SET\b", code, re.I)
    assert code.count("CREATE TABLE IF NOT EXISTS") == 2
    assert not re.search(r"INSERT\s+(?:IGNORE\s+)?INTO\s+(?:media_characters|media_regions|media_vehicles|media_locations|characters|regions|vehicles|missions|locations)\b", code, re.I)
    seed = (ROOT / "database" / "seed.sql").read_text(encoding="utf-8")
    tail = sql[sql.index("INSERT INTO media_assets"):].rstrip("\n")
    assert tail.count("\nINSERT INTO ") == 2 and tail in seed                                    # a fresh database ends in the same state
    schema = (ROOT / "database" / "schema.sql").read_text(encoding="utf-8")
    for table in ("media_collections", "media_collection_items"):
        block = re.search(rf"CREATE TABLE IF NOT EXISTS {table} \(.*?\) ENGINE=InnoDB[^;]*;", sql, re.S).group(0).replace("IF NOT EXISTS ", "")
        assert re.sub(r"\s+", " ", block) in re.sub(r"\s+", " ", schema), table
    assert "DROP TABLE IF EXISTS media_collection_items;" in schema and "DROP TABLE IF EXISTS media_collections;" in schema


def test_migration_009_plans_cleanly_and_changes_nothing(app, capsys):
    assert migrate_db.main(["--test", "--only", "009_media_screening.sql", "--plan"]) == 0
    out = capsys.readouterr().out
    assert "009_media_screening.sql" in out and "--plan given: nothing was changed" in out and "008_music.sql" not in out
    assert out.count("    - ") == 5


def _hash(sql):
    connection = mysql.connector.connect(**TestingConfig.db_kwargs())
    try:
        cursor = connection.cursor()
        cursor.execute(sql)
        digest = hashlib.sha256()
        for row in cursor.fetchall():
            digest.update(repr([str(v) for i, v in enumerate(row)]).encode())
        return digest.hexdigest()
    finally:
        connection.close()


OLD_MEDIA = "SELECT media_id, slug, title, media_type, intended_use, source_url, embed_url, local_path, attribution, usage_status, approval_status, notes FROM media_assets WHERE media_id <= 114 ORDER BY media_id"
NEW_STATE = ("SELECT 'a', media_id, slug, title, media_type, embed_url, usage_status FROM media_assets WHERE media_id >= 115 "
             "UNION ALL SELECT 'c', c.collection_id, c.slug, c.title, c.kind, c.download_bytes, c.verified_on FROM media_collections c "
             "UNION ALL SELECT 'i', i.collection_id, i.position, i.media_id, i.title, i.poster_media_id, i.runtime_seconds FROM media_collection_items i ORDER BY 1, 2, 3")


def test_applying_009_to_a_database_that_has_everything_up_to_008_ends_in_the_same_state_and_touches_nothing_else(app, capsys):
    """The real database's situation: the 114 media rows and every other table exist, the two new tables and the 92 new rows do not."""
    try:
        done = _hash(NEW_STATE)
        old = _hash(OLD_MEDIA)
        everything_else = {t: _hash(f"SELECT * FROM {t} ORDER BY 1, 2") for t in ("characters", "regions", "locations", "missions", "vehicles", "media_characters", "media_regions", "media_vehicles", "mission_locations", "character_regions", "radio_stations", "music_tracks")}
        as_migrator(["SET FOREIGN_KEY_CHECKS = 0", "DROP TABLE media_collection_items", "DROP TABLE media_collections", "DELETE FROM media_assets WHERE media_id >= 115", "SET FOREIGN_KEY_CHECKS = 1"])
        assert migrate_db.main(["--test", "--only", "009_media_screening.sql", "--yes"]) == 0
        assert "Applied 009_media_screening.sql: 5 statements OK" in capsys.readouterr().out
        assert _hash(NEW_STATE) == done                                                           # ids, order, titles, dates, posters: identical
        assert _hash(OLD_MEDIA) == old                                                            # the 114 existing media rows: not one column changed
        assert {t: _hash(f"SELECT * FROM {t} ORDER BY 1, 2") for t in everything_else} == everything_else
        assert migrate_db.main(["--test", "--only", "009_media_screening.sql", "--yes"]) == 0     # and it is safe to run again
        capsys.readouterr()
        assert _hash(NEW_STATE) == done and _hash(OLD_MEDIA) == old
    finally:
        init_database(TestingConfig, seed=True, reset=True)


def test_deleting_a_collection_removes_only_its_items_and_never_the_media_rows(app):
    try:
        before = _hash("SELECT media_id, slug FROM media_assets ORDER BY 1")
        as_migrator(["DELETE FROM media_collections WHERE slug = 'clips'"])
        assert _hash("SELECT media_id, slug FROM media_assets ORDER BY 1") == before                  # the pictures stay recorded
        assert _hash("SELECT i.position FROM media_collection_items i JOIN media_collections c USING (collection_id) WHERE c.slug = 'clips'") == hashlib.sha256(b"").hexdigest()
    finally:
        init_database(TestingConfig, seed=True, reset=True)


# ------------------------------------------------------------------ scripts/verify_media.py (the parser, without the network)
def test_the_verification_script_reads_rockstars_page_data_in_order_and_sorts_screenshots_into_their_collections():
    from scripts import verify_media
    bs = chr(92)
    def item(title, src, ident):
        return ('{"title":"' + title + '","thumbnail":{"src":"' + src + '","width":3840,"height":2160,"blurWidth":8,"blurHeight":5,"blurDataURL":"data:x"},"variant":"image","media":[{"src":"$21"}],"id":"' + ident + '"}').replace('"', bs + '"')
    page = "".join([item("Jason Duval 07", "/VI/_next/static/media/Jason_Duval_07.0abc.jpg", "vi_downloads_screenshots_jason_duval_07"),
                    item("Ultimate Edition 02", "/VI/_next/static/media/Ultimate_Edition_02.0def.jpg", "vi_downloads_ultimate_edition_02"),
                    item("Vintage Vice City Pack 01", "/VI/_next/static/media/Vintage_Vice_City_Pack_01.0ghi.jpg", "vi_downloads_vintage_vice_city_pack_01"),
                    item("Jason Duval 07", "/VI/_next/static/media/Jason_Duval_07.0abc.jpg", "vi_downloads_screenshots_jason_duval_07")])         # a repeat is listed once
    items = verify_media.parse_items(page)
    assert [i["title"] for i in items] == ["Jason Duval 07", "Ultimate Edition 02", "Vintage Vice City Pack 01"]
    assert [verify_media.collection_of(i["id"]) for i in items] == ["screenshots", "ultimate-edition-benefits", "vintage-vice-city-pack"]
    assert verify_media.stem("https://www.rockstargames.com/VI/_next/static/media/Jason_Duval_07.0abc.jpg?akim=1") == "Jason_Duval_07"
    assert verify_media.parse_items("") == []
