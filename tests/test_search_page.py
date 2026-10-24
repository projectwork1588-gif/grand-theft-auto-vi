"""The /search page (Stage 4B, milestone 2): server-rendered, works without JavaScript, escapes everything, pages through results, keeps CSP, and says what it found
in words a screen reader announces. Reads the *_test database only."""
import re

import mysql.connector.errors
import pytest

from app.repositories import search as search_repo


def get(client, **params):
    return client.get("/search", query_string=params)


def text(response):
    return response.get_data(as_text=True)


def hrefs_in_results(page):
    region = page.split('id="results"', 1)[1]
    return re.findall(r'class="hit" href="([^"]+)"', region)


# ------------------------------------------------------------------ the states
def test_without_a_query_the_page_explains_itself_and_searches_nothing(client, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("an empty search must not touch the database")
    monkeypatch.setattr(search_repo, "query_all", forbidden)
    response = get(client)
    page = text(response)
    assert response.status_code == 200 and "What are you looking for?" in page and 'role="status"' in page
    assert 'name="q"' in page and 'role="search"' in page


def test_results_show_title_kind_detail_and_a_concept_label(client):
    page = text(get(client, q="neon row"))
    assert "Neon Row District" in page and 'href="/locations/neon-row-district"' in page
    assert re.search(r'class="hit__kind">Place<', page) and "Concept" in page
    assert re.search(r'role="status">1&ndash;\d+ of \d+ for &ldquo;neon row&rdquo;', page)


def test_official_results_are_labelled_official_and_pages_carry_no_label(client):
    page = text(get(client, q="jason"))
    assert 'href="/characters/jason-duval"' in page and "badge--official" in page
    assert 'class="hit__kind">Page<' in page


def test_the_type_chips_count_each_kind_and_mark_the_current_one(client):
    page = text(get(client, q="vice", type="place"))
    assert 'aria-label="Result types"' in page
    assert re.search(r'<a class="chip" href="/search\?q=vice&amp;type=place#results" aria-current="true">Place <small>\d+</small>', page)
    assert all("/locations/" in h for h in hrefs_in_results(page))
    assert 'name="type" value="place"' in page


def test_nothing_found_is_said_plainly(client):
    page = text(get(client, q="zzzzqqxx"))
    assert "Nothing found" in page and "No matches for" in page and 'class="hit"' not in page


def test_the_results_have_one_labelled_region_one_h1_and_noindex(client):
    page = text(get(client, q="vice"))
    assert page.count('id="results"') == 1 and 'aria-label="Search results"' in page and page.count("<h1") == 1
    assert '<meta name="robots" content="noindex">' in page
    assert page.index('role="search"') < page.index('id="results"') < page.index('role="status"', page.index('id="results"') - 5)
    assert 'action="/search#results"' in page


def test_the_page_is_titled_and_has_no_inline_script_or_style(client):
    page = text(get(client, q="vice"))
    assert "<title>Search | Team Valkyrie</title>" in page
    assert not re.search(r"<script(?![^>]*\bsrc=)[^>]*>", page) and " style=" not in page and " onclick=" not in page


# ------------------------------------------------------------------ escaping
HOSTILE = ['"><script>alert(1)</script>', "<img src=x onerror=alert(1)>", "'; DROP TABLE users; --", "&lt;b&gt;", "\"onfocus=\"alert(1)\" autofocus=\""]


@pytest.mark.parametrize("q", HOSTILE)
def test_the_query_is_reflected_escaped_everywhere(client, q):
    from markupsafe import escape
    page = text(get(client, q=q))
    assert "<script>alert" not in page and "<img src=x" not in page and 'onfocus="alert' not in page
    assert f'name="q" value="{escape(q)}"' in page                          # in the box exactly as Jinja escapes it, and nowhere raw
    assert page.count(q) == 0                                              # every hostile string here contains a character Jinja escapes


def test_hostile_values_in_the_database_are_escaped(client, monkeypatch):
    hostile = {"kind": "story", "slug": "harbour-lights", "title": "<img src=x onerror=alert(1)>", "detail": "<script>alert(2)</script>",
               "summary": "\"><svg onload=alert(3)>", "status": "demo", "anchor": "", "rank_": 100}
    monkeypatch.setattr(search_repo, "search", lambda *a, **k: [hostile])
    monkeypatch.setattr(search_repo, "counts", lambda *a, **k: {"story": 1})
    page = text(get(client, q="anything"))
    assert "<img src=x" not in page and "<script>alert(2)" not in page and "<svg onload" not in page
    assert "&lt;img src=x onerror=alert(1)&gt;" in page


def test_every_result_address_on_the_page_is_a_local_page_that_exists(client):
    page = text(get(client, q="a", per_page=50))
    found = hrefs_in_results(page)
    assert len(found) > 10
    for href in found:
        assert href.startswith("/") and not href.startswith("//")
        assert client.get(href.split("#")[0]).status_code == 200, href


# ------------------------------------------------------------------ paging and errors
def test_results_are_paged_and_the_pager_lands_on_the_results(client):
    first = text(get(client, q="a", per_page=3))
    assert 'class="pager"' in first and 'rel="next"' in first and re.search(r'href="/search\?q=a&amp;per_page=3&amp;page=2#results"', first)
    second = text(get(client, q="a", per_page=3, page=2))
    assert hrefs_in_results(first) != hrefs_in_results(second) and len(hrefs_in_results(second)) == 3
    assert 'start="4"' in second and re.search(r"4&ndash;6 of \d+", second)


@pytest.mark.parametrize("params", [{"q": "x" * 81}, {"q": "a b c d e f"}, {"q": "a", "type": "nonsense"}, {"q": "a", "page": "0"}, {"q": "a", "per_page": "99"},
                                    {"q": "a", "page": "999"}, {"q": "a", "page": "many"}])
def test_bad_input_is_the_sites_own_400_page(client, params):
    response = get(client, **params)
    page = text(response)
    assert response.status_code == 400 and "text/html" in response.content_type and 'class="link-list error-details"' in page and "Bad request" in page


def test_a_database_failure_is_the_branded_503_page(client, monkeypatch):
    def broken(*args, **kwargs):
        raise mysql.connector.errors.DatabaseError("secret-host password=hunter2")
    monkeypatch.setattr(search_repo, "query_all", broken)
    response = get(client, q="vice")
    page = text(response)
    assert response.status_code == 503 and "Back in a moment" in page and "hunter2" not in page and "secret-host" not in page
