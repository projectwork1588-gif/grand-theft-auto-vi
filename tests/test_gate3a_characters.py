"""Gate 3A: the Characters redesign. Official characters are the public cast; the three original characters stay in the
database for the DBMS demonstration and in the original stories, but never appear as part of the official cast."""
import re
from pathlib import Path

import pytest
from scripts.fetch_clips import CHARACTER_CLIPS

from app import media_slots
from app.repositories import characters as repo
from app.repositories import regions as regions_repo

ROOT = Path(__file__).resolve().parent.parent
OFFICIAL = {"jason-duval", "lucia-caminos", "cal-hampton", "boobie-ike", "dre-quan-priest", "raul-bautista",
            "brian-heder", "real-dimez"}
ORIGINAL = {"delia-marsh", "nico-brandt", "tomas-reyes-hall"}


# ------------------------------------------------------------------ the public visibility rule
def slugs(rows):
    return {r["slug"] for r in rows}


def test_public_listing_is_official_only_and_original_needs_the_explicit_switch(app_context):
    rows, total = repo.search(None, None, None, "name_asc", 50, 0)
    assert total == 8 and slugs(rows) == OFFICIAL
    rows, total = repo.search(None, None, None, "name_asc", 50, 0, include_original=True)
    assert total == 11 and slugs(rows) == OFFICIAL | ORIGINAL


def test_public_search_cannot_reach_an_original_character_by_any_filter(app_context):
    for q_like, status, region in (("%Delia%", None, None), ("%Nico%", "demo", None), (None, "demo", None), (None, None, "port-gellhorn")):
        rows, total = repo.search(q_like, status, region, "name_asc", 50, 0)
        assert total == 0 and rows == [], (q_like, status, region)


def test_public_detail_hides_original_characters(app_context):
    for slug in ORIGINAL:
        assert repo.get_by_slug(slug) is None
        assert repo.get_by_slug(slug, include_original=True)["slug"] == slug
    assert repo.get_by_slug("jason-duval")["content_status"] == "official"


def test_public_connections_never_lead_to_an_original_character(app_context):
    ids = repo.ids_by_slug(["jason-duval", "delia-marsh"])
    # the demo relationships belong to the original characters only; an official profile shows none of them
    for slug in OFFICIAL:
        character_id = repo.ids_by_slug([slug])[slug]
        assert not slugs(repo.relationships_for(character_id)) & ORIGINAL, slug
        assert not slugs(repo.costars_for(character_id)) & ORIGINAL, slug
    delia = ids["delia-marsh"]
    assert repo.relationships_for(delia) == []                          # public view of an original: nothing to link to
    assert slugs(repo.relationships_for(delia, include_original=True)) == {"nico-brandt", "tomas-reyes-hall"}
    assert slugs(repo.costars_for(delia, include_original=True)) == {"nico-brandt", "tomas-reyes-hall"}


def test_region_pages_list_only_official_characters(app_context):
    vice_city = regions_repo.ids_by_slug(["vice-city"])["vice-city"]
    rows = regions_repo.characters_based_in(vice_city)
    assert [r["slug"] for r in rows] == ["boobie-ike"]
    assert rows[0]["home_location_name"]                                     # the sentence Rockstar's page supports


# ------------------------------------------------------------------ the data behind the redesign
def test_all_database_records_are_kept(cur):
    cur.execute("SELECT content_status AS s, COUNT(*) AS n FROM characters GROUP BY content_status")
    assert {r["s"]: r["n"] for r in cur.fetchall()} == {"official": 8, "demo": 3}
    cur.execute("SELECT COUNT(*) AS n FROM mission_characters")
    assert cur.fetchone()["n"] == 10                                      # the original stories keep their whole cast
    cur.execute("SELECT COUNT(*) AS n FROM character_relationships WHERE content_status = 'demo'")
    assert cur.fetchone()["n"] == 3


def test_dre_quan_and_real_dimez_relationship_is_sourced(cur):
    cur.execute("""SELECT cr.relationship_type, cr.description, cr.content_status, cr.source_url
                   FROM character_relationships cr
                   JOIN characters a ON a.character_id = cr.from_character_id
                   JOIN characters b ON b.character_id = cr.to_character_id
                   WHERE a.slug = 'dre-quan-priest' AND b.slug = 'real-dimez'""")
    row = cur.fetchone()
    assert row and row["relationship_type"] == "associate" and row["content_status"] == "official"
    assert row["source_url"].startswith("https://www.rockstargames.com/VI/")
    assert "Only Raw Records" in row["description"]


def test_every_official_relationship_has_a_source(cur):
    cur.execute("SELECT COUNT(*) AS n FROM character_relationships WHERE content_status = 'official' "
                "AND (source_url IS NULL OR source_url = '')")
    assert cur.fetchone()["n"] == 0
    cur.execute("SELECT COUNT(*) AS n FROM character_relationships WHERE content_status = 'official'")
    assert cur.fetchone()["n"] == 5


