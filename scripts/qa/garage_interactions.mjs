// Real-browser checks of the Garage: the opening and its controller, the collection's controls, the showcase viewer and the other
// ways each vehicle's pictures are set.
//   node scripts/qa/cdp.mjs scripts/qa/garage_interactions.mjs      (the app on 5057; GARAGE_BASE to change)
const BASE = process.env.GARAGE_BASE || "http://127.0.0.1:5057";
let failures = 0;
const check = (name, ok, detail = "") => { console.log((ok ? "PASS  " : "FAIL  ") + name + (detail ? "  (" + detail + ")" : "")); if (!ok) { failures++; } };
const ALL = ["grotti-cheetah", "vapid-dominator-buggy", "shitzu-squalo", "vapid-stanier", "vapid-ganado", "dinka-enduro", "crest-kayak"];

export default async function (b) {
  const ev = (js) => b.eval(js);
  const key = async (k, code, vk) => {
    await b.send("Input.dispatchKeyEvent", { type: "keyDown", key: k, code, windowsVirtualKeyCode: vk });
    await b.send("Input.dispatchKeyEvent", { type: "keyUp", key: k, code, windowsVirtualKeyCode: vk });
  };
  await b.colorScheme(false);
  await b.send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  await b.open(BASE + "/about", 100);
  await ev(`localStorage.setItem("tv-motion", "1"); true`);

  // ---- the opening
  await b.open(BASE + "/vehicles", 1500);
  const state = `(() => ({ active: [...document.querySelectorAll("[data-panel]")].filter(p => p.classList.contains("is-active") && !p.hidden).map(p => p.dataset.panel),
    visible: [...document.querySelectorAll("[data-panel]")].filter(p => !p.hidden).map(p => p.dataset.panel), current: [...document.querySelectorAll("[data-pick]")].filter(a => a.getAttribute("aria-current") === "true").map(a => a.dataset.pick),
    live: document.querySelector("[data-stage-live]").textContent, count: document.querySelector("[data-count]").textContent, tint: document.querySelector("[data-stage]").dataset.vehicle }))()`;
  let s = await ev(state);
  check("opening: the first machine is on show, alone", s.active.length === 1 && s.active[0] === "grotti-cheetah" && s.visible.length === 1, JSON.stringify(s));
  check("opening: seven machines in the lineup", (await ev(`document.querySelectorAll("[data-pick]").length`)) === 7);
  check("opening: the arrows are shown now that script runs", await ev(`!document.querySelector("[data-ctl]").hidden && getComputedStyle(document.querySelector("[data-ctl]")).display !== "none"`));
  await ev(`document.querySelector('[data-pick="shitzu-squalo"]').click(); true`);
  await b.sleep(1200);
  s = await ev(state);
  check("opening: choosing from the lineup switches the machine", s.active[0] === "shitzu-squalo" && s.visible.length === 1 && s.current[0] === "shitzu-squalo", JSON.stringify(s));
  check("opening: the counter, the tint and the announcement follow", s.count === "03" && s.tint === "shitzu-squalo" && /Squalo/i.test(s.live), JSON.stringify(s));
  check("opening: the page did not navigate", (await ev(`location.pathname`)) === "/vehicles");
  check("opening: the new picture is loaded and decoded", await ev(`(() => { const i = document.querySelector('[data-panel="shitzu-squalo"] img'); return i.complete && i.naturalWidth > 0; })()`));
  await ev(`document.querySelector('[data-step="1"]').click(); true`); await b.sleep(1100);
  check("opening: the next arrow moves on", (await ev(state)).active[0] === "vapid-stanier");
  await ev(`document.querySelector('[data-step="-1"]').click(); document.querySelector('[data-step="-1"]').click(); true`); await b.sleep(1300);
  check("opening: the previous arrow moves back, quick clicks included", (await ev(state)).active[0] === "vapid-dominator-buggy", JSON.stringify(await ev(state)));
  await ev(`document.querySelector('[data-pick="shitzu-squalo"]').focus(); true`);
  await key("ArrowRight", "ArrowRight", 39); await b.sleep(1000);
  s = await ev(state);
  check("opening: the right arrow key moves to the next machine", s.active[0] === "vapid-stanier" && (await ev(`document.activeElement.dataset.pick`)) === "vapid-stanier", JSON.stringify(s));
  await key("End", "End", 35); await b.sleep(1000);
  check("opening: End goes to the last machine", (await ev(state)).active[0] === "crest-kayak");
  await key("Home", "Home", 36); await b.sleep(1000);
  check("opening: Home goes back to the first", (await ev(state)).active[0] === "grotti-cheetah");
  const stableY = await ev(`document.querySelector("[data-lineup]").getBoundingClientRect().top`);
  await ev(`document.querySelector('[data-pick]:not([aria-current])').click(); true`); await b.sleep(1000);
  check("opening: switching does not move the lineup", Math.abs((await ev(`document.querySelector("[data-lineup]").getBoundingClientRect().top`)) - stableY) < 1);
  await ev(`document.querySelector('[data-pick="grotti-cheetah"]').click(); true`); await b.sleep(4500);
  check("opening: nothing changes by itself", (await ev(state)).active[0] === "grotti-cheetah");
  check("opening: the action leads to the vehicle's page", (await ev(`document.querySelector('[data-panel="grotti-cheetah"] .gbtn').getAttribute("href")`)) === "/vehicles/grotti-cheetah");
  // a swipe on a touch screen
  await b.send("Emulation.setDeviceMetricsOverride", { width: 390, height: 844, deviceScaleFactor: 1, mobile: true });
  await b.open(BASE + "/vehicles", 1500);
  await ev(`(() => { const t = document.querySelector(".cine__panels"); const r = t.getBoundingClientRect(); const mk = (type, x) => t.dispatchEvent(new PointerEvent(type, { pointerType: "touch", clientX: x, clientY: r.top + 100, bubbles: true })); mk("pointerdown", 300); mk("pointerup", 120); return true; })()`);
  await b.sleep(1300);
  check("opening (phone): a swipe to the left moves to the next machine", (await ev(state)).active[0] === "vapid-dominator-buggy", JSON.stringify(await ev(state)));
  await b.send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });

  // ---- the collection's controls (they must really filter)
  const tiles = `[...document.querySelectorAll(".tile__model")].map(n => n.textContent.trim())`;
  await b.open(BASE + "/vehicles", 1200);
  check("collection: seven tiles by default", (await ev(tiles)).length === 7, (await ev(tiles)).join(" | "));
  await b.open(BASE + "/vehicles?category=boat", 1000);
  check("collection: a category shows only its vehicles", JSON.stringify(await ev(tiles)) === JSON.stringify(["Squalo", "Kayak"]), (await ev(tiles)).join(" | "));
  check("collection: the active category is marked", (await ev(`document.querySelector('.ctl__cats a[aria-current="true"]').textContent.trim()`)).startsWith("Boats"));
  check("collection: the result line appears and says so", /2\s*machines\s*in\s*Boats/.test(await ev(`document.querySelector(".gresult").textContent.replace(/\\s+/g, " ")`)) && (await ev(`!document.querySelector(".gresult").hidden`)));
  await b.open(BASE + "/vehicles?q=vapid", 1000);
  check("collection: search matches the maker", (await ev(tiles)).length === 3, (await ev(tiles)).join(" | "));
  await b.open(BASE + "/vehicles?q=vapid&sort=name_desc", 1000);
  check("collection: sorting Z to A", JSON.stringify(await ev(tiles)) === JSON.stringify(["Stanier", "Ganado Retro Build", "Dominator Buggy"]), (await ev(tiles)).join(" | "));
  const boatHref = await ev(`document.querySelector('.ctl__cats a[href*="category=boat"]').getAttribute("href")`);
  check("collection: a category link keeps the search and the sort", boatHref.includes("q=vapid") && boatHref.includes("sort=name_desc"), boatHref);
  await b.open(BASE + "/vehicles?q=zzzz", 1000);
  check("collection: no match gives a clear empty state", (await ev(`!!document.querySelector(".gempty") && document.querySelectorAll(".tile").length === 0`)));
  check("collection: the empty state can be cleared", (await ev(`document.querySelector(".gempty .gbtn").getAttribute("href")`)).startsWith("/vehicles"));
  await b.open(BASE + "/vehicles", 1000);
  await ev(`const sel = document.querySelector("[data-autosubmit]"); sel.value = "name_desc"; sel.dispatchEvent(new Event("change", { bubbles: true })); true`);
  await b.sleep(1800);
  check("collection: the sort menu applies by itself", (await ev(`location.search`)).includes("sort=name_desc") && (await ev(tiles))[0] === "Stanier", (await ev(`location.search`)) + " " + (await ev(tiles))[0]);
  await ev(`document.querySelector(".ctl input[type=search]").value = "squalo"; document.querySelector(".ctl__form").requestSubmit(); true`);
  await b.sleep(1800);
  check("collection: the search box submits", (await ev(tiles)).join("|") === "Squalo", (await ev(`location.search`)));

  // ---- the viewer (the Dominator Buggy is set as a viewer)
  await b.open(BASE + "/vehicles/vapid-dominator-buggy", 1500);
  await ev(`document.querySelector("[data-viewer]").scrollIntoView(); true`); await b.sleep(900);
  const view = `(() => ({ at: document.querySelector("[data-index]").textContent, active: [...document.querySelectorAll("[data-slide]")].filter(s => s.classList.contains("is-active") && !s.hidden).length, shown: [...document.querySelectorAll("[data-slide]")].filter(s => !s.hidden).length,
    caption: document.querySelector("[data-caption]").textContent, cur: [...document.querySelectorAll("[data-thumb]")].findIndex(t => t.getAttribute("aria-current") === "true") + 1 }))()`;
  let v = await ev(view);
  check("viewer: three pictures besides the opening one", (await ev(`document.querySelectorAll("[data-slide]").length`)) === 3 && v.at === "1" && v.active === 1, JSON.stringify(v));
  check("viewer: it never repeats the opening picture", await ev(`(() => { const hero = document.querySelector(".vopen img").currentSrc.split("?")[0]; return ![...document.querySelectorAll("[data-slide] img")].some(i => i.src.split("?")[0] === hero); })()`));
  check("viewer: every thumbnail is loaded (no empty rectangles)", await ev(`[...document.querySelectorAll(".viewer__thumb")].every(i => i.complete && i.naturalWidth > 0)`));
  await ev(`document.querySelector("[data-next]").click(); true`); await b.sleep(1000);
  v = await ev(view);
  check("viewer: next moves to picture 2 and updates the caption", v.at === "2" && v.cur === 2 && v.active === 1 && v.shown === 1 && v.caption.length > 10, JSON.stringify(v));
  await ev(`document.querySelector("[data-prev]").click(); document.querySelector("[data-prev]").click(); true`); await b.sleep(1000);
  v = await ev(view);
  check("viewer: previous wraps round to the last picture", v.at === "3" && v.cur === 3, JSON.stringify(v));
  await ev(`document.querySelectorAll("[data-thumb]")[1].click(); true`); await b.sleep(1000);
  check("viewer: a thumbnail selects its picture", (await ev(view)).at === "2");
  await ev(`document.querySelector("[data-next]").focus(); true`);
  await key("ArrowRight", "ArrowRight", 39); await b.sleep(900);
  check("viewer: the right arrow key advances", (await ev(view)).at === "3");
  await ev(`document.querySelector("[data-open]").click(); true`); await b.sleep(1000);
  const lb = await ev(`(() => { const d = document.getElementById("image-dialog"); return { open: d.open, count: d.querySelector("[data-count]").textContent }; })()`);
  check("viewer: the large picture opens the full-size viewer at the same picture", lb.open && lb.count === "3 / 3", JSON.stringify(lb));
  await key("ArrowLeft", "ArrowLeft", 37); await b.sleep(500);
  check("viewer: the full-size viewer moves with the arrow keys", (await ev(`document.getElementById("image-dialog").querySelector("[data-count]").textContent`)) === "2 / 3");
  await key("Escape", "Escape", 27); await b.sleep(500);
  check("viewer: Esc closes it", !(await ev(`document.getElementById("image-dialog").open`)));

  // ---- the other settings of pictures
  for (const [slug, selector, n] of [["grotti-cheetah", ".mos li", 3], ["vapid-stanier", ".mos li", 3], ["shitzu-squalo", ".pano li", 3], ["dinka-enduro", ".scenefig li", 1], ["crest-kayak", ".scenefig li", 1]]) {
    await b.open(BASE + "/vehicles/" + slug, 900);
    await ev(`document.querySelectorAll("img").forEach(i => { i.loading = "eager"; }); true`); await b.sleep(2500);
    check(`${slug}: its pictures are set as ${selector.slice(1, 4)} and all load`, (await ev(`document.querySelectorAll("${selector}").length`)) === n && (await ev(`[...document.querySelectorAll("${selector} img")].every(i => i.complete && i.naturalWidth > 0)`)));
  }
  await ev(`document.querySelector(".vshow a[data-lightbox]").click(); true`); await b.sleep(900);
  check("a still opens the full-size viewer from its set", await ev(`document.getElementById("image-dialog").open`));
  await key("Escape", "Escape", 27);
  await b.open(BASE + "/vehicles/vapid-ganado", 1200);
  check("one-picture vehicle: no gallery section and no empty frame", await ev(`!document.querySelector(".vshow") && !document.querySelector("[data-viewer]")`));

  // ---- every vehicle page
  for (const slug of ALL) {
    await b.open(BASE + "/vehicles/" + slug, 900);
    await ev(`document.querySelectorAll("img").forEach(i => { i.loading = "eager"; }); true`); await b.sleep(3000);
    const bad = await ev(`[...document.images].filter(i => getComputedStyle(i).display !== "none" && !i.closest("[hidden]") && !i.closest("dialog") && (!i.complete || i.naturalWidth === 0)).length`);
    const next = await ev(`document.querySelectorAll(".neighbour").length`);
    const rail = await ev(`document.querySelectorAll(".rail__item").length`);
    check("vehicle page " + slug + ": every shown picture loads, previous and next, all seven in the row", bad === 0 && next === 2 && rail === 7, "broken " + bad + ", next " + next + ", rail " + rail);
  }
  console.log(failures ? "\n" + failures + " FAILED" : "\nall passed");
  process.exitCode = failures ? 1 : 0;
}
