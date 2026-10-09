# Media inventory

**Policy.** Nothing from Rockstar is downloaded or committed. Official images and videos are **remote references to Rockstar's own published media**, shown with attribution and a link back to the source page. Watermarks and copyright notices are never removed. Fictional demo records (vehicles, locations, missions, three characters) never receive official images. All visuals the project itself owns are original (the vehicle silhouettes in `app/static/img/vehicles.svg`, the CSS fallbacks).

The database table `media_assets` holds exactly the rows below, with `media_characters` and `media_regions` linking them to characters and regions. The table is generated from one manifest, so this page and the database cannot drift apart. A test (`test_seed_and_migration_agree`) proves a fresh seed and an upgraded database match.

## Where the media came from (checked 2026-10-09)

| Source page | What it offers |
|-------------|----------------|
| https://www.rockstargames.com/VI/media/artwork-wallpapers | 23 artwork and wallpaper items (character portraits, Jason and Lucia art, region postcards) |
| https://www.rockstargames.com/VI/media/screenshots | 162 official screenshots (per character and per region, plus edition content) |
| https://www.rockstargames.com/VI/trailer-1, /trailer-2, /an-extended-look | Official videos, each embedding Rockstar's own player (`/videoplayer?id=...&embed`) |

All 57 referenced URLs were requested before they were recorded and returned HTTP 200 with the expected content type. The player pages send no framing restriction (they are built to be embedded). Images load with a foreign referrer and Rockstar's image service accepts a width parameter, which the site uses to request 640, 1280 and 1920 pixel versions.

## Integration approach

* **Videos:** a poster card on the homepage opens a native `<dialog>`. Only then does JavaScript create the iframe pointing at Rockstar's player, so nothing loads until a visitor presses play. Closing the dialog removes the iframe, which stops playback.
* **Images:** ordinary `<img>` elements with `srcset`, `loading="lazy"` (the hero image uses `fetchpriority="high"`) and `referrerpolicy="no-referrer"`, over an original fallback layer. If an image fails, the fallback shows.
* **Safety:** templates only render a URL that starts with Rockstar's exact image prefix or player prefix (`app/media_urls.py`). The Content-Security-Policy allows images and frames only from `www.rockstargames.com`. A hostile database value is ignored (tested).
* **Reduced motion:** visitors who ask for reduced motion get a still first hero image and no slideshow.

## Status and risks

| Item | Status |
|------|--------|
| Rockstar states **no licence terms** on its Media page, only an invitation to download and share | **Human review recommended.** The Phase 2 media brief authorised use of official sources, and nothing is copied, but the owner should confirm this is acceptable. |
| Image file names are **build-hashed** (for example `Cal_Hampton_landscape.17k7bnt3myg.2.jpg`) | They may change when Rockstar redeploys. The site then falls back to original artwork. Re-run the URL check and update `database/migrations/` to refresh. |
| Official vehicle imagery | **Not used.** Rockstar's pre-order screenshots name real vehicles, but the schema has no media-to-vehicle link, and attaching them to fictional demo vehicles would mislead. A `media_vehicles` junction is a Phase 3 or 5 decision. |
| Trailer thumbnails | Rockstar publishes none we can reference, so posters use official screenshots instead. |
| Music, wallpaper downloads (zip files) | **Not used or downloaded.** The site links to Rockstar's own download page. |

## Inventory (57 rows)