def test_character_regions_hold_only_what_rockstar_states(cur):
    cur.execute("""SELECT c.slug AS c, r.slug AS r, cg.source_url AS u
                   FROM character_regions cg JOIN characters c ON c.character_id = cg.character_id
                   JOIN regions r ON r.region_id = cg.region_id ORDER BY c.slug""")
    rows = cur.fetchall()
    assert [(x["c"], x["r"]) for x in rows] == [("boobie-ike", "vice-city"), ("brian-heder", "leonida-keys"), ("jason-duval", "leonida-keys")]
    assert all(x["u"].startswith("https://www.rockstargames.com/VI/") for x in rows)


def test_deleting_a_character_region_row_does_not_touch_the_character(conn, cur):
    cur.execute("DELETE FROM character_regions WHERE character_id = (SELECT character_id FROM characters WHERE slug = 'boobie-ike')")
    cur.execute("SELECT COUNT(*) AS n FROM characters WHERE slug = 'boobie-ike'")
    assert cur.fetchone()["n"] == 1
    conn.rollback()


def test_migration_005_is_non_destructive_and_repeatable():
    from scripts import migrate_db
    path = ROOT / "database" / "migrations" / "005_gate3a_cast.sql"
    migrate_db.check_non_destructive(path)                                # the project's own detector: no DROP, DELETE or TRUNCATE
    sql = path.read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS character_regions" in sql and "WHERE NOT EXISTS" in sql


# ------------------------------------------------------------------ original stories keep their cast, unlinked
def test_original_stories_name_their_cast_without_linking_it(client):
    page = client.get("/missions/last-call-smokestack-row").get_data(as_text=True)
    assert "Delia Marsh" in page or "Nico Brandt" in page or "Tomas Reyes-Hall" in page
    assert not re.search(r'href="/characters/(delia-marsh|nico-brandt|tomas-reyes-hall)"', page)
    assert "Original character" in page


def test_every_public_page_keeps_original_characters_out_of_the_cast(client):
    for path in ("/", "/characters", "/characters/jason-duval", "/regions/vice-city", "/regions/port-gellhorn"):
        page = client.get(path).get_data(as_text=True)
        assert not re.search(r'href="/characters/(delia-marsh|nico-brandt|tomas-reyes-hall)"', page), path


# ------------------------------------------------------------------ the framing, motion and markup rules
def test_new_templates_use_no_inline_styles_and_no_inline_script():
    for name in ("characters/index.html", "characters/detail.html", "characters/_cast.html"):
        source = (ROOT / "app" / "templates" / name).read_text(encoding="utf-8")
        assert not re.search(r"\sstyle\s*=", source), name
        assert not re.search(r"<script(?![^>]*\bsrc=)", source), name
        assert not re.search(r"\son[a-z]+\s*=", source), name


def test_every_framing_lands_on_the_css_grid():
    """Crops are computed from the faces (media_slots.IMAGE_FACE) and must land on the grid characters.css has rules for
    (X in steps of 2, Y in steps of 5), because the CSP forbids inline styles."""
    from app.services import site
    css = (ROOT / "app" / "static" / "css" / "characters.css").read_text(encoding="utf-8")
    for slug in media_slots.IMAGE_FACE:
        for aspect in (0.75, 0.8, 1.25, 1.6, 2.1, 4 / 3, 16 / 9):
            x, y = (int(v.strip("%")) for v in site.frame_pos(slug, aspect).split())
            assert x % 2 == 0 and y % 5 == 0 and 0 <= x <= 100 and 0 <= y <= 100, (slug, aspect, x, y)
            assert f'.shot[data-px="{x}"]' in css and f'.shot[data-py="{y}"]' in css, (slug, aspect, x, y)
            assert f'.shot[data-pxn="{x}"]' in css and f'.shot[data-pyn="{y}"]' in css, (slug, aspect, x, y)


def test_every_picture_the_pages_use_has_a_face_position():
    wanted = set()
    for pick in media_slots.CHARACTER_STAGE.values():
        wanted.update(pick[k] for k in ("hero", "card", "second") if pick[k])
    assert wanted <= set(media_slots.IMAGE_FACE), sorted(wanted - set(media_slots.IMAGE_FACE))


def test_a_head_is_never_cropped_out():
    """In every box the pages use, the face is inside the visible part of its picture."""
    from app.services import site
    for slug, (fx, fy) in media_slots.IMAGE_FACE.items():
        for aspect in (0.75, 0.8, 1.25, 1.6, 2.1, 4 / 3):
            x, y = (int(v.strip("%")) / 100 for v in site.frame_pos(slug, aspect).split())
            if aspect >= 16 / 9:
                window = (16 / 9) / aspect
                top = (1 - window) * y
                assert top - 0.02 <= fy <= top + window + 0.02, (slug, aspect)
            else:
                window = aspect / (16 / 9)
                left = (1 - window) * x
                assert left - 0.02 <= fx <= left + window + 0.02, (slug, aspect)


def test_no_profile_repeats_its_hero_in_the_story_or_the_overlap():
    for slug, pick in media_slots.CHARACTER_STAGE.items():
        if slug != "real-dimez":                                     # the one deliberate repeat: the duo's hero is the artwork of both
            assert pick["hero"] != pick["main"], slug                # the hero and the large picture below it differ
        if slug != "dre-quan-priest":                                # his one official solo picture: wide in the hero, a tall cut in the overlap
            assert pick["hero"] != pick["second"], slug              # and so do the hero and the overlapping picture
        assert pick["main"] != pick["second"] or pick["second"] is None, slug


