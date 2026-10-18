// The Garage opening's camera movement, checked in a real browser: a slow push-in with a small drift on each scene's picture, never a bared edge, no jump when it starts or when
// the scene is replaced, stopped in a hidden tab or when the opening is out of the window, absent for a visitor who asks for reduced motion, no visible play/pause control at any width,
// no sideways scrolling, no console errors.
//   TL_BASE=http://127.0.0.1:5059 node scripts/qa/cdp.mjs scripts/qa/garage_camera.mjs      (exit status 1 on any failure)
const BASE = process.env.TL_BASE || "http://127.0.0.1:5059";
let failed = 0;
const ok = (c, label, detail = "") => { if (!c) { failed++; } console.log((c ? "PASS  " : "FAIL  ") + label + (detail ? "  (" + detail + ")" : "")); };
const SLUGS = ["grotti-cheetah", "vapid-dominator-buggy", "shitzu-squalo", "vapid-stanier", "vapid-ganado", "dinka-enduro", "crest-kayak"];
const ZOOM = { "grotti-cheetah": 1.06, "vapid-dominator-buggy": 1.055, "shitzu-squalo": 1.055, "vapid-stanier": 1.035, "vapid-ganado": 1.035, "dinka-enduro": 1.04, "crest-kayak": 1.03 };

