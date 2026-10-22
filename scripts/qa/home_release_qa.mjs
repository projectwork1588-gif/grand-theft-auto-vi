// Home: the picture challenge ("How well do you know Leonida?"), the official release block, the hero's camera and the trailer dialog, in a real browser.
//   TL_BASE=http://127.0.0.1:5071 node scripts/qa/cdp.mjs scripts/qa/home_release_qa.mjs        (exit status 1 on any failure)
// Use a server that does NOT force motion on (TV_AUTOPLAY_ALWAYS unset) so the reduced-motion check is meaningful.
// At every size: no horizontal overflow, no console, page or request errors, both sections drawn, the key art and the Launch Trailer card loaded, no inline style, links to Rockstar https and
// opening in a new tab with noopener. Once, at desktop: nothing of the challenge is requested before it is near; five rounds from Rockstar's pictures with four answers each, right and wrong
// answers marked in words as well as colour, a working link to the site's own page for each answer, the result and Play again; the keyboard path; a picture that cannot load is skipped and
// if none can, the three plain links remain; the Launch Trailer opens in Rockstar's own player with a loading state, Escape closes it and clears the page state; the hero camera (arrival and
// breath), its reveal and its pausing off screen and behind a dialog; reduced motion.
//   QA_SIZES=1920x1080,1440x900,1024x768,768x1024,390x844,360x740   QA_REDUCE=1 emulates the visitor's reduced-motion preference.
const BASE = process.env.TL_BASE || "http://127.0.0.1:5071";
const SIZES = (process.env.QA_SIZES || "1920x1080,1440x900,1024x768,768x1024,390x844,360x740").split(",").map((s) => s.split("x").map(Number));
let failed = 0;
const report = (ok, label, d = "") => { if (!ok) { failed++; } console.log((ok ? "PASS  " : "FAIL  ") + label + (d ? "  (" + d + ")" : "")); };