| ID | Slug | Type | Source page | Remote reference | Linked to | Usage | Approval |
|----|------|------|-------------|------------------|-----------|-------|----------|
| 1 | `official-trailer-1` | trailer | /VI/trailer-1 | `videoplayer?id=rkoCtr1r&embed` | Jason Duval, Lucia Caminos | embed_permitted | approved |
| 2 | `official-trailer-2` | trailer | /VI/trailer-2 | `videoplayer?id=cpys7u21&embed` | Jason Duval, Lucia Caminos | embed_permitted | approved |
| 3 | `official-media-artwork-hub` | wallpaper | /VI/media | `(link only)` | none | link_only | approved |
| 4 | `official-an-extended-look` | video | /VI/an-extended-look | `videoplayer?id=rk721912&embed` | none | embed_permitted | approved |
| 5 | `art-jason-lucia-beach` | artwork | /VI/media/artwork-wallpapers | `…/media/Jason_and_Lucia_Beach_landscape.0419q._86ukpt.jpg` | Jason Duval, Lucia Caminos | embed_permitted | approved |
| 6 | `art-jason-lucia-01` | artwork | /VI/media/artwork-wallpapers | `…/media/Jason_and_Lucia_01_landscape.12x2gvspcm_3m.jpg` | Jason Duval, Lucia Caminos | embed_permitted | approved |
| 7 | `art-jason-lucia-02` | artwork | /VI/media/artwork-wallpapers | `…/media/Jason_and_Lucia_02_landscape.0cosv-uzbpt91.jpg` | Jason Duval, Lucia Caminos | embed_permitted | approved |
| 8 | `art-jason-lucia-robbery` | artwork | /VI/media/artwork-wallpapers | `…/media/Jason_and_Lucia_Robbery_landscape.09c8a~do21h4p.jpg` | Jason Duval, Lucia Caminos | embed_permitted | approved |
| 9 | `art-jason-lucia-motel` | artwork | /VI/media/artwork-wallpapers | `…/media/Jason_and_Lucia_Motel_landscape.08edvuwtm-20v.jpg` | Jason Duval, Lucia Caminos | embed_permitted | approved |
| 10 | `art-cal-hampton` | artwork | /VI/media/artwork-wallpapers | `…/media/Cal_Hampton_landscape.17k7bnt3myg.2.jpg` | Cal Hampton | embed_permitted | approved |
| 11 | `art-boobie-ike` | artwork | /VI/media/artwork-wallpapers | `…/media/Boobie_Ike_landscape.0ldnbn87k-8mq.jpg` | Boobie Ike | embed_permitted | approved |
| 12 | `art-dequan-priest` | artwork | /VI/media/artwork-wallpapers | `…/media/DreQuan_Priest_landscape.0_b7hszyze6cy.jpg` | Dre'Quan Priest | embed_permitted | approved |
| 13 | `art-real-dimez` | artwork | /VI/media/artwork-wallpapers | `…/media/Real_Dimez_landscape.0637akp_a5a_q.jpg` | Real Dimez | embed_permitted | approved |
| 14 | `art-raul-bautista` | artwork | /VI/media/artwork-wallpapers | `…/media/Raul_Bautista_landscape.11_3hd0fr69~j.jpg` | Raul Bautista | embed_permitted | approved |
| 15 | `art-brian-heder` | artwork | /VI/media/artwork-wallpapers | `…/media/Brian_Heder_landscape.0a-egj5b8yo1q.jpg` | Brian Heder | embed_permitted | approved |
| 16 | `postcard-vice-city` | artwork | /VI/media/artwork-wallpapers | `…/media/Vice_City_Postcard_landscape.0v2njmlk2n-qm.jpg` | Vice City | embed_permitted | approved |
| 17 | `postcard-leonida-keys` | artwork | /VI/media/artwork-wallpapers | `…/media/Leonida_Keys_Postcard_landscape.05oezf2h--~ed.jpg` | Leonida Keys | embed_permitted | approved |
| 18 | `postcard-grassrivers` | artwork | /VI/media/artwork-wallpapers | `…/media/Grassrivers_Postcard_landscape.15-10i39nhex2.jpg` | Grassrivers | embed_permitted | approved |
| 19 | `postcard-port-gellhorn` | artwork | /VI/media/artwork-wallpapers | `…/media/Port_Gellhorn_Postcard_landscape.176c2o75nmcr8.jpg` | Port Gellhorn | embed_permitted | approved |
| 20 | `postcard-ambrosia` | artwork | /VI/media/artwork-wallpapers | `…/media/Ambrosia_Postcard_landscape.0gd~9a41ia-rt.jpg` | Ambrosia | embed_permitted | approved |
| 21 | `postcard-mount-kalaga` | artwork | /VI/media/artwork-wallpapers | `…/media/Mount_Kalaga_National_Park_Postcard_landscape.0c1cb4ocq16n3.jpg` | Mount Kalaga | embed_permitted | approved |
| 22 | `shot-jason-duval-01` | screenshot | /VI/media/screenshots | `…/media/Jason_Duval_01.07m377xeb6jhq.jpg` | Jason Duval | embed_permitted | approved |
| 23 | `shot-jason-duval-02` | screenshot | /VI/media/screenshots | `…/media/Jason_Duval_02.1486~7_v40cn..jpg` | Jason Duval | embed_permitted | approved |
| 24 | `shot-jason-duval-03` | screenshot | /VI/media/screenshots | `…/media/Jason_Duval_03.0-1vum7x-3vtp.jpg` | Jason Duval | embed_permitted | approved |
| 25 | `shot-lucia-caminos-01` | screenshot | /VI/media/screenshots | `…/media/Lucia_Caminos_01.0a7yqvewctkfp.jpg` | Lucia Caminos | embed_permitted | approved |
| 26 | `shot-lucia-caminos-02` | screenshot | /VI/media/screenshots | `…/media/Lucia_Caminos_02.16n.5umvlu_48.jpg` | Lucia Caminos | embed_permitted | approved |
| 27 | `shot-lucia-caminos-03` | screenshot | /VI/media/screenshots | `…/media/Lucia_Caminos_03.14xgd2y_ymmeg.jpg` | Lucia Caminos | embed_permitted | approved |
| 28 | `shot-jason-and-lucia-01` | screenshot | /VI/media/screenshots | `…/media/Jason_and_Lucia_01.0naeahss9-1x6.jpg` | Jason Duval, Lucia Caminos | embed_permitted | approved |
| 29 | `shot-jason-and-lucia-02` | screenshot | /VI/media/screenshots | `…/media/Jason_and_Lucia_02.0uig00eojlokf.jpg` | Jason Duval, Lucia Caminos | embed_permitted | approved |
| 30 | `shot-jason-and-lucia-03` | screenshot | /VI/media/screenshots | `…/media/Jason_and_Lucia_03.15z-.c0tptrzs.jpg` | Jason Duval, Lucia Caminos | embed_permitted | approved |
| 31 | `shot-jason-and-lucia-04` | screenshot | /VI/media/screenshots | `…/media/Jason_and_Lucia_04.0m7i~huzhskdw.jpg` | Jason Duval, Lucia Caminos | embed_permitted | approved |
| 32 | `shot-cal-hampton-01` | screenshot | /VI/media/screenshots | `…/media/Cal_Hampton_01.0xlil231_osh4.jpg` | Cal Hampton | embed_permitted | approved |
| 33 | `shot-cal-hampton-02` | screenshot | /VI/media/screenshots | `…/media/Cal_Hampton_02.05r2t_mck65fe.jpg` | Cal Hampton | embed_permitted | approved |
| 34 | `shot-boobie-ike-01` | screenshot | /VI/media/screenshots | `…/media/Boobie_Ike_01.0-wji2pg5anfs.jpg` | Boobie Ike | embed_permitted | approved |
| 35 | `shot-boobie-ike-02` | screenshot | /VI/media/screenshots | `…/media/Boobie_Ike_02.0sp9mtc.1cdzs.jpg` | Boobie Ike | embed_permitted | approved |
| 36 | `shot-dequan-priest-01` | screenshot | /VI/media/screenshots | `…/media/DreQuan_Priest_01.0_0~wi-ipdj35.jpg` | Dre'Quan Priest | embed_permitted | approved |
| 37 | `shot-dequan-priest-02` | screenshot | /VI/media/screenshots | `…/media/DreQuan_Priest_02.02u69e~nkk3eo.jpg` | Dre'Quan Priest | embed_permitted | approved |
| 38 | `shot-real-dimez-01` | screenshot | /VI/media/screenshots | `…/media/Real_Dimez_01.0djwwboo8-glx.jpg` | Real Dimez | embed_permitted | approved |
| 39 | `shot-real-dimez-02` | screenshot | /VI/media/screenshots | `…/media/Real_Dimez_02.1366u9.x.yp0_.jpg` | Real Dimez | embed_permitted | approved |
| 40 | `shot-raul-bautista-01` | screenshot | /VI/media/screenshots | `…/media/Raul_Bautista_01.0md1ii-yrn96r.jpg` | Raul Bautista | embed_permitted | approved |
| 41 | `shot-raul-bautista-02` | screenshot | /VI/media/screenshots | `…/media/Raul_Bautista_02.10ddy6ogywu-t.jpg` | Raul Bautista | embed_permitted | approved |
| 42 | `shot-brian-heder-01` | screenshot | /VI/media/screenshots | `…/media/Brian_Heder_01.0r.ute88os9k-.jpg` | Brian Heder | embed_permitted | approved |
| 43 | `shot-brian-heder-02` | screenshot | /VI/media/screenshots | `…/media/Brian_Heder_02.0kmg6iw38f-9o.jpg` | Brian Heder | embed_permitted | approved |
| 44 | `shot-vice-city-01` | screenshot | /VI/media/screenshots | `…/media/Vice_City_01.135x56yoeu.6t.jpg` | Vice City | embed_permitted | approved |
| 45 | `shot-vice-city-02` | screenshot | /VI/media/screenshots | `…/media/Vice_City_02.0c5.7qx17u9kl.jpg` | Vice City | embed_permitted | approved |
| 46 | `shot-vice-city-03` | screenshot | /VI/media/screenshots | `…/media/Vice_City_03.0nqz~lrqdmlze.jpg` | Vice City | embed_permitted | approved |
| 47 | `shot-vice-city-04` | screenshot | /VI/media/screenshots | `…/media/Vice_City_04.06evqutgh7624.jpg` | Vice City | embed_permitted | approved |
| 48 | `shot-leonida-keys-01` | screenshot | /VI/media/screenshots | `…/media/Leonida_Keys_01.0zgz7tveur6y8.jpg` | Leonida Keys | embed_permitted | approved |
| 49 | `shot-leonida-keys-02` | screenshot | /VI/media/screenshots | `…/media/Leonida_Keys_02.0~ptk-53gl0lq.jpg` | Leonida Keys | embed_permitted | approved |
| 50 | `shot-grassrivers-01` | screenshot | /VI/media/screenshots | `…/media/Grassrivers_01.1096rw4lbjur_.jpg` | Grassrivers | embed_permitted | approved |
| 51 | `shot-grassrivers-02` | screenshot | /VI/media/screenshots | `…/media/Grassrivers_02.0teqs5xe2pem1.jpg` | Grassrivers | embed_permitted | approved |
| 52 | `shot-port-gellhorn-01` | screenshot | /VI/media/screenshots | `…/media/Port_Gellhorn_01.0fmisvza-5-cq.jpg` | Port Gellhorn | embed_permitted | approved |
| 53 | `shot-port-gellhorn-02` | screenshot | /VI/media/screenshots | `…/media/Port_Gellhorn_02.00e7cz6lwrup-.jpg` | Port Gellhorn | embed_permitted | approved |
| 54 | `shot-ambrosia-01` | screenshot | /VI/media/screenshots | `…/media/Ambrosia_01.0rqphs0gazkm..jpg` | Ambrosia | embed_permitted | approved |
| 55 | `shot-ambrosia-02` | screenshot | /VI/media/screenshots | `…/media/Ambrosia_02.0wtqs05ozl.ym.jpg` | Ambrosia | embed_permitted | approved |
| 56 | `shot-mount-kalaga-01` | screenshot | /VI/media/screenshots | `…/media/Mount_Kalaga_National_Park_01.0v5fl0f83hjv_.jpg` | Mount Kalaga | embed_permitted | approved |
| 57 | `shot-mount-kalaga-02` | screenshot | /VI/media/screenshots | `…/media/Mount_Kalaga_National_Park_02.0f24dhopdprvx.jpg` | Mount Kalaga | embed_permitted | approved |

Attribution for every row: *Copyright Rockstar Games / Take-Two Interactive.* Intended use: character portraits and galleries, region covers, the homepage hero, trailer previews and the screenshot mosaic.

## Adding a new asset (checklist)

1. Read the URL from the official page. Request it once to confirm it loads.
2. Add it to the manifest, regenerate `database/migrations/` and the seed block, and add it here.
3. Link it to the right character or region. Never link official media to a fictional demo record.
4. Never commit the file itself.