def test_overlap_pictures_keep_the_profiles_subject():
    """What shows until the still frames are built, and what the frames are: nobody's overlap is someone else's picture."""
    stage = media_slots.CHARACTER_STAGE
    assert stage["dre-quan-priest"]["second"] == "shot-dequan-priest-02" and stage["dre-quan-priest"]["shape"] == "tall"
    assert stage["real-dimez"]["second"] is None                                      # no overlap until the duo frame exists
    for slug, pick in stage.items():
        for role in ("card", "second"):
            if pick[role] and slug != "dre-quan-priest":
                assert "dequan" not in pick[role], (slug, role)                       # the group screenshot is nobody's picture
    assert stage["real-dimez"]["main"] == stage["real-dimez"]["hero"] == stage["real-dimez"]["card"] == "art-real-dimez"
    picks = media_slots.LOCAL_STILL_PICKS
    assert picks["real-dimez"]["second"][0] == "real-dimez-duo" and picks["real-dimez"]["second"][2] == "wide"
    assert picks["dre-quan-priest"]["second"][0] == "dre-quan-priest-studio" and picks["dre-quan-priest"]["second"][2] == "tall"
    for name in (v[0] for roles in picks.values() for v in roles.values()):
        spec = media_slots.LOCAL_STILLS[name]
        assert spec["clip"] in CHARACTER_CLIPS and 0 <= spec["frame"] < 30 and (spec["crop"][0] + spec["crop"][2] <= 2160 if "crop" in spec else True)
    assert media_slots.LOCAL_STILLS["real-dimez-duo"]["clip"] == "Real_Dimez_Video_Clip"      # frames of the duo's own clip only
    assert media_slots.LOCAL_STILLS["dre-quan-priest-studio"]["clip"] == "DreQuan_Priest_Video_Clip"


@pytest.fixture()
def local_stills(app, tmp_path):
    """A media folder holding stand-ins for the frames `make_loops --stills` builds."""
    clips = tmp_path / "clips"
    clips.mkdir()
    for name in media_slots.LOCAL_STILLS:
        (clips / f"{name}.jpg").write_bytes(b"JFIF")
        (clips / f"{name}-800.jpg").write_bytes(b"JFIF")
    previous = app.config["MEDIA_ROOT"]
    app.config["MEDIA_ROOT"] = str(tmp_path)
    yield tmp_path
    app.config["MEDIA_ROOT"] = previous


def _story_media(page):
    return page.split('class="p-media p-media--')[1].split("</section>")[0]


def test_dre_quans_overlap_is_a_different_picture_from_his_hero(client, local_stills):
    page = client.get("/characters/dre-quan-priest").get_data(as_text=True)
    hero = page.split('<header class="p-hero')[1].split("</header>")[0]
    media = _story_media(page)
    assert "DreQuan_Priest_02" in hero                                                  # the pool-bar screenshot opens the page
    assert "p-media__second--tall" in media and "/media/clips/dre-quan-priest-studio.jpg" in media
    assert "DreQuan_Priest_02" not in media and "DreQuan_Priest_01" not in media        # and is not repeated in the story
    assert "Real_Dimez" not in media and "real-dimez" not in media


def test_dre_quans_story_shows_him_not_the_duo_before_the_frames_exist(client):
    media = _story_media(client.get("/characters/dre-quan-priest").get_data(as_text=True))
    assert "p-media__second--tall" in media and "DreQuan_Priest_02" in media and "DreQuan_Priest_01" not in media
    assert "Real_Dimez" not in media


def test_real_dimez_keeps_its_overlap_with_both_women(client, local_stills):
    page = client.get("/characters/real-dimez").get_data(as_text=True)
    media = _story_media(page)
    assert 'class="p-media p-media--square" data-solo' not in page and "data-solo" not in media[:60]
    assert 'class="p-media__second p-media__second--wide"' in media and "/media/clips/real-dimez-duo.jpg" in media
    assert media.index("motion-portrait__frame") < media.index('class="p-media__second ')       # in front of the large picture
    assert "Real_Dimez_landscape" not in media.split('class="p-media__second')[1]               # the overlap is the frame, not the artwork again
    assert "DreQuan_Priest" not in media


def test_real_dimez_overlap_falls_back_to_the_duo_alone(client):
    page = client.get("/characters/real-dimez").get_data(as_text=True)
    media = _story_media(page)
    assert "data-solo" in page.split('class="p-media p-media--')[1][:40] and 'class="p-media__second' not in media
    assert "DreQuan_Priest" not in media


