// Media page, "The Screening" (/media), in a real browser.
//   TL_BASE=http://127.0.0.1:5063 node scripts/qa/cdp.mjs scripts/qa/screening_qa.mjs        (exit status 1 on any failure)
// At every size: no horizontal overflow, no console, page or request errors, every picture that has been scrolled to loaded, nothing larger than the screen, every external link
// https to an official host in a new tab, the rail present and in step with the sections, the menu marks Media, the opening's title clear of the header.
// Once, at desktop: the trailer player opens for each film with the right Rockstar address and closes on Escape; the viewer opens on the right picture, moves with the arrow keys,
// shows its position and closes on Escape with focus returned; deep links open the right picture, follow the viewer and are cleared on close; an unknown deep link does nothing; the
// every chapter's View all opens one viewer across that chapter's pictures, and its closed thumbnails open it too; the chapters keep their own compositions; the old Stories pages still answer; the first load asks for few pictures, no video and no zip.
//   QA_SIZES=1920x1080,1440x900,1024x768,768x1024,390x844,360x740   QA_REDUCE=1 emulates reduced motion.
const BASE = process.env.TL_BASE || "http://127.0.0.1:5063";
const SIZES = (process.env.QA_SIZES || "1920x1080,1440x900,1024x768,768x1024,390x844,360x740").split(",").map((s) => s.split("x").map(Number));
const HOSTS = ["www.rockstargames.com", "rockstargames.com", "media-rockstargames-com.akamaized.net"];
let failed = 0;
const report = (ok, label, detail = "") => { if (!ok) { failed++; } console.log((ok ? "PASS  " : "FAIL  ") + label + (detail ? "  (" + detail + ")" : "")); };

