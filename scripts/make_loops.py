"""Turn the fetched official clips into small, muted, web-friendly loops for LOCAL playback.

    python -m scripts.fetch_clips      # 1. fetch Rockstar's character clips into media/source/
    python -m scripts.make_loops       # 2. build media/clips/ (needs ffmpeg: `pip install imageio-ffmpeg` is enough)

Outputs in media/clips/ (all Git-ignored, never committed):
  <slug>.mp4        one short muted loop per character, 1280x720 (forward then backward, so it loops without a jump)
  <slug>.jpg        a poster frame for each loop
  leonida-reel.mp4  all eight clips cut into one ~10 second muted reel (1280x720, soft blurred extension for the 1:1 clips)
  leonida-reel.jpg  poster for the reel
  manifest.json     the reel's segment times, used by the page to jump to a character

The clips are 1 to 1.5 seconds long at 4K and 50 to 130 Mbps. Each loop is about 0.3 to 1 MB and the reel about 3 MB.
"""
import json
import shutil
import subprocess
import sys

from scripts.fetch_clips import CHARACTER_CLIPS, SOURCE_DIR
from scripts.schema_info import ROOT

CLIPS_DIR = ROOT / "media" / "clips"
SLUGS = {
    "Jason_Duval_Video_Clip": ("jason-duval", "Jason Duval"),
    "Lucia_Caminos_Video_Clip": ("lucia-caminos", "Lucia Caminos"),
    "Cal_Hampton_Video_Clip": ("cal-hampton", "Cal Hampton"),
    "Boobie_Ike_Video_Clip": ("boobie-ike", "Boobie Ike"),
    "DreQuan_Priest_Video_Clip": ("dre-quan-priest", "Dre'Quan Priest"),
    "Real_Dimez_Video_Clip": ("real-dimez", "Real Dimez"),
    "Raul_Bautista_Video_Clip": ("raul-bautista", "Raul Bautista"),
    "Brian_Heder_Video_Clip": ("brian-heder", "Brian Heder"),
}
ENCODE = ["-an", "-c:v", "libx264", "-preset", "slow", "-crf", "27", "-pix_fmt", "yuv420p", "-r", "30", "-movflags", "+faststart"]


def ffmpeg_exe():
    found = shutil.which("ffmpeg")
    if found:
        return found
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        sys.exit("ffmpeg was not found. Install it, or run: pip install imageio-ffmpeg")


def run(ffmpeg, *args):
    subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error", "-y", *args], check=True)


def duration(ffmpeg, path):
    result = subprocess.run([ffmpeg, "-hide_banner", "-i", str(path)], capture_output=True, text=True)
    for line in result.stderr.splitlines():
        if "Duration:" in line:
            h, m, s = line.split("Duration:")[1].split(",")[0].strip().split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    raise RuntimeError(f"could not read the duration of {path}")


def main():
    ffmpeg = ffmpeg_exe()
    missing = [n for n in CHARACTER_CLIPS if not (SOURCE_DIR / f"{n}.mp4").exists()]
    if missing:
        sys.exit("Missing source clips. Run: python -m scripts.fetch_clips")
    CLIPS_DIR.mkdir(parents=True, exist_ok=True)

    manifest, segments, cursor = [], [], 0.0
    for stem in CHARACTER_CLIPS:
        slug, name = SLUGS[stem]
        src = SOURCE_DIR / f"{stem}.mp4"
        length = duration(ffmpeg, src)
        wide = stem in ("Jason_Duval_Video_Clip", "Lucia_Caminos_Video_Clip")

        # A 1280x720 canvas. The 1:1 clips sit in the centre over a blurred, darkened copy of themselves,
        # so every loop and the reel share one frame shape.
        seg = CLIPS_DIR / f"_seg_{slug}.mp4"
        if wide:
            graph = "[0:v]scale=1280:720[v]"
        else:
            graph = ("[0:v]split[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,"
                     "boxblur=30:4,eq=brightness=-0.18[b];[fg]scale=-2:720[f];[b][f]overlay=(W-w)/2:0[v]")
        run(ffmpeg, "-i", str(src), "-filter_complex", graph, "-map", "[v]", *ENCODE, str(seg))

        # Per-character loop: forward then backward, so it repeats without a visible jump.
        run(ffmpeg, "-i", str(seg), "-filter_complex",
            "[0:v]split[a][b];[b]reverse[r];[a][r]concat=n=2:v=1:a=0[v]", "-map", "[v]", *ENCODE,
            str(CLIPS_DIR / f"{slug}.mp4"))
        run(ffmpeg, "-ss", f"{length / 2:.2f}", "-i", str(seg), "-frames:v", "1", "-q:v", "4", str(CLIPS_DIR / f"{slug}.jpg"))
        segments.append(seg)
        manifest.append({"slug": slug, "name": name, "start": round(cursor, 2), "end": round(cursor + length, 2)})
        cursor += length

    listing = CLIPS_DIR / "_reel.txt"
    listing.write_text("".join(f"file '{s.name}'\n" for s in segments), encoding="utf-8")
    run(ffmpeg, "-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", str(CLIPS_DIR / "leonida-reel.mp4"))
    run(ffmpeg, "-ss", "0.4", "-i", str(CLIPS_DIR / "leonida-reel.mp4"), "-frames:v", "1", "-q:v", "4", str(CLIPS_DIR / "leonida-reel.jpg"))
    for s in segments:
        s.unlink()
    listing.unlink()
    (CLIPS_DIR / "manifest.json").write_text(json.dumps({"duration": round(cursor, 2), "segments": manifest}, indent=2), encoding="utf-8")

    total = 0
    for f in sorted(CLIPS_DIR.iterdir()):
        total += f.stat().st_size
        print(f"  {f.name:28s} {f.stat().st_size / 1024:8.0f} KB")
    print(f"Reel length {cursor:.1f}s. Total {total / 1048576:.1f} MB in {CLIPS_DIR}")


if __name__ == "__main__":
    main()
