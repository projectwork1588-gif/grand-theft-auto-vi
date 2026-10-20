"""The Music page (/music): Rockstar's own radio stations, score and album, as its Music page shows them, with sources. Nothing here is audio and nothing is invented: every fact is a database
row marked official with its source, every link leaves the site only for Rockstar's own pages or the link pages that Music page uses, and Team Valkyrie's own places (the old Locations section)
stay in the database, the API and their own pages, untouched."""
import re
from pathlib import Path

import mysql.connector
import pytest

from app.repositories import music as music_repo
from app.services import music

ROOT = Path(__file__).resolve().parent.parent
STATIONS = ["Cocoteo FM", "Back Country Radio", "AfroBank FM", "The Chamber", "Flash FM", "Dirty South Classics"]
HOSTS = ["El Martillo and La Gata", "MW and Delta Dawne", "Burna and Palmsy", "DJ Tom and DJ Kerry", "Robyn and Alex", "Trick and Trina"]
SINGLES = [("That&#39;s It (feat. Future &amp; Metro Boomin)", "Yung Lean"), ("RHYNO", "Travis Scott"), ("Sexy Magic", "CA7RIEL"), ("Flower in a Hurricane", "Justice"),
           ("Last Thing You Need", "Morgan Wallen"), ("Suzuki", "Fuerza Regida"), ("Macacoa 2000", "Rauw Alejandro"), ("Don&#39;t Chart", "Cardi B"),
           ("Bright Lights, Big City", "Keith Richards")]
LINKS = {"https://www.rockstargames.com/VI/music", "https://justice.lnk.to/flowerinahurricane", "https://gtavi-thealbum.lnk.to/gtavithealbum", "https://gtavithealbum.lnk.to/store",
         "https://www.gtavi-thealbum.com", "https://gtavi-thealbum.lnk.to/thatsit", "https://gtavi-thealbum.lnk.to/rhyno", "https://gtavi-thealbum.lnk.to/sexymagic",
         "https://gtavi-thealbum.lnk.to/FIAH", "https://gtavi-thealbum.lnk.to/lastthingyouneed", "https://gtavi-thealbum.lnk.to/suzuki", "https://gtavi-thealbum.lnk.to/macacoa2000",
         "https://gtavi-thealbum.lnk.to/dontchart", "https://gtavi-thealbum.lnk.to/brightlightsbigcity"}


def page(client, path="/music"):
    response = client.get(path)
    assert response.status_code == 200, path
    return response.get_data(as_text=True)


def main_of(p):
    return p.split("<main")[1].split("</main>")[0]


# ------------------------------------------------------------------ the page
def test_the_music_page_has_its_title_heading_and_menu_entry(client):
    p = page(client)
    assert re.search(r"<title>Music \|", p) and p.count("<h1") == 1 and "The music of Grand Theft Auto VI" in p
    header = p.split('class="header-nav"')[1].split("</nav>")[0]
    assert '<a href="/music" aria-current="page">Music</a>' in header and ">Locations</a>" not in header
    assert 'name="description"' in p and "Rockstar" in p.split('name="description"')[1][:300]


def test_the_six_stations_are_in_rockstars_order_with_the_words_it_uses(client):
    p = main_of(page(client))
    assert re.findall(r'class="mu-st__name" id="st-[a-z-]+-name">([^<]+)<', p) == STATIONS
    assert re.findall(r'<p class="mu-st__with">With ([^<]+)</p>', p) == HOSTS
    for words in ("Modern Latin from El Martillo and La Gata. El party que nunca se apaga.", "Airboat-ready renegade country from MW and Delta Dawne.",
                  "Turn up the gbedu.", "Crushing metal has landed in Leonida.", "The Vice City institution that delivers the best in pop music", "A little southern hospitality from Trick and Trina"):
        assert words in p, words
    assert p.count('class="mu-st__heard"') == 6 and p.count("Heard in Rockstar&rsquo;s preview") == 6
    assert "Bad Bunny" in p and "Black Sabbath" in p and "Charli xcx" in p and "Loretta Lynn" in p and "Asake" in p and "Solé" in p


def test_the_station_songs_are_described_as_the_preview_not_a_playlist(client):
    p = main_of(page(client))
    assert "what that preview plays, not a full playlist" in p and "Rockstar has not published one" in p


def test_the_score_and_the_album_say_what_rockstars_page_says(client):
    p = main_of(page(client))
    score = p.split('id="score-title"')[1].split("</section>")[0]
    assert ">Original Score Spotlight</h2>" in p and "Official Score by Justice" not in p       # the heading does not suggest Justice scored the whole game
    assert "standalone single" in score and "original score composers Justice" in score and "Flower in a Hurricane" in p and "Tame Impala" in p and "King Gizzard &amp; The Lizard Wizard" in p
    assert "Grand Theft Auto VI: The Album" in p and "Coming November 19" in p and "34 original tracks" in p and "Atlantic Records" in p
    assert "2026" not in re.sub(r"(read|checked) on? ?\d+ \w+ 2026|checked \d+ \w+ 2026", "", p.split('id="album"')[1].split('class="mu-source"')[0])      # no year invented for the release
    singles = p.split('id="singles-title"')[1].split("</ol>")[0]
    for title, artist in SINGLES:
        assert title in singles and artist in singles, title
    assert singles.count('class="mu-singles__no"') == 9 and "from the score&rsquo;s composers" in singles


