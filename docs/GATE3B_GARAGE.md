# Gate 3B: the Garage ("Machines of Leonida")

The Garage was rebuilt from the audit up. This note records why, what was chosen, and how to run and check it. The code is in
`app/templates/vehicles/`, `app/static/css/garage.css`, `app/static/js/garage.js`, the vehicle section of `app/services/site.py` and the
Garage block at the end of `app/media_slots.py`. Nothing outside the Garage loads the new stylesheet or script.

## 1. Audit: why the old Garage felt weak

* **The opening was a generic banner.** The same `page_hero` every catalogue page uses: a dimmed picture with a title, no way in.
* **The catalogue was five identical rows.** Image left, text right, then image right, text left. Each vehicle got the same weight and
  the same crop (16:10 over a 16:9 picture, chosen by a generic "focus" word), so a long car was cut at the nose or the tail.
* **The controls were chips only.** The back end already supported search, sort and pagination; the page used none of it.
* **The vehicle page was the generic profile.** About, a two-column facts list, a bento gallery, then three related cards.
* **The related cards set the vehicle's name at heading size over a busy picture** ("'67 VAPID DOMINATOR BUGGY" at 65 px, three lines,
  clipped), the complaint that led to this rebuild.
* **Pictures repeated**: the first gallery picture was the hero, so the same screenshot appeared twice on one page.
* **Phones got the desktop layout shrunk**, and every picture loaded at the largest size.

What was kept: the routes, the services and repositories (official vehicles only, bound parameters, sort/page validation), the API
contract, the content-status labels and source links, the media registry, the shared image viewer and the motion policy.

## 2. Direction

Three directions were compared on paper: (a) a magazine grid of equal cards, (b) one scrolling "chapter" per vehicle, (c) a stage with a
lineup, then a planned showroom. (a) is what we had; (b) hides the database and is poor with five vehicles; (c) was chosen.

* **The opening** is one machine at a time, large, with its name, maker, a one-line summary and a single action. A lineup of all
  five sits beneath it (click, tap, arrow keys, Home/End). Nothing advances by itself. Wide screens put the words opposite the vehicle;
  tablets and phones put the picture on top and the words under it, so a long car is never hidden behind its own title.
* **The showroom** is the database: real `GET` search, category, sort and pagination, a result line that says what is shown, a clear
  link, an empty state. The grid is planned (`site.garage_layout`): a feature, a pair, a wide and a narrow, a narrow and a wide, and a
  last card with no partner always spans the row, so there is never a hole. Every card is one link.
* **The vehicle page** is an editorial feature: a full-bleed opening, the database description set large, a plate of only verified
  details, the showcase, the connected world (only if the database records one), and more machines.
* **Accent**: no new colours or fonts. The label gold marks the lit item; the action pink is the one action colour (the Team Valkyrie
  tokens, checked by `tests/test_design_tokens.py`, which now also covers `garage.css`).

## 3. Pictures

All 17 official vehicle screenshots (3840 x 2160, Rockstar's own) were inspected one by one. They are the only vehicle pictures the
project has: Cheetah 4, Dominator Buggy 4, Squalo 4, Stanier 4, Ganado 1. `media_slots.GARAGE_FRAMES` records, for each, what it shows
(used for the alt text and caption: a description of what is visible, never a claim) and where the subject sits for wide and narrow
crops. `GARAGE_PICKS` says which picture opens the page and which is the card. The showcase never repeats the opening picture, and a card
is a different picture from the opening wherever the vehicle has more than one.

The Ganado has one picture. Its page says so ("Rockstar has published one official image of this vehicle so far") instead of inventing a
gallery, and its card and opening use that picture cut differently.

No generated media exists for the Garage: the pictures are remote references to Rockstar's server, as before, so there is nothing new to
build or to keep out of Git.

## 4. Behaviour

* **Choosing a vehicle**: the chosen picture grows into the vehicle's page (cross-document view transitions in Chrome; every other
  browser just loads the page). Off under reduced motion.
* **Motion**: every transition sits under `html.motion-on`; under the system reduced-motion setting the two pictures that change on request
  keep a 0.25 s plain fade (no zoom, no rise). The opening has no auto-advance and no loop anywhere.
* **Pictures** are decoded before their panel is shown, so a change is never a blank frame; the next machine is fetched quietly on
  desktop, the rest on demand; a picture that fails leaves its tinted frame, not a broken-image icon.
* **Without script** the opening shows the first machine, the lineup is five links, the showroom is a form and links, the showcase shows
  its first picture and each thumbnail links to the full picture.

## 5. Database and back end

No schema change, no migration, no new endpoint. `repositories/media.py` gained `counts()` (how many official pictures an entity has);
`services/site.py` builds the view-models; `frame_pos()` gained an optional `face` argument (Characters calls it as before).
The old `.garage-rows` and `.more-grid` rules were removed from `pages.css` (no template uses them).

## 6. Checks

`tests/test_gate3b_garage.py` (the planner, the pictures, the opening, the controls and their SQL behaviour, the pages, the CSS scope),
plus the real-browser scripts in `scripts/qa/`: `garage_interactions.mjs`, `garage_keyboard.mjs`, `garage_resilience.mjs`,
`garage_stage_shots.mjs`, `garage_review_shots.mjs`, `garage_record.mjs`, `capture_pages.mjs`, and the existing `sweep.mjs`.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m flask --app wsgi run
# with the app on 5057 (the preview server), in Git Bash:
MSYS_NO_PATHCONV=1 node scripts/qa/cdp.mjs scripts/qa/garage_interactions.mjs
MSYS_NO_PATHCONV=1 node scripts/qa/cdp.mjs scripts/qa/garage_keyboard.mjs
MSYS_NO_PATHCONV=1 node scripts/qa/cdp.mjs scripts/qa/garage_resilience.mjs
SWEEP_ROUTES=/vehicles,/vehicles/vapid-stanier MSYS_NO_PATHCONV=1 node scripts/qa/cdp.mjs scripts/qa/sweep.mjs
```

## 7. Limits

* Five vehicles and 17 pictures: a filtered showroom can hold one card, and pagination only appears past nine vehicles (it works; it is
  tested with `per_page=2`).
* The official vehicles have no recorded missions or places, so "The connected world" is not shown for any of them yet (it renders, labelled,
  as soon as the database records one; tested).
* Rockstar has published no specifications, so the plate says "Not published by Rockstar" and nothing else is stated.
* The picture-to-page transition is Chrome-only; other browsers load the page normally.
