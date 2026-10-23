// Command palette (Ctrl/Cmd+K) and the header search icon, in a real browser. Read-only: GET requests only (it never submits a form).
//   TL_BASE=http://127.0.0.1:5059 node scripts/qa/cdp.mjs scripts/qa/palette_qa.mjs        (exit status 1 on any failure)
// Per size: the icon is there and large enough, nothing overflows, no console/page/request/CSP errors. At desktop: Ctrl+K and "/" open it with the field focused (and "/" does
// not while typing in a field), Esc closes it and puts focus back, Tab stays inside, results appear with the combobox/listbox attributes right, arrows move the active option,
// Enter opens it, ">" lists commands and the motion command works, hostile text is shown as text, "no results" falls back to the search page, a click on the backdrop closes it,
// reduced motion plays nothing, and without JavaScript the icon is a plain link. Measures: open-to-first-frame, and a keystroke to painted results.
//   QA_SIZES=1440x900,1024x768,768x1024,390x844,360x740,320x640   QA_REDUCE=1 emulates reduced motion.
const BASE = process.env.TL_BASE || "http://127.0.0.1:5059";
const SIZES = (process.env.QA_SIZES || "1440x900,1024x768,768x1024,390x844,360x740,320x640").split(",").map((s) => s.split("x").map(Number));
let failed = 0;
const report = (ok, label, detail = "") => { if (!ok) { failed++; } console.log((ok ? "PASS  " : "FAIL  ") + label + (detail !== "" ? "  (" + detail + ")" : "")); };
const info = (label) => console.log("INFO  " + label);