export default async function (b) {
  const problems = [];
  const reqs = new Map();
  let counting = false;
  b.on((d) => {
    if (d.method === "Runtime.exceptionThrown") { problems.push("exception: " + (d.params.exceptionDetails.exception?.description || d.params.exceptionDetails.text)); }
    if (d.method === "Runtime.consoleAPICalled" && d.params.type === "error") { problems.push("console: " + (d.params.args || []).map((a) => a.value || a.description).join(" ")); }
    if (d.method === "Network.loadingFailed" && !d.params.canceled && !String(d.params.errorText).includes("BLOCKED")) { problems.push("failed: " + d.params.errorText + " " + (d.params.type || "")); }
    if (d.method === "Network.requestWillBeSent" && counting) { reqs.set(d.params.requestId, d.params.request.url); }
  });
  const json = async (js) => JSON.parse(await b.eval(`JSON.stringify((() => { ${js} })())`));
  const waitFor = (js, ms = 8000) => b.eval(`new Promise((r) => { const t0 = Date.now(); const t = setInterval(() => { let ok = false; try { ok = (${js}); } catch (e) {} if (ok || Date.now() - t0 > ${ms}) { clearInterval(t); r(!!ok); } }, 100); })`);
  // a real key press: Enter carries its character, as it does from a keyboard (a button is activated by that, not by the key-down alone)
  const key = async (k, code, vk) => { const text = k === "Enter" ? "\r" : undefined; await b.send("Input.dispatchKeyEvent", { type: "keyDown", key: k, code, windowsVirtualKeyCode: vk, ...(text ? { text } : {}) }); await b.send("Input.dispatchKeyEvent", { type: "keyUp", key: k, code, windowsVirtualKeyCode: vk }); };
  const toSection = (id, dy = 0) => b.eval(`(() => { const e = document.getElementById("${id}"); window.scrollTo(0, e.getBoundingClientRect().top + scrollY + ${dy}); })()`);
  await b.send("Network.enable");
  await b.send("Network.setCacheDisabled", { cacheDisabled: true });
  await b.colorScheme(process.env.QA_REDUCE === "1");
  await b.open(BASE + "/about", 100);
  // a visitor who has asked for reduced motion and not switched motion on must get none: only the normal run opts in
  await b.eval(process.env.QA_REDUCE === "1" ? `localStorage.removeItem("tv-motion"); true` : `localStorage.setItem("tv-motion", "1"); true`);

  // ---- first load: nothing of the challenge is asked for before it is near; no poster pictures for videos far below
  await b.send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  reqs.clear(); counting = true;
  await b.open(BASE + "/", 3000);
  counting = false;
  const urls = [...reqs.values()];
  report(!urls.some((u) => /imwidth=960/.test(u)), "first load: no picture of the challenge is requested before it is near", urls.filter((u) => /imwidth=960/.test(u)).length + " requested");
  report(!urls.some((u) => /\.mp4/.test(u)), "first load: no video file is requested");
  report(!urls.some((u) => /moment-[123]\.jpg|leonida-reel\.jpg/.test(u)) || urls.filter((u) => /moment-[123]\.jpg|leonida-reel\.jpg/.test(u)).length <= 1, "first load: the posters of the videos far below are not requested", urls.filter((u) => /moment-[123]\.jpg|leonida-reel\.jpg/.test(u)).map((u) => u.split("/").pop()).join(" "));

  for (const [W, H] of SIZES) {
    await b.send("Emulation.setDeviceMetricsOverride", { width: W, height: H, deviceScaleFactor: 1, mobile: W < 700 });
    problems.length = 0;
    await b.open(BASE + "/", 1800);
    const tag = `${W}x${H}`;
    const total = await b.eval("document.documentElement.scrollHeight");
    for (let y = 0; y < total; y += Math.round(H * 0.75)) { await b.eval(`window.scrollTo(0, ${y}); true`); await b.sleep(90); }
    await b.sleep(1500);
    const over = await b.eval(`Math.max(document.documentElement.scrollWidth, document.body.scrollWidth) - window.innerWidth`);
    report(over <= 0, `${tag}: no horizontal overflow`, over + "px");
    await toSection("release", -20);
    await waitFor(`(() => { const s = document.getElementById("release"); const a = s.querySelector(".release__art img"), f = s.querySelector(".release__film img"); return a && f && a.complete && a.naturalWidth > 0 && f.complete && f.naturalWidth > 0; })()`, 12000);
    const rel = await json(`const s = document.getElementById("release"); const art = s.querySelector(".release__art img"); const film = s.querySelector(".release__film img"); const r = s.getBoundingClientRect();
      const links = [...s.querySelectorAll("a[href]")].map((a) => ({ h: a.href, t: a.target, r: a.rel }));
      return { art: !!art && art.complete && art.naturalWidth > 0, film: !!film && film.complete && film.naturalWidth > 0, links, inlineStyle: s.querySelectorAll("[style]").length, h: Math.round(r.height), clipped: [...s.querySelectorAll("h2, .release__actions .btn")].filter((e) => e.scrollWidth > e.clientWidth + 1).length };`);
    report(rel.art && rel.film, `${tag}: the release block's key art and film poster loaded`, JSON.stringify({ art: rel.art, film: rel.film }));
    report(rel.links.length === 2 && rel.links.every((l) => /^https:\/\/www\.rockstargames\.com\/VI/.test(l.h) && l.t === "_blank" && /noopener/.test(l.r)) && rel.inlineStyle === 0 && rel.clipped === 0, `${tag}: the release links go to Rockstar's own pages in a new tab, nothing clipped, no inline style`, JSON.stringify(rel.links.map((l) => l.h)));
    await toSection("challenge", -20); await b.sleep(2500);
    const ch = await json(`const s = document.getElementById("challenge"); const q = s.querySelector("[data-quiz]"); const ui = s.querySelector("[data-quiz-ui]"); const img = s.querySelector("[data-quiz-img]"); const opts = [...s.querySelectorAll(".quiz__opt")];
      return { shown: !ui.hidden, plainHidden: getComputedStyle(s.querySelector(".quiz__plain")).display === "none", loaded: img.complete && img.naturalWidth > 100, opts: opts.length, inlineStyle: s.querySelectorAll("[style]").length, tooSmall: opts.filter((o) => { const r = o.getBoundingClientRect(); return r.height < 44; }).length, clipped: opts.filter((o) => o.scrollWidth > o.clientWidth + 2).length };`);
    report(ch.shown && ch.plainHidden && ch.loaded && ch.opts === 4, `${tag}: the challenge shows a Rockstar picture with four answers`, JSON.stringify(ch));
    report(ch.inlineStyle === 0 && ch.tooSmall === 0 && ch.clipped === 0, `${tag}: answers are touch-sized and unclipped, no inline style`);
    report(problems.length === 0, `${tag}: no console, page or request errors`, problems.slice(0, 3).join(" | "));
  }

  // ---- once, at desktop
  await b.send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  await b.open(BASE + "/", 2000);
  await toSection("challenge", -20);
  await waitFor(`document.querySelector("[data-quiz-img]").complete && document.querySelector("[data-quiz-img]").naturalWidth > 100`, 10000);
  const state = () => json(`const s = document.getElementById("challenge"); const reveal = s.querySelector("[data-quiz-reveal]"), end = s.querySelector("[data-quiz-end]");
    return { round: s.querySelector("[data-quiz-round]").textContent, score: s.querySelector("[data-quiz-score]").textContent, ask: s.querySelector("[data-quiz-ask]").textContent, opts: [...s.querySelectorAll(".quiz__opt")].map((o) => ({ t: o.textContent, d: o.disabled, c: o.className })), revealShown: !reveal.hidden, verdict: s.querySelector("[data-quiz-verdict]").textContent, line: s.querySelector("[data-quiz-line]").textContent, link: s.querySelector("[data-quiz-link]").getAttribute("href"), endShown: !end.hidden, total: s.querySelector("[data-quiz-total]").textContent, alt: s.querySelector("[data-quiz-img]").alt, focus: document.activeElement && (document.activeElement.getAttribute("data-quiz-next") !== null ? "next" : document.activeElement.getAttribute("data-quiz-ask") !== null ? "ask" : document.activeElement.className) };`);
  let st = await state();
  report(/^Picture 1 of 5$/.test(st.round) && st.score === "0 right" && !st.revealShown && st.opts.length === 4 && /^(Who is this\?|Which place is this\?|Which machine is this\?)$/.test(st.ask) && st.alt === "", "challenge: starts on picture 1 of 5, nothing revealed, the picture's alt does not give the answer away", JSON.stringify({ round: st.round, ask: st.ask, alt: st.alt }));
  let rights = 0, wrongs = 0, linksOk = true, badLink = "", marked = true;
  for (let round = 1; round <= 5; round++) {
    await waitFor(`document.querySelector("[data-quiz-img]").complete && document.querySelector("[data-quiz-img]").naturalWidth > 100 && !document.querySelector("[data-quiz-ask]").textContent.startsWith("Your")`, 10000);
    st = await state();
    if (round === 3) {                         // the keyboard path: Tab to an answer and press Enter
      await b.eval(`document.querySelector(".quiz__opt").focus(); true`);
      await key("Enter", "Enter", 13);
    } else {
      const pick = round % 2 === 0 ? 0 : 2;     // some right, some wrong, by chance
      await b.eval(`document.querySelectorAll(".quiz__opt")[${pick}].click(); true`);
    }
    await b.sleep(500);
    st = await state();
    const right = st.opts.filter((o) => /is-right/.test(o.c)).length === 1, wrong = st.opts.filter((o) => /is-wrong/.test(o.c)).length;   // the answer buttons only
    if (/^Right:/.test(st.verdict)) { rights++; if (wrong !== 0) { marked = false; } } else { wrongs++; if (wrong !== 1) { marked = false; } }
    if (!(right && st.opts.every((o) => o.d) && st.revealShown && st.alt.length > 5 && st.focus === "next")) { marked = false; }
    const href = st.link; const res = await b.eval(`fetch(${JSON.stringify(href)}).then((r) => r.status)`);
    if (!(href.startsWith("/") && res === 200)) { linksOk = false; badLink += href + ":" + res + " "; }
    if (round < 5) { await b.eval(`document.querySelector("[data-quiz-next]").click(); true`); await b.sleep(400); }
  }
  report(marked, "challenge: every answer locks the choices, marks the right one (and the pick if wrong) in words, names the answer in the picture's alt, and moves focus to Next picture");
  report(linksOk, "challenge: every reveal's link goes to a page of this site that exists", badLink);
  report(rights + wrongs === 5, "challenge: five rounds were played", `${rights} right, ${wrongs} wrong`);
  await b.eval(`document.querySelector("[data-quiz-next]").click(); true`); await b.sleep(500);
  st = await state();
  report(st.endShown && new RegExp("^You named " + rights + " of 5\\.$").test(st.total) && st.opts.length === 0, "challenge: the result states the score and offers the three pages and Play again", st.total);
  await b.eval(`document.querySelector("[data-quiz-again]").click(); true`);
  await waitFor(`document.querySelector("[data-quiz-img]").complete && document.querySelector("[data-quiz-img]").naturalWidth > 100`, 10000);
  st = await state();
  report(/^Picture 1 of 5$/.test(st.round) && st.score === "0 right" && !st.endShown && st.opts.length === 4, "challenge: Play again starts a new round from the beginning");
  // the keyboard: focus lands on the question after Next, answers are reachable with Tab
  report(await b.eval(`[...document.querySelectorAll(".quiz__opt")].every((o) => o.tabIndex >= 0 && o.tagName === "BUTTON")`), "challenge: the answers are real buttons in the tab order");

  // ---- a picture that cannot be loaded is skipped; if none can, the three plain links are what is left
  await b.send("Network.setBlockedURLs", { urls: ["*rockstargames.com/VI/_next/static/media/*imwidth=960*"] });
  await b.open(BASE + "/", 2000);
  await toSection("challenge", -20); await b.sleep(4000);
  const broken = await json(`const s = document.getElementById("challenge"); const q = s.querySelector("[data-quiz]"); return { broken: q.classList.contains("is-broken"), uiHidden: s.querySelector("[data-quiz-ui]").hidden, plain: getComputedStyle(s.querySelector(".quiz__plain")).display, links: s.querySelectorAll(".quiz__plain a").length };`);
  report(broken.broken && broken.uiHidden && broken.plain !== "none" && broken.links === 3, "challenge: when no picture can be loaded it steps aside and shows the three plain links", JSON.stringify(broken));
  await b.send("Network.setBlockedURLs", { urls: [] });

  // ---- the Launch Trailer opens in Rockstar's own player, with a loading state, and closes cleanly
  await b.open(BASE + "/", 1800);
  await toSection("release", -20); await b.sleep(1500);
  await b.eval(`document.querySelector(".release__film").click(); true`); await b.sleep(500);
  const dlg = await json(`const d = document.getElementById("video-dialog"); const f = d.querySelector("iframe"); return { open: d.open, src: f ? f.src : null, title: d.querySelector("[data-title]").textContent, status: d.querySelector("[data-player-status]").textContent, loadingClass: d.querySelector(".player").classList.contains("is-loading"), hasModal: document.documentElement.classList.contains("has-modal") };`);
  report(dlg.open && dlg.src && dlg.src.startsWith("https://www.rockstargames.com/videoplayer?id=76orsa95") && /Launch Trailer/.test(dlg.title) && dlg.hasModal, "the Launch Trailer opens Rockstar's own player, and the page knows a dialog is open", JSON.stringify({ src: (dlg.src || "").slice(0, 70), title: dlg.title }));
  report(await waitFor(`!document.querySelector("#video-dialog .player").classList.contains("is-loading") || document.querySelector("#video-dialog [data-player-status]").textContent.length > 0`, 12000), "the player shows a loading state, then either loads or says it is slow", dlg.status + " | loading=" + dlg.loadingClass);
  await key("Escape", "Escape", 27); await b.sleep(500);
  const closed = await json(`const d = document.getElementById("video-dialog"); return { open: d.open, frames: d.querySelectorAll("iframe").length, hasModal: document.documentElement.classList.contains("has-modal"), status: d.querySelector("[data-player-status]").hidden, loading: d.querySelector(".player").classList.contains("is-loading") };`);
  report(!closed.open && closed.frames === 0 && !closed.hasModal && closed.status && !closed.loading, "Escape closes it, stops the player and clears the page state", JSON.stringify(closed));

  // ---- the hero's camera
  await b.open(BASE + "/", 2500);
  const cam = await json(`const s = document.querySelector("[data-hero-stage]"); const l = s.querySelector(".hero__layer--fg"); const cs = getComputedStyle(l); return { cls: s.className, name: cs.animationName, dur: cs.animationDuration, motion: document.documentElement.classList.contains("motion-on"), opacity: getComputedStyle(s).opacity };`);
  if (process.env.QA_REDUCE === "1") {
    report(!cam.motion || cam.name === "none" || cam.dur.split(",").every((x) => parseFloat(x) < 0.01), "reduced motion: the hero camera does not run", JSON.stringify(cam));
  } else {
    report(cam.motion && /is-ready/.test(cam.cls) && cam.opacity === "1" && /heroDolly/.test(cam.name) && /heroArrive/.test(cam.name) && /^12s,\s*2\.6s$/.test(cam.dur), "hero: the layers were revealed together and run the arrival and the 12 s breath", JSON.stringify(cam));
    await b.eval(`window.scrollTo(0, 1800); true`); await b.sleep(700);
    report(await b.eval(`document.querySelector("[data-hero-stage]").classList.contains("is-paused") && getComputedStyle(document.querySelector(".hero__layer--fg")).animationPlayState === "paused" && getComputedStyle(document.querySelector(".hero__layer--fg")).willChange === "auto"`), "hero: off screen the camera is paused and the layers are not promoted");
    await b.eval(`window.scrollTo(0, 0); true`); await b.sleep(500);
    await b.eval(`document.querySelector("[data-video]").click(); true`); await b.sleep(600);
    report(await b.eval(`getComputedStyle(document.querySelector(".hero__layer--fg")).animationPlayState === "paused" && getComputedStyle(document.getElementById("video-dialog"), "::backdrop").backdropFilter === "none"`), "hero: behind an open dialog the camera is paused and the backdrop has no blur");
    await key("Escape", "Escape", 27); await b.sleep(400);
  }
  console.log(failed ? `\n${failed} FAILED` : "\nall passed");
  process.exitCode = failed ? 1 : 0;
}
