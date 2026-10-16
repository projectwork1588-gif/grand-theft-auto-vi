// How the Garage behaves when things go wrong or are switched off: console errors, no script, reduced motion, and Rockstar's image
// server unreachable. Every page must stay readable and usable.
//   GARAGE_OUT=review/gate3b/resilience/ node scripts/qa/cdp.mjs scripts/qa/garage_resilience.mjs
import { mkdirSync } from "node:fs";

const BASE = process.env.GARAGE_BASE || "http://127.0.0.1:5057";
const OUT = process.env.GARAGE_OUT || "review/garage-resilience/";
const ROUTES = ["/vehicles", "/vehicles?category=boat&sort=name_desc", "/vehicles?q=zzzz", "/vehicles/grotti-cheetah", "/vehicles/vapid-dominator-buggy", "/vehicles/shitzu-squalo", "/vehicles/vapid-stanier", "/vehicles/vapid-ganado", "/vehicles/dinka-enduro", "/vehicles/crest-kayak"];
let failures = 0;
const check = (name, ok, detail = "") => { console.log((ok ? "PASS  " : "FAIL  ") + name + (detail ? "  (" + detail + ")" : "")); if (!ok) { failures++; } };

export default async function (b) {
  mkdirSync(OUT, { recursive: true });
  const problems = [];
  b.on((d) => {
    if (d.method === "Runtime.exceptionThrown") { problems.push("exception: " + (d.params.exceptionDetails.exception?.description || d.params.exceptionDetails.text).split("\n")[0]); }
    if (d.method === "Runtime.consoleAPICalled" && ["error", "assert"].includes(d.params.type)) { problems.push("console." + d.params.type + ": " + d.params.args.map((a) => a.value || a.description).join(" ").slice(0, 160)); }
    if (d.method === "Log.entryAdded" && d.params.entry.level === "error") { problems.push("log: " + d.params.entry.text + " " + (d.params.entry.url || "").slice(0, 100)); }
    if (d.method === "Network.loadingFailed" && !d.params.canceled && !d.params.blockedReason) { problems.push("request failed: " + d.params.errorText); }
    if (d.method === "Network.responseReceived" && d.params.response.status >= 400) { problems.push("http " + d.params.response.status + " " + d.params.response.url.slice(0, 120)); }
  });
  await b.send("Log.enable"); await b.send("Network.enable");
  await b.colorScheme(false);

  // ---- 1. nothing in the console, nothing failing, on every page at two widths
  for (const [w, h] of [[1440, 900], [390, 844]]) {
    await b.send("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: 1, mobile: w < 700 });
    for (const route of ROUTES) {
      problems.length = 0;
      await b.open(BASE + route, 1200);
      await b.eval(`document.querySelectorAll("img").forEach(i => { i.loading = "eager"; }); window.scrollTo(0, document.body.scrollHeight); true`);
      await b.sleep(1800);
      check(`${w}px ${route}: no console errors, no failed requests`, problems.length === 0, problems.slice(0, 3).join(" | "));
    }
  }

  // ---- 2. without script
  await b.send("Emulation.setScriptExecutionDisabled", { value: true });
  await b.send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  await b.open(BASE + "/vehicles", 1500);
  const nojs = await b.eval(`({ visible: [...document.querySelectorAll("[data-panel]")].filter(p => !p.hidden).length, links: [...document.querySelectorAll("[data-pick]")].map(a => a.getAttribute("href")), cards: document.querySelectorAll(".tile").length, form: document.querySelector(".ctl__form").method + " " + document.querySelector(".ctl__form").getAttribute("action"), cats: document.querySelectorAll(".ctl__cats a").length })`);
  check("without script: one machine on show, the lineup is seven links, the showroom is a form and links", nojs.visible === 1 && nojs.links.length === 7 && nojs.cards === 7 && /get/i.test(nojs.form) && nojs.cats === 7, JSON.stringify(nojs));
  await b.shot(OUT + "no-script-vehicles.jpg");
  await b.open(BASE + "/vehicles/vapid-dominator-buggy", 1500);
  const nojs2 = await b.eval(`({ slides: [...document.querySelectorAll("[data-slide]")].filter(s => !s.hidden).length, thumbs: [...document.querySelectorAll("[data-thumb]")].map(a => a.getAttribute("href").includes("imwidth=2560")).every(Boolean), more: document.querySelectorAll(".neighbour").length })`);
  check("without script: the showcase shows its first picture and every thumbnail links to the full picture", nojs2.slides === 1 && nojs2.thumbs && nojs2.more === 2, JSON.stringify(nojs2));
  await b.shot(OUT + "no-script-vehicle.jpg", { full: true });
  await b.send("Emulation.setScriptExecutionDisabled", { value: false });

  // ---- 3. reduced motion: no movement, a short plain fade
  await b.send("Emulation.setEmulatedMedia", { features: [{ name: "prefers-reduced-motion", value: "reduce" }] });
  await b.open(BASE + "/vehicles", 1500);
  const calm = await b.eval(`(() => { const p = document.querySelector('[data-panel="grotti-cheetah"]'); const c = getComputedStyle(p); const img = getComputedStyle(p.querySelector("img")); const copy = getComputedStyle(p.querySelector(".plate"));
    return { fade: c.transitionDuration, prop: c.transitionProperty, imgT: img.transform, copyT: copy.transform, imgDur: img.transitionDuration, anim: getComputedStyle(document.querySelector(".cine__head")).animationDuration }; })()`);
  check("reduced motion: the picture does not zoom or the words rise", calm.imgT === "none" && calm.copyT === "none", JSON.stringify(calm));
  check("reduced motion: only a short opacity fade remains", /0\.25s/.test(calm.fade) && /opacity/.test(calm.prop), calm.fade + " " + calm.prop);
  await b.eval(`document.querySelector('[data-pick="shitzu-squalo"]').click(); true`);
  await b.sleep(1300);
  check("reduced motion: choosing a machine still works", await b.eval(`document.querySelector('[data-panel="shitzu-squalo"]').classList.contains("is-active")`));
  await b.send("Emulation.setEmulatedMedia", { features: [{ name: "prefers-reduced-motion", value: "no-preference" }] });

  // ---- 4. Rockstar's image server unreachable: the pages stay readable
  await b.send("Network.setBlockedURLs", { urls: ["https://www.rockstargames.com/*"] });
  await b.open(BASE + "/vehicles", 1800);
  const dark = await b.eval(`({ h1: document.querySelector("h1").textContent, name: document.querySelector(".scene.is-active .plate").textContent, cards: [...document.querySelectorAll(".tile__model")].length, overflow: document.documentElement.scrollWidth > innerWidth })`);
  check("images blocked: the opening, the names and the showroom are still there", dark.h1 === "Machines of Leonida" && dark.cards === 7 && !dark.overflow, JSON.stringify(dark));
  await b.shot(OUT + "images-blocked-vehicles.jpg");
  await b.open(BASE + "/vehicles/vapid-stanier", 1800);
  await b.shot(OUT + "images-blocked-vehicle.jpg", { full: true });
  check("images blocked: a vehicle page keeps its text, plate and links", await b.eval(`!!document.querySelector(".vopen__plate") && !!document.querySelector(".vcredits") && document.querySelectorAll(".neighbour").length === 2`));
  await b.send("Network.setBlockedURLs", { urls: [] });

  console.log(failures ? "\n" + failures + " FAILED" : "\nall passed");
  process.exitCode = failures ? 1 : 0;
}
