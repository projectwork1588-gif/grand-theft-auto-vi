"""Home's picture challenge, the official release block, the hero's camera, the Characters opening picture, the Garage's arrivals and what a first visit asks for.

Nothing here is invented: the challenge is built from rows the Characters, Leonida and Garage pages already show; the release block is media_slots.OFFICIAL_RELEASE, whose facts were read
from rockstargames.com/VI and /VI/editions on 21 October 2026; the Characters opening picture is a Rockstar screenshot no curated page uses."""
import json
import re
from pathlib import Path

from app import media_slots, media_urls
from app.db import query_all, query_one
from app.repositories import media as media_repo
from app.services import discover

ROOT = Path(__file__).resolve().parent.parent
SAFE_NAME = re.compile(r"[A-Za-z0-9._~%+-]+")


def page(client, path="/"):
    response = client.get(path)
    assert response.status_code == 200, path
    return response.get_data(as_text=True)


def static(kind, name):
    return (ROOT / "app" / "static" / kind / name).read_text(encoding="utf-8")


def section(p, ident):
    return p.split(f'id="{ident}"', 1)[1].split("</section>")[0]


def quiz_data(p):
    match = re.search(r"data-quiz-data='([^']*)'", p)                                                       # in an attribute: the site allows no inline script block, not even a data one
    assert match, "the challenge's data is missing"
    return json.loads(match.group(1))


# ------------------------------------------------------------------ the picture challenge
def test_the_challenge_is_built_from_the_database_and_every_answer_leads_to_a_real_page(client):
    data = quiz_data(page(client))
    assert set(data["pools"]) == {"people", "places", "machines"} and data["rounds"] == 5
    assert {k: len(v) for k, v in data["answers"].items()} == {"people": 8, "places": 6, "machines": 7}
    names = {k: {a["n"] for a in v.values()} for k, v in data["answers"].items()}
    assert {"Jason Duval", "Lucia Caminos", "Real Dimez"} <= names["people"] and {"Vice City", "Leonida Keys", "Mount Kalaga"} <= names["places"]
    for kind, answers in data["answers"].items():
        for slug, info in answers.items():
            assert info["n"] and info["s"] and info["h"].startswith("/") and not info["h"].startswith("//"), (kind, slug)
            assert client.get(info["h"]).status_code == 200, info["h"]                                   # the answer's own page exists
        pool_answers = {q["a"] for q in data["pools"][kind]}
        assert pool_answers == set(answers), kind                                                         # every answer has a picture, every picture an answer
        assert len(pool_answers) >= discover.MIN_ANSWERS                                                  # one right answer and three others of its kind
    assert any(v.get("b") for v in data["answers"]["places"].values())                                   # Rockstar's own notes on who is based where reach the reveal


def test_every_challenge_picture_is_a_row_rockstar_published_and_the_address_is_rebuilt_safely(app, client):
    data = quiz_data(page(client))
    with app.app_context():
        official = {r["embed_url"] for r in query_all("SELECT embed_url FROM media_assets WHERE approval_status = 'approved' AND embed_url IS NOT NULL")}
    for kind, pool in data["pools"].items():
        for q in pool:
            assert SAFE_NAME.fullmatch(q["p"]), q["p"]
            assert media_urls.IMAGE_PREFIX + q["p"] in official, q["p"]
    assert data["prefix"] == media_urls.IMAGE_PREFIX


def test_the_challenge_markup_is_a_progressive_enhancement_with_no_inline_style_or_frame(client):
    p = page(client)
    s = section(p, "challenge")
    assert 'data-quiz-ui hidden' in s and "quiz__plain" in s and s.count('<a class="pill"') >= 3             # without script: three plain links
    assert "style=" not in s and "<iframe" not in s and "<form" not in s and "onclick" not in s and "<script" not in s
    assert 'role="group" aria-labelledby="quiz-ask"' in s and 'aria-live="polite"' in s                      # the answers are a labelled group; results are announced
    assert p.count('id="quiz-ask"') == 1 and 'rel="stylesheet" href="/static/css/home.css"' in p and "/static/js/home.js" in p


