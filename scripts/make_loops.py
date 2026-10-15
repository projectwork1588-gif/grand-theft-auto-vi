"""Turn the fetched official clips into a natural-speed reel and per-person sequences for LOCAL playback.

    python -m scripts.fetch_clips      # 1. fetch Rockstar's character clips into media/source/
    python -m scripts.make_loops       # 2. build media/clips/ (needs ffmpeg: `pip install imageio-ffmpeg` is enough)
    python -m scripts.make_loops --posters   # only redo the per-person poster stills from the built sequences
    python -m scripts.make_loops --portraits # the Characters pages' portraits: each person in the shape it was shot in
                                             # (a listing set and a profile set; also fetches Lucia's main artwork once)

Rockstar's character clips are only 1 to 1.5 seconds long. Each person gets a short, elegant beat and no artificial
slow motion: the clip plays at its true speed (SPEED is 1.0), dissolves over 0.4 s into the person's official artwork,
and the artwork is held for a moment with a very slow push-in. That is 2.6 to 3.1 seconds per person.
Square clips sit flush right over a feathered, blurred extension of themselves (no black bars) and leave the left of the
frame free for the caption. The artwork is fetched once from Rockstar's own site into media/source/art/.

Outputs in media/clips/ (all Git-ignored, never committed):
  leonida-reel.mp4  all eight people in app.media_slots.CAST_ORDER, 0.3 s dissolves between them, about 20 s, 1600x900
  leonida-reel.jpg  poster for the reel
  <slug>-portrait.mp4/.jpg   the Characters landing tiles: the clip in its own shape, dissolving into the artwork
  <slug>-profile.mp4/.jpg    the large picture of "The story so far" on each profile: it starts on the artwork (the .jpg
                    is that very frame), dissolves into the clip, plays it whole at true speed, dissolves back
  <slug>.mp4/.jpg   one sequence per person with a short dip to black at each end, for the profile pages. The .jpg is the
                    poster: the clip's own frame at POSTER_AT, lifted towards a readable brightness (a few of the clips
                    are very dark scenes), never the black first frame
  manifest.json     each person's [start, end) inside the reel, used by the page to keep the caption in step
"""
import json
import math
import shutil
import subprocess
import sys
import urllib.request

from app.media_slots import CAST_ORDER, PORTRAIT_POSTER_AT, PORTRAIT_SHAPE
from scripts.fetch_clips import CHARACTER_CLIPS, SOURCE_DIR
from scripts.schema_info import ROOT

CLIPS_DIR = ROOT / "media" / "clips"
ART_DIR = SOURCE_DIR / "art"
ART_BASE = "https://www.rockstargames.com/VI/_next/static/media/"
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
# The official artwork each person dissolves into (the same pictures the stage shows for that person).
ARTWORK = {
    "jason-duval": "Jason_Duval_01.07m377xeb6jhq.jpg",
    "lucia-caminos": "Lucia_Caminos_03.14xgd2y_ymmeg.jpg",
    "cal-hampton": "Cal_Hampton_landscape.17k7bnt3myg.2.jpg",
    "boobie-ike": "Boobie_Ike_landscape.0ldnbn87k-8mq.jpg",
    "dre-quan-priest": "DreQuan_Priest_landscape.0_b7hszyze6cy.jpg",
    "real-dimez": "Real_Dimez_landscape.0637akp_a5a_q.jpg",
    "raul-bautista": "Raul_Bautista_landscape.11_3hd0fr69~j.jpg",
    "brian-heder": "Brian_Heder_landscape.0a-egj5b8yo1q.jpg",
}
# One explicit sequence: the reel is cut in app.media_slots.CAST_ORDER, the same order the homepage lists the cast in.
STEM_BY_SLUG = {slug: stem for stem, (slug, _name) in SLUGS.items()}
SEQUENCE = [STEM_BY_SLUG[slug] for slug in CAST_ORDER]
WIDE = ("Jason_Duval_Video_Clip", "Lucia_Caminos_Video_Clip")  # 16:9 sources; the rest are square

SPEED = 1.0          # the clip plays at its true speed: no slow motion, no frame interpolation
CLIP_TO_ART = 0.4    # dissolve from the moving clip into the artwork
ART_LEN = 2.0        # length of the artwork beat; it is visible for ART_LEN - CLIP_TO_ART seconds after the clip ends
ART_HOLD = ART_LEN - CLIP_TO_ART
REEL_DISSOLVE = 0.3  # cross-dissolve between people in the reel
PUSH = 0.05          # total slow push-in over the artwork beat
WIDTH, HEIGHT = 1600, 900
SQUARE_X = WIDTH - HEIGHT   # square clips are placed flush right
FEATHER = 140        # width of the soft edge where the square meets its extension

