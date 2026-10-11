# Gate 3A: Characters redesign (implementation note)

Direction approved by the owner: Concept A (Editorial Spreads) as the foundation, with the interactive character
navigation and the relationship network from Concept B. The proposal is in `GATE3A_CHARACTERS_PROPOSAL.md`.

## What the visitor gets

**`/characters`**

1. A cinematic opening on the beach artwork (both leads, faces whole).
2. A sticky jump bar with all eight names. It follows the reader (current person marked) and jumps with a click.
3. A secondary **Explore** panel (search, region, sort), closed by default. Submitting it switches the page to a plain
   results list; "Back to the full cast" returns to the editorial page.
4. **The leads**: Jason and Lucia as full spreads, a second picture each, their stated connections, the motion portrait.
5. **Around them**: the six supporting characters, compact and grouped by what the data says ties them together
   (tied to a lead, the Only Raw Records cluster, a single person with no stated connection yet). The groups come from
   `character_relationships`, they are not typed into the template.
6. **The connections Rockstar has stated**: a relationship network drawn from the real rows (five of them). Hover or
   focus lights a person's lines; people with no stated connection are dimmed and say so. Phones get a plain list.

**`/characters/<slug>`**: one design for all eight. Full-bleed hero for the leads, a framed picture for the others;
the story with the motion portrait; connections shown with faces and the sentence Rockstar's page supports; a gallery;
previous and next; the whole cast.

**Motion portraits**: each person's local loop (Rockstar's clip, then the held artwork) plays **once** when it is at
least half on screen, one at a time, then rests. Nothing loops. If motion is off (reduced-motion preference or the
site's own switch) the portrait stays a still with a small Play button. The homepage and Leonida cinematics are
untouched and a portrait never starts while one of them is playing.

## Data and visibility rules

| Rule | Where it lives |
|------|----------------|
| Public pages show **official** characters only | `app/repositories/characters.py` (`_where`, `get_by_slug`, `relationships_for`, `costars_for`) and `app/repositories/regions.py` |
| A status in the page query string is ignored | `services/site.py`, `character_index` |
| An original character's slug is a styled 404 | `get_by_slug(slug)` returns nothing unless `include_original` |
| The API returns official characters by default | `GET /api/v1/characters` |
| The API can return everything for the DBMS demonstration | `?include=original` (documented in `ROUTES.md`); `?status=demo` needs it |
| The five original stories keep their cast | `mission_characters` is untouched. Story and place pages name the people unlinked with an "Original character" badge (`person_item` macro) |
| Nothing is deleted | no `DROP`, `DELETE` or `TRUNCATE` in any migration; counts are asserted in tests |

### New data (migration `005_gate3a_cast.sql`, additive and idempotent)

* `character_regions`: where Rockstar's own text places a person, with the sentence and the source. Three rows:
  Jason Duval and Brian Heder in the Leonida Keys, Boobie Ike in Vice City. It exists so the region filter works for
  official characters, who have no invented home place.
* One relationship: **Dre'Quan Priest to Real Dimez** (`associate`, official). Rockstar's page says he signed Real
  Dimez to Only Raw Records, so it is supported; it is sourced and worded exactly that way. The homepage's "who
  knows whom" strip keeps the four lines you approved.

Until the migration is applied on the development database, the site still works (the region lookups tolerate the
missing table and fall back to home places only); a test builds a Phase 1-shaped database to prove it.

## Things worth knowing

* **Region filter is deliberately small.** Rockstar's page states a region for three of the eight people. Filtering by
  any other region shows an explanatory empty state rather than inventing links. The `regions.description` texts in the
  database say more than the official page does about who "belongs" to a region; that wording is older and was not
  changed here.
* **Original characters remain available** to the DBMS demonstration through `?include=original` and through the SQL
  in `queries.sql` (queries 15 to 18 are new). No public HTML page uses the switch.
* **Framing** uses `data-pos` / `data-pos-m` attributes and CSS rules, not inline styles, because the site's CSP
  forbids inline styles. `tests/test_gate3a_characters.py` checks that every framing in `media_slots.py` has a rule.
* The motion portraits use only the eight local loops already built from Rockstar's clips; no new footage was added.

## Tests

`tests/test_gate3a_characters.py` (new), plus updates to the character, API, region, migration, seed and setup tests.
Full suite: 369 passed. Width sweep: 15 routes at 88 widths from 320 to 1920 px, no overflow and no header problems.
