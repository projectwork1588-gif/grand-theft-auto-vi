// The Garage opening's automatic showcase, checked in a real browser: 01 to 07 and round to 01, the hold on each scene, a choice
// resetting the hold, the clock waiting for a pointer, for focus, for the opening to leave the window and for a hidden tab, motion switched off,
// the page never scrolling by itself, and the pictures and the sea clip being fetched only when needed.
//   TL_BASE=http://127.0.0.1:5059 node scripts/qa/cdp.mjs scripts/qa/garage_autoplay.mjs        (exit status 1 on any failure)
// The hold is shortened to 2.5 s with ?dwell=2.5 (the page accepts 2 to 30 s) so the whole round fits in a minute; the default is 3 s (one extra check below runs at the default).
const BASE = process.env.TL_BASE || "http://127.0.0.1:5059";
const PAGE = process.env.AUTOPLAY_PATH || "/vehicles";
const DWELL = 2.5;
let failed = 0;
const report = (ok, label, detail = "") => { if (!ok) { failed++; } console.log((ok ? "PASS  " : "FAIL  ") + label + (detail ? "  (" + detail + ")" : "")); };

export default async function (b) {
  await b.colorScheme(false);
  await b.send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  await b.send("Network.enable");
  await b.send("Network.setCacheDisabled", { cacheDisabled: false });         // the timing checks run with Rockstar's pictures already in the cache (a first fetch over a slow link is the network's time, not the showcase's); the fetch check at the end switches it off
  await b.send("Emulation.setFocusEmulationEnabled", { enabled: true });      // a headless page is not focused by default, and a focus event would never fire
  const requested = [];
  b.on((d) => { if (d.method === "Network.requestWillBeSent") { requested.push(d.params.request.url); } });
  const ev = (x) => b.eval(x);
  const shown = () => ev(`document.querySelector("[data-stage]").getAttribute("data-vehicle")`);
  const clock = () => ev(`JSON.stringify(window.__gxClock ? window.__gxClock() : null)`).then(JSON.parse);
  // `preload`: every opening picture is asked for and waited for, so the timing checks measure the showcase and not the speed of Rockstar's server (a first fetch over a slow link can take seconds)
  const open = async (query, motion = "1", preload = true) => {
    await b.open(BASE + "/about", 100);
    await ev(`localStorage.setItem("tv-motion", "${motion}"); true`);
    await b.open(BASE + PAGE + query, 800);
    for (let i = 0; i < 40 && !(await ev(`!!window.__gxClock`).catch(() => false)); i++) { await b.sleep(100); }
    if (preload) { await ev(`new Promise((done) => { const imgs = [...document.querySelectorAll(".gx-art img")]; imgs.forEach((i) => { i.loading = "eager"; }); const t0 = Date.now(); const check = () => (imgs.every((i) => i.complete) || Date.now() - t0 > 40000 ? done(true) : setTimeout(check, 100)); check(); })`); }
  };
  // watch the shown machine for `seconds`, returning each change as [machine, seconds since the start]
  const watch = async (seconds, every = 100) => {
    const t0 = Date.now(); let last = await shown(); const changes = [];
    while (Date.now() - t0 < seconds * 1000) { await b.sleep(every); const now = await shown(); if (now !== last) { changes.push([now, (Date.now() - t0) / 1000]); last = now; } }
    return changes;
  };

  // warm the cache once: every opening picture is asked for and waited for
  await open("?autoplay=0");
  await ev(`new Promise((done) => { const imgs = [...document.querySelectorAll(".gx-art img")]; imgs.forEach((i) => { i.loading = "eager"; }); const t0 = Date.now(); const check = () => (imgs.every((i) => i.complete) || Date.now() - t0 > 30000 ? done(true) : setTimeout(check, 100)); check(); })`);
  // ---- 1. it starts on the Cheetah and goes 01 to 07 and round to 01, holding each scene
  await open(`?dwell=${DWELL}`);
  report((await shown()) === "grotti-cheetah", "it starts with the Cheetah (01)");
  const scrollBefore = await ev("scrollY");
  const changes = await watch(DWELL * 9 + 16);
  const names = ["grotti-cheetah", ...changes.map((c) => c[0])];
  const expected = ["grotti-cheetah", "vapid-dominator-buggy", "shitzu-squalo", "vapid-stanier", "vapid-ganado", "dinka-enduro", "crest-kayak", "grotti-cheetah"];
  report(JSON.stringify(names.slice(0, 8)) === JSON.stringify(expected), "the order is 01, 02, 03, 04, 05, 06, 07 and then 01 again", names.join(" > "));
  const gaps = changes.slice(1, 7).map((c, i) => c[1] - changes[i][1]);
  report(gaps.every((g) => g > DWELL * 0.9 && g < DWELL + 3.5), `each scene is held for about the dwell (${DWELL} s, plus the second it takes to open and the time its picture takes to arrive)`, gaps.map((g) => g.toFixed(1)).join(", "));
  report((await ev("scrollY")) === scrollBefore, "the page did not scroll by itself while it cycled", String(scrollBefore) + " -> " + (await ev("scrollY")));
  const c1 = await clock();
  report(typeof c1.elapsed === "number" && c1.dwell === DWELL * 1000, "the progress clock runs against the dwell", JSON.stringify({ elapsed: Math.round(c1.elapsed), dwell: c1.dwell }));
  const barMoves = await ev(`getComputedStyle(document.querySelector("[data-stage]")).getPropertyValue("--p")`);
  report(parseFloat(barMoves) >= 0, "the progress value is published for the bar", barMoves);

  // ---- 2. there is no play or pause control: the showcase simply runs (its camera stops with it when the tab is hidden or the opening is out of the window, see garage_camera.mjs)
  await open(`?dwell=${DWELL}`);
  const noCtl = await ev(`document.querySelectorAll("[data-playpause], .gx-pause, .gx-play").length + [...document.querySelectorAll("[data-stage] button")].filter((x) => /pause|play|resume/i.test(x.getAttribute("aria-label") || x.textContent)).length`);
  report(noCtl === 0, "there is no visible play or pause control", String(noCtl));
  const running = await clock();
  report(running.userPaused === false && running.running === true, "it starts running by itself", JSON.stringify({ paused: running.userPaused, running: running.running }));

  // ---- 3. a choice responds at once, sets the hold back to nothing, and never stops the showcase: pressed with a real mouse (which then stays on the index) or the keyboard
  const press = async (slug) => {
    const r = JSON.parse(await ev(`(() => { const q = document.querySelector('[data-pick="${slug}"]').getBoundingClientRect(); return JSON.stringify([q.left + q.width / 2, q.top + q.height / 2]); })()`));
    await b.send("Input.dispatchMouseEvent", { type: "mouseMoved", x: r[0], y: r[1] });
    await b.send("Input.dispatchMouseEvent", { type: "mousePressed", x: r[0], y: r[1], button: "left", buttons: 1, clickCount: 1 });
    await b.send("Input.dispatchMouseEvent", { type: "mouseReleased", x: r[0], y: r[1], button: "left", buttons: 0, clickCount: 1 });
  };
  await open(`?dwell=${DWELL}`);
  await b.sleep(DWELL * 1000 - 700);                      // nearly at the end of the Cheetah's hold
  const t0 = Date.now();
  await press("vapid-ganado");
  const idx = await ev(`(() => { const a = document.querySelector('[data-pick="vapid-ganado"]'); const lit = a.getAttribute("aria-current") === "true"; return lit; })()`);
  report(idx === true, "the index answers a real press at once (the lit number has already moved when the press returns)", String(idx));
  let at = null;
  for (let i = 0; i < 40; i++) { if ((await shown()) === "vapid-ganado") { at = Date.now() - t0; break; } await b.sleep(50); }
  report(at !== null && at < 4500, "choosing a machine with a real press shows its scene as soon as its picture is decoded (software rendering on a busy machine: seconds at the very most; the index answers at once)", at === null ? "never" : at + " ms");
  const afterChoice = await watch(DWELL + 2.2);
  const firstAuto = afterChoice[0];
  report(!!firstAuto && firstAuto[0] === "dinka-enduro" && firstAuto[1] > DWELL * 0.85, "after a choice (the mouse still on the index) the hold starts again and the next machine follows it (06 after 05)", firstAuto ? firstAuto[0] + " after " + firstAuto[1].toFixed(1) + " s" : "no change");
  await press("shitzu-squalo");
  await b.sleep(400);
  const afterThree = await watch(DWELL + 2.2);
  report(afterThree.length >= 1 && afterThree[0][0] === "vapid-stanier", "choosing 03 shows 03 and then goes on to 04", afterThree.map((c) => c[0]).join(","));
  await press("crest-kayak");
  await b.sleep(400);
  const afterSeven = await watch(DWELL + 2.2);
  report(afterSeven.length >= 1 && afterSeven[0][0] === "grotti-cheetah", "choosing 07 shows 07 and then goes on to 01", afterSeven.map((c) => c[0]).join(","));
  const stillRunning = await clock();
  report(stillRunning.userPaused === false && stillRunning.running === true, "choosing numbers never pauses the showcase", JSON.stringify({ paused: stillRunning.userPaused, running: stillRunning.running }));
  // the keyboard: focus a number and press Enter; focus stays on it, and the showcase goes on
  await ev(`document.querySelector('[data-pick="dinka-enduro"]').focus(); true`);
  await b.send("Input.dispatchKeyEvent", { type: "keyDown", key: "Enter", code: "Enter", windowsVirtualKeyCode: 13 });
  await b.send("Input.dispatchKeyEvent", { type: "keyUp", key: "Enter", code: "Enter", windowsVirtualKeyCode: 13 });
  await b.sleep(500);
  const keyed = await shown();
  const afterKey = await watch(DWELL + 2.2);
  report(keyed === "dinka-enduro" && afterKey.length >= 1 && afterKey[0][0] === "crest-kayak", "choosing 06 from the keyboard shows 06 and then goes on to 07", keyed + " then " + afterKey.map((c) => c[0]).join(","));
  // the showcase's own pace, recorded inside the page (no polling from here): with no review switch it changes about every three seconds
  await open("");
  const paceGaps = await ev(`new Promise((done) => { const st = document.querySelector("[data-stage]"), at = []; const mo = new MutationObserver(() => at.push(performance.now())); mo.observe(st, { attributes: true, attributeFilter: ["data-vehicle"] }); setTimeout(() => { mo.disconnect(); done(JSON.stringify(at.slice(1).map((x, i) => +((x - at[i]) / 1000).toFixed(2)))); }, 24000); })`).then(JSON.parse);
  const sorted = [...paceGaps].sort((x, y) => x - y), median = sorted[Math.floor(sorted.length / 2)];
  report(paceGaps.length >= 3 && median >= 2.6 && median <= 4.6 && sorted[sorted.length - 1] < 7, "at its own pace the scene changes about every three seconds (median, longest)", `${median} s, ${sorted[sorted.length - 1]} s of ${paceGaps.length}: ${paceGaps.join(", ")}`);

  // ---- 4. a pointer on the words or the controls holds it; so does focus
  await open(`?dwell=${DWELL}`);
  const btn = JSON.parse(await ev(`(() => { const r = document.querySelector('.gx-scene.is-active .gbtn').getBoundingClientRect(); return JSON.stringify([r.left + r.width / 2, r.top + r.height / 2]); })()`));
  await b.send("Input.dispatchMouseEvent", { type: "mouseMoved", x: btn[0], y: btn[1] });
  const heldPointer = await watch(DWELL * 2 + 1);
  report(heldPointer.length === 0, "with the pointer on Explore it does not advance", String(heldPointer.length) + " changes");
  await b.send("Input.dispatchMouseEvent", { type: "mouseMoved", x: 700, y: 300 });
  const afterPointer = await watch(DWELL + 2.5);
  report(afterPointer.length >= 1, "with the pointer away it goes on", afterPointer.map((c) => c[0]).join(","));
  await open(`?dwell=${DWELL}`);
  await ev(`document.querySelector('[data-pick="vapid-stanier"]').focus(); true`);
  const heldFocus = await watch(DWELL * 2 + 1);
  report(heldFocus.length >= 1, "keyboard focus in the index does not stop it (a choice there never pauses the showcase)", heldFocus.map((c) => c[0]).join(","));
  await ev(`document.querySelector('.gx-scene.is-active .gbtn').focus(); true`);
  const heldExplore = await watch(DWELL * 2 + 1);
  report(heldExplore.length === 0, "with keyboard focus on Explore it does not advance", String(heldExplore.length) + " changes");
  await ev(`document.activeElement.blur(); true`);
  const afterFocus = await watch(DWELL + 2.5);
  report(afterFocus.length >= 1, "with focus gone it goes on", afterFocus.map((c) => c[0]).join(","));

  // ---- 5. off screen and a hidden tab
  await open(`?dwell=${DWELL}`);
  await ev(`window.scrollTo(0, 1800); true`);
  await b.sleep(600);
  const offA = await shown();
  const offChanges = await watch(DWELL * 2 + 1);
  report(offChanges.length === 0 && (await shown()) === offA, "with the opening out of the window it does not advance", String(offChanges.length) + " changes");
  const scrolled = await ev("scrollY");
  await ev(`window.scrollTo(0, 0); true`);
  const backChanges = await watch(DWELL + 2.5);
  report(backChanges.length >= 1, "scrolled back into view it goes on", backChanges.map((c) => c[0]).join(",") + " (was at " + scrolled + ")");
  await open(`?dwell=${DWELL}`);
  await ev(`Object.defineProperty(document, "hidden", { configurable: true, get: () => true }); document.dispatchEvent(new Event("visibilitychange")); true`);
  const hiddenChanges = await watch(DWELL * 2 + 1);
  report(hiddenChanges.length === 0, "with the tab hidden it does not advance", String(hiddenChanges.length) + " changes");
  await ev(`Object.defineProperty(document, "hidden", { configurable: true, get: () => false }); document.dispatchEvent(new Event("visibilitychange")); true`);
  const shownAgain = await watch(DWELL + 2.5);
  report(shownAgain.length >= 1, "with the tab shown again it goes on", shownAgain.map((c) => c[0]).join(","));

  // ---- 6. motion switched off (the site's own switch), and the page's own off switch
  await open(`?dwell=${DWELL}`, "0");
  const off = await ev(`document.documentElement.classList.contains("motion-on") + "|" + (window.__gxClock().userPaused)`);
  report(off === "false|true", "with motion off it waits for a choice and does not cycle by itself", off);
  const offMoves = await watch(DWELL * 2 + 1);
  report(offMoves.length === 0, "with motion off it does not advance by itself", String(offMoves.length) + " changes");
  await press("grotti-cheetah");
  await ev(`document.querySelector('[data-pick="vapid-stanier"]').click(); true`);
  await b.sleep(700);
  report((await shown()) === "vapid-stanier", "with motion off a choice still shows its scene at once, with the plain fade");
  await open(`?autoplay=0&dwell=${DWELL}`);
  const zero = await watch(DWELL * 2 + 1);
  report(zero.length === 0 && (await clock()).userPaused === true, "?autoplay=0 starts it paused");

  // ---- 7. what is fetched: one big picture at first, the next only when it is nearly time, and the clip only when the finale is near
  await b.send("Network.setCacheDisabled", { cacheDisabled: true });
  requested.length = 0;
  await open(`?dwell=${DWELL * 2}`, "1", false);
  await b.sleep(900);
  const bigStage = new Set(requested.filter((u) => /rockstargames\.com/.test(u) && /imwidth=(1920|2560|3840)/.test(u)));
  report(bigStage.size <= 3, "at first only the scene on show and the next two are fetched (not all seven)", String(bigStage.size) + " large pictures requested");
  const videoAny = await ev(`document.querySelectorAll("video").length`);
  report(videoAny === 0, "the collection has no video to load, stall or restart (every chapter is a still picture)", String(videoAny));
  await ev(`document.querySelector(".gx-f--finale").scrollIntoView({ block: "start" }); true`);
  await b.sleep(2500);
  const videoRequests = requested.filter((u) => /\.mp4/.test(u)).length;
  report(videoRequests === 0, "scrolling to the finale asks for no video file", String(videoRequests));
  // ---- a scene is never shown before its picture has arrived (no empty frame): on a slow link, with nothing cached, the showcase waits for the picture
  await b.send("Network.emulateNetworkConditions", { offline: false, latency: 250, downloadThroughput: 300 * 1024, uploadThroughput: 300 * 1024 });
  await b.send("Network.setCacheDisabled", { cacheDisabled: true });
  await open("?dwell=30", "1", false);
  const empty = await ev(`new Promise((done) => {
    const bad = []; const t0 = performance.now(); let shown = 0;
    document.querySelector('[data-pick="vapid-stanier"]').click();
    setTimeout(() => document.querySelector('[data-pick="vapid-ganado"]').click(), 300);
    const tick = () => { document.querySelectorAll(".gx-scene.is-active").forEach((p) => { shown++; const i = p.querySelector(".gx-art img"); if (!(i.complete && i.naturalWidth > 0)) { bad.push(p.dataset.panel + "@" + Math.round(performance.now() - t0)); } }); if (performance.now() - t0 < 14000) { requestAnimationFrame(tick); } else { done(JSON.stringify({ bad: bad.slice(0, 3), frames: shown, now: document.querySelector("[data-stage]").getAttribute("data-vehicle") })); } };
    requestAnimationFrame(tick);
  })`).then(JSON.parse);
  report(empty.bad.length === 0 && empty.now === "vapid-ganado", "on a slow link a scene is not shown until its picture has arrived (no empty frame)", JSON.stringify(empty));
  await b.send("Network.emulateNetworkConditions", { offline: false, latency: 0, downloadThroughput: -1, uploadThroughput: -1 });
  await b.send("Network.setCacheDisabled", { cacheDisabled: false });

  await ev(`localStorage.clear(); true`);
  console.log(failed ? `\n${failed} FAILED` : "\nall passed");
  process.exitCode = failed ? 1 : 0;
}