POSTER_AT = 0.55         # seconds into the sequence: after the fade from black, before the dissolve into the artwork
POSTER_TARGET = 84       # average luma (0 to 255) a dark poster is lifted towards
POSTER_MAX_GAMMA = 1.9   # never lift further than this, so the picture stays natural

# Character portraits (Characters pages): 16:9 leads keep the full frame, the square clips stay square. No blurred
# extension, no black dips. The square artwork crop follows the person across the landscape picture.
PORTRAIT_SIZE = {"wide": (1600, 900), "square": (1080, 1080)}
PORTRAIT_FOCUS = {   # where the person sits across the 16:9 artwork (0 to 1), so a square crop keeps them whole
    "cal-hampton": 0.46, "boobie-ike": 0.55, "dre-quan-priest": 0.58, "real-dimez": 0.50, "raul-bautista": 0.50,
    "brian-heder": 0.70,
}
PORTRAIT_DISSOLVE = 0.5        # dissolve from the clip back into the artwork
PORTRAIT_HOLD = 2.0            # how long the artwork then rests (with a very slow push-in)
PROFILE_INTRO = 0.3            # dissolve from the artwork into the clip's first frame (profile sequences only)
# The picture each person rests on in the profile sequence is their main artwork on the page. Only Lucia's differs from
# the older ARTWORK table (which the homepage reel keeps): her main picture is Lucia_Caminos_02.
PROFILE_ART = {"lucia-caminos": "Lucia_Caminos_02.16n.5umvlu_48.jpg"}
PORTRAIT_GRADE_TARGET = 66     # the very dark night clips are lifted gently towards this average luma while they play
PORTRAIT_MAX_GAMMA = 1.7

