// Tab through the Garage pages: every stop is reachable in a sensible order, has an accessible name, and shows a visible focus ring.
//   node scripts/qa/cdp.mjs scripts/qa/garage_keyboard.mjs
const BASE = process.env.GARAGE_BASE || "http://127.0.0.1:5057";
let failures = 0;
const check = (name, ok, detail = "") => { console.log((ok ? "PASS  " : "FAIL  ") + name + (detail ? "  (" + detail + ")" : "")); if (!ok) { failures++; } };

export default async function (b) {
  const tab = async (shift) => {
    await b.send("Input.dispatchKeyEvent", { type: "keyDown", key: "Tab", code: "Tab", windowsVirtualKeyCode: 9, modifiers: shift ? 8 : 0 });
    await b.send("Input.dispatchKeyEvent", { type: "keyUp", key: "Tab", code: "Tab", windowsVirtualKeyCode: 9, modifiers: shift ? 8 : 0 });
  };
  const describe = `(() => { const e = document.activeElement; if (!e || e === document.body) { return null; } const c = getComputedStyle(e); const r = e.getBoundingClientRect();
    const name = (e.getAttribute("aria-label") || e.textContent || e.value || e.getAttribute("placeholder") || "").replace(/\\s+/g, " ").trim().slice(0, 48);
    return { main: !!e.closest("main"), tag: e.tagName.toLowerCase() + (e.className && typeof e.className === "string" ? "." + e.className.split(" ")[0] : ""), name, ring: c.outlineStyle !== "none" && parseFloat(c.outlineWidth) >= 2, w: Math.round(r.width), h: Math.round(r.height), onscreen: r.bottom > 0 && r.top < innerHeight }; })()`;
  for (const [w, h] of [[1440, 900], [390, 844]]) {
    await b.send("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: 1, mobile: w < 700 });
    for (const route of ["/vehicles", "/vehicles/vapid-stanier", "/vehicles/vapid-ganado"]) {
      await b.open(BASE + route, 1500);
      await b.eval(`document.activeElement && document.activeElement.blur(); window.scrollTo(0, 0); true`);
      const stops = [];
      for (let i = 0; i < 60; i++) {
        await tab(false); await b.sleep(40);
        const d = await b.eval(describe);
        if (!d) { continue; }
        stops.push(d);
        if (/Back to the garage|Show the whole|Credits and legal|About the project/.test(d.name) && i > 5 && d.tag.startsWith("a") && /Credits|About/.test(d.name)) { break; }
      }
      const unnamed = stops.filter((s) => !s.name);
      const noRing = stops.filter((s) => !s.ring);
      const tiny = stops.filter((s) => s.main && (s.w < 24 || s.h < 24));      // the footer and header are shared and checked with their own pages
      check(`${w}px ${route}: ${stops.length} tab stops, all named`, stops.length > 8 && unnamed.length === 0, unnamed.map((s) => s.tag).join(","));
      check(`${w}px ${route}: every stop shows a focus ring`, noRing.length === 0, noRing.map((s) => s.tag + ":" + s.name).join(" | "));
      check(`${w}px ${route}: no stop is smaller than 24 px`, tiny.length === 0, tiny.map((s) => s.tag + " " + s.w + "x" + s.h).join(" | "));
      if (route === "/vehicles") {
        const order = stops.map((s) => s.name);
        const iLine = order.findIndex((n) => /Cheetah/.test(n)), iSearch = order.findIndex((n) => /Search/.test(n));
        check(`${w}px ${route}: the lineup comes before the search, the search before the cards`, iLine > -1 && iSearch > iLine && order.findIndex((n, i) => i > iSearch && /Cheetah/.test(n)) > iSearch, order.slice(0, 14).join(" > "));
      }
    }
  }
  console.log(failures ? "\n" + failures + " FAILED" : "\nall passed");
  process.exitCode = failures ? 1 : 0;
}