def test_a_hostile_name_or_picture_never_reaches_the_challenge(app, monkeypatch):
    rows = [{"title": "Jason Duval 01", "embed_url": "https://evil.example/x.jpg", "published_on": None},
            {"title": "Jason Duval 02", "embed_url": media_urls.IMAGE_PREFIX + "a b.jpg", "published_on": None},
            {"title": "Jason Duval 03", "embed_url": media_urls.IMAGE_PREFIX + "ok.123.jpg", "published_on": None}]
    monkeypatch.setattr(media_repo, "collection_items", lambda slug: rows if slug == "screenshots" else [])
    monkeypatch.setattr(media_repo, "solo_vehicle_pictures", lambda: [])
    evil = 'Evil </script><img src=x onerror=alert(1)>'
    people = [{"slug": s, "full_name": evil if s == "jason-duval" else s, "role_title": "r", "summary": "s"} for s in ("jason-duval", "lucia-caminos", "cal-hampton", "boobie-ike")]
    with app.test_request_context("/"):
        result = discover.challenge(people, [], [], lambda kind, slug: "/" + kind + "/" + slug)
    assert result is None                                                                                    # one kind of question is not enough to ask: the section is left out
    pools = {"people": {}}
    for item in rows:
        path = discover._path(item)
        if path:
            pools["people"].setdefault("jason-duval", []).append(path)
    assert pools["people"] == {"jason-duval": ["ok.123.jpg"]}                                               # only the one Rockstar address survives
    rendered = app.jinja_env.from_string("{{ d | tojson }}").render(d={"n": evil})
    assert "</script>" not in rendered and "<img" not in rendered and "'" not in rendered                   # the name can neither close a block nor leave the attribute that carries the data


def test_the_section_and_the_page_survive_a_database_with_too_little_to_ask_about(client, monkeypatch):
    monkeypatch.setattr(media_repo, "collection_items", lambda slug: [])
    monkeypatch.setattr(media_repo, "solo_vehicle_pictures", lambda: [])
    p = page(client)
    assert 'id="challenge"' not in p and 'id="top"' in p and 'id="leads"' in p                              # a quiet omission, not an error


def test_when_no_picture_can_be_loaded_the_challenge_steps_aside_for_its_plain_links():
    js, css = static("js", "home.js"), static("css", "home.css")
    assert 'root.classList.add("is-broken")' in js and ".js .quiz.is-broken .quiz__plain { display: block; }" in css


def test_the_challenge_script_builds_everything_with_text_and_checks_every_address():
    js = static("js", "home.js")
    assert "innerHTML" not in js and "eval(" not in js and "document.write" not in js and "insertAdjacentHTML" not in js
    assert js.count("textContent") >= 4 and js.count("setText(") >= 10 and 'indexOf("https://www.rockstargames.com/") !== 0' in js and "SAFE_NAME" in js
    assert "IntersectionObserver" in js and "rootMargin" in js                                              # nothing is requested until the section is near
    assert 'truth.h.charAt(0) === "/"' in js                                                                # a link is followed only if it is one of the site's own pages


# ------------------------------------------------------------------ the official release block
def test_the_release_block_shows_only_what_rockstars_pages_say_and_says_where_it_came_from(client):
    p = page(client)
    s = section(p, "release")
    facts = media_slots.OFFICIAL_RELEASE
    assert "Coming" in s and facts["date"] in s and all(x.split("|")[0] in s for x in facts["platforms"])
    assert facts["checked"] in s and "Official key art &copy; Rockstar Games" in s
    assert "unofficial fan project" in s and "sells nothing" in s and "not Rockstar" in s                  # the fan project is told apart from Rockstar's own site
    for e in facts["editions"] + facts["bonuses"]:
        assert e in s, e
    assert media_urls.IMAGE_PREFIX in s                                                                       # the key art is Rockstar's own picture
    video = re.search(r'<button class="release__film[^>]*data-video="([^"]+)"', s)
    assert video and video.group(1).startswith(media_urls.PLAYER_PREFIX) and "76orsa95" in video.group(1)   # the newest film, in Rockstar's own player, opened only on a press
    assert "<iframe" not in s                                                                                 # no player is loaded until it is asked for


def test_the_release_call_to_action_is_an_honest_link_to_rockstars_own_pages_and_nothing_is_sold(client):
    s = section(page(client), "release")
    hrefs = re.findall(r'<a class="btn[^"]*" href="([^"]+)" target="_blank" rel="noopener noreferrer"', s)
    assert hrefs == [media_slots.OFFICIAL_RELEASE["preorder_url"], media_slots.OFFICIAL_RELEASE["editions_url"]]
    assert all(h.startswith("https://www.rockstargames.com/VI") for h in hrefs)
    assert "has no address of its own" in s                                                                   # why the button links to the page that carries Rockstar's own Pre-Order Now
    lowered = s.lower()
    for word in ("<form", "<input", "checkout", "credit card", "card number", "add to cart", "price"):
        assert word not in lowered, word                                                                      # no checkout, no payment details, no prices invented


