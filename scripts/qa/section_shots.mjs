// One screenshot per chapter of the Garage landing page (the whole section, at full width), for before and after comparisons.
//   SEC_BASE=http://127.0.0.1:5059 SEC_OUT=dir/ SEC_W=1440 SEC_PATH=/garage-concept?autoplay=0 node scripts/qa/cdp.mjs scripts/qa/section_shots.mjs
// The window is made as tall as the page, every picture is loaded and decoded, motion is off (so nothing waits to be revealed), and each chapter is cut out by its box.
import { mkdirSync } from "node:fs";
const BASE = process.env.SEC_BASE || "http://127.0.0.1:5059";
const OUT = process.env.SEC_OUT || "review/sections/";
const W = Number(process.env.SEC_W || 1440);
const PATH = process.env.SEC_PATH || "/garage-concept?autoplay=0";
const CHAPTERS = (process.env.SEC_CHAPTERS || "performance,street,beyond,water").split(",");
const EXTRA = (process.env.SEC_EXTRA || "").split(";").filter(Boolean).map((x) => x.split(":"));     // name:css-selector pairs for other parts, e.g. customs:.gx-customs

export default async function (b) {
  mkdirSync(OUT, { recursive: true });
  await b.colorScheme(false);
  await b.send("Emulation.setDeviceMetricsOverride", { width: W, height: 900, deviceScaleFactor: 1, mobile: W < 700 });
  await b.open(BASE + "/about", 100);
  await b.eval(`localStorage.setItem("tv-motion", "0"); true`);
  await b.open(BASE + PATH, 1500);
  await b.eval(`document.querySelectorAll("img").forEach((i) => { i.loading = "eager"; }); true`);
  const total = await b.eval("document.documentElement.scrollHeight");
  for (let y = 0; y < total; y += 450) { await b.eval(`window.scrollTo(0, ${y}); true`); await b.sleep(100); }
  for (let i = 0; i < 80; i++) { const n = await b.eval(`[...document.images].filter((i) => i.getClientRects().length && (!i.complete || i.naturalWidth === 0)).length`); if (n <= 0) { break; } await b.sleep(250); }
  await b.eval(`Promise.all([...document.images].filter((i) => i.getClientRects().length).map((i) => i.decode().catch(() => {}))).then(() => true)`);
  const tall = Math.min(await b.eval("document.documentElement.scrollHeight"), 12000);
  await b.send("Emulation.setDeviceMetricsOverride", { width: W, height: tall, deviceScaleFactor: 1, mobile: W < 700 });
  await b.eval("window.scrollTo(0, 0); true"); await b.sleep(1500);
  await b.eval(`Promise.all([...document.images].filter((i) => i.getClientRects().length).map((i) => i.decode().catch(() => {}))).then(() => true)`);
  for (const key of CHAPTERS) {
    const box = JSON.parse(await b.eval(`(() => { const e = document.querySelector('.gx-chapter--${key}'); if (!e) return "null"; const r = e.getBoundingClientRect(); return JSON.stringify([r.left, r.top + scrollY, r.width, r.height]); })()`));
    if (!box) { console.log(key, "not found"); continue; }
    await b.shot(`${OUT}${W}-${key}.jpg`, { clip: { x: 0, y: box[1], width: W, height: Math.min(box[3], 4000) } });
    console.log(key, Math.round(box[3]), "px");
  }
  for (const [name, selector] of EXTRA) {
    const box = JSON.parse(await b.eval(`(() => { const e = document.querySelector(${JSON.stringify(selector)}); if (!e) return "null"; const r = e.getBoundingClientRect(); return JSON.stringify([r.left, r.top + scrollY, r.width, r.height]); })()`));
    if (!box) { console.log(name, "not found"); continue; }
    await b.shot(`${OUT}${W}-${name}.jpg`, { clip: { x: 0, y: box[1], width: W, height: Math.min(box[3], 4000) } });
    console.log(name, Math.round(box[3]), "px");
  }
  await b.eval(`localStorage.clear(); true`);
}