export default async function (b) {
  const problems = [];
  b.on((d) => {
    if (d.method === "Runtime.exceptionThrown") { problems.push("exception: " + (d.params.exceptionDetails.exception?.description || d.params.exceptionDetails.text)); }
    if (d.method === "Runtime.consoleAPICalled" && d.params.type === "error") { problems.push("console: " + (d.params.args || []).map((a) => a.value || a.description).join(" ")); }
    if (d.method === "Log.entryAdded" && d.params.entry.level === "error") { problems.push("log: " + d.params.entry.text + " " + (d.params.entry.url || "")); }
    if (d.method === "Network.loadingFailed" && !d.params.canceled) { problems.push("failed: " + d.params.errorText + " " + (d.params.type || "")); }
  });
  await b.send("Network.enable"); await b.send("Log.enable");
  await b.colorScheme(process.env.QA_REDUCE === "1");
  const key = async (k, code, vk, extra = {}) => { await b.send("Input.dispatchKeyEvent", { type: "keyDown", key: k, code, windowsVirtualKeyCode: vk, ...extra }); await b.send("Input.dispatchKeyEvent", { type: "keyUp", key: k, code, windowsVirtualKeyCode: vk, ...extra }); };
  const ctrlK = () => key("k", "KeyK", 75, { modifiers: 2 });
  const metaK = () => key("k", "KeyK", 75, { modifiers: 4 });
  const type = async (text) => { await b.send("Input.insertText", { text }); };
  const state = async () => JSON.parse(await b.eval(`JSON.stringify((() => { const d = document.getElementById("palette"), i = d.querySelector("[data-palette-input]"); const opts = [...d.querySelectorAll('[role=option]')];
    return { open: d.open, focusOnInput: document.activeElement === i, options: opts.length, selected: opts.filter((o) => o.getAttribute("aria-selected") === "true").length, active: i.getAttribute("aria-activedescendant"),
      activeIsSelected: !!opts.find((o) => o.id === i.getAttribute("aria-activedescendant") && o.getAttribute("aria-selected") === "true"), expanded: i.getAttribute("aria-expanded"), titles: opts.map((o) => o.textContent.trim().replace(/\\s+/g, " ")).slice(0, 8), where: location.pathname + location.hash,
      status: d.querySelector("[data-palette-status]").textContent, insideDialog: d.contains(document.activeElement), notes: [...d.querySelectorAll(".palette__note")].map((n) => n.textContent) }; })())`));
  const waitFor = async (cond, ms = 3000) => { const end = Date.now() + ms; while (Date.now() < end) { if (await b.eval(cond)) { return true; } await b.sleep(40); } return false; };
  // real results, not the quick links the palette already lists when it opens
  const results = () => waitFor(`(document.querySelectorAll('#palette [role=option]').length > 0 && !document.querySelector('#palette .palette__item--command')) || !!document.querySelector('#palette .palette__note')`);

  await b.open(BASE + "/about", 100);
  await b.eval(`localStorage.setItem("tv-motion", "1"); true`);

  for (const [W, H] of SIZES) {
    await b.send("Emulation.setDeviceMetricsOverride", { width: W, height: H, deviceScaleFactor: 1, mobile: W < 700 });
    problems.length = 0;
    const tag = `${W}x${H}`;
    await b.open(BASE + "/characters", 1200);
    const icon = JSON.parse(await b.eval(`JSON.stringify((() => { const a = document.querySelector("[data-palette-open]"); const r = a.getBoundingClientRect(), s = getComputedStyle(a); return { shown: s.display !== "none" && r.width > 0, w: Math.round(r.width), h: Math.round(r.height), label: a.getAttribute("aria-label"), href: a.getAttribute("href"), keys: a.getAttribute("aria-keyshortcuts"), onScreen: r.left >= 0 && r.right <= innerWidth }; })())`));
    if (W < 360) { report(!icon.shown, `${tag}: the icon steps aside on the narrowest phones (the site menu has a Search row)`); }
    else { report(icon.shown && icon.w >= 24 && icon.h >= 24 && icon.onScreen && icon.label === "Search" && icon.href === "/search" && /Control\+K/.test(icon.keys), `${tag}: the Search icon is visible, on screen, at least 24 px, named, a link to /search, and says its shortcut`, JSON.stringify(icon)); }
    const over = await b.eval(`Math.max(document.documentElement.scrollWidth, document.body.scrollWidth) - window.innerWidth`);
    report(over <= 0, `${tag}: no horizontal overflow`, over + "px");
    if (W >= 360) {
      const clash = await b.eval(`(() => { const a = document.querySelector(".header-search").getBoundingClientRect(); return [...document.querySelectorAll(".header-inner > .brand, .header-nav a, .header-pill, .menu-btn")].filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && !(r.right <= a.left || r.left >= a.right || r.bottom <= a.top || r.top >= a.bottom); }).map((e) => e.className || e.textContent.trim()).join(","); })()`);
      report(clash === "", `${tag}: the icon overlaps nothing in the header`, clash);
    }
    await b.eval(`document.querySelector("[data-palette-open]").click(); true`);
    await b.sleep(200);
    let s = await state();
    if (W >= 360) {
      report(s.open && s.focusOnInput, `${tag}: clicking the icon opens the palette with the field focused`, JSON.stringify({ open: s.open, focus: s.focusOnInput }));
      const fit = JSON.parse(await b.eval(`JSON.stringify((() => { const d = document.getElementById("palette"), r = d.getBoundingClientRect(); return { left: Math.round(r.left), right: Math.round(r.right), top: Math.round(r.top), bottom: Math.round(r.bottom), scrollOver: d.scrollWidth - d.clientWidth, vw: innerWidth, vh: innerHeight }; })())`));
      report(fit.left >= 0 && fit.right <= fit.vw && fit.bottom <= fit.vh + 1 && fit.scrollOver <= 0, `${tag}: the palette fits the screen with nothing sideways`, JSON.stringify(fit));
      if (W < 700 && process.env.QA_OUT) { await b.shot(`${process.env.QA_OUT}/palette_${tag}.jpg`).catch(() => {}); }
      await key("Escape", "Escape", 27); await b.sleep(150);
    }
    report(problems.length === 0, `${tag}: no console, page, request or CSP errors`, problems.slice(0, 3).join(" | "));
  }

  // ---------------------------------------------------------------- desktop behaviour
  await b.send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  problems.length = 0;
  await b.open(BASE + "/characters", 1200);

  // opening, the shortcuts, and where focus goes
  await b.eval(`document.querySelector(".header-nav li:nth-child(2) a").focus(); window.__origin = document.activeElement.getAttribute("href"); true`);
  await ctrlK(); await b.sleep(150);
  let s = await state();
  report(s.open && s.focusOnInput, "Ctrl+K opens the palette with the field focused");
  report(s.options >= 5 && s.expanded === "true" && s.titles[0].startsWith("Go to"), "the opening state offers quick links to the main pages", s.titles.slice(0, 3).join(" | "));
  await key("Escape", "Escape", 27); await b.sleep(200);
  s = await state();
  const back = await b.eval(`document.activeElement.getAttribute("href") === window.__origin`);
  report(!s.open && back, "Esc closes it and focus goes back to the link it came from");
  await metaK(); await b.sleep(150);
  report((await state()).open, "Cmd+K (Meta) opens it too");
  await metaK(); await b.sleep(150);
  report(!(await state()).open, "the same shortcut closes it again");
  await b.eval(`document.body.focus(); true`);
  await key("/", "Slash", 191, { text: "/" }); await b.sleep(150);
  s = await state();
  report(s.open && s.focusOnInput, "/ opens it when you are not typing");
  report(await b.eval(`document.querySelector("#palette [data-palette-input]").value === ""`), "...and the slash itself is not typed into the field");
  await key("Escape", "Escape", 27); await b.sleep(150);
  await b.open(BASE + "/missions", 900);
  await b.eval(`document.querySelector('.filters input[type=search]').focus(); true`);
  await key("/", "Slash", 191, { text: "/" }); await b.sleep(150);
  report(!(await state()).open && await b.eval(`document.querySelector('.filters input[type=search]').value === "/"`), "/ does not open it while typing in a field (the slash is typed)");
  await b.eval(`document.querySelector('.filters input[type=search]').value = ""; document.activeElement.blur(); true`);
  await b.open(BASE + "/characters", 900);

  // focus stays inside while it is open
  await ctrlK(); await b.sleep(120);
  let inside = true;
  const contained = () => b.eval(`(() => { const a = document.activeElement; return document.getElementById("palette").contains(a) || a === document.body || a === document.documentElement; })()`);
  for (let i = 0; i < 6; i++) { await key("Tab", "Tab", 9); inside = inside && await contained(); }
  for (let i = 0; i < 3; i++) { await key("Tab", "Tab", 9, { modifiers: 8 }); inside = inside && await contained(); }
  report(inside, "Tab and Shift+Tab never reach the page behind it (focus stays in the palette, or goes up to the browser as for any modal dialog)");
  await key("Escape", "Escape", 27); await b.sleep(150);

  // searching
  await ctrlK(); await b.sleep(120);
  const t0 = Date.now();
  await type("jason"); const got = await results(); const tEnd = Date.now() - t0; await b.sleep(150);
  s = await state();
  report(got && s.titles.some((t) => t.startsWith("Character Jason Duval")), "typing a name finds the person", s.titles.slice(0, 3).join(" | "));
  report(s.options <= 8 && s.selected === 1 && s.activeIsSelected && s.expanded === "true", "at most eight results; exactly one active, and aria-activedescendant points at it", `options ${s.options}, selected ${s.selected}`);
  report(/results?\./.test(s.status) || /result/.test(s.status), "the count is announced in the live region", s.status);
  const roles = JSON.parse(await b.eval(`JSON.stringify((() => { const d = document.getElementById("palette"), i = d.querySelector("[data-palette-input]"), l = d.querySelector("[data-palette-list]"); return { combobox: i.getAttribute("role"), controls: i.getAttribute("aria-controls") === l.id, listbox: l.getAttribute("role"), named: !!d.getAttribute("aria-label") && !!i.getAttribute("aria-label"), autocomplete: i.getAttribute("aria-autocomplete") }; })())`));
  report(roles.combobox === "combobox" && roles.controls && roles.listbox === "listbox" && roles.named && roles.autocomplete === "list", "the combobox, listbox, names and aria-controls are right", JSON.stringify(roles));
  info(`typing 'jason' to results painted: ${tEnd} ms from the first character (includes the 120 ms pause that waits for you to stop typing)`);
  const first = s.active;
  await key("ArrowDown", "ArrowDown", 40); await b.sleep(80);
  s = await state(); report(s.active !== first && s.selected === 1 && s.activeIsSelected, "ArrowDown moves the active option", `${first} -> ${s.active}`);
  await key("ArrowUp", "ArrowUp", 38); await b.sleep(80);
  s = await state(); report(s.active === first, "ArrowUp moves it back");
  await key("ArrowUp", "ArrowUp", 38); await b.sleep(80);
  s = await state(); report(s.active === `palette-option-${s.options - 1}`, "ArrowUp from the first wraps to the last");
  report(await b.eval(`[...document.querySelectorAll("#palette .palette__link")].every((a) => a.getBoundingClientRect().height >= 44)`), "every result row is at least 44 px tall");
  // Enter opens the active result
  await b.eval(`document.querySelector("#palette [data-palette-input]").value = ""; true`);
  await b.eval(`(() => { const i = document.querySelector("#palette [data-palette-input]"); i.dispatchEvent(new Event("input", { bubbles: true })); return true; })()`);
  await type("cheetah"); await results(); await b.sleep(80);
  await key("Enter", "Enter", 13); await b.sleep(1200);
  report((await b.eval("location.pathname")) === "/vehicles/grotti-cheetah", "Enter opens the best match", await b.eval("location.pathname"));

  // commands
  await b.open(BASE + "/characters", 900);
  await ctrlK(); await b.sleep(120);
  await type(">"); await b.sleep(150);
  s = await state();
  const names = JSON.parse(await b.eval(`JSON.stringify([...document.querySelectorAll("#palette [role=option]")].map((o) => o.textContent.trim().replace(/\\s+/g, " ")))`));
  report(names.length >= 10 && names.some((n) => /motion and footage/i.test(n)), "> lists the commands, including the motion switch", `${names.length} commands`);
  report(names.every((n) => /^Command (Go to|Open the full search|Turn motion)/.test(n)) && !names.some((n) => /sign out|log out|delete|admin/i.test(n)), "only navigation and the motion switch are offered, nothing that changes an account or data", names.join(" | "));
  await type("garage"); await b.sleep(120);
  s = await state(); report(s.options === 1 && /Go to Garage/.test(s.titles[0]), "typing after > filters the commands", s.titles.join(" | "));
  await key("Backspace", "Backspace", 8); await b.send("Input.dispatchKeyEvent", { type: "keyUp", key: "Backspace", code: "Backspace", windowsVirtualKeyCode: 8 });
  await b.eval(`(() => { const i = document.querySelector("#palette [data-palette-input]"); i.value = ">motion"; i.dispatchEvent(new Event("input", { bubbles: true })); return true; })()`); await b.sleep(120);
  const before = await b.eval(`JSON.stringify({ store: localStorage.getItem("tv-motion"), on: document.documentElement.classList.contains("motion-on") })`);
  await key("Enter", "Enter", 13); await b.sleep(300);
  const after = await b.eval(`JSON.stringify({ store: localStorage.getItem("tv-motion"), on: document.documentElement.classList.contains("motion-on"), live: [...document.querySelectorAll('[role=status]')].map((e) => e.textContent).join("|") })`);
  const B = JSON.parse(before), A = JSON.parse(after);
  report(!(await state()).open && A.store !== B.store && A.on !== B.on, "the motion command flips the site's own switch and closes", `${before} -> ${after}`);
  report(/Motion and footage are now (on|off)/.test(A.live), "...and says the new state in a live region that outlives the dialog", A.live);
  await b.eval(`localStorage.setItem("tv-motion", "1"); true`);

  // hostile text, no results, backdrop
  await b.open(BASE + "/characters", 900);
  await ctrlK(); await b.sleep(120);
  await type(`<img src=x onerror="window.__xss=1"> <script>window.__xss=2</script>`); await b.sleep(900);
  const xss = JSON.parse(await b.eval(`JSON.stringify({ flag: window.__xss === undefined, imgs: document.querySelectorAll("#palette img, #palette script").length })`));
  report(xss.flag && xss.imgs === 0, "hostile text typed in runs nothing and creates no elements", JSON.stringify(xss));
  await b.eval(`(() => { const i = document.querySelector("#palette [data-palette-input]"); i.value = "zzzzqqxx"; i.dispatchEvent(new Event("input", { bubbles: true })); return true; })()`); await b.sleep(900);
  s = await state();
  report(s.options === 0 && s.notes.some((n) => /Nothing found/.test(n)) && /No results/.test(s.status), "no match says so in the list and in the live region", JSON.stringify(s.notes));
  await key("Enter", "Enter", 13); await b.sleep(1200);
  report((await b.eval("location.pathname + location.search")) === "/search?q=zzzzqqxx", "Enter with no match goes to the search page with the query", await b.eval("location.pathname + location.search"));
  await b.open(BASE + "/characters", 900);
  await ctrlK(); await b.sleep(120);
  await b.send("Input.dispatchMouseEvent", { type: "mousePressed", x: 20, y: 880, button: "left", clickCount: 1 }); await b.send("Input.dispatchMouseEvent", { type: "mouseReleased", x: 20, y: 880, button: "left", clickCount: 1 }); await b.sleep(200);
  report(!(await state()).open, "a click on the backdrop closes it");
  await ctrlK(); await b.sleep(100);
  await b.eval(`document.querySelector("#palette [data-palette-close]").click(); true`); await b.sleep(150);
  report(!(await state()).open, "the Close button closes it");

  // another dialog open: the shortcuts keep out of its way
  await b.eval(`document.getElementById("image-dialog").showModal(); true`);
  await ctrlK(); await b.sleep(120);
  report(!(await state()).open, "with the site's image viewer open, Ctrl+K leaves it alone");
  await b.eval(`document.getElementById("image-dialog").close(); true`);

  // timing
  const open = [];
  for (let i = 0; i < 8; i++) {
    open.push(await b.eval(`(async () => { const d = document.getElementById("palette"), t = performance.now(); document.dispatchEvent(new KeyboardEvent("keydown", { key: "k", ctrlKey: true, bubbles: true })); const focused = document.activeElement === d.querySelector("[data-palette-input]");
      await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r))); const ms = performance.now() - t; d.close(); await new Promise((r) => setTimeout(r, 30)); return focused ? ms : -1; })()`));
  }
  open.sort((x, y) => x - y);
  report(open[0] > 0 && open[Math.floor(open.length * 0.75)] <= 100, "open to first painted frame is within 100 ms", `median ${open[Math.floor(open.length / 2)].toFixed(1)} ms, worst ${open[open.length - 1].toFixed(1)} ms of ${open.length}`);
  const typed = [];
  for (const q of ["j", "ja", "jason", "vice", "neon", "radio", "garage", "harbour"]) {
    typed.push(JSON.parse(await b.eval(`(async () => { const d = document.getElementById("palette"), i = d.querySelector("[data-palette-input]"); document.dispatchEvent(new KeyboardEvent("keydown", { key: "k", ctrlKey: true, bubbles: true }));
      const list = d.querySelector("[data-palette-list]"); let painted = 0, fetchDone = 0;
      const seen = new Promise((res) => { const mo = new MutationObserver(() => { if (list.querySelector("[role=option]") && list.dataset.q !== "1") { mo.disconnect(); requestAnimationFrame(() => { painted = performance.now(); res(); }); } }); mo.observe(list, { childList: true }); });
      performance.clearResourceTimings(); list.textContent = ""; const t = performance.now(); i.value = ${JSON.stringify(q)}; i.dispatchEvent(new Event("input", { bubbles: true })); await seen;
      const entry = performance.getEntriesByType("resource").filter((e) => e.name.includes("/api/v1/search")).pop(); const responseEnd = entry ? entry.responseEnd : 0;
      d.close(); await new Promise((r) => setTimeout(r, 40)); return JSON.stringify({ total: painted - t, afterResponse: responseEnd ? painted - responseEnd : null }); })()`)));
  }
  const totals = typed.map((x) => x.total).sort((x, y) => x - y), answered = typed.map((x) => x.afterResponse).filter((x) => x !== null).sort((x, y) => x - y);
  info(`keystroke to painted results, total (includes the 120 ms pause): median ${totals[Math.floor(totals.length / 2)].toFixed(0)} ms, worst ${totals[totals.length - 1].toFixed(0)} ms`);
  report(answered.length > 0 && answered[answered.length - 1] <= 150, "from the server's answer to painted results is within 150 ms", `median ${answered[Math.floor(answered.length / 2)]?.toFixed(1)} ms, worst ${answered[answered.length - 1]?.toFixed(1)} ms`);

  // reduced motion and no JavaScript
  await b.colorScheme(true);
  await b.eval(`localStorage.removeItem("tv-motion"); true`);
  await b.open(BASE + "/characters", 900);
  await ctrlK(); await b.sleep(250);
  report(await b.eval(`document.getElementById("palette").getAnimations().length === 0 && !document.documentElement.classList.contains("motion-on")`), "with reduced motion nothing animates when it opens");
  await key("Escape", "Escape", 27);
  await b.colorScheme(false); await b.eval(`localStorage.setItem("tv-motion", "1"); true`);
  await b.send("Emulation.setScriptExecutionDisabled", { value: true });
  await b.open(BASE + "/characters", 600);
  report(await b.eval(`document.querySelector("[data-palette-open]").getAttribute("href") === "/search"`), "without JavaScript the icon is a plain link to /search");
  await b.send("Emulation.setScriptExecutionDisabled", { value: false });
  report(problems.length === 0, "no console, page, request or CSP errors in the desktop run", problems.slice(0, 3).join(" | "));
  if (failed) { console.log(`\n${failed} check(s) failed`); process.exitCode = 1; } else { console.log("\nall checks passed"); }
}