def test_real_dimez_landing_tile_rests_on_the_footage_not_the_artwork(client, local_portraits):
    """The tile beside the large artwork must not rest on that artwork: it uses its own sequence, the profile keeps the artwork one."""
    (local_portraits / "clips" / "real-dimez-landing.mp4").write_bytes(b"ftypmp42")
    (local_portraits / "clips" / "real-dimez-landing.jpg").write_bytes(b"JFIF")
    landing = client.get("/characters").get_data(as_text=True)
    tile = landing.split('id="real-dimez"')[1].split("</article>")[0]
    assert "/media/clips/real-dimez-landing.mp4" in tile and "/media/clips/real-dimez-landing.jpg" in tile
    assert "real-dimez-profile" not in tile
    for slug in ("cal-hampton", "boobie-ike", "dre-quan-priest", "raul-bautista", "brian-heder"):      # nobody else changed
        other = landing.split(f'id="{slug}"')[1].split("</article>")[0]
        assert f"/media/clips/{slug}-profile.mp4" in other and "-landing" not in other, slug
    profile = client.get("/characters/real-dimez").get_data(as_text=True)
    assert "/media/clips/real-dimez-profile.mp4" in profile and "real-dimez-landing" not in profile   # the profile keeps the artwork sequence


def test_real_dimez_landing_tile_falls_back_to_the_profile_sequence(client, local_portraits):
    tile = client.get("/characters").get_data(as_text=True).split('id="real-dimez"')[1].split("</article>")[0]
    assert "/media/clips/real-dimez-profile.mp4" in tile and "real-dimez-landing" not in tile


def test_the_landing_rest_still_is_a_footage_frame_of_the_duo():
    assert media_slots.LANDING_REST == {"real-dimez": "real-dimez-duo"}
    assert media_slots.LOCAL_STILLS["real-dimez-duo"]["clip"] == "Real_Dimez_Video_Clip"


def test_real_dimez_has_no_gallery_and_nobody_else_lost_theirs(client):
    page = client.get("/characters/real-dimez").get_data(as_text=True)
    assert 'id="gallery-title"' not in page and "From the footage and artwork" not in page and "p-gallery" not in page
    for slug in ("jason-duval", "lucia-caminos"):
        assert 'id="gallery-title"' in client.get(f"/characters/{slug}").get_data(as_text=True), slug


def test_the_landing_picture_of_real_dimez_is_the_duo_without_dre_quan(client, local_portraits):
    page = client.get("/characters").get_data(as_text=True)
    article = page.split('id="real-dimez"')[1].split("</article>")[0]
    art = article.split('class="person__art"')[1].split("</a>")[0]
    assert "Real_Dimez_landscape" in art and "DreQuan_Priest" not in art
    assert "motion-portrait" in article                                                 # the IN MOTION tile is unchanged




def test_lucia_leads_with_a_distinct_lit_close_picture(client):
    page = client.get("/characters").get_data(as_text=True)
    lucia = page.split('id="lucia-caminos"')[1].split("</article>")[0]
    assert "Lucia_Caminos_01." in lucia and "Lucia_Caminos_02." not in lucia     # the spread is not the pool artwork her tile rests on
    assert media_slots.CHARACTER_STAGE["lucia-caminos"]["main"] == "shot-lucia-caminos-02"


def test_leads_landing_picture_is_not_the_artwork_their_tile_rests_on():
    for slug in media_slots.CAST_LEADS:
        pick = media_slots.CHARACTER_STAGE[slug]
        assert pick["card"] != pick["main"], slug


def test_hero_images_are_full_bleed_for_all_eight(client):
    for slug in media_slots.CHARACTERS_ORDER:
        page = client.get(f"/characters/{slug}").get_data(as_text=True)
        assert 'class="p-hero p-hero--full p-hero--' in page and "p-hero--split" not in page, slug
        hero = page.split('class="p-hero__art"')[1].split("</div>")[0]
        assert "data-px=" in hero and "data-pxn=" in hero, slug


def test_partner_banner_shows_both_protagonists_from_one_official_screenshot(client):
    page = client.get("/characters").get_data(as_text=True)
    banner = page.split('class="together"')[1].split("</div>")[0]
    assert "Jason_and_Lucia_01." in banner and "Jason_and_Lucia_03." not in banner
    assert media_slots.CAST_TOGETHER == "shot-jason-and-lucia-01"


def test_pictures_declare_the_width_they_are_really_drawn_at(client):
    """A tall crop of a 16:9 picture is drawn much wider than its box. `sizes` that only describe the box make the browser
    pick a small file and upscale it, which is what made the Lucia spread soft."""
    page = client.get("/characters").get_data(as_text=True)
    spread = page.split('id="jason-duval"')[1].split("</article>")[0]
    assert 'sizes="(min-width: 1100px) 94vw, (min-width: 761px) 170vw, 205vw"' in spread
    assert 'sizes="max(100vw, 185vh)"' in page.split('class="cast-open"')[1].split("</header>")[0]
    hero = client.get("/characters/jason-duval").get_data(as_text=True).split('class="p-hero__art"')[1].split("</div>")[0]
    assert "265vw" in hero and "data-px=" in hero and "data-pxn=" in hero


