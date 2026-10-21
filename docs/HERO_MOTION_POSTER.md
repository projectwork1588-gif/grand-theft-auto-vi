# Hero motion poster

The homepage hero artwork (Jason and Lucia, Robbery) behaves like an animated loading-screen poster: a very slow push-in
with real depth, a little atmosphere, and nothing else. The lockup, buttons and layout are unchanged.

## What it is

| Part | How |
|------|-----|
| **Layers** | The artwork is cut into **sky** (sky and everything far away), **world** (station, vehicles, palms, wires) and **the pair**. Each holds only its own pixels and the layers behind are completed under it (sky behind the palms and wires, station and car behind her legs and his), so edges that separate reveal believable picture, never a second copy. Built by `scripts/make_hero_layers.py`. |
| **Camera** | **Retuned 21 October 2026 (the first version, 26 s each way, read as nearly still):** an arrival (a 2.6 s decelerating pull from a slightly tighter frame, on `transform`) and then a breath (sky 1.035, world 1.06, pair 1.095 at the fullest, plus 2 / 6 / 12 px of lateral travel), 12 s each way (10 s on phones), eased, alternating, on the separate `scale` and `translate` properties so the two never fight. The timings are the variables `--arrive` and `--dolly` on `.hero__stage`; `site.css` reads the same variables for a visitor who opts in to motion on a reduced-motion system. The layers fade in together once decoded (`is-ready`) and are only promoted to the GPU while they move. The original description follows: one slow push-in. Each layer scales and travels together from rest (sky 1.025, world 1.045, pair 1.07 at the fullest, plus 1.5 / 4 / 9 px of lateral travel), 26 s each way, eased, alternating, so it breathes in and out with no seam. The zoom is anchored at the top so Jason's hair never leaves the card. |
| **Atmosphere** | A soft haze of pink and lavender drifting slowly behind the world (41 s), and a sunset glow low behind the station that rises and falls (13 s). Plain gradients, no blend modes. |
| **Light on the pair** | A pre-warmed copy of the cut-out pair cross-fades over them (up to 34 percent, in step with the glow): the figures catch a little more warm light when it is strongest. An opacity change only. |

## How the layers were made

* **The pair:** GrabCut, seeded from two rectangles, pinned on known trouble spots (the car's tail lights sit right
  against both of his legs) and with his trousers traced as an outline. The mask is grown by 3 px so the painter's dark
  outline and pale rim light travel with the figures; no halo is left behind.
* **The sky:** the large smooth sky-coloured areas, plus slivers the outline cut off (between an arm and a head) judged by
  how close they are to the colour the sky should be there. Palm silhouettes are sky-coloured but darker, so they stay
  in the world.
* **Completing what is hidden:** Telea inpainting (at half size; only a thin band at the edge of a hidden area is ever
  seen). Behind the pair, each hidden pixel takes sky or world from its nearest visible neighbour, and above the
  station roofline it is always sky.
* **Checks that gate the build:** the three layers stacked untouched reproduce the artwork (PSNR 46 dB; what differs is the
  one-pixel feather at the figures' edge), and a stress test slides the pair 14 px against the world (the page never
  exceeds about 9) with no ghost, cut-out edge or smear.

## Rules it follows

* Runs only when motion is allowed: the same switch as the footage (`html.motion-on`). A reduced-motion or data-saver
  visitor, or one who switched autoplay off, gets the still artwork, at rest, identical to the previous hero.
* Pauses when the hero is off screen and when the tab is hidden.
* Phones: push-in and depth only (no haze, no light pass, smaller travel), the 1280-px layers.
* No audio, no controls. The three cinematic sections are untouched.

## Left out, on purpose

* **Palm sway:** the palms share a layer with the station and the wires cross them, their trunks vanish behind the
  canopy; swaying them without a visible seam is not reliable at this resolution.
* **Hair and cloth movement:** the figures are painted single images; moving parts of them would distort faces, hands or
  bandanas. A light pass was used instead.

## Measured (visible Chrome, 12 s each)

| Size | Frames | Frame time median / p95 / worst | Frames over 20 ms | Main thread busy | Layout shift |
|------|--------|-------------------------------|------------------|------------------|--------------|
| Desktop 1440 x 900 | 719 | 16.7 / 16.8 / 18.7 ms | 0 | 16.7 % | 0 |
| Tablet 820 x 1180 | 719 | 16.7 / 16.8 / 16.8 ms | 0 | 10.8 % | 0 |
| Phone 390 x 844 at 2x | 719 | 16.7 / 16.8 / 16.8 ms | 0 | 9.4 % | 0 |

An earlier version used blend modes and a CSS filter for the atmosphere and the light pass; it ran at about 47 fps on
desktop (154 of 564 frames over 20 ms). Replacing them with plain gradients and a pre-warmed image restored 60 fps.

Page weight (WebP): sky 21 KB, world 151 KB, pair 144 KB, warm pair 154 KB on desktop (about 470 KB); 11 / 102 / 76 / 80 KB for phones (about 270 KB, the warm copy is not loaded there).
