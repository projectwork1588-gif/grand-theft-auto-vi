"""Turn the fetched official clips into slow, held, web-friendly sequences for LOCAL playback.

    python -m scripts.fetch_clips      # 1. fetch Rockstar's character clips into media/source/
    python -m scripts.make_loops       # 2. build media/clips/ (needs ffmpeg: `pip install imageio-ffmpeg` is enough)

Rockstar's character clips are only 1 to 1.5 seconds long, so each one is given a full beat of screen time:
slowed to about 2.6 seconds of smooth motion (motion-interpolated), then held on its final frame while a slow
push-in continues, 4.0 seconds in all. Square clips sit flush right over a feathered, blurred extension of
themselves (no black bars) and leave the left of the frame free for the caption.

Outputs in media/clips/ (all Git-ignored, never committed):
  leonida-reel.mp4  all eight people in app.media_slots.CAST_ORDER, 0.5 s dissolves between them, ~28.5 s, 1280x720
  leonida-reel.jpg  poster for the reel
  <slug>.mp4/.jpg   one 4 s sequence per person with a short dip to black at each end, for the profile pages
  manifest.json     each person's [start, end) inside the reel, used by the page to keep the caption in step
"""
import json
import shutil
import subprocess
import sys

from app.media_slots import CAST_ORDER
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
# One explicit sequence: the reel is cut in app.media_slots.CAST_ORDER, the same order the homepage lists the cast in.
STEM_BY_SLUG = {slug: stem for stem, (slug, _name) in SLUGS.items()}
SEQUENCE = [STEM_BY_SLUG[slug] for slug in CAST_ORDER]
WIDE = ("Jason_Duval_Video_Clip", "Lucia_Caminos_Video_Clip")  # 16:9 sources; the rest are square

SEGMENT = 4.0        # seconds of screen time per person
MOTION = 2.6         # of which this much is the (slowed) clip; the rest is a held frame with a slow push-in
DISSOLVE = 0.5       # cross-dissolve between people in the reel
PUSH = 0.045         # total slow zoom over a segment
SQUARE_X = 560       # square clips are placed flush right: 1280 - 720
FEATHER = 110        # width of the soft edge where the square meets its extension

INTERMEDIATE = ["-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", "-r", "30"]
FINAL = ["-an", "-c:v", "libx264", "-preset", "slow", "-crf", "26", "-pix_fmt", "yuv420p", "-r", "30",
         "-profile:v", "high", "-movflags", "+faststart"]


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


def compose_filter(wide):
    """Frame composition: full frame for 16:9 sources, flush-right square over a feathered ambient extension."""
    if wide:
        return "[0:v]scale=1280:720:flags=lanczos[c]"
    return (
        "[0:v]split[bg][fg];"
        "[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,gblur=sigma=26,eq=brightness=-0.24:saturation=0.92[b];"
        f"[fg]scale=720:720:flags=lanczos,format=yuva420p,"
        f"geq=lum='lum(X,Y)':cb='cb(X,Y)':cr='cr(X,Y)':a='if(lt(X,{FEATHER}),255*X/{FEATHER},255)'[f];"
        f"[b][f]overlay={SQUARE_X}:0:format=auto[c]"
    )


def build_segment(ffmpeg, src, out, length, wide):
    """4 s: slowed motion, then a held last frame, with a continuous slow push-in over all of it."""
    factor = MOTION / max(length, 0.5)
    hold = SEGMENT - MOTION
    zoom = f"(1+{PUSH}*t/{SEGMENT})"
    graph = (
        compose_filter(wide)
        + f";[c]setpts={factor:.4f}*PTS,minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,"
        f"tpad=stop_mode=clone:stop_duration={hold:.3f},trim=duration={SEGMENT:.3f},setpts=PTS-STARTPTS,"
        f"scale=w='trunc(1280*{zoom}/2)*2':h='trunc(720*{zoom}/2)*2':eval=frame:flags=bicubic,crop=1280:720[v]"
    )
    run(ffmpeg, "-i", str(src), "-filter_complex", graph, "-map", "[v]", *INTERMEDIATE, str(out))


def main():
    ffmpeg = ffmpeg_exe()
    assert sorted(SEQUENCE) == sorted(CHARACTER_CLIPS), "CAST_ORDER must name every character clip exactly once"
    missing = [n for n in SEQUENCE if not (SOURCE_DIR / f"{n}.mp4").exists()]
    if missing:
        sys.exit("Missing source clips. Run: python -m scripts.fetch_clips")
    CLIPS_DIR.mkdir(parents=True, exist_ok=True)

    segments, manifest = [], []
    step = SEGMENT - DISSOLVE
    for index, stem in enumerate(SEQUENCE):
        slug, name = SLUGS[stem]
        src = SOURCE_DIR / f"{stem}.mp4"
        length = duration(ffmpeg, src)
        seg = CLIPS_DIR / f"_seg_{slug}.mp4"
        print(f"  {name}: {length:.2f}s source -> {SEGMENT:.1f}s", flush=True)
        build_segment(ffmpeg, src, seg, length, stem in WIDE)
        segments.append(seg)

        # Profile-page version: dips through black at both ends so it loops without a visible jump.
        run(ffmpeg, "-i", str(seg), "-vf", f"fade=t=in:st=0:d=0.35,fade=t=out:st={SEGMENT - 0.35:.2f}:d=0.35",
            *FINAL, str(CLIPS_DIR / f"{slug}.mp4"))
        run(ffmpeg, "-ss", "1.4", "-i", str(seg), "-frames:v", "1", "-q:v", "3", str(CLIPS_DIR / f"{slug}.jpg"))
        start = round(index * step, 2)
        manifest.append({"slug": slug, "name": name, "start": start, "end": round(start + step, 2)})

    # The reel: dissolves between people. A keyframe sits at the start of every person, so a seek is instant.
    inputs, chain, last = [], [], "[0:v]"
    for seg in segments:
        inputs += ["-i", str(seg)]
    for k in range(1, len(segments)):
        label = f"[x{k}]"
        chain.append(f"{last}[{k}:v]xfade=transition=fade:duration={DISSOLVE}:offset={k * step:.2f}{label}")
        last = label
    total = round(len(segments) * SEGMENT - (len(segments) - 1) * DISSOLVE, 2)
    keyframes = ",".join(f"{m['start']}" for m in manifest)
    run(ffmpeg, *inputs, "-filter_complex", ";".join(chain), "-map", last, "-force_key_frames", keyframes,
        *FINAL, str(CLIPS_DIR / "leonida-reel.mp4"))
    run(ffmpeg, "-ss", "0.6", "-i", str(CLIPS_DIR / "leonida-reel.mp4"), "-frames:v", "1", "-q:v", "3",
        str(CLIPS_DIR / "leonida-reel.jpg"))
    for seg in segments:
        seg.unlink()
    (CLIPS_DIR / "manifest.json").write_text(
        json.dumps({"duration": total, "segment": SEGMENT, "dissolve": DISSOLVE, "segments": manifest}, indent=2),
        encoding="utf-8")

    size = 0
    for f in sorted(CLIPS_DIR.iterdir()):
        size += f.stat().st_size
        print(f"  {f.name:28s} {f.stat().st_size / 1024:8.0f} KB")
    print(f"Reel length {total:.1f}s ({len(segments)} people, {SEGMENT:.1f}s each). Total {size / 1048576:.1f} MB in {CLIPS_DIR}")


if __name__ == "__main__":
    main()
