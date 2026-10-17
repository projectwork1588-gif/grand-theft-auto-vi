// The Garage opening's automatic showcase, checked in a real browser: 01 to 07 and round to 01, the hold on each scene, Pause and Play, a choice
// resetting the hold, the clock waiting for a pointer, for focus, for the opening to leave the window and for a hidden tab, motion switched off,
// the page never scrolling by itself, and the pictures and the sea clip being fetched only when needed.
//   TL_BASE=http://127.0.0.1:5059 node scripts/qa/cdp.mjs scripts/qa/garage_autoplay.mjs        (exit status 1 on any failure)
// The hold is shortened to 2.5 s with ?dwell=2.5 (the page accepts 2 to 30 s) so the whole round fits in a minute; the default is 7 s.
const BASE = process.env.TL_BASE || "http://127.0.0.1:5059";
const PAGE = process.env.AUTOPLAY_PATH || "/garage-concept";
const DWELL = 2.5;
let failed = 0;
const report = (ok, label, detail = "") => { if (!ok) { failed++; } console.log((ok ? "PASS  " : "FAIL  ") + label + (detail ? "  (" + detail + ")" : "")); };

export default async function (b) {
  await b.colorScheme(false);
  await b.send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  await b.send("Network.enable");
  await b.send("Network.setCacheDisabled", { cacheDisabled: true });          // so a picture that is shown again is fetched again, and the requests mean what they say
  await b.send("Emulation.setFocusEmulationEnabled", { enabled: true });      // a headless page is not focused by default, and a focus event would never fire
  const requested = [];
  b.on((d) => { if (d.method === "Network.requestWillBeSent") { requested.push(d.params.request.url); } });
  const ev = (x) => b.eval(x);
  const shown = () => ev(`document.querySelector("[data-stage]").getAttribute("data-vehicle")`);
  const clock = () => ev(`JSON.stringify(window.__gxClock ? window.__gxClock() : null)`).then(JSON.parse);
  const open = async (query, motion = "1") => {
    await b.open(BASE + "/about", 100);
    await ev(`localStorage.setItem("tv-motion", "${motion}"); true`);
    await b.open(BASE + PAGE + query, 800);
    for (let i = 0; i < 40 && !(await ev(`!!window.__gxClock`).catch(() => false)); i++) { await b.sleep(100); }
  };
  // watch the shown machine for `seconds`, returning each change as [machine, seconds since the start]
  const watch = async (seconds, every = 100) => {
    const t0 = Date.now(); let last = await shown(); const changes = [];
    while (Date.now() - t0 < seconds * 1000) { await b.sleep(every); const now = await shown(); if (now !== last) { changes.push([now, (Date.now() - t0) / 1000]); last = now; } }
    return changes;
  };

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

  // ---- 2. Pause and Play
  await open(`?dwell=${DWELL}`);
  const label1 = await ev(`document.querySelector("[data-playpause]").getAttribute("aria-label") + "|" + document.querySelector("[data-playpause]").getAttribute("aria-pressed")`);
  report(label1 === "Pause the showcase|false", "while it plays the button says Pause", label1);
  await ev(`document.querySelector("[data-playpause]").click(); true`);
  const label2 = await ev(`document.querySelector("[data-playpause]").getAttribute("aria-label") + "|" + document.querySelector("[data-playpause]").getAttribute("aria-pressed") + "|" + document.querySelector("[data-playword]").textContent`);
  report(label2 === "Play the showcase|true|Play", "after Pause the button says Play", label2);
  const heldAt = await shown();
  const whilePaused = await watch(DWELL * 2 + 1);
  report(whilePaused.length === 0 && (await shown()) === heldAt, "paused, it does not advance in two and a half holds", String(whilePaused.length) + " changes");
  await ev(`document.querySelector("[data-playpause]").click(); true`);
  const afterPlay = await watch(DWELL + 2.5);
  report(afterPlay.length >= 1, "pressing Play sets it going again", afterPlay.map((c) => c[0]).join(","));

  // ---- 3. a choice responds at once and sets the hold back to nothing
  await open(`?dwell=${DWELL}`);
  await b.sleep(DWELL * 1000 - 700);                      // nearly at the end of the Cheetah's hold
  const t0 = Date.now();
  await ev(`document.querySelector('[data-pick="vapid-ganado"]').click(); true`);
  let at = null;
  for (let i = 0; i < 40; i++) { if ((await shown()) === "vapid-ganado") { at = Date.now() - t0; break; } await b.sleep(50); }
  report(at !== null && at < 900, "choosing a machine shows it at once", at === null ? "never" : at + " ms");
  const afterChoice = await watch(DWELL + 2.2);
  const firstAuto = afterChoice[0];
  report(!!firstAuto && firstAuto[0] === "dinka-enduro" && firstAuto[1] > DWELL * 0.85, "after a choice the hold starts again and the next machine follows it (06 after 05)", firstAuto ? firstAuto[0] + " after " + firstAuto[1].toFixed(1) + " s" : "no change");

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
  report(heldFocus.length === 0, "with keyboard focus in the index it does not advance", String(heldFocus.length) + " changes");
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
  const off = await ev(`document.querySelector("[data-playpause]").getAttribute("aria-pressed") + "|" + document.documentElement.classList.contains("motion-on")`);
  report(off === "true|false", "with motion off it starts paused and offers Play", off);
  const offMoves = await watch(DWELL * 2 + 1);
  report(offMoves.length === 0, "with motion off it does not advance by itself", String(offMoves.length) + " changes");
  await ev(`document.querySelector("[data-playpause]").click(); true`);
  const playedOff = await watch(DWELL + 2.5);
  report(playedOff.length >= 1, "a visitor who presses Play gets it, with the plain fade", playedOff.map((c) => c[0]).join(","));
  await open(`?autoplay=0&dwell=${DWELL}`);
  const zero = await watch(DWELL * 2 + 1);
  report(zero.length === 0 && (await clock()).userPaused === true, "?autoplay=0 starts it paused");

  // ---- 7. what is fetched: one big picture at first, the next only when it is nearly time, and the clip only when the finale is near
  requested.length = 0;
  await open(`?dwell=${DWELL * 2}`);
  await b.sleep(900);
  const bigStage = new Set(requested.filter((u) => /rockstargames\.com/.test(u) && /imwidth=(1920|2560|3840)/.test(u)));
  report(bigStage.size <= 2, "at first only the first scene's large picture is fetched (not all seven)", String(bigStage.size) + " large pictures requested");
  const video0 = requested.filter((u) => /on-the-water\.mp4/.test(u)).length;
  report(video0 === 0, "the sea clip is not asked for while the opening is on show", String(video0));
  await ev(`document.querySelector(".gx-finale").scrollIntoView({ block: "start" }); true`);
  await b.sleep(4500);
  const videoRequests = requested.filter((u) => /on-the-water\.mp4/.test(u)).length;
  const sea = await ev(`(() => { const v = document.querySelector(".gx-sea__video"); return v ? JSON.stringify({ src: !!v.currentSrc, ended: v.ended, playing: document.querySelector(".gx-sea").classList.contains("is-playing"), muted: v.muted }) : "none"; })()`);
  console.log("      sea clip: " + sea + ", requests " + videoRequests);
  report(sea === "none" || (videoRequests >= 1 && videoRequests <= 3 && JSON.parse(sea).muted), "near the finale the clip is requested once (muted)", String(videoRequests));
  await open(`?dwell=${DWELL}`, "0");
  await ev(`window.scrollTo(0, document.documentElement.scrollHeight); true`);
  requested.length = 0;
  await b.sleep(2500);
  report(requested.filter((u) => /on-the-water\.mp4/.test(u)).length === 0, "with motion off the clip is never asked for (the still stays)");

  await ev(`localStorage.clear(); true`);
  console.log(failed ? `\n${failed} FAILED` : "\nall passed");
  process.exitCode = failed ? 1 : 0;
}
