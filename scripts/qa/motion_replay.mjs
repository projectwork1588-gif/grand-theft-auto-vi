// Real-browser replay trace for the eight Characters landing tiles: down, up, down, up, with a playback count for every
// genuine visit (a visit starts when at least half the tile is in view below the sticky bars and ends when almost none is).
//   node scripts/qa/cdp.mjs scripts/qa/motion_replay.mjs      (RP_WIDTH=390 for a phone, RP_OUT=file.json to keep the trace)
// The listeners go in at document start (capture phase on the document), so no play is ever missed.
import { writeFileSync } from "node:fs";

const BASE = process.env.TL_BASE || "http://127.0.0.1:5057";
const WIDTH = Number(process.env.RP_WIDTH || 1440);
const ORDER = ["jason-duval", "lucia-caminos", "cal-hampton", "brian-heder", "boobie-ike", "dre-quan-priest", "real-dimez", "raul-bautista"];
let failures = 0;
const check = (name, ok, detail = "") => { if (!ok) { failures++; } console.log(`${ok ? "PASS" : "FAIL"}  ${name}${detail ? "  (" + detail + ")" : ""}`); };

export const HOOK = `(() => {
  window.__rp = { plays: [], ends: [], samples: [], visits: {} };
  const slugOf = (t) => { const h = t.closest("[id]:not(#main)"); return h ? h.id : location.pathname.split("/").pop(); };
  document.addEventListener("play", (e) => { const v = e.target; if (!(v instanceof HTMLVideoElement)) return; const t = v.closest("[data-portrait]"); if (t) window.__rp.plays.push({ slug: slugOf(t), t: performance.now(), ct: +v.currentTime.toFixed(2) }); }, true);
  document.addEventListener("ended", (e) => { const v = e.target; if (!(v instanceof HTMLVideoElement)) return; const t = v.closest("[data-portrait]"); if (t) window.__rp.ends.push({ slug: slugOf(t), t: performance.now() }); }, true);
  setInterval(() => {
    const inset = document.querySelector("[data-cast-nav]") ? 120 : 64;
    document.querySelectorAll("[data-portrait]").forEach((t) => {
      const r = t.getBoundingClientRect(); const slug = slugOf(t);
      const vis = Math.max(0, Math.min(r.bottom, innerHeight) - Math.max(r.top, inset)) / r.height;
      const st = window.__rp.visits; const o = st[slug] || (st[slug] = { open: null, list: [] });
      const now = performance.now();
      if (o.open === null && vis >= 0.5) { o.open = now; }
      if (o.open !== null && vis < 0.02) { o.list.push({ enter: o.open, leave: now }); o.open = null; }
    });
  }, 40);
})();`;