def test_the_page_states_what_it_is_and_is_not(client):
    p = main_of(page(client))
    assert "What is confirmed" in p and "unofficial fan project" in p and "not affiliated with Rockstar Games" in p
    assert "hosts and plays no audio" in p and "read on 19 October 2026" in p
    assert "Rockstar has not said beyond its own pages" in p


# ------------------------------------------------------------------ nothing is audio, nothing pretends
def test_there_is_no_audio_no_player_and_no_control_that_does_nothing(client):
    p = main_of(page(client))
    for tag in ("<audio", "<video", "<iframe", "<button", "<source", "onclick=", "autoplay", 'role="slider"'):
        assert tag not in p, tag
    assert " .mp3" not in p and ".mp3" not in p and ".m4a" not in p                        # Rockstar's own preview files are not hot-linked; its page plays them
    assert not (ROOT / "app" / "static" / "js" / "music.js").exists()                       # no script: nothing to pretend with


def test_every_link_leaves_the_site_safely_for_an_official_destination(client):
    p = main_of(page(client))
    anchors = re.findall(r"<a [^>]*>", p)
    external = [a for a in anchors if 'href="http' in a]
    assert external
    seen = set()
    for a in external:
        href = re.search(r'href="([^"]+)"', a).group(1)
        seen.add(href)
        assert href.startswith("https://") and href.split("/")[2] in music.LINK_HOSTS, href
        assert 'target="_blank"' in a and 'rel="noopener noreferrer"' in a, a
    assert LINKS <= seen, sorted(LINKS - seen)
    assert p.count("(opens in a new tab)") >= len(external)                                 # each says so for a screen reader


def test_every_picture_is_one_of_rockstars_own_and_has_a_proper_alt(client):
    p = main_of(page(client))
    srcs = re.findall(r'<img [^>]*src="([^"]+)"', p)
    assert len(srcs) >= 15 and all(s.startswith("https://www.rockstargames.com/VI/_next/static/media/") for s in srcs)
    assert all('referrerpolicy="no-referrer"' in tag for tag in re.findall(r"<img [^>]*>", p))
    for tag in re.findall(r"<img [^>]*>", p):
        assert "alt=" in tag
    assert 'alt="Justice"' in p and 'alt="Cocoteo FM logo"' in p and "The artwork of Grand Theft Auto VI: The Album" in p


def test_the_page_uses_no_inline_styles_or_scripts(client):
    p = page(client)
    assert 'style="' not in p.split("<body")[1] and "<script>" not in p.split("<body")[1].replace("<script src", "")


# ------------------------------------------------------------------ the data
def test_every_music_row_is_official_dated_and_sourced(app):
    with app.app_context():
        rows = music_repo.stations() + music_repo.releases()
        assert len(music_repo.stations()) == 6 and len(music_repo.releases()) == 2
        for r in rows:
            assert r["content_status"] == "official" and r["source_url"] == "https://www.rockstargames.com/VI/music" and r["source_note"] and str(r["verified_on"]) == "2026-10-19"
        for r in music_repo.stations():
            assert r["logo_url"].startswith("https://www.rockstargames.com/VI/_next/static/media/") and r["background_url"].startswith("https://www.rockstargames.com/VI/_next/static/media/")
        urls = [t["listen_url"] for t in music_repo.tracks([r["release_id"] for r in music_repo.releases()])]
        assert len(urls) == 9 and all(music.safe_link(u) == u for u in urls)
        assert [t["title"] for t in music_repo.tracks([r["release_id"] for r in music_repo.releases() if r["kind"] == "album"])][3].startswith("Flower in a Hurricane")


def test_unofficial_rows_would_never_be_shown(app, monkeypatch):
    with app.app_context():
        assert music_repo.stations("demo") == [] and music_repo.releases("fan") == []


def test_hostile_values_are_escaped_and_unsafe_links_and_pictures_are_dropped(app, client, monkeypatch):
    with app.app_context():
        first = music_repo.stations()[0]
    evil = [dict(first, name="<script>alert(1)</script>", description="<img src=x onerror=alert(2)>", hosts='"><b>x</b>', source_url="javascript:alert(3)",
                 logo_url="https://evil.example/logo.png", background_url="https://www.rockstargames.com/VI/_next/static/media/a b.jpg")]
    monkeypatch.setattr(music_repo, "stations", lambda status="official": evil)
    p = page(client)
    assert "<script>alert" not in p and "<img src=x onerror" not in p and "<b>x</b>" not in p and "javascript:alert" not in p and "evil.example" not in p
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in p


@pytest.mark.parametrize("bad", ["http://www.rockstargames.com/VI/music", "https://evil.example/x", "https://www.rockstargames.com.evil.example/", "https://user@www.rockstargames.com/",
                                 "javascript:alert(1)", "//www.rockstargames.com/VI/music", "https://www.rockstargames.com/a b", 'https://www.rockstargames.com/"x', "", None])
