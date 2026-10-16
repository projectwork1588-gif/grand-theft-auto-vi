# Gate 3A: Characters, final pass

## One canonical cast order

`media_slots.CHARACTERS_ORDER` is the only definition of the Characters section's order:

    Jason Duval, Lucia Caminos, Cal Hampton, Brian Heder, Boobie Ike, Dre'Quan Priest, Real Dimez, Raul Bautista

The landing cards and their numbers, the jump bar, the Explore default (`sort=cast`, built with a bound `FIELD()`
parameter list, never string-built), the previous and next cards (circular), the footer list and the `NN / 08`
numbers all read it. It is a presentation order only: relationships come from `character_relationships`. The homepage
reel keeps its own `CAST_ORDER`. The API stays alphabetical by default and offers `?sort=cast`.

## Images

Every crop is computed, not hand-tuned: `media_slots.IMAGE_FACE` holds where the face sits in each picture and
`site.frame_pos()` turns it into an `object-position` for the box the picture fills (hero, spread, card, second picture,
phone). The CSS has one grid of rules (X in 2s, Y in 5s) because the CSP forbids inline styles; tests prove every
computed crop lands on it and that no head is cropped out.

Per person (`CHARACTER_STAGE`): `main` (the artwork the motion sequence rests on and the large story picture), `hero`
(the full-bleed opening; never the same picture as `main`), `card` (the landing picture) and `second` (the overlapping
picture). The leads' landing picture is their hero, not the artwork their tile rests on, so the resting tile is
complementary instead of a copy. Every profile now opens full bleed (the words on the side the person is not); the old
framed split hero is gone.

| | Hero | Large (rests on) | Overlapping |
|---|---|---|---|
| Jason | car interior | motorcycle artwork | patterned shirt |
| Lucia | gym | pool | neon car |
| Cal | golf | illustrated boat | pool table |
| Brian | night bar | illustrated boat yard | car |
| Boobie | armchair | illustrated club | Jack of Hearts, phone |
| Dre'Quan | Dreams neon, blue suit | illustrated Jack of Hearts | with Bae-Luxe and Roxy |
| Real Dimez | Roxy, studio | illustrated duo | both women (with Dre'Quan) |
| Raul | driving | illustrated mural | phone close-up |

Deliberate repetition: the screenshot of Dre'Quan between Bae-Luxe and Roxy is Dre'Quan's overlapping picture, Real
Dimez's overlapping picture and Real Dimez's landing card. It is the one official screenshot that shows both women
clearly, and it shows the label with its artists; Real Dimez's is cut wide (4:3) and larger so both stay in it.

## Relationship portraits

Faces cut from Rockstar's character artwork (`media_slots.AVATARS`): the illustrations, so the eight portraits have the
same lighting and weight (the earlier scene screenshots were dark and showed scenery). Each face is placed from its
position and the head's height, so every head fills the same share of its circle. Real Dimez, a duo, has two overlapping
circles. The same macro draws the connection cards on the profiles and the phone list (which now also shows Raul as
"No stated connection yet", with no line invented).

## Verified in the browser

`scripts/qa/cast_navigation.mjs` clicks all eight Previous and all eight Next cards, checks the labels, numbers,
footer lists, jump bar and Explore order (52 checks). `scripts/qa/motion_scenarios.mjs` and `motion_timeline.mjs` cover
the 16 playback contexts. See the review pack.

## Acceptance correction (replay, portraits, Real Dimez hero)

* **Replay.** Each landing and profile tile is a state machine (`data-state`: armed, playing, rested). A finished tile
  is re-armed when it has genuinely left the view (under 2% visible, the sticky bars counting as covering the top of the
  screen) and plays once again on the next visit; staying near it never replays it. Entry needs half the tile for 380 ms,
  so scrolling past does not start and stop clips. Tiles in view together play one after another (rows in the direction of
  travel, left to right in a row). `scripts/qa/motion_replay.mjs` traces down, up, down, up with a play count per visit.
  The earlier rule ("a finished tile never replays in the same page visit") was the cause of the missed replays.
* **Portraits.** Heads are read by eye from the pictures at full resolution (`media_slots.AVATARS`: head centre and height,
  optional zoom, and the colour of the picture's top edge for heads at the very top). One macro (`avatar`) draws the network,
  the connection cards and the phone list; Raul is no longer dimmed (only his ring and name are quieter).
* **Real Dimez hero.** The official artwork of both women (Bae-Luxe: braids, "BL" chain; Roxy: curls, "ROXY" chain), words on the
  left; on screens under 901 px the picture is drawn wider than the screen and not cropped, so both stay in. The story's large
  picture rests on the same artwork (the one deliberate repeat): there is no other official picture of the duo that is clear,
  bright and wide enough for a hero, and the screenshot with Dre'Quan between them would make him the subject.
* **Brian's 2.91 s.** The old instrumentation attached its listeners after playback had begun (the first event it saw was at
  video time 0.92 s), so the wall time was measured from mid-clip. It now listens on `document` from document start.

## Final cleanup (profile content and focus)

* **Dre'Quan Priest.** The overlapping picture in "The story so far" is now a tall cut of his own official solo screenshot
  (`shot-dequan-priest-02`, blue jacket at the pool bar), not the one with Bae-Luxe and Roxy beside him. His hero is the wide frame
  of the same screenshot, the one deliberate repeat on his page: no other official picture shows him alone.
* **Real Dimez.** The overlapping picture is gone (`second` is `None` in `media_slots.CHARACTER_STAGE`); the large picture is the
  official artwork of both women, with the layout's room for the overhang removed (`.p-media[data-solo]`). The only other pictures are
  the screenshot with Dre'Quan between them, a single woman, and a crowd scene where the women are small.
* **Gallery.** "From the footage and artwork" is off for Real Dimez (`media_slots.NO_GALLERY`); Jason and Lucia keep it.
* Tests: `test_overlap_pictures_keep_the_profiles_subject`, `test_dre_quans_story_shows_him_not_the_duo`,
  `test_real_dimez_story_has_the_duo_alone_and_no_gallery`, `test_jason_and_lucia_keep_their_gallery`.

## Three image corrections (after the owner's review of 852dd2c)

* **Real Dimez, /characters.** The large picture is the official artwork of both women (`art-real-dimez`), not the screenshot with
  Dre'Quan between them. A frame of the duo's own clip was tried first and is stronger on a desktop, but Bae-Luxe stands at the very
  left edge of every frame of that clip, which is where the IN MOTION tile sits, so at 820 and 390 px the tile hides her.
* **Real Dimez, profile.** The overlapping picture is back: frame 10 (0-based, 0.33 s) of `Real_Dimez_Video_Clip.mp4`, both women and
  nobody else, shown 4:3 (`real-dimez-duo.jpg`). Real Dimez still has no "From the footage and artwork" gallery.
* **Dre'Quan Priest.** The overlapping picture is frame 13 (0.43 s) of `DreQuan_Priest_Video_Clip.mp4` cut 4:5 around him
  (`dre-quan-priest-studio.jpg`): the recording studio, the Manatees jersey, a different scene from the pool-bar hero.
* The frames are built locally, like the sequences: `python -m scripts.make_loops --stills` (media/clips/, Git-ignored, graded like the
  clips that play on the same pages: gamma 1.7). Until they exist the pages show what 852dd2c showed (Dre'Quan: a tall cut of his
  pool-bar screenshot; Real Dimez: the duo artwork alone). `shot` draws such a frame from `media/clips/` (`m.local`).
