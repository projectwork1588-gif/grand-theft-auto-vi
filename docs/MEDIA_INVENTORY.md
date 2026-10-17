# Media inventory

**Policy.** Nothing from Rockstar is committed. The only files that are downloaded are the eight character clips that `scripts/fetch_clips.py` reads, and the loops built from them, which stay in the Git-ignored `media/` folder on your own machine. Official images and videos are **remote references to Rockstar's own published media**, shown with attribution and a link back to the source page. Watermarks and copyright notices are never removed. Concept records (some characters, all locations and missions, and the concept vehicles) never receive official images. Everything the project owns is original: the CSS fallbacks and the brand mark.

The database table `media_assets` holds exactly the rows below, linked to characters, regions and vehicles through `media_characters`, `media_regions` and `media_vehicles`. Rows 1-57 come from migration 001, rows 58-85 from migration 002 and rows 86-107 from migration 004 (rows 61-68 also gain a `local_path` there). All are generated from manifests, and a test (`test_seed_and_migration_agree`) proves that a fresh seed and an upgraded Phase 1 database end up identical.

## Where the media came from (checked 2026-10-09 and 2026-10-10)

| Source page | What it offers |
|-------------|----------------|
| https://www.rockstargames.com/VI/media/artwork-wallpapers | 23 artwork and wallpaper items (character portraits, Jason and Lucia art, region postcards) |
| https://www.rockstargames.com/VI/media/screenshots | 162 official screenshots (per character, per region, and the Ultimate Edition and Vintage Vice City Pack vehicle sets) |
| https://www.rockstargames.com/VI/media/videos | Three videos, the cover-art animation, and eight character clips, each with a poster image |
| https://www.rockstargames.com/VI/trailer-1, /trailer-2, /an-extended-look | Official videos, each embedding Rockstar's own player (`/videoplayer?id=...&embed`) |
| https://www.rockstargames.com/VI/editions | The vehicle names (for example the '95 Grotti Cheetah) |

All 85 referenced URLs were requested before they were recorded and returned HTTP 200 with the expected content type. Rockstar's player pages send no framing restriction (they are built to be embedded). Rockstar's image service accepts a width parameter, which the site uses to request 640, 1280 and 1920 pixel versions.

## What changed in the refinement pass

