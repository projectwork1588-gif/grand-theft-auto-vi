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
