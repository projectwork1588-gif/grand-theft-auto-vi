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

## The cinematic moment (`media/cinematic/`)

The homepage has one full-screen section after Jason and Lucia. It shows an official still and opens the trailer in
Rockstar's own player until you provide authorised footage. To use native video, put these in `media/cinematic/`:

| File | Needed | Notes |
|------|--------|-------|
| `cinematic.mp4` | yes | H.264, no audio track needed, 8 to 12 seconds, loops. About 1080p and a few MB. |
| `cinematic.jpg` | recommended | Poster shown before it plays and for reduced-motion visitors. |
| `cinematic-mobile.mp4` | optional | A lighter cut (about 720 px wide). Phones play it; without it phones keep the poster. |

Names are lower case letters, digits and hyphens only. Source footage can wait in `media/source-videos/`
(`trailers/`, `gameplay/`, `other-clips/`). Everything in `media/` stays out of Git.