export default async function (b) {
  const problems = [];
  const reqs = new Map();
  let bytes = { image: 0, other: 0, n: 0, media: 0, zip: 0 };
  let counting = false;
  b.on((d) => {
    if (d.method === "Runtime.exceptionThrown") { problems.push("exception: " + (d.params.exceptionDetails.exception?.description || d.params.exceptionDetails.text)); }
    if (d.method === "Runtime.consoleAPICalled" && d.params.type === "error") { problems.push("console: " + (d.params.args || []).map((a) => a.value || a.description).join(" ")); }
    if (d.method === "Network.loadingFailed" && !d.params.canceled) { problems.push("failed: " + d.params.errorText + " " + (d.params.type || "")); }
    if (d.method === "Network.requestWillBeSent" && counting) { reqs.set(d.params.requestId, { url: d.params.request.url, type: d.params.type }); }
    if (d.method === "Network.loadingFinished" && counting && reqs.has(d.params.requestId)) {
      const r = reqs.get(d.params.requestId);
      bytes.n++;
      if (r.type === "Image") { bytes.image += d.params.encodedDataLength; } else { bytes.other += d.params.encodedDataLength; }
      if (/\.mp4(\?|$)/.test(r.url) || r.type === "Media") { bytes.media++; }
      if (/\.zip(\?|$)/.test(r.url)) { bytes.zip++; }
    }
  });
  await b.send("Network.enable");
  // wait for a condition in the page, polling, for at most `ms` (a bounded wait, never a fixed sleep); resolves true if the condition held, false if the time ran out
  const waitFor = (js, ms = 8000) => b.eval(`new Promise((r) => { const t0 = Date.now(); const t = setInterval(() => { let ok = false; try { ok = (${js}); } catch (e) {} if (ok || Date.now() - t0 > ${ms}) { clearInterval(t); r(!!ok); } }, 100); })`);
  await b.colorScheme(process.env.QA_REDUCE === "1");
  await b.send("Network.setCacheDisabled", { cacheDisabled: true });          // a picture from the cache would hide whether it was asked for
  await b.open(BASE + "/about", 100);
  await b.eval(`localStorage.setItem("tv-motion", "1"); true`);

  // ---- first load, measured at laptop size before anything is scrolled
  await b.send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  reqs.clear(); bytes = { image: 0, other: 0, n: 0, media: 0, zip: 0 }; counting = true;
  await b.open(BASE + "/media", 3500);
  counting = false;
  const firstImages = [...reqs.values()].filter((r) => r.type === "Image").length;
  const huge = [...reqs.values()].filter((r) => /imwidth=(2560|3840)/.test(r.url)).length;
  report(firstImages <= 14, "first load: only the pictures near the top are asked for", `${firstImages} pictures, ${(bytes.image / 1048576).toFixed(2)} MB of images, ${(bytes.other / 1024).toFixed(0)} KB of everything else`);
  report(huge === 0, "first load: no full-size (2560 or 3840 wide) picture is downloaded");
  const thumbs = [...reqs.values()].filter((r) => /imwidth=360/.test(r.url)).length;
  report(thumbs === 0, "first load: no thumbnail from behind a chapter's View all is downloaded");
  report(bytes.media === 0 && bytes.zip === 0, "first load: no video file and no zip is downloaded");
  report(bytes.image < 6 * 1048576, "first load: images under 6 MB", (bytes.image / 1048576).toFixed(2) + " MB");

  for (const [W, H] of SIZES) {
    await b.send("Emulation.setDeviceMetricsOverride", { width: W, height: H, deviceScaleFactor: 1, mobile: W < 700 });
    problems.length = 0;
    await b.open(BASE + "/media", 1800);
    const tag = `${W}x${H}`;
    const total = await b.eval("document.documentElement.scrollHeight");
    for (let y = 0; y < total; y += Math.round(H * 0.75)) { await b.eval(`window.scrollTo(0, ${y}); true`); await b.sleep(90); }
    await b.sleep(1500);
    const over = await b.eval(`Math.max(document.documentElement.scrollWidth, document.body.scrollWidth) - window.innerWidth`);
    report(over <= 0, `${tag}: no horizontal overflow`, over + "px");
    const screens = (total / H).toFixed(1);
    console.log(`INFO  ${tag}: the page is ${total}px, ${screens} screens`);
    report(problems.length === 0, `${tag}: no console, page or request errors`, problems.slice(0, 3).join(" | "));
    // pictures come from Rockstar over the network: give those still loading up to 20 s to finish. A picture that has FAILED is already complete with no width, so it is not waited for and still fails below.
    const settled = await waitFor(`[...document.querySelectorAll("main img.sc-img")].filter((i) => !i.closest("details:not([open])")).every((i) => i.complete)`, 20000);
    const pics = JSON.parse(await b.eval(`(() => { const imgs = [...document.querySelectorAll("main img.sc-img")].filter((i) => i.closest("details:not([open])") === null); return JSON.stringify({ n: imgs.length, broken: imgs.filter((i) => !(i.complete && i.naturalWidth > 0)).map((i) => (i.alt || i.currentSrc).slice(-60) + " [complete=" + i.complete + ", width=" + i.naturalWidth + ", " + (i.currentSrc || i.src).slice(-40) + "]") }); })()`));
    report(pics.n >= 70 && pics.broken.length === 0, `${tag}: every picture loaded`, `${pics.n} pictures${settled ? "" : ", still loading after 20 s"}, broken: ${pics.broken.slice(0, 3).join(", ")}`);
    const shape = JSON.parse(await b.eval(`(() => { const tiles = [...document.querySelectorAll("main a[data-lightbox][id]")]; const ids = tiles.map((t) => t.id); const drawn = tiles.filter((t) => !t.closest("details:not([open])"));
      const small = drawn.filter((t) => { const r = t.getBoundingClientRect(); return r.width < 60 || r.height < 30; }).length;
      const wide = drawn.filter((t) => t.getBoundingClientRect().width > window.innerWidth + 1).length;
      const heads = [...document.querySelectorAll(".sc-h2, .sc-h3, .sc-h4, .sc-title")].filter((e) => e.scrollWidth > e.clientWidth + 1).map((e) => e.textContent.trim().slice(0, 30));
      return JSON.stringify({ tiles: tiles.length, unique: new Set(ids).size, noId: ids.filter((i) => !i).length, small, wide, heads }); })()`));
    report(shape.tiles === 187 && shape.unique === 187 && shape.noId === 0, `${tag}: 187 pictures, each with its own deep-link id`, JSON.stringify(shape));
    report(shape.small === 0 && shape.wide === 0 && shape.heads.length === 0, `${tag}: nothing too small, wider than the screen or clipped`, JSON.stringify(shape));
    const links = JSON.parse(await b.eval(`JSON.stringify([...document.querySelectorAll("main a[href^='http']:not([data-lightbox]):not([data-open])")].map((a) => ({ h: a.href, t: a.target, r: a.rel, dl: !!a.closest(".sc-dl") })))`));
    const lbBad = await b.eval(`[...document.querySelectorAll("main a[data-lightbox], main a[data-open]")].filter((a) => !a.href.startsWith("https://www.rockstargames.com/VI/_next/static/media/")).length`);
    report(lbBad === 0, `${tag}: every picture link points at Rockstar's own image address`);
    const badLinks = links.filter((l) => !(l.h.startsWith("https://") && HOSTS.includes(new URL(l.h).hostname) && (l.dl || l.t === "_blank") && /noopener/.test(l.r)));
    report(links.length >= 20 && badLinks.length === 0, `${tag}: every external link is https to an official host and opens safely`, `${links.length} links, bad: ${JSON.stringify(badLinks.slice(0, 2))}`);
    const rail = JSON.parse(await b.eval(`JSON.stringify([...document.querySelectorAll("[data-rail-link]")].map((a) => ({ id: a.dataset.railLink, ok: !!document.getElementById(a.dataset.railLink), count: +a.querySelector("i").textContent })))`));
    report(rail.length === 8 && rail.every((r) => r.ok), `${tag}: the rail has a link to every section`, rail.map((r) => r.id + ":" + r.count).join(" "));
    await b.eval(`window.scrollTo(0, 0); true`); await b.sleep(500);
    const head = JSON.parse(await b.eval(`(() => { const t = document.querySelector(".sc-title").getBoundingClientRect(), h = document.querySelector(".site-header").getBoundingClientRect(); const cur = document.querySelector('.header-nav a[aria-current="page"], .site-menu a[aria-current="page"]'); return JSON.stringify({ top: Math.round(t.top - h.bottom), left: Math.round(t.left), right: Math.round(window.innerWidth - t.right), cur: cur ? cur.textContent.trim() : null }); })()`));
    report(head.top >= 0 && head.left >= 0 && head.right >= 0, `${tag}: the opening's title is on the screen and clear of the header`, JSON.stringify(head));
    report(W < 1024 || head.cur === "Media", `${tag}: the menu marks Media`, String(head.cur));
  }

  // ---- once, at desktop
  await b.send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  await b.open(BASE + "/media", 2000);
  const json = async (js) => JSON.parse(await b.eval(`JSON.stringify((() => { ${js} })())`));
  const viewer = () => json(`const d = document.getElementById("image-dialog"); return { open: d.open, cap: d.querySelector("[data-caption]").textContent, count: d.querySelector("[data-count]").textContent, hash: location.hash, ok: d.querySelector("[data-image]").naturalWidth > 0 };`);
  let v;
  const key = async (k, code, vk) => { await b.send("Input.dispatchKeyEvent", { type: "keyDown", key: k, code, windowsVirtualKeyCode: vk }); await b.send("Input.dispatchKeyEvent", { type: "keyUp", key: k, code, windowsVirtualKeyCode: vk }); };
  const closeVisible = async (dialogId) => b.eval(`(() => { const c = document.querySelector("#${dialogId} [data-close]"); const r = c.getBoundingClientRect(); const top = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2); return top === c && r.top >= 0 && r.bottom <= window.innerHeight; })()`);
  // the opening and every film open Rockstar's own player with their own address, and close on Escape
  const players = JSON.parse(await b.eval(`JSON.stringify([...document.querySelectorAll("[data-video]")].map((e) => ({ v: e.dataset.video, t: e.dataset.title })))`));
  const want = { "76orsa95": "Launch Trailer", "rk721912": "An Extended Look", "cpys7u21": "Trailer 2", "rkoCtr1r": "Trailer 1" };
  report(players.length === 5 && Object.keys(want).every((id) => players.some((p) => p.v.startsWith("https://www.rockstargames.com/videoplayer?id=" + id + "&embed"))), "players: the opening and four films carry Rockstar's own player address", players.map((p) => p.v.match(/id=(\w+)/)[1]).join(" "));
  for (const [id, name] of Object.entries(want)) {
    await b.eval(`document.querySelector('[data-video*="id=${id}&"]').click(); true`); await b.sleep(900);
    const st = JSON.parse(await b.eval(`(() => { const d = document.getElementById("video-dialog"); const f = d.querySelector("iframe"); return JSON.stringify({ open: d.open, src: f ? f.src : null, title: d.querySelector("[data-title]").textContent }); })()`));
    report(st.open && st.src && st.src.startsWith("https://www.rockstargames.com/videoplayer?id=" + id) && new RegExp(name.replace("Launch ", "")).test(st.title + " "), `player: ${name} opens Rockstar's player`, JSON.stringify(st).slice(0, 150));
    await key("Escape", "Escape", 27); await b.sleep(400);
    const closed = JSON.parse(await b.eval(`JSON.stringify({ open: document.getElementById("video-dialog").open, frames: document.getElementById("video-dialog").querySelectorAll("iframe").length })`));
    report(!closed.open && closed.frames === 0, `player: Escape closes ${name} and stops it`);
    await b.eval(`document.querySelector('[data-video*="id=${id}&"]').click(); true`); await b.sleep(700);
    report(await closeVisible("video-dialog"), `player: the Close button of ${name} is drawn, on the screen and the topmost thing at its place`);
    await b.eval(`document.querySelector("#video-dialog [data-close]").click(); true`); await b.sleep(400);
    report(!(await b.eval(`document.getElementById("video-dialog").open`)), `player: the Close button closes ${name}`);
  }
  // the viewer
  const first = await b.eval(`(() => { const t = document.querySelector("#pair a.sc-tile"); t.scrollIntoView({ block: "center" }); return t.id; })()`);
  await b.sleep(600);
  await b.eval(`document.getElementById(${JSON.stringify(first)}).focus(); true`);
  await key("Enter", "Enter", 13); await b.sleep(900);
  await b.eval(`new Promise((r) => { const i = document.querySelector("#image-dialog [data-image]"); const t = setInterval(() => { if (i.naturalWidth > 0) { clearInterval(t); r(true); } }, 100); setTimeout(() => { clearInterval(t); r(false); }, 8000); })`);
  const v1 = JSON.parse(await b.eval(`(() => { const d = document.getElementById("image-dialog"); return JSON.stringify({ open: d.open, cap: d.querySelector("[data-caption]").textContent, count: d.querySelector("[data-count]").textContent, src: d.querySelector("[data-image]").src.slice(0, 90), hash: location.hash, ok: d.querySelector("[data-image]").naturalWidth > 0 }); })()`));
  report(v1.open && v1.count === "1 / 13" && /Jason and Lucia 01/.test(v1.cap) && v1.hash === "#" + first && v1.ok, "viewer: Enter on a picture opens it, whole, with its title and position", JSON.stringify(v1).slice(0, 220));
  report(await closeVisible("image-dialog"), "viewer: the Close button is drawn, on the screen and the topmost thing at its place");
  await key("ArrowRight", "ArrowRight", 39); await b.sleep(700);
  const v2 = JSON.parse(await b.eval(`(() => { const d = document.getElementById("image-dialog"); return JSON.stringify({ cap: d.querySelector("[data-caption]").textContent, count: d.querySelector("[data-count]").textContent, hash: location.hash }); })()`));
  report(v2.count === "2 / 13" && /Jason and Lucia 02/.test(v2.cap) && v2.hash === "#shot-jason-and-lucia-02", "viewer: ArrowRight moves on and the address follows", JSON.stringify(v2));
  await key("ArrowLeft", "ArrowLeft", 37); await b.sleep(500);
  report((await b.eval(`document.getElementById("image-dialog").querySelector("[data-count]").textContent`)) === "1 / 13", "viewer: ArrowLeft moves back");
  const nav = JSON.parse(await b.eval(`(() => { const d = document.getElementById("image-dialog"); const r = (s) => d.querySelector(s).getBoundingClientRect(); return JSON.stringify({ prev: [Math.round(r("[data-lb-prev]").width), Math.round(r("[data-lb-prev]").height)], next: [Math.round(r("[data-lb-next]").width), Math.round(r("[data-lb-next]").height)], close: [Math.round(r("[data-close]").width), Math.round(r("[data-close]").height)] }); })()`));
  report(nav.prev[0] >= 40 && nav.prev[1] >= 40 && nav.next[0] >= 40 && nav.next[1] >= 40 && nav.close[1] >= 36, "viewer: previous, next and close are comfortable to touch", JSON.stringify(nav));
  await key("Escape", "Escape", 27); await b.sleep(500);
  const v3 = JSON.parse(await b.eval(`JSON.stringify({ open: document.getElementById("image-dialog").open, hash: location.hash, focus: document.activeElement.id })`));
  report(!v3.open && v3.hash === "" && v3.focus === first, "viewer: Escape closes it, clears the address and returns focus to the picture", JSON.stringify(v3));
  // the first chapter: four pictures large, then View all, in one viewer group of thirteen
  await b.open(BASE + "/media", 1800);
  const ch = await json(`const c = document.getElementById("pair"); return { large: c.querySelectorAll("a.sc-tile").length, thumbs: c.querySelectorAll("a.sc-sheet__tile").length, group: c.querySelectorAll("[data-gallery] a[data-lightbox]").length, closed: !c.querySelector("details.sc-more").open, drawn: [...c.querySelectorAll(".sc-sheet__tile img")].filter((i) => i.getClientRects().length > 0 && !i.closest("details:not([open])")).length, btn: (c.querySelector(".sc-btn") || {}).textContent };`);
  report(ch.large === 4 && ch.thumbs === 9 && ch.group === 13 && ch.closed && ch.drawn === 0 && /View all 13/.test(ch.btn), "first chapter: four pictures drawn large, nine behind View all in the same viewer group, thumbnails closed", JSON.stringify(ch));
  await b.eval(`(() => { const o = document.querySelector("#pair .sc-btn"); o.scrollIntoView({ block: "center" }); o.focus(); o.click(); })()`);
  await waitFor(`document.querySelector("#image-dialog [data-image]").naturalWidth > 0`);
  v = await viewer();
  report(v.open && v.count === "1 / 13" && v.ok && /Jason and Lucia 01/.test(v.cap), "first chapter: View all 13 opens the viewer at 1 / 13", JSON.stringify(v).slice(0, 140));
  for (let i = 0; i < 4; i++) { await key("ArrowRight", "ArrowRight", 39); await b.sleep(250); }
  await b.sleep(400);
  v = await viewer();
  report(v.count === "5 / 13", "first chapter: the arrows go on from the four large pictures into the nine that were not drawn", JSON.stringify(v).slice(0, 120));
  await key("Escape", "Escape", 27); await b.sleep(500);
  report(!(await viewer()).open && (await b.eval(`!!document.activeElement.closest("#pair")`)), "first chapter: Escape closes the viewer and focus stays in the chapter");
  await b.open(BASE + "/media#shot-jason-and-lucia-09", 2500);
  await waitFor(`document.querySelector("#image-dialog [data-image]").naturalWidth > 0`);
  v = await viewer();
  const onScreen = await b.eval(`(() => { const r = document.getElementById("pair").getBoundingClientRect(); return r.top < innerHeight && r.bottom > 0; })()`);
  report(v.open && v.count === "9 / 13" && /Jason and Lucia 09/.test(v.cap) && v.ok && onScreen, "first chapter: a deep link to a picture that is not drawn opens it at 9 / 13 with its chapter on the screen", JSON.stringify({ ...v, onScreen }).slice(0, 170));
  await key("Escape", "Escape", 27); await b.sleep(400);
  // deep links
  await b.open(BASE + "/media#shot-jason-duval-07", 2500);
  await b.eval(`new Promise((r) => { const i = document.querySelector("#image-dialog [data-image]"); const t = setInterval(() => { if (i.naturalWidth > 0) { clearInterval(t); r(true); } }, 100); setTimeout(() => { clearInterval(t); r(false); }, 8000); })`);
  const dl = JSON.parse(await b.eval(`(() => { const d = document.getElementById("image-dialog"); return JSON.stringify({ open: d.open, cap: d.querySelector("[data-caption]").textContent, count: d.querySelector("[data-count]").textContent, ok: d.querySelector("[data-image]").naturalWidth > 0 }); })()`));
  const expect = await b.eval(`(() => { const t = document.getElementById("shot-jason-duval-07"); const group = [...t.closest("[data-gallery]").querySelectorAll("a[data-lightbox]")]; return (group.indexOf(t) + 1) + " / " + group.length; })()`);
  report(dl.open && /Jason Duval 07/.test(dl.cap) && dl.count === expect && dl.ok, "deep link: /media#shot-jason-duval-07 opens Jason Duval 07 at its place in its chapter", JSON.stringify(dl) + " expected " + expect);
  await key("Escape", "Escape", 27); await b.sleep(400);
  await b.open(BASE + "/media#shot-no-such-picture", 1800);
  report(!(await b.eval(`document.getElementById("image-dialog").open`)), "deep link: an unknown address opens nothing");
  await b.open(BASE + "/media#art-official-cover-art", 2500);
  const dl2 = JSON.parse(await b.eval(`(() => { const d = document.getElementById("image-dialog"); return JSON.stringify({ open: d.open, cap: d.querySelector("[data-caption]").textContent, count: d.querySelector("[data-count]").textContent }); })()`));
  report(dl2.open && /Official Cover Art/.test(dl2.cap) && /\/ 25$/.test(dl2.count), "deep link: key art opens in its own group of 25", JSON.stringify(dl2));
  await key("Escape", "Escape", 27); await b.sleep(300);
  // a picture Rockstar no longer serves: an empty frame, not a broken icon; and the viewer says so
  await b.open(BASE + "/media", 1800);
  await b.eval(`(() => { const t = document.getElementById("shot-jason-and-lucia-02"); t.scrollIntoView({ block: "center" }); const i = t.querySelector("img"); i.removeAttribute("srcset"); i.src = "https://www.rockstargames.com/VI/_next/static/media/this-picture-does-not-exist.jpg"; })()`); await b.sleep(2500);
  report(await b.eval(`document.getElementById("shot-jason-and-lucia-02").classList.contains("is-broken") && getComputedStyle(document.querySelector("#shot-jason-and-lucia-02 img")).visibility === "hidden"`), "broken picture: the tile becomes an empty frame and the broken icon is hidden");
  await b.eval(`document.getElementById("shot-jason-and-lucia-03").href = "https://www.rockstargames.com/VI/_next/static/media/this-picture-does-not-exist.jpg"; document.getElementById("shot-jason-and-lucia-03").click(); true`); await b.sleep(2500);
  report(await b.eval(`document.getElementById("image-dialog").open && /could not be loaded from Rockstar/.test(document.querySelector("#image-dialog [data-caption]").textContent)`), "broken picture: the viewer says the picture could not be loaded");
  await key("Escape", "Escape", 27); await b.sleep(300);
  // the rail
  await b.open(BASE + "/media", 1800);
  await b.eval(`document.querySelector('[data-rail-link="places"]').click(); true`); await b.sleep(1600);
  const cur = await b.eval(`(document.querySelector('[data-rail-link][aria-current="true"]') || {}).dataset ? document.querySelector('[data-rail-link][aria-current="true"]').dataset.railLink : null`);
  const gap = await b.eval(`Math.round(document.getElementById("places").getBoundingClientRect().top - document.querySelector(".sc-rail").getBoundingClientRect().bottom)`);
  const railH = await b.eval(`Math.round(document.querySelector(".sc-rail").getBoundingClientRect().height)`);
  report(railH <= 44, "rail: the programme bar is quiet, a single slim line", railH + "px");
  report(cur === "places" && gap >= -2 && gap < 400, "rail: a link scrolls to its reel, clear of the header and the rail, and marks it", `current ${cur}, gap ${gap}px`);
  // every chapter's View all opens the viewer at 1 / N, in the chapter's own group, and the arrows move on
  const pills = await json(`return [...document.querySelectorAll("main a.sc-btn[data-open]")].map((a) => ({ id: a.dataset.open, n: +a.textContent.match(/\\d+/)[0], chapter: (a.closest("article, section, .sc-edition") || {}).id || "" }));`);
  report(pills.length === 18 && pills.reduce((s, x) => s + x.n, 0) === 187, "View all: 18 chapters, together every one of the 187 pictures", pills.map((x) => x.n).join(" "));
  let okPills = 0; const badPills = [];
  for (let i = 0; i < pills.length; i++) {
    await b.eval(`(() => { const a = document.querySelectorAll("main a.sc-btn[data-open]")[${i}]; a.scrollIntoView({ block: "center" }); a.click(); })()`);
    await waitFor(`document.querySelector("#image-dialog [data-image]").naturalWidth > 0 && document.getElementById("image-dialog").open`);
    v = await viewer();
    if (v.open && v.count === "1 / " + pills[i].n && v.ok && v.hash === "#" + pills[i].id) { okPills++; } else { badPills.push(pills[i].id + " " + JSON.stringify(v).slice(0, 80)); }
    await key("Escape", "Escape", 27); await b.sleep(250);
  }
  report(okPills === pills.length, "View all: each opens the viewer at 1 / N of its own chapter", badPills.slice(0, 3).join(" | "));
  // the closed thumbnails of a chapter open when asked, load only then, and open the same viewer
  await b.open(BASE + "/media", 1500);
  reqs.clear(); counting = true;
  await b.eval(`(() => { const d = document.querySelector("#people-jason-duval details.sc-more"); d.scrollIntoView({ block: "center" }); d.querySelector("summary").click(); })()`);
  await waitFor(`[...document.querySelectorAll("#people-jason-duval .sc-sheet__tile img")].every((i) => i.complete && i.naturalWidth > 0)`); await b.sleep(500);
  counting = false;
  const th = [...reqs.values()].filter((r) => /imwidth=360/.test(r.url));
  report(th.length === 10 && th.every((r) => /Jason_Duval_/.test(r.url)), "thumbnails: opening one chapter's sheet loads exactly that chapter's ten thumbnails, no other chapter's", th.length + " requested");
  const thumbHref = await b.eval(`document.querySelectorAll("#people-jason-duval .sc-sheet__tile")[4].href`);
  await b.eval(`(() => { const t = document.querySelectorAll("#people-jason-duval .sc-sheet__tile")[4]; t.scrollIntoView({ block: "center" }); t.click(); })()`);
  const thumbLoaded = await waitFor(`(() => { const d = document.getElementById("image-dialog"), i = d.querySelector("[data-image]"); return d.open && i.src === ${JSON.stringify(thumbHref)} && i.complete && i.naturalWidth > 0; })()`, 15000);
  v = await viewer();
  const thumbState = await json(`const i = document.querySelector("#image-dialog [data-image]"); return { complete: i.complete, width: i.naturalWidth, isThisPicture: i.src === ${JSON.stringify(thumbHref)} };`);
  report(thumbLoaded && v.open && /\/ 10$/.test(v.count) && v.ok, "thumbnails: a thumbnail opens the viewer in its chapter's group of ten", JSON.stringify({ ...v, ...thumbState }).slice(0, 200));
  await key("Escape", "Escape", 27); await b.sleep(300);
  // each chapter keeps its own composition (desktop)
  const comp = await json(`const top = (s) => Math.round(document.querySelector(s).getBoundingClientRect().top); const w = (s) => [...document.querySelectorAll(s)].map((e) => Math.round(e.getBoundingClientRect().width));
    const leads = [...document.querySelectorAll(".sc-lead")].map((e) => Math.round(e.getBoundingClientRect().top + scrollY));
    return { leadsApart: leads.length === 2 ? leads[1] - leads[0] : -1, cast: document.querySelectorAll(".sc-cell").length, hang: w(".sc-hang .sc-mat"), regions: w(".sc-reg"), showroom: document.querySelectorAll(".sc-frame").length, index: document.querySelectorAll(".sc-index a").length };`);
  report(comp.leadsApart > 40 && comp.cast === 6, "people: the two leads side by side, the second set lower, with the six around them", JSON.stringify(comp));
  report(new Set(comp.hang).size >= 3 && comp.hang.length === 4, "key art: four pieces hung at different scales", comp.hang.join(" "));
  report(new Set(comp.regions).size === 2 && comp.regions.length === 5, "places: five regions in two widths of collage", comp.regions.join(" "));
  report(comp.showroom === 8 && comp.index >= 20, "editions: four frames and an index of every group for each", `${comp.showroom} frames, ${comp.index} index links`);
  // keyboard focus
  await b.open(BASE + "/media", 1500);
  let reached = 0, rings = 0;
  for (let i = 0; i < 40 && reached < 4; i++) {
    await key("Tab", "Tab", 9);
    const onLink = await b.eval(`(() => { const e = document.activeElement; if (!e || !e.closest(".sc")) { return null; } const cs = getComputedStyle(e); return { ring: cs.outlineStyle !== "none" && parseFloat(cs.outlineWidth) >= 2 }; })()`);
    if (onLink) { reached++; if (onLink.ring) { rings++; } }
  }
  report(reached >= 4 && rings === reached, "keyboard: Tab reaches the page's own controls and each shows a focus ring", `${rings}/${reached}`);
  // the old stories still answer
  for (const [p, code] of [["/missions", 200], ["/missions/harbour-lights", 200], ["/locations/neon-row-district", 200]]) {
    await b.open(BASE + p, 400);
    report((await b.eval(`location.pathname`)) === p && (await b.eval(`document.querySelector("h1") !== null`)), `legacy: ${p} still opens`);
  }
  const anim = await b.eval(`document.getAnimations().length`);
  if (process.env.QA_REDUCE === "1") { report(anim === 0, "reduced motion: no animation is running", String(anim)); }
  console.log(failed ? `\n${failed} FAILED` : "\nall passed");
  process.exitCode = failed ? 1 : 0;
}
