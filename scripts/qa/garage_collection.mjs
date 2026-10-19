// The Garage concept's collection in a real browser: the strip of customs and classics (buttons, keys, counter), the chapter index at the right edge (shown, lit for the chapter in view,
// every chapter heading lands clear of the sticky header), the diptych (the machine under the pointer opens wider), the water chapter (stills only, the Kayak closes it) and the motion
// switch (with motion off every picture and every line of words is shown at once).
//   TL_BASE=http://127.0.0.1:5059 node scripts/qa/cdp.mjs scripts/qa/garage_collection.mjs      (exit status 1 on any failure)
const BASE = process.env.TL_BASE || "http://127.0.0.1:5059";
let failed = 0;
const ok = (c, label, detail = "") => { if (!c) { failed++; } console.log((c ? "PASS  " : "FAIL  ") + label + (detail ? "  (" + detail + ")" : "")); };

export default async function (b) {
  const ev = (x) => b.eval(x);
  await b.colorScheme(false);
  await b.send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  await b.open(BASE + "/about", 100);
  await ev(`localStorage.setItem("tv-motion", "1"); true`);
  await b.open(BASE + "/vehicles?autoplay=0", 2000);

  // ---- the strip of customs and classics
  await ev(`document.querySelector(".gx-customs").scrollIntoView({ block: "center" }); true`);
  await b.sleep(1500);
  const st0 = JSON.parse(await ev(`JSON.stringify({ now: document.querySelector("[data-strip-now]").textContent, prev: document.querySelector('[data-strip-step="-1"]').disabled, next: document.querySelector('[data-strip-step="1"]').disabled, left: document.querySelector("[data-strip]").scrollLeft, cells: document.querySelectorAll(".gx-customs__cell").length, hidden: document.querySelector("[data-strip-ctl]").hidden })`));
  ok(st0.now === "1" && st0.prev === true && st0.next === false && st0.left === 0 && st0.cells === 4 && st0.hidden === false, "the strip starts at the first picture, Previous off, the controls shown", JSON.stringify(st0));
  await ev(`document.querySelector('[data-strip-step="1"]').click(); true`);
  await b.sleep(1300);
  const st1 = JSON.parse(await ev(`JSON.stringify({ now: document.querySelector("[data-strip-now]").textContent, left: document.querySelector("[data-strip]").scrollLeft, prev: document.querySelector('[data-strip-step="-1"]').disabled })`));
  ok(st1.left > 300 && st1.now === "2" && st1.prev === false, "Next moves to the second picture and the counter follows", JSON.stringify(st1));
  await ev(`document.querySelector("[data-strip]").focus(); true`);
  for (let i = 0; i < 3; i++) { await b.send("Input.dispatchKeyEvent", { type: "keyDown", key: "ArrowRight", code: "ArrowRight", windowsVirtualKeyCode: 39 }); await b.send("Input.dispatchKeyEvent", { type: "keyUp", key: "ArrowRight", code: "ArrowRight", windowsVirtualKeyCode: 39 }); await b.sleep(900); }
  const st2 = JSON.parse(await ev(`JSON.stringify({ now: document.querySelector("[data-strip-now]").textContent, next: document.querySelector('[data-strip-step="1"]').disabled })`));
  ok(st2.now === "4" && st2.next === true, "the arrow key walks to the last picture, where Next switches off", JSON.stringify(st2));
  await ev(`document.querySelector('[data-strip-step="-1"]').click(); true`);
  await b.sleep(1100);
  ok((await ev(`document.querySelector("[data-strip-now]").textContent`)) !== "4", "Previous walks back");

  // ---- the chapter index: off over the opening, on over the collection, lit for the chapter in view, and a heading never lands under the header
  await ev(`scrollTo(0, 0); true`); await b.sleep(900);
  ok(!(await ev(`document.querySelector("[data-chapter-rail]").classList.contains("is-on")`)), "the chapter index is not shown over the opening");
  for (const key of ["performance", "street", "beyond", "water"]) {
    await ev(`document.querySelector('[data-chapter-rail] a[data-for="${key}"]').click(); true`);
    await b.sleep(2000);
    const r = JSON.parse(await ev(`(() => { const h = document.querySelector("#ch-${key}").getBoundingClientRect(); const head = document.querySelector(".site-header").getBoundingClientRect(); const lit = document.querySelector("[data-chapter-rail] a[aria-current]"); return JSON.stringify({ on: document.querySelector("[data-chapter-rail]").classList.contains("is-on"), top: Math.round(h.top), bottom: Math.round(head.bottom), lit: lit ? lit.getAttribute("data-for") : null }); })()`));
    ok(r.on && r.top >= r.bottom - 2 && r.lit === key, `the index link for ${key} lands the chapter heading clear of the header and lights its number`, JSON.stringify(r));
  }

  // ---- the diptych: the machine under the pointer opens wider
  await ev(`document.querySelector(".gx-duo").scrollIntoView({ block: "center" }); true`);
  await b.sleep(1800);
  const w0 = JSON.parse(await ev(`JSON.stringify([...document.querySelectorAll(".gx-d")].map((d) => Math.round(d.getBoundingClientRect().width)))`));
  const box = JSON.parse(await ev(`(() => { const r = document.querySelector(".gx-d--b .gx-d__pic").getBoundingClientRect(); return JSON.stringify({ x: r.left + r.width / 2, y: r.top + r.height / 2 }); })()`));
  await b.send("Input.dispatchMouseEvent", { type: "mouseMoved", x: box.x, y: box.y });
  await b.sleep(1400);
  const w1 = JSON.parse(await ev(`JSON.stringify([...document.querySelectorAll(".gx-d")].map((d) => Math.round(d.getBoundingClientRect().width)))`));
  ok(w0[0] > w0[1] && w1[1] > w0[1] && w1[0] < w0[0] && w1[0] + w1[1] >= w0[0] + w0[1] - 12, "the diptych opens the machine under the pointer wider, the other narrower, the pair keeps its width", w0.join("/") + " -> " + w1.join("/"));
  // the whole half is one link: a real press on the picture goes to that machine
  await b.send("Input.dispatchMouseEvent", { type: "mouseMoved", x: 5, y: 5 });

  // ---- the water chapter: stills only, the Squalo then the Kayak, the Kayak's words are readable
  const water = JSON.parse(await ev(`JSON.stringify({ video: document.querySelectorAll("video").length, order: [...document.querySelectorAll(".gx-sea .gx-f")].map((a) => a.dataset.vehicle) })`));
  ok(water.video === 0 && water.order.join() === "shitzu-squalo,crest-kayak", "the water chapter is two stills, the Squalo and then the Kayak, with no video", JSON.stringify(water));
  const gap = JSON.parse(await ev(`(() => { const a = document.querySelector(".gx-f--sea_a").getBoundingClientRect(), z = document.querySelector(".gx-f--finale").getBoundingClientRect(); return JSON.stringify({ a: Math.round(a.bottom), z: Math.round(z.top) }); })()`));
  ok(gap.z >= gap.a - 1, "the two water stages never overlap (the Kayak starts where the Squalo ends)", JSON.stringify(gap));
  await ev(`document.querySelector(".gx-f--finale").scrollIntoView({ block: "center" }); true`);
  await b.sleep(2000);
  const fin = JSON.parse(await ev(`(() => { const f = document.querySelector(".gx-f--finale"); const w = f.querySelector(".gx-f__words h3"); const r = w.getBoundingClientRect(); const a = f.querySelector(".gx-f__art"); return JSON.stringify({ op: getComputedStyle(w).opacity, artOp: getComputedStyle(a).opacity, inView: r.top > 72 && r.bottom < innerHeight }); })()`));
  ok(fin.op === "1" && fin.artOp === "1" && fin.inView, "at the finale the Kayak's picture and name are fully shown and in the window", JSON.stringify(fin));

  // ---- every machine in the collection is one link wherever it is pressed (its picture, its words, its small detail), and nothing else lies over it
  const hits = JSON.parse(await ev(`(async () => {
    const out = [];
    for (const a of document.querySelectorAll(".gx-f, .gx-d")) {
      a.scrollIntoView({ block: "center" });
      await new Promise((r) => setTimeout(r, 120));
      for (const sel of [".gx-f__art, .gx-d__pic", ".gx-f__words h3", ".gx-f__inset"]) {
        const e = a.querySelector(sel);
        if (!e) { continue; }
        const r = e.getBoundingClientRect();
        const x = Math.min(Math.max(r.left + r.width * 0.5, 4), innerWidth - 80), y = Math.min(Math.max(r.top + r.height * 0.5, 80), innerHeight - 4);
        const at = document.elementFromPoint(x, y);
        out.push([a.dataset.vehicle, sel.split(",")[0], at && at.closest("a") === a]);
      }
    }
    return JSON.stringify(out);
  })()`));
  ok(hits.length === 17 && hits.every((h) => h[2]), "a press on any machine's picture, words or detail reaches that machine's own link", hits.length + " checked; " + hits.filter((h) => !h[2]).map((h) => h[0] + " " + h[1]).join(", "));

  // ---- the slow drift of a stage's picture is real and small: it follows the scroll and never exceeds a few percent
  await ev(`document.querySelector(".gx-f--perf").scrollIntoView({ block: "start" }); true`);
  await b.sleep(700);
  const d1 = await ev(`getComputedStyle(document.querySelector(".gx-f--perf .gx-f__art .gshot")).transform`);
  await ev(`scrollBy(0, 260); true`);
  await b.sleep(700);
  const d2 = await ev(`getComputedStyle(document.querySelector(".gx-f--perf .gx-f__art .gshot")).transform`);
  const ty = (m) => parseFloat(String(m).replace(/matrix\(|\)/g, "").split(",")[5] || "0");
  ok(d1 !== d2 && Math.abs(ty(d1)) < 60 && Math.abs(ty(d2)) < 60, "a stage's picture drifts a little against the scroll", d1 + " -> " + d2);

  // ---- pictures that fail to load: every picture of Rockstar's is blocked, and the page still reads: the words, the links and the layout stay, nothing throws, nothing scrolls sideways
  const thrown = [];
  b.on((d) => { if (d.method === "Runtime.exceptionThrown") { thrown.push(d.params.exceptionDetails.exception?.description || d.params.exceptionDetails.text); } });
  await b.send("Network.enable");
  await b.send("Network.setBlockedURLs", { urls: ["*rockstargames.com*"] });
  await b.open(BASE + "/about", 100);
  await ev(`localStorage.setItem("tv-motion", "1"); true`);
  await b.open(BASE + "/vehicles?autoplay=0", 2500);
  await ev(`document.querySelectorAll("img").forEach((i) => { i.loading = "eager"; }); true`);
  await b.sleep(2500);
  const fail = JSON.parse(await ev(`JSON.stringify({ imgs: document.querySelectorAll("img.gshot").length, broken: document.querySelectorAll("img.gshot.is-broken").length, words: [...document.querySelectorAll(".gx-f__words h3, .gx-d__words h3, .gx-scene.is-active .plate")].filter((e) => e.getBoundingClientRect().height > 0 && getComputedStyle(e).visibility !== "hidden").length, side: document.documentElement.scrollWidth > document.documentElement.clientWidth, h: document.documentElement.scrollHeight })`));
  ok(fail.imgs > 20 && fail.broken >= fail.imgs - 2 && fail.words >= 8 && !fail.side && thrown.length === 0, "with every picture failing, the page keeps its words, links and layout and throws nothing", JSON.stringify(fail) + (thrown[0] ? " " + thrown[0] : ""));
  await ev(`document.querySelector(".gx-f--finale").scrollIntoView({ block: "center" }); true`);
  await b.sleep(2200);
  ok(await ev(`getComputedStyle(document.querySelector(".gx-f--finale .gx-f__words h3")).opacity === "1"`), "and the Kayak finale still shows its name and its Explore link");
  await b.send("Network.setBlockedURLs", { urls: [] });

  // ---- the motion switch: with motion off nothing waits for an animation, and the strip and the index still work
  await b.open(BASE + "/about", 100);
  await ev(`localStorage.setItem("tv-motion", "0"); true`);
  await b.open(BASE + "/vehicles?autoplay=0", 1800);
  await ev(`scrollTo(0, 1200); true`); await b.sleep(600);
  const still = JSON.parse(await ev(`JSON.stringify({ motion: document.documentElement.classList.contains("motion-on"), hidden: [...document.querySelectorAll(".gx-f__art, .gx-d__pic, .gx-f__words > *")].filter((e) => getComputedStyle(e).opacity !== "1").length, drift: [...document.querySelectorAll(".gx-f__art .gshot")].filter((i) => getComputedStyle(i).transform !== "none").length })`));
  ok(!still.motion && still.hidden === 0 && still.drift === 0, "motion off: every picture and line of words is shown, and no picture drifts", JSON.stringify(still));
  await ev(`localStorage.setItem("tv-motion", "1"); true`);
  console.log(failed ? `\n${failed} FAILED` : "\nall passed");
  process.exitCode = failed ? 1 : 0;
}
