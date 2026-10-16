// Screenshots of the Garage's interactive states for the review pack: the showcase viewer (each picture, the full-size viewer), the
// showroom controls in use, the related-vehicle cards, and keyboard focus.
//   GARAGE_OUT=review/gate3b/pack/states/ node scripts/qa/cdp.mjs scripts/qa/garage_review_shots.mjs
import { mkdirSync } from "node:fs";

const BASE = process.env.GARAGE_BASE || "http://127.0.0.1:5057";
const OUT = process.env.GARAGE_OUT || "review/garage-states/";
const H = { 1440: 900, 820: 1180, 390: 844 };

export default async function (b) {
  mkdirSync(OUT, { recursive: true });
  await b.colorScheme(false);
  const key = async (k, code, vk) => { await b.send("Input.dispatchKeyEvent", { type: "keyDown", key: k, code, windowsVirtualKeyCode: vk }); await b.send("Input.dispatchKeyEvent", { type: "keyUp", key: k, code, windowsVirtualKeyCode: vk }); };
  const settle = async () => {
    await b.eval(`document.querySelectorAll("img").forEach(i => { i.loading = "eager"; }); true`);
    for (let i = 0; i < 40; i++) { const n = await b.eval(`[...document.images].filter(i => i.getClientRects().length && !i.closest("dialog") && (!i.complete || i.naturalWidth === 0)).length`); if (n === 0) { break; } await b.sleep(250); }
    await b.eval(`Promise.all([...document.images].filter((i) => i.getClientRects().length).map((i) => i.decode().catch(() => {}))).then(() => true)`);
    await b.sleep(700);
  };
  for (const w of [1440, 820, 390]) {
    await b.send("Emulation.setDeviceMetricsOverride", { width: w, height: H[w], deviceScaleFactor: 1, mobile: w < 700 });
    await b.open(BASE + "/about", 100);
    await b.eval(`localStorage.setItem("tv-motion", "0"); true`);

    // ---- the showcase viewer: each picture, then the full-size viewer
    await b.open(BASE + "/vehicles/shitzu-squalo", 1500);
    await settle();
    for (let i = 1; i <= 3; i++) {
      await b.eval(`document.querySelector("#showcase").scrollIntoView(); window.scrollBy(0, -40); true`); await b.sleep(500);
      await b.shot(`${OUT}${w}-viewer-${i}.jpg`);
      await b.eval(`document.querySelector("[data-next]").click(); true`); await b.sleep(900);
    }
    await b.eval(`document.querySelector("[data-open]").click(); true`); await b.sleep(1400);
    await b.shot(`${OUT}${w}-viewer-fullsize.jpg`);
    await key("Escape", "Escape", 27); await b.sleep(500);

    // ---- related-vehicle cards
    await b.eval(`document.querySelector(".vmore").scrollIntoView(); true`); await b.sleep(600);
    const r = await b.eval(`(() => { const e = document.querySelector(".vmore").getBoundingClientRect(); return { x: 0, y: e.top + scrollY, width: innerWidth, height: e.height }; })()`);
    await b.shot(`${OUT}${w}-related-cards.jpg`, { clip: r });

    // ---- the showroom in use
    for (const [name, route] of [["filter-boats", "/vehicles?category=boat"], ["search-vapid-sorted", "/vehicles?q=vapid&sort=name_desc"], ["empty-search", "/vehicles?q=zzzz"], ["page-two", "/vehicles?per_page=2&page=2"], ["category-and-search", "/vehicles?category=offroad&q=dominator"]]) {
      await b.open(BASE + route, 1300);
      await b.eval(`document.getElementById("showroom").scrollIntoView(); true`); await settle();
      await b.shot(`${OUT}${w}-showroom-${name}.jpg`);
    }

    // ---- keyboard focus
    await b.open(BASE + "/vehicles", 1500); await settle();
    await b.eval(`document.querySelector('[data-pick="grotti-cheetah"]').focus(); true`);
    await key("ArrowRight", "ArrowRight", 39); await b.sleep(900);
    await b.shot(`${OUT}${w}-focus-lineup.jpg`);
    await b.eval(`document.getElementById("showroom").scrollIntoView(); document.querySelector(".gcard__link").focus(); true`); await b.sleep(600);
    await b.shot(`${OUT}${w}-focus-card.jpg`);
    console.log(w, "done");
  }
  await b.eval(`localStorage.clear(); true`);
}