def test_poster_lift_is_gentle_and_never_applied_to_a_bright_clip():
    from scripts import make_loops
    assert make_loops.poster_gamma(200) == 1.0 and make_loops.poster_gamma(make_loops.POSTER_TARGET) == 1.0
    lifts = [make_loops.poster_gamma(m) for m in (70, 50, 30, 10, 1)]
    assert lifts == sorted(lifts) and 1.0 < lifts[0] and lifts[-1] <= make_loops.POSTER_MAX_GAMMA
    assert 0.4 <= make_loops.POSTER_AT <= 0.7        # after the fade from black, before the dissolve into the artwork


def test_motion_portrait_keeps_the_still_until_the_clip_is_playing():
    css = (ROOT / "app" / "static" / "css" / "characters.css").read_text(encoding="utf-8")
    assert re.search(r"\.motion-portrait__video \{[^}]*opacity: 0", css)
    assert re.search(r"\.motion-portrait\.is-live \.motion-portrait__video \{[^}]*opacity: 1", css)
    script = (ROOT / "app" / "static" / "js" / "site.js").read_text(encoding="utf-8")
    assert 'classList.remove("is-live", "is-rest")' in script         # leaving the view brings the artwork back


def test_lead_heroes_start_below_the_header_so_the_head_always_has_room():
    css = (ROOT / "app" / "static" / "css" / "characters.css").read_text(encoding="utf-8")
    assert re.search(r"\.p-hero--full \.p-hero__art \{[^}]*top: var\(--header-h\)", css)


def test_the_cast_page_script_respects_motion_and_never_loops_a_clip():
    script = (ROOT / "app" / "static" / "js" / "site.js").read_text(encoding="utf-8")
    block = script.split("function portraits()")[1].split("function loops()")[0]
    assert "motionAllowed()" in block and "loop" not in block.replace("loops", "").replace("preload", "")
    assert "ended" in block and "IntersectionObserver" in block


def test_cast_order_covers_exactly_the_eight_official_characters():
    assert set(media_slots.CHARACTER_STAGE) == OFFICIAL
    assert set(media_slots.CAST_LEADS) == {"jason-duval", "lucia-caminos"}
    assert set(media_slots.NETWORK_LAYOUT) == OFFICIAL


@pytest.mark.parametrize("path", ["/characters", "/characters/jason-duval", "/characters/real-dimez"])
def test_character_pages_have_one_h1_and_labelled_landmarks(client, path):
    page = client.get(path).get_data(as_text=True)
    assert len(re.findall(r"<h1[ >]", page)) == 1
    assert 'id="main"' in page and "<main" in page
    assert not re.search(r"<img(?![^>]*\balt=)", page), path               # every picture states its alt text


def test_jump_bar_marks_the_person_being_read_and_never_contradicts_a_click():
    script = (ROOT / "app" / "static" / "js" / "site.js").read_text(encoding="utf-8")
    block = script.split("function castNavigation()")[1].split("var web = document.querySelector")[0]
    assert "window.innerHeight * 0.45" in block                     # one reading line
    assert "locked" in block and "lockSeen" in block                  # a chosen name stays marked until it has been seen and left
    assert "requestAnimationFrame" in block and "passive: true" in block


# ------------------------------------------------------------------ final profile and motion polish
def test_each_person_is_shown_in_the_shape_the_footage_was_shot_in(client, local_portraits):
    for slug in ("jason-duval", "lucia-caminos"):
        page = client.get(f"/characters/{slug}").get_data(as_text=True)
        assert "motion-portrait--wide" in page and f'data-src="/media/clips/{slug}-profile.mp4"' in page, slug
        assert 'class="p-story p-story--wide"' in page and 'class="p-media p-media--wide"' in page, slug
    for slug in ("cal-hampton", "boobie-ike", "dre-quan-priest", "real-dimez", "raul-bautista", "brian-heder"):
        page = client.get(f"/characters/{slug}").get_data(as_text=True)
        assert "motion-portrait--square" in page and "motion-portrait--wide" not in page, slug
        assert f'data-src="/media/clips/{slug}-profile.mp4"' in page, slug
        assert 'class="p-story p-story--square"' in page and 'class="p-media p-media--square"' in page, slug
        assert 'data-poster-at="0"' in page, slug               # the sequence starts on the still: nothing to match up


def test_the_landing_tiles_use_the_same_sequences_as_the_profiles(client, local_portraits):
    """One pipeline: a person's tile on the landing page and their profile play the same file, so the pacing cannot differ."""
    page = client.get("/characters").get_data(as_text=True)
    assert page.count("-profile.mp4") == 8 and page.count("motion-portrait--wide") == 2 and page.count("motion-portrait--square") == 6
    assert page.count("motion-portrait--tile") == 6 and "-portrait.mp4" not in page and "motion-portrait--legacy" not in page
    assert page.count('data-poster-at="0"') == 8


def test_the_homepage_keeps_its_own_clips(client, local_portraits):
    home = client.get("/").get_data(as_text=True)
    assert "-portrait" not in home and "-profile" not in home


def test_pages_fall_back_to_the_older_loop_until_the_sequences_are_built(client, local_clips):
    page = client.get("/characters/cal-hampton").get_data(as_text=True)      # local_clips has only the older loops
    assert "motion-portrait--legacy" in page and 'class="p-media p-media--square"' in page
    assert "p-media__second" in page                                         # the layout does not depend on the footage


