"""Fetch Rockstar's official short video clips for LOCAL playback. Nothing here is ever committed.

    python -m scripts.fetch_clips --list          # show what Rockstar's clips bundle contains
    python -m scripts.fetch_clips                 # fetch the eight character clips into media/source/

Source: https://www.rockstargames.com/VI/media/videos ("Download and share official videos").
The clips bundle is one zip. Only the entries we need are read, using HTTP range requests, so about 80 MB is
transferred and the full 115 MB bundle is never downloaded. Files land in media/source/, which Git ignores.

Usage rights: Rockstar's page invites visitors to download and share these clips but states no licence terms.
They are used for local playback only and are never added to the repository. See docs/MEDIA_INVENTORY.md.
"""
import argparse
import struct
import sys
import urllib.request
import zlib
from pathlib import Path

from scripts.schema_info import ROOT

ZIP_URL = "https://media-rockstargames-com.akamaized.net/VI/downloads/videos/GTAVI_Videos.zip"
SOURCE_DIR = ROOT / "media" / "source"
CHARACTER_CLIPS = (
    "Jason_Duval_Video_Clip", "Lucia_Caminos_Video_Clip", "Cal_Hampton_Video_Clip", "Boobie_Ike_Video_Clip",
    "DreQuan_Priest_Video_Clip", "Real_Dimez_Video_Clip", "Raul_Bautista_Video_Clip", "Brian_Heder_Video_Clip",
)
TIMEOUT = 90


def _request(start=None, end=None, method="GET"):
    headers = {"User-Agent": "TeamValkyrie-fan-project/1.0 (educational)"}
    if start is not None:
        headers["Range"] = f"bytes={start}-{end}"
    return urllib.request.Request(ZIP_URL, headers=headers, method=method)


def _read_range(start, end):
    with urllib.request.urlopen(_request(start, end), timeout=TIMEOUT) as response:
        return response.read()


def zip_entries():
    """Read the zip's central directory (a few KB at the end of the file) and return {name: entry}."""
    with urllib.request.urlopen(_request(method="HEAD"), timeout=TIMEOUT) as response:
        size = int(response.headers["Content-Length"])
    tail = _read_range(max(0, size - 65536), size - 1)
    pos = tail.rfind(b"PK\x05\x06")
    _, _, _, count, _, cd_size, cd_offset, _ = struct.unpack("<IHHHHIIH", tail[pos:pos + 22])
    directory = _read_range(cd_offset, cd_offset + cd_size - 1)
    entries, p = {}, 0
    while p < len(directory) and directory[p:p + 4] == b"PK\x01\x02":
        (_, _, _, _, method, _, _, crc, csize, usize, nlen, elen, clen, _, _, _, offset) = struct.unpack(
            "<IHHHHHHIIIHHHHHII", directory[p:p + 46])
        name = directory[p + 46:p + 46 + nlen].decode("utf-8", "replace")
        entries[name] = {"method": method, "crc": crc, "csize": csize, "usize": usize, "offset": offset}
        p += 46 + nlen + elen + clen
    return size, entries


def fetch_entry(name, entry, target):
    """Download one zip entry by range, inflate it, verify its CRC, write it to target."""
    header = _read_range(entry["offset"], entry["offset"] + 29)
    nlen, elen = struct.unpack("<HH", header[26:30])
    data_start = entry["offset"] + 30 + nlen + elen
    with urllib.request.urlopen(_request(data_start, data_start + entry["csize"] - 1), timeout=TIMEOUT) as response:
        inflater = zlib.decompressobj(-15) if entry["method"] == 8 else None
        crc, written = 0, 0
        target.parent.mkdir(parents=True, exist_ok=True)
        part = target.with_suffix(".part")
        with open(part, "wb") as out:
            while True:
                chunk = response.read(1 << 20)
                if not chunk:
                    break
                chunk = inflater.decompress(chunk) if inflater else chunk
                crc = zlib.crc32(chunk, crc)
                written += len(chunk)
                out.write(chunk)
            if inflater:
                tail = inflater.flush()
                crc = zlib.crc32(tail, crc)
                written += len(tail)
                out.write(tail)
    if written != entry["usize"] or crc & 0xFFFFFFFF != entry["crc"]:
        part.unlink(missing_ok=True)
        raise RuntimeError(f"{name}: integrity check failed (size {written} vs {entry['usize']})")
    part.replace(target)
    return written


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--list", action="store_true", help="list the bundle's contents and exit")
    parser.add_argument("--only", help="fetch a single clip name, for example Jason_Duval_Video_Clip")
    args = parser.parse_args(argv)

    size, entries = zip_entries()
    print(f"Rockstar clips bundle: {size / 1048576:.1f} MB, {len(entries)} files (only requested entries are read)")
    for name, e in sorted(entries.items()):
        print(f"  {name:48s} {e['usize'] / 1048576:7.1f} MB")
    if args.list:
        return 0

    wanted = [args.only] if args.only else list(CHARACTER_CLIPS)
    total = 0
    for stem in wanted:
        name = stem + ".mp4"
        if name not in entries:
            print(f"Not in the bundle: {name}", file=sys.stderr)
            return 1
        target = SOURCE_DIR / name
        if target.exists() and target.stat().st_size == entries[name]["usize"]:
            print(f"Already have {name}")
            continue
        print(f"Fetching {name} ({entries[name]['csize'] / 1048576:.1f} MB) ...", flush=True)
        total += fetch_entry(name, entries[name], target)
    print(f"Done. {total / 1048576:.1f} MB written to {SOURCE_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