INTERMEDIATE = ["-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", "-r", "30"]
FINAL = ["-an", "-c:v", "libx264", "-preset", "slow", "-crf", "25", "-pix_fmt", "yuv420p", "-r", "30",
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


def fetch_artwork():
    """Download each person's official artwork once (host and type checked). Skips files that are already there."""
    ART_DIR.mkdir(parents=True, exist_ok=True)
    for slug, name in ARTWORK.items():
        target = ART_DIR / f"{slug}.jpg"
        if target.exists() and target.stat().st_size > 50_000:
            continue
        url = f"{ART_BASE}{name}?akim=1&imdensity=1&imwidth=1920"
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (TeamValkyrie fan project)"})
        with urllib.request.urlopen(request, timeout=60) as response:
            if "image/jpeg" not in response.headers.get("Content-Type", ""):
                sys.exit(f"Unexpected content type for {url}")
            target.write_bytes(response.read())
        print(f"  fetched artwork for {slug}", flush=True)


def compose_filter(wide):
    """Frame composition: full frame for 16:9 sources, flush-right square over a feathered ambient extension."""
    if wide:
        return f"[0:v]fps=30,scale={WIDTH}:{HEIGHT}:flags=lanczos[c]"
    return (
        "[0:v]fps=30,split[bg][fg];"
        f"[bg]scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,crop={WIDTH}:{HEIGHT},gblur=sigma=30,eq=brightness=-0.24:saturation=0.92[b];"
        f"[fg]scale={HEIGHT}:{HEIGHT}:flags=lanczos,format=yuva420p,"
        f"geq=lum='lum(X,Y)':cb='cb(X,Y)':cr='cr(X,Y)':a='if(lt(X,{FEATHER}),255*X/{FEATHER},255)'[f];"
        f"[b][f]overlay={SQUARE_X}:0:format=auto[c]"
    )


def mean_luma(ffmpeg, video, at):
    """Average brightness (0 to 255) of the frame at `at` seconds."""
    raw = subprocess.run([ffmpeg, "-v", "error", "-ss", f"{at}", "-i", str(video), "-frames:v", "1",
                          "-vf", "scale=1:1,format=gray", "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    return raw[0] if raw else 128


def poster_gamma(mean):
    """Gamma that lifts an average luma of `mean` to POSTER_TARGET (1.0 when it is bright enough already)."""
    mean = max(int(mean), 1)
    if mean >= POSTER_TARGET:
        return 1.0
    return min(POSTER_MAX_GAMMA, math.log(mean / 255) / math.log(POSTER_TARGET / 255))


def make_poster(ffmpeg, video, out):
    gamma = poster_gamma(mean_luma(ffmpeg, video, POSTER_AT))
    chain = [f"eq=gamma={gamma:.2f}"] if gamma > 1.0 else []
    args = ["-vf", ",".join(chain)] if chain else []
    run(ffmpeg, "-ss", f"{POSTER_AT}", "-i", str(video), "-frames:v", "1", *args, "-q:v", "3", str(out))
    return gamma


def build_posters_only():
    ffmpeg = ffmpeg_exe()
    for slug in CAST_ORDER:
        video = CLIPS_DIR / f"{slug}.mp4"
        if not video.exists():
            print(f"  {slug}: no sequence yet (run without --posters first)")
            continue
        gamma = make_poster(ffmpeg, video, CLIPS_DIR / f"{slug}.jpg")
        print(f"  poster for {slug} (lift gamma {gamma:.2f})", flush=True)


def profile_art(slug):
    """The artwork a person rests on: their main picture on the page (a separate file only where it differs)."""
    own = ART_DIR / f"{slug}-main.jpg"
    return own if slug in PROFILE_ART else ART_DIR / f"{slug}.jpg"


def fetch_profile_art():
    """Download the one main artwork that is not in ARTWORK (host and type checked, skipped when already there)."""
    for slug, name in PROFILE_ART.items():
        target = ART_DIR / f"{slug}-main.jpg"
        if target.exists() and target.stat().st_size > 50_000:
            continue
        ART_DIR.mkdir(parents=True, exist_ok=True)
        url = f"{ART_BASE}{name}?akim=1&imdensity=1&imwidth=1920"
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (TeamValkyrie fan project)"})
        with urllib.request.urlopen(request, timeout=60) as response:
            if "image/jpeg" not in response.headers.get("Content-Type", ""):
                sys.exit(f"Unexpected content type for {url}")
            target.write_bytes(response.read())
        print(f"  fetched main artwork for {slug}", flush=True)


def _grade(ffmpeg, src):
    """The gentle lift for a very dark clip, as an ffmpeg filter fragment ('' when the clip is bright enough)."""
    mean = (mean_luma(ffmpeg, src, 0.25) + mean_luma(ffmpeg, src, 0.6)) / 2
    if mean >= PORTRAIT_GRADE_TARGET:
        return "", 1.0
    gamma = min(PORTRAIT_MAX_GAMMA, math.log(max(mean, 1) / 255) / math.log(PORTRAIT_GRADE_TARGET / 255))
    return (f",eq=gamma={gamma:.2f}" if gamma > 1.0 else ""), gamma


def _art_crop(slug, w, h, wide):
    """Filter fragment that fits the 16:9 artwork to the clip's own shape around the person."""
    x = "0" if wide else f"min(max({PORTRAIT_FOCUS[slug]}*iw-{w}/2,0),iw-{w})"
    return f"scale=-2:{h}:flags=lanczos,crop={w}:{h}:x='{x}':y=0"


def build_profile(ffmpeg, stem, slug):
    """media/clips/<slug>-profile.mp4 and .jpg for the large picture on a profile page.

    It starts on the person's artwork (the .jpg is exactly that first frame), dissolves for PROFILE_INTRO into the
    clip's first frame, plays the whole clip at true speed, then dissolves for PORTRAIT_DISSOLVE back into the artwork
    while the clip's last frame is held, and rests on the artwork for PORTRAIT_HOLD with a very slow push-in. The clip is
    never sped up, slowed down, interpolated or trimmed, and there is no black frame anywhere."""
    wide = PORTRAIT_SHAPE.get(slug, "square") == "wide"
    w, h = PORTRAIT_SIZE["wide" if wide else "square"]
    src = SOURCE_DIR / f"{stem}.mp4"
    length = duration(ffmpeg, src) / SPEED
    grade, gamma = _grade(ffmpeg, src)
    outro = PORTRAIT_DISSOLVE + PORTRAIT_HOLD
    zoom = f"(1+{PUSH}*t/{outro})"
    cfr = "setpts=PTS-STARTPTS,fps=30"
    graph = (
        f"[0:v]fps=30,scale={w}:{h}:flags=lanczos{grade},format=yuv420p,"
        f"tpad=start_mode=clone:start_duration={PROFILE_INTRO}:stop_mode=clone:stop_duration={PORTRAIT_DISSOLVE + 0.2},{cfr}[c];"
        f"[1:v]fps=30,{_art_crop(slug, w, h, wide)},format=yuv420p,split[ai][ao];"
        f"[ai]trim=duration={PROFILE_INTRO},{cfr}[a1];"
        f"[ao]scale=w='trunc({w}*{zoom}/2)*2':h='trunc({h}*{zoom}/2)*2':eval=frame:flags=bicubic,crop={w}:{h},"
        f"trim=duration={outro},{cfr}[a2];"
        f"[a1][c]xfade=transition=fade:duration={PROFILE_INTRO}:offset=0[r1];"
        f"[r1]{cfr}[r2];"
        f"[r2][a2]xfade=transition=fade:duration={PORTRAIT_DISSOLVE}:offset={length + PROFILE_INTRO:.3f}[v]"
    )
    out = CLIPS_DIR / f"{slug}-profile.mp4"
    run(ffmpeg, "-i", str(src), "-loop", "1", "-t", f"{outro + PROFILE_INTRO + 1:.1f}", "-i", str(profile_art(slug)),
        "-filter_complex", graph, "-map", "[v]", *FINAL, str(out))
    run(ffmpeg, "-i", str(out), "-frames:v", "1", "-q:v", "2", str(CLIPS_DIR / f"{slug}-profile.jpg"))
    return {"slug": slug, "shape": "wide" if wide else "square", "gamma": round(gamma, 2),
            "length": round(length + PROFILE_INTRO + PORTRAIT_DISSOLVE + PORTRAIT_HOLD, 2), "clip": round(length, 2)}


def build_portrait(ffmpeg, stem, slug):
    """media/clips/<slug>-portrait.mp4 and .jpg (the Characters landing tiles): the clip at true speed in its own
    shape, dissolving into the artwork cropped to the same shape. The .jpg is the exact frame at PORTRAIT_POSTER_AT,
    so the still and the clip join up."""
    wide = PORTRAIT_SHAPE.get(slug, "square") == "wide"
    w, h = PORTRAIT_SIZE["wide" if wide else "square"]
    src = SOURCE_DIR / f"{stem}.mp4"
    art = profile_art(slug)
    length = duration(ffmpeg, src) / SPEED
    grade, gamma = _grade(ffmpeg, src)
    hold = PORTRAIT_DISSOLVE + PORTRAIT_HOLD
    zoom = f"(1+{PUSH}*t/{hold})"
    graph = (
        # the clip's last frame is held a little past the dissolve so the dissolve always completes
        f"[0:v]fps=30,scale={w}:{h}:flags=lanczos{grade},format=yuv420p,tpad=stop_mode=clone:stop_duration=0.2[c];"
        f"[1:v]fps=30,{_art_crop(slug, w, h, wide)},"
        f"scale=w='trunc({w}*{zoom}/2)*2':h='trunc({h}*{zoom}/2)*2':eval=frame:flags=bicubic,crop={w}:{h},format=yuv420p[a];"
        f"[c][a]xfade=transition=fade:duration={PORTRAIT_DISSOLVE}:offset={length - PORTRAIT_DISSOLVE:.3f}[v]"
    )
    out = CLIPS_DIR / f"{slug}-portrait.mp4"
    run(ffmpeg, "-i", str(src), "-loop", "1", "-t", f"{hold}", "-i", str(art), "-filter_complex", graph,
        "-map", "[v]", *FINAL, str(out))
    run(ffmpeg, "-ss", f"{PORTRAIT_POSTER_AT}", "-i", str(out), "-frames:v", "1", "-q:v", "2", str(CLIPS_DIR / f"{slug}-portrait.jpg"))
    return {"slug": slug, "shape": "wide" if wide else "square", "width": w, "height": h, "gamma": round(gamma, 2),
            "length": round(length - PORTRAIT_DISSOLVE + hold, 2)}


def build_portraits_only():
    ffmpeg = ffmpeg_exe()
    CLIPS_DIR.mkdir(parents=True, exist_ok=True)
    fetch_artwork()
    fetch_profile_art()
    for stem in SEQUENCE:
        slug, name = SLUGS[stem]
        tile = build_portrait(ffmpeg, stem, slug)
        prof = build_profile(ffmpeg, stem, slug)
        print(f"  {name}: {tile['shape']}, lift gamma {tile['gamma']}; tile {tile['length']}s, profile {prof['length']}s "
              f"(clip {prof['clip']}s whole)", flush=True)


def build_segment(ffmpeg, src, art, out, length, wide):
    """The clip at true speed, dissolving into its artwork, which holds with a very slow push-in."""
    zoom = f"(1+{PUSH}*t/{ART_LEN})"
    graph = (
        compose_filter(wide)
        + f";[1:v]fps=30,scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,crop={WIDTH}:{HEIGHT},"
        f"scale=w='trunc({WIDTH}*{zoom}/2)*2':h='trunc({HEIGHT}*{zoom}/2)*2':eval=frame:flags=bicubic,crop={WIDTH}:{HEIGHT},format=yuv420p[a];"
        f"[c]format=yuv420p[cc];[cc][a]xfade=transition=fade:duration={CLIP_TO_ART}:offset={length - CLIP_TO_ART:.3f}[v]"
    )
    run(ffmpeg, "-i", str(src), "-loop", "1", "-t", f"{ART_LEN}", "-i", str(art), "-filter_complex", graph,
        "-map", "[v]", *INTERMEDIATE, str(out))
    return length - CLIP_TO_ART + ART_LEN


def main():
    ffmpeg = ffmpeg_exe()
    assert sorted(SEQUENCE) == sorted(CHARACTER_CLIPS), "CAST_ORDER must name every character clip exactly once"
    missing = [n for n in SEQUENCE if not (SOURCE_DIR / f"{n}.mp4").exists()]
    if missing:
        sys.exit("Missing source clips. Run: python -m scripts.fetch_clips")
    assert set(ARTWORK) == set(CAST_ORDER)
    fetch_artwork()
    CLIPS_DIR.mkdir(parents=True, exist_ok=True)

    segments, lengths, manifest = [], [], []
    for stem in SEQUENCE:
        slug, name = SLUGS[stem]
        src = SOURCE_DIR / f"{stem}.mp4"
        length = duration(ffmpeg, src) / SPEED
        seg = CLIPS_DIR / f"_seg_{slug}.mp4"
        total_seg = build_segment(ffmpeg, src, ART_DIR / f"{slug}.jpg", seg, length, stem in WIDE)
        print(f"  {name}: {length:.2f}s clip at true speed + {ART_HOLD:.1f}s artwork = {total_seg:.2f}s", flush=True)
        segments.append(seg)
        lengths.append(total_seg)

        # Profile-page version: dips through black at both ends so it loops without a visible jump.
        run(ffmpeg, "-i", str(seg), "-vf", f"fade=t=in:st=0:d=0.3,fade=t=out:st={total_seg - 0.3:.2f}:d=0.3", *FINAL,
            str(CLIPS_DIR / f"{slug}.mp4"))
        make_poster(ffmpeg, seg, CLIPS_DIR / f"{slug}.jpg")

    # The reel: short dissolves between people. A keyframe sits at the start of every person, so a seek is instant.
    offset = 0.0
    for index, stem in enumerate(SEQUENCE):
        slug, name = SLUGS[stem]
        last = index == len(SEQUENCE) - 1
        end = offset + lengths[index] - (0 if last else REEL_DISSOLVE)
        manifest.append({"slug": slug, "name": name, "start": round(offset, 2), "end": round(end, 2)})
        offset += lengths[index] - REEL_DISSOLVE
    inputs, chain, joined = [], [], "[0:v]"
    for seg in segments:
        inputs += ["-i", str(seg)]
    position = lengths[0] - REEL_DISSOLVE
    for k in range(1, len(segments)):
        label = f"[x{k}]"
        chain.append(f"{joined}[{k}:v]xfade=transition=fade:duration={REEL_DISSOLVE}:offset={position:.3f}{label}")
        joined = label
        position += lengths[k] - REEL_DISSOLVE
    total = round(sum(lengths) - (len(lengths) - 1) * REEL_DISSOLVE, 2)
    keyframes = ",".join(f"{m['start']}" for m in manifest)
    run(ffmpeg, *inputs, "-filter_complex", ";".join(chain), "-map", joined, "-force_key_frames", keyframes,
        *FINAL, str(CLIPS_DIR / "leonida-reel.mp4"))
    run(ffmpeg, "-ss", "0.6", "-i", str(CLIPS_DIR / "leonida-reel.mp4"), "-frames:v", "1", "-q:v", "3",
        str(CLIPS_DIR / "leonida-reel.jpg"))
    for seg in segments:
        seg.unlink()
    (CLIPS_DIR / "manifest.json").write_text(
        json.dumps({"duration": total, "speed": SPEED, "art_hold": ART_HOLD, "dissolve": REEL_DISSOLVE, "segments": manifest}, indent=2),
        encoding="utf-8")

    size = 0
    for f in sorted(CLIPS_DIR.iterdir()):
        size += f.stat().st_size
        print(f"  {f.name:28s} {f.stat().st_size / 1024:8.0f} KB")
    print(f"Reel length {total:.1f}s ({len(segments)} people, natural speed). Total {size / 1048576:.1f} MB in {CLIPS_DIR}")


if __name__ == "__main__":
    if "--portraits" in sys.argv[1:]:
        build_portraits_only()
    elif "--posters" in sys.argv[1:]:
        build_posters_only()
    else:
        main()
