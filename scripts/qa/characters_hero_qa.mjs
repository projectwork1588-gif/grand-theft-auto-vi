// The Characters opening picture, in a real browser: the right picture, loaded, sharp and sensibly sized at every size.
//   TL_BASE=http://127.0.0.1:5059 node scripts/qa/cdp.mjs scripts/qa/characters_hero_qa.mjs        (exit status 1 on any failure)
// At six sizes (with the pixel density a real device of that size has): no horizontal overflow, no console, page or request errors, the opening picture is Rockstar's own, was asked for at high
// priority, loaded, shown whole to the window's width, is SHARP (the file that was loaded has at least as many pixels as the screen needs: the cover size times the density, within 15 percent),
// and a phone is not sent the largest file. The heading and the cast navigation are on the screen and clear of the header.
const BASE = process.env.TL_BASE || "http://127.0.0.1:5059";
const SIZES = [[1920, 1080, 1], [1440, 900, 1], [1024, 768, 1], [820, 1180, 2], [390, 844, 2], [360, 740, 3]];
let failed = 0;
const report = (ok, label, d = "") => { if (!ok) { failed++; } console.log((ok ? "PASS  " : "FAIL  ") + label + (d ? "  (" + d + ")" : "")); };

export default async function (b) {
  const problems = [];
  b.on((d) => {
    if (d.method === "Runtime.exceptionThrown") { problems.push("exception: " + (d.params.exceptionDetails.exception?.description || d.params.exceptionDetails.text)); }
    if (d.method === "Runtime.consoleAPICalled" && d.params.type === "error") { problems.push("console: " + (d.params.args || []).map((a) => a.value || a.description).join(" ")); }
    if (d.method === "Network.loadingFailed" && !d.params.canceled) { problems.push("failed: " + d.params.errorText + " " + (d.params.type || "")); }
  });
  await b.send("Network.enable");
  await b.send("Network.setCacheDisabled", { cacheDisabled: true });
  await b.colorScheme(false);
  await b.open(BASE + "/about", 100);
  for (const [W, H, dpr] of SIZES) {
    await b.send("Emulation.setDeviceMetricsOverride", { width: W, height: H, deviceScaleFactor: dpr, mobile: W < 700 });
    problems.length = 0;
    await b.open(BASE + "/characters", 1500);
    await b.eval(`new Promise((r) => { const i = document.querySelector(".cast-open__bg img"); const t0 = Date.now(); const t = setInterval(() => { if ((i.complete && i.naturalWidth > 0) || Date.now() - t0 > 12000) { clearInterval(t); r(true); } }, 100); })`);
    await b.sleep(400);
    const tag = `${W}x${H}@${dpr}`;
    const r = JSON.parse(await b.eval(`JSON.stringify((() => { const i = document.querySelector(".cast-open__bg img"); const box = i.getBoundingClientRect(); const file = +((i.currentSrc.match(/imwidth=(\\d+)/) || [0, 0])[1]);
      // "cover": the picture is scaled until it fills the box in both directions, so the width it is drawn at is the larger of the box width and the box height times 16:9
      const drawn = Math.max(box.width, box.height * 16 / 9); const h1 = document.querySelector(".cast-open h1").getBoundingClientRect(); const hdr = document.querySelector(".site-header").getBoundingClientRect();
      return { official: i.currentSrc.startsWith("https://www.rockstargames.com/VI/_next/static/media/"), name: i.currentSrc.split("/").pop().split("?")[0], loaded: i.complete && i.naturalWidth > 0, eager: i.getAttribute("fetchpriority") === "high" && i.getAttribute("loading") !== "lazy", file, need: Math.round(drawn * devicePixelRatio), boxW: Math.round(box.width), vw: innerWidth,
        over: Math.max(document.documentElement.scrollWidth, document.body.scrollWidth) - innerWidth, h1Visible: h1.top >= hdr.bottom - 2 && h1.bottom <= innerHeight + 2 && h1.left >= 0, nav: !!document.querySelector("[data-cast-nav]"), opacity: getComputedStyle(i).opacity }; })()) `));
    report(r.official && /^Jason_and_Lucia_11\./.test(r.name), `${tag}: the opening is Rockstar's own "Jason and Lucia 11"`, r.name);
    report(r.loaded && r.eager && r.boxW >= r.vw - 1, `${tag}: it is loaded at high priority and fills the window's width`, JSON.stringify({ loaded: r.loaded, eager: r.eager, boxW: r.boxW, vw: r.vw }));
    report(r.file >= r.need * 0.85, `${tag}: it is sharp: the loaded file (${r.file} px wide) has the pixels the screen needs (${r.need})`);
    report(W >= 700 || r.file < 3840, `${tag}: a phone is not sent the largest file`, String(r.file));
    report(r.over <= 0 && r.h1Visible && r.nav, `${tag}: no horizontal overflow; the heading is on the screen and clear of the header`, JSON.stringify({ over: r.over, h1: r.h1Visible }));
    report(problems.length === 0, `${tag}: no console, page or request errors`, problems.slice(0, 3).join(" | "));
  }
  console.log(failed ? `\n${failed} FAILED` : "\nall passed");
  process.exitCode = failed ? 1 : 0;
}
