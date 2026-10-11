"""Print a loudness profile (dBFS RMS per window) of a media file's audio, so a silent or jumping section is easy to see.

    python scripts/qa/audio_profile.py <file> [start_seconds] [length_seconds] [window_ms]

Needs ffmpeg (imageio-ffmpeg is enough). Pure standard library; nothing is written except a temporary raw file.
"""
import array
import math
import subprocess
import sys
import tempfile
from pathlib import Path


def ffmpeg_exe():
    import shutil
    found = shutil.which("ffmpeg")
    if found:
        return found
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def samples(path, start=0.0, length=None, rate=48000):
    with tempfile.TemporaryDirectory() as tmp:
        raw = Path(tmp) / "a.raw"
        cmd = [ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-y", "-ss", str(start)]
        if length:
            cmd += ["-t", str(length)]
        cmd += ["-i", str(path), "-vn", "-ac", "1", "-ar", str(rate), "-f", "s16le", str(raw)]
        subprocess.run(cmd, check=True)
        data = array.array("h")
        data.frombytes(raw.read_bytes())
    return data


def profile(path, start=0.0, length=None, window_ms=250, rate=48000):
    data = samples(path, start, length, rate)
    size = int(rate * window_ms / 1000)
    rows = []
    for i in range(0, len(data) - size + 1, size):
        chunk = data[i:i + size]
        rms = math.sqrt(sum(s * s for s in chunk) / size) / 32768.0
        peak = max(abs(s) for s in chunk) / 32768.0
        rows.append((start + i / rate, 20 * math.log10(rms) if rms > 0 else -120.0, 20 * math.log10(peak) if peak > 0 else -120.0))
    return rows, len(data) / rate


if __name__ == "__main__":
    path = sys.argv[1]
    start = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
    length = float(sys.argv[3]) if len(sys.argv) > 3 else None
    window = int(sys.argv[4]) if len(sys.argv) > 4 else 250
    rows, seconds = profile(path, start, length, window)
    print(f"{path}: {seconds:.2f} s of audio")
    for t, rms, peak in rows:
        bar = "#" * max(0, int((rms + 70) / 2))
        print(f"{t:7.2f}s  rms {rms:7.1f}  peak {peak:7.1f}  {bar}")
