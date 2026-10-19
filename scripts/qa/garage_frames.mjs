// Frame timing of the Garage opening in this browser (headless Chrome, SOFTWARE rendering: not a GPU laptop or a phone, so it is a pessimistic floor, not a claim about real hardware).
//   TL_BASE=http://127.0.0.1:5059 FRAMES_PATH="/vehicles?autoplay=0" node scripts/qa/cdp.mjs scripts/qa/garage_frames.mjs
const BASE = process.env.TL_BASE || "http://127.0.0.1:5059";
const PATH = process.env.FRAMES_PATH || "/vehicles?autoplay=0";
export default async function (b) {
  await b.colorScheme(false);
  await b.send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  await b.open(BASE + "/about", 100);
  await b.eval(`localStorage.setItem("tv-motion", "1"); true`);
  await b.open(BASE + PATH, 2500);
  const measure = (label, action, ms) => b.eval(`new Promise(res => { const t = []; let last = performance.now(); const stop = last + ${ms}; ${action}; function f(now) { t.push(now - last); last = now; if (now < stop) requestAnimationFrame(f); else { t.shift(); t.sort((a, b) => a - b); const q = (p) => t[Math.min(t.length - 1, Math.floor(t.length * p))]; res(JSON.stringify({ label: ${JSON.stringify(label)}, frames: t.length, median: +q(.5).toFixed(1), p95: +q(.95).toFixed(1), max: +t[t.length - 1].toFixed(1), over50: t.filter(x => x > 50).length })); } } requestAnimationFrame(f); })`);
  for (const slug of ["vapid-dominator-buggy", "vapid-stanier", "vapid-ganado", "crest-kayak", "grotti-cheetah"]) {
    await b.eval(`document.querySelector('[data-panel="${slug}"] img').loading = "eager"; true`); await b.sleep(1200);
    console.log(await measure("scene change to " + slug, `document.querySelector('[data-pick="${slug}"]').click()`, 2200));
  }
  console.log(await measure("a scene at rest (drift running)", "", 2000));
  console.log(await measure("scrolling the landing page", `(() => { let y = 0; const id = setInterval(() => { y += 60; scrollTo(0, y); if (y > 5000) clearInterval(id); }, 16); })()`, 3500));
}
