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

## The command palette (milestone 3)

Press **Ctrl+K** (Cmd+K on a Mac), or **/** when you are not typing in a field, or click the Search icon in the header. A native `<dialog>` opens over the page.

**Ways in.** Ctrl/Cmd+K toggles it (the page calls `preventDefault`, because some browsers use Ctrl+K for their own search bar). `/` opens it only when focus is
not in an input, a select, a text area or an editable element, and only when no other dialog (the trailer player, the image viewer) is open. The header icon is a
plain link to `/search` without JavaScript; with JavaScript a click opens the palette (a Ctrl/Cmd/Shift-click still opens `/search` in a new tab). The site menu has a
Search row as well, for the narrowest phones where the icon steps aside (under 360 px).

**What it does.**
* Empty: quick links to the main pages.
* Text: after a 120 ms pause, `GET /api/v1/search?limit=8`; at most eight results, the best one already active, so Enter opens it. Stale requests are cancelled with
  `AbortController`; the last 20 answers are kept in memory.
* `>` switches to **commands**, filtered as you type. The set is an allow-list rendered by the server (`<template data-palette-commands>` in `base.html`, so every
  address comes from `url_for`): Go to Home, Characters, Garage, Leonida, Music, Media, Stories, About, Credits; open the full search page; Go to Sign in (or Go to
  your favourites when signed in); and Turn autoplay and motion on or off, which drives the site's own motion switch. Nothing that changes an account or data is
  offered (no sign out, no forms, no POST), and a test checks that.
* Enter with nothing matching, or "All results", goes to `/search?q=...#results`.

**Keyboard and screen readers.**
* The field is an ARIA combobox (`role="combobox"`, `aria-expanded`, `aria-controls`, `aria-activedescendant`) over a `role="listbox"` of `role="option"` rows, exactly
  one `aria-selected`. Arrow Up/Down move (and wrap), Enter opens (Ctrl/Cmd+Enter in a new tab), Esc closes.
* Focus returns to the control that opened the palette (the header icon, or whatever had focus), or to the header icon if that element is gone. Because the dialog is
  modal the page behind it is inert; Tab stays in the palette or goes up to the browser, as for any modal dialog.
* A polite `role="status"` region announces "8 results. Vice City, Region." or "No results." after each search. The motion command announces "Autoplay and motion are
  now on/off." in a separate page-level live region, because the one inside the dialog is gone once it closes.
* The visible "Close" button's name is its own text (WCAG 2.5.3). Result rows are at least 44 px tall; the active row has a 2 px outline as well as a tint, so it
  survives forced-colours mode.

**Safety.** Every visible string is built with `createElement` and `textContent` (the match highlight splits text into text nodes and `<mark>` elements); the script
never uses `innerHTML`, `eval`, `document.write` or the like (a test scans for each). It talks to one address, `/api/v1/search`, and follows only addresses that are a
path on this site. The Content-Security-Policy is exactly what it was (a test pins it): `script-src 'self'`, `connect-src 'self'`, no inline script or style.

**Motion.** Nothing animates unless the site's own motion switch is on (`html.motion-on`, which reduced motion keeps off): then the dialog fades in over the standard
duration. The caret is the browser's own; nothing blinks by design.

**Design.** Original and built from the tokens: a `>_` prompt in Barlow Condensed in the action colour, Manrope rows, the Official or Concept label from the existing
labels, `mark` in the action colour. On phones (640 px and under) it is a full-screen sheet.

**The header icon changes nothing else.** It hangs in the space between the menu and the Trailers pill; its negative margin cancels its own width. Checked by taking
it in and out of layout on four pages at eleven widths (1920 down to 360): not one other header element moved by even 0.01 px. Full-page snapshots against the
previous stage differ only inside the icon's strip (y 24 to 47) with identical document heights.

**Cost.** `palette.js` is 14.2 KB (4.2 KB gzipped); `palette.css` is 5.6 KB (1.7 KB gzipped); the dialog adds 2.2 KB of markup to every page. The budget set was 8 KB of
script gzipped. The script is loaded with `defer` on every page, not on first use: at 4.2 KB gzipped a lazy loader would cost more in complexity and in first-open
delay than it saves.

**Measured in a real browser** (`scripts/qa/palette_qa.mjs`, headless Chrome, the Flask development server, 1440 x 900): open to the first painted frame 22 ms
median (30 ms worst, budget 100 ms); a keystroke to painted results 145 ms median (157 ms worst), of which 120 ms is the deliberate pause that waits for you to stop
typing; from the server's answer to painted results 8 ms median (20 ms worst, budget 150 ms).

**Tests.** `tests/test_palette.py` (the markup on 14 kinds of page, the commands, the script's safety, the unchanged policy, the size budget) and
`scripts/qa/palette_qa.mjs` (67 browser checks at six sizes from 1440 down to 320 wide: shortcuts, focus and its return, the ARIA, arrows, Enter, commands, hostile
text, no results, the backdrop, reduced motion, no JavaScript, no console or CSP errors).
