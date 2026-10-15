// Real-browser timeline of the Characters motion portraits: what each one actually does when it is scrolled into view.
//   node scripts/qa/cdp.mjs scripts/qa/motion_timeline.mjs
// Environment: TL_BASE (default http://127.0.0.1:5057), TL_ROUTE (default /characters), TL_WIDTH (default 1440),
//              TL_REPEAT (default 0: scroll through the page again this many times, to catch replays and glitches).
// For every tile it reports (decoded by the browser, not read from metadata): how long the file is, when it started,
// the video time at which the clip took over from the still, how long it took to end in real time, the playback rate
// between frames, frames presented against frames expected and how many it dropped, pauses before the end and replays.
import { writeFileSync } from "node:fs";

export default async function (b) {
  const base = process.env.TL_BASE || "http://127.0.0.1:5057";
  const route = process.env.TL_ROUTE || "/characters";
  const width = Number(process.env.TL_WIDTH || 1440);
  const repeat = Number(process.env.TL_REPEAT || 0);
  const mobile = width < 700;
  await b.send("Emulation.setDeviceMetricsOverride", { width, height: mobile ? 844 : 900, deviceScaleFactor: 1, mobile });
  await b.open(base + "/about", 300);
  await b.eval(`localStorage.clear(); true`);
  // the listeners go in before the page's own script runs, so a tile that is already in view at load (a profile page) is seen from its first frame
  const hook = `(() => {
    window.__log = [];
    const attach = () => {
      [...document.querySelectorAll("[data-portrait]")].forEach((t, i) => {
        const v = t.querySelector("video");
        const host = t.closest("[id]:not(#main)");
        const slug = host ? host.id : location.pathname.split("/").pop();
        const note = (ev) => window.__log.push({ i, slug, ev, w: performance.now(), ct: +v.currentTime.toFixed(3), live: t.classList.contains("is-live") });
        ["play", "playing", "pause", "ended", "seeking", "seeked", "waiting", "stalled", "error"].forEach((e) => v.addEventListener(e, () => note(e)));
        let last = 0;
        v.addEventListener("timeupdate", () => { const n = performance.now(); if (n - last > 90) { last = n; note("tick"); } });
        new MutationObserver(() => note("class:" + (t.classList.contains("is-live") ? "live" : "") + (t.classList.contains("is-rest") ? " rest" : ""))).observe(t, { attributes: true, attributeFilter: ["class"] });
      });
    };
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", attach); else attach();
  })();`;
  await b.send("Page.addScriptToEvaluateOnNewDocument", { source: hook });
  await b.open(base + route, 1800);
  const count = await b.eval(`document.querySelectorAll("[data-portrait]").length`);
  const pass = async () => {
    for (let i = 0; i < count; i++) {
      // a natural scroll: a few wheel-sized steps toward the tile, then wait for it to finish (or give up)
      const target = await b.eval(`(() => { const r = document.querySelectorAll("[data-portrait]")[${i}].getBoundingClientRect(); return r.top + scrollY - innerHeight * 0.4; })()`);
      const start = await b.eval(`scrollY`);
      for (let s = 1; s <= 8; s++) { await b.eval(`window.scrollTo(0, ${start + ((target - start) * s) / 8}); true`); await b.sleep(40); }
      for (let t = 0; t < 40; t++) {
        await b.sleep(250);
        const done = await b.eval(`document.querySelectorAll("[data-portrait]")[${i}].classList.contains("is-rest")`);
        if (done) break;
      }
      await b.sleep(250);
    }
  };
  await pass();
  for (let r = 0; r < repeat; r++) { await b.eval(`window.scrollTo(0, 0); true`); await b.sleep(600); await pass(); }
  const result = await b.eval(`(() => ({ log: window.__log, q: [...document.querySelectorAll("[data-portrait] video")].map((v) => {
    const qy = v.getVideoPlaybackQuality ? v.getVideoPlaybackQuality() : {};
    return { src: v.currentSrc.split("/").pop(), duration: +v.duration.toFixed(3), total: qy.totalVideoFrames, dropped: qy.droppedVideoFrames };
  }) }))()`);
  const rows = [];
  for (let i = 0; i < count; i++) {
    const ev = result.log.filter((e) => e.i === i);
    const slug = ev[0] ? ev[0].slug : String(i);
    const plays = ev.filter((e) => e.ev === "playing");
    const firstPlay = plays[0];
    const live = ev.find((e) => e.ev.startsWith("class:live"));
    const ended = ev.find((e) => e.ev === "ended");
    const ticks = ev.filter((e) => e.ev === "tick" && firstPlay && e.w >= firstPlay.w && (!ended || e.w <= ended.w));
    const rates = [];
    for (let k = 1; k < ticks.length; k++) { const dw = (ticks[k].w - ticks[k - 1].w) / 1000; const dc = ticks[k].ct - ticks[k - 1].ct; if (dw > 0.05 && dc >= 0) rates.push(dc / dw); }
    rates.sort((x, y) => x - y);
    const q = result.q[i] || {};
    rows.push({
      slug, file: q.src, fileSeconds: q.duration, started: !!firstPlay, playCount: ev.filter((e) => e.ev === "play").length,
      takeoverAtVideoTime: live ? live.ct : null,
      realSecondsToEnd: firstPlay && ended ? +((ended.w - firstPlay.w) / 1000).toFixed(2) : null,
      rate: rates.length ? +rates[Math.floor(rates.length / 2)].toFixed(2) : null,
      framesPresented: q.total, framesExpected: Math.round((q.duration || 0) * 30), dropped: q.dropped,
      pausesBeforeEnd: ev.filter((e) => e.ev === "pause" && (!ended || e.w < ended.w) && e.ct < (q.duration || 0) - 0.1).length,
      stalls: ev.filter((e) => e.ev === "waiting" || e.ev === "stalled").length,
    });
  }
  if (process.env.TL_RAW) {
    const i = Number(process.env.TL_RAW);
    const first = result.log.find((e) => e.i === i);
    console.error(result.log.filter((e) => e.i === i && e.ev !== "tick").map((e) => `${((e.w - (first ? first.w : 0)) / 1000).toFixed(2)}s ${e.ev} ct=${e.ct}`).join(String.fromCharCode(10)));
  }
  console.log(JSON.stringify(rows, null, 1));
  const out = process.env.TL_OUT;
  if (out) writeFileSync(out, JSON.stringify({ route, width, rows }, null, 1));
}
