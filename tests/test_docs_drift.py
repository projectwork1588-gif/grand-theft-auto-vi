"""Documentation drift guards (Stage 5). Each test pins a kind of statement that went stale once: a route listed as "planned" after it was built, a count of vehicles that grew, a
status line that called finished work a later phase, a hosting guide that names a setting or route the code does not have. They read text files and the URL map only."""
import re
from pathlib import Path

import pytest

from app import create_app

ROOT = Path(__file__).resolve().parent.parent
DOCS = sorted((ROOT / "docs").glob("*.md")) + [ROOT / "README.md"]


def text(name):
    return (ROOT / name).read_text(encoding="utf-8")


def section(doc, heading):
    match = re.search(rf"^## {re.escape(heading)}[^\n]*\n(.*?)(?=^## |\Z)", doc, flags=re.S | re.M)
    assert match, heading
    return match.group(1)


@pytest.fixture(scope="module")
def rules():
    return {rule.rule for rule in create_app("testing").url_map.iter_rules() if rule.endpoint != "static"}


# ------------------------------------------------------------------ "planned" means not built
def test_nothing_in_the_planned_table_exists_in_the_url_map(rules):
    planned = re.sub(r"\([^)]*\)", "", section(text("docs/ROUTES.md"), "Planned (not built)"))          # "(reuses /regions/<slug>)" points at something built; it is not a plan
    listed = set()
    for token in re.findall(r"`([^`]+)`", planned):
        for part in token.split(","):
            part = re.sub(r"^(GET|POST)\s+", "", part.strip())
            if part.startswith("/"):
                listed.add(part)
    assert listed, "the Planned table should still list something"
    assert listed & rules == set(), f"built routes still listed as planned: {sorted(listed & rules)}"


def test_the_readme_does_not_call_built_features_later_phases():
    status = next(line for line in text("README.md").splitlines() if line.startswith("**Status:"))
    later = status.split("The interactive atlas")[1].split("later phases")[0]               # the sentence that lists what is still to come
    assert "atlas" in status and later.strip()
    for built in ("search", "palette", "admin", "accounts", "favourites"):
        assert built not in later.lower(), f"the README status lists {built!r} as a later phase"
    roadmap = section(text("README.md"), "Roadmap")
    assert re.search(r"^4\. Global search and the command palette \(built\)", roadmap, flags=re.M)
    assert "(this phase)" not in roadmap


# ------------------------------------------------------------------ numbers that grew
HISTORICAL = ("seven", "at the time", "migration 002", "Migration 002", "| 002 |", "001 to 004", "ids 9 to 13", "migrations 001")
RECORD_MARKERS = ("Historical record", "Current state", "COMPLETED", "CURRENT STATE")      # a dated document must say it is dated, in its first lines


def says_it_is_a_record(path):
    head = " ".join(path.read_text(encoding="utf-8").splitlines()[:8])
    return any(marker in head for marker in RECORD_MARKERS)


def test_the_dated_records_that_keep_old_numbers_say_so():
    """The rule behind the exemption above: these documents mention five vehicles and are allowed to, because each opens by saying it is a record."""
    for name in ("CINEMATIC_IMPLEMENTATION.md", "GATE3B_GARAGE.md", "GATE3B_GARAGE_RESUME.md"):
        assert says_it_is_a_record(ROOT / "docs" / name), f"{name} mentions old numbers but does not say it is a historical record"


def test_every_mention_of_five_vehicles_says_it_is_history_or_says_seven():
    """Seven vehicles are official since migration 006. A line may still say five when it is about the first migrations; it must then say so."""
    offenders = []
    for path in DOCS:
        if path.name == "STAGE5_AUDIT.md" or says_it_is_a_record(path):          # the audit quotes the stale line it found; a marked record keeps the numbers of its day
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if re.search(r"\b(the )?five (official )?vehicles\b", line, flags=re.I) and not any(marker in line for marker in HISTORICAL):
                offenders.append(f"{path.name}:{number}: {line.strip()[:90]}")
    assert offenders == []


def test_the_stated_number_of_official_vehicles_is_the_seeds(app, app_context):
    from app.db import query_one
    assert query_one("SELECT COUNT(*) AS n FROM vehicles WHERE content_status = 'official'")["n"] == 7
    readme = text("README.md")
    assert "seven vehicles" in readme and "five vehicles" not in readme


