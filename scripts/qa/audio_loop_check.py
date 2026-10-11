"""Check that a cinematic moment's sound is whole and loops cleanly.

    python scripts/qa/audio_loop_check.py media/cinematic/moment-1.mp4 [source.mp4 source_start [second_start from_seconds]]

A moment cut from two places (Moment 2) takes the second source start, as it would be at the file's time 0, and the file
time from which it applies.

Reports: audio length against picture length; the quietest 100 ms window (a silent gap shows as under -60 dB); the
level a quarter second either side of the loop point and the largest sample jump there against the file's normal
sample-to-sample movement (a click shows as many times larger); and, if a source recording and its start are given,
how closely the first seconds of the file follow the original soundtrack. Standard library only; needs ffmpeg.
"""
import math
import re
import subprocess
import sys

from audio_profile import ffmpeg_exe, samples

RATE = 48000


def stream_seconds(path, kind):
    """Length of the audio ('a') or video ('v') stream, from the last time= ffmpeg reports when copying it."""
    r = subprocess.run([ffmpeg_exe(), "-hide_banner", "-i", str(path), "-map", f"0:{kind}", "-c", "copy", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    times = re.findall(r"time=(\d+):(\d+):([\d.]+)", r.stderr)
    h, m, s = times[-1]
    return int(h) * 3600 + int(m) * 60 + float(s)


def db(x):
    return 20 * math.log10(x) if x > 0 else -120.0


def rms(chunk):
    return math.sqrt(sum(v * v for v in chunk) / max(len(chunk), 1)) / 32768.0


def main():
    path = sys.argv[1]
    data = samples(path)
    secs = len(data) / RATE
    a, v = stream_seconds(path, "a"), stream_seconds(path, "v")
    print(f"{path}")
    print(f"  decoded audio {secs:.3f} s | audio stream {a:.3f} s | picture stream {v:.3f} s | difference {a - v:+.3f} s")

    win = RATE // 10
    levels = [(i / RATE, db(rms(data[i:i + win]))) for i in range(0, len(data) - win + 1, win)]
    quiet = min(levels, key=lambda x: x[1])
    loud = max(levels, key=lambda x: x[1])
    print(f"  100 ms windows: quietest {quiet[1]:.1f} dBFS at {quiet[0]:.2f} s, loudest {loud[1]:.1f} dBFS at {loud[0]:.2f} s, "
          f"spread {loud[1] - quiet[1]:.1f} dB")
    gaps = [(t, l) for t, l in levels if l < -60]
    print(f"  silent windows (under -60 dBFS): {len(gaps)}" + (f", first at {gaps[0][0]:.2f} s" if gaps else ""))

    # the loop point: the end of the file followed by its start
    quarter = RATE // 4
    end, start = data[-quarter:], data[:quarter]
    diffs = [abs(data[i + 1] - data[i]) for i in range(0, len(data) - 1)]
    typical = sum(diffs) / len(diffs)
    joined = list(end) + list(start)
    jump = max(abs(joined[i + 1] - joined[i]) for i in range(len(joined) - 1))
    boundary = abs(start[0] - end[-1])
    print(f"  loop point: last 250 ms {db(rms(end)):.1f} dBFS -> first 250 ms {db(rms(start)):.1f} dBFS "
          f"(step {db(rms(start)) - db(rms(end)):+.1f} dB)")
    inner = max(diffs)
    near = max(abs(joined[i + 1] - joined[i]) for i in range(quarter - 3, quarter + 3))
    print(f"  loop point: sample step {boundary}, biggest step across the join {near}; the biggest step anywhere inside "
          f"the file is {inner} (typical {typical:.0f}) - a click would be far above that")

    # the seam: level through the last second, 100 ms apart, so a dip or hole is visible
    print("  last 1.2 s (rms dBFS per 100 ms): " + " ".join(f"{db(rms(data[i:i + win])):.0f}"
          for i in range(max(len(data) - int(1.2 * RATE), 0), len(data) - win + 1, win)))

    if len(sys.argv) >= 4:
        src, src_start = sys.argv[2], float(sys.argv[3])
        ref = samples(src, src_start, secs + 0.2)
        ref2 = samples(src, float(sys.argv[4]), secs + 0.2) if len(sys.argv) >= 6 else None
        switch = float(sys.argv[5]) if len(sys.argv) >= 6 else None
        # compare 1 s windows of the file's middle with the original (same instants), allowing a flat gain and a small offset
        best = []
        for t0 in (1.0, 3.0, 5.0, 7.0):
            n = RATE
            i0 = int(t0 * RATE)
            x = data[i0:i0 + n]
            top = (-2, 0)
            use = ref2 if (ref2 is not None and t0 >= switch) else ref
            for lag in range(-480, 481, 8):
                y = use[i0 + lag:i0 + lag + n]
                if len(y) < n:
                    continue
                num = sum(a_ * b_ for a_, b_ in zip(x, y))
                den = math.sqrt(sum(a_ * a_ for a_ in x) * sum(b_ * b_ for b_ in y)) or 1
                if num / den > top[0]:
                    top = (num / den, lag)
            best.append(top)
        print("  match with the original soundtrack (1 s windows at 1, 3, 5, 7 s): "
              + ", ".join(f"r={c:.3f} at {lag / RATE * 1000:+.0f} ms" for c, lag in best))


if __name__ == "__main__":
    main()
