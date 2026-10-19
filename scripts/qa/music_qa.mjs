// Music page (/music) browser checks, in a real browser.
//   TL_BASE=http://127.0.0.1:5059 node scripts/qa/cdp.mjs scripts/qa/music_qa.mjs        (exit status 1 on any failure)
// At every size: no horizontal overflow, no console, page or request errors, every picture loaded, nothing clipped (station names, singles, logos inside their banners), every external link
// https to an official host and opening in a new tab with rel noopener, the menu marks Music, the opening's words clear of the header. Once, at desktop: the jump links land clear of the sticky
// header, keyboard focus is visible on the links that matter, the old /locations address arrives on /music, a place page still opens, and there is no animation under reduced motion.
//   QA_SIZES=1920x1080,1440x900,1024x768,768x1024,390x844,360x740   QA_REDUCE=1 emulates reduced motion.
const BASE = process.env.TL_BASE || "http://127.0.0.1:5059";
const SIZES = (process.env.QA_SIZES || "1920x1080,1440x900,1024x768,768x1024,390x844,360x740").split(",").map((s) => s.split("x").map(Number));
const HOSTS = ["www.rockstargames.com", "rockstargames.com", "www.gtavi-thealbum.com", "gtavi-thealbum.lnk.to", "gtavithealbum.lnk.to", "justice.lnk.to"];
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
  for (const [W, H] of SIZES) {
    await b.send("Emulation.setDeviceMetricsOverride", { width: W, height: H, deviceScaleFactor: 1, mobile: W < 700 });
    problems.length = 0;
    await b.open(BASE + "/music", 1200);
    const tag = `${W}x${H}`;
    const total = await b.eval("document.documentElement.scrollHeight");
    for (let y = 0; y < total; y += Math.round(H * 0.7)) { await b.eval(`window.scrollTo(0, ${y}); true`); await b.sleep(180); }
    await b.sleep(1200);
    const over = await b.eval(`Math.max(document.documentElement.scrollWidth, document.body.scrollWidth) - window.innerWidth`);
    report(over <= 0, `${tag}: no horizontal overflow`, over + "px");
    report(problems.length === 0, `${tag}: no console, page or request errors`, problems.slice(0, 3).join(" | "));
    const pics = JSON.parse(await b.eval(`(() => { const imgs = [...document.querySelectorAll("main img")]; return JSON.stringify({ n: imgs.length, broken: imgs.filter((i) => !(i.complete && i.naturalWidth > 0)).map((i) => i.currentSrc.slice(-50)) }); })()`));
    report(pics.n >= 15 && pics.broken.length === 0, `${tag}: every picture loaded`, `${pics.n} pictures, broken: ${pics.broken.join(", ")}`);
    const clip = JSON.parse(await b.eval(`(() => { const bad = []; for (const e of document.querySelectorAll(".mu-st__name, .mu-st__with, .mu-st__desc, .mu-singles__main b, .mu-title, .mu-h")) { if (e.scrollWidth > e.clientWidth + 1) { bad.push(e.className + ": " + e.textContent.slice(0, 30)); } }
      for (const s of document.querySelectorAll(".mu-st__banner")) { const l = s.querySelector(".mu-st__logo"); if (!l) { continue; } const a = s.getBoundingClientRect(), r = l.getBoundingClientRect(); if (r.left < a.left - 1 || r.right > a.right + 1 || r.top < a.top - 1 || r.bottom > a.bottom + 1) { bad.push("logo outside its banner: " + l.alt); } }
      return JSON.stringify(bad); })()`));
    report(clip.length === 0, `${tag}: nothing is clipped and every logo sits inside its banner`, clip.join(" | "));
    const links = JSON.parse(await b.eval(`JSON.stringify([...document.querySelectorAll("main a[href^='http']")].map((a) => ({ h: a.href, t: a.target, r: a.rel })))`));
    const badLinks = links.filter((l) => !(l.h.startsWith("https://") && HOSTS.includes(new URL(l.h).hostname) && l.t === "_blank" && /noopener/.test(l.r) && /noreferrer/.test(l.r)));
    report(links.length >= 20 && badLinks.length === 0, `${tag}: every external link is https to an official host, in a new tab, with noopener and noreferrer`, `${links.length} links, bad: ${JSON.stringify(badLinks.slice(0, 2))}`);
    await b.eval(`window.scrollTo(0, 0); true`); await b.sleep(400);
    const head = JSON.parse(await b.eval(`(() => { const t = document.querySelector(".mu-title").getBoundingClientRect(), h = document.querySelector(".site-header").getBoundingClientRect(); const cur = document.querySelector('.header-nav a[aria-current="page"], .site-menu a[aria-current="page"]'); return JSON.stringify({ top: Math.round(t.top - h.bottom), left: Math.round(t.left), right: Math.round(window.innerWidth - t.right), cur: cur ? cur.textContent.trim() : null }); })()`));
    report(head.top >= 0 && head.left >= 0 && head.right >= 0, `${tag}: the opening's title is on the screen and clear of the header`, JSON.stringify(head));
    report(W < 1024 || head.cur === "Music", `${tag}: the menu marks Music`, String(head.cur));
  }
  // ---- once, at desktop
  await b.send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  await b.open(BASE + "/music", 1500);
  for (const id of ["score", "radio", "album"]) {
    await b.eval(`document.querySelector('.mu-jump a[href="#${id}"]').click(); true`);
    await b.sleep(900);
    const gap = await b.eval(`(() => { const s = document.getElementById("${id}").getBoundingClientRect(), h = document.querySelector(".site-header").getBoundingClientRect(); return Math.round(s.top - h.bottom); })()`);
    report(gap >= -2 && gap < 400, `jump: #${id} lands clear of the sticky header`, gap + "px");
  }
  await b.open(BASE + "/music", 1200);
  let reached = 0, rings = 0;
  for (let i = 0; i < 60 && reached < 3; i++) {      // real Tab presses, so :focus-visible applies
    await b.send("Input.dispatchKeyEvent", { type: "keyDown", key: "Tab", code: "Tab", windowsVirtualKeyCode: 9 });
    await b.send("Input.dispatchKeyEvent", { type: "keyUp", key: "Tab", code: "Tab", windowsVirtualKeyCode: 9 });
    const onLink = await b.eval(`(() => { const e = document.activeElement; if (!e || !e.closest(".mu")) { return null; } const cs = getComputedStyle(e); return { cls: e.className, ring: cs.outlineStyle !== "none" && parseFloat(cs.outlineWidth) >= 2 }; })()`);
    if (onLink) { reached++; if (onLink.ring) { rings++; } }
  }
  report(reached >= 3 && rings === reached, "keyboard: Tab reaches the page's own links and each shows a focus ring", `${rings}/${reached}`);
  await b.open(BASE + "/locations?q=marina&region=vice-city", 1200);
  report((await b.eval(`location.pathname`)) === "/music" && (await b.eval(`location.search`)) === "", "legacy: /locations arrives on /music without its old filters");
  await b.open(BASE + "/locations/neon-row-district", 1200);
  report((await b.eval(`document.querySelector("h1").textContent.includes("Neon Row")`)) && (await b.eval(`/Team Valkyrie original/.test(document.body.innerText)`)), "legacy: a place's own page still opens, labelled a Team Valkyrie original");
  const anim = await b.eval(`document.getAnimations().length`);
  if (process.env.QA_REDUCE === "1") { console.log(`INFO  animations running with reduced motion emulated and the site's motion on: ${anim}`); }
  console.log(failed ? `\n${failed} FAILED` : "\nall passed");
  process.exitCode = failed ? 1 : 0;
}
