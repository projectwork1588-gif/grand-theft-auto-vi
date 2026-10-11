"""Split the homepage hero artwork (Jason and Lucia, Robbery) into three parallax layers for the motion poster.

    python -m scripts.make_hero_layers                      # reads media/source/hero-robbery.png (or .jpg)
    python -m scripts.make_hero_layers path/to/artwork.png  # any 16:9 copy of the same picture
    python -m scripts.make_hero_layers --fetch              # first downloads the picture the site already shows, from Rockstar

Writes media/hero/ (Git-ignored, like every other local derivative; nothing here is ever committed):
  sky.webp   the sky and everything far away, with everything else painted out behind it
  mid.webp   the world: station, vehicles, palms, wires (transparent where the sky is), painted out behind the pair
  fg.webp    Jason and Lucia on their own
  fg-lit.webp  the same figures a little brighter and warmer: the page cross-fades it in and out for the sunset light
  *-1280.webp  lighter copies for phones, and layers.json

Why layers and not a copy of the picture moved around: a copy of the whole picture shifted behind itself ghosts at every
edge. Here each layer holds only its own pixels and the layers behind it are completed under it (a few pixels of the
sky behind the palms, the station behind her legs, the car behind his), so when the camera pushes in and the layers
travel at different speeds the edges reveal believable picture, not a second copy of the figures.

How: the pair is cut out with GrabCut seeded from two rectangles and a traced outline of his trousers (the car sits
against both edges there, so colour alone cannot be trusted); the sky is the large low-gradient, sky-coloured areas of
the picture; everything else is the world. Positions are in 1920 x 1080 picture pixels; the artwork is rescaled to that.
Needs: pip install -r requirements-media.txt (numpy, opencv-python-headless, pillow).
"""
import json
import sys
import urllib.request
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from scripts.schema_info import ROOT

W, H = 1920, 1080
SOURCE_CANDIDATES = [ROOT / "media" / "source" / "hero-robbery.png", ROOT / "media" / "source" / "hero-robbery.jpg"]
OUT_DIR = ROOT / "media" / "hero"
ARTWORK_URL = ("https://www.rockstargames.com/VI/_next/static/media/Jason_and_Lucia_Robbery_landscape.09c8a~do21h4p.jpg"
               "?akim=1&imdensity=1&imwidth=1920")
SMALL_W = 1280


def kernel(r):
    return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))


# ---------------------------------------------------------------------------------------------------- the pair
def figures_mask(img):
    """Binary mask (0/255) of Jason and Lucia."""
    rect = (700, 20, 960, 1060)
    mask = np.zeros((H, W), np.uint8)
    bgd = np.zeros((1, 65), np.float64)
    fgd = np.zeros((1, 65), np.float64)
    cv2.grabCut(img, mask, rect, bgd, fgd, 6, cv2.GC_INIT_WITH_RECT)
    first = np.where((mask == 1) | (mask == 3), 255, 0).astype(np.uint8)

    # second pass: the first result seeds a trimap, and known trouble spots are pinned
    mask = np.full((H, W), cv2.GC_BGD, np.uint8)
    mask[cv2.dilate(first, kernel(28)) > 0] = cv2.GC_PR_BGD
    mask[first > 0] = cv2.GC_PR_FGD
    mask[cv2.erode(first, kernel(10)) > 0] = cv2.GC_FGD

    def pin(label, x0, y0, x1, y1):
        mask[y0:y1, x0:x1] = label

    pin(cv2.GC_BGD, 1490, 770, 1920, 1080)      # the car, right of Jason
    pin(cv2.GC_BGD, 1165, 850, 1215, 965)       # its tail, left of his leg
    pin(cv2.GC_BGD, 560, 860, 880, 1000)        # pumps and forecourt left of Lucia's leg
    pin(cv2.GC_BGD, 600, 1000, 900, 1080)       # pavement
    pin(cv2.GC_BGD, 1180, 790, 1203, 1000)      # the gap between her leg and his
    pin(cv2.GC_BGD, 1160, 840, 1214, 960)
    pin(cv2.GC_BGD, 1160, 960, 1245, 1045)
    pin(cv2.GC_BGD, 1442, 830, 1500, 960)       # the car's tail lights, right of his leg
    pin(cv2.GC_BGD, 1458, 960, 1500, 1050)
    pin(cv2.GC_FGD, 970, 410, 1100, 530)        # the grey hoodie and the denim, which look like the canopy
    pin(cv2.GC_FGD, 950, 650, 1110, 770)

    # his trousers, traced: the car is right against both edges, so a band around the outline decides, not colour
    outline = np.array([(1212, 640), (1215, 720), (1218, 800), (1228, 880), (1248, 960), (1285, 1040), (1315, 1085),
                        (1433, 1085), (1437, 1040), (1437, 960), (1442, 880), (1464, 800), (1484, 720), (1490, 640)], np.int32)
    poly = np.zeros((H, W), np.uint8)
    cv2.fillPoly(poly, [outline], 255)
    inner, outer = cv2.erode(poly, kernel(5)), cv2.dilate(poly, kernel(5))
    zone = np.zeros((H, W), np.uint8)
    zone[640:800, 1206:1560] = 255
    zone[800:, 1178:1560] = 255
    mask[(zone > 0) & (outer == 0)] = cv2.GC_BGD
    mask[(zone > 0) & (outer > 0) & (poly == 0)] = cv2.GC_PR_BGD
    mask[(zone > 0) & (poly > 0)] = cv2.GC_PR_FGD
    mask[(zone > 0) & (inner > 0)] = cv2.GC_FGD

    cv2.grabCut(img, mask, None, bgd, fgd, 6, cv2.GC_INIT_WITH_MASK)
    out = np.where((mask == 1) | (mask == 3), 255, 0).astype(np.uint8)
    # no islands, no pin-holes
    n, lab, stats, _ = cv2.connectedComponentsWithStats(out, connectivity=8)
    keep = np.zeros_like(out)
    for i in range(1, n):
        if stats[i, cv2.CC_STAT_AREA] > 1500:
            keep[lab == i] = 255
    n, lab, stats, _ = cv2.connectedComponentsWithStats(255 - keep, connectivity=4)
    for i in range(1, n):
        if stats[i, cv2.CC_STAT_AREA] < 400:
            keep[lab == i] = 255
    return keep


