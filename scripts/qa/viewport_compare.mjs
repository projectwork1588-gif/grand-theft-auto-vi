// The same window on several pages, scrolled to the same steps: for a side-by-side judgement of art direction and pacing.
//   CMP_OUT=dir/ CMP_ROUTES=/,/characters,/vehicles CMP_W=1440 CMP_H=900 CMP_STEPS=4 node scripts/qa/cdp.mjs scripts/qa/viewport_compare.mjs
import { mkdirSync } from "node:fs";
const BASE = process.env.TL_BASE || "http://127.0.0.1:5059";
const OUT = process.env.CMP_OUT || "review/compare/";
const ROUTES = (process.env.CMP_ROUTES || "/,/characters,/vehicles").split(",");
const W = Number(process.env.CMP_W || 1440), H = Number(process.env.CMP_H || 900), STEPS = Number(process.env.CMP_STEPS || 4);
const name = (r) => (r.replace(/^\//, "").replace(/[\/?&=]+/g, "_") || "home");

export default async function (b) {
  mkdirSync(OUT, { recursive: true });
  await b.colorScheme(false);
  await b.send("Emulation.setDeviceMetricsOverride", { width: W, height: H, deviceScaleFactor: 1, mobile: W < 700 });
  await b.open(BASE + "/about", 100);
  await b.eval(`localStorage.setItem("tv-motion", "0"); true`);
  for (const route of ROUTES) {
    await b.open(BASE + route, 1500);
    await b.eval(`document.querySelectorAll("img").forEach((i) => { i.loading = "eager"; }); true`);
    const total = await b.eval("document.documentElement.scrollHeight");
    for (let y = 0; y < total; y += 450) { await b.eval(`window.scrollTo(0, ${y}); true`); await b.sleep(90); }
    await b.sleep(1500);
    for (let i = 0; i < STEPS; i++) {
      await b.eval(`window.scrollTo(0, ${i * H}); true`); await b.sleep(900);
      await b.shot(`${OUT}${W}-${name(route)}-${i}.jpg`);
    }
    console.log(route, "height", total);
  }
}
