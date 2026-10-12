"""Gate 3A: the Characters redesign. Official characters are the public cast; the three original characters stay in the
database for the DBMS demonstration and in the original stories, but never appear as part of the official cast."""
import re
from pathlib import Path

import pytest

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


def test_every_framing_in_the_stage_table_has_a_css_rule():
    css = (ROOT / "app" / "static" / "css" / "characters.css").read_text(encoding="utf-8")
    token = lambda v: v.replace("%", "").replace(" ", "-")
    for slug, spec in media_slots.CHARACTER_STAGE.items():
        for key in ("pos", "pos2", "pos_hero"):
            if spec.get(key):
                assert f'[data-pos="{token(spec[key])}"]' in css, (slug, key, spec[key])
        if spec.get("pos_t"):
            assert f'[data-pos-t="{token(spec["pos_t"])}"]' in css, (slug, spec["pos_t"])
        if spec.get("pos_m"):
            assert f'[data-pos-m="{token(spec["pos_m"])}"]' in css, (slug, spec["pos_m"])


def test_lucia_leads_with_a_bright_close_picture(client):
    page = client.get("/characters").get_data(as_text=True)
    lucia = page.split('id="lucia-caminos"')[1].split("</article>")[0]
    assert "Lucia_Caminos_02." in lucia                                  # the daylight picture, face large and lit
    assert "Lucia_Caminos_03." not in lucia                              # not the dim night shot
    assert media_slots.CHARACTER_STAGE["lucia-caminos"]["main"] == "shot-lucia-caminos-02"


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
    assert "265vw" in hero and 'data-pos="78-0"' in hero and 'data-pos-t="74-0"' in hero and 'data-pos-m="71-0"' in hero


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
    assert 'remove("is-rest", "is-live")' in script           # leaving the view brings the bright still back


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
