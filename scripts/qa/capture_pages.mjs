// Full-page and first-screen screenshots of any routes at any widths, with images loaded and motion at rest.
//   CAP_OUT=dir CAP_ROUTES=/vehicles,/vehicles/vapid-stanier CAP_WIDTHS=1440,390 CAP_MODE=full,first node scripts/qa/cdp.mjs scripts/qa/capture_pages.mjs
// Environment: TL_BASE (default http://127.0.0.1:5057), CAP_OUT (a folder ending in /), CAP_ROUTES, CAP_WIDTHS, CAP_MODE (full, first), CAP_MOTION=1 keeps motion on.
const BASE = process.env.TL_BASE || "http://127.0.0.1:5057";
const OUT = process.env.CAP_OUT || "review/capture/";
const ROUTES = (process.env.CAP_ROUTES || "/vehicles").split(",");
const WIDTHS = (process.env.CAP_WIDTHS || "1440,820,390").split(",").map(Number);
const MODES = (process.env.CAP_MODE || "full,first").split(",");
const H = { 1920: 1080, 1440: 900, 1280: 800, 1024: 768, 820: 1180, 768: 1024, 390: 844, 320: 640 };
const name = (r) => (r.replace(/^\//, "").replace(/[\/?&=]+/g, "_") || "home");

export default async function (b) {
  for (const w of WIDTHS) {
    await b.send("Emulation.setDeviceMetricsOverride", { width: w, height: H[w] || 900, deviceScaleFactor: 1, mobile: w < 700 });
    await b.open(BASE + "/about", 100);
    if (!process.env.CAP_MOTION) { await b.eval(`localStorage.setItem("tv-motion", "0"); true`); }
    for (const route of ROUTES) {
      await b.open(BASE + route, 1400);
      await b.eval(`document.querySelectorAll("img").forEach(i => { i.loading = "eager"; }); true`);
      const total = await b.eval("document.documentElement.scrollHeight");
      for (let y = 0; y < total; y += 450) { await b.eval(`window.scrollTo(0, ${y}); true`); await b.sleep(110); }
      for (let i = 0; i < 80; i++) { const n = await b.eval(`[...document.images].filter(i => i.getClientRects().length && (!i.complete || i.naturalWidth === 0)).length`); if (n <= 0) break; await b.sleep(250); }
      await b.eval(`Promise.all([...document.images].filter((i) => i.getClientRects().length).map((i) => i.decode().catch(() => {}))).then(() => true)`);
      await b.eval("window.scrollTo(0, 0); true"); await b.sleep(900);
      if (MODES.includes("first")) { await b.shot(`${OUT}${w}-${name(route)}-first.jpg`); }
      if (MODES.includes("full")) { await b.shot(`${OUT}${w}-${name(route)}-full.jpg`, { full: true }); }
    }
    console.log(w, "done", await b.eval(`document.documentElement.scrollWidth > document.documentElement.clientWidth`) ? "OVERFLOW" : "no overflow");
  }
  await b.eval(`localStorage.clear(); true`);
}
