"""Build the three homepage cinematic moments (web video and posters) from the owner's local source recordings.

    python -m scripts.make_cinematics            # all three moments
    python -m scripts.make_cinematics moment-2   # one

Reads media/source-videos/trailers/ and writes media/cinematic/ (both Git-ignored; nothing here is ever committed).
The source recordings are never modified. Needs ffmpeg (`pip install imageio-ffmpeg` is enough).

For every moment it writes
  moment-N.mp4          desktop: H.264 High, AAC stereo, faststart, loudness-normalised
  moment-N-mobile.mp4   a lighter cut cropped for phones (4:5 or 4:3)
  moment-N.jpg          a high-quality poster (also the reduced-motion and data-saver picture)

Trailer 2's picture is letterboxed (2.22:1 inside a 16:9 frame); the black bars are cropped away, so those moments are
true 2.22:1 pictures. Audio from every moment is brought to one loudness (-16 LUFS) so visitors do not hear jumps.
"""
import json
import re
import shutil
import subprocess
import sys

from scripts.schema_info import ROOT

SOURCE_DIR = ROOT / "media" / "source-videos" / "trailers"
OUT_DIR = ROOT / "media" / "cinematic"
TRAILER_1 = SOURCE_DIR / "GTAVI_Trailer_1.mp4"
TRAILER_2 = SOURCE_DIR / "GTAVI_Trailer_2.mp4"
BARS = "crop=3840:1728:0:216"     # Trailer 2: remove the 216 px letterbox bars
LOUDNESS = {"I": -16.0, "TP": -1.5, "LRA": 11.0}
AUDIO_BITRATE = "128k"
FADE_IN, FADE_OUT = 0.25, 0.4     # audio only; the picture is faded by the page

# Each moment: its parts (source, start seconds, length seconds), an optional dissolve between two parts, the poster
# frame, and the phone crop applied after the parts are joined (t is seconds into the finished moment).
MOMENTS = {
    "moment-1": {
        "title": "Dawn over Leonida",
        "parts": [(TRAILER_1, 19.16, 8.26)],
        "bars": False,
        "desktop": "scale=1920:1080:flags=lanczos",
        # 4:5. Focal points per shot: marsh and flamingos, beach, speedboat, night road.
        "mobile": "crop=1728:2160:x='if(lt(t,2.56),1056,if(lt(t,4.10),864,if(lt(t,5.66),1363,403)))':y=0,scale=720:900:flags=lanczos",
        "poster": (TRAILER_1, 21.3),
        "desktop_crf": 23, "mobile_crf": 25, "maxrate": "9M", "mobile_maxrate": "3.5M",
    },
    "moment-2": {
        "title": "Sun, water, speed",
        "parts": [(TRAILER_2, 6.35, 3.35), (TRAILER_2, 138.15, 5.50)],
        "dissolve": 0.4,
        "bars": True,
        "desktop": "scale=1920:864:flags=lanczos",
        # 4:3, centred; the helicopter shot sits right of centre.
        "mobile": "crop=2304:1728:x='if(between(t,2.95,4.75),1150,768)':y=0,scale=960:720:flags=lanczos",
        "poster": (TRAILER_2, 141.0),
        "desktop_crf": 23, "mobile_crf": 25, "maxrate": "7M", "mobile_maxrate": "3M",
    },
    "moment-3": {
        "title": "Last light",
        "parts": [(TRAILER_2, 152.85, 10.95)],
        "bars": True,
        "desktop": "scale=1920:864:flags=lanczos",
        # 4:3, centred on the logo (a 1:1 crop would clip the date line).
        "mobile": "crop=2304:1728:768:0,scale=960:720:flags=lanczos",
        "poster": (TRAILER_2, 154.2),
        "desktop_crf": 23, "mobile_crf": 25, "maxrate": "5M", "mobile_maxrate": "2M",
    },
}


def ffmpeg_exe():
    found = shutil.which("ffmpeg")
    if found:
        return found
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        sys.exit("ffmpeg was not found. Install it, or run: pip install imageio-ffmpeg")


def run(ffmpeg, *args, capture=False):
    return subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error", "-y", *args], check=True,
                          capture_output=capture, text=True, encoding="utf-8", errors="replace")


def total_length(moment):
    parts, dissolve = moment["parts"], moment.get("dissolve", 0.0)
    return sum(length for _s, _t, length in parts) - dissolve * (len(parts) - 1)


def input_args(moment):
    args = []
    for src, start, length in moment["parts"]:
        args += ["-ss", f"{start:.3f}", "-t", f"{length:.3f}", "-i", str(src)]
    return args


def video_graph(moment, variant):
    """Filter graph that joins the parts and ends on the [v] label. Desktop scales each part; mobile crops after the join."""
    parts, dissolve = moment["parts"], moment.get("dissolve", 0.0)
    prefix = (moment["bars"] and BARS + ",") or ""
    per_part = moment["desktop"] if variant == "desktop" else ""
    chains = []
    for i in range(len(parts)):
        steps = prefix + (per_part + "," if per_part else "") + "setsar=1,format=yuv420p"
        chains.append(f"[{i}:v]{steps}[p{i}]")
    if len(parts) == 1:
        joined = "[p0]"
    else:
        offset = parts[0][2] - dissolve
        chains.append(f"[p0][p1]xfade=transition=fade:duration={dissolve}:offset={offset:.3f}[j]")
        joined = "[j]"
    tail = "" if variant == "desktop" else moment["mobile"] + ","
    chains.append(f"{joined}{tail}fps=30,format=yuv420p[v]")
    return ";".join(chains)


