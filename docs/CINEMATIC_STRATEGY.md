# GTA VI cinematic strategy: source review, shortlist and recommendation

Status: **research and proposal only. Nothing was integrated, no footage was edited or published, and no application code, database or test was changed.** Gate 2 is awaiting the owner's visual approval; Gate 3 and Phase 3 are not authorised.

The analysis was made from the owner's local files in `media/source-videos/`, shot by shot (one frame per second across every second of all three videos, then four frames per second around each candidate, plus automatic cut detection). All analysis frames live in the Git-ignored `review/cinematic/` folder. The three source videos and every frame stay out of Git.

---

## A. Source media inventory

| File | Path | Duration | Resolution | Video | Audio | Size | Notes |
|------|------|----------|-----------|-------|-------|------|-------|
| Trailer 1 | `media/source-videos/trailers/GTAVI_Trailer_1.mp4` | 90.03 s | 3840 x 2160, 16:9, 30 fps | MPEG-4 Part 2 (Simple Profile), 63 Mb/s | AAC stereo 189 kb/s | 680.1 MB | Full frame, no letterbox. ESRB card 0 to 2.7 s. |
| Trailer 2 | `media/source-videos/trailers/GTAVI_Trailer_2.mp4` | 166.73 s | 3840 x 2160, 30 fps | MPEG-4 Part 2 (Simple Profile), 63 Mb/s | AAC stereo 192 kb/s | 1,252.5 MB | **Letterboxed:** the picture is 3840 x 1728 (2.22:1) with 216 px black bars top and bottom. ESRB card and R* logo 0 to 6 s. |
| Official cover-art animation | `media/source-videos/other-clips/GTAVI_Official_Cover_Art_Landscape.mp4` | 32.67 s | 3840 x 2160, 16:9, 30 fps | H.264 High, 9.4 Mb/s | AAC stereo 119 kb/s | 37.1 MB | No cuts. A title sequence, not scene footage. |
| Eight character clips | `media/source-videos/other-clips/*_Video_Clip.mp4` | 1.0 to 1.5 s each | six at 2160 x 2160 (1:1), Jason and Lucia at 3840 x 2160 | H.264 High, 47 to 128 Mb/s | silent AAC | 5.6 to 15.3 MB each | Same files as the existing reel. |

* **Absent, as expected:** An Extended Look (excluded by the owner). `media/source-videos/gameplay/` is empty. Nothing was substituted.
* **Compatibility:** Both trailers use an old codec (MPEG-4 Part 2) that browsers do not play natively and at about 63 Mb/s they are unsuitable for the web as they are. Any web version must be transcoded (H.264, and optionally AV1 or VP9). No corruption was found; both decode cleanly end to end.
* **Letterboxing matters:** Trailer 2 is a 2.22:1 picture. A 16:9 full-viewport crop would lose about 25 percent of the width, so the recommendations below present Trailer 2 in a 21:9 band instead.
* **Disk:** 91 GB free.

---

## B. Cinematic shortlist (ten candidates)

Timestamps are source times, snapped to the detected cut (first frame of a shot to the last frame before the next cut; one frame is 0.033 s).