def test_the_second_picture_overlaps_the_large_picture(client):
    for slug in ("jason-duval", "lucia-caminos", "cal-hampton", "boobie-ike", "dre-quan-priest", "raul-bautista", "brian-heder"):
        page = client.get(f"/characters/{slug}").get_data(as_text=True)
        media = page.split('class="p-media p-media--')[1].split("</section>")[0]
        assert media.index("motion-portrait__frame") < media.index('class="p-media__second '), slug     # in front, after it
        assert media.count("<img") >= 2, slug                                   # the large picture and the small one
        assert "p-story__second" not in page, slug


def test_the_gallery_does_not_repeat_the_two_pictures_above_it(client):
    page = client.get("/characters/jason-duval").get_data(as_text=True)
    gallery = page.split('id="gallery-title"')[1].split("</section>")[0]
    assert "Jason_Duval_01." not in gallery and "Jason_Duval_04." not in gallery


def test_overlap_geometry_is_in_css():
    css = (ROOT / "app" / "static" / "css" / "characters.css").read_text(encoding="utf-8")
    second = re.search(r"\.p-media__second \{([^}]*)\}", css).group(1)
    assert "position: absolute" in second and "right: calc(-1 * var(--ov-x))" in second and "bottom: calc(-1 * var(--ov-y))" in second
    assert "width: 46%" in second and "z-index: 2" in second and "box-shadow" in second and "border-radius" in second
    assert re.search(r"\.p-media \{[^}]*margin: 0 var\(--ov-x\) calc\(var\(--ov-y\) \+ 26px\) 0", css)   # the overhang has room
    assert "width: 44%" in css and "width: 42%" in css                    # tablet and phone proportions
    assert re.search(r"\.p-media--square \.p-media__second--tall \{[^}]*aspect-ratio: 4 / 5", css)
    assert re.search(r"\.p-media--square \.p-media__second--wide \{[^}]*aspect-ratio: 4 / 3", css)   # the duo's wide second picture


def test_portrait_builder_tables_cover_every_person():
    from scripts import make_loops
    squares = set(media_slots.CAST_ORDER) - set(media_slots.PORTRAIT_SHAPE)
    assert set(media_slots.PORTRAIT_SHAPE) == set(media_slots.CAST_LEADS)
    assert set(make_loops.PORTRAIT_FOCUS) == squares                      # each square clip has a focus for its artwork crop
    assert all(0.2 <= v <= 0.8 for v in make_loops.PORTRAIT_FOCUS.values())
    w, h = make_loops.PORTRAIT_SIZE["wide"]
    assert (w, h) == (1600, 900) and make_loops.PORTRAIT_SIZE["square"][0] == make_loops.PORTRAIT_SIZE["square"][1]
    assert make_loops.PORTRAIT_MAX_GAMMA <= 1.8                           # a lift, never a re-grade


def test_motion_tiles_are_never_cropped_or_stretched():
    css = (ROOT / "app" / "static" / "css" / "characters.css").read_text(encoding="utf-8")
    assert re.search(r"\.motion-portrait__frame \{[^}]*aspect-ratio: 1;", css)
    assert re.search(r"\.motion-portrait--wide \.motion-portrait__frame \{[^}]*aspect-ratio: 16 / 9;", css)
    assert re.search(r"\.motion-portrait__poster, \.motion-portrait__video \{[^}]*object-fit: cover", css)


def test_profile_sequence_constants_match_the_approved_pacing():
    from scripts import make_loops
    assert make_loops.PORTRAIT_DISSOLVE == 0.5 and make_loops.PORTRAIT_HOLD == 2.0 and make_loops.PROFILE_INTRO == 0.3
    assert make_loops.SPEED == 1.0                                          # never slowed down or sped up
    assert set(make_loops.PROFILE_ART) <= set(media_slots.CAST_ORDER)
    assert make_loops.profile_art("lucia-caminos").name == "lucia-caminos-main.jpg"
    assert make_loops.profile_art("jason-duval").name == "jason-duval.jpg"


def test_locally_built_profile_sequences_have_the_approved_length_when_they_exist():
    from scripts import make_loops
    ffmpeg = make_loops.ffmpeg_exe()
    built = [slug for slug in media_slots.CAST_ORDER if (make_loops.CLIPS_DIR / f"{slug}-profile.mp4").exists()]
    if not built:
        pytest.skip("the profile sequences have not been built on this machine")
    stems = {slug: stem for stem, (slug, _n) in make_loops.SLUGS.items()}
    for slug in built:
        clip = make_loops.duration(ffmpeg, make_loops.SOURCE_DIR / f"{stems[slug]}.mp4")
        total = make_loops.duration(ffmpeg, make_loops.CLIPS_DIR / f"{slug}-profile.mp4")
        expected = clip + make_loops.PROFILE_INTRO + make_loops.PORTRAIT_DISSOLVE + make_loops.PORTRAIT_HOLD
        assert abs(total - expected) < 0.15, (slug, total, expected)


