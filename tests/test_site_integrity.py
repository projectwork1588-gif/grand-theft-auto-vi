"""Crawl the whole site from the homepage: every internal link must work and every page must be sound HTML."""
import re
from html.parser import HTMLParser

PAIRED = {"div", "section", "ul", "ol", "li", "a", "nav", "main", "header", "footer", "dialog", "button", "dl", "aside",
          "article", "h1", "h2", "h3", "h4", "span", "form", "label", "select", "svg", "dt", "dd", "small", "strong", "title", "head", "body", "html"}


class Checker(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack, self.errors, self.h1, self.imgs_without_alt, self.links, self.ids = [], [], 0, [], [], []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in PAIRED:
            self.stack.append(tag)
        if tag == "h1":
            self.h1 += 1
        if tag == "img" and "alt" not in a:
            self.imgs_without_alt.append(a.get("src"))
        if tag == "a" and "href" in a:
            self.links.append(a["href"])
        if "id" in a:
            self.ids.append(a["id"])

    def handle_endtag(self, tag):
        if tag in PAIRED:
            if not self.stack or self.stack[-1] != tag:
                self.errors.append(f"unexpected </{tag}> (open: {self.stack[-3:]})")
                if tag in self.stack:
                    while self.stack and self.stack.pop() != tag:
                        pass
            else:
                self.stack.pop()


def crawl(client):
    seen, queue, pages = set(), ["/"], {}
    while queue:
        path = queue.pop(0)
        if path in seen:
            continue
        seen.add(path)
        response = client.get(path)
        pages[path] = response
        if response.status_code == 200 and "text/html" in response.content_type:
            checker = Checker()
            checker.feed(response.get_data(as_text=True))
            for href in checker.links:
                clean = href.split("#")[0]
                if clean.startswith("/") and not clean.startswith("//"):
                    queue.append(clean)
    return pages


def test_every_internal_link_resolves(client):
    pages = crawl(client)
    broken = {p: r.status_code for p, r in pages.items() if r.status_code != 200}
    assert broken == {}, broken
    html_pages = [p for p, r in pages.items() if "text/html" in r.content_type]
    # homepage + 5 list pages + 11 characters + 8 vehicles + 6 regions + 8 locations + 5 missions
    assert len(html_pages) >= 44, len(html_pages)
    assert {"/", "/characters", "/vehicles", "/regions", "/music", "/media", "/missions"} <= set(html_pages)


def test_static_assets_referenced_by_pages_exist(client):
    page = client.get("/").get_data(as_text=True)
    for url in re.findall(r'(?:href|src)="(/static/[^"]+)"', page):
        assert client.get(url).status_code == 200, url


def test_every_page_is_well_formed_accessible_html(client):
    pages = crawl(client)
    for path, response in pages.items():
        if "text/html" not in response.content_type:
            continue
        text = response.get_data(as_text=True)
        checker = Checker()
        checker.feed(text)
        assert checker.errors == [], (path, checker.errors[:3])
        assert checker.stack == [], (path, checker.stack)
        assert checker.h1 == 1, (path, "must have exactly one h1")
        assert checker.imgs_without_alt == [], (path, checker.imgs_without_alt)
        assert len(checker.ids) == len(set(checker.ids)), (path, "duplicate ids")
        assert '<html lang="en">' in text and 'name="viewport"' in text and "<title>" in text, path
        assert 'href="#main"' in text and 'id="main"' in text, path           # skip link target
        assert "aria-current" in text or path in ("/", "/about", "/credits") or path.startswith(("/missions", "/locations/")), path     # Stories has no menu entry now, so its pages and the place pages mark none


def test_filter_forms_are_labelled_and_keyboard_usable(client):
    for path in ("/characters", "/missions"):
        page = client.get(path).get_data(as_text=True)
        assert 'role="search"' in page and "aria-label=" in page
        controls = len(re.findall(r"<(?:input|select)\b", page))
        assert controls >= 3 and page.count("<label>") >= controls - 0 or page.count("<label") >= 3, path
        assert 'type="submit"' in page, path  # works without JavaScript


def test_internal_links_keep_working_for_every_listed_entity(client):
    """Each catalogue card must link to a detail page that exists (checked through the real database slugs)."""
    for listing, detail_prefix in (("/api/v1/characters", "/characters/"), ("/api/v1/vehicles?status=official", "/vehicles/"),
                                   ("/api/v1/missions", "/missions/"), ("/api/v1/locations", "/locations/"),
                                   ("/api/v1/regions", "/regions/")):
        sep = "&" if "?" in listing else "?"
        for item in client.get(f"{listing}{sep}per_page=50").get_json()["data"]:
            assert client.get(detail_prefix + item["slug"]).status_code == 200, (detail_prefix, item["slug"])