* **Official garage.** Only vehicles that Rockstar names and shows are public: the '95 Grotti Cheetah, '67 Vapid Dominator Buggy, Shitzu Squalo, Vapid Stanier and Vapid Ganado Retro Build (17 official screenshots). Several names that look like vehicles (Stock 305, Electric Fang, Rideout Customs, One-Eyed Willie's) are stores or services on Rockstar's own page, and were **not** added. The concept vehicles stay in the database for the story archive but get no public page and no official imagery.
* **Posters.** Each trailer card uses the official poster Rockstar publishes for that video.
* **Character clips.** Rockstar publishes one short clip per named character. The clip files are **not** hosted or played here. Each character gets a poster-and-link card that opens Rockstar's Videos page. The poster image is stored in `embed_url`, and the clip page in `source_url`.

## What changed in refinement round 2

* **Reel pacing (round 3 follow-up).** The clips are 1 to 1.5 s, so the reel gives each person a full beat: about 2.6 s of the clip slowed and motion-interpolated, then a held final frame with a slow push-in, 4.0 s in all, with 0.5 s dissolves, 28.5 s for eight people. Square clips sit flush right over a feathered extension of themselves. Total media is about 8 MB.
* **Local motion.** Rockstar's downloads archive (`GTAVI_Videos.zip`, linked from its Videos page) holds the eight character clips at 1 to 1.5 seconds and 4K. `scripts/fetch_clips.py` reads only those eight out of the archive with HTTP range requests (about 40 MB, CRC checked). `scripts/make_loops.py` builds a muted 1280 by 720 loop and a poster for each (about 0.3 to 1 MB each) and one 9-second reel (2.2 MB). Total about 6 MB.
* **Why these and not the trailers.** The trailers are 4K files over a gigabyte and Rockstar's player has no mute, loop or background control. Only the short clips are a sensible size for an ambient loop.
* **Not committed.** `media/` is Git-ignored apart from its README. A fresh clone has no loops and every page falls back to official stills and posters.
* **Rights.** Rockstar states no licence terms for these files. Rows 61 to 68 carry the loop's path; row 107 (the reel) is marked `permission_required` / `pending_review`. The owner should decide before publishing the site publicly.
* **New images.** 21 further official screenshots (rows 86 to 106) give each region a wider selection and Jason and Lucia more choice of crop. Each URL was requested before it was recorded.

> **Reel update (cinematic implementation).** The cast reel no longer slows the clips. Each person plays their clip at true speed (1.0 to 1.5 s), dissolves over 0.4 s into their official artwork and holds it for about 1.6 s with a very slow push-in: 2.6 to 3.1 s per person, 19.7 s for all eight, 1600 x 900. `scripts/make_loops.py` fetches the eight artworks once into `media/source/art/`.

## The signature moment (refinement round 3)

> **Superseded by Design Reset Gate 2.** The homepage no longer plays any trailer footage through YouTube's player as a background. The section is now a native-video slot: an official still with a play control that opens Rockstar's own player on request, or, when the owner supplies footage that is authorised for reuse and builds `media/cinematic/cinematic.mp4`, native HTML5 video (muted autoplay in view, paused out of view, an Enable sound button, reduced-motion and phone fallbacks). The rights findings below still apply and are the reason nothing is copied from the trailers. See `docs/DESIGN_GATE2.md`.

The homepage has one full-screen sequence between the two leads and the cast. This section records how it was chosen, what the usage position is, and what the limits are.

### Rights position

| Question | Finding |
|----------|---------|
| Does Rockstar offer the trailers for download? | **No.** Its Videos page (rockstargames.com/VI/media/videos) offers one zip (`GTAVI_Videos.zip`) holding nine clips: the cover-art animation and the eight character clips. The trailers and "An Extended Look" are offered only through Rockstar's embedded player and its YouTube channel. |
| Is there a licence for reuse? | **None stated** on the media pages. Rockstar's "Policy on posting copyrighted Rockstar Games material" tolerates non-commercial fan content and keeps the right to remove it, but it is written for in-game footage and does not address trailers or marketing video. |
| Therefore | The trailers are **not downloaded, cut, re-encoded or hosted** by this project. A local clip of a trailer would be an unauthorised copy. The sequence is played from Rockstar's own upload through YouTube's embedded player, unaltered, with the player's own branding intact. |
| Embedding | `oEmbed` returns 200 for Trailer 1 (`QdBZY2fkU-0`) and Trailer 2 (`VQRLujxTm3c`), uploaded by "Rockstar Games", so embedding is enabled by the owner. The privacy-enhanced `youtube-nocookie.com` host is used. |
| An Extended Look | Rockstar's page links `tJbzMqJGH4k`, which YouTube marks **age-restricted**, and age-restricted videos cannot be embedded on other sites. It is excluded from the moment. It still plays in Rockstar's own player in the trailer dialog. |

### Candidates reviewed

Each official video was stepped through frame by frame (once per second, and per half second around cuts) in the embedded player. The trailers are fast-cut montages, so a single unbroken eight-to-twelve-second take does not exist; the choice is the best continuous stretch of Rockstar's own edit.

| # | Where | Length | What it shows | Verdict |
|---|-------|--------|---------------|---------|
| 1 | Trailer 1, 18.5 s to 27.3 s | 8.8 s | Skyscraper tilt-up, golden marsh dawn, flamingo flock, beach, harbour speedboat, neon highway at night. No title card, dialogue or social-media overlay. Moves from dawn to neon, which is the site's own palette. | **Chosen** |
| 2 | Trailer 1, 31.4 s to 37.9 s | 6.5 s | Night aerial of the city, neon boulevard, club crowd, causeway and seaplane. Strong, but short, and ends on a suggestive pool close-up. | Rejected: too short |
| 3 | Trailer 1, about 39.3 s to 41.3 s | 2 s | The sunset VICE sign. Iconic, but two seconds, followed by phone-video overlays. | Rejected: too short |
| 4 | Trailer 2, 35.5 s to 39.5 s | 4 s | First-person highway drive with road signs. Good camera movement but a single short beat. | Rejected: too short |
| 5 | Trailer 2, 6.5 s to 10 s | 3.5 s | Coastal aerial and a stilt house, then dialogue scenes. | Rejected: too short, then talking heads |
| 6 | An Extended Look | n/a | Could not be reviewed or embedded: age-restricted. | Excluded |
| 7 | Official Cover Art Animation (the one downloadable "video" besides the character clips, 32.7 s, 3840 by 2160, with sound) | 32.7 s | An ESRB card, the R★ mark, a VI logo reveal and the key-art collage assembling, then the release date. A title sequence, not footage. | Rejected: not cinematic footage |

### Why it is an embed and not a native video

The goal was a background that feels native: no player interface, starting as the section arrives. The strongest compliant way to get that is limited by who owns the footage.

| Route | What it would give | Why it is or is not used |
|-------|-------------------|--------------------------|
| A local `<video>` cut from the trailer | Fully native: no interface, instant, sound control, loops | **Not used.** There is no trailer download and no licence. This would be copying and re-editing Rockstar's marketing video without permission |
| An officially downloadable clip | Native | Only the cover-art animation and eight 1 to 1.5 s character clips are offered. The animation is a title sequence; the clips are used for the cast reel |
| Rockstar's own player (`/videoplayer?id=...`) | Rockstar's chosen presentation | It is a thin wrapper around the same YouTube embed (`youtube-nocookie.com/embed/<id>?autoplay=0&enablejsapi=1`), with no extra parameters to remove interface |
| **YouTube's embedded player via the IFrame API** | The footage is Rockstar's own upload, unaltered; muted autoplay; scroll-aware pause; sound on request | **Used.** Interface cannot be switched off entirely, and we do not crop or cover it |

What the page does to make it feel as native as the provider allows: it pre-rolls the player hidden behind an official still so YouTube's own title bar has faded; it only reveals the footage once it has really been playing and the section is on screen; it dissolves it in; it puts the still back whenever it is paused; the control layer is one "Enable sound" pill, an icon pause button and a credit line. What it does not do: remove or restyle YouTube's branding, crop the frame to hide it, or download anything.

Sound: autoplay with sound is blocked by browsers, so the footage starts muted and a clearly labelled **Enable sound** button turns it on (a user gesture, so it is allowed).

### How it is played

* The page loads YouTube's IFrame API and creates the player only when the section is within about one screen of the viewport, muted, with controls and keyboard off.
* The section shows an official Rockstar still (a Grassrivers screenshot, a wetland scene that matches the sequence) until the player is really playing inside the chosen window, so the frames before it (a "Rockstar Games presents" card at 18.2 s) are never seen.
* It loops through a short dip to black, pauses when scrolled away or when the tab is hidden, and is **not started automatically** for visitors who prefer reduced motion or have data saver on (they get the still and a "Play the footage" button).
* A Sound button unmutes on request. The caption credits Rockstar, and "Watch the full trailer" opens the same video in Rockstar's own player.
* Cost: about 30 KB of YouTube's loader script, then YouTube's player and a video stream that adapts to the screen. Nothing is loaded before the section is near.

### Limits to know about

* YouTube's embed cannot hide all of its own interface. The player is shown without controls and without pointer input, but if it is paused its own pause mark appears, and the title bar appears if the pointer is allowed onto it. Branding is not cropped or covered.
* Autoplay needs the page to be visible. A background tab or a hidden window will not start it, by design.
* The window start and end (18.5 and 27.3) are the trailer's own cuts as measured. If Rockstar re-uploads the trailer, re-check them.
* Playback was verified in the preview browser only when the pane was visible. See the verification record.

## Integration approach

* **Videos:** a poster card opens a native `<dialog>`. Only then does JavaScript create the iframe that points at Rockstar's player, so nothing loads until a visitor presses play. Closing the dialog removes the iframe, which stops playback.
* **Why trailers are not background video:** the trailer files are 4K and large (Trailer 2 is about 1.2 GB) and the player offers no mute or loop control. The trailers stay on Rockstar's player, on demand. Ambient motion comes only from the short local loops.
* **Local loops:** `<video muted loop playsinline preload="none">` with no `autoplay` attribute. The script starts a loop only when it is on screen, pauses it when it leaves, never starts it for visitors who prefer reduced motion or have data saver on, and always offers Pause and Play.
* **Images:** ordinary `<img>` elements with `srcset`, `loading="lazy"` (the hero image uses `fetchpriority="high"`) and `referrerpolicy="no-referrer"`, over an original fallback layer. If an image fails, the fallback shows.
* **Safety:** templates only render a URL that starts with Rockstar's exact image prefix or player prefix (`app/media_urls.py`). The Content-Security-Policy allows images and frames only from `www.rockstargames.com`. A hostile database value is ignored (tested).
* **Reduced motion:** visitors who ask for reduced motion get a still first hero image and no slideshow.

## Status and risks

| Item | Status |
|------|--------|
| Rockstar states **no licence terms** on its Media page, only an invitation to download and share | **Human review recommended.** The Phase 2 media brief authorised use of official sources, and nothing is copied, but the owner should confirm this is acceptable. |
| Image file names are **build-hashed** (for example `Cal_Hampton_landscape.17k7bnt3myg.2.jpg`) | They may change when Rockstar redeploys. The site then falls back to original artwork. Re-run the URL check and refresh the migrations. |
| Vehicle specifications | Rockstar publishes none, so none are shown. |
| Vehicle categories | Judged from Rockstar's own screenshots where its page does not state a type (for example the Shitzu Squalo). Each such record says so in its source note. |
| Character clip files | **Used locally**, as short muted loops, and never committed (see above). The 4K trailers are not downloaded. |

## Inventory (114 rows)

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
| 58 | `poster-trailer-1` | artwork | /VI/media/videos | `…/media/GTAVI_Trailer1_poster.12x2gvspcm_3m.jpg` | none | embed_permitted | approved |
| 59 | `poster-trailer-2` | artwork | /VI/media/videos | `…/media/GTAVI_Trailer2_poster.0cosv-uzbpt91.jpg` | none | embed_permitted | approved |
| 60 | `poster-extended-look` | artwork | /VI/media/videos | `…/media/GTAVI_An_Extended_Look_poster.0ijbsha5fo1te.jpg` | none | embed_permitted | approved |
| 61 | `clip-jason-duval` | video | /VI/media/videos | `…/media/Jason_Duval_Video_Clip.024oe-y640yxp.jpg` + local loop `media/clips/jason-duval.mp4` | Jason Duval | link_only | approved |
| 62 | `clip-lucia-caminos` | video | /VI/media/videos | `…/media/Lucia_Caminos_Video_Clip.0uqwkm_u_fu_9.jpg` + local loop `media/clips/lucia-caminos.mp4` | Lucia Caminos | link_only | approved |
| 63 | `clip-cal-hampton` | video | /VI/media/videos | `…/media/Cal_Hampton_Video_Clip.127phn-5fdl9r.jpg` + local loop `media/clips/cal-hampton.mp4` | Cal Hampton | link_only | approved |
| 64 | `clip-boobie-ike` | video | /VI/media/videos | `…/media/Boobie_Ike_Video_Clip.06_gu6y13hufm.jpg` + local loop `media/clips/boobie-ike.mp4` | Boobie Ike | link_only | approved |
| 65 | `clip-dequan-priest` | video | /VI/media/videos | `…/media/DreQuan_Priest_Video_Clip.0p5nv9luhe2va.jpg` + local loop `media/clips/dre-quan-priest.mp4` | Dre'Quan Priest | link_only | approved |
| 66 | `clip-real-dimez` | video | /VI/media/videos | `…/media/Real_Dimez_Video_Clip.05f8p4_2sk82a.jpg` + local loop `media/clips/real-dimez.mp4` | Real Dimez | link_only | approved |
| 67 | `clip-raul-bautista` | video | /VI/media/videos | `…/media/Raul_Bautista_Video_Clip.07g3eeo2bgg2k.jpg` + local loop `media/clips/raul-bautista.mp4` | Raul Bautista | link_only | approved |
| 68 | `clip-brian-heder` | video | /VI/media/videos | `…/media/Brian_Heder_Video_Clip.0wbjj2r2i_2~c.jpg` + local loop `media/clips/brian-heder.mp4` | Brian Heder | link_only | approved |
| 69 | `vehicle-grotti-cheetah-01` | screenshot | /VI/media/screenshots | `…/media/ULTIMATE_EDITION_GROTTI_CHEETAH_01.0a.wy3s_ogjey.jpg` | '95 Grotti Cheetah | embed_permitted | approved |
| 70 | `vehicle-grotti-cheetah-02` | screenshot | /VI/media/screenshots | `…/media/ULTIMATE_EDITION_GROTTI_CHEETAH_02.0rkrlsu_dg~ww.jpg` | '95 Grotti Cheetah | embed_permitted | approved |
| 71 | `vehicle-grotti-cheetah-03` | screenshot | /VI/media/screenshots | `…/media/ULTIMATE_EDITION_GROTTI_CHEETAH_03.0v3_dryhtjarc.jpg` | '95 Grotti Cheetah | embed_permitted | approved |
| 72 | `vehicle-grotti-cheetah-04` | screenshot | /VI/media/screenshots | `…/media/ULTIMATE_EDITION_GROTTI_CHEETAH_04.0caq_y0_f1rvt.jpg` | '95 Grotti Cheetah | embed_permitted | approved |
| 73 | `vehicle-vapid-dominator-buggy-01` | screenshot | /VI/media/screenshots | `…/media/ULTIMATE_EDITION_VAPID_BUGGY_01.0jxfiql~371ik.jpg` | '67 Vapid Dominator Buggy | embed_permitted | approved |
| 74 | `vehicle-vapid-dominator-buggy-02` | screenshot | /VI/media/screenshots | `…/media/ULTIMATE_EDITION_VAPID_BUGGY_04.0_29d.bgfvon7.jpg` | '67 Vapid Dominator Buggy | embed_permitted | approved |
| 75 | `vehicle-vapid-dominator-buggy-03` | screenshot | /VI/media/screenshots | `…/media/ULTIMATE_EDITION_VAPID_BUGGY_02.0tf15jp~61bkj.jpg` | '67 Vapid Dominator Buggy | embed_permitted | approved |
| 76 | `vehicle-vapid-dominator-buggy-04` | screenshot | /VI/media/screenshots | `…/media/ULTIMATE_EDITION_VAPID_BUGGY_03.0s2rbkg98-0ac.jpg` | '67 Vapid Dominator Buggy | embed_permitted | approved |
| 77 | `vehicle-shitzu-squalo-01` | screenshot | /VI/media/screenshots | `…/media/ULTIMATE_EDITION_SQUALO_01.0cim7hj58ypb1.jpg` | Shitzu Squalo | embed_permitted | approved |
| 78 | `vehicle-shitzu-squalo-02` | screenshot | /VI/media/screenshots | `…/media/ULTIMATE_EDITION_SQUALO_04.00vlesedwtiuy.jpg` | Shitzu Squalo | embed_permitted | approved |
| 79 | `vehicle-shitzu-squalo-03` | screenshot | /VI/media/screenshots | `…/media/ULTIMATE_EDITION_SQUALO_02.09qplkj.rjnk7.jpg` | Shitzu Squalo | embed_permitted | approved |
| 80 | `vehicle-shitzu-squalo-04` | screenshot | /VI/media/screenshots | `…/media/ULTIMATE_EDITION_SQUALO_03.0quncwrsw97j1.jpg` | Shitzu Squalo | embed_permitted | approved |
| 81 | `vehicle-vapid-stanier-01` | screenshot | /VI/media/screenshots | `…/media/VINTAGE_VICE_CITY_PACK_VAPID_STANIER_01.004m_8d1~qngy.jpg` | Vapid Stanier | embed_permitted | approved |
| 82 | `vehicle-vapid-stanier-02` | screenshot | /VI/media/screenshots | `…/media/VINTAGE_VICE_CITY_PACK_VAPID_STANIER_02.0s2wun4_vzld2.jpg` | Vapid Stanier | embed_permitted | approved |
| 83 | `vehicle-vapid-stanier-03` | screenshot | /VI/media/screenshots | `…/media/VINTAGE_VICE_CITY_PACK_VAPID_STANIER_03.0dzlk-r0ehlu4.jpg` | Vapid Stanier | embed_permitted | approved |
| 84 | `vehicle-vapid-stanier-04` | screenshot | /VI/media/screenshots | `…/media/VINTAGE_VICE_CITY_PACK_VAPID_STANIER_04.0n002i9p87b~q.jpg` | Vapid Stanier | embed_permitted | approved |
| 85 | `vehicle-vapid-ganado-01` | screenshot | /VI/media/screenshots | `…/media/ULTIMATE_EDITION_VAPID_GANADO_RETRO_BUILD_01.062dgvkwdynw5.jpg` | Vapid Ganado Retro Build | embed_permitted | approved |
| 86 | `shot-lucia-caminos-08` | screenshot | /VI/media/screenshots | `…/media/Lucia_Caminos_08.08wo73uyjkhlk.jpg` | Lucia Caminos | embed_permitted | approved |
| 87 | `shot-lucia-caminos-09` | screenshot | /VI/media/screenshots | `…/media/Lucia_Caminos_09.0pd.ppokmi8-n.jpg` | Lucia Caminos | embed_permitted | approved |
| 88 | `shot-lucia-caminos-10` | screenshot | /VI/media/screenshots | `…/media/Lucia_Caminos_10.0s770xrip~yb..jpg` | Lucia Caminos | embed_permitted | approved |
| 89 | `shot-jason-duval-04` | screenshot | /VI/media/screenshots | `…/media/Jason_Duval_04.16d-z2wa2s~bk.jpg` | Jason Duval | embed_permitted | approved |
| 90 | `shot-jason-duval-06` | screenshot | /VI/media/screenshots | `…/media/Jason_Duval_06.086o72llg6~1p.jpg` | Jason Duval | embed_permitted | approved |
| 91 | `shot-vice-city-08` | screenshot | /VI/media/screenshots | `…/media/Vice_City_08.0bbg_xp4hqdvz.jpg` | Vice City | embed_permitted | approved |
| 92 | `shot-vice-city-09` | screenshot | /VI/media/screenshots | `…/media/Vice_City_09.0~ng.c8ack3fp.jpg` | Vice City | embed_permitted | approved |
| 93 | `shot-vice-city-10` | screenshot | /VI/media/screenshots | `…/media/Vice_City_10.0f1q-xa_4q8r2.jpg` | Vice City | embed_permitted | approved |
| 94 | `shot-vice-city-11` | screenshot | /VI/media/screenshots | `…/media/Vice_City_11.09paum3g942sc.jpg` | Vice City | embed_permitted | approved |
| 95 | `shot-leonida-keys-03` | screenshot | /VI/media/screenshots | `…/media/Leonida_Keys_03.0v_3~-9ceyixc.jpg` | Leonida Keys | embed_permitted | approved |
| 96 | `shot-leonida-keys-05` | screenshot | /VI/media/screenshots | `…/media/Leonida_Keys_05.0yerhvjhto-h..jpg` | Leonida Keys | embed_permitted | approved |
| 97 | `shot-leonida-keys-06` | screenshot | /VI/media/screenshots | `…/media/Leonida_Keys_06.0eapr3hbeyewx.jpg` | Leonida Keys | embed_permitted | approved |
| 98 | `shot-grassrivers-03` | screenshot | /VI/media/screenshots | `…/media/Grassrivers_03.14cuv-vg9orw4.jpg` | Grassrivers | embed_permitted | approved |
| 99 | `shot-grassrivers-04` | screenshot | /VI/media/screenshots | `…/media/Grassrivers_04.01ckpqbhxyz76.jpg` | Grassrivers | embed_permitted | approved |
| 100 | `shot-grassrivers-05` | screenshot | /VI/media/screenshots | `…/media/Grassrivers_05.0.dx9~67tljry.jpg` | Grassrivers | embed_permitted | approved |
| 101 | `shot-port-gellhorn-06` | screenshot | /VI/media/screenshots | `…/media/Port_Gellhorn_06.13ghhmb440r6e.jpg` | Port Gellhorn | embed_permitted | approved |
| 102 | `shot-ambrosia-04` | screenshot | /VI/media/screenshots | `…/media/Ambrosia_04.0.2cefoguu-tt.jpg` | Ambrosia | embed_permitted | approved |
| 103 | `shot-mount-kalaga-03` | screenshot | /VI/media/screenshots | `…/media/Mount_Kalaga_National_Park_03.037k2s87rwuxc.jpg` | Mount Kalaga | embed_permitted | approved |
| 104 | `shot-mount-kalaga-04` | screenshot | /VI/media/screenshots | `…/media/Mount_Kalaga_National_Park_04.0e1sxnp1mln2u.jpg` | Mount Kalaga | embed_permitted | approved |
| 105 | `shot-mount-kalaga-05` | screenshot | /VI/media/screenshots | `…/media/Mount_Kalaga_National_Park_05.0_~vto-o2zxok.jpg` | Mount Kalaga | embed_permitted | approved |
| 106 | `shot-mount-kalaga-06` | screenshot | /VI/media/screenshots | `…/media/Mount_Kalaga_National_Park_06.166ouq5pjd7h0.jpg` | Mount Kalaga | embed_permitted | approved |
| 107 | `reel-leonida` | video | /VI/media/videos | `local: media/clips/leonida-reel.mp4` (Git-ignored) | none | permission_required | pending_review |
| 108 | `vehicle-dinka-enduro-01` | screenshot | /VI/media/screenshots | `…/media/ULTIMATE_EDITION_SAFEHOUSE_VEHICLES_02.0-2n5rm9n8.rq.jpg` | Dinka Enduro Motorcycle | embed_permitted | approved |
| 109 | `vehicle-crest-kayak-01` | screenshot | /VI/media/screenshots | `…/media/ULTIMATE_EDITION_SAFEHOUSE_VEHICLES_03.0c9.qtpdi.tf..jpg` | Crest Kayak | embed_permitted | approved |
| 110 | `garage-jasons-safehouse` | screenshot | /VI/media/screenshots | `…/media/ULTIMATE_EDITION_SAFEHOUSE_VEHICLES_01.0wv6pw3t-mky3.jpg` | Dinka Enduro Motorcycle, Crest Kayak (scene; no vehicle named) | embed_permitted | approved |
| 111 | `garage-rideout-customs-01` | screenshot | /VI/media/screenshots | `…/media/ULTIMATE_EDITION_RIDEOUT_CUSTOMS_01.065-ms8~k8vbq.jpg` | none (atmosphere; car not named) | embed_permitted | approved |
| 112 | `garage-one-eyed-willies-01` | screenshot | /VI/media/screenshots | `…/media/ULTIMATE_EDITION_ONE_EYED_WILLIE_01.0n7-__or5f.b6.jpg` | none (atmosphere; truck not named) | embed_permitted | approved |
| 113 | `garage-classic-cars-02` | screenshot | /VI/media/screenshots | `…/media/ULTIMATE_EDITION_WYMAN_CAR_COLLECTION_02.0_biiqjqkpg2b.jpg` | none (atmosphere; car not named) | embed_permitted | approved |
| 114 | `garage-classic-cars-04` | screenshot | /VI/media/screenshots | `…/media/ULTIMATE_EDITION_WYMAN_CAR_COLLECTION_04.05ku1csui.4h6.jpg` | none (atmosphere; car not named) | embed_permitted | approved |

Attribution for every row: *Copyright Rockstar Games / Take-Two Interactive.*

## Garage research (Gate 3B, 2026-10-16)

Rockstar's screenshots page (https://www.rockstargames.com/VI/media/screenshots) lists 166 pictures. All were reviewed as 360 px thumbnails.
Vehicles Rockstar names: the five already registered, plus the **Dinka Enduro Motorcycle** and **Crest Kayak** (titles of two pictures in its
"Jason's Safehouse Vehicles" set), now rows 108 and 109 and the two newest official vehicles. Pictures that show cars Rockstar does not
name (the Rideout Customs and One-Eyed Willie's mod shops, the Classic Car Collection, the safehouse scene) are rows 110 to 114 and are used as
atmosphere only. The two trailers (media/source-videos/trailers) were sampled every two seconds: their vehicles are unnamed, small and
people-centred, so no frame was used. Not used: location shots with unnamed vehicles (Leonida Keys, Grassrivers, Mount Kalaga, Ambrosia).

## Adding a new asset (checklist)

1. Read the URL from the official page. Request it once to confirm it loads.
2. Add it to the manifest, regenerate the next migration and the seed block, and add it here.
3. Link it to the right character, region or vehicle. Never link official media to a concept record.
4. Never commit the file itself.

## Garage sea clip (the owner's instruction, 2026-10-17)

The owner supplied Rockstar's Launch Trailer (published 15 October 2026) and asked for short excerpts to strengthen the Garage. This supersedes the earlier "trailers are not cut" decision for this one purpose; the files stay Git-ignored and removable.
All three trailers on disk (Launch Trailer, Trailer 1, Trailer 2) were stepped through. The shots are mostly 0.5 to 2 s long and many carry people, weapons or text, so only two calm, caption-free shots were used, joined by a 0.5 s dissolve into one 3.3 s muted clip (`media/clips/garage/on-the-water.mp4`, built by `python -m scripts.make_garage_clips`):

| Shot | Source | Time | What it shows | Used because |
|---|---|---|---|---|
| Marina from the air | Launch Trailer | 4.98 to 6.90 s | A slow aerial of a boat marina, boats stacked in racks | Boats and water, no people, no overlay; says nothing about which vehicle is which |
| Sunset over a dock | Trailer 2 | 83.15 to 85.00 s | Golden sunset on calm water, a dock rail, string lights, life rings | The continuity into the Kayak's own sunset picture |

Considered and not used: the aerial boat and surf shots (Trailer 1, 10.8 to 14.2 s: three shots of 0.6 to 0.9 s each); the dirt-bike jump (Launch Trailer, about 1.3 s); the green lowrider (Launch Trailer, 19.0 to 21.0 s: a pistol is in frame); the street and police shots (0.25 to 0.5 s each); the marina seaplane (0.9 s). No unnamed vehicle in the footage is identified as one of the seven. The page asks for the file only when the finale is near, only when motion is allowed and data saver is off, plays it once, and rests on its last frame (the still picture).