| Rank | Source | Start | End | Duration | Scene description | Visual impact /10 | Recommended location |
|---|---|---|---|---|---|---|---|
| 1 | Trailer 1 | 19.17 | 27.40 | 8.2 s | Golden marsh at dawn with an airboat, a flock of flamingos, the crowded beach, a speedboat past the container port, then a neon night road with a dancer on a convertible. No text, no overlays, no cuts to dialogue. | **9.5** | **Moment 1** (signature) |
| 2 | Trailer 2 | 152.85 | 162.00 | 9.15 s | Golden-hour aerial of an overpass and palms with sun flare over the skyline, a fade to black, the neon outline of VI igniting and filling with the sunset gradient, then the Grand Theft Auto wordmark and the date. | **9.3** | **Moment 3** (finale) |
| 3 | Trailer 2 | 6.35 to 9.70, then 138.15 to 143.65 | 8.45 s (two shots, one dissolve) | | Turquoise Keys aerial with houses on the water, a stilt house and Cadillac, then a helicopter chasing a boat through the swamp, a jet ski couple and a motorcycle under a seaplane. Bright, fast, sunny. | **8.6** | **Moment 2** (world of Leonida) |
| 4 | Trailer 1 | 2.65 | 8.30 | 5.6 s | Pink sunset over a highway at rush hour, barbed wire against the sunset, Lucia looking out of a prison van. Matches the site palette exactly. Short. | 8.4 | Reserve (Lucia profile, or a hero alternative) |
| 5 | Trailer 2 | 79.50 | 85.10 | 5.6 s | Jason and Lucia with beers at a bar, sitting on a dock at sunset, lights over golden water. The only sustained leads moment that is calm. | 8.2 | Reserve (Jason and Lucia profile pages) |
| 6 | Trailer 2 | 138.15 | 143.65 | 5.5 s | Helicopter and boat in the swamp, jet ski, motorcycle with seaplane. The second half of candidate 3 on its own. | 8.0 | Folded into Moment 2 |
| 7 | Trailer 1 | 31.10 | 37.25 | 6.15 s | Night aerial of the islands, neon boulevard with sports cars, club crowd, then a daytime causeway and seaplane. Mixed grade, includes a crowd. | 7.6 | Reserve (Vice City at night) |
| 8 | Trailer 1 | 60.50 | 64.60 | 4.1 s | Jason driving and Lucia in the passenger seat, billboard and desert road. Short and followed by news overlays. | 7.0 | Reserve |
| 9 | Trailer 1 | 76.60 | 87.60 | 11 s | An armed hold-up (1.8 s) then the VI logo reveal. Violent opening and the logo is the same as candidate 2, which is better. | 7.0 | Not recommended |
| 10 | Cover-art animation | 6.80 | 23.20 | 16.4 s | The neon VI emerges, polygons fan out and assemble into the key-art collage, ending on the date and PRE-ORDER NOW. Flat grey-purple background. A graphic, not footage. | 6.5 as a film, 8 as a reveal | Optional bridge into the pre-order and key-art section |

Material that was rejected on sight: ESRB cards and R* logos (the first 3 to 6 s of each), the social-media overlay montage in Trailer 1 (41 to 60 s), the news-overlay segments (64 to 70 s), most dialogue and narrative scenes in Trailer 2 (10 to 35 s, 52 to 70 s, 100 to 138 s), and the suggestive pool and club shots (not suitable for a school-project homepage).

**Why the first three rise to the top:** each is a continuous stretch free of text and overlays, each has a distinct light (dawn gold, midday turquoise, sunset gold into neon), and none depends on dialogue, so they read with the sound off.

---

## C. Final three recommendations

### Moment 1: "Dawn over Leonida"

| | |
|---|---|
| 1. Source | Trailer 1 |
| 2. In and out | 19.17 s to 27.40 s |
| 3. Duration | 8.2 s |
| 4. Visuals | Golden marsh and airboat, flamingos taking off over the water, the beach, a speedboat cutting past a container ship, a neon night road. A dawn-to-night arc inside one clip. |
| 5. Why it is exceptional | The widest range of colour and place of any stretch in either trailer, with natural pacing (about 2 s per shot, each a different texture), strong movement in every shot and no text. It is the clip most people remember from the trailer's first third. It works muted. |
| 6. Placement | Immediately after "Jason and Lucia" and before the cast. A full-viewport, edge-to-edge 16:9 band (about 86 vh). The people section hands over to the world: the section above ends on the dark ground, the clip fades up from it. |
| 7. Framing | Desktop: 16:9 `object-fit: cover`; the subjects sit in the central 60 percent, so a 21:9 monitor loses only sky and water. Mobile: a 4:5 crop (720 x 900) with per-shot focal points, initially marsh x 0.60 (airboat), flamingos x 0.45, beach x 0.35, speedboat x 0.58, night road x 0.30. |
| 8. Optimised size | Desktop 1080p H.264: **7.1 MB** (balanced, CRF 24) or 10.7 MB (high, CRF 21; 17.0 MB at 1440p). Mobile 4:5 720 x 900: **2.5 MB**. Poster 1920 x 1080: 305 KB. |
| 9. Sound | Muted by default. A deliberate "Enable sound" click unmutes (see the sound note below). |
| 10. Rights | Provenance and terms unconfirmed. See section C-4. |