# ---------------------------------------------------------------------------------------------------- the sky
def sky_mask(img, fg):
    """Binary mask (0/255) of the sky. Sky is the big, smooth, sky-coloured areas; the rest of the picture is the world."""
    blur = cv2.GaussianBlur(img, (0, 0), 1.0)
    lab = cv2.cvtColor(blur, cv2.COLOR_BGR2LAB).astype(np.float32)
    gx = cv2.Sobel(lab, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(lab, cv2.CV_32F, 0, 1, ksize=3)
    grad = np.sqrt((gx ** 2 + gy ** 2).sum(axis=2))
    hsv = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)
    hue, sat, val = hsv[..., 0].astype(np.int32) * 2, hsv[..., 1], hsv[..., 2]
    low = ((grad < 18) & (cv2.dilate(fg, np.ones((7, 7), np.uint8)) == 0)).astype(np.uint8)
    low[880:, :] = 0                                  # below the horizon is ground
    low[790:, 1180:] = 0                              # and the car
    n, cc, stats, _ = cv2.connectedComponentsWithStats(low, connectivity=4)
    sky = np.zeros((H, W), np.uint8)
    for i in range(1, n):
        area = stats[i, cv2.CC_STAT_AREA]
        if area < 1500:
            continue
        m = cc == i
        h, s, v = np.median(hue[m]), np.median(sat[m]), np.median(val[m])
        skylike = h >= 255 or h <= 30 or 255 <= h <= 330 or (245 <= h < 255 and s > 70)
        top = stats[i, cv2.CC_STAT_TOP] == 0
        # palm silhouettes are sky-coloured but darker than any sky: keep them out of the sky
        if skylike and (top or (area > 3000 and v >= 175)):
            sky[m] = 255
    # slivers of sky the pair's outline cut off (between an arm and a head, along an edge): small components whose colour is
    # what the sky around them would be there. The expected sky is the big sky continued into the gaps.
    expected = fill(img, np.where(sky > 0, 0, 255).astype(np.uint8), radius=5, scale=0.5)
    elab = cv2.cvtColor(expected, cv2.COLOR_BGR2LAB).astype(np.float32)
    ilab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB).astype(np.float32)
    away = np.sqrt(((elab - ilab) ** 2).sum(axis=2))
    rest = np.where((sky == 0) & (cv2.dilate(fg, np.ones((5, 5), np.uint8)) == 0), 255, 0).astype(np.uint8)
    n, cc, stats, _ = cv2.connectedComponentsWithStats(rest, connectivity=8)
    for i in range(1, n):
        x, y, w, h, area = stats[i]
        if area < 25000 and y + h < 840:
            m = cc == i
            if np.median(away[m]) < 16 and np.percentile(away[m], 85) < 30:
                sky[m] = 255
    # and the ring along the pair's outline, which the gradient test kept away from: whatever there is the colour the
    # sky is expected to be, is sky (the station and the car are nothing like it)
    ring = cv2.dilate(fg, kernel(14)) > 0
    sky[ring & (fg == 0) & (away < 14)] = 255
    # the plane, the birds and the contrail are far away too: small things high in the picture belong to the sky
    world = 255 - sky
    n, cc, stats, _ = cv2.connectedComponentsWithStats(world, connectivity=8)
    for i in range(1, n):
        x, y, w, h, area = stats[i]
        if area < 5000 and y + h < 760 and not np.logical_and(cv2.dilate((cc == i).astype(np.uint8), kernel(2)) > 0, fg > 0).any():
            sky[cc == i] = 255
    # edge pixels between the two are blends: let the sky take back none of them, but close one-pixel pin-holes
    sky = cv2.morphologyEx(sky, cv2.MORPH_OPEN, kernel(1))
    return sky


