# media/

Local assets only. **Git ignores everything in this folder except this note**, so nothing here is ever committed.

`media/clips/` and `media/source/` are built on your own machine by two optional scripts:

```powershell
pip install -r requirements-media.txt      # a private ffmpeg, only for building loops
python -m scripts.fetch_clips              # reads Rockstar's published character clips (about 40 MB) into media/source/
python -m scripts.make_loops               # builds muted 1280x720 loops and one short reel into media/clips/ (about 6 MB)
```

The site shows them when they exist and falls back to Rockstar's own posters when they do not.
They are Rockstar's content. Rockstar states no licence terms for its media page, so keep them out of Git,
and remove the folder if Rockstar asks. Every row is listed in `docs/MEDIA_INVENTORY.md`.

## The cinematic moments (`media/cinematic/`)

The homepage has three native-video moments: after Jason and Lucia (full viewport), above the region explorer (a
2.22:1 band) and before the closing (the finale, on black). Build them from your own recordings:

```powershell
pip install -r requirements-media.txt                   # a private ffmpeg, only for building
python -m scripts.make_cinematics                       # all three; or: python -m scripts.make_cinematics moment-2
```

It reads `media/source-videos/trailers/GTAVI_Trailer_1.mp4` and `GTAVI_Trailer_2.mp4` and writes, per moment:

| File | What it is |
|------|------------|
| `moment-N.mp4` | Desktop: H.264 High, AAC stereo, faststart, loudness-normalised to -16 LUFS (about 8.7, 6.3 and 3.0 MB) |
| `moment-N-mobile.mp4` | A lighter phone cut, cropped 4:5, 4:3 and 4:3 (about 2.5, 2.4 and 1.5 MB) |
| `moment-N.jpg` | A high-quality poster, also the reduced-motion and data-saver picture |

The source recordings are never modified. A moment appears on the page only when its video exists; without
`moment-1.mp4` the first slot falls back to an official still with a link into Rockstar's own player.

