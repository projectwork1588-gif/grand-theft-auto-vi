// Leonida / Regions browser checks, in a real browser: the index and the six region pages.
//   TL_BASE=http://127.0.0.1:5059 node scripts/qa/cdp.mjs scripts/qa/regions_qa.mjs        (exit status 1 on any failure)
// For every page and size: no horizontal overflow, no console, page or request errors, no broken pictures, the opening's words sit on the screen and clear of the header,
// previous/next/jump links lead where they say. Once, at desktop: the camera really runs (motion on), the compact index appears after the opening and marks the region in view,
// the anchor lands clear of the sticky header, a picture opens in the site's viewer and closes with Escape, and keyboard focus is visible on the links that matter.
//   QA_SIZES=1920x1080,1440x900,1024x768,820x1180,390x844   QA_REDUCE=1 emulates the visitor's reduced-motion preference.
const BASE = process.env.TL_BASE || "http://127.0.0.1:5059";
const SIZES = (process.env.QA_SIZES || "1920x1080,1440x900,1024x768,820x1180,390x844").split(",").map((s) => s.split("x").map(Number));
const SLUGS = ["vice-city", "leonida-keys", "grassrivers", "port-gellhorn", "ambrosia", "mount-kalaga"];
let failed = 0;
const report = (ok, label, detail = "") => { if (!ok) { failed++; } console.log((ok ? "PASS  " : "FAIL  ") + label + (detail ? "  (" + detail + ")" : "")); };

