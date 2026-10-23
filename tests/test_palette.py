"""The command palette and the header Search icon (Stage 4B, milestone 3), the parts a server-side test can prove: the markup is on every page, the script cannot build
HTML from text, the policy is unchanged, the commands are navigation only, and the size budget holds. Behaviour in a real browser (shortcuts, focus, announcements,
timing) is scripts/qa/palette_qa.mjs. Reads the *_test database only."""
import gzip
import re
from pathlib import Path

import pytest

from tests import account_helpers as h

STATIC = Path(__file__).resolve().parent.parent / "app" / "static"
JS = (STATIC / "js" / "palette.js").read_text(encoding="utf-8")
CSS = (STATIC / "css" / "palette.css").read_text(encoding="utf-8")
POLICY = ("default-src 'self'; img-src 'self' https://www.rockstargames.com data:; media-src 'self'; frame-src https://www.rockstargames.com https://www.youtube-nocookie.com; "
          "style-src 'self'; font-src 'self'; script-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'self'")
PAGES = ["/", "/characters", "/characters/jason-duval", "/vehicles", "/regions", "/music", "/media", "/missions", "/about", "/credits", "/login", "/search", "/search?q=vice",
         "/no-such-page"]


def page(client, path):
    return client.get(path).get_data(as_text=True)


# ------------------------------------------------------------------ the markup, on every page
@pytest.mark.parametrize("path", PAGES)
def test_every_page_has_the_icon_the_dialog_and_the_script_once(client, path):
    html = page(client, path)
    assert html.count('id="palette"') == 1 and html.count('data-palette-open') == 1 and html.count("js/palette.js") == 1 and html.count("css/palette.css") == 1
    assert re.search(r'<a class="header-search" href="/search" aria-label="Search" aria-keyshortcuts="Control\+K Meta\+K" data-palette-open>', html)


def test_the_icon_is_inside_the_header_actions_before_the_trailers_pill(client):
    html = page(client, "/")
    actions = html.split('<div class="header-actions">', 1)[1].split("</div>", 1)[0]
    assert actions.index("header-search") < actions.index("header-pill") < actions.index("menu-btn")


def test_the_dialog_is_labelled_and_the_field_is_a_combobox_over_a_listbox(client):
    html = page(client, "/")
    dialog = html.split('<dialog class="palette"', 1)[1].split("</dialog>", 1)[0]
    assert dialog.startswith(' id="palette" aria-label="Search the site"')                    # the dialog itself is named
    assert 'role="combobox"' in dialog and 'aria-controls="palette-list"' in dialog and 'aria-autocomplete="list"' in dialog and 'aria-expanded="false"' in dialog
    assert 'role="listbox"' in dialog and 'id="palette-list"' in dialog and 'role="status" aria-live="polite"' in dialog
    assert "maxlength=\"80\"" in dialog and 'autocomplete="off"' in dialog
    assert 'data-palette-close>Close</button>' in dialog                       # the visible word is the accessible name (WCAG 2.5.3)


def test_the_menu_has_a_search_row(client):
    assert 'href="/search">Search</a></li>' in page(client, "/").split('id="site-menu"', 1)[1].split("</nav>", 1)[0]


def test_without_javascript_nothing_needs_it_the_icon_links_to_the_search_page(client):
    assert client.get("/search").status_code == 200
    assert 'href="/search"' in page(client, "/characters")


# ------------------------------------------------------------------ the commands are navigation and the motion switch, nothing else
def commands(client, path="/characters"):
    html = page(client, path).split("<template data-palette-commands>", 1)[1].split("</template>", 1)[0]
    return re.findall(r'<li data-name="([^"]+)"(?: data-href="([^"]*)")?(?: data-action="([^"]*)")?></li>', html)