def audio_graph(moment, normaliser):
    """Joined, faded, loudness-normalised audio ending on the [a] label."""
    parts, dissolve = moment["parts"], moment.get("dissolve", 0.0)
    chains = [f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo[s{i}]" for i in range(len(parts))]
    if len(parts) == 1:
        joined = "[s0]"
    else:
        chains.append(f"[s0][s1]acrossfade=d={dissolve}:c1=tri:c2=tri[aj]")
        joined = "[aj]"
    length = total_length(moment)
    chains.append(f"{joined}{normaliser}afade=t=in:st=0:d={FADE_IN},afade=t=out:st={length - FADE_OUT:.3f}:d={FADE_OUT}[a]")
    return ";".join(chains)


def measure_loudness(ffmpeg, moment):
    """First pass: integrated loudness of the finished audio, so the second pass can apply an exact linear gain."""
    flt = audio_graph(moment, f"loudnorm=I={LOUDNESS['I']}:TP={LOUDNESS['TP']}:LRA={LOUDNESS['LRA']}:print_format=json,")
    result = subprocess.run([ffmpeg, "-hide_banner", *input_args(moment), "-filter_complex", flt, "-map", "[a]", "-vn", "-f", "null", "-"],
                            capture_output=True, text=True, encoding="utf-8", errors="replace")
    blob = result.stderr[result.stderr.rindex("{"):result.stderr.rindex("}") + 1]
    stats = json.loads(blob)
    return {key: stats[key] for key in ("input_i", "input_tp", "input_lra", "input_thresh", "target_offset")}


def normaliser_for(stats):
    return (f"loudnorm=I={LOUDNESS['I']}:TP={LOUDNESS['TP']}:LRA={LOUDNESS['LRA']}:"
            f"measured_I={stats['input_i']}:measured_TP={stats['input_tp']}:measured_LRA={stats['input_lra']}:"
            f"measured_thresh={stats['input_thresh']}:offset={stats['target_offset']}:linear=true,")


def encode(ffmpeg, moment, variant, normaliser, out):
    crf = moment[f"{variant}_crf"]
    maxrate = moment["maxrate" if variant == "desktop" else "mobile_maxrate"]
    graph = video_graph(moment, variant) + ";" + audio_graph(moment, normaliser)
    run(ffmpeg, *input_args(moment), "-filter_complex", graph, "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "slow", "-profile:v", "high", "-crf", str(crf), "-maxrate", maxrate,
        "-bufsize", f"{float(maxrate[:-1]) * 2:g}M", "-pix_fmt", "yuv420p", "-g", "30",
        "-c:a", "aac", "-b:a", AUDIO_BITRATE, "-ar", "48000", "-ac", "2", "-movflags", "+faststart", str(out))


def poster(ffmpeg, moment, out):
    src, at = moment["poster"]
    prefix = (moment["bars"] and BARS + ",") or ""
    run(ffmpeg, "-ss", f"{max(at - 2, 0):.3f}", "-i", str(src), "-ss", f"{at - max(at - 2, 0):.3f}", "-frames:v", "1",
        "-vf", prefix + "scale=1920:-2:flags=lanczos", "-q:v", "2", str(out))


def main(only=None):
    ffmpeg = ffmpeg_exe()
    for source in (TRAILER_1, TRAILER_2):
        if not source.exists():
            sys.exit(f"Missing source recording: {source}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    report = {}
    for slot, moment in MOMENTS.items():
        if only and slot != only:
            continue
        print(f"{slot} ({moment['title']}), {total_length(moment):.2f} s", flush=True)
        stats = measure_loudness(ffmpeg, moment)
        norm = normaliser_for(stats)
        print(f"  loudness before: {stats['input_i']} LUFS, true peak {stats['input_tp']} dBTP", flush=True)
        encode(ffmpeg, moment, "desktop", norm, OUT_DIR / f"{slot}.mp4")
        encode(ffmpeg, moment, "mobile", norm, OUT_DIR / f"{slot}-mobile.mp4")
        poster(ffmpeg, moment, OUT_DIR / f"{slot}.jpg")
        report[slot] = {"title": moment["title"], "seconds": round(total_length(moment), 2),
                        "loudness_before_lufs": float(stats["input_i"])}
    manifest = OUT_DIR / "manifest.json"
    existing = json.loads(manifest.read_text(encoding="utf-8")) if manifest.exists() else {}
    existing.update(report)
    manifest.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    total = 0
    for f in sorted(OUT_DIR.iterdir()):
        total += f.stat().st_size
        print(f"  {f.name:24s} {f.stat().st_size / 1048576:7.2f} MB")
    print(f"Total {total / 1048576:.1f} MB in {OUT_DIR}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
