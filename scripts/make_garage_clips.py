"""Build the Garage's one short atmosphere clip from Rockstar's own trailers (local files only; nothing here is ever committed).

    python -m scripts.make_garage_clips            # builds media/clips/garage/on-the-water.mp4 plus two stills

The clip is a dissolve from two shots Rockstar published: a slow aerial of the marina (Launch Trailer, 4.98 to 6.90 s) into a sunset over a
dock (Trailer 2, 83.15 to 85.00 s). It is muted, 1920 x 1080, about 3.3 s, with no title card, logo, caption or character in frame. The source
files are never touched. Each shot is trimmed a few frames inside its cut, so no frame of a neighbouring shot appears.

Sources (Git-ignored, supplied by the owner):
    media/source/rockstar/gta-vi-launch-trailer.mp4      Rockstar's Launch Trailer (15 October 2026)
    media/source-videos/trailers/GTAVI_Trailer_2.mp4     Rockstar's Trailer 2

Rockstar states no licence terms for its trailers; the owner has asked for this excerpt, and the folder is Git-ignored so it can be removed
at any time. The Garage shows it only when the file exists and falls back to the still picture otherwise.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "media" / "clips" / "garage"
LAUNCH = ROOT / "media" / "source" / "rockstar" / "gta-vi-launch-trailer.mp4"
TRAILER_2 = ROOT / "media" / "source-videos" / "trailers" / "GTAVI_Trailer_2.mp4"
MARINA = (4.98, 1.92)         # start, length (seconds into the Launch Trailer): Brian's Marina from the air
SUNSET = (83.15, 1.85)        # start, length (seconds into Trailer 2): the sunset over the dock
DISSOLVE = 0.5


def ffmpeg():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return "ffmpeg"


def run(args):
    result = subprocess.run([ffmpeg(), "-hide_banner", "-loglevel", "error", "-y", *args], capture_output=True, text=True)
    if result.returncode:
        sys.exit(result.stderr)


def main():
    for source in (LAUNCH, TRAILER_2):
        if not source.is_file():
            sys.exit(f"missing source: {source}")
    OUT.mkdir(parents=True, exist_ok=True)
    clip = OUT / "on-the-water.mp4"
    offset = MARINA[1] - DISSOLVE
    graph = (f"[0:v]fps=30,scale=1920:1080:flags=lanczos,setsar=1,format=yuv420p[a];[1:v]fps=30,scale=1920:1080:flags=lanczos,setsar=1,format=yuv420p[b];"
             f"[a][b]xfade=transition=fade:duration={DISSOLVE}:offset={offset:.2f},format=yuv420p[v]")
    run(["-ss", str(MARINA[0]), "-t", str(MARINA[1]), "-i", str(LAUNCH), "-ss", str(SUNSET[0]), "-t", str(SUNSET[1]), "-i", str(TRAILER_2),
         "-filter_complex", graph, "-map", "[v]", "-an", "-c:v", "libx264", "-preset", "slow", "-crf", "27", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(clip)])
    total = MARINA[1] + SUNSET[1] - DISSOLVE
    # the stills: the first frame (what a visitor sees as the clip begins) and the last (what it rests on, and what a visitor who has asked for no motion sees)
    run(["-i", str(clip), "-vframes", "1", "-q:v", "3", str(OUT / "on-the-water-start.jpg")])
    run(["-ss", f"{total - 0.12:.2f}", "-i", str(clip), "-vframes", "1", "-q:v", "3", str(OUT / "on-the-water.jpg")])
    print(f"{clip} ({clip.stat().st_size // 1024} KB, about {total:.1f} s)")


if __name__ == "__main__":
    main()
