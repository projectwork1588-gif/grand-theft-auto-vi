// Title placement and vehicle visibility on the Garage opening, measured in a real browser at the sizes the opening is built for.
// Each scene carries `data-subject` (x0,y0,x1,y1: where the machine sits in its picture, as fractions, measured by eye). For every machine at every size the
// script works out where that box lands on the screen (the picture is drawn with object-fit: cover and its own object-position), and checks that
//   * no part of the words (the kicker, the name, the line about the picture, the Explore button) crosses the machine (its box is shrunk by 5 percent each side so
//     a rectangle is not mistaken for the machine's outline), and
//   * the machine is not cut off by the window (at least 95 percent of its box is on screen, measured where the camera's push has taken it by its end and clear of the header).
// It also writes one screenshot per machine and size with the words (cyan) and the machine's box (magenta) drawn on, for the review pack.
//   TL_BASE=http://127.0.0.1:5059 TITLES_OUT=dir/ node scripts/qa/cdp.mjs scripts/qa/garage_titles.mjs      (exit status 1 on any crossing)
import { mkdirSync } from "node:fs";
const BASE = process.env.TL_BASE || "http://127.0.0.1:5059";
const PAGE = process.env.TITLES_PATH || "/garage-concept?autoplay=0";      // the automatic clock off, so a scene is measured where it rests
const OUT = process.env.TITLES_OUT || "";
const SIZES = (process.env.TITLES_SIZES || "1920x1080,1440x900,1366x768,1280x720").split(",").map((s) => s.split("x").map(Number));
let failed = 0;
const report = (ok, label, detail = "") => { if (!ok) { failed++; } console.log((ok ? "PASS  " : "FAIL  ") + label + (detail ? "  (" + detail + ")" : "")); };

