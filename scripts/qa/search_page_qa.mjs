// The /search page in a real browser. GET requests only.
//   TL_BASE=http://127.0.0.1:5059 node scripts/qa/cdp.mjs scripts/qa/search_page_qa.mjs        (exit status 1 on any failure)
// At every size: the help state, a results page, a no-match page and a hostile query draw without horizontal overflow, console, page or request errors; every control a keyboard
// reaches shows a focus indicator; result rows are tall enough to hit; a result link opens a page that exists. Once: submitting the form, the type chips and the pager land on the
// results below the fixed header, the hostile query is shown as text (nothing runs), and under reduced motion nothing animates.
//   QA_SIZES=1440x900,1024x768,768x1024,390x844,360x740,320x640   QA_REDUCE=1 emulates reduced motion.
const BASE = process.env.TL_BASE || "http://127.0.0.1:5059";
const SIZES = (process.env.QA_SIZES || "1440x900,1024x768,768x1024,390x844,360x740,320x640").split(",").map((s) => s.split("x").map(Number));
let failed = 0;
const report = (ok, label, detail = "") => { if (!ok) { failed++; } console.log((ok ? "PASS  " : "FAIL  ") + label + (detail !== "" ? "  (" + detail + ")" : "")); };

export default async function (b) {
  const problems = [];
  b.on((d) => {
    if (d.method === "Runtime.exceptionThrown") { problems.push("exception: " + (d.params.exceptionDetails.exception?.description || d.params.exceptionDetails.text)); }
    if (d.method === "Runtime.consoleAPICalled" && d.params.type === "error") { problems.push("console: " + (d.params.args || []).map((a) => a.value || a.description).join(" ")); }
    if (d.method === "Log.entryAdded" && d.params.entry.level === "error") { problems.push("log: " + d.params.entry.text); }
    if (d.method === "Network.loadingFailed" && !d.params.canceled) { problems.push("failed: " + d.params.errorText); }
  });
  await b.send("Network.enable"); await b.send("Log.enable");
  await b.colorScheme(process.env.QA_REDUCE === "1");
  const key = async (k, code, vk) => { await b.send("Input.dispatchKeyEvent", { type: "keyDown", key: k, code, windowsVirtualKeyCode: vk }); await b.send("Input.dispatchKeyEvent", { type: "keyUp", key: k, code, windowsVirtualKeyCode: vk }); };
  await b.open(BASE + "/about", 100);
  await b.eval(`localStorage.setItem("tv-motion", "1"); true`);
  const HOSTILE = `"><img src=x onerror="window.__xss=1"><script>window.__xss=2</script>`;
  const views = [["the help state", "/search"], ["a results page", "/search?q=vice"], ["a page of results", "/search?q=a&per_page=4&page=2"], ["no match", "/search?q=zzzzqqxx"], ["a hostile query", "/search?q=" + encodeURIComponent(HOSTILE)]];

  for (const [W, H] of SIZES) {
    await b.send("Emulation.setDeviceMetricsOverride", { width: W, height: H, deviceScaleFactor: 1, mobile: W < 700 });
    const tag = `${W}x${H}`;
    for (const [name, path] of views) {
      problems.length = 0;
      await b.open(BASE + path, 900);
      const over = await b.eval(`Math.max(document.documentElement.scrollWidth, document.body.scrollWidth) - window.innerWidth`);
      const h1 = await b.eval(`document.querySelectorAll("h1").length`);
      report(over <= 0 && h1 === 1 && problems.length === 0, `${tag}: ${name}: no overflow, one h1, no errors`, `overflow ${over}px, h1 ${h1}, ${problems.slice(0, 2).join(" | ")}`);
    }
    await b.open(BASE + "/search?q=vice", 900);
    const rows = JSON.parse(await b.eval(`JSON.stringify([...document.querySelectorAll(".hit")].map((a) => Math.round(a.getBoundingClientRect().height)))`));
    report(rows.length > 3 && rows.every((x) => x >= 44), `${tag}: result rows are at least 44 px tall`, `${rows.length} rows, shortest ${Math.min(...rows)} px`);
    const clip = await b.eval(`[...document.querySelectorAll(".hit__title, .hit__detail, .hit__summary")].filter((e) => e.scrollWidth > e.clientWidth + 1).length`);
    report(clip === 0, `${tag}: no result text is cut off sideways`, clip + " elements");
  }

  // ---------------------------------------------------------------- desktop, once
  await b.send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  problems.length = 0;
  await b.open(BASE + "/search?q=a&per_page=3", 900);
  // keyboard: every stop shows a focus indicator
  const stops = [];
  for (let i = 0; i < 40; i++) {
    await key("Tab", "Tab", 9);
    const r = JSON.parse(await b.eval(`JSON.stringify((() => { const e = document.activeElement; if (!e || e === document.body) return null; const s = getComputedStyle(e); const r = e.getBoundingClientRect(); return { name: (e.getAttribute("aria-label") || e.textContent || e.className).trim().replace(/\\s+/g, " ").slice(0, 26), vis: r.width > 0 && r.height > 0, ring: (s.outlineStyle !== "none" && parseFloat(s.outlineWidth) > 0) || (s.boxShadow && s.boxShadow !== "none") || s.textDecorationLine.includes("underline") }; })())`));
    if (r) { stops.push(r); }
  }
  const bad = stops.filter((s) => s.vis && !s.ring);
  report(stops.length >= 15 && bad.length === 0, "keyboard: every stop on the results page shows a focus indicator", `${stops.length} stops, without: ${bad.map((s) => s.name).slice(0, 4).join(", ")}`);

  // landing on the results, under the fixed header
  await b.open(BASE + "/search", 700);
  await b.eval(`document.querySelector('input[name=q]').value = "vice"; document.querySelector('.search-form button').click(); true`);
  await b.sleep(1200);
  const landed = JSON.parse(await b.eval(`JSON.stringify({ where: location.pathname + location.search + location.hash, top: Math.round(document.getElementById("results").getBoundingClientRect().top), header: Math.round(document.querySelector("[data-header]").getBoundingClientRect().height) })`));
  report(landed.where === "/search?q=vice#results" && landed.top >= landed.header, "submitting the form lands on the results, below the header", JSON.stringify(landed));
  await b.eval(`document.querySelector('.chips a[href*="type=place"]').click(); true`); await b.sleep(1200);
  const chip = JSON.parse(await b.eval(`JSON.stringify({ where: location.search + location.hash, current: document.querySelector('.chips [aria-current]').textContent.trim(), kinds: [...new Set([...document.querySelectorAll(".hit__kind")].map((e) => e.textContent))] })`));
  report(chip.where === "?q=vice&type=place#results" && /^Place/.test(chip.current) && chip.kinds.join() === "Place", "a type chip lands on the results and filters to that kind", JSON.stringify(chip));
  await b.open(BASE + "/search?q=a&per_page=3#results", 900);
  await b.eval(`document.querySelector('.pager a[rel=next]').click(); true`); await b.sleep(1200);
  const pg = JSON.parse(await b.eval(`JSON.stringify({ where: location.search + location.hash, status: document.querySelector('#results [role=status]').textContent.trim().slice(0, 14), top: Math.round(document.getElementById("results").getBoundingClientRect().top) })`));
  report(/page=2#results$/.test(pg.where) && /^4.6 of/.test(pg.status.replace(/–/g, "-")), "the pager's next link lands on the next page of results", JSON.stringify(pg));

  // a result opens a real page
  await b.open(BASE + "/search?q=cheetah", 800);
  await b.eval(`document.querySelector(".hit").click(); true`); await b.sleep(1200);
  report((await b.eval("location.pathname")) === "/vehicles/grotti-cheetah" && (await b.eval(`document.querySelectorAll("h1").length`)) === 1, "a result opens its page", await b.eval("location.pathname"));

  // hostile text is only text
  await b.open(BASE + "/search?q=" + encodeURIComponent(HOSTILE), 900);
  const x = JSON.parse(await b.eval(`JSON.stringify({ ran: window.__xss !== undefined, imgs: document.querySelectorAll("main img[src=x], main script").length, boxHasText: document.querySelector('input[name=q]').value === ${JSON.stringify(HOSTILE)} })`));
  report(!x.ran && x.imgs === 0 && x.boxHasText, "a hostile query is shown in the box as text and runs nothing", JSON.stringify(x));

  // reduced motion
  await b.colorScheme(true);
  await b.eval(`localStorage.removeItem("tv-motion"); true`);
  await b.open(BASE + "/search?q=vice", 1500);
  report(await b.eval(`document.getAnimations().filter((a) => a.playState === "running").length === 0`), "with reduced motion nothing animates on the page");
  report(problems.length === 0, "no console, page, request or CSP errors in the desktop run", problems.slice(0, 3).join(" | "));
  if (failed) { console.log(`\n${failed} check(s) failed`); process.exitCode = 1; } else { console.log("\nall checks passed"); }
}
