// Screenshots of the Characters pages for review: heroes, story sections and whole pages of the profiles, the landing page and
// its network, at the widths a reviewer cares about. Motion is switched off so the stills are what a visitor sees at rest.
//   CAP_OUT=dir CAP_WIDTHS=1440,820,390 CAP_SLUGS=real-dimez CAP_KIND=hero,story,full,landing,network node scripts/qa/cdp.mjs scripts/qa/capture_characters.mjs
const BASE = process.env.TL_BASE || "http://127.0.0.1:5057";
const OUT = process.env.CAP_OUT || "review/capture/";
const ORDER = ["jason-duval", "lucia-caminos", "cal-hampton", "brian-heder", "boobie-ike", "dre-quan-priest", "real-dimez", "raul-bautista"];
const SLUGS = (process.env.CAP_SLUGS || ORDER.join(",")).split(",");
const WIDTHS = (process.env.CAP_WIDTHS || "1440,820,390").split(",").map(Number);
const KINDS = (process.env.CAP_KIND || "hero,story,full,landing,network").split(",");
const H = { 1440: 900, 1280: 800, 1024: 768, 820: 1180, 390: 844 };

export default async function (b) {
  for (const w of WIDTHS) {
    const mobile = w < 700;
    const dpr = KINDS.includes("network") && process.env.CAP_HIDPI ? (mobile ? 3 : 2) : 1;
    await b.send("Emulation.setDeviceMetricsOverride", { width: w, height: H[w] || 900, deviceScaleFactor: dpr, mobile });
    const settle = async () => {
      await b.eval(`document.querySelectorAll("img").forEach(i => { i.loading = "eager"; }); true`);
      const total = await b.eval("document.documentElement.scrollHeight");
      for (let y = 0; y < total; y += 500) { await b.eval(`window.scrollTo(0, ${y}); true`); await b.sleep(120); }
      for (let i = 0; i < 80; i++) { const n = await b.eval(`[...document.images].filter(i => !i.complete || i.naturalWidth === 0).length`); if (n <= 1) break; await b.sleep(300); }
      await b.eval("window.scrollTo(0, 0); true"); await b.sleep(500);
    };
    await b.open(BASE + "/about", 100);
    await b.eval(`localStorage.setItem("tv-motion", "0"); true`);
    for (const slug of SLUGS) {
      if (!KINDS.some((k) => ["hero", "story", "full"].includes(k))) { break; }
      await b.open(BASE + "/characters/" + slug, 1200);
      await settle();
      if (KINDS.includes("hero")) { await b.shot(`${OUT}${w}-${slug}-hero.jpg`); }
      if (KINDS.includes("full")) { await b.shot(`${OUT}${w}-${slug}-full.jpg`, { full: true }); }
      if (KINDS.includes("story")) {
        await b.eval(`window.scrollTo(0, document.querySelector(".p-story").getBoundingClientRect().top + scrollY - 130); true`); await b.sleep(600);
        await b.shot(`${OUT}${w}-${slug}-story.jpg`);
      }
    }
    if (KINDS.includes("landing") || KINDS.includes("network")) {
      await b.open(BASE + "/characters", 1500);
      await settle();
      if (KINDS.includes("landing")) { await b.shot(`${OUT}${w}-landing-full.jpg`, { full: true }); }
      if (KINDS.includes("network")) {
        const r = await b.eval(`(() => { const r = document.querySelector(".web").getBoundingClientRect(); return {x: 0, y: r.top + scrollY, width: innerWidth, height: r.height}; })()`);
        await b.shot(`${OUT}net-${w}.jpg`, { clip: r });
      }
    }
    console.log(w, "done", await b.eval(`document.documentElement.scrollWidth > document.documentElement.clientWidth`) ? "OVERFLOW" : "no overflow");
  }
  await b.eval(`localStorage.clear(); true`);
}