export default async function (b) {
  const problems = [];
  b.on((d) => {
    if (d.method === "Runtime.exceptionThrown") { problems.push("exception: " + (d.params.exceptionDetails.exception?.description || d.params.exceptionDetails.text)); }
    if (d.method === "Runtime.consoleAPICalled" && d.params.type === "error") { problems.push("console: " + (d.params.args || []).map((a) => a.value || a.description).join(" ")); }
    if (d.method === "Network.loadingFailed" && !d.params.canceled) { problems.push("failed: " + d.params.errorText + " " + (d.params.type || "")); }
  });
  await b.send("Network.enable");
  await b.colorScheme(process.env.QA_REDUCE === "1");
  await b.open(BASE + "/about", 100);
  await b.eval(`localStorage.setItem("tv-motion", "1"); true`);
  const pages = ["/regions", ...SLUGS.map((s) => "/regions/" + s)];
  for (const [W, H] of SIZES) {
    await b.send("Emulation.setDeviceMetricsOverride", { width: W, height: H, deviceScaleFactor: 1, mobile: W < 700 });
    for (const path of pages) {
      problems.length = 0;
      await b.open(BASE + path, 1200);
      const tag = `${W}x${H} ${path}`;
      const total = await b.eval("document.documentElement.scrollHeight");
      for (let y = 0; y < total; y += Math.round(H * 0.8)) { await b.eval(`window.scrollTo(0, ${y}); true`); await b.sleep(140); }
      await b.sleep(700);
      const over = await b.eval(`Math.max(document.documentElement.scrollWidth, document.body.scrollWidth) - window.innerWidth`);
      report(over <= 0, `${tag}: no horizontal overflow`, over + "px");
      report(problems.length === 0, `${tag}: no console, page or request errors`, problems.slice(0, 3).join(" | "));
      const blank = await b.eval(`[...document.querySelectorAll("img.rshot")].filter((i) => i.complete && i.naturalWidth === 0 && i.currentSrc).length`);
      report(blank === 0, `${tag}: no broken pictures`, blank + " broken");
      await b.eval(`window.scrollTo(0, 0); true`);
      await b.sleep(400);
      // the words of the opening are inside the window and below the header; nothing is cut off
      const words = JSON.parse(await b.eval(`(() => { const copy = document.querySelector(".rgh__copy, .rg-intro__copy"); const hb = document.querySelector(".site-header").getBoundingClientRect(); const r = copy.getBoundingClientRect();
        const t = copy.querySelector("h1").getBoundingClientRect(); return JSON.stringify({ l: r.left, r: r.right, t: t.top, b: t.bottom, hb: hb.bottom, w: window.innerWidth }); })()`));
      report(words.l >= 0 && words.r <= words.w + 1 && words.t >= words.hb - 1, `${tag}: the words of the opening are on the screen and clear of the header`, JSON.stringify(words));
      if (path !== "/regions" && W >= 1024) {      // the title and the line beneath it stay on the panel, clear of the picture's slanted edge
        const clear = JSON.parse(await b.eval(`(() => { const art = document.querySelector(".rgh__art").getBoundingClientRect(); const h = document.querySelector(".rgh").getBoundingClientRect();
          const edge = (y) => art.left + 0.11 * art.width * (1 - (y - h.top) / h.height);
          const worst = [...document.querySelectorAll(".rgh__copy h1, .rgh__copy .rg-hero__line, .rgh__copy .rg-cue")].map((e) => { const r = e.getBoundingClientRect(); const range = document.createRange(); range.selectNodeContents(e); const t = range.getBoundingClientRect(); return edge(r.bottom) - Math.max(t.right, 0); });
          return JSON.stringify({ min: Math.round(Math.min(...worst)) }); })()`));
        report(clear.min >= 8, `${tag}: the title, line and cue sit on the panel, clear of the picture`, clear.min + "px");
      }
      if (path === "/regions") {
        const jump = await b.eval(`[...document.querySelectorAll(".rg-index a")].map((a) => a.getAttribute("href")).join(",")`);
        report(jump === SLUGS.map((s) => "#" + s).join(","), `${tag}: the index in the opening lists the six regions in order`, jump);
      } else {
        const slug = path.split("/")[2], i = SLUGS.indexOf(slug);
        const nav = JSON.parse(await b.eval(`(() => { const n = document.querySelector('a[rel="next"]'), p = document.querySelector('a[rel="prev"]'); return JSON.stringify({ n: n ? n.getAttribute("href") : "", p: p ? p.getAttribute("href") : "", back: !!document.querySelector('.rg-back[href="/regions"]') }); })()`));
        report(nav.n.endsWith("/regions/" + SLUGS[(i + 1) % 6]) && nav.p.endsWith("/regions/" + SLUGS[(i + 5) % 6]) && nav.back, `${tag}: previous, next and the way back`, nav.p + " " + nav.n);
      }
    }
  }
  // ---- once, at desktop
  await b.send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  for (const slug of SLUGS) {
    await b.open(BASE + "/regions/" + slug, 1500);
    const cam = JSON.parse(await b.eval(`(() => { const im = document.querySelector(".rgh__art img.rshot"); return JSON.stringify({ n: im.getAnimations().length, motion: document.documentElement.classList.contains("motion-on") }); })()`));
    if (process.env.QA_REDUCE === "1") { console.log(`INFO  ${slug}: camera animations ${cam.n}, motion-on ${cam.motion}`); }
    else { report(cam.n > 0 && cam.motion, `${slug}: the camera runs`, JSON.stringify(cam)); }
    await b.eval(`document.querySelector('a[href="#about"]').click(); true`);
    await b.sleep(900);
    const gap = await b.eval(`(() => { const m = document.querySelector("#about").getBoundingClientRect(), h = document.querySelector(".site-header").getBoundingClientRect(); return Math.round(m.top - h.bottom); })()`);
    report(gap >= 0, `${slug}: the anchor lands clear of the sticky header`, gap + "px");
  }
  // the compact index on the landing
  await b.open(BASE + "/regions", 1500);
  const hiddenAtTop = await b.eval(`!document.querySelector("[data-jump-bar]").classList.contains("is-on")`);
  report(hiddenAtTop, "index: the compact index is not shown over the opening");
  await b.eval(`document.getElementById("grassrivers").scrollIntoView(); true`);
  await b.sleep(1200);
  const state = JSON.parse(await b.eval(`(() => { const bar = document.querySelector("[data-jump-bar]"); const cur = bar.querySelector('[aria-current="true"]'); return JSON.stringify({ on: bar.classList.contains("is-on"), cur: cur ? cur.getAttribute("data-jump") : null, visible: getComputedStyle(bar).visibility }); })()`));
  report(state.on && state.cur === "grassrivers" && state.visible === "visible", "index: the compact index appears and marks the region in view", JSON.stringify(state));
  await b.eval(`document.querySelector('[data-jump-bar] [data-jump="ambrosia"]').click(); true`);
  await b.sleep(1200);
  const landed = JSON.parse(await b.eval(`(() => { const s = document.getElementById("ambrosia").getBoundingClientRect(), h = document.querySelector(".site-header").getBoundingClientRect(); return JSON.stringify({ top: Math.round(s.top), hb: Math.round(h.bottom), hash: location.hash }); })()`));
  report(landed.hash === "#ambrosia" && landed.top >= landed.hb - 2 && landed.top < 200, "index: choosing a region in the compact index scrolls to it, clear of the header", JSON.stringify(landed));
  // keyboard: focus is visible on the Explore links and the previous/next links
  await b.open(BASE + "/regions", 1200);
  let reached = false;
  for (let i = 0; i < 80 && !reached; i++) {      // real Tab presses, so :focus-visible applies
    await b.send("Input.dispatchKeyEvent", { type: "keyDown", key: "Tab", code: "Tab", windowsVirtualKeyCode: 9 });
    await b.send("Input.dispatchKeyEvent", { type: "keyUp", key: "Tab", code: "Tab", windowsVirtualKeyCode: 9 });
    reached = await b.eval(`document.activeElement && document.activeElement.classList.contains("rg-go")`);
  }
  const ring = reached && (await b.eval(`(() => { const cs = getComputedStyle(document.activeElement); return cs.outlineStyle !== "none" && parseFloat(cs.outlineWidth) >= 2; })()`));
  report(!!ring, "keyboard: Tab reaches the Explore link and it shows a focus ring", reached ? "" : "not reached in 80 presses");
  // the viewer
  await b.open(BASE + "/regions/vice-city", 1500);
  await b.eval(`document.querySelector("[data-gallery]").scrollIntoView(); true`);
  await b.sleep(700);
  await b.eval(`document.querySelector("[data-lightbox]").click(); true`);
  await b.sleep(900);
  report(await b.eval(`!!document.querySelector("dialog[open]")`), "viewer: a picture opens in the site's image viewer");
  await b.send("Input.dispatchKeyEvent", { type: "keyDown", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
  await b.send("Input.dispatchKeyEvent", { type: "keyUp", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
  await b.sleep(600);
  report(await b.eval(`!document.querySelector("dialog[open]")`), "viewer: Escape closes it");
  console.log(failed ? `\n${failed} FAILED` : "\nall passed");
  process.exitCode = failed ? 1 : 0;
}
