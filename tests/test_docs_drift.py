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


# ------------------------------------------------------------------ the verification log has ONE final entry, and its numbers belong to their commits
FINAL_HEADING = "### Final verification of the pull-request head `0eab145` (24 October 2026)"


def final_entry(log):
    """The text of the one final entry: from its heading to the next heading of the same or a higher level, or the end of the file."""
    after = log.split(FINAL_HEADING)[1]
    return re.split(r"\n#{1,3} ", after)[0]


def test_there_is_exactly_one_final_entry_in_the_verification_log():
    """Two commits once each recorded 'the final results' for the same head (one local, one on the pull request branch). A second final section, however it is worded, must fail."""
    log = text("docs/VERIFICATION.md")
    finals = re.findall(r"^#{1,6} .*(?:final candidate|final follow-up|final verification|final integration).*$", log, flags=re.IGNORECASE | re.MULTILINE)
    assert finals == [FINAL_HEADING], f"expected one final entry, found: {finals}"
    assert log.count("`0eab145`**") >= 1 and log.count("Final: full suite on") == 1


def test_a_total_is_never_paired_with_the_wrong_commit_in_the_final_entry_or_the_history():
    log = text("docs/VERIFICATION.md")
    final = final_entry(log)
    assert "1,873 passed" in final
    for line in final.splitlines():
        if "1,820 passed" in line:                                  # the earlier total may be mentioned, but only attributed to its own commit and called history
            assert "`a3ccbab`" in line and "historical" in line, f"the earlier run's total appears in the final entry without being attributed to a3ccbab: {line[:90]}"
        if "1,873 passed" in line:
            assert "`a3ccbab`" not in line, f"the final total is paired with the earlier commit: {line[:90]}"
    for line in log.splitlines():
        if "first verification run" in line:
            assert "1,873" not in line and "0eab145" not in line.split("|")[1], f"the earlier run's row carries the final run's figures: {line[:90]}"


def counts_per_commit(cell):
    """Every 'N passed on the `sha` tree' in a cell, as {N: sha}: the generic form of a count pinned to the commit it was measured on."""
    return {count: sha for count, sha in re.findall(r"(\d[\d,]*) passed on the `([0-9a-f]{7})` tree", cell)}


def test_the_focused_counts_name_their_selection_their_commit_and_why_they_differ():
    final = final_entry(text("docs/VERIFICATION.md"))
    row = next(line for line in final.splitlines() if line.startswith("| Focused search, palette and documentation tests"))
    for name in ("test_docs_drift.py", "test_docs_routes_sync.py", "test_docs_schema_sync.py", "test_search_degradation.py", "test_search_page.py", "test_search_api.py", "test_palette.py"):
        assert name in row, f"the focused row does not name {name}: the selection must be exact"
    result = row.split("|")[2]                                      # the result cell: the evidence cell may name the same commit, so only this cell can pin a count to its commit
    assert "**208 passed on the `0eab145` tree.**" in result, "the focused count must be stated for the 0eab145 tree, in the result cell"
    assert "210 on the local commit `5bc6274`" in result and "217 on the reconciliation commit" in result, "the larger counts must each be attributed to their own commit"
    assert "guard tests" in result and "not because the selection changed" in result, "the row must explain why the count grew"
    assert counts_per_commit(result) == {"208": "0eab145"}, "a count is paired with the wrong commit"


def test_the_degradation_count_names_its_commit_and_is_inside_the_full_run():
    final = final_entry(text("docs/VERIFICATION.md"))
    row = next(line for line in final.splitlines() if line.startswith("| Search degradation regression tests"))
    result = row.split("|")[2]
    assert "**53 passed on the `0eab145` tree**" in result, "the degradation count must be stated for the 0eab145 tree, in the result cell"
    assert "test_search_degradation.py" in result and "1,873" in result and counts_per_commit(result) == {"53": "0eab145"}


def test_github_actions_is_never_said_to_have_passed():
    for line in text("docs/VERIFICATION.md").splitlines():
        if "GitHub Actions" in line:
            assert any(marker in line for marker in ("No claim", "not a GitHub Actions", "no workflow", "No workflow", "no GitHub Actions")), f"a line talks about GitHub Actions without disclaiming a run: {line[:100]}"
    assert not (ROOT / ".github").exists(), "a workflow directory now exists: the log's statement about CI must be revisited"


def test_the_production_blockers_stay_in_the_final_entry_and_it_authorises_nothing():
    final = final_entry(text("docs/VERIFICATION.md"))
    assert "#### Production readiness: still blocked" in final and "do **not** authorize deployment" in final
    for needle in ("WSGI server", "TLS with certificate verification", "migration state", "pool capacity", "licensing"):
        assert needle in final, f"the blocker list lost: {needle}"
    assert "No production database, migration, deployment" in final


def test_the_evidence_labels_are_defined_and_used():
    final = final_entry(text("docs/VERIFICATION.md"))
    assert all(f"*{word}*" in final.split("| Point |")[0] for word in ("Confirmed", "Reported", "Not rerun")), "each evidence label must be defined before the table"
    table = final.split("| Point |")[1]
    rows = [line for line in table.splitlines() if line.startswith("| ") and not line.startswith("|--")]          # data rows only: the split already removed the header's first cells
    assert len(rows) == 12 and rows[0].startswith("| **Final: full suite on `0eab145`**"), "every data row, starting with the full suite, must be checked" and "**Not rerun on `0eab145`**" in table
    for row in rows:
        evidence = row.split("|")[3].lower()
        assert any(label in evidence for label in ("confirmed", "reported", "n/a")), f"a row of the final table has no evidence label: {row[:80]}"
    assert sum("confirmed" in row.split("|")[3].lower() for row in rows) >= 4 and sum("reported" in row.split("|")[3].lower() for row in rows) >= 4