# ------------------------------------------------------------------ the hosting guide only names what the code has
def test_every_setting_the_hosting_guide_names_exists_in_the_configuration():
    guide = text("docs/HOSTING.md")
    settings = set(re.findall(r"`((?:TV|DB|MIGRATE_DB|FLASK|SECRET)_[A-Z_]+|SECRET_KEY)`", guide))
    assert {"FLASK_ENV", "SECRET_KEY", "TV_PUBLIC_ORIGINS", "TV_TRUSTED_PROXIES", "TV_HSTS_MAX_AGE", "DB_HOST", "DB_PASSWORD"} <= settings
    known = text("app/config.py") + text(".env.example")
    missing = sorted(name for name in settings if name not in known and name != "DB_SSL_CA")       # DB_SSL_CA is a proposal, named as one in section 5
    assert missing == [], f"the hosting guide names settings that the code does not read: {missing}"
    assert "DB_SSL_CA" not in known, "DB_SSL_CA became real: update the hosting guide's section 5"


def test_the_routes_the_hosting_guide_relies_on_exist(rules):
    guide = text("docs/HOSTING.md")
    for route in ("/robots.txt", "/health"):
        assert f"`{route}`" in guide and route in rules


def test_the_hosting_guide_claims_nothing_is_deployed():
    guide = text("docs/HOSTING.md")
    assert "Nothing has been deployed" in guide and "no provider has been chosen" in guide


# ------------------------------------------------------------------ the README lists the documents
@pytest.mark.parametrize("name", ["HOSTING", "STAGE5_AUDIT", "SEARCH", "ACCOUNTS", "ADMIN", "MUSIC", "MEDIA_SCREENING", "ROUTES", "ARCHITECTURE", "DATABASE"])
def test_the_readme_links_the_document(name):
    assert (ROOT / "docs" / f"{name}.md").exists() and f"docs/{name}.md" in text("README.md")


def test_the_verification_log_covers_the_stages_after_phase_two():
    log = text("docs/VERIFICATION.md")
    assert "## Stages 3 to 5" in log and "1,749 passed" in log and "104/104" in log
    assert "recorded here when" not in log, "the log still has a placeholder for results that were never filled in"
    assert "1,820 passed" in log and "Stage 5, first verification run: full suite on `a3ccbab`" in log      # the earlier run is kept, and labelled as the earlier run
    assert "Final verification of the pull-request head `0eab145`" in log


def test_each_full_suite_row_carries_its_own_commit_and_count_and_only_one_is_final():
    """A count must never drift onto the wrong commit: every row that names a commit's full suite states that commit's own total, and exactly one row is the final one."""
    log = text("docs/VERIFICATION.md")
    rows = [line for line in log.splitlines() if re.search(r"full suite on `[0-9a-f]{7}`", line)]
    expected = {"a3ccbab": "1,820 passed", "0eab145": "1,873 passed"}
    assert {re.search(r"full suite on `([0-9a-f]{7})`", row).group(1) for row in rows} == set(expected), "a full-suite row names a commit this test does not know: add its total here"
    for row in rows:
        sha = re.search(r"full suite on `([0-9a-f]{7})`", row).group(1)
        others = [count for other, count in expected.items() if other != sha]
        assert expected[sha] in row and not any(count in row for count in others), f"the row for {sha} carries another commit's total"
    assert log.count("**Final: full suite on `0eab145`**") == 1 and log.count("Final: full suite on") == 1


def test_the_final_entry_says_what_was_not_rerun_and_claims_no_ci_run():
    log = text("docs/VERIFICATION.md")
    assert "**Not rerun on `0eab145`**" in log and "Confirmed for `b73e147`" in log and "**not** for `0eab145`" in log
    assert "GitHub Actions" in log and "No claim is made" in log
    assert "32 warnings" in log and "ResourceWarning: unclosed file" in log             # the warnings are kept in the record, and named for what they are
    final = log.split("### Final verification of the pull-request head `0eab145`")[1]
    assert "**Where each figure comes from.**" in final and all(word in final for word in ("Confirmed", "Reported", "Not rerun"))
