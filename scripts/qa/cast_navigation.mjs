// Real-browser check of the Characters navigation: the final circular cast order, every previous and next card clicked,
// the footer list, the numbering, the jump bar and the Explore default.
//   node scripts/qa/cdp.mjs scripts/qa/cast_navigation.mjs      (the app on TL_BASE, default http://127.0.0.1:5057)
const BASE = process.env.TL_BASE || "http://127.0.0.1:5057";
const ORDER = ["jason-duval", "lucia-caminos", "cal-hampton", "brian-heder", "boobie-ike", "dre-quan-priest", "real-dimez", "raul-bautista"];
const NAMES = { "jason-duval": "Jason Duval", "lucia-caminos": "Lucia Caminos", "cal-hampton": "Cal Hampton", "brian-heder": "Brian Heder", "boobie-ike": "Boobie Ike", "dre-quan-priest": "Dre'Quan Priest", "real-dimez": "Real Dimez", "raul-bautista": "Raul Bautista" };
let failures = 0;
const check = (name, ok, detail = "") => { if (!ok) { failures++; } console.log(`${ok ? "PASS" : "FAIL"}  ${name}${detail ? "  (" + detail + ")" : ""}`); };

export default async function (b) {
  await b.send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  const path = () => b.eval(`location.pathname`);
  const click = async (sel) => {
    const before = await path();
    await b.eval(`document.querySelector(${JSON.stringify(sel)}).click(); true`);
    for (let t = 0; t < 40; t++) { await b.sleep(150); if ((await path()) !== before && (await b.eval(`document.readyState`)) === "complete") { break; } }
    await b.sleep(500);
  };

  // ---- previous and next: click each card and land on the right person, with the right label and number
  for (let i = 0; i < ORDER.length; i++) {
    const slug = ORDER[i], prev = ORDER[(i + 7) % 8], next = ORDER[(i + 1) % 8];
    await b.open(`${BASE}/characters/${slug}`, 1400);
    const head = await b.eval(`(document.querySelector(".p-hero .eyebrow") || {}).textContent.trim().replace(/\\s+/g, " ")`);
    check(`${slug}: numbered ${String(i + 1).padStart(2, "0")} / 08`, head.startsWith(`${String(i + 1).padStart(2, "0")} / 08`), head);
    const labels = await b.eval(`({ prev: document.querySelector("[rel=prev] b").textContent, next: document.querySelector("[rel=next] b").textContent })`);
    check(`${slug}: Previous card names ${NAMES[prev]}, Next card names ${NAMES[next]}`, labels.prev === NAMES[prev] && labels.next === NAMES[next], JSON.stringify(labels));
    await click("[rel=prev]");
    check(`${slug}: clicking Previous lands on ${prev}`, (await path()) === `/characters/${prev}`, await path());
    await b.open(`${BASE}/characters/${slug}`, 700);
    await click("[rel=next]");
    check(`${slug}: clicking Next lands on ${next}`, (await path()) === `/characters/${next}`, await path());
    const foot = await b.eval(`[...document.querySelectorAll(".p-all ol a")].map((a) => a.getAttribute("href").split("/").pop())`);
    check(`${next}: the footer list is in the final order and marks this person`, JSON.stringify(foot) === JSON.stringify(ORDER) && (await b.eval(`document.querySelector(".p-all a[aria-current=page]").getAttribute("href")`)) === `/characters/${next}`);
  }

  // ---- the landing: jump bar order and clicks, card order, Explore default
  await b.open(`${BASE}/characters`, 1500);
  const jump = await b.eval(`[...document.querySelectorAll("[data-cast-nav] a[href^='#']")].map((a) => a.getAttribute("href").slice(1)).filter((h) => h !== "explore")`);
  check("jump bar lists the eight in the final order", JSON.stringify(jump) === JSON.stringify(ORDER), jump.join(","));
  const cards = await b.eval(`[...document.querySelectorAll(".spread[id], .person[id]")].map((e) => e.id)`);
  check("the cards follow the final order top to bottom", JSON.stringify(cards) === JSON.stringify(ORDER), cards.join(","));
  for (const slug of ORDER) {
    await b.eval(`document.querySelector("[data-cast-nav] a[href='#${slug}']").click(); true`);
    await b.sleep(1500);
    const at = await b.eval(`(() => { const e = document.getElementById("${slug}").getBoundingClientRect(); const n = document.querySelector("[data-cast-nav]").getBoundingClientRect();
      return { top: Math.round(e.top), navBottom: Math.round(n.bottom), marked: ((document.querySelector("[data-cast-nav] a[aria-current=true]") || {}).textContent || "").replace(/\\s+/g, " ").trim() }; })()`);
    check(`jump bar: ${slug} lands below the bars and is the marked name`, at.top >= at.navBottom && at.marked.includes(NAMES[slug]), JSON.stringify(at));
  }
  await b.open(`${BASE}/characters?region=leonida-keys`, 900);
  const results = await b.eval(`[...document.querySelectorAll(".result__name")].map((e) => e.textContent.trim())`);
  check("Explore default (cast order): Jason before Brian", JSON.stringify(results) === JSON.stringify(["Jason Duval", "Brian Heder"]), results.join(","));
  await b.open(`${BASE}/characters?sort=cast`, 900);
  const all = await b.eval(`[...document.querySelectorAll(".result__name")].map((e) => e.textContent.trim())`);
  check("Explore with the cast sort lists all eight in order", JSON.stringify(all) === JSON.stringify(ORDER.map((s) => NAMES[s])), all.join(","));

  console.log(failures ? `\n${failures} FAILED` : "\nall passed");
  process.exitCode = failures ? 1 : 0;
}
