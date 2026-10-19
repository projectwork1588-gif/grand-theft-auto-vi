// Checks of the Garage concept page in a real browser: no console errors, every state of the MySQL-backed collection lays out, reduced motion, no script, keyboard.
const BASE = process.env.TL_BASE || "http://127.0.0.1:5059";
const Q = "autoplay=0";                                  // the clock is off here: these checks are about structure, not timing (scripts/qa/garage_autoplay.mjs covers the clock)
let failed = 0;
const ok = (c, label, detail = "") => { if (!c) { failed++; } console.log((c ? "PASS  " : "FAIL  ") + label + (detail ? "  (" + detail + ")" : "")); };

export default async function (b) {
  const errors = [];
  b.on((d) => {
    if (d.method === "Runtime.exceptionThrown") { errors.push("exception: " + (d.params.exceptionDetails.exception?.description || d.params.exceptionDetails.text)); }
    if (d.method === "Runtime.consoleAPICalled" && d.params.type === "error") { errors.push("console.error: " + d.params.args.map((a) => a.value || a.description).join(" ")); }
    if (d.method === "Log.entryAdded" && d.params.entry.level === "error" && !/rockstargames/.test(d.params.entry.url || "")) { errors.push("log: " + d.params.entry.text); }
  });
  await b.send("Log.enable");
  await b.colorScheme(false);
  await b.send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  await b.open(BASE + "/about", 100);
  await b.eval(`localStorage.setItem("tv-motion", "1"); true`);

  const count = (sel) => b.eval(`document.querySelectorAll(${JSON.stringify(sel)}).length`);
  const states = [
    ["/vehicles?"+Q, "all seven: four chapters, the mod-shop strip inside Street & Classics, the Kayak finale", { machines: 7, chapters: 4, customs: 1, finale: 1, list: 0 }],
    ["/vehicles?category=boat", "Boats: an ordered list of two, no chapters", { machines: 2, chapters: 0, customs: 0, finale: 0, list: 1 }],
    ["/vehicles?category=sports", "Sports: a list of one", { machines: 1, chapters: 0, customs: 0, finale: 0, list: 1 }],
    ["/vehicles?q=vapid&sort=name_desc", "search and sort together: the Vapid machines, Z to A", { machines: 3, chapters: 0, customs: 0, finale: 0, list: 1 }],
    ["/vehicles?per_page=3&page=2", "page two of a three-per-page list", { machines: 3, chapters: 0, customs: 0, finale: 0, list: 1 }],
  ];
  for (const [path, label, want] of states) {
    await b.open(BASE + path, 1600);
    const got = { machines: await count(".gx-m, .gx-f, .gx-d"), chapters: await count(".gx-chapter"), customs: await count(".gx-customs"), finale: await count(".gx-f--finale"), list: await count(".gx-list") };
    ok(JSON.stringify(got) === JSON.stringify(want), label, JSON.stringify(got));
    ok(!(await b.eval(`document.documentElement.scrollWidth > document.documentElement.clientWidth`)), `  no sideways scroll`);
  }
  await b.open(BASE + "/vehicles?q=zzzz", 1200);
  ok((await count(".gempty")) === 1 && (await count(".gx-m, .gx-f, .gx-d")) === 0, "an empty search shows the clear way back");
  const chap = await b.eval(`JSON.stringify([...document.querySelectorAll(".gx-chapter")].map((a) => a.dataset.chapter))`);
  console.log("      chapters on a plain visit: " + chap);

  // every machine's card links to its own page, and every picture that is drawn has loaded
  await b.open(BASE + "/vehicles?" + Q, 1500);
  await b.eval(`document.querySelectorAll("img").forEach((i) => { i.loading = "eager"; }); true`);
  await b.sleep(5000);
  const links = JSON.parse(await b.eval(`JSON.stringify([...document.querySelectorAll(".gx-f, .gx-d")].map((a) => a.getAttribute("href")))`));
  ok(links.length === 7 && new Set(links).size === 7 && links.every((l) => /^\/vehicles\/[a-z-]+$/.test(l)), "seven stages, seven different vehicle pages", links.join(" "));
  const broken = await b.eval(`[...document.images].filter((i) => i.getClientRects().length && (!i.complete || i.naturalWidth === 0)).length`);
  ok(broken === 0, "every picture drawn has loaded", String(broken));

  // keyboard: Tab reaches the Explore button, the arrows, the bays, the controls; arrow keys move along the bays
  await b.open(BASE + "/vehicles?" + Q, 1500);
  const stops = [];
  for (let i = 0; i < 32; i++) {
    await b.send("Input.dispatchKeyEvent", { type: "keyDown", key: "Tab", code: "Tab", windowsVirtualKeyCode: 9 });
    await b.send("Input.dispatchKeyEvent", { type: "keyUp", key: "Tab", code: "Tab", windowsVirtualKeyCode: 9 });
    stops.push(await b.eval(`(() => { const e = document.activeElement; const r = e.getBoundingClientRect(); return (e.getAttribute("aria-label") || e.textContent || e.tagName).trim().replace(/\\s+/g, " ").slice(0, 70) + "|" + Math.round(r.height) + "|" + getComputedStyle(e).outlineStyle; })()`));
  }
  console.log("      first stops: " + stops.slice(0, 14).join(" > "));
  ok(stops.some((s) => s.startsWith("Explore the")), "the Explore button is a tab stop");
  ok(!stops.some((s) => /(pause|resume|play) the showcase/i.test(s)), "there is no play or pause control among the tab stops (the showcase just runs)");
  ok(stops.filter((s) => /Previous machine|Next machine/.test(s)).length === 2, "the two arrows are tab stops");
  ok(stops.filter((s) => /, (Sports|Off-road|Boats|Sedans|Muscle|Motorcycles)\|/.test(s)).length >= 7, "the seven numbers in the index are tab stops, each named with its category");

  // reduced motion: scenes still change, nothing is hidden waiting for an animation
  await b.colorScheme(true);
  await b.open(BASE + "/about", 100);
  await b.eval(`localStorage.setItem("tv-motion", "0"); true`);      // motion is off for this visitor (the system asks for none; this test server also forces autoplay, so the stored choice is what turns it off)
  await b.open(BASE + "/vehicles?" + Q, 1500);
  await b.eval(`document.querySelector('[data-pick="shitzu-squalo"]').click(); true`);
  await b.sleep(1200);
  ok(await b.eval(`document.querySelector('[data-panel="shitzu-squalo"]').classList.contains("is-active") && getComputedStyle(document.querySelector('[data-panel="shitzu-squalo"] .gx-copy')).opacity === "1"`), "reduced motion: choosing a machine shows it, words included");
  ok(!(await b.eval(`document.documentElement.classList.contains("motion-on")`)), "reduced motion: the motion class is off");
  await b.eval(`window.scrollTo(0, 1700); true`); await b.sleep(500);
  ok(await b.eval(`getComputedStyle(document.querySelector(".gx-f__art")).opacity === "1" && getComputedStyle(document.querySelector(".gx-f__words h3")).opacity === "1"`), "reduced motion: the first chapter's picture and words are fully shown, not waiting to be revealed");
  await b.colorScheme(false);

  // no script: the first scene shows and the bays are plain links
  await b.send("Emulation.setScriptExecutionDisabled", { value: true });
  await b.open(BASE + "/vehicles?" + Q, 1500);
  const nojs = JSON.parse(await b.eval(`JSON.stringify({ visible: [...document.querySelectorAll("[data-panel]")].filter((p) => !p.hidden).length, ticks: [...document.querySelectorAll(".gx-tick")].filter((a) => /^\\/vehicles\\//.test(a.getAttribute("href"))).length, arrows: getComputedStyle(document.querySelector("[data-ctl]")).display })`).catch(() => "{}"));
  ok(nojs.visible === 1 && nojs.ticks === 7 && nojs.arrows === "none", "no script: one scene, seven index links, no dead arrows", JSON.stringify(nojs));
  await b.send("Emulation.setScriptExecutionDisabled", { value: false });

  ok(errors.length === 0, "no console errors or exceptions on any of these pages", errors.slice(0, 3).join(" | "));
  console.log(failed ? `\n${failed} FAILED` : "\nall passed");
  process.exitCode = failed ? 1 : 0;
}