def test_supporting_cards_layer_the_clip_over_their_picture(client):
    page = client.get("/characters").get_data(as_text=True)
    cards = page.split('class="tier tier--crew"')[1].split('class="web"')[0]
    assert cards.count('class="person__media"') == 6
    for chunk in cards.split('class="person__media"')[1:]:
        assert chunk.index("person__art") < chunk.index("motion-portrait--tile") if "motion-portrait--tile" in chunk else True


def test_the_landing_has_one_motion_controller_with_a_dwell_and_no_cut_off():
    script = (ROOT / "app" / "static" / "js" / "site.js").read_text(encoding="utf-8")
    block = script.split("(function portraits() {")[1].split("// ---- Short muted loops")[0]
    assert "DWELL" in block and "finish(p)" in block and "toArtwork(p)" in block
    assert "is-blocked" in block and "NotAllowedError" in block
    assert block.count(".loop") == 0 and " loop" not in block.replace("loops", "")


def test_the_network_names_never_sit_under_a_line():
    assert media_slots.NETWORK_NAME_RIGHT <= set(media_slots.NETWORK_LAYOUT)
    xs = {media_slots.NETWORK_LAYOUT[s][0] for s in media_slots.NETWORK_NAME_RIGHT}
    assert len(xs) == 1                                                     # one column, so its lines are vertical


def test_one_sequence_set_and_a_stronger_compression_for_the_characters_pages():
    from scripts import make_loops
    assert not hasattr(make_loops, "build_portrait")                      # the landing no longer has its own, different build
    assert "27" in make_loops.PROFILE_FINAL and "25" in make_loops.FINAL    # light files; the homepage reel keeps its own quality
    assert make_loops.SPEED == 1.0


def test_motion_controller_waits_for_the_whole_sequence_and_the_nav_resets():
    script = (ROOT / "app" / "static" / "js" / "site.js").read_text(encoding="utf-8")
    block = script.split("(function portraits() {")[1].split("// ---- Short muted loops")[0]
    assert "readyState < 4" in block and "canplaythrough" in block
    nav = script.split("function castNavigation()")[1].split("var web = document.querySelector")[0]
    assert "list.scrollTo({ left: 0" in nav


# ------------------------------------------------------------------ the final cast order
ORDER = ["jason-duval", "lucia-caminos", "cal-hampton", "brian-heder", "boobie-ike", "dre-quan-priest", "real-dimez", "raul-bautista"]
RING = {  # slug: (previous, next): the owner's circular order
    "jason-duval": ("raul-bautista", "lucia-caminos"), "lucia-caminos": ("jason-duval", "cal-hampton"),
    "cal-hampton": ("lucia-caminos", "brian-heder"), "brian-heder": ("cal-hampton", "boobie-ike"),
    "boobie-ike": ("brian-heder", "dre-quan-priest"), "dre-quan-priest": ("boobie-ike", "real-dimez"),
    "real-dimez": ("dre-quan-priest", "raul-bautista"), "raul-bautista": ("real-dimez", "jason-duval"),
}


def test_the_canonical_order_is_one_tuple_and_the_homepage_keeps_its_own():
    assert list(media_slots.CHARACTERS_ORDER) == ORDER
    assert media_slots.CAST_ORDER != media_slots.CHARACTERS_ORDER          # the homepage reel is not touched
    assert set(media_slots.CAST_ORDER) == set(media_slots.CHARACTERS_ORDER)


def test_previous_and_next_follow_the_circular_order_on_every_profile(client):
    for slug, (previous, following) in RING.items():
        page = client.get(f"/characters/{slug}").get_data(as_text=True)
        nxt = page.split('class="p-next"')[1].split("</section>")[0]
        prev_link = re.search(r'<a class="p-next__card" href="/characters/([a-z-]+)" rel="prev"', nxt)
        next_link = re.search(r'<a class="p-next__card" href="/characters/([a-z-]+)" rel="next"', nxt)
        assert prev_link and prev_link.group(1) == previous, (slug, "prev")
        assert next_link and next_link.group(1) == following, (slug, "next")
        assert f"<small>Previous</small><b>" in nxt and "<small>Next</small><b>" in nxt


def test_the_footer_list_and_the_numbers_follow_the_order(client):
    for number, slug in enumerate(ORDER, start=1):
        page = client.get(f"/characters/{slug}").get_data(as_text=True)
        assert f"{number:02d} / 08" in page, slug
        nav = page.split('aria-label="All eight characters"')[1].split("</nav>")[0]
        assert re.findall(r'href="/characters/([a-z-]+)"', nav) == ORDER, slug
        assert re.findall(r"<span>(\d\d)</span>", nav) == [f"{i:02d}" for i in range(1, 9)], slug


def test_the_landing_jump_bar_cards_and_explore_default_follow_the_order(client):
    page = client.get("/characters").get_data(as_text=True)
    nav = page.split("data-cast-nav")[1].split("</nav>")[0]
    assert re.findall(r'href="#([a-z-]+)"', nav)[:8] == ORDER
    assert re.findall(r'<span class="cast-nav__no">(\d\d)</span>', nav) == [f"{i:02d}" for i in range(1, 9)]
    cards = re.findall(r'<article class="(?:spread|person)[^"]*" id="([a-z-]+)"', page)
    assert cards == ORDER
    results_page = client.get("/characters?sort=cast&per_page=50").get_data(as_text=True)
    assert re.findall(r'href="/characters/([a-z-]+)"', results_page.split('class="results__list"')[1].split("</ul>")[0]) == ORDER
    assert '<option value="cast" selected>' in results_page                  # the default choice in the Explore form
    assert '<option value="cast" selected>' in page