export default async function (b) {
  if (OUT) { mkdirSync(OUT, { recursive: true }); }
  await b.colorScheme(false);
  await b.open(BASE + "/about", 100);
  await b.eval(`localStorage.setItem("tv-motion", "1"); true`);   // motion on, so the camera is there: the scene is measured at the END of its push (the animations are played to their end below), where it crops most
  for (const [W, H] of SIZES) {
    await b.send("Emulation.setDeviceMetricsOverride", { width: W, height: H, deviceScaleFactor: 1, mobile: false });
    await b.open(BASE + PAGE, 1500);
    const slugs = JSON.parse(await b.eval(`JSON.stringify([...document.querySelectorAll("[data-stage] [data-pick]")].map((a) => a.dataset.pick))`));
    for (const slug of slugs) {
      await b.eval(`document.querySelector('[data-pick="${slug}"]').click(); true`);
      for (let i = 0; i < 80; i++) {
        const ready = await b.eval(`(() => { const p = document.querySelector('[data-panel="${slug}"]'); const im = p.querySelector("img"); return p.classList.contains("is-active") && !document.querySelector(".is-leaving") && im.complete && im.naturalWidth > 0; })()`).catch(() => false);
        if (ready) { break; }
        await b.sleep(150);
      }
      await b.sleep(2100);   // the entrance has mostly finished
      await b.eval(`document.getAnimations().forEach((a) => { try { a.finish(); } catch (e) {} }); true`);   // the slow settle of the picture is played to its end, where it rests
      const r = JSON.parse(await b.eval(`(() => { const p = document.querySelector('[data-panel="${slug}"]'); const art = p.querySelector(".gx-art"), im = art.querySelector("img");
        const box = art.getBoundingClientRect(); const cs = getComputedStyle(im); const [ox, oy] = cs.objectPosition.split(" ").map((v) => parseFloat(v) / 100);
        const nw = im.naturalWidth || 1600, nh = im.naturalHeight || 900; const contain = cs.objectFit === "contain"; const scale = contain ? Math.min(box.width / nw, box.height / nh) : Math.max(box.width / nw, box.height / nh); const dw = nw * scale, dh = nh * scale;
        const left = box.left - (dw - box.width) * ox, top = box.top - (dh - box.height) * oy;      // cover cuts the overflow; contain sets the whole picture inside the box
        // the camera: the picture is drawn through its transform (a push-in about the machine, a small drift), so the machine's box is moved by it too: the machine is checked where it really is at the end of the push
        const mx = new DOMMatrix(cs.transform), [oxs, oys] = cs.transformOrigin.split(" ").map(parseFloat), tox = box.left + oxs, toy = box.top + oys;
        const mapX = (x) => tox + mx.a * (x - tox) + mx.e, mapY = (y) => toy + mx.d * (y - toy) + mx.f;
        const subjects = (p.dataset.subject || "0,0,0,0").split(";").map((s) => { const [x0, y0, x1, y1] = s.split(",").map(Number); return { l: mapX(left + x0 * dw), t: mapY(top + y0 * dh), r: mapX(left + x1 * dw), b: mapY(top + y1 * dh) }; });
        const rect = (e) => { const q = e.getBoundingClientRect(); return { l: q.left, t: q.top, r: q.right, b: q.bottom, w: q.width, h: q.height, name: (e.className && e.className.toString().split(" ")[0]) || e.tagName.toLowerCase() }; };
        const words = [...p.querySelectorAll(".gx-kicker, .plate, .gx-sum, .gx-actions a, .gx-head__title, .gx-play")].map(rect).filter((q) => q.w > 0 && q.h > 0);
        const header = document.querySelector(".site-header").getBoundingClientRect();
        return JSON.stringify({ subjects, words, art: { l: box.left, t: box.top, r: box.right, b: box.bottom }, headerBottom: header.bottom, plate: p.dataset.plate }); })()`));
      let area = 0, shown = 0, crossing = [];
      for (const s of r.subjects) {
        const sw = s.r - s.l, sh = s.b - s.t;
        const inner = { l: s.l + sw * 0.05, r: s.r - sw * 0.05, t: s.t + sh * 0.05, b: s.b - sh * 0.05 };
        crossing = crossing.concat(r.words.filter((q) => q.l < inner.r && q.r > inner.l && q.t < inner.b && q.b > inner.t).map((q) => q.name));
        const cx = Math.max(0, Math.min(s.r, r.art.r) - Math.max(s.l, r.art.l)), cy = Math.max(0, Math.min(s.b, r.art.b) - Math.max(s.t, r.art.t));
        area += sw * sh; shown += cx * cy;
      }
      crossing = [...new Set(crossing)];
      const visible = shown / area;
      const tag = `${W}x${H} ${slug}`;
      report(crossing.length === 0, `${tag}: the words stay clear of the machine`, crossing.join(", "));
      report(visible >= 0.95, `${tag}: the whole machine is on screen`, (visible * 100).toFixed(1) + " percent");
      if (OUT) {
        await b.shot(`${OUT}${W}x${H}-${slug}.jpg`);
        await b.eval(`(() => { const d = document.createElement("canvas"); return true; })()`);
        const marks = JSON.stringify({ subjects: r.subjects, words: r.words });
        await b.eval(`(() => { const m = ${marks}; const draw = (b, color) => { const e = document.createElement("div"); e.className = "__mark"; e.style.cssText = ""; e.style.setProperty("position", "fixed"); e.style.setProperty("left", b.l + "px"); e.style.setProperty("top", b.t + "px"); e.style.setProperty("width", (b.r - b.l) + "px"); e.style.setProperty("height", (b.b - b.t) + "px"); e.style.setProperty("outline", "2px solid " + color); e.style.setProperty("z-index", "9999"); e.style.setProperty("pointer-events", "none"); document.body.appendChild(e); };
          m.subjects.forEach((s) => draw(s, "#ff2bd6")); m.words.forEach((w) => draw(w, "#25e8ff")); return true; })()`);
        await b.shot(`${OUT}${W}x${H}-${slug}-boxes.jpg`);
        await b.eval(`document.querySelectorAll(".__mark").forEach((e) => e.remove()); true`);
      }
    }
  }
  console.log(failed ? `\n${failed} FAILED` : "\nall passed");
  process.exitCode = failed ? 1 : 0;
}