# ---------------------------------------------------------------------------------------------------- filling
def fill(img, hole, radius=5, scale=0.5):
    """Paint hole (0/255) out of img from its surroundings. Done at half size and put back: only a thin band at the
    edge of a hole is ever seen, and the large middle is hidden behind the layer in front."""
    small = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    hs = cv2.resize(hole, (small.shape[1], small.shape[0]), interpolation=cv2.INTER_NEAREST)
    done = cv2.inpaint(small, hs, radius, cv2.INPAINT_TELEA)
    big = cv2.resize(done, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_CUBIC)
    out = img.copy()
    out[hole > 0] = big[hole > 0]
    return out


def rgba(bgr, alpha):
    return Image.fromarray(np.dstack([cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB), alpha]), "RGBA")


def save(image, path, quality):
    image.save(path, "WEBP", quality=quality, alpha_quality=100, method=6)
    size = Path(path).stat().st_size
    print(f"  {Path(path).name:18s} {size / 1024:7.0f} KB", flush=True)


def build(source, out_dir=OUT_DIR, debug_dir=None):
    img = cv2.imread(str(source), cv2.IMREAD_COLOR)
    if img is None:
        sys.exit(f"Could not read {source}")
    if (img.shape[1], img.shape[0]) != (W, H):
        if abs(img.shape[1] / img.shape[0] - W / H) > 0.01:
            sys.exit("The artwork must be 16:9")
        img = cv2.resize(img, (W, H), interpolation=cv2.INTER_AREA if img.shape[1] > W else cv2.INTER_CUBIC)
    out_dir.mkdir(parents=True, exist_ok=True)

    print("the pair ...", flush=True)
    fg = figures_mask(img)
    print("the sky ...", flush=True)
    sky = sky_mask(img, fg)

    # --- figures: the mask grown by 3 px. GrabCut's edge sits inside the pale rim light and the dark outline the painter
    # put around the pair; taking those few pixels with the figures means nothing of them is left behind as a halo when
    # the figures travel. Those pixels are sky or backdrop coloured anyway, so they ride along unseen.
    fg_full = cv2.dilate(fg, kernel(3))
    alpha_fg = cv2.GaussianBlur(fg_full, (0, 0), 0.8)
    fg_rgb = img.copy()

    # --- the world: everything that is not sky, with the pair painted out of it
    pair_hole = cv2.dilate(fg_full, kernel(2))
    known_world = (sky == 0) & (pair_hole == 0)
    # behind the pair: each hidden pixel takes sky or world from the nearest visible pixel (never from far away, so no
    # island of world can appear in the middle of the sky behind the figures)
    label = np.where(sky > 0, 0, 255).astype(np.uint8)
    unknown = np.where(pair_hole > 0, 255, 0).astype(np.uint8)
    _, near = cv2.distanceTransformWithLabels(unknown, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
    visible = np.flatnonzero(unknown == 0)
    world_alpha = label.reshape(-1)[visible[near - 1].reshape(-1)].reshape(H, W)
    # above the horizon of the station and the car there is only sky behind the upper bodies
    world_alpha[:600][pair_hole[:600] > 0] = 0
    mid_src = img.copy()
    mid_hole = np.where(known_world, 0, 255).astype(np.uint8)       # sky and the pair are both "unknown" for the world
    mid_rgb = fill(mid_src, mid_hole, radius=5)
    alpha_mid = cv2.GaussianBlur(world_alpha, (0, 0), 0.7)

    # --- the sky: everything else painted out of it (a little past each edge, where pixels are blends)
    sky_hole = cv2.dilate(np.where(sky > 0, 0, 255).astype(np.uint8), kernel(2))
    sky_rgb = fill(img, sky_hole, radius=5)

    # the pair in warmer, stronger sunlight: lifted and nudged toward amber, same edge
    lit = fg_rgb.astype(np.float32) * 1.16
    lit[..., 2] += 10      # red (BGR order)
    lit[..., 0] -= 8       # blue
    fg_lit = np.clip(lit, 0, 255).astype(np.uint8)
    sets = {"sky": Image.fromarray(cv2.cvtColor(sky_rgb, cv2.COLOR_BGR2RGB), "RGB"), "mid": rgba(mid_rgb, alpha_mid), "fg": rgba(fg_rgb, alpha_fg),
            "fg-lit": rgba(fg_lit, alpha_fg)}
    print("writing ...", flush=True)
    for name, image in sets.items():
        save(image, out_dir / f"{name}.webp", 90 if name != "sky" else 88)
        small = image.resize((SMALL_W, round(SMALL_W * H / W)), Image.LANCZOS)
        save(small, out_dir / f"{name}-{SMALL_W}.webp", 86)
    (out_dir / "layers.json").write_text(json.dumps({"width": W, "height": H, "layers": ["sky", "mid", "fg", "fg-lit"]}), encoding="utf-8")

    # --- self-check: the three layers stacked, untouched, must give the artwork back
    stack = sky_rgb.astype(np.float32)
    for rgb, a in ((mid_rgb, alpha_mid), (fg_rgb, alpha_fg)):
        a3 = (a.astype(np.float32) / 255.0)[..., None]
        stack = rgb.astype(np.float32) * a3 + stack * (1 - a3)
    diff = np.abs(stack - img.astype(np.float32))
    mse = float((diff ** 2).mean())
    psnr = 99.0 if mse == 0 else 10 * np.log10(255 ** 2 / mse)
    print(f"stacked layers against the artwork: PSNR {psnr:.1f} dB, worst pixel {diff.max():.0f}", flush=True)

    if debug_dir:
        debug_dir.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(debug_dir / "fg-mask.png"), fg)
        cv2.imwrite(str(debug_dir / "sky-mask.png"), sky)
        cv2.imwrite(str(debug_dir / "stack.png"), np.clip(stack, 0, 255).astype(np.uint8))
        for tag, (dx, dy, mx) in {"push": (-10, 0, 0), "pull": (10, 0, 0)}.items():
            canvas = sky_rgb.astype(np.float32)
            for rgb, a, ox in ((mid_rgb, alpha_mid, mx), (fg_rgb, alpha_fg, dx)):
                M = np.float32([[1, 0, ox], [0, 1, dy]])
                rs = cv2.warpAffine(rgb, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE).astype(np.float32)
                a3 = (cv2.warpAffine(a, M, (W, H), flags=cv2.INTER_LINEAR).astype(np.float32) / 255.0)[..., None]
                canvas = rs * a3 + canvas * (1 - a3)
            cv2.imwrite(str(debug_dir / f"stress-{tag}.png"), np.clip(canvas, 0, 255).astype(np.uint8))
    return out_dir


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    source = Path(args[0]) if args else next((p for p in SOURCE_CANDIDATES if p.exists()), None)
    if "--fetch" in argv:
        target = SOURCE_CANDIDATES[1]
        target.parent.mkdir(parents=True, exist_ok=True)
        print(f"downloading the artwork the site already shows -> {target}", flush=True)
        request = urllib.request.Request(ARTWORK_URL, headers={"User-Agent": "Mozilla/5.0 (Team Valkyrie fan project)"})
        with urllib.request.urlopen(request, timeout=60) as response:
            target.write_bytes(response.read())
        source = target
    if source is None or not Path(source).exists():
        sys.exit("No artwork. Put a 16:9 copy at media/source/hero-robbery.png, or run with --fetch.")
    debug = ROOT / "media" / "hero" / "debug" if "--debug" in argv else None
    build(Path(source), OUT_DIR, debug)


if __name__ == "__main__":
    main(sys.argv[1:])