def test_safe_link_refuses_anything_but_an_https_link_to_an_official_host(bad):
    assert music.safe_link(bad) is None


def test_safe_link_accepts_the_official_hosts():
    for url in LINKS:
        assert music.safe_link(url) == url


def test_a_database_without_the_music_tables_gives_an_honest_empty_page_not_an_error(client, monkeypatch):
    def missing(*args, **kwargs):
        raise mysql.connector.errors.ProgrammingError("Table 'radio_stations' doesn't exist", errno=1146)
    monkeypatch.setattr(music_repo, "query_all", missing)
    p = page(client)
    assert p.count("<h1") == 1 and "The music data is not loaded yet" in p and "migrate_db --only 008_music.sql" in p and "mu-st__name" not in p


# ------------------------------------------------------------------ the old Locations section: replaced in the menu, preserved underneath
def test_the_old_places_index_redirects_and_drops_its_filters(client):
    for query in ("", "?q=marina", "?region=vice-city&page=2&sort=newest"):
        response = client.get("/locations" + query)
        assert response.status_code == 302 and response.headers["Location"].endswith("/music") and "?" not in response.headers["Location"]


def test_team_valkyries_places_are_all_still_in_the_database_with_their_relationships(app):
    from app.db import query_all
    with app.app_context():
        places = query_all("SELECT slug, content_status FROM locations ORDER BY location_id")
        assert len(places) == 8 and {p["content_status"] for p in places} == {"demo"}
        assert query_all("SELECT COUNT(*) n FROM mission_locations")[0]["n"] == 8
        assert query_all("SELECT COUNT(*) n FROM characters WHERE home_location_id IS NOT NULL")[0]["n"] == 3
        assert query_all("SELECT COUNT(*) n FROM missions WHERE content_status = 'demo'")[0]["n"] == 5


def test_the_places_pages_the_stories_and_the_api_still_work(client):
    for slug in ("sunset-pier-boardwalk", "neon-row-district", "bayfront-studio-lot", "coral-hook-marina", "heron-reach-dock", "pelican-quay-terminal", "smokestack-row", "kalaga-ridge-lookout"):
        p = page(client, f"/locations/{slug}")
        assert "A Team Valkyrie original" in p and 'href="/locations"' not in p
    assert 'href="/locations/pelican-quay-terminal"' in page(client, "/missions/harbour-lights")
    body = client.get("/api/v1/locations").get_json()
    assert body["pagination"]["total"] == 8 and {l["content_status"] for l in body["data"]} == {"demo"}
    assert client.get("/api/v1/locations/neon-row-district").status_code == 200


def test_a_place_page_marks_no_menu_entry_now_that_stories_has_left_the_menu(client):
    header = page(client, "/locations/neon-row-district").split('class="header-nav"')[1].split("</nav>")[0]
    assert 'aria-current="page"' not in header and ">Media</a>" in header and ">Stories</a>" not in header


# ------------------------------------------------------------------ the migration
def test_migration_008_is_non_destructive_and_the_seed_mirrors_it():
    sql = (ROOT / "database" / "migrations" / "008_music.sql").read_text(encoding="utf-8")
    code = re.sub(r"--.*", "", sql)
    from scripts import migrate_db
    migrate_db.check_non_destructive(ROOT / "database" / "migrations" / "008_music.sql")      # the runner's own check: no DROP, DELETE or TRUNCATE ("ON DELETE CASCADE" is not a delete)
    assert not re.search(r"\bALTER\b", code, re.I)
    assert code.count("CREATE TABLE IF NOT EXISTS") == 4 and "locations" not in code.lower().replace("locations, stories", "")
    seed = (ROOT / "database" / "seed.sql").read_text(encoding="utf-8")
    inserts = re.findall(r"(INSERT INTO (?:radio_stations|station_preview_tracks|music_releases|music_tracks).*?;)\n", sql, re.S)
    assert len(inserts) == 4 and all(i in seed for i in inserts)                                  # a fresh database ends in the same state
    schema = (ROOT / "database" / "schema.sql").read_text(encoding="utf-8")
    assert all(f"CREATE TABLE {t} " in schema for t in ("radio_stations", "station_preview_tracks", "music_releases", "music_tracks"))


def test_migration_008_plans_cleanly_and_changes_nothing(app, capsys):
    from scripts import migrate_db
    assert migrate_db.main(["--test", "--only", "008_music.sql", "--plan"]) == 0
    out = capsys.readouterr().out
    assert "008_music.sql" in out and "--plan given: nothing was changed" in out and "001_phase2_media.sql" not in out


def test_the_stylesheet_is_tokens_only_and_respects_reduced_motion():
    css = (ROOT / "app" / "static" / "css" / "music.css").read_text(encoding="utf-8")
    assert "prefers-reduced-motion: reduce" in css and "@import" not in css and "!important" in css
    assert css.count("html.motion-on") >= 3                                                         # the only motion is the opening's, under the site's own motion class
