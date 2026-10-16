// Real-browser checks of the Garage: the opening lineup, the showroom controls, the vehicle showcase and its image viewer.
//   node scripts/qa/cdp.mjs scripts/qa/garage_interactions.mjs      (the app on 5057; GARAGE_BASE to change)
const BASE = process.env.GARAGE_BASE || "http://127.0.0.1:5057";
let failures = 0;
const check = (name, ok, detail = "") => { console.log((ok ? "PASS  " : "FAIL  ") + name + (detail ? "  (" + detail + ")" : "")); if (!ok) { failures++; } };

export default async function (b) {
  const ev = (js) => b.eval(js);
  const key = async (k, code, vk) => {
    await b.send("Input.dispatchKeyEvent", { type: "keyDown", key: k, code, windowsVirtualKeyCode: vk });
    await b.send("Input.dispatchKeyEvent", { type: "keyUp", key: k, code, windowsVirtualKeyCode: vk });
  };
  await b.send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  await b.open(BASE + "/about", 100);
  await ev(`localStorage.setItem("tv-motion", "1"); true`);

  // ---- the opening
  await b.open(BASE + "/vehicles", 1500);
  const state = `(() => ({ active: [...document.querySelectorAll("[data-panel]")].filter(p => p.classList.contains("is-active") && !p.hidden).map(p => p.dataset.panel),
    visible: [...document.querySelectorAll("[data-panel]")].filter(p => !p.hidden).map(p => p.dataset.panel), current: [...document.querySelectorAll("[data-pick]")].filter(a => a.getAttribute("aria-current") === "true").map(a => a.dataset.pick),
    live: document.querySelector("[data-stage-live]").textContent }))()`;
  let s = await ev(state);
  check("opening: the first machine is on show, alone", s.active.length === 1 && s.active[0] === "grotti-cheetah" && s.visible.length === 1, JSON.stringify(s));
  check("opening: five machines in the lineup", (await ev(`document.querySelectorAll("[data-pick]").length`)) === 5);
  await ev(`document.querySelector('[data-pick="shitzu-squalo"]').click(); true`);
  await b.sleep(1100);
  s = await ev(state);
  check("opening: clicking the lineup switches the machine", s.active[0] === "shitzu-squalo" && s.visible.length === 1 && s.current[0] === "shitzu-squalo", JSON.stringify(s));
  check("opening: the change is announced", /Shitzu Squalo/i.test(s.live), s.live);
  check("opening: the page did not navigate", (await ev(`location.pathname`)) === "/vehicles");
  check("opening: the new picture is loaded", await ev(`(() => { const i = document.querySelector('[data-panel="shitzu-squalo"] img'); return i.complete && i.naturalWidth > 0; })()`));
  await ev(`document.querySelector('[data-pick="shitzu-squalo"]').focus(); true`);
  await key("ArrowRight", "ArrowRight", 39);
  await b.sleep(900);
  s = await ev(state);
  check("opening: the right arrow moves to the next machine", s.active[0] === "vapid-stanier" && (await ev(`document.activeElement.dataset.pick`)) === "vapid-stanier", JSON.stringify(s));
  await key("End", "End", 35);
  await b.sleep(900);
  s = await ev(state);
  check("opening: End goes to the last machine", s.active[0] === "vapid-ganado", JSON.stringify(s));
  const stableY = await ev(`document.querySelector("[data-lineup]").getBoundingClientRect().top`);
  await ev(`document.querySelector('[data-pick="grotti-cheetah"]').click(); true`); await b.sleep(900);
  check("opening: switching does not move the lineup", Math.abs((await ev(`document.querySelector("[data-lineup]").getBoundingClientRect().top`)) - stableY) < 1);
  await b.sleep(4000);
  check("opening: nothing changes by itself", (await ev(state)).active[0] === "grotti-cheetah");
  check("opening: the call to action leads to the vehicle's page", (await ev(`document.querySelector('[data-panel="grotti-cheetah"] .gbtn').getAttribute("href")`)) === "/vehicles/grotti-cheetah");

  // ---- the showroom controls (they must really filter)
  const cards = `[...document.querySelectorAll(".gcard__name")].map(n => n.textContent.trim())`;
  await b.open(BASE + "/vehicles", 1200);
  check("showroom: five cards by default", (await ev(cards)).length === 5, (await ev(cards)).join(" | "));
  await b.open(BASE + "/vehicles?category=boat", 1000);
  check("showroom: a category shows only its vehicles", JSON.stringify(await ev(cards)) === JSON.stringify(["Shitzu Squalo"]), (await ev(cards)).join(" | "));
  check("showroom: the active category is marked", (await ev(`document.querySelector('.gcats a[aria-current="true"]').textContent.trim()`)).startsWith("Boats"));
  check("showroom: the result line says so", /1\s*machine\s*in\s*Boats/.test(await ev(`document.querySelector(".gresult").textContent.replace(/\\s+/g, " ")`)));
  await b.open(BASE + "/vehicles?q=vapid", 1000);
  check("showroom: search matches the maker", (await ev(cards)).length === 3, (await ev(cards)).join(" | "));
  await b.open(BASE + "/vehicles?q=vapid&sort=name_desc", 1000);
  check("showroom: sorting Z to A", JSON.stringify(await ev(cards)) === JSON.stringify(["Vapid Stanier", "Vapid Ganado Retro Build", "'67 Vapid Dominator Buggy"]), (await ev(cards)).join(" | "));
  const boatHref = await ev(`document.querySelector('.gcats a[href*="category=boat"]').getAttribute("href")`);
  check("showroom: a category link keeps the search and the sort", boatHref.includes("q=vapid") && boatHref.includes("sort=name_desc"), boatHref);
  await b.open(BASE + "/vehicles?q=zzzz", 1000);
  check("showroom: no match gives a clear empty state", (await ev(`!!document.querySelector(".gempty") && document.querySelectorAll(".gcard").length === 0`)) && /No machines/.test(await ev(`document.querySelector(".gresult").textContent`)));
  check("showroom: the empty state can be cleared", (await ev(`document.querySelector(".gempty .gbtn").getAttribute("href")`)).startsWith("/vehicles"));
  await b.open(BASE + "/vehicles", 1000);
  await ev(`const sel = document.querySelector("[data-autosubmit]"); sel.value = "name_asc"; sel.dispatchEvent(new Event("change", { bubbles: true })); true`);
  await b.sleep(1800);
  check("showroom: the sort menu applies by itself", (await ev(`location.search`)).includes("sort=name_asc") && (await ev(cards))[0] === "'67 Vapid Dominator Buggy", (await ev(`location.search`)));
  await ev(`document.querySelector(".gtools input[type=search]").value = "squalo"; document.querySelector(".gtools").requestSubmit(); true`);
  await b.sleep(1800);
  check("showroom: the search box submits", (await ev(cards)).join("|") === "Shitzu Squalo", (await ev(`location.search`)));

  // ---- a vehicle's showcase
  await b.open(BASE + "/vehicles/vapid-stanier", 1500);
  await ev(`document.querySelector("#showcase").scrollIntoView(); true`); await b.sleep(900);
  const view = `(() => ({ at: document.querySelector("[data-index]").textContent, active: [...document.querySelectorAll("[data-slide]")].filter(s => s.classList.contains("is-active") && !s.hidden).length, shown: [...document.querySelectorAll("[data-slide]")].filter(s => !s.hidden).length,
    caption: document.querySelector("[data-caption]").textContent, cur: [...document.querySelectorAll("[data-thumb]")].findIndex(t => t.getAttribute("aria-current") === "true") + 1 }))()`;
  let v = await ev(view);
  check("showcase: three pictures besides the opening one", (await ev(`document.querySelectorAll("[data-slide]").length`)) === 3 && v.at === "1" && v.active === 1, JSON.stringify(v));
  check("showcase: it never repeats the opening picture", await ev(`(() => { const hero = document.querySelector(".vhero img").currentSrc.split("?")[0]; return ![...document.querySelectorAll("[data-slide] img")].some(i => i.src.split("?")[0] === hero); })()`));
  await ev(`document.querySelector("[data-next]").click(); true`); await b.sleep(900);
  v = await ev(view);
  check("showcase: next moves to picture 2 and updates the caption", v.at === "2" && v.cur === 2 && v.active === 1 && v.shown === 1 && v.caption.length > 10, JSON.stringify(v));
  await ev(`document.querySelector("[data-prev]").click(); document.querySelector("[data-prev]").click(); true`); await b.sleep(900);
  v = await ev(view);
  check("showcase: previous wraps round to the last picture", v.at === "3" && v.cur === 3, JSON.stringify(v));
  await ev(`document.querySelectorAll("[data-thumb]")[1].click(); true`); await b.sleep(900);
  v = await ev(view);
  check("showcase: a thumbnail selects its picture", v.at === "2" && v.cur === 2, JSON.stringify(v));
  await ev(`document.querySelector("[data-next]").focus(); true`);
  await key("ArrowRight", "ArrowRight", 39);
  await b.sleep(800);
  check("showcase: the right arrow key advances", (await ev(view)).at === "3");
  await ev(`document.querySelector("[data-open]").click(); true`); await b.sleep(900);
  const lb = await ev(`(() => { const d = document.getElementById("image-dialog"); return { open: d.open, src: d.querySelector("[data-image]").src.split("?")[0].split("/").pop(), count: d.querySelector("[data-count]").textContent }; })()`);
  check("showcase: the large picture opens the full-size viewer at the same picture", lb.open && lb.count === "3 / 3" && lb.src.length > 5, JSON.stringify(lb));
  await key("ArrowLeft", "ArrowLeft", 37);
  await b.sleep(500);
  check("showcase: the full-size viewer moves with the arrow keys", (await ev(`document.getElementById("image-dialog").querySelector("[data-count]").textContent`)) === "2 / 3");
  await key("Escape", "Escape", 27);
  await b.sleep(500);
  check("showcase: Esc closes it", !(await ev(`document.getElementById("image-dialog").open`)));

  // ---- the vehicle with one picture, and every vehicle page
  await b.open(BASE + "/vehicles/vapid-ganado", 1200);
  check("one-picture vehicle: no viewer, an honest note instead", (await ev(`!document.querySelector("[data-viewer]") && !!document.querySelector(".showcase--none")`)) && /one official image/.test(await ev(`document.querySelector(".showcase--none").textContent`)));
  for (const slug of ["grotti-cheetah", "vapid-dominator-buggy", "shitzu-squalo", "vapid-stanier", "vapid-ganado"]) {
    await b.open(BASE + "/vehicles/" + slug, 900);
    await ev(`document.querySelectorAll("img").forEach(i => { i.loading = "eager"; }); true`); await b.sleep(3000);
    const bad = await ev(`[...document.images].filter(i => getComputedStyle(i).display !== "none" && !i.closest("[hidden]") && !i.closest("dialog") && (!i.complete || i.naturalWidth === 0)).length`);
    const more = await ev(`document.querySelectorAll(".gtile").length`);
    check("vehicle page " + slug + ": every shown picture loads, four others to explore", bad === 0 && more === 4, "broken " + bad + ", more " + more);
  }
  console.log(failures ? "\n" + failures + " FAILED" : "\nall passed");
  process.exitCode = failures ? 1 : 0;
}
