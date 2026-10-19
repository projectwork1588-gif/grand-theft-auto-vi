"""All SQL for the Music page: the radio stations, the score and the album Rockstar shows on its own Music page."""
import logging

from mysql.connector import errors

from ..db import query_all

log = logging.getLogger(__name__)


def _guarded(sql, params=()):
    """Run a read; a database that has not had migration 008 applied yet has no music tables, which is an empty page rather than an error."""
    try:
        return query_all(sql, params)
    except errors.ProgrammingError as exc:
        if exc.errno != 1146:      # table missing
            raise
        log.warning("Music tables are missing (%s). Has migration 008 been applied?", exc)
        return []


def stations(status="official"):
    return _guarded(
        """SELECT station_id, slug, name, hosts, description, logo_url, background_url, sort_order,
                  content_status, source_url, source_note, verified_on
           FROM radio_stations WHERE content_status = %s ORDER BY sort_order""",
        (status,))


def preview_tracks(station_ids):
    ids = [int(i) for i in station_ids]
    if not ids:
        return []
    marks = ", ".join(["%s"] * len(ids))
    return _guarded(
        f"SELECT station_id, sort_order, title, artists FROM station_preview_tracks WHERE station_id IN ({marks}) ORDER BY station_id, sort_order", ids)


def releases(status="official"):
    return _guarded(
        """SELECT release_id, slug, kind, title, byline, description, release_note, track_count, label, artwork_url,
                  primary_url, primary_label, secondary_url, secondary_label, content_status, source_url, source_note, verified_on
           FROM music_releases WHERE content_status = %s ORDER BY release_id""",
        (status,))


def tracks(release_ids):
    ids = [int(i) for i in release_ids]
    if not ids:
        return []
    marks = ", ".join(["%s"] * len(ids))
    return _guarded(
        f"SELECT release_id, sort_order, title, artists, listen_url, is_score FROM music_tracks WHERE release_id IN ({marks}) ORDER BY release_id, sort_order", ids)
