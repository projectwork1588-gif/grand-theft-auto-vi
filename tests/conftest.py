"""Shared fixtures. Tests run against a REAL MySQL database named *_test (never the dev data)."""
import json

import mysql.connector
import pytest

from app import create_app
from app.config import TestingConfig
from scripts.init_db import init_database


CLIP_SLUGS = ("jason-duval", "lucia-caminos", "cal-hampton", "boobie-ike",
              "dre-quan-priest", "real-dimez", "raul-bautista", "brian-heder")


@pytest.fixture(scope="session")
def app(tmp_path_factory):
    assert TestingConfig.DB_NAME.endswith("_test"), "tests must never run against the real database"
    init_database(TestingConfig, seed=True, reset=True)  # migration account; fresh, deterministic schema + seed
    application = create_app("testing")
    # Tests never depend on clips someone happened to build locally: the default is an empty media folder.
    application.config["MEDIA_ROOT"] = str(tmp_path_factory.mktemp("no-media"))
    return application


@pytest.fixture()
def local_clips(app, tmp_path):
    """A media folder with tiny stand-in loops, a reel and its manifest, for the pages that show local video."""
    clips = tmp_path / "clips"
    clips.mkdir()
    segments, cursor = [], 0.0
    for slug in CLIP_SLUGS:
        (clips / f"{slug}.mp4").write_bytes(b"ftypmp42")
        (clips / f"{slug}.jpg").write_bytes(b"JFIF")
        segments.append({"slug": slug, "name": slug, "start": round(cursor, 2), "end": round(cursor + 2.9, 2)})
        cursor += 2.9
    (clips / "leonida-reel.mp4").write_bytes(b"ftypmp42")
    (clips / "leonida-reel.jpg").write_bytes(b"JFIF")
    (clips / "manifest.json").write_text(json.dumps({"duration": round(cursor + 0.5, 2), "speed": 1.0, "art_hold": 1.6, "dissolve": 0.3, "segments": segments}), encoding="utf-8")
    previous = app.config["MEDIA_ROOT"]
    app.config["MEDIA_ROOT"] = str(tmp_path)
    yield tmp_path
    app.config["MEDIA_ROOT"] = previous


@pytest.fixture()
def local_portraits(app, tmp_path):
    """local_clips plus the character portraits built by `make_loops --portraits` (<slug>-portrait.mp4 and .jpg)."""
    clips = tmp_path / "clips"
    clips.mkdir()
    segments, cursor = [], 0.0
    for slug in CLIP_SLUGS:
        for name in (f"{slug}.mp4", f"{slug}-portrait.mp4"):
            (clips / name).write_bytes(b"ftypmp42")
        for name in (f"{slug}.jpg", f"{slug}-portrait.jpg"):
            (clips / name).write_bytes(b"JFIF")
        segments.append({"slug": slug, "name": slug, "start": round(cursor, 2), "end": round(cursor + 2.9, 2)})
        cursor += 2.9
    (clips / "leonida-reel.mp4").write_bytes(b"ftypmp42")
    (clips / "leonida-reel.jpg").write_bytes(b"JFIF")
    (clips / "manifest.json").write_text(json.dumps({"duration": round(cursor + 0.5, 2), "speed": 1.0, "art_hold": 1.6, "dissolve": 0.3, "segments": segments}), encoding="utf-8")
    previous = app.config["MEDIA_ROOT"]
    app.config["MEDIA_ROOT"] = str(tmp_path)
    yield tmp_path
    app.config["MEDIA_ROOT"] = previous


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def app_context(app):
    with app.app_context():
        yield


@pytest.fixture()
def conn():
    """Raw connection for integrity tests. Everything is rolled back, so the seed stays intact."""
    connection = mysql.connector.connect(**TestingConfig.db_kwargs())
    connection.autocommit = False
    yield connection
    connection.rollback()
    connection.close()


@pytest.fixture()
def cur(conn):
    cursor = conn.cursor(dictionary=True)
    yield cursor
    cursor.close()
