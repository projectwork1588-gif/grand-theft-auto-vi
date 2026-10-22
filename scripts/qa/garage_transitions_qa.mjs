// The Garage opening's scene changes, in a real browser: how quickly a choice is answered, pacing, the cross-fade, forward and backward through all seven, rapid input, the keyboard, reduced motion.
//   TL_BASE=http://127.0.0.1:5071 node scripts/qa/cdp.mjs scripts/qa/garage_transitions_qa.mjs        (exit status 1 on any failure; use a server that does not force motion on)
// Checks the timing (a 350 ms arrival, a 5 s hold, a 7 s camera push), that a choice is answered at once (the index lights, the picture starts to change and is fully in within a fraction of a second), that no clip-path box is ever used, that every step of seven forward and seven backward, twice round, ends with one
// active scene and the index, stage and picture agreeing, that the arrival is a real cross-fade sampled frame by frame (never a blank or dimmed frame, monotonic, about 1.1 s), that ten
// choices in three seconds and an A-B-A change of mind end in one consistent state, the arrow keys, Home and End, the clock's own changes (never faster than 6 s), and reduced motion.
const BASE = process.env.TL_BASE || "http://127.0.0.1:5071";
let failed = 0;
const report = (ok, label, d = "") => { if (!ok) failed++; console.log((ok ? "PASS  " : "FAIL  ") + label + (d ? "  (" + d + ")" : "")); };
export default async function (b) {
  const json = async (js) => JSON.parse(await b.eval(`JSON.stringify((() => { ${js} })())`));
  await b.send("Network.enable");
  await b.colorScheme(false);
  await b.open(BASE + "/about", 100);
  await b.eval(`localStorage.setItem("tv-motion", "1"); true`);
  await b.send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  await b.open(BASE + "/vehicles?autoplay=0", 2500);          // the clock off: only our own choices change the scene
  const state = () => json(`const s = document.querySelector("[data-stage]"); const panels = [...s.querySelectorAll("[data-panel]")];
    const vis = panels.filter((p) => !p.hidden); const act = panels.filter((p) => p.classList.contains("is-active"));
    return { stage: s.getAttribute("data-vehicle"), active: act.map((p) => p.getAttribute("data-panel")), visible: vis.map((p) => p.getAttribute("data-panel")), leaving: panels.filter((p) => p.classList.contains("is-leaving")).map((p) => p.getAttribute("data-panel")),
      current: (s.querySelector('[data-pick][aria-current="true"]') || {}).dataset ? s.querySelector('[data-pick][aria-current="true"]').dataset.pick : null, pending: s.querySelectorAll(".is-pending").length };`);
  const slugs = await json(`return [...document.querySelectorAll("[data-stage] [data-pick]")].map((a) => a.getAttribute("data-pick"));`);
  report(slugs.length === 7, "the seven vehicles are all there, in order", slugs.join(" "));
  const vars = await json(`const s = document.querySelector("[data-stage]"); return { fade: s.style.getPropertyValue("--gx-fade"), push: s.style.getPropertyValue("--gx-push"), clock: window.__gxClock && window.__gxClock().dwell };`);
  report(vars.fade === "350ms" && vars.push === "7000ms" && vars.clock === 5000, "timing: a 350 ms arrival, a 5 s hold, a 7 s camera push (it was 1.1 s, 6.5 s and 7.6 s)", JSON.stringify(vars));
  // ---- no box: the arriving picture is never clipped
  const clip = await json(`return [...document.querySelectorAll(".gx-scene .gx-art")].map((e) => getComputedStyle(e).clipPath).filter((c) => c !== "none");`);
  report(clip.length === 0, "no clip-path on any scene picture (the box-opening effect is gone)", JSON.stringify(clip));
  // ---- forward through all seven, twice round, and backward through all seven, twice round
  let ok = true, bad = "";
  const settled = (expect) => b.eval(`new Promise((r) => { const t0 = Date.now(); const t = setInterval(() => { const s = document.querySelector("[data-stage]"); const vis = [...s.querySelectorAll("[data-panel]")].filter((p) => !p.hidden); const ok = vis.length === 1 && vis[0].getAttribute("data-panel") === ${JSON.stringify(expect)} && !s.querySelector(".is-leaving"); if (ok || Date.now() - t0 > 7000) { clearInterval(t); r(ok); } }, 80); })`);
  const check = async (label, expect) => {
    await settled(expect);                                      // a bounded wait for the scene to settle, never a fixed pause: a slow machine takes longer
    const s = await state();
    const good = s.active.length === 1 && s.active[0] === expect && s.stage === expect && s.current === expect && s.visible.length === 1 && s.leaving.length === 0 && s.pending === 0;
    if (!good) { ok = false; bad += ` [${label}: ${JSON.stringify(s)} expected ${expect}]`; }
  };
  let idx = 0;
  for (let i = 0; i < 14; i++) { await b.eval(`document.querySelector('[data-step="1"]').click(); true`); idx = (idx + 1) % 7; await check("next " + (i + 1), slugs[idx]); }
  report(ok, "forward through all seven, twice round: each step ends with one active scene, one visible, the index and the stage agreeing", bad.slice(0, 300));
  ok = true; bad = "";
  for (let i = 0; i < 14; i++) { await b.eval(`document.querySelector('[data-step="-1"]').click(); true`); idx = (idx + 6) % 7; await check("prev " + (i + 1), slugs[idx]); }
  report(ok, "backward through all seven, twice round: the same", bad.slice(0, 300));
  // ---- how quickly a choice is answered (the pictures have arrived by now; a slow machine gets a generous margin)
  await b.sleep(5000);
  const lat = JSON.parse(await b.eval(`new Promise((res) => { const s = document.querySelector("[data-stage]"); const to = ${JSON.stringify(slugs[3])}; const tick = s.querySelector('[data-pick="' + to + '"]'); const panel = s.querySelector('[data-panel="' + to + '"]'); const m = { lit: null, start: null, full: null }; const t0 = performance.now(); tick.click();
    const f = (n) => { const t = n - t0; if (m.lit === null && tick.getAttribute("aria-current") === "true") m.lit = t; const op = panel.hidden ? 0 : +getComputedStyle(panel).opacity; if (m.start === null && op >= 0.1) m.start = t; if (m.full === null && op >= 0.99) m.full = t; if (t < 2500 && m.full === null) requestAnimationFrame(f); else res(JSON.stringify(m)); }; requestAnimationFrame(f); })`));
  report(lat.lit !== null && lat.lit <= 120, "a choice lights its number in the index at once", Math.round(lat.lit) + " ms");
  report(lat.start !== null && lat.start <= 250 && lat.full !== null && lat.full <= 800, "…the picture starts to change within a fraction of a second and is fully in well under a second", `starts ${Math.round(lat.start)} ms, fully in ${Math.round(lat.full)} ms`);
  await settled(slugs[3]);
  // ---- the arrival, frame by frame: nothing blank, nothing that flashes
  await b.eval(`window.__samples = []; window.__sample = (ms) => new Promise((res) => { const t0 = performance.now(); const tick = (n) => { const s = document.querySelector("[data-stage]"); const o = {}; [...s.querySelectorAll("[data-panel]")].filter((p) => !p.hidden).forEach((p) => { o[p.getAttribute("data-panel")] = +getComputedStyle(p).opacity; }); window.__samples.push({ t: Math.round(n - t0), o }); if (n - t0 < ms) requestAnimationFrame(tick); else res(window.__samples.length); }; requestAnimationFrame(tick); }); true`);
  const from = await state(); const to = slugs[(slugs.indexOf(from.active[0]) + 3) % 7];
  const run = b.eval(`window.__sample(2000)`);
  await b.sleep(120);
  await b.eval(`document.querySelector('[data-stage] [data-pick="${to}"]').click(); true`);
  await run;
  const samples = await json(`return window.__samples;`);
  const during = samples.filter((s) => Object.keys(s.o).length > 1);
  const blank = samples.filter((s) => Math.max(0, ...Object.values(s.o)) < 0.999);
  const arriving = samples.map((s) => s.o[to]).filter((v) => v !== undefined);
  let monotone = true; for (let i = 1; i < arriving.length; i++) { if (arriving[i] + 0.002 < arriving[i - 1]) monotone = false; }
  const span = during.length ? during[during.length - 1].t - during[0].t : 0;
  report(during.length >= 5 && span >= 200, "the change is a real cross-fade: two scenes on screen for the arrival", during.length + " frames with both, over " + span + " ms");
  report(blank.length === 0, "never a blank or dimmed frame: at every frame one scene is fully opaque", blank.length + " frames below full cover of " + samples.length);
  report(monotone && arriving[arriving.length - 1] === 1, "the arriving scene fades in smoothly and monotonically to full", arriving.slice(0, 3).map((v) => v.toFixed(2)).join(",") + " ... " + arriving.slice(-2).join(","));
  const fadeMs = (() => { const first = samples.findIndex((s) => s.o[to] > 0.01), last = samples.findIndex((s) => s.o[to] >= 0.999); return first >= 0 && last >= 0 ? samples[last].t - samples[first].t : -1; })();
  report(fadeMs >= 200 && fadeMs <= 600, "the arrival takes about a third of a second", fadeMs + " ms");
  // ---- rapid input: ten different choices within about three seconds
  await b.sleep(1500);
  const seq = [2, 5, 0, 4, 1, 6, 3, 5, 2, 4].map((i) => slugs[i]);
  for (const s of seq) { await b.eval(`document.querySelector('[data-stage] [data-pick="${s}"]').click(); true`); await b.sleep(280); }
  const last = seq[seq.length - 1];
  await settled(last);
  let st = await state();
  report(st.active.length === 1 && st.active[0] === last && st.stage === last && st.current === last && st.visible.length === 1 && st.leaving.length === 0 && st.pending === 0, "rapid input (ten choices in three seconds) ends in one consistent state: the last choice, one scene, nothing left over", JSON.stringify(st));
  // ---- rapid choices never dip: sample while clicking fast
  await b.eval(`window.__samples = []; true`);
  const run2 = b.eval(`window.__sample(3200)`);
  await b.sleep(100);
  for (const i of [1, 4, 2, 6, 3, 0]) { await b.eval(`document.querySelector('[data-stage] [data-pick="${slugs[i]}"]').click(); true`); await b.sleep(330); }
  await run2;
  const s2 = await json(`return window.__samples;`);
  const dips = s2.filter((s) => Math.max(0, ...Object.values(s.o)) < 0.999);
  report(dips.length === 0, "rapid choices never leave a blank or dimmed frame", dips.length + " of " + s2.length + " frames");
  await settled(slugs[0]); st = await state();
  report(st.active.length === 1 && st.visible.length === 1 && st.leaving.length === 0 && st.active[0] === slugs[0], "…and settle on the last choice with one scene", JSON.stringify(st));
  // ---- choosing the machine already on show, and choosing A then B then A again before B arrives, change nothing and leave nothing pending
  await b.eval(`document.querySelector('[data-stage] [data-pick="${slugs[0]}"]').click(); true`); await b.sleep(600);
  await b.eval(`document.querySelector('[data-stage] [data-pick="${slugs[3]}"]').click(); document.querySelector('[data-stage] [data-pick="${slugs[0]}"]').click(); true`); await b.sleep(1600);
  st = await state();
  report(st.active[0] === slugs[0] && st.current === slugs[0] && st.pending === 0 && st.visible.length === 1, "A, B, then A again at once: stays on A with nothing pending", JSON.stringify(st));
  // ---- keyboard: arrows, Home, End on the index
  await b.eval(`document.querySelector('[data-stage] [data-pick="${slugs[0]}"]').focus(); true`);
  const key = async (k, code, vk) => { await b.send("Input.dispatchKeyEvent", { type: "keyDown", key: k, code, windowsVirtualKeyCode: vk }); await b.send("Input.dispatchKeyEvent", { type: "keyUp", key: k, code, windowsVirtualKeyCode: vk }); await b.sleep(1500); };
  await key("ArrowDown", "ArrowDown", 40); st = await state();
  report(st.active[0] === slugs[1] && st.current === slugs[1], "keyboard: ArrowDown moves to the next machine", st.active[0]);
  await key("End", "End", 35); st = await state();
  report(st.active[0] === slugs[6], "keyboard: End goes to the last", st.active[0]);
  await key("Home", "Home", 36); st = await state();
  report(st.active[0] === slugs[0], "keyboard: Home goes to the first", st.active[0]);
  report(await b.eval(`document.activeElement.getAttribute("data-pick") === "${slugs[0]}"`), "keyboard: focus stays on the index, on the machine shown");
  // ---- the automatic clock: calm, on its own (a fresh page, clock running)
  await b.open(BASE + "/vehicles", 800);
  await b.eval(`window.__changes = []; new MutationObserver(() => { window.__changes.push(Math.round(performance.now())); }).observe(document.querySelector("[data-stage]"), { attributes: true, attributeFilter: ["data-vehicle"] }); true`);
  await b.sleep(21000);
  const ch = await json(`return window.__changes;`);
  const gaps = ch.slice(1).map((t, i) => t - ch[i]);
  report(ch.length >= 2 && gaps.every((g) => g >= 4500 && g <= 7500), "the clock changes the scene every 5 seconds on its own (never faster than 4.5 s)", `${ch.length} changes, gaps ${gaps.join(", ")} ms`);
  // ---- reduced motion: the plain short fade, no clock
  await b.colorScheme(true);
  await b.eval(`localStorage.removeItem("tv-motion"); true`);
  await b.open(BASE + "/vehicles", 2500);
  const rm = await json(`const s = document.querySelector("[data-stage]"); return { motion: document.documentElement.classList.contains("motion-on"), clock: window.__gxClock && window.__gxClock().running, op: getComputedStyle(s.querySelector(".gx-scene.is-active")).opacity, tr: getComputedStyle(s.querySelector(".gx-scene.is-active")).transitionDuration };`);
  report(!rm.motion && !rm.clock && rm.op === "1", "reduced motion: no motion class, the clock does not run, the shown scene is plain and visible", JSON.stringify(rm));
  await b.eval(`document.querySelector('[data-step="1"]').click(); true`); await b.sleep(900);
  st = await state();
  report(st.active.length === 1 && st.active[0] === slugs[1] && st.current === slugs[1], "reduced motion: the arrows still change the machine", JSON.stringify(st));
  await b.colorScheme(false);
  console.log(failed ? `\n${failed} FAILED` : "\nall passed"); process.exitCode = failed ? 1 : 0;
}
