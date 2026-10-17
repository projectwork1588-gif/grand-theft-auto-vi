// A screenshot of the Garage opening for every machine in the lineup, at each width: what a visitor sees after choosing it.
//   GARAGE_OUT=dir/ GARAGE_WIDTHS=1440,820,390 node scripts/qa/cdp.mjs scripts/qa/garage_stage_shots.mjs
const BASE = process.env.GARAGE_BASE || "http://127.0.0.1:5057";
const OUT = process.env.GARAGE_OUT || "review/garage-stage/";
const WIDTHS = (process.env.GARAGE_WIDTHS || "1440,820,390").split(",").map(Number);
const H = { 1920: 1080, 1440: 900, 1366: 768, 1280: 720, 1024: 768, 820: 1180, 390: 844, 360: 740, 320: 640 };

export default async function (b) {
  for (const w of WIDTHS) {
    await b.send("Emulation.setDeviceMetricsOverride", { width: w, height: H[w] || 900, deviceScaleFactor: 1, mobile: w < 700 });
    await b.open(BASE + "/about", 100);
    await b.eval(`localStorage.setItem("tv-motion", "0"); true`);
    await b.open(BASE + (process.env.GARAGE_PATH || "/vehicles"), 1500);
    const slugs = await b.eval(`[...document.querySelectorAll("[data-pick]")].map(a => a.dataset.pick)`);
    for (const slug of slugs) {
      await b.eval(`window.scrollTo(0, 0); document.querySelector('[data-pick="${slug}"]').click(); true`);
      for (let i = 0; i < 60; i++) {
        const ok = await b.eval(`(() => { const im = document.querySelector('[data-panel="${slug}"] img'); return im.complete && im.naturalWidth > 0; })()`);
        if (ok) { break; }
        await b.sleep(250);
      }
      await b.sleep(1300);
      await b.shot(`${OUT}${w}-stage-${slug}.jpg`);
    }
    console.log(w, "done");
  }
  await b.eval(`localStorage.clear(); true`);
}
