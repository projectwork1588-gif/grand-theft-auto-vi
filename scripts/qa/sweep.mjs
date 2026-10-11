// Width sweep: horizontal overflow and header fit on every public route, 320 to 1920 px in steps of 20
// plus common device widths. Fails (exit 1) on sideways page scroll, an element past the viewport edge, or a header that does not fit.
// Start the app first, then:  node scripts/qa/cdp.mjs scripts/qa/sweep.mjs
// Environment: SWEEP_BASE (default http://127.0.0.1:5057), SWEEP_ROUTES (comma separated; on Windows Git Bash set MSYS_NO_PATHCONV=1).
export default async function (b) {
  const base = process.env.SWEEP_BASE || "http://127.0.0.1:5057";
  const routes = (process.env.SWEEP_ROUTES || "/,/characters,/vehicles,/regions,/locations,/missions,/about,/credits").split(",");
  const widths = [];
  for (let w = 320; w <= 1920; w += 20) widths.push(w);
  for (const w of [375, 390, 414, 768, 820, 1024, 1366, 1440, 1536]) if (!widths.includes(w)) widths.push(w);
  widths.sort((a, c) => a - c);
  const bad = [];
  for (const route of routes) {
    await b.size(1280, 900); await b.open(base + route, 500);
    for (const w of widths) {
      await b.size(w, 900, w < 700);
      await b.sleep(60);
      const r = await b.eval(`(() => {
        const vw = document.documentElement.clientWidth;
        const doc = document.documentElement.scrollWidth;
        let worst = null, over = 0;
        for (const el of document.querySelectorAll("body *")) {
          const cs = getComputedStyle(el);
          if (cs.position === "fixed" || cs.display === "none" || cs.visibility === "hidden") continue;
          // ignore anything inside a horizontal scroller (showroom track) or intentionally clipped
          let p = el.parentElement, clipped = false;
          while (p && p !== document.body) { const o = getComputedStyle(p); if (o.overflowX !== "visible") { clipped = true; break; } p = p.parentElement; }
          if (clipped) continue;
          const rc = el.getBoundingClientRect();
          if (rc.width === 0 || rc.height === 0) continue;
          if (rc.right > vw + 1 || rc.left < -1) { const o = Math.max(rc.right - vw, -rc.left); if (o > over) { over = o; worst = el.tagName.toLowerCase() + "." + (el.className && el.className.baseVal === undefined ? String(el.className).split(" ").slice(0,2).join(".") : ""); } }
        }
        const h = document.querySelector(".site-header");
        let header = null;
        if (h) { const inner = h.querySelector(".header-inner"); const kids = [...inner.children].filter(k => getComputedStyle(k).display !== "none").map(k => k.getBoundingClientRect()); header = { right: Math.max(...kids.map(k => k.right)), left: Math.min(...kids.map(k => k.left)), height: h.getBoundingClientRect().height, wrapped: h.scrollWidth > h.clientWidth }; }
        return { vw, doc, over: Math.round(over), worst, header };
      })()`);
      const issues = [];
      if (r.doc > r.vw) issues.push(`page scrolls sideways by ${r.doc - r.vw}px`);
      if (r.over > 1) issues.push(`element past edge by ${r.over}px (${r.worst})`);
      if (r.header && (r.header.right > r.vw + 0.5 || r.header.left < -0.5 || r.header.wrapped)) issues.push(`header does not fit (right=${Math.round(r.header.right)})`);
      if (issues.length) bad.push(`${route} @ ${w}: ${issues.join("; ")}`);
    }
  }
  if (bad.length) { process.exitCode = 1; }
  console.log(bad.length ? "FAILURES (" + bad.length + ")\n" + bad.join("\n") : "OK: no overflow or header issues across " + routes.length + " routes x " + widths.length + " widths");
}
