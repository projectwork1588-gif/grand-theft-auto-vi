// The site header while scrolling the Garage: is the logo and the wordmark ever clipped, moved or covered? Checked with real mouse-wheel scrolling (not scrollTo),
// at the window sizes and display scalings laptops use (125 and 150 percent scaling make fractional pixel ratios), on the opening, the collection and the end.
//   node scripts/qa/cdp.mjs scripts/qa/garage_header.mjs        (TL_BASE, HEADER_PATH; exit status 1 on any problem)
const BASE = process.env.TL_BASE || "http://127.0.0.1:5057";
const PAGE = process.env.HEADER_PATH || "/vehicles";
const SETUPS = [[1536, 730, 1.25], [1280, 680, 1.5], [1440, 900, 1], [1920, 940, 1], [390, 844, 3], [412, 800, 2.625]];
let failed = 0;

export default async function (b) {
  await b.colorScheme(false);
  await b.open(BASE + "/about", 100);
  await b.eval(`localStorage.setItem("tv-motion", "1"); true`);
  for (const [W, H, dpr] of SETUPS) {
    await b.send("Emulation.setDeviceMetricsOverride", { width: W, height: H, deviceScaleFactor: dpr, mobile: W < 700 });
    await b.open(BASE + PAGE, 2200);
    const total = await b.eval("document.documentElement.scrollHeight");
    let samples = 0, bad = [];
    for (let target = 0; target < total - H; target += Math.round(H * 0.6)) {
      // scroll with the wheel, as a visitor does, then let it settle
      for (let guard = 0; guard < 60; guard++) {
        const y = await b.eval("scrollY");
        if (Math.abs(y - target) < 6) { break; }
        await b.send("Input.dispatchMouseEvent", { type: "mouseWheel", x: W / 2, y: H / 2, deltaX: 0, deltaY: Math.sign(target - y) * Math.min(240, Math.abs(target - y)) });
        await b.sleep(50);
      }
      await b.sleep(350);
      const r = JSON.parse(await b.eval(`(() => { const R = (e) => { const r = e.getBoundingClientRect(); return [r.left, r.top, r.right, r.bottom]; };
        const h = document.querySelector(".site-header"), em = document.querySelector(".brand__emblem"), t = document.querySelector(".brand__title"), s = document.querySelector(".brand__sub");
        const over = (e) => { const r = e.getBoundingClientRect(); const el = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2); return !(el && (el === e || e.contains(el) || el.closest(".brand"))); };
        const hb = R(h); return JSON.stringify({ y: Math.round(scrollY), header: hb, emblem: R(em), title: R(t), sub: R(s), covered: over(em) || over(t) || over(s), solid: h.classList.contains("is-solid"), pos: getComputedStyle(h).position }); })()`));
      samples++;
      const inside = (c) => c[1] >= r.header[1] - 0.5 && c[3] <= r.header[3] + 0.5 && c[0] >= -0.5;
      if (r.header[1] !== 0 || r.pos !== "fixed" || !inside(r.emblem) || !inside(r.title) || !inside(r.sub) || r.covered || (r.y > 60 && !r.solid)) { bad.push(JSON.stringify(r)); }
    }
    if (bad.length) { failed++; }
    console.log((bad.length ? "FAIL  " : "PASS  ") + `${W}x${H} at ${dpr}x: logo and wordmark whole, in place and uncovered at ${samples} wheel-scroll positions of ${PAGE}`, bad.slice(0, 2).join(" | "));
  }
  console.log(failed ? `\n${failed} FAILED` : "\nall passed");
  process.exitCode = failed ? 1 : 0;
}
