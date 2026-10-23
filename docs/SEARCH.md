# Search (Stage 4B)

Site search has three parts, built in this order: the backend and JSON API (milestone 1), the `/search` page (milestone 2) and the command palette (milestone 3). This
document grows with each. It describes what is built and measured, not what is planned.

## Backend and API (milestone 1)

**Layers.** `app/blueprints/api.py` (route) -> `app/services/search.py` (rules, ranking, links) -> `app/repositories/search.py` (all SQL). No migration and no schema
change: search reads the existing tables.

**What is searched, and who may see it.** The rule is the pages' own: a record is found only if it has a public page.

| Kind | Source | Matched columns | Visibility |
|------|--------|-----------------|------------|
| `character` | `characters` | name, alias, role, summary | official only (the three original characters have no page) |
| `vehicle` | `vehicles` | name, manufacturer, summary | official only (the eight concept vehicles have no page) |
| `region` | `regions` | name, summary | all |
| `place` | `locations` (+ its region's name) | name, summary, region | all; shown as **Concept** |
| `story` | `missions` | title, summary, type | all; shown as **Concept** |
| `music` | `radio_stations`, `music_releases`, `music_tracks` | name, hosts, description, title, byline, artists | all; links to the section of `/music` |
| `page` | a short list in the service | title, a line, a few extra words | the site's own pages |

**The query.** `q` is trimmed, control characters become spaces, runs of white space collapse. At most 80 characters and five words, otherwise a 400 that names the
problem. Every word must match somewhere in a record (AND), each as a `LIKE '%word%' ESCAPE '!'` pattern with `%`, `_` and `!` escaped, so `50%` means a literal
percent sign. Case and accents do not matter (the database collation, and the same folding for the page list).

**Ranking.** By the whole phrase against the title: exact (100), starts with (80), a word starts with (60), contains (40), matched elsewhere only (20). Ties: the site's
own pages first, then character, vehicle, region, place, story, music, then title. Up to 200 results are reachable.

**One statement.** All kinds are searched by one `UNION ALL` wrapped in an `ORDER BY ... LIMIT`, so a search is one database round trip (a test counts the calls).

**Safety.**
* Every value is a bound parameter. The SQL text is built only from constants in the repository file and a count of `%s` marks; a test captures the statement and
  checks that the query text appears only in the parameters and that placeholders and parameters match one to one. Another test checks, from the source, that the
  repository functions never see the raw query.
* Hostile strings (quotes, `UNION SELECT`, backslashes, wildcards, control characters, full-width and emoji text, 80 characters) return a normal answer or a 400, and
  the row counts are unchanged afterwards.
* A database failure is the generic 503 (no SQL, host or password), as everywhere else.
* The route is read-only and public.

**Cost** (test database, through the Flask test client, warm, 1,950 requests over 13 queries): p50 5.3 ms, p95 5.9 ms, p99 6.9 ms; the largest response is 2.0 KB.
The budget the plan set was p95 <= 50 ms and 6 KB; `tests/test_search_api.py` enforces it with those limits.

**Tests.** `tests/test_search_api.py`.

## The `/search` page (milestone 2)

`GET /search` renders `templates/search/index.html` with `services/search.page_search`, which uses the same repository and rules as the API and adds a count for
each kind (a second `GROUP BY` statement over the same union) and paging. It is server-rendered and needs no JavaScript.

* **States.** No `q`: the help state, which does no database work (a test forbids it). A query with matches: a status line ("1-12 of 34 for "vice""), the ranked
  rows and a pager. A query without matches: "Nothing found" with a way to start again.
* **Parameters.** `q`, `type`, `page`, `per_page` (1 to 50, default 12). At most 200 results can be paged to. Invalid input is the site's branded 400 page, which
  lists the problem.
* **Rows.** Kind, title, a detail line (a role, a manufacturer, "District in Vice City"), a short summary, and the Official or Concept label from the existing badge.
  The site's own pages carry no label. Every address comes from `url_for`, never from stored text.
* **Anchor and announcement.** The form, the type chips and the pager all land on the labelled `#results` region (the Stories pattern from Stage 4A); the status
  line is `role="status"`, so a screen reader hears the count after a search.
* **Escaping.** Every value is autoescaped by Jinja. Tests reflect hostile queries and hostile database values and check nothing is rendered raw; there is no
  inline script, style or handler (CSP unchanged).
* **Indexing.** `noindex`: result pages are not for search engines.

**Tests.** `tests/test_search_page.py`.