export default async function (b) {
  const mobile = WIDTH < 700;
  await b.send("Emulation.setDeviceMetricsOverride", { width: WIDTH, height: mobile ? 844 : 900, deviceScaleFactor: 1, mobile });
  await b.open(BASE + "/about", 200);
  await b.eval(`localStorage.clear(); true`);
  await b.send("Page.addScriptToEvaluateOnNewDocument", { source: HOOK });
  await b.open(BASE + "/characters", 2200);

  const state = (slug) => b.eval(`(() => { const t = document.querySelector("#${slug} [data-portrait]"); const v = t.querySelector("video");
    return { state: t.getAttribute("data-state"), ct: +v.currentTime.toFixed(2), paused: v.paused, rest: t.classList.contains("is-rest"), live: t.classList.contains("is-live") }; })()`);
  const playingNow = () => b.eval(`[...document.querySelectorAll("[data-portrait] video")].filter((v) => !v.paused).length`);
  const scrollTo = async (y, steps = 8) => {
    const from = await b.eval(`scrollY`);
    for (let s = 1; s <= steps; s++) { await b.eval(`window.scrollTo(0, ${from + ((y - from) * s) / steps}); true`); await b.sleep(40); }
  };
  const tileY = (slug) => b.eval(`document.querySelector("#${slug} [data-portrait]").getBoundingClientRect().top + scrollY - innerHeight * 0.4`);
  const waitState = async (slug, want, ms = 14000) => { for (let t = 0; t < ms / 150; t++) { if ((await state(slug)).state === want) { return true; } await b.sleep(150); } return false; };
  let maxPlaying = 0;
  const watch = async () => { maxPlaying = Math.max(maxPlaying, await playingNow()); };
  const timer = setInterval(() => { watch().catch(() => {}); }, 120);

  const pass = async (order, label) => {
    const notRested = [];
    for (const slug of order) {
      await scrollTo(await tileY(slug));
      if (!(await waitState(slug, "rested"))) { notRested.push(slug); }
      await b.sleep(400);
    }
    check(`${label}: every tile played through to its resting artwork`, notRested.length === 0, notRested.join(",") || "all eight");
  };

  await pass(ORDER, "1. first scroll down");
  await pass([...ORDER].reverse(), "2. scroll back up");
  await pass(ORDER, "3. scroll down again");
  await pass([...ORDER].reverse(), "4. scroll up again");
  clearInterval(timer);
  check("never two clips at once during the four passes", maxPlaying <= 1, "max " + maxPlaying);

  // ---- the trace: plays per genuine visit, per character
  const rp = await b.eval(`window.__rp`);
  const end = await b.eval(`performance.now()`);
  const table = [];
  let loops = 0, missed = 0;
  for (const slug of ORDER) {
    const o = rp.visits[slug] || { open: null, list: [] };
    const visits = [...o.list, ...(o.open !== null ? [{ enter: o.open, leave: end }] : [])];
    const row = visits.map((v) => rp.plays.filter((p) => p.slug === slug && p.t >= v.enter - 50 && p.t <= v.leave + 50).length);
    table.push({ slug, visits: visits.length, perVisit: row, passThroughs: visits.filter((v, i) => row[i] === 0 && v.leave - v.enter <= 1500).length, plays: rp.plays.filter((p) => p.slug === slug).length, startedAtZero: rp.plays.filter((p) => p.slug === slug && p.ct > 0.2).length });
    // a visit shorter than the dwell plus a moment is a pass-through (the tile is not given a chance to start)
    visits.forEach((v, i) => { if (row[i] > 1) { loops++; } if (row[i] === 0 && v.leave - v.enter > 1500) { missed++; } });
  }
  console.log("\nplays per genuine visit (down, up, down, up; a tile resting in view between passes stays one visit):");
  for (const r of table) { console.log("  " + r.slug.padEnd(16) + " visits " + r.visits + "  plays per visit [" + r.perVisit.join(", ") + "]  total plays " + r.plays); }
  check("no visit ever plays a tile twice (no loops)", loops === 0, loops + " visits with more than one play");
  check("no visit passed without its tile playing", missed === 0, missed + " visits with no play");
  check("every character was visited more than once and replayed", table.every((r) => r.visits - r.passThroughs >= 2 && r.plays >= r.visits - r.passThroughs), table.map((r) => r.visits + "/" + r.plays).join(" "));
  check("every play started from the beginning of its sequence", table.every((r) => r.startedAtZero === 0));
  if (process.env.RP_OUT) { writeFileSync(process.env.RP_OUT, JSON.stringify({ width: WIDTH, table, plays: rp.plays.length }, null, 1)); }

  if (!mobile) {
    // ---- stay near a tile for longer than its sequence: it plays once and does not loop
    await scrollTo(0);
    await b.sleep(1500);
    const before = await b.eval(`window.__rp.plays.filter((p) => p.slug === "cal-hampton").length`);
    await scrollTo(await tileY("cal-hampton"));
    await waitState("cal-hampton", "rested");
    await b.sleep(9000);
    const after = await b.eval(`window.__rp.plays.filter((p) => p.slug === "cal-hampton").length`);
    check("staying 9 s after it finished: Cal played once and did not loop", after - before === 1, `${after - before} plays`);

    // ---- Cal and Brian share a row: approached from above and from below, each plays once, one after the other
    for (const [from, label] of [["top", "from above"], ["bottom", "from below"]]) {
      await scrollTo(from === "top" ? 0 : await b.eval(`document.documentElement.scrollHeight`), 6);
      await b.sleep(1800);
      const mark = await b.eval(`window.__rp.plays.length`);
      await scrollTo(await tileY("cal-hampton"), 6);
      let seen = [];
      for (let t = 0; t < 90 && seen.length < 2; t++) {
        await b.sleep(150);
        seen = (await b.eval(`window.__rp.plays.slice(${mark}).map((p) => p.slug)`)).filter((s) => s === "cal-hampton" || s === "brian-heder");
      }
      await b.sleep(1500);
      const row = await b.eval(`window.__rp.plays.slice(${mark}).map((p) => p.slug)`);
      check(`Cal and Brian ${label}: both play, Cal first, once each`, row.filter((s) => s === "cal-hampton").length === 1 && row.filter((s) => s === "brian-heder").length === 1 && row.indexOf("cal-hampton") < row.indexOf("brian-heder"), row.join(" > "));
    }

    // ---- Boobie, Dre'Quan and Real Dimez approached from either direction
    for (const [from, label] of [["top", "from above"], ["bottom", "from below"]]) {
      await scrollTo(from === "top" ? 0 : await b.eval(`document.documentElement.scrollHeight`), 6);
      await b.sleep(1800);
      const mark = await b.eval(`window.__rp.plays.length`);
      await scrollTo(await tileY("dre-quan-priest"), 6);
      for (let t = 0; t < 120; t++) {
        await b.sleep(150);
        const got = await b.eval(`window.__rp.plays.slice(${mark}).map((p) => p.slug)`);
        if (["boobie-ike", "dre-quan-priest", "real-dimez"].every((s) => got.includes(s))) { break; }
      }
      await b.sleep(1500);
      const row = (await b.eval(`window.__rp.plays.slice(${mark}).map((p) => p.slug)`)).filter((s) => ["boobie-ike", "dre-quan-priest", "real-dimez"].includes(s));
      check(`Boobie, Dre'Quan, Real Dimez ${label}: all three play, once each`, ["boobie-ike", "dre-quan-priest", "real-dimez"].every((s) => row.filter((x) => x === s).length === 1), row.join(" > "));
    }

    // ---- revisit the trouble spots repeatedly: every genuine return plays each tile once, never twice, never none
    for (const [group, label, anchor] of [[["cal-hampton", "brian-heder"], "Cal and Brian", "cal-hampton"], [["boobie-ike", "dre-quan-priest", "real-dimez"], "Boobie, Dre'Quan and Real Dimez", "dre-quan-priest"]]) {
      const mark = await b.eval(`window.__rp.plays.length`);
      for (let round = 0; round < 4; round++) {
        await scrollTo(round % 2 ? await b.eval(`document.documentElement.scrollHeight`) : 0, 5);
        await b.sleep(1600);
        await scrollTo(await tileY(anchor), 6);
        for (let t = 0; t < 140; t++) {
          await b.sleep(150);
          const got = await b.eval(`window.__rp.plays.slice(${mark}).map((p) => p.slug)`);
          if (group.every((g) => got.filter((x) => x === g).length >= round + 1)) { break; }
        }
        await b.sleep(900);
      }
      const got = await b.eval(`window.__rp.plays.slice(${mark}).map((p) => p.slug)`);
      const counts = group.map((g) => got.filter((x) => x === g).length);
      check(`${label}: four separate returns, each tile played exactly four times`, counts.every((n) => n === 4), group.map((g, i) => g + "=" + counts[i]).join(" "));
    }

    // ---- a fast scroll away in the middle of a playback: it returns to a clean artwork, and plays again on return
    await scrollTo(0, 4); await b.sleep(1500);
    await scrollTo(await tileY("raul-bautista"), 6);
    for (let t = 0; t < 30 && (await state("raul-bautista")).state !== "playing"; t++) { await b.sleep(150); }
    await b.sleep(1200);
    await scrollTo(0, 2);
    await b.sleep(1300);
    const cut = await state("raul-bautista");
    check("fast scroll away mid-playback: back to a clean artwork, armed", cut.state === "armed" && cut.paused && cut.ct < 0.1 && !cut.live && !cut.rest, JSON.stringify(cut));
    const mark2 = await b.eval(`window.__rp.plays.length`);
    await scrollTo(await tileY("raul-bautista"), 6);
    check("...and a later visit plays it again, to the end", await waitState("raul-bautista", "rested", 14000) && (await b.eval(`window.__rp.plays.slice(${mark2}).filter((p) => p.slug === "raul-bautista").length`)) === 1);

    // ---- keyboard / jump bar: return to an already viewed character
    await b.eval(`document.querySelector("[data-cast-nav] a[href='#jason-duval']").click(); true`);
    await b.sleep(3500);
    const mark3 = await b.eval(`window.__rp.plays.length`);
    await b.eval(`document.querySelector("[data-cast-nav] a[href='#cal-hampton']").click(); true`);
    check("jump bar back to Cal (already seen): he plays again, once", await waitState("cal-hampton", "rested", 16000) && (await b.eval(`window.__rp.plays.slice(${mark3}).filter((p) => p.slug === "cal-hampton").length`)) === 1);
  }

  const dup = await b.eval(`performance.getEntriesByType("resource").filter((r) => /\\.mp4/.test(r.name)).map((r) => r.name.split("/").pop())`);
  check("no video file was downloaded twice", new Set(dup).size === dup.length, dup.length + " requests for " + new Set(dup).size + " files");
  console.log(failures ? `\n${failures} FAILED` : "\nall passed");
  process.exitCode = failures ? 1 : 0;
}