**One alternative end point:** ending at 24.70 s (after the speedboat) gives a 5.5 s daytime-only clip and drops the night-road dancer.

### Moment 2: "Sun, water, speed"

| | |
|---|---|
| 1. Source | Trailer 2, two shots joined by a 0.4 s dissolve |
| 2. In and out | 6.35 to 9.70 s, then 138.15 to 143.65 s |
| 3. Duration | 8.45 s |
| 4. Visuals | A turquoise Keys aerial, a stilt house with a Cadillac, a helicopter chasing a boat through the swamp, a jet-ski couple on bright water, a motorcycle with a seaplane overhead. |
| 5. Why it is exceptional | The only bright, high-energy daylight material in either trailer, and the only footage that suggests the Keys and the Grassrivers, which is exactly what the region explorer is about. Trailer 2 has no single continuous daylight take longer than 3.5 s, so a one-dissolve edit is the cleanest honest way to give it a length that lets it breathe. |
| 6. Placement | A 21:9 "cinemascope" band directly above the Leonida region explorer. Its frame is the same shape as the explorer stage (2.2:1), so the page rhythm is: band, then stage. It introduces the explorer. |
| 7. Framing | Desktop and tablet: the 2.22:1 picture at full width with the black bars removed (no crop). Mobile: a 4:3 crop (960 x 720), focal points near the centre. |
| 8. Optimised size | Desktop 1920 x 864: **about 4.9 MB** (CRF 24; 7.3 MB at CRF 21 as measured). Mobile 4:3: **about 2.6 MB**. Poster 152 KB. |
| 9. Sound | Muted by default; Enable sound shares the one global sound state. |
| 10. Rights | Same unconfirmed provenance as Moment 1. |

### Moment 3: "Last light"