def test_the_release_facts_are_one_reviewed_setting_with_official_addresses(app):
    facts = media_slots.OFFICIAL_RELEASE
    assert facts["date"] == media_slots.RELEASE_NOTE == "November 19, 2026" and facts["platforms"] == ("PlayStation 5", "Xbox Series X|S")
    assert facts["preorder_url"] == media_slots.OFFICIAL_LINKS["site"] and facts["editions_url"] == media_slots.OFFICIAL_LINKS["editions"]
    assert facts["checked"] == "21 October 2026"
    with app.app_context():
        for slug in (facts["art"], facts["video"], facts["poster"]):
            row = query_one("SELECT media_type, approval_status, embed_url FROM media_assets WHERE slug = %s", (slug,))
            assert row and row["approval_status"] == "approved", slug
        assert media_urls.is_official_image(query_one("SELECT embed_url FROM media_assets WHERE slug = %s", (facts["art"],))["embed_url"])
        assert media_urls.player_src(query_one("SELECT embed_url FROM media_assets WHERE slug = %s", (facts["video"],))["embed_url"])


def test_the_release_block_is_left_out_without_its_artwork_and_loses_only_the_film_without_its_video(client, monkeypatch):
    monkeypatch.setitem(media_slots.OFFICIAL_RELEASE, "video", "no-such-video")
    s = section(page(client), "release")
    assert "release__film" not in s and "Coming" in s and "release__art" in s
    monkeypatch.setitem(media_slots.OFFICIAL_RELEASE, "art", "no-such-picture")
    assert 'id="release"' not in page(client)


# ------------------------------------------------------------------ what a first visit asks for
def test_no_video_asks_for_its_picture_before_it_is_wanted(client, local_clips):
    for path in ("/", "/characters"):
        p = page(client, path)
        assert "<video" in p and not re.search(r"<video[^>]*\sposter=", p), path                            # the lazy still beside each video is its poster


# ------------------------------------------------------------------ the Characters opening picture
def test_the_characters_opening_is_not_the_two_pictures_the_owner_rejected():
    assert media_slots.CHARACTERS_OPENING not in ("art-jason-lucia-beach", "rs-jason-and-lucia-12")        # the illustrated beach art, and the dark screenshot 12 that replaced it


def test_only_the_opening_picture_offers_the_3840_original(client):
    p = page(client, "/characters")
    assert p.count("imwidth=3840") >= 1 and p.split('class="cast-open__bg"')[1].split("</div>")[0].count("imwidth=3840") == 1
    assert "imwidth=3840" not in page(client, "/")                                                          # nothing else grew: Home and the rest keep their widths


def test_the_characters_opening_is_a_verified_rockstar_screenshot_no_curated_page_uses(app, client):
    slug = media_slots.CHARACTERS_OPENING
    with app.app_context():
        return _opening_checks(client, slug)


def _opening_checks(client, slug):
    row = query_one("SELECT media_id, title, media_type, approval_status, embed_url, source_url FROM media_assets WHERE slug = %s", (slug,))
    assert row and row["approval_status"] == "approved" and row["media_type"] == "screenshot" and media_urls.is_official_image(row["embed_url"])
    assert row["source_url"] == "https://www.rockstargames.com/VI/media/screenshots" and row["title"].startswith("Jason and Lucia")
    item = [i for i in media_repo.collection_items("screenshots") if i["media_slug"] == slug]
    assert len(item) == 1 and item[0]["title"] == row["title"]                                              # it is on Rockstar's own Screenshots page, under that title
    for table in ("media_characters", "media_regions", "media_vehicles", "media_locations"):
        assert query_one(f"SELECT COUNT(*) n FROM {table} WHERE media_id = %s", (row["media_id"],))["n"] == 0, table   # no character, region or vehicle page draws it
    elsewhere = [name for name, value in vars(media_slots).items() if name != "CHARACTERS_OPENING" and slug in repr(value)]
    assert elsewhere == []                                                                                   # no other picture slot of the site names it
    p = page(client, "/characters")
    hero = p.split('class="cast-open__bg"')[1].split("</div>")[0]
    assert row["embed_url"].rsplit("/", 1)[1] in hero and 'fetchpriority="high"' in hero
    assert 'data-px="100"' in hero and 'data-pxn="66"' in hero                                              # framed for a wide window and for a phone, both leads whole
    srcset = re.search(r'srcset="([^"]+)"', hero).group(1)
    assert " 3840w" in srcset and "imwidth=3840" in srcset                                                   # Rockstar's 3840 px original is on offer for a large or high-density screen
    assert "(max-width: 760px) max(100vw, 101vh)" in hero.split('sizes="')[1].split('"')[0]                # ...but a phone is told how much it really shows, so it never fetches the largest file
    for other in ("/", "/vehicles", "/regions", "/music"):
        assert row["embed_url"].rsplit("/", 1)[1] not in page(client, other), other                           # not on Home, the Garage, Leonida or Music


