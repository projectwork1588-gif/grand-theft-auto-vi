"""Stories results anchor (Stage 4A): the filters, the type chips, Reset and the pager all land on the results, which carry an id, a name for screen readers and
a scroll margin that clears the fixed header."""
import re
from pathlib import Path

from app.blueprints.main import page_url


def test_stories_results_have_an_anchor_and_every_filter_control_lands_on_it(client):
    page = client.get("/missions", query_string={"type": "heist"}).get_data(as_text=True)
    assert page.count('id="results"') == 1
    assert 'id="results" class="story-results" aria-label="Story results"' in page
    assert 'action="/missions#results"' in page                                         # the form's own submit lands on the results
    chips = re.findall(r'class="chip" href="(/missions[^"]*)"', page)
    assert chips and all(href.endswith("#results") for href in chips)
    assert 'href="/missions#results">Reset</a>' in page
    assert page.index('role="search"') < page.index('id="results"') < page.index('role="status"')   # the live line is inside the region


def test_the_empty_state_lives_inside_the_results_and_resets_to_them(client):
    page = client.get("/missions", query_string={"q": "zzzzqq"}).get_data(as_text=True)
    assert 'class="empty"' in page and 'href="/missions#results">Reset the filters</a>' in page
    assert page.index('id="results"') < page.index('class="empty"')


def test_page_url_keeps_filters_and_adds_the_anchor_only_when_asked(app):
    with app.test_request_context("/missions?type=heist&q=harbour"):
        assert page_url(2) == "/missions?type=heist&q=harbour&page=2"
        assert page_url(2, "results") == "/missions?type=heist&q=harbour&page=2#results"


def test_pagers_elsewhere_are_unchanged(client):
    page = client.get("/characters").get_data(as_text=True)
    assert "#results" not in page


def test_the_results_clear_the_fixed_header_when_scrolled_to():
    """The site keeps scroll-padding under the fixed header (site.css); the results add a small margin of their own, never the header height a second time."""
    css_dir = Path(__file__).resolve().parent.parent / "app" / "static" / "css"
    assert "scroll-padding-top: calc(var(--header-h) + 8px)" in (css_dir / "site.css").read_text(encoding="utf-8")
    assert re.search(r"\.story-results \{ scroll-margin-top: 16px; \}", (css_dir / "pages.css").read_text(encoding="utf-8"))