| | |
|---|---|
| 1. Source | Trailer 2 |
| 2. In and out | 152.85 s to 162.00 s |
| 3. Duration | 9.15 s |
| 4. Visuals | A golden-hour aerial over an overpass, palms and the skyline with sun flare, a fade to black, the neon outline of VI igniting and filling with the sunset gradient, the Grand Theft Auto wordmark, the date. |
| 5. Why it is exceptional | A sunset the site's own colours were drawn from, resolving into the same VI numeral as the hero. It closes the "day in Leonida" arc and flows straight into the date and the pre-order call to action. It needs no sound. |
| 6. Placement | Near the end, before the pre-order and closing-artwork section, on a pure-black section (the logo card's own background), as a 21:9 band. The sections around it fade to and from black. |
| 7. Framing | Desktop and tablet: the 2.22:1 picture at full width, black bars removed. Mobile: a 1:1 crop (720 x 720) centred on the logo. |
| 8. Optimised size | Desktop 1920 x 864: **about 2.2 MB** (CRF 24; 3.3 MB at CRF 21 and 5.2 MB at CRF 18 as measured). Mobile 1:1: **about 0.9 MB**. Poster 154 KB. |
| 9. Sound | Muted by default; the clip is the one most improved by sound (the music resolves with the logo). |
| 10. Rights | Same unconfirmed provenance. It also shows Rockstar's logo and the release date, which are official but make it less neutral than a pure scene clip. |

### C-4. Media-rights status

| Question | Status |
|----------|--------|
| Source of the two trailer files | **Not verified.** Local access is not permission. When last checked (2026-10-10) Rockstar's Videos page offered a zip with the cover-art animation and eight character clips, and the trailers only through its embedded player; no download or licence was stated for the trailers. These files may have come from a newer official media page or elsewhere. **The owner must state where they were obtained and under what terms.** |
| Cover-art animation and character clips | Offered for download by Rockstar's media page; no licence text is stated. Lower risk than trailers; the same caution applies to hosting and redistribution. |
| Music in the trailers | Third-party licensed music appears to run under the footage. Even if Rockstar permitted the picture, **the audio may carry separate licences.** Do not host the original soundtrack without confirmation. |
| What would make hosting safe | Written permission from Take-Two (copyright@take2games.com is the address in Rockstar's posting policy) for a short, muted, credited, non-commercial excerpt. A draft is in the appendix below. The owner decides whether to send it; nothing has been sent. |
| Fallback if permission is unavailable | Keep the Gate 2 behaviour: the official still and a "Watch the trailer" control that opens Rockstar's own embedded player. No iframe is shown on the page itself. |

**Sound note.** The encodes proposed above are picture-only by default. If the owner wants an Enable sound button on footage, the original audio can be carried over (about 100 KB per clip), but only if the music rights are confirmed; otherwise the sound control should be omitted for that clip.

---

## D. Visual layout proposal

`review/cinematic/journey.jpg` shows the homepage in order with the approved Gate 2 sections and frames from the three clips. Summary:

| Order | Section | Treatment |
|-------|---------|-----------|
| 1 | Hero | Gate 2 (unchanged) |
| 2 | Jason and Lucia | Gate 2 (unchanged) |
| 3 | **Moment 1, Dawn over Leonida** | Full viewport 16:9, top shade fades from the dark section above |
| 4 | Cast stage | Existing, with the reel re-cut at natural speed |
| 5 | **Moment 2, Sun, water, speed** | 21:9 band above the explorer |
| 6 | Region explorer | Gate 2 (unchanged) |
| 7 | Garage, stories, trailers | Gate 3 restyle |
| 8 | **Moment 3, Last light** | 21:9 band on black; fades to black above and below |
| 9 | Pre-order and closing artwork | Planned for a later gate |

**The narrative.** One day in Leonida: dawn (Moment 1), the bright middle of the day and the six regions (Moment 2), last light into the neon logo and the date (Moment 3). Each clip is a different colour world, and none repeats a shot from another.

**Why not full-screen three times.** Only Moment 1 is full viewport. Moments 2 and 3 are cinemascope bands because Trailer 2 is 2.22:1; scaling them to full viewport would crop the sides and raise the file size for no gain. Three identical full-screen takeovers would also read as repetition.

**Transitions.** Moment 1 uses a top gradient from the section's ground colour and a bottom fade into the cast section; each clip plays once on entry, then holds its last frame. Moment 3 sits on black: the section above blends to black over 120 px and the clip's own fade-to-black carries the join.

---

## E. Character reel recommendation

**Review of the eight clips (all 1.0 to 1.5 s):**

| Character | Clip quality | Verdict |
|-----------|--------------|---------|
| Jason Duval (16:9, 1.0 s) | Bandana and sunglasses, leaning toward the camera with a gun in a shop. Strong motion. | Good |
| Lucia Caminos (16:9, 1.5 s) | Neon night, looking out of a truck. Rich. | Good |
| Cal Hampton (1:1, 1.0 s) | Bright sky, a plane overhead, little motion. | Acceptable |
| DreQuan Priest (1:1, 1.0 s) | Walks toward the camera in a Manatees jersey. | Good |
| Raul Bautista (1:1, 1.5 s) | Moving through a street with a rifle. Strongest motion of the square clips. | Good |
| Brian Heder (1:1, 1.0 s) | Seated, dim, almost no motion. | Weak |
| Real Dimez (1:1, 1.0 s) | Very dark, face partly hidden. | Weak |
| Boobie Ike (1:1, 1.0 s) | Under-exposed purple bokeh, face barely readable. | **Weakest** |

**Recommended approach (no artificial slow motion):**

1. **Natural speed, then an artwork hold.** Each person plays their clip at 1.0x (1.0 to 1.5 s), dissolves over 0.4 s into their official landscape artwork, and holds it for about 1.6 s with a 4 to 5 percent push-in: **2.6 to 3.1 s per person, 19.7 s for all eight**. A prototype built exactly this way is at `review/design-concepts/reel-natural-speed-prototype.mp4` (4 MB) with a contact sheet beside it.
2. **Square clips are not extended with blur.** The six square clips sit flush right on the stage; the dissolve into the full-frame artwork removes the need for a blurred extension.
3. **Selection is immediate and exact.** Choosing a name seeks to that person's segment, plays it once at natural speed, and rests on the artwork. Names, roles and descriptions come from one ordered manifest so the caption always matches the picture.
4. **Controls.** Pause freezes the current beat; Replay restarts the current person; "Play whole reel" runs the eight in the fixed order. Play whole reel is visible from the first paint.

**Where better source footage would help (the owner has offered additional files):** Boobie Ike, Real Dimez and Brian Heder. Their current clips are too dark or too still to carry a 1.5 s beat. Official clips of those three with the face lit and some movement would raise the whole reel. Cal Hampton would also benefit from a clip with more movement, but he is acceptable.

---

## F. Performance assessment

| | Desktop (balanced) | Desktop (high quality) | Mobile |
|---|---|---|---|
| Moment 1 | 7.1 MB | 10.7 MB | 2.5 MB |
| Moment 2 | about 4.9 MB | 7.3 MB | about 2.6 MB |
| Moment 3 | about 2.2 MB | 3.3 MB | about 0.9 MB |
| **Total if all three play** | **about 14 MB** | **about 21 MB** | **about 6 MB** |
| Posters (three, JPEG) | 0.6 MB | 0.6 MB | 0.6 MB |

* **Initial load:** unchanged. Videos use `preload="none"` and start loading only when the section is within one screen, so the homepage weight on first paint grows only by the three posters if they are in view (they are lazy too).
* **Playback:** one video plays at a time; the rest pause when they leave the viewport. At 8 to 9 s per clip, 1080p H.264 decodes in hardware on every current phone, laptop and iPad.
* **Bandwidth ceiling:** a visitor who scrolls the whole page on desktop downloads at most about 14 to 21 MB, comparable to one large hero image set. Data-saver and 2G/3G visitors get posters only.
* **Quality versus size:** CRF 24 is visually transparent for these clips at normal viewing; CRF 21 retains finer foliage and flock detail at 1.5 times the size. Recommend CRF 23 to 24 with a maximum bitrate cap.
* **Layout shift:** each section reserves its height with `aspect-ratio`; the poster occupies it until the first frame plays.
* **Formats:** H.264 MP4 for all browsers. An AV1 WebM alternative could roughly halve sizes for browsers that support it; not necessary for this project.

---

## G. Implementation plan (not applied)

| Stage | Work | Touches |
|-------|------|---------|
| 0 | Owner confirms provenance and rights of the three sources, confirms the sound policy, and approves the three picks and edit points. | none |
| 1 | `scripts/make_cinematics.py`: reads `media/source-videos/`, applies the exact in/out points and the bar crop, encodes desktop and mobile H.264 and posters into `media/cinematic/` as `moment-1`, `moment-2`, `moment-3` (`.mp4`, `-mobile.mp4`, `.jpg`) plus a manifest. Reproducible; originals never modified. | new script, no app code |
| 2 | Generalise the Gate 2 slot from one to three: `local_media.cinematics()` returns slots by name; `media_slots.CINEMATICS` lists the three specs (poster and trailer fallback slugs, placement text). | `app/local_media.py`, `app/media_slots.py`, `app/services/site.py` |
| 3 | Template: turn the Gate 2 cinematic block into a macro used three times, with a `band` variant (2.22:1) and a black-ground variant for the finale; keep the official-still fallback for each slot. | `app/templates/home.html`, CSS |
| 4 | Script: loop over every `[data-cinema]`, play once then hold the last frame, replay on re-entry, only one playing at a time, one shared sound state, entry and exit fades, reduced-motion and data-saver posters. | `app/static/js/site.js` |
| 5 | Chapter navigation: replace the floating pill with the quiet rail (wide) and a bottom progress hairline (phones). Hero art: pause the cross-fade off-screen; keep three artworks or choose one (see below). Visitor-facing wording: "Watch Official Trailer", detailed attribution on Credits. | `base`/`home` templates, CSS, JS |
| 6 | Tests (slot naming and strict file names, markup states, no third-party player, CSP unchanged), width sweep, and screenshots at desktop, tablet and mobile for the owner's visual review. | `tests/`, `scripts/qa` |

**Database:** no schema change is required. Slots are configured in `media_slots.py`; official stills and trailer links are already `media_assets` rows. An optional later migration could record the three clips' source and timestamps as metadata for attribution; not needed for function.

**Risks:** rights (above); a two-shot composite means an edit of the source (needs the same authorisation as a cut); mobile focal crops need a quick check per shot; the finale shows Rockstar's logo.

---

## Owner decisions on Gate 2 (Part 2): my recommendations

| Topic | Recommendation |
|-------|----------------|
| **Chapter navigation** | Replace the floating "Jump to..." pill with a quiet vertical rail of eight dots at the right edge on screens 1100 px and wider: the active dot shows its number and name, the others name themselves on hover or focus; fully keyboard and screen-reader accessible. Below 1100 px no floating control at all: a 3 px progress hairline on the bottom edge and the header menu. Mock-up: `review/cinematic/hero-and-rail.jpg`. |
| **Hero artwork** | Keeping the three-image cycle is reasonable, but the **Beach** artwork is the strongest single frame for the lockup. If you want one image, choose Beach; if you keep three, hold each for 12 s with a 1.4 s cross-fade (today 9 s), keep Beach first, and pause the cycle when the hero is off screen. Comparison: `review/cinematic/hero-and-rail.jpg`. Reduced-motion visitors already see only the first. |
| **Visible text** | Agreed. Replace "Played in Rockstar's own player" with "Watch Official Trailer" and move the attribution to Credits. A small wording change that can ship with the next gate. |
| **Native foundation** | Kept. The native component stays; no YouTube background implementation will be reintroduced. If permission is unavailable, the public fallback remains the official still and the trailer overlay. |

---

## What I need before anything is built

1. **Where the two trailer files came from and under what terms** (or confirmation that permission has been requested).
2. **Sound policy:** picture-only, or carry the original audio (only if the music rights allow).
3. **Approval of the three picks** (or an alternative), including the two-shot edit for Moment 2.
4. **Hero artwork:** three images or Beach alone.
5. **Optional:** additional official clips for Boobie Ike, Real Dimez and Brian Heder.

Gate 3 and Phase 3 remain unauthorised.

---

## Appendix: draft permission request (not sent)

> Subject: Request to host short muted excerpts of Grand Theft Auto VI trailers on a non-commercial student fan site
>
> Hello, I am a student at [college] building an unofficial, non-commercial educational website about Grand Theft Auto VI for a Web Technologies and database course. It is not monetised, carries a clear non-affiliation notice, and credits Rockstar Games throughout.
>
> I would like permission to host three short, muted excerpts (each under ten seconds, picture only) from the official Trailer 1 and Trailer 2 as background moments on the homepage, with a visible credit and a link to Rockstar's official pages. I would remove them immediately on request.
>
> May I have your permission, or let me know any conditions? Thank you. [name, college, contact]

---

## Update: owner decisions and the four-artwork hero comparison

### Decisions recorded

| Topic | Decision |
|-------|----------|
| Footage | The owner's own recordings, for a classroom presentation; the owner handles permissions. Originals stay local and Git-ignored. Work now focuses on editing and optimisation. |
| Sound | Autoplay with sound where possible, with an elegant Enable sound button (design below). |
| Three moments | Approved: Moment 1 Trailer 1 19.17 to 27.40 s; Moment 2 Trailer 2 6.35 to 9.70 s and 138.15 to 143.65 s; Moment 3 Trailer 2 152.85 to 162.00 s. |
| Character reel | Natural speed, then a brief artwork hold. Existing eight clips kept for now. |
| Navigation | Subtle desktop chapter rail and minimal mobile navigation, provisionally approved. |
| Process | Gate 2 and these visuals still await the owner's review. Nothing is integrated, no Gate 3, no Phase 3. |

### Sound: what a browser allows, and the design that gets closest

Browsers do not permit audible autoplay until the visitor has interacted with the page, so a first scroll-in can only start muted. The design that keeps sound as often as the platform allows:

1. **Before any interaction:** each moment starts muted when it enters the viewport, with a clear "Enable sound" button.
2. **One deliberate click** on Enable sound turns sound on for that clip and **remembers the choice for the visit** (session storage).
3. **Later moments:** once the visitor has interacted with the page and has chosen sound on, the next moments start with sound, faded in over about 0.4 s and faded out when they leave the screen.
4. **Always:** one clip audible at a time, a visible "Sound on" state with one-click mute, no sound while a clip is out of view or the tab is hidden, and a muted fallback if the browser refuses.

The encodes will carry the clips' own stereo audio (AAC, about 96 kb/s, roughly 0.1 MB per clip), so the totals in section F change by under 0.4 MB.

### Hero artwork: four candidates in the real Gate 2 hero

Board: `review/cinematic/hero4-comparison.jpg` (the four artworks as published, then at 1440 px and 390 px in the actual hero).

**Embedded logos or text:** none of the four published artworks carries a logo or caption. The only lettering is in-world (a "HADDIE" shirt print and a petrol-station sign). All four are acceptable on that criterion.

| Artwork | Desktop (lockup on the left) | Phone (subjects at top, text below) | Verdict |
|---------|------------------------------|-------------------------------------|---------|
| **A. Beach** | Both faces large and on the right; the lockup sits on calm sky and the skyline. Warm palette that matches the site. | Both faces visible, the strongest close crop. | **Best single hero** |
| B. 01 | Iconic pair-on-the-car composition but the lockup lands on the bonnet, palms and hotel: busy. | Lucia is cropped out; only Jason's face remains. | Weak in the hero; already the trailer poster |
| C. 02 | Jason aims at the camera and Lucia stands behind him on the left, so **the lockup sits on top of Lucia**. Bright, daytime, teal water. | Lucia is cropped out. | Not suitable behind the lockup |
| **D. Robbery** | The pair walk in from the right; the lockup sits on a dark petrol station, clean and legible. Darker, menacing, stylish. | Lucia (bandana) and Jason both present, with the lockup on dark. | **Best companion to A** |

**Recommendation:** make **A (Beach) the lead image**. If the owner prefers to keep a cycle, use **A then D** only, 12 s each with a 1.4 s cross-fade, paused when the hero is off screen; drop B and C from the hero. B is better used as the Trailer 1 poster and C as a regions or characters banner, where nothing sits on its left. A phone-specific `object-position` per slide (A about 62 percent, D about 30 percent) keeps both characters in frame.

