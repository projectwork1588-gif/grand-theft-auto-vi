// Stage B browser checks for the seven vehicle pages, in a real browser.
//   TL_BASE=http://127.0.0.1:5059 node scripts/qa/cdp.mjs scripts/qa/vehicle_detail_qa.mjs        (exit status 1 on any failure)
// For every vehicle and size: no horizontal overflow, no console or page errors, no failed requests, the opening's words stay clear of the machine at the END of the
// camera's push, the machine is on screen and the next link leads where it says. Once, at desktop: the camera really runs, the anchor lands clear of the
// sticky header, and the viewer, keyboard and image viewer work.
//   QA_SIZES=1920x1080,1440x900,1024x768,820x1180,390x844   QA_REDUCE=1 emulates the visitor's reduced-motion preference.
const BASE = process.env.TL_BASE || "http://127.0.0.1:5059";
const SIZES = (process.env.QA_SIZES || "1920x1080,1440x900,1024x768,820x1180,390x844").split(",").map((s) => s.split("x").map(Number));
const SLUGS = ["grotti-cheetah", "vapid-dominator-buggy", "shitzu-squalo", "vapid-stanier", "vapid-ganado", "dinka-enduro", "crest-kayak"];
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
    for (const slug of SLUGS) {
      problems.length = 0;
      await b.open(BASE + "/vehicles/" + slug, 1200);
      const tag = `${W}x${H} ${slug}`;
      const total = await b.eval("document.documentElement.scrollHeight");
      for (let y = 0; y < total; y += Math.round(H * 0.8)) { await b.eval(`window.scrollTo(0, ${y}); true`); await b.sleep(140); }
      await b.sleep(700);
      const over = await b.eval(`Math.max(document.documentElement.scrollWidth, document.body.scrollWidth) - window.innerWidth`);
      report(over <= 0, `${tag}: no horizontal overflow`, over + "px");
      report(problems.length === 0, `${tag}: no console, page or request errors`, problems.slice(0, 3).join(" | "));
      const blank = await b.eval(`[...document.querySelectorAll("img.gshot")].filter((i) => i.complete && i.naturalWidth === 0 && i.currentSrc).length`);
      report(blank === 0, `${tag}: no broken pictures`, blank + " broken");
      await b.eval(`window.scrollTo(0, 0); true`);
      await b.sleep(300);
      await b.eval(`document.getAnimations().forEach((a) => { try { a.finish(); } catch (e) {} }); true`);   // the camera is played to its end, where it crops most
      const r = JSON.parse(await b.eval(`(() => { const W_NARROW = window.innerWidth < 900; const h = document.querySelector(".vd-hero"); const art = h.querySelector(".vd-hero__art"), im = art.querySelector("img.gshot");
        const box = art.getBoundingClientRect(), cs = getComputedStyle(im); const [ox, oy] = cs.objectPosition.split(" ").map((v) => parseFloat(v) / 100);
        const nw = im.naturalWidth || 1600, nh = im.naturalHeight || 900; const contain = cs.objectFit === "contain";
        const lw = im.offsetWidth, lh = im.offsetHeight, lx = box.left + im.offsetLeft, ly = box.top + im.offsetTop;
        const scale = contain ? Math.min(lw / nw, lh / nh) : Math.max(lw / nw, lh / nh); const dw = nw * scale, dh = nh * scale;
        const left = lx - (dw - lw) * ox, top = ly - (dh - lh) * oy;
        const mx = new DOMMatrix(cs.transform === "none" ? "matrix(1,0,0,1,0,0)" : cs.transform); const [oxs, oys] = cs.transformOrigin.split(" ").map(parseFloat); const tox = lx + oxs, toy = ly + oys;
        const mapX = (x) => tox + mx.a * (x - tox) + mx.e, mapY = (y) => toy + mx.d * (y - toy) + mx.f;
        const subjects = (h.dataset.subject || "").split(";").filter(Boolean).map((s) => { const [x0, y0, x1, y1] = s.split(",").map(Number); return { l: mapX(left + x0 * dw), t: mapY(top + y0 * dh), r: mapX(left + x1 * dw), b: mapY(top + y1 * dh) }; });
        const rect = (e) => { const q = e.getBoundingClientRect(); return { l: q.left, t: q.top, r: q.right, b: q.bottom, w: q.width, h: q.height, name: (e.className && e.className.toString().split(" ")[0]) || e.tagName.toLowerCase() }; };
        const words = [...h.querySelectorAll(".vd-kicker, .vd-plate, .vd-hero__line, .vd-cue")].map(rect).filter((q) => q.w > 0 && q.h > 0);
        const hb = document.querySelector(".site-header").getBoundingClientRect(); const hr = h.getBoundingClientRect();
        return JSON.stringify({ subjects, words, art: { l: hr.left, t: Math.max(hr.top, W_NARROW ? hb.bottom : 0), r: hr.right, b: Math.min(hr.bottom, window.innerHeight) } }); })()`));
      let area = 0, shown = 0, crossing = [];
      for (const s of r.subjects) {
        const sw = s.r - s.l, sh = s.b - s.t;
        const inner = { l: s.l + sw * 0.05, r: s.r - sw * 0.05, t: s.t + sh * 0.05, b: s.b - sh * 0.05 };
        crossing = crossing.concat(r.words.filter((q) => q.l < inner.r && q.r > inner.l && q.t < inner.b && q.b > inner.t).map((q) => q.name));
        const cx = Math.max(0, Math.min(s.r, r.art.r) - Math.max(s.l, r.art.l)), cy = Math.max(0, Math.min(s.b, r.art.b) - Math.max(s.t, r.art.t));
        area += sw * sh; shown += cx * cy;
      }
      crossing = [...new Set(crossing)];
      if (r.subjects.length) {
        report(crossing.length === 0, `${tag}: the words stay clear of the machine`, crossing.join(", "));
        report(shown / area >= 0.95, `${tag}: the whole machine is on screen`, ((shown / area) * 100).toFixed(1) + " percent");
      }
      const nav = JSON.parse(await b.eval(`(() => { const a = document.querySelector('a[rel="next"]'), p = document.querySelector('a[rel="prev"]'); return JSON.stringify({ n: a ? a.getAttribute("href") : "", p: p ? p.getAttribute("href") : "" }); })()`));
      const i = SLUGS.indexOf(slug);
      report(nav.n.endsWith("/vehicles/" + SLUGS[(i + 1) % 7]) && nav.p.endsWith("/vehicles/" + SLUGS[(i + 6) % 7]), `${tag}: previous and next links`, nav.p + " " + nav.n);
    }
  }
  // ---- once, at desktop: the camera, the anchor, the viewer, the keyboard
  await b.send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  for (const slug of SLUGS) {
    await b.open(BASE + "/vehicles/" + slug, 1500);
    const cam = JSON.parse(await b.eval(`(() => { const im = document.querySelector(".vd-hero__art img.gshot"); const a = im.getAnimations(); return JSON.stringify({ n: a.length, motion: document.documentElement.classList.contains("motion-on"), t: getComputedStyle(im).transform }); })()`));
    if (process.env.QA_REDUCE === "1") { console.log(`INFO  ${slug}: camera animations ${cam.n}, motion-on ${cam.motion}`); }
    else { report(cam.n > 0 && cam.motion, `${slug}: the camera runs`, JSON.stringify(cam)); }
    await b.eval(`document.querySelector('a[href="#machine"]').click(); true`);
    await b.sleep(900);
    const gap = await b.eval(`(() => { const m = document.querySelector("#machine").getBoundingClientRect(), h = document.querySelector(".site-header").getBoundingClientRect(); return Math.round(m.top - h.bottom); })()`);
    report(gap >= 0, `${slug}: the anchor lands clear of the sticky header`, gap + "px");
  }
  await b.open(BASE + "/vehicles/vapid-dominator-buggy", 1500);
  await b.eval(`document.querySelector("[data-viewer]").scrollIntoView(); true`);
  await b.sleep(600);
  const before = await b.eval(`document.querySelector("[data-index]").textContent`);
  await b.eval(`document.querySelector("[data-next]").click(); true`);
  await b.sleep(1600);
  const after = await b.eval(`document.querySelector("[data-index]").textContent`);
  report(before !== after, "viewer: the next button moves to another picture", before + " -> " + after);
  await b.eval(`document.querySelector("[data-viewer]").dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowLeft", bubbles: true })); true`);
  await b.sleep(1600);
  report((await b.eval(`document.querySelector("[data-index]").textContent`)) === before, "viewer: the left arrow key goes back");
  await b.eval(`document.querySelector("[data-open]").click(); true`);
  await b.sleep(900);
  report(await b.eval(`!!document.querySelector(".lightbox, [role=dialog]")`), "viewer: the large picture opens the site's image viewer");
  console.log(failed ? `\n${failed} FAILED` : "\nall passed");
  process.exitCode = failed ? 1 : 0;
}