# ------------------------------------------------------------------ the camera and the arrivals (static rules)
def test_the_hero_camera_is_one_tuned_setting_not_a_global_speed_up():
    pages, site, js = static("css", "pages.css"), static("css", "site.css"), static("js", "site.js")
    assert "--dolly: 12s" in pages and "--arrive: 2.6s" in pages and "@keyframes heroArrive" in pages and "26s" not in pages.split("HERO MOTION POSTER")[1]
    assert "var(--dolly)" in site and "var(--arrive)" in site and "26s" not in site                          # a visitor who opts in on a reduced-motion system gets the same timings back
    assert "will-change: scale, translate" in pages and ":not(.is-paused):not(.is-hidden)" in pages        # promoted only while it moves
    assert "html.js .hero__stage { opacity: 0; animation: heroStageIn" in pages                             # the layers arrive together; without script the stylesheet reveals them itself
    assert 'classList.add("is-ready")' in js and "window.setTimeout(reveal, 2200)" in js
    assert "rise .85s" in pages and "animation-delay: .7s" in pages                                          # the words settle in about a second and a half, not two and a half


def test_ambient_motion_stops_behind_a_dialog_and_the_dialog_backdrop_has_no_pointless_blur():
    components, pages, site, js = static("css", "components.css"), static("css", "pages.css"), static("css", "site.css"), static("js", "site.js")
    backdrop = re.search(r"dialog::backdrop\s*\{([^}]*)\}", components).group(1)
    assert "backdrop-filter" not in backdrop and "radial-gradient" in backdrop
    assert "html.has-modal .hero__stage *" in pages and "html.has-modal .cast-open__bg .shot" in components
    assert js.count('classList.add("has-modal")') == 2 and js.count('classList.remove("has-modal")') == 2   # the video dialog and the image dialog both set and clear it
    header = re.search(r"\.site-header\.is-solid[^{]*\{([^}]*)\}", site).group(1)
    assert "backdrop-filter" not in header and "rgba(26, 23, 64, .985)" in header


def test_the_trailer_dialog_has_a_loading_state_a_slow_state_and_warms_rockstars_host_only_on_intent(client):
    p = page(client)
    assert 'data-player-status role="status"' in p
    js, components = static("js", "site.js"), static("css", "components.css")
    assert "Loading the official player" in js and "The player is taking a while." in js and "https://www.rockstargames.com/VI/media/videos" in js
    assert '["pointerenter", "focus", "touchstart"]' in js and 'link.rel = "preconnect"' in js and "warmed" in js
    assert ".player.is-loading" in components and "@keyframes playerShimmer" in components
    assert 'rel="preload" href="/static/fonts/barlow-condensed-normal-700.woff2"' in p                      # the display face is not discovered late


def test_the_garage_arrives_by_cross_fade_not_by_an_expanding_box_and_its_timings_agree():
    js, css = static("js", "garage_concept.js"), static("css", "garage_concept.css")
    for gone in ("origin(", "--ox", "--oy", "is-entering"):
        assert gone not in js, gone
    for gone in ("@keyframes gx-open", "clip-path", "is-entering", "--ox"):
        assert gone not in css, gone
    assert "var FADE = 350;" in js and ": 5) * 1000" in js and '"--gx-fade"' in js and '"--gx-push"' in js
    assert "var(--gx-fade, .35s)" in css and "var(--gx-push, 7s)" in css and "Math.max(PUSH, DWELL + FADE)" in js   # the script and the stylesheet name the same arrival, and the camera outlasts the scene
    assert "opacity: 0; transition: opacity var(--gx-fade, .35s)" in css and "z-index: var(--zi, 2)" in css and "String(++layer)" in js   # a transition on the scene itself; the newest is always on top
    assert "is-pending" in js and "is-pending" in css


def test_a_garage_choice_is_answered_quickly_and_the_automatic_hold_is_neither_too_fast_nor_too_slow():
    js, css = static("js", "garage_concept.js"), static("css", "garage_concept.css")
    fade = int(re.search(r"var FADE = (\d+);", js).group(1))
    hold = float(re.search(r"dwellSeconds : ([\d.]+)\) \* 1000", js).group(1)) * 1000
    push = int(re.search(r"var PUSH = (\d+);", js).group(1))
    assert 250 <= fade <= 400                                                                                # the cross-fade: a third of a second (it was 1.1 s)
    assert 4000 <= hold <= 6500 and push >= hold + fade                                                      # a hold that is not rushed (2.8 s was), and a camera that outlasts the stay
    delays = [float(x) for x in re.findall(r"is-active \.gx-copy > :nth-child\(\d\) \{ transition-delay: ([\d.]+)s; \}", css)]
    assert len(delays) == 4 and max(delays) <= 0.3                                                          # the new words begin within a third of a second and are all in by about half a second
    assert "transition: opacity .18s var(--ease)" in css and "transition: width .35s var(--ease)" in css  # the old words go at once; the index line grows with the arrival
    assert "cubic-bezier(.2, .6, .3, 1)" in css                                                              # the fade starts at once and lands softly
