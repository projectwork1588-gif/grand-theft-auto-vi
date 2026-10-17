r"""Check that review recordings really contain what they claim: no blank stretches, and picture that changes over time.

    .venv\Scripts\python.exe scripts/qa/recording_check.py review/some/recordings/ [--fps 4]

Every mp4 in the folder is decoded (with the ffmpeg bundled in imageio-ffmpeg), sampled a few times a second, and each sample is
measured: a frame is "blank" when it is almost one flat colour (its pixel spread is tiny), and a video fails when it has any blank
sample, a blank run, or fewer than three distinct moments (a recording that never changes is not evidence of motion).
The result is written to recording-check.txt in the same folder and the exit status is 1 on any failure.
"""
import pathlib, subprocess, sys, tempfile
from PIL import Image, ImageStat, ImageChops

ROOT = pathlib.Path(__file__).resolve().parents[2]
FFMPEG = next((ROOT / ".venv/Lib/site-packages/imageio_ffmpeg/binaries").glob("ffmpeg*"), "ffmpeg")
BLANK_SPREAD = 4.0     # standard deviation of a grey version of the frame, 0..255; real pages are far above this
CHANGED = 2.0          # mean absolute difference between two samples that counts as "the picture changed"


def check(video, fps):
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([str(FFMPEG), "-hide_banner", "-loglevel", "error", "-i", str(video), "-vf", f"fps={fps},scale=320:-2", f"{tmp}/%05d.png"], check=True)
        files = sorted(pathlib.Path(tmp).glob("*.png"))
        spreads, diffs, prev = [], 0, None
        blank_idx = []
        for i, f in enumerate(files):
            im = Image.open(f).convert("L")
            spread = ImageStat.Stat(im).stddev[0]
            spreads.append(spread)
            if spread < BLANK_SPREAD:
                blank_idx.append(i)
            if prev is not None and ImageStat.Stat(ImageChops.difference(prev, im)).mean[0] > CHANGED:
                diffs += 1
            prev = im
    longest = run = 0
    last = -2
    for i in blank_idx:
        run = run + 1 if i == last + 1 else 1
        longest, last = max(longest, run), i
    return {"samples": len(files), "blank": len(blank_idx), "longest_blank_run": longest, "changes": diffs, "min_spread": min(spreads) if spreads else 0}


def main():
    folder = pathlib.Path(sys.argv[1])
    fps = float(sys.argv[sys.argv.index("--fps") + 1]) if "--fps" in sys.argv else 4
    lines, failed = [f"Recording check (sampled at {fps:g} frames a second; blank = pixel spread under {BLANK_SPREAD})", ""], False
    for v in sorted(folder.glob("*.mp4")):
        r = check(v, fps)
        ok = r["blank"] == 0 and r["changes"] >= 3
        failed |= not ok
        lines.append(f"{'PASS' if ok else 'FAIL'}  {v.name}: {r['samples']} samples, {r['blank']} blank, longest blank run {r['longest_blank_run']}, {r['changes']} moments where the picture changed, lowest spread {r['min_spread']:.1f}")
    (folder / "recording-check.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    sys.exit(1 if failed else 0)


main()
