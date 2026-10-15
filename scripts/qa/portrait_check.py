"""Checks the locally built Characters motion sequences against the rules they are built to (needs media/clips/*-profile.mp4).

    python -m scripts.qa.portrait_check

For every person it reports, measured from the decoded frames (never from file names or metadata):
  * the first frame against the artwork the sequence is supposed to start on (the still is that very frame),
  * the clip's own first and last frame against that artwork (they differ, which is why the sequence dissolves),
  * the resting frame against the artwork,
  * the darkest frame against the darkest of the artwork and the clip (no black flash, no dip),
  * the length and frame rate (a true-speed clip at 30 fps).
Developer tooling only; exit status 1 when a rule is broken.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageChops, ImageStat

from app.media_slots import CAST_ORDER, PORTRAIT_SHAPE
from scripts import make_loops as m

SMALL = 160


def luma(im):
    return im.convert("L")


def mad(a, b):
    """Mean absolute difference of two pictures, 0 (identical) to 255, on a small grayscale copy."""
    a = luma(a).resize((SMALL, SMALL))
    b = luma(b).resize((SMALL, SMALL))
    return ImageStat.Stat(ImageChops.difference(a, b)).mean[0]


def frames(ffmpeg, video, fps, directory):
    pattern = Path(directory) / "f%04d.png"
    subprocess.run([ffmpeg, "-v", "error", "-y", "-i", str(video), "-vf", f"fps={fps},scale={SMALL * 2}:{SMALL * 2}", str(pattern)], check=True)
    return [Image.open(p).convert("RGB") for p in sorted(Path(directory).glob("f*.png"))]


def art_crop(slug, size):
    """The artwork cut to the sequence's shape, the way build_profile cuts it (no push-in)."""
    art = Image.open(m.profile_art(slug)).convert("RGB")
    wide = PORTRAIT_SHAPE.get(slug, "square") == "wide"
    w, h = m.PORTRAIT_SIZE["wide" if wide else "square"]
    art = art.resize((round(art.width * h / art.height), h))
    x = 0 if wide else int(min(max(m.PORTRAIT_FOCUS[slug] * art.width - w / 2, 0), art.width - w))
    return art.crop((x, 0, x + w, h)).resize((SMALL * 2, SMALL * 2))


def check(slug, stem):
    ffmpeg = m.ffmpeg_exe()
    video = m.CLIPS_DIR / f"{slug}-profile.mp4"
    result = {"slug": slug, "problems": []}
    if not video.exists():
        result["problems"].append("sequence not built")
        return result
    clip_len = m.duration(ffmpeg, m.SOURCE_DIR / f"{stem}.mp4")
    total = m.duration(ffmpeg, video)
    expected = clip_len + m.PROFILE_INTRO + m.PORTRAIT_DISSOLVE + m.PORTRAIT_HOLD
    result.update(total=round(total, 2), expected=round(expected, 2), clip=round(clip_len, 2))
    if abs(total - expected) > 0.15:
        result["problems"].append(f"length {total:.2f}s, expected {expected:.2f}s")
    with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as tmp2:
        seq = frames(ffmpeg, video, 30, tmp)
        src = frames(ffmpeg, m.SOURCE_DIR / f"{stem}.mp4", 30, tmp2)
        _grade, gamma = m._grade(ffmpeg, m.SOURCE_DIR / f"{stem}.mp4")
        if gamma > 1.0:                       # compare like with like: the sequence plays the lifted clip
            lut = [round(255 * (v / 255) ** (1 / gamma)) for v in range(256)]
            src = [f.point(lut * 3) for f in src]
        art = art_crop(slug, SMALL * 2)
        result["frames"] = len(seq)
        result["first_vs_art"] = round(mad(seq[0], art), 1)
        result["clip_first_vs_art"] = round(mad(src[0], art), 1)
        result["clip_last_vs_art"] = round(mad(src[-1], art), 1)
        result["rest_vs_art"] = round(mad(seq[-1], art), 1)
        lumas = [ImageStat.Stat(luma(f)).mean[0] for f in seq]
        floor = min(ImageStat.Stat(luma(art)).mean[0], *[ImageStat.Stat(luma(f)).mean[0] for f in src])
        result["darkest_frame"] = round(min(lumas), 1)
        result["darkest_source"] = round(floor, 1)
        if result["first_vs_art"] > 6:
            result["problems"].append("first frame is not the artwork")
        if min(lumas) < floor * 0.85 - 2:
            result["problems"].append("a frame is darker than both the artwork and the clip (a dip or flash)")
        # a hard cut shows as a big jump between neighbouring frames, a dissolve never does
        # (fast footage has big steps of its own, so the sequence is held to the source clip's largest step)
        jumps = [mad(seq[i], seq[i + 1]) for i in range(len(seq) - 1)]
        source_jumps = [mad(src[i], src[i + 1]) for i in range(len(src) - 1)]
        result["largest_step"] = round(max(jumps), 1)
        result["largest_source_step"] = round(max(source_jumps), 1)
        if max(jumps) > max(28, max(source_jumps) * 1.15):
            result["problems"].append("a hard cut between two frames")
        # the dissolve back into the artwork must be even and must finish (no snap at its end)
        first = round((clip_len + m.PROFILE_INTRO) * 30) + 1
        window = [j for j in jumps[first:first + round((m.PORTRAIT_DISSOLVE + 0.1) * 30)] if j > 1.0]
        if window:
            median = sorted(window)[len(window) // 2]
            result["dissolve_even"] = round(max(window) / median, 2)
            if max(window) > 2.0 * median:
                result["problems"].append("the dissolve back snaps at its end")
    return result


def main():
    stems = {slug: stem for stem, (slug, _n) in m.SLUGS.items()}
    results = [check(slug, stems[slug]) for slug in CAST_ORDER]
    for r in results:
        if "frames" not in r:
            print(f"{r['slug']:16s} {'; '.join(r['problems'])}")
            continue
        print(f"{r['slug']:16s} {r['total']:.1f}s (clip {r['clip']:.1f}s whole)  first frame vs artwork {r['first_vs_art']:5.1f}  "
              f"clip first {r['clip_first_vs_art']:5.1f}  clip last {r['clip_last_vs_art']:5.1f}  rest {r['rest_vs_art']:5.1f}  "
              f"darkest {r['darkest_frame']:5.1f} (source floor {r['darkest_source']:5.1f})  biggest step {r['largest_step']:4.1f} "
              f"(source {r['largest_source_step']:4.1f})  dissolve max/median {r.get('dissolve_even', '-')}  "
              f"{'OK' if not r['problems'] else '; '.join(r['problems'])}")
    out = Path(__file__).resolve().parents[2] / "review" / "gate3a" / "final" / "portrait-check.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=1), encoding="utf-8")
    return 1 if any(r["problems"] for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
