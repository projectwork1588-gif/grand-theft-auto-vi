// Layout shift while the Garage landing page loads, cycles and is scrolled from top to bottom, at desktop and phone sizes (Chrome's own layout-shift entries).
//   TL_BASE=http://127.0.0.1:5059 CLS_PATH=/vehicles node scripts/qa/cdp.mjs scripts/qa/garage_cls.mjs
const BASE = process.env.TL_BASE || "http://127.0.0.1:5059";
const PATH = process.env.CLS_PATH || "/vehicles?dwell=3";
export default async function (b) {
  await b.colorScheme(false);
  await b.open(BASE + "/about", 100);
  await b.eval(`localStorage.setItem("tv-motion", "1"); true`);
  for (const [W, H, dpr] of [[1440, 900, 1], [390, 844, 3]]) {
    await b.send("Emulation.setDeviceMetricsOverride", { width: W, height: H, deviceScaleFactor: dpr, mobile: W < 700 });
    await b.open(BASE + PATH, 0);
    await b.eval(`window.__cls = 0; window.__shifts = []; new PerformanceObserver((l) => { for (const e of l.getEntries()) { if (!e.hadRecentInput) { window.__cls += e.value; window.__shifts.push(+e.value.toFixed(4)); } } }).observe({ type: "layout-shift", buffered: true }); true`);
    await b.sleep(7000);                                   // two or three scenes change
    const total = await b.eval("document.documentElement.scrollHeight");
    for (let y = 0; y < total; y += 300) { await b.eval(`window.scrollTo(0, ${y}); true`); await b.sleep(120); }
    await b.sleep(2500);
    console.log(`${W}x${H} ${PATH}: layout shift ${(await b.eval("window.__cls")).toFixed(4)} over ${await b.eval("window.__shifts.length")} shifts`, await b.eval("JSON.stringify(window.__shifts.slice(0, 6))"));
  }
}