def test_the_signed_out_commands_are_exactly_navigation_the_search_page_sign_in_and_the_motion_switch(client):
    found = commands(client)
    names = [name for name, _href, _action in found]
    assert names == ["Go to Home", "Go to Characters", "Go to Garage", "Go to Leonida", "Go to Music", "Go to Media", "Go to Stories", "Go to About", "Go to Credits",
                     "Open the full search page", "Go to Sign in", "Turn autoplay and motion on or off"]
    assert [a for _n, _h, a in found if a] == ["motion"]


def test_every_command_address_is_a_page_that_exists(client):
    for name, href, action in commands(client):
        if action:
            continue
        assert href.startswith("/") and not href.startswith("//"), name
        assert client.get(href).status_code == 200, (name, href)


@pytest.mark.usefixtures("clean_accounts")
def test_a_signed_in_visitor_is_offered_favourites_not_sign_in_and_never_sign_out(client):
    h.register(client)
    names = [name for name, _h, _a in commands(client)]
    assert "Go to your favourites" in names and "Go to Sign in" not in names
    assert not any(re.search(r"sign out|log out|delete|admin|password", name, re.I) for name in names)
    html = page(client, "/").split('<dialog class="palette"', 1)[1].split("</dialog>", 1)[0]
    assert "<form" not in html and 'method="post"' not in html and "csrf" not in html.lower()      # nothing in the palette can send a state-changing request


# ------------------------------------------------------------------ the script cannot build HTML from text, and keeps to this site
@pytest.mark.parametrize("forbidden", [r"\.innerHTML", r"\.outerHTML", r"insertAdjacentHTML", r"document\.write", r"\beval\s*\(", r"new Function", r"setTimeout\(\s*[\"']", r"setInterval\(\s*[\"']",
                                       r"javascript:", r"\.srcdoc", r"createContextualFragment", r"DOMParser", r"localStorage", r"sessionStorage", r"document\.cookie", r"XMLHttpRequest"])
def test_the_script_never_uses_what_turns_text_into_markup_or_code(forbidden):
    assert not re.search(forbidden, JS), forbidden


def test_the_script_only_talks_to_the_search_api_and_only_follows_local_paths():
    assert re.findall(r"fetch\(([^,)]+)", JS) == ["url"] and 'var API = "/api/v1/search";' in JS
    assert "http://" not in JS and "https://" not in JS
    assert 'charAt(0) === "/" && href.charAt(1) !== "/"' in JS and "isLocalPath(hit.url)" in JS and "isLocalPath(record.href)" in JS
    assert "window.open(record.href, \"_blank\", \"noopener\")" in JS


def test_the_script_builds_everything_with_createElement_and_textContent():
    assert "document.createElement" in JS and "textContent" in JS and "createTextNode" in JS


def test_the_script_and_style_use_no_inline_style_and_no_event_handler_attributes():
    assert ".style." not in JS and "setAttribute(\"style\"" not in JS and "setAttribute(\"on" not in JS


# ------------------------------------------------------------------ policy and budget
def test_the_content_security_policy_is_exactly_what_it_was(client):
    response = client.get("/")
    assert response.headers["Content-Security-Policy"] == POLICY
    assert "unsafe-inline" not in POLICY and "unsafe-eval" not in POLICY


def test_the_palette_costs_under_8_kb_of_script_and_under_4_kb_of_style_once_compressed():
    script, style = len(gzip.compress(JS.encode("utf-8"), 9)), len(gzip.compress(CSS.encode("utf-8"), 9))
    assert script <= 8 * 1024, f"palette.js is {script} bytes gzipped"
    assert style <= 4 * 1024, f"palette.css is {style} bytes gzipped"


def test_the_palette_adds_little_to_a_page(client):
    html = page(client, "/about")
    assert len(html.encode("utf-8")) < 40 * 1024
    dialog = html.split('<dialog class="palette"', 1)[1].split("</dialog>", 1)[0]
    assert len(dialog.encode("utf-8")) < 3 * 1024, "the palette markup must stay small on every page"