export default async function (b) {
  const errors = [];
  b.on((d) => {
    if (d.method === "Runtime.exceptionThrown") { errors.push("exception: " + (d.params.exceptionDetails.exception?.description || d.params.exceptionDetails.text)); }
    if (d.method === "Runtime.consoleAPICalled" && d.params.type === "error") { errors.push("console.error: " + d.params.args.map((a) => a.value || a.description).join(" ")); }
  });
  const ev = (x) => b.eval(x);
  await b.colorScheme(false);
  await b.send("Emulation.setFocusEmulationEnabled", { enabled: true });
  const open = async (w, h, query = "?dwell=30", motion = "1") => {
    await b.send("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: 1, mobile: w < 700 });
    await b.open(BASE + "/about", 100);
    await ev(`localStorage.setItem("tv-motion", "${motion}"); true`);
    await b.open(BASE + "/garage-concept" + query, 1500);
  };
  // the scale and the shift of a scene's picture, and whether it still covers its frame
  const look = (slug) => ev(`(() => { const p = document.querySelector('[data-panel="${slug}"]'); const i = p.querySelector(".gx-art img"); const a = p.querySelector(".gx-art").getBoundingClientRect(); const r = i.getBoundingClientRect();
    const m = new DOMMatrix(getComputedStyle(i).transform); const an = i.getAnimations().map((x) => x.animationName + ":" + x.playState);
    return JSON.stringify({ s: +m.a.toFixed(4), tx: +(m.e / r.width * 100).toFixed(3), ty: +(m.f / r.height * 100).toFixed(3), covers: r.left <= a.left + 0.6 && r.right >= a.right - 0.6 && r.top <= a.top + 0.6 && r.bottom >= a.bottom - 0.6, an, fit: getComputedStyle(i).objectFit }); })()`).then(JSON.parse);
  const choose = async (slug) => {
    await ev(`document.querySelector('[data-pick="${slug}"]').click(); true`);
    for (let i = 0; i < 60; i++) { if (await ev(`document.querySelector('[data-panel="${slug}"]').classList.contains("is-active") && !document.querySelector(".is-entering")`).catch(() => false)) { break; } await b.sleep(50); }
  };

  // ---- no visible play/pause control, at a desktop and a phone width
  for (const [w, h] of [[1440, 900], [390, 844]]) {
    await open(w, h);
    const ctl = await ev(`JSON.stringify({ hooks: document.querySelectorAll("[data-playpause], .gx-pause, .gx-play").length, buttons: [...document.querySelectorAll("[data-stage] button")].map((x) => (x.getAttribute("aria-label") || x.textContent || "").trim()).filter((t) => /pause|play|resume|stop/i.test(t)) })`).then(JSON.parse);
    ok(ctl.hooks === 0 && ctl.buttons.length === 0, `${w}px: the opening has no play or pause control`, JSON.stringify(ctl));
  }

  // ---- each scene's camera
  await open(1440, 900);
  for (const slug of SLUGS) {
    await choose(slug);
    const t0 = Date.now();
    const a = await look(slug);
    await b.sleep(Math.max(0, 1500 - (Date.now() - t0)));
    const m = await look(slug);
    await b.sleep(Math.max(0, 3200 - (Date.now() - t0)));
    const z = await look(slug);
    const z1 = ZOOM[slug];
    ok(a.an.some((n) => n.startsWith("gx-push")) && m.s > a.s && z.s > m.s && z.s <= z1 + 0.002 && a.s >= 1, `${slug}: a slow push-in, still moving after three seconds, never past ${z1}`, [a.s, m.s, z.s].join(" > "));
    ok(a.covers && m.covers && z.covers, `${slug}: the picture always covers its frame (no bared edge)`, JSON.stringify([a.covers, m.covers, z.covers]));
    ok(Math.abs(z.tx) < 1.1 && Math.abs(z.ty) < 0.9, `${slug}: the drift stays small`, `${z.tx}%, ${z.ty}%`);
  }

  // ---- no jump when a scene begins, and the one being replaced keeps moving under the one arriving
  await choose("grotti-cheetah");
  await b.sleep(2200);
  const before = await look("grotti-cheetah");
  // one in-page recording across the change, frame by frame: the scene being replaced (A) and the one arriving (B)
  const frames = await ev(`new Promise((done) => {
    const A = document.querySelector('[data-panel="grotti-cheetah"] .gx-art img'), B = document.querySelector('[data-panel="vapid-dominator-buggy"] .gx-art img'), out = [], t0 = performance.now();
    const scale = (i) => new DOMMatrix(getComputedStyle(i).transform).a;
    const cover = (i) => { const a = i.parentElement.getBoundingClientRect(), r = i.getBoundingClientRect(); return r.left <= a.left + 0.6 && r.right >= a.right - 0.6 && r.top <= a.top + 0.6 && r.bottom >= a.bottom - 0.6; };
    document.querySelector('[data-pick="vapid-dominator-buggy"]').click();
    const tick = () => { const t = performance.now() - t0; out.push([Math.round(t), +scale(A).toFixed(4), +scale(B).toFixed(4), cover(A) && cover(B)]); if (t < 640) { requestAnimationFrame(tick); } else { done(JSON.stringify(out)); } };
    requestAnimationFrame(tick);
  })`).then(JSON.parse);
  const aS = frames.map((f) => f[1]), bS = frames.map((f) => f[2]);
  ok(aS.every((s, i) => s >= before.s - 0.0005 && (i === 0 || s >= aS[i - 1] - 0.0005)), "the scene being replaced is not reset: its camera keeps moving under the new one", `${before.s} > ${aS[0]} ... ${aS[aS.length - 1]} (${frames.length} frames)`);
  ok(bS.every((s) => s >= 1 && s < 1.03) && bS.every((s, i) => i === 0 || s >= bS[i - 1] - 0.0005), "the arriving scene's camera starts from the picture as it rests", `${bS[0]} ... ${bS[bS.length - 1]}`);
  ok(frames.every((f) => f[3]), "no edge is bared while two scenes are on show");

  // ---- the lifecycle: stopped in a hidden tab, stopped out of the window, going on when it comes back
  await choose("shitzu-squalo");
  await ev(`Object.defineProperty(document, "hidden", { configurable: true, get: () => true }); document.dispatchEvent(new Event("visibilitychange")); true`);
  await b.sleep(300);
  const hid = await ev(`JSON.stringify({ paused: document.querySelector("[data-stage]").classList.contains("is-paused"), states: document.querySelector('[data-panel="shitzu-squalo"] .gx-art img').getAnimations().map((x) => x.playState) })`).then(JSON.parse);
  ok(hid.paused && hid.states.length > 0 && hid.states.every((s) => s === "paused"), "in a hidden tab the camera and the clock are stopped", JSON.stringify(hid));
  await ev(`Object.defineProperty(document, "hidden", { configurable: true, get: () => false }); document.dispatchEvent(new Event("visibilitychange")); true`);
  await b.sleep(300);
  ok(await ev(`!document.querySelector("[data-stage]").classList.contains("is-paused") && document.querySelector('[data-panel="shitzu-squalo"] .gx-art img').getAnimations().some((x) => x.playState === "running")`), "shown again, it goes on");
  await ev(`scrollTo(0, 2200); true`);
  await b.sleep(700);
  ok(await ev(`document.querySelector("[data-stage]").classList.contains("is-paused")`), "with the opening out of the window the camera is stopped");
  await ev(`scrollTo(0, 0); true`);
  await b.sleep(700);
  ok(await ev(`!document.querySelector("[data-stage]").classList.contains("is-paused")`), "back in the window it goes on");

  // ---- reduced motion: the system asks for none (and the site is not told to autoplay regardless), so nothing moves and nothing cycles. The test server forces autoplay (TV_AUTOPLAY_ALWAYS=1),
  // as the owner's does, so this part needs a second server without it:  TV_AUTOPLAY_ALWAYS=0 flask --app "app:create_app('testing')" run --port 5063
  const RM = process.env.RM_BASE || "http://127.0.0.1:5063";
  const up = await fetch(RM + "/about").then((r) => r.ok).catch(() => false);
  if (up) {
    await b.send("Emulation.setEmulatedMedia", { features: [{ name: "prefers-reduced-motion", value: "reduce" }] });
    await b.send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
    await b.open(RM + "/about", 100);
    await ev(`localStorage.removeItem("tv-motion"); true`);
    await b.open(RM + "/garage-concept?dwell=2", 1800);
    const red = await ev(`JSON.stringify({ motion: document.documentElement.classList.contains("motion-on"), anim: document.querySelector(".gx-scene.is-active .gx-art img").getAnimations().length, shown: document.querySelector("[data-stage]").getAttribute("data-vehicle") })`).then(JSON.parse);
    await b.sleep(4600);
    const still = await ev(`document.querySelector("[data-stage]").getAttribute("data-vehicle")`);
    ok(!red.motion && red.anim === 0 && still === red.shown, "reduced motion: no camera movement, and the scenes do not cycle by themselves", JSON.stringify(red) + " -> " + still);
    await ev(`document.querySelector('[data-pick="vapid-stanier"]').click(); true`);
    await b.sleep(900);
    ok(await ev(`document.querySelector('[data-panel="vapid-stanier"]').classList.contains("is-active")`), "reduced motion: choosing a scene still works");
    await ev(`localStorage.setItem("tv-motion", "1"); true`);
    await b.open(RM + "/garage-concept?dwell=2", 1800);
    const first = await ev(`document.querySelector("[data-stage]").getAttribute("data-vehicle")`);
    await b.sleep(3600);
    ok((await ev(`document.querySelector("[data-stage]").getAttribute("data-vehicle")`)) !== first, "reduced motion, but the visitor has switched motion on in the menu: the showcase runs");
    await b.send("Emulation.setEmulatedMedia", { features: [{ name: "prefers-reduced-motion", value: "no-preference" }] });
    await ev(`localStorage.removeItem("tv-motion"); true`);
  } else {
    ok(false, "reduced motion: a second server without forced autoplay is needed on " + RM);
  }

  // ---- no sideways scrolling or console errors at narrow, standard, 4:3 and ultrawide shapes
  for (const [w, h] of [[390, 844], [820, 1180], [1024, 768], [1440, 900], [2560, 1080]]) {
    await open(w, h, "?dwell=30");
    for (const slug of ["vapid-stanier", "crest-kayak"]) { await choose(slug); await b.sleep(900); }
    ok(!(await ev(`document.documentElement.scrollWidth > document.documentElement.clientWidth`)), `${w}x${h}: no sideways scrolling while the camera moves`);
  }
  ok(errors.length === 0, "no console errors or exceptions", errors.slice(0, 2).join(" | "));
  console.log(failed ? `\n${failed} FAILED` : "\nall passed");
  process.exitCode = failed ? 1 : 0;
}
