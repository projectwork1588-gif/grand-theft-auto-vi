"""The Music page: Rockstar's own radio stations, score and album, as recorded in the database with their sources.

Nothing here is audio. A link leaves the site only if it is https and on a host that Rockstar or the album's own site uses, so a bad database row can never send a visitor
somewhere else; a picture is drawn only from Rockstar's own image address (app.media_urls)."""
import re
from urllib.parse import urlparse

from ..media_urls import is_official_image
from ..repositories import music as repo

# the only hosts a Music link may point at: Rockstar's own site, the album's own site and the link pages Rockstar's Music page uses for the album and the score
LINK_HOSTS = ("www.rockstargames.com", "rockstargames.com", "www.gtavi-thealbum.com", "gtavi-thealbum.lnk.to", "gtavithealbum.lnk.to", "justice.lnk.to")


def safe_link(url):
    """The address if it is an https link to one of the hosts above, otherwise None (the template then shows no link)."""
    if not url or len(url) > 500 or re.search(r'[\s"<>\\]', url):
        return None
    parts = urlparse(url)
    return url if parts.scheme == "https" and parts.hostname in LINK_HOSTS and not parts.username else None


def day(d):
    """A date the way the page says it: 19 October 2026 (no zero, and no platform-specific format code)."""
    return f"{d.day} {d:%B %Y}" if d else None


def safe_image(url):
    return url if is_official_image(url) else None


def page():
    """Everything the Music page draws: the score, the stations with the songs of their previews, the album with its singles."""
    stations = repo.stations()
    previews = {}
    for row in repo.preview_tracks([s["station_id"] for s in stations]):
        previews.setdefault(row["station_id"], []).append({"title": row["title"], "artists": row["artists"]})
    for s in stations:
        s["tracks"] = previews.get(s["station_id"], [])
        s["logo"], s["banner"], s["source"] = safe_image(s["logo_url"]), safe_image(s["background_url"]), safe_link(s["source_url"])
        s["number"] = s["sort_order"]
    releases = repo.releases()
    by_release = {}
    for row in repo.tracks([r["release_id"] for r in releases]):
        by_release.setdefault(row["release_id"], []).append({**row, "link": safe_link(row["listen_url"]), "is_score": bool(row["is_score"])})
    for r in releases:
        r["art"] = safe_image(r["artwork_url"])
        r["primary"], r["secondary"], r["source"] = safe_link(r["primary_url"]), safe_link(r["secondary_url"]), safe_link(r["source_url"])
        r["singles"] = by_release.get(r["release_id"], [])
        r["checked"] = day(r["verified_on"])
    return {
        "stations": stations,
        "score": next((r for r in releases if r["kind"] == "score"), None),
        "album": next((r for r in releases if r["kind"] == "album"), None),
        "checked": day(max((x["verified_on"] for x in stations + releases if x.get("verified_on")), default=None)),
        "empty": not stations and not releases,
    }
