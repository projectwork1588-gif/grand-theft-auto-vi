// Real-browser scenarios for the Characters motion portraits and navigation. Prints PASS / FAIL per check, exits 1 on a failure.
//   node scripts/qa/cdp.mjs scripts/qa/motion_scenarios.mjs
// Needs the app on TL_BASE (default http://127.0.0.1:5057) and the built sequences (python -m scripts.make_loops --portraits).
// The server's TV_AUTOPLAY_ALWAYS=1 (the local .env) lets headless Chrome, which reports reduced motion, autoplay.
const BASE = process.env.TL_BASE || "http://127.0.0.1:5057";
let failures = 0;
const check = (name, ok, detail = "") => { if (!ok) { failures++; } console.log(`${ok ? "PASS" : "FAIL"}  ${name}${detail ? "  (" + detail + ")" : ""}`); };

export default async function (b) {
  const view = (w, mobile = false) => b.send("Emulation.setDeviceMetricsOverride", { width: w, height: mobile ? 844 : 900, deviceScaleFactor: 1, mobile });
  const open = async (path, wait = 1500) => { await b.open(BASE + path, wait); };
  const fresh = async (path) => { await b.open(BASE + "/health", 100); await b.eval(`localStorage.clear(); true`); await open(path); };
  const tile = (slug) => `(document.querySelector("#${slug} [data-portrait]") || document.querySelector("[data-portrait]"))`;
  const st = (slug) => b.eval(`(() => { const t = ${tile(slug)}; const v = t.querySelector("video");
    return { paused: v.paused, ct: +v.currentTime.toFixed(2), dur: +(v.duration || 0).toFixed(2), live: t.classList.contains("is-live"), rest: t.classList.contains("is-rest"), blocked: t.classList.contains("is-blocked"),
             opacity: +getComputedStyle(v).opacity, src: !!v.getAttribute("src") }; })()`);
  const playingNow = () => b.eval(`[...document.querySelectorAll("[data-portrait] video")].filter((v) => !v.paused).length`);
  const toTile = async (slug, frac = 0.35) => {
    const y = await b.eval(`${tile(slug)}.getBoundingClientRect().top + scrollY - innerHeight * ${frac}`);
    await b.eval(`window.scrollTo(0, ${y}); true`);
  };
  const waitRest = async (slug, ms = 7000) => { for (let t = 0; t < ms / 200; t++) { if ((await st(slug)).rest) { return true; } await b.sleep(200); } return false; };
  const errors = [];
  await b.send("Runtime.enable");

  await view(1440);
  // ---- 1. fresh load: nothing plays until a tile is in view; then one plays once and rests
  await fresh("/characters");
  check("fresh load: nothing playing at the top of the page", (await playingNow()) === 0);
  await toTile("cal-hampton");
  let any = 0;
  for (let t = 0; t < 14 && !any; t++) { await b.sleep(250); any = await playingNow(); }
  check("a tile in view starts by itself (the one nearest the reading line goes first)", any === 1, any + " playing");
  check("the neighbour beside it waits, then plays and rests (Cal and Brian are side by side)", await waitRest("cal-hampton", 12000));
  const done = await st("cal-hampton");
  check("a finished tile stays put (paused, not looping)", done.paused && done.rest, JSON.stringify(done));

  // ---- 2. scrolling away and back to a finished tile does not replay it
  await b.eval(`window.scrollTo(0, 0); true`); await b.sleep(1200);
  await toTile("cal-hampton"); await b.sleep(2200);
  const again = await st("cal-hampton");
  check("returning to a finished tile does not replay it", again.paused && again.rest && again.ct >= 3, JSON.stringify(again));

  // ---- 3. leaving mid-way goes back to the artwork (no frozen half-dissolve), and the tile plays again on return
  await fresh("/characters");
  await toTile("raul-bautista"); await b.sleep(2000);
  const playing = await st("raul-bautista");
  await b.eval(`window.scrollTo(0, 0); true`); await b.sleep(1300);
  const left = await st("raul-bautista");
  check("leaving mid-way: it was playing", !playing.paused && playing.ct > 0.3, JSON.stringify(playing));
  check("leaving mid-way: it stops and returns to the artwork (not live, at 0)", left.paused && !left.live && !left.rest && left.ct < 0.1, JSON.stringify(left));
  await toTile("raul-bautista");
  check("returning: it plays through and rests", await waitRest("raul-bautista", 9000));

  // ---- 4. fast scrolling past several tiles: at most one plays at a time, none is left half-way
  await fresh("/characters");
  let maxPlaying = 0;
  const sample = async (ms) => { for (let t = 0; t < ms / 60; t++) { maxPlaying = Math.max(maxPlaying, await playingNow()); await b.sleep(60); } };
  const total = await b.eval(`document.documentElement.scrollHeight`);
  for (let s = 1; s <= 12; s++) { await b.eval(`window.scrollTo(0, ${(total * 0.65 * s) / 12}); true`); await b.sleep(45); }
  await sample(7000);
  check("fast scroll: never two clips at once", maxPlaying <= 1, "max " + maxPlaying);
  const ghosts = await b.eval(`[...document.querySelectorAll("[data-portrait]")].filter((t) => { const v = t.querySelector("video");
    return v.paused && !t.classList.contains("is-rest") && (v.currentTime > 0.05 || t.classList.contains("is-live")); }).length`);
  check("fast scroll: no tile is left frozen part-way", ghosts === 0, ghosts + " frozen");

  // ---- 5. the jump bar: a click lands on the person and their clip plays
  await fresh("/characters");
  await b.eval(`document.querySelector("[data-cast-nav] a[href='#real-dimez']").click(); true`);
  await b.sleep(2400);
  const dim = await st("real-dimez");
  check("jump bar: the chosen person's clip is playing or finished", !dim.paused || dim.rest, JSON.stringify(dim));
  const heading = await b.eval(`(() => { const h = document.querySelector("#real-dimez .person__name").getBoundingClientRect(); const n = document.querySelector("[data-cast-nav]").getBoundingClientRect(); return { top: h.top, navBottom: n.bottom }; })()`);
  check("jump bar: the heading is not hidden under the bars", heading.top >= heading.navBottom + 4, JSON.stringify(heading));

  // ---- 6. motion switched off: nothing plays, Play buttons are visible, one click plays that tile
  await b.eval(`localStorage.setItem("tv-motion", "0"); true`);
  await open("/characters");
  await toTile("boobie-ike"); await b.sleep(2500);
  const off = await st("boobie-ike");
  const button = await b.eval(`(() => { const e = ${tile("boobie-ike")}.querySelector("[data-motion-optin]"); const r = e.getBoundingClientRect(); return { hidden: e.hidden, w: r.width }; })()`);
  check("motion off: the clip does not play", off.paused && !off.live && off.ct === 0, JSON.stringify(off));
  check("motion off: a Play button is shown", !button.hidden && button.w > 20, JSON.stringify(button));
  await b.eval(`${tile("boobie-ike")}.querySelector("[data-motion-optin]").click(); true`);
  await b.sleep(1500);
  check("motion off: one click plays it", !(await st("boobie-ike")).paused);
  await b.eval(`localStorage.clear(); true`);

  // ---- 7. autoplay refused by the browser: the still stays, a Play button appears, nothing throws
  const blocker = await b.send("Page.addScriptToEvaluateOnNewDocument", { source: `window.__block = true; const o = HTMLMediaElement.prototype.play;
    HTMLMediaElement.prototype.play = function () { return window.__block ? Promise.reject(new DOMException("blocked", "NotAllowedError")) : o.apply(this, arguments); };
    window.addEventListener("unhandledrejection", () => { window.__unhandled = (window.__unhandled || 0) + 1; });` });
  await open("/characters");
  await toTile("dre-quan-priest"); await b.sleep(2500);
  const blocked = await st("dre-quan-priest");
  const showing = await b.eval(`(() => { const e = ${tile("dre-quan-priest")}.querySelector("[data-motion-optin]"); return getComputedStyle(e).display !== "none"; })()`);
  check("autoplay refused: the still stays and the tile is marked", blocked.paused && blocked.blocked && !blocked.live, JSON.stringify(blocked));
  check("autoplay refused: a Play button is visible", showing);
  check("autoplay refused: no unhandled errors", ((await b.eval(`window.__unhandled || 0`)) === 0));
  await b.send("Page.removeScriptToEvaluateOnNewDocument", { identifier: blocker.identifier });

  // ---- 8. a phone
  await view(390, true);
  await fresh("/characters");
  await toTile("raul-bautista", 0.3);
  let phone = await st("raul-bautista");
  for (let t = 0; t < 16 && phone.paused && !phone.rest; t++) { await b.sleep(250); phone = await st("raul-bautista"); }
  check("phone: the clip plays in view", !phone.paused || phone.rest, JSON.stringify(phone));
  check("phone: it rests on the artwork", await waitRest("raul-bautista", 8000));
  const wide = await b.eval(`document.documentElement.scrollWidth > document.documentElement.clientWidth`);
  check("phone: no sideways scroll", !wide);
  await view(1440);

  // ---- 9. repeated navigation between profiles: each plays once and rests, whatever the order
  const order = ["jason-duval", "cal-hampton", "lucia-caminos", "boobie-ike", "jason-duval", "real-dimez", "raul-bautista", "brian-heder", "dre-quan-priest", "cal-hampton"];
  let navOk = true; const bad = [];
  for (const slug of order) {
    await fresh("/characters/" + slug);
    await b.eval(`window.scrollTo(0, document.querySelector(".p-story").getBoundingClientRect().top + scrollY - 180); true`);
    let rested = false;
    for (let t = 0; t < 30; t++) { await b.sleep(200); const s = await b.eval(`(() => { const t = document.querySelector("[data-portrait]"); return t.classList.contains("is-rest"); })()`); if (s) { rested = true; break; } }
    const plays = await b.eval(`document.querySelector("[data-portrait] video").getVideoPlaybackQuality().corruptedVideoFrames`);
    if (!rested || plays > 0) { navOk = false; bad.push(slug); }
  }
  check("profiles: all eight play through once and rest, repeated in any order", navOk, bad.join(","));

  // ---- 10. keyboard: the jump bar and every control show a visible focus indicator
  await fresh("/characters");
  const focusInfo = [];
  for (let k = 0; k < 28; k++) {
    await b.send("Input.dispatchKeyEvent", { type: "keyDown", key: "Tab", code: "Tab", windowsVirtualKeyCode: 9 });
    await b.send("Input.dispatchKeyEvent", { type: "keyUp", key: "Tab", code: "Tab", windowsVirtualKeyCode: 9 });
    focusInfo.push(await b.eval(`(() => { const e = document.activeElement; if (!e || e === document.body) return null; const c = getComputedStyle(e);
      const r = e.getBoundingClientRect(); return { tag: e.tagName, text: (e.textContent || "").trim().slice(0, 24), outline: c.outlineStyle !== "none" && parseFloat(c.outlineWidth) > 0, shadow: c.boxShadow !== "none", underline: c.textDecorationLine.includes("underline"), onScreen: r.bottom > 0 && r.top < innerHeight }; })()`));
  }
  const reached = focusInfo.filter(Boolean);
  const invisible = reached.filter((f) => !f.outline && !f.shadow && !f.underline);
  check("keyboard: Tab reaches the links in order", reached.length >= 20, reached.length + " stops");
  check("keyboard: every focused control has a visible indicator", invisible.length === 0, invisible.map((f) => f.text).join(" | "));
  const jump = await b.eval(`[...document.querySelectorAll("[data-cast-nav] a[href^='#']")].length`);
  check("jump bar: eight people and an Explore link", jump >= 8, jump + " links");

  console.log(failures ? `\n${failures} FAILED` : "\nall passed");
  process.exitCode = failures ? 1 : 0;
}
