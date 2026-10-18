"""Regression: the Explore button on the Garage opening must respond over its whole visible surface.

The defect (owner-reported, live): the pink Explore pill was drawn in full, but the lineup console sat over its lower part with a transparent top
(padding and a fade), so most of the pill never received a press. Programmatic `element.click()` checks passed, because they do not use hit testing.
These tests use REAL pointer events in a real browser (scripts/qa/garage_pointer.mjs): a grid of hit-tests over the pill, real presses on its left edge,
text, centre, arrow and right edge (touch taps on phones), Enter on the focused button, and one real navigation per machine, at laptop, desktop and phone
sizes, for all seven machines. They are skipped where Node or Chrome is not installed."""
import os
import re
import shutil
import subprocess
import threading
from pathlib import Path

import pytest
from werkzeug.serving import make_server

ROOT = Path(__file__).resolve().parent.parent
CHROME_PATHS = [os.environ.get("CHROME_PATH"), "C:/Program Files/Google/Chrome/Application/chrome.exe", "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
                "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe", "/usr/bin/google-chrome", "/usr/bin/chromium",
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]
HAVE_BROWSER = bool(shutil.which("node")) and any(p and Path(p).exists() for p in CHROME_PATHS)


def css(name):
    return (ROOT / "app" / "static" / "css" / name).read_text(encoding="utf-8")


def rule(text, selector):
    match = re.search(r"(?m)^" + re.escape(selector) + r"\s*\{([^}]*)\}", text)
    return match.group(1) if match else ""


def test_the_console_box_takes_no_pointer_events_over_the_stage_and_only_its_controls_do():
    """The cause, stated in CSS: the console's box is taller than what is in it and lies over the Explore button, so it must not catch presses itself."""
    garage = css("garage.css")
    assert "pointer-events: none" in rule(garage, ".cine__console")
    assert "pointer-events: auto" in rule(garage, ".cine__ctl") and "pointer-events: auto" in rule(garage, ".cine__console .rail__item")
    assert int(re.search(r"z-index:\s*(\d+)", rule(garage, ".scene__copy")).group(1)) > int(re.search(r"z-index:\s*(\d+)", rule(garage, ".cine__console")).group(1))


def run_pointer_script(app, page, sizes, expected_links):
    server = make_server("127.0.0.1", 0, app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        env = {**os.environ, "TL_BASE": f"http://127.0.0.1:{server.server_port}", "POINTER_PATH": page, "POINTER_SIZES": sizes}
        result = subprocess.run([shutil.which("node"), "scripts/qa/cdp.mjs", "scripts/qa/garage_pointer.mjs"], cwd=ROOT, env=env, capture_output=True, text=True, timeout=1700)
    finally:
        server.shutdown()
    lines = result.stdout.splitlines()
    failures = [line for line in lines if line.startswith("FAIL")]
    assert result.returncode == 0 and not failures, "\n".join(failures[:12]) or (result.stdout + result.stderr)[-1500:]
    passes = [line for line in lines if line.startswith("PASS")]
    # every machine, every size: the point of the test is that it really ran
    for size in sizes.split(","):
        assert sum(1 for line in passes if line.startswith(f"PASS  {size} ") and "reaches the Explore link" in line) >= expected_links, size


@pytest.mark.skipif(not HAVE_BROWSER, reason="needs Node and Chrome")
def test_explore_button_responds_over_its_whole_surface_for_all_seven_machines(app):
    # per size and machine: left edge, text, centre, arrow, right edge, top edge and bottom edge = 7 real presses
    run_pointer_script(app, "/vehicles", "1440x900,1024x768,390x844", expected_links=7 * 7)


@pytest.mark.skipif(not HAVE_BROWSER, reason="needs Node and Chrome")
def test_explore_button_responds_over_its_whole_surface_on_the_concept_opening_too(app):
    # the same real presses, taps, Enter and one real navigation per machine, on the redesigned opening, at a desktop and a phone size
    run_pointer_script(app, "/garage-concept?autoplay=0", "1440x900,390x844", expected_links=7 * 7)