def test_the_api_keeps_its_alphabetical_default_and_offers_the_cast_order(client):
    names = [c["slug"] for c in client.get("/api/v1/characters").get_json()["data"]]
    assert names == sorted(names, key=lambda s: client.get(f"/api/v1/characters/{s}").get_json()["full_name"])
    assert [c["slug"] for c in client.get("/api/v1/characters?sort=cast&per_page=50").get_json()["data"]] == ORDER
    assert client.get("/api/v1/characters?sort=cast&include=original&per_page=50").get_json()["data"][-3]["slug"] in {
        "delia-marsh", "nico-brandt", "tomas-reyes-hall"}               # originals come after the cast


# ------------------------------------------------------------------ relationship network portraits
def test_every_node_has_a_portrait_and_the_duo_has_two_circles(client):
    page = client.get("/characters").get_data(as_text=True)
    svg = page.split("data-network")[1].split('class="web__list"')[0]
    for slug in ORDER:
        node = re.search(rf'<a class="node[^"]*" href="/characters/{slug}".*?</a>', svg, re.S).group(0)
        assert "<image " in node and "Jason_and_Lucia" in node or "<image " in node, slug
        assert node.count("av__ring") == (2 if slug == "real-dimez" else 1), slug
    assert set(media_slots.AVATARS) == set(media_slots.CHARACTERS_ORDER)
    assert len(media_slots.AVATARS["real-dimez"]["heads"]) == 2


def test_portraits_come_from_the_artwork_not_scene_screenshots():
    for slug, spec in media_slots.AVATARS.items():
        assert spec["media"].startswith("art-"), slug                       # one lighting and one style for all eight
        for head in spec["heads"]:
            x, y, h = head[:3]
            assert 0.1 <= h <= 0.4 and 0 < x < 1 and 0 < y < 1, (slug, head)
            assert y - h / 2 >= -0.01 and y + h / 2 <= 1, (slug, head)     # the whole head is inside its picture
    assert 0.6 <= media_slots.AVATAR_HEAD <= 0.8


def test_every_portrait_is_drawn_by_the_one_macro_with_the_same_head_size(client):
    page = client.get("/characters").get_data(as_text=True)
    assert "class=\"av__fill\"" not in page
    for slug in ("jason-duval", "dre-quan-priest", "raul-bautista"):
        profile = client.get(f"/characters/{slug}").get_data(as_text=True)
        assert 'class="p-conn__face"' in profile or "has not stated any connections" in profile, slug
    # the connection cards and the network use the same macro and the same specs: no second crop table exists
    css = (ROOT / "app" / "static" / "css" / "characters.css").read_text(encoding="utf-8")
    assert "p-conn__face .shot" not in css


def test_a_person_with_no_stated_connection_keeps_a_bright_portrait():
    css = (ROOT / "app" / "static" / "css" / "characters.css").read_text(encoding="utf-8")
    assert not re.search(r"\.node--alone\s*\{[^}]*opacity", css)               # the portrait is never dimmed
    assert ".node--alone .av__ring" in css


def test_real_dimez_hero_shows_both_members(client):
    page = client.get("/characters/real-dimez").get_data(as_text=True)
    hero = page.split('class="p-hero p-hero--full')[1].split("</header>")[0]
    assert "p-hero--duo" in page and "Real_Dimez_landscape" in hero          # the artwork of both women
    assert "p-hero--left" in page.split('class="p-hero p-hero--full')[1][:60]
    css = (ROOT / "app" / "static" / "css" / "characters.css").read_text(encoding="utf-8")
    assert re.search(r"\.p-hero--duo \.p-hero__art \{[^}]*height: calc\(140vw", css)    # shown whole on narrow screens


# ------------------------------------------------------------------ one complete playback per genuine visit
def test_motion_controller_is_a_state_machine_with_rearm_on_leaving():
    script = (ROOT / "app" / "static" / "js" / "site.js").read_text(encoding="utf-8")
    block = script.split("(function portraits() {")[1].split("// ---- Short muted loops")[0]
    for token in ('"armed"', '"playing"', '"rested"', "REARM", "ENTER", "KEEP", "data-state", "pick(ready)", "rootMargin"):
        assert token in block, token
    assert 'p.state === "rested" && p.ratio < REARM' in block              # a finished tile is re-armed once it has left the view
    assert "done" not in block.replace("done:", "")                         # the old one-way flag is gone
    assert block.count(".loop") == 0
def test_the_phone_list_shows_the_portraits_and_the_person_without_a_stated_connection(client):
    page = client.get("/characters").get_data(as_text=True)
    items = page.split('class="web__list"')[1].split("</ul>")[0]
    assert items.count('class="web__faces"') == 6                           # five relationships and Raul
    assert "Raul Bautista" in items and "No stated connection yet" in items
