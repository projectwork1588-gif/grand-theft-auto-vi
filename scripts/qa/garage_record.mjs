// Browser recordings of the Garage's interactions, for review: what a visitor sees when they choose a machine, move through
// the showcase, open the full-size viewer and filter the showroom. Chrome's screencast delivers a frame whenever the page changes;
// ffmpeg joins them at their real timing into an mp4 (the one bundled with imageio-ffmpeg is enough).
//   GARAGE_OUT=review/gate3b/recordings/ node scripts/qa/cdp.mjs scripts/qa/garage_record.mjs
import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, readdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";

const BASE = process.env.GARAGE_BASE || "http://127.0.0.1:5057";
const OUT = process.env.GARAGE_OUT || "review/garage-recordings/";
const PAGE = process.env.GARAGE_PATH || "/vehicles";                      // the Garage page recorded (the concept page has its own path)
const FFMPEG = process.env.FFMPEG || (() => {
  const dir = ".venv/Lib/site-packages/imageio_ffmpeg/binaries";
  return existsSync(dir) ? join(dir, readdirSync(dir).find((f) => f.startsWith("ffmpeg"))) : "ffmpeg";
})();

export default async function (b) {
  mkdirSync(OUT, { recursive: true });
  let frames = [];
  let recording = false;
  const statsFile = join(OUT, "recording-stats.json");
  const stats = existsSync(statsFile) ? JSON.parse(readFileSync(statsFile, "utf8")) : {};

  // Chrome's screencast only delivers a frame when the compositor happens to produce one, which in a headless window is far too
  // few to show a half-second fade; so the recorder takes screenshots as fast as the browser will give them (about ten a second)
  // while the scene plays, and keeps each frame's real time.
  const record = async (name, width, height, scene) => {
    if (process.env.GARAGE_ONLY && !name.startsWith(process.env.GARAGE_ONLY)) { return; }
    await b.send("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile: width < 700 });
    frames = [];
    recording = true;
    const loop = (async () => {
      while (recording) {
        const t = Date.now() / 1000;
        try {
          // no clip rectangle: a clip is in page coordinates, so once the page has scrolled it lies outside the window and the frame comes back as
          // blank ground (the cause of the empty frames in the first recordings); with none, the screenshot is the window as it is
          const r = await Promise.race([b.send("Page.captureScreenshot", { format: "jpeg", quality: 62, optimizeForSpeed: true }), new Promise((_, no) => setTimeout(() => no(new Error("slow")), 1200))]);
          frames.push({ t, data: r.data });
        } catch { /* a page change in the middle of a frame */ }
      }
    })();
    await scene();
    await b.sleep(400);
    recording = false;
    await loop;
    if (frames.length < 6) { console.log(name, "too few frames:", frames.length); return; }
    const dir = resolve(OUT, "_frames_" + name);
    mkdirSync(dir, { recursive: true });
    const lines = [];
    frames.forEach((f, i) => {
      const file = join(dir, String(i).padStart(5, "0") + ".jpg");
      writeFileSync(file, Buffer.from(f.data, "base64"));
      const next = frames[i + 1] ? frames[i + 1].t - f.t : 0.5;
      lines.push(`file '${file.replace(/\\/g, "/")}'`, `duration ${Math.max(0.016, Math.min(next, 1.5)).toFixed(3)}`);
    });
    lines.push(`file '${join(dir, String(frames.length - 1).padStart(5, "0") + ".jpg").replace(/\\/g, "/")}'`);
    const list = join(dir, "list.txt");
    writeFileSync(list, lines.join("\n"));
    const out = join(OUT, name + ".mp4");
    const r = spawnSync(FFMPEG, ["-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", list, "-vf", `fps=30,scale=${width > 700 ? 960 : width}:-2,format=yuv420p`, "-c:v", "libx264", "-crf", "24", "-preset", "veryfast", "-movflags", "+faststart", out]);
    if (r.status !== 0) { console.log(name, "ffmpeg failed", String(r.stderr)); } else {
      const secs = frames[frames.length - 1].t - frames[0].t;
      stats[name] = { frames: frames.length, seconds: Number(secs.toFixed(1)), capturedPerSecond: Number((frames.length / Math.max(secs, 0.1)).toFixed(1)) };
      console.log(name, frames.length, "frames over", secs.toFixed(1), "s ->", out);
    }
    rmSync(dir, { recursive: true, force: true });
  };

  await b.colorScheme(false);                       // record the motion as a visitor who allows it sees it (this machine's own setting may ask for none)
  await b.open(BASE + "/about", 100);
  await b.eval(`localStorage.setItem("tv-motion", "1"); true`);
  const click = (sel) => b.eval(`document.querySelector(${JSON.stringify(sel)}).click(); true`);
  const key = async (k, code, vk) => { await b.send("Input.dispatchKeyEvent", { type: "keyDown", key: k, code, windowsVirtualKeyCode: vk }); await b.send("Input.dispatchKeyEvent", { type: "keyUp", key: k, code, windowsVirtualKeyCode: vk }); };

  await b.send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  await b.open(BASE + PAGE, 2500);
  await record("01-opening-lineup-desktop", 1440, 900, async () => {
    await b.sleep(900);
    for (const slug of ["vapid-dominator-buggy", "shitzu-squalo", "vapid-stanier", "dinka-enduro", "crest-kayak", "grotti-cheetah"]) { await click(`[data-pick="${slug}"]`); await b.sleep(1700); }
  });
  await record("02-opening-keyboard-desktop", 1440, 900, async () => {
    await b.eval(`document.querySelector('[data-pick="grotti-cheetah"]').focus(); true`);
    for (let i = 0; i < 3; i++) { await key("ArrowRight", "ArrowRight", 39); await b.sleep(1500); }
  });
  await record("03-showroom-scroll-desktop", 1440, 900, async () => {
    for (let y = 0; y <= 4800; y += 90) { await b.eval(`window.scrollTo(0, ${y}); true`); await b.sleep(40); }
    await b.sleep(900);
    for (let y = 4800; y >= 0; y -= 160) { await b.eval(`window.scrollTo(0, ${y}); true`); await b.sleep(40); }
  });
  await b.open(BASE + PAGE, 1500);
  await record("04-showroom-filters-desktop", 1440, 900, async () => {
    await b.eval(`document.getElementById("showroom").scrollIntoView(); true`); await b.sleep(900);
    await b.eval(`document.querySelector('.ctl__cats a[href*="category=boat"]').click(); true`); await b.sleep(2200);
    for (let i = 0; i < 40 && !(await b.eval(`!!document.querySelector('.gresult__clear')`).catch(() => false)); i++) { await b.sleep(250); }
    await b.eval(`(document.querySelector('.gresult__clear') || { click() {} }).click(); true`); await b.sleep(2000);
  });
  await b.open(BASE + "/vehicles/vapid-dominator-buggy", 2500);
  await record("05-vehicle-page-and-showcase-desktop", 1440, 900, async () => {
    await b.sleep(1200);
    await b.eval(`document.querySelector("[data-viewer]").scrollIntoView(); true`); await b.sleep(1200);
    for (let i = 0; i < 3; i++) { await click("[data-next]"); await b.sleep(1300); }
    await click("[data-open]"); await b.sleep(1200);
    await key("ArrowRight", "ArrowRight", 39); await b.sleep(900);
    await key("Escape", "Escape", 27); await b.sleep(900);
  });
  await b.open(BASE + PAGE, 2500);
  await record("06-choose-a-vehicle-transition-desktop", 1440, 900, async () => {
    await b.sleep(800);
    await b.eval(`document.querySelector('[data-stage] [data-panel]:not([hidden]) a.gbtn').click(); true`);
    await b.sleep(2600);
    // the page has changed by now (a navigation has only two states to see); scroll the new page so the recording also shows it settling
    for (let y = 0; y <= 760; y += 40) { await b.eval(`window.scrollTo(0, ${y}); true`); await b.sleep(50); }
  });
  await b.open(BASE + PAGE, 2500);
  await record("07-opening-lineup-phone", 390, 844, async () => {
    await b.sleep(900);
    for (const slug of ["vapid-dominator-buggy", "shitzu-squalo", "vapid-stanier"]) { await click(`[data-pick="${slug}"]`); await b.sleep(1700); }
  });
  await b.open(BASE + "/vehicles/vapid-dominator-buggy", 2500);
  await record("08-showcase-phone", 390, 844, async () => {
    await b.eval(`document.querySelector("[data-viewer]").scrollIntoView(); true`); await b.sleep(1100);
    for (let i = 0; i < 3; i++) { await click("[data-next]"); await b.sleep(1300); }
  });
  writeFileSync(statsFile, JSON.stringify(stats, null, 2));
  await b.eval(`localStorage.clear(); true`);
}
