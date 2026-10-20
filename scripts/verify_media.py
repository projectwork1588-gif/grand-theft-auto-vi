"""Check the Media page's data against Rockstar's own Media pages, live. READ-ONLY: it requests Rockstar's pages and the pictures and zips the database points at (HEAD only), reads
the database with SELECT, and changes nothing anywhere.

    python -m scripts.verify_media            # development database
    python -m scripts.verify_media --test     # the *_test database
    python -m scripts.verify_media --offline  # skip the requests for each picture (faster)

Pictures are Rockstar's own files, linked and never copied, and their file names carry a build hash that Rockstar can change. This is how to find out: every collection's count, order and
titles are compared with the page it was copied from, every picture address is compared with the one Rockstar serves now, and every stored address and zip is requested. Exit status 1 on any
difference. Run it before relying on the Media page after a long time, and after Rockstar's site changes."""
import argparse
import html
import re
import sys
import urllib.request

BASE = "https://www.rockstargames.com/VI/media"
PAGES = {"screenshots": BASE + "/screenshots", "videos": BASE + "/videos", "artwork-wallpapers": BASE + "/artwork-wallpapers"}
UA = {"User-Agent": "Mozilla/5.0 (Team Valkyrie media check)"}
BS = chr(92)
ITEM = re.compile(r'\{"title":"([^"]+)","thumbnail":\{"src":"([^"]+)","width":(\d+),"height":(\d+)[^}]*\},"variant":"(\w+)","media":\[(.*?)\],"id":"([a-z0-9_]+)"')


def decode(page):
    """Rockstar's pages carry their data as escaped JSON inside the page: unescape it into plain text."""
    text = page.replace(BS + '"', '"').replace(BS + "/", "/").replace(BS + "u0026", "&")
    text = re.sub(re.escape(BS + "u") + "([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), text)
    return re.sub(r'"blurDataURL":"[^"]*"', '"<blur>"', text)


def parse_items(page):
    """Every item on one of Rockstar's media pages: [{title, src, id}], in the order Rockstar lists them, each listed once."""
    seen, items = set(), []
    for m in ITEM.finditer(decode(page)):
        if m.group(7) not in seen:
            seen.add(m.group(7))
            items.append({"title": html.unescape(m.group(1)), "src": m.group(2), "id": m.group(7)})
    return items


def collection_of(item_id):
    """screenshots, ultimate or vintage: Rockstar's own card ids say which collection a screenshot belongs to."""
    return {"screenshots": "screenshots", "ultimate": "ultimate-edition-benefits", "vintage": "vintage-vice-city-pack"}.get(item_id.split("_")[2])


def stem(url):
    return re.sub(r"\.[0-9a-z_~.-]+\.(jpg|png|webp|mp4)$", "", url.split("?")[0].rsplit("/", 1)[-1])


def fetch(url, head=False):
    request = urllib.request.Request(url, method="HEAD" if head else "GET", headers=UA)
    with urllib.request.urlopen(request, timeout=60) as response:
        return response if head else response.read().decode("utf-8", "replace")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--test", action="store_true", help="use the pytest database")
    parser.add_argument("--offline", action="store_true", help="do not request each picture and zip")
    args = parser.parse_args(argv)

    from app import create_app
    from app.db import query_all
    from app.repositories import media as repo
    app = create_app("testing" if args.test else "development")
    problems = []

    def check(ok, label, detail=""):
        print(("PASS  " if ok else "DIFF  ") + label + (f"  ({detail})" if detail else ""))
        if not ok:
            problems.append(label)

    live = {}
    for name, url in PAGES.items():
        live[name] = parse_items(fetch(url))
    expected = {"screenshots": [], "ultimate-edition-benefits": [], "vintage-vice-city-pack": []}
    for item in live["screenshots"]:
        expected[collection_of(item["id"])].append(item)
    expected["artwork-wallpapers"] = live["artwork-wallpapers"]
    videos = live["videos"]
    with app.app_context():
        collections = {c["slug"]: c for c in repo.collections()}
        if not collections:
            print("The media tables are empty or missing: apply migration 009 first.")
            return 1
        for slug, items in expected.items():
            rows = repo.collection_items(slug)
            check(len(rows) == len(items), f"{slug}: {len(rows)} stored, {len(items)} on Rockstar's page")
            check([r["title"] for r in rows] == [i["title"] for i in items], f"{slug}: titles and order match Rockstar's page")
            check([stem(r["embed_url"]) for r in rows] == [stem(i["src"]) for i in items], f"{slug}: picture files match what Rockstar serves now")
            current = {stem(i["src"]): i["src"] for i in items}
            stale = [r["title"] for r in rows if stem(r["embed_url"]) in current and r["embed_url"].rsplit("/", 1)[-1] != current[stem(r["embed_url"])].rsplit("/", 1)[-1]]
            check(not stale, f"{slug}: no picture has a changed file name", ", ".join(stale[:3]))
        stored = repo.collection_items("videos") + repo.collection_items("clips")
        titles = [r["title"] for r in stored]
        check(sorted(titles) == sorted(v["title"] for v in videos), f"videos and clips: {len(stored)} stored, {len(videos)} on Rockstar's page")
        if not args.offline:
            urls = [r["embed_url"] for slug in expected for r in repo.collection_items(slug)] + [r["poster_url"] for r in repo.collection_items("videos")]
            bad = []
            for url in urls:
                try:
                    ok = fetch(url + ("?akim=1&imdensity=1&imwidth=360" if "/_next/" in url else ""), head=True).status == 200
                except Exception:
                    ok = False
                if not ok:
                    bad.append(url.rsplit("/", 1)[-1])
            check(not bad, f"every stored picture address answers ({len(urls)} requested)", ", ".join(bad[:3]))
            for c in collections.values():
                if c["download_url"]:
                    size = int(fetch(c["download_url"], head=True).headers.get("Content-Length", -1))
                    check(size == c["download_bytes"], f"{c['slug']}: zip is {size} bytes, {c['download_bytes']} stored")
        check(bool(query_all("SELECT 1 FROM media_collection_items LIMIT 1")), "the collection items table holds rows")
    print("\n" + (f"{len(problems)} difference(s): update the data (a new migration) before relying on the page." if problems else "Everything matches Rockstar's pages."))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
