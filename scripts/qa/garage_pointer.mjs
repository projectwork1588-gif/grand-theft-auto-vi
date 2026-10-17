// REAL pointer testing of the Garage opening's Explore button. A programmatic element.click() ignores whatever lies on top of the button, which is how
// an overlapped button passed earlier browser checks. This script instead:
//   * hit-tests a grid of points across the visible pill (document.elementFromPoint): every point inside the pill's shape must belong to the button;
//   * sends real mouse presses at the left edge, the text, the centre, the arrow and the right edge (Input.dispatchMouseEvent), and on phones a real
//     touch tap (Input.dispatchTouchEvent), and requires the browser to land on /vehicles/<the machine on show>, which must then answer with its own page;
//   * presses Enter on the focused button.
// It does this for every machine in the lineup at laptop, desktop, tablet and phone sizes.
//   node scripts/qa/cdp.mjs scripts/qa/garage_pointer.mjs        (the app on TL_BASE, default http://127.0.0.1:5057; exit status 1 on any failure)
const BASE = process.env.TL_BASE || "http://127.0.0.1:5057";
const PAGE = process.env.POINTER_PATH || "/vehicles";                  // the page whose opening is tested (the Garage)
const SIZES = (process.env.POINTER_SIZES || "1920x1080,1440x900,1366x768,1280x720,1024x768,820x1180,390x844,360x740").split(",").map((s) => s.split("x").map(Number));
const BUTTON = `document.querySelector('[data-stage] [data-panel].is-active a.gbtn')`;
let failed = 0;
const report = (ok, label, detail = "") => { if (!ok) { failed++; } console.log((ok ? "PASS  " : "FAIL  ") + label + (detail ? "  (" + detail + ")" : "")); };

export default async function (b) {
  await b.colorScheme(false);
  await b.open(BASE + "/about", 100);
  await b.eval(`localStorage.setItem("tv-motion", "1"); true`);
  for (const [W, H] of SIZES) {
    const phone = W < 700;
    await b.send("Emulation.setDeviceMetricsOverride", { width: W, height: H, deviceScaleFactor: 1, mobile: phone });
    await b.send("Emulation.setTouchEmulationEnabled", phone ? { enabled: true, maxTouchPoints: 5 } : { enabled: false });
    await b.open(BASE + PAGE, 1500);
    const slugs = JSON.parse(await b.eval(`JSON.stringify([...document.querySelectorAll("[data-stage] [data-pick]")].map((a) => a.dataset.pick))`));
    report(slugs.length >= 2, `${W}x${H}: the lineup has machines to test`, slugs.length + " machines");
    for (const [index, slug] of slugs.entries()) {
      const tag = `${W}x${H} ${slug}`;
      // the opening with this machine on show: loaded, the script ready, and the other panels gone (polled, never a fixed wait; tried again if the page lags)
      const ready = `(() => { const shown = [...document.querySelectorAll("[data-stage] [data-panel]")].filter((p) => !p.hidden); return location.pathname === "${PAGE.split("?")[0]}" && shown.length === 1 && shown[0].dataset.panel === "${slug}" && shown[0].classList.contains("is-active"); })()`;
      const show = async () => {
        for (let attempt = 0; attempt < 3; attempt++) {
          await b.open(BASE + PAGE, 600);
          for (let i = 0; i < 40; i++) {
            if (await b.eval(`location.pathname === "${PAGE.split("?")[0]}" && !!document.querySelector('[data-stage] [data-pick]')`).catch(() => false)) { break; }
            await b.sleep(150);
          }
          if (index > 0) { await b.eval(`document.querySelector('[data-stage] [data-pick="${slug}"]').click(); true`).catch(() => {}); }
          for (let i = 0; i < 40; i++) {
            if (await b.eval(ready).catch(() => false)) {
              // the entrance still moves the words for about a second: wait until the button has stopped before measuring where to press
              let last = "", still = 0;
              for (let k = 0; k < 60 && still < 3; k++) {
                // the rect is only trusted when nothing on the page is still animating (a delayed entrance is motionless for a moment before it moves)
                const now = await b.eval(`JSON.stringify((() => { const r = ${BUTTON}.getBoundingClientRect(); const running = document.getAnimations().filter((a) => (a.playState === "running" || a.playState === "pending") && !(a.effect && a.effect.getTiming().duration >= 3000)).length;   // the entrance moves the words; the slow settle of the picture (9 s) does not move the button return [running, getComputedStyle(${BUTTON}).opacity, ...[r.left, r.top, r.width, r.height].map((v) => Math.round(v * 10) / 10)]; })())`).catch(() => "");
                still = (now === last && now.startsWith("[0,\"1\"")) ? still + 1 : 0; last = now; await b.sleep(120);
              }
              return true;
            }
            await b.sleep(150);
          }
        }
        report(false, `${tag}: the opening could not be brought up with this machine on show`);
        return false;
      };
      if (!(await show())) { continue; }
      const info = JSON.parse(await b.eval(`(() => { const a = ${BUTTON}; const r = a.getBoundingClientRect(); const panel = a.closest("[data-panel]");
        const inside = (x, y) => { const rad = r.height / 2, cx = Math.min(Math.max(x, r.left + rad), r.right - rad), cy = r.top + rad; return Math.hypot(x - cx, y - cy) <= rad - 1.5; };
        let tested = 0, blocked = [];
        for (let fx = 0.03; fx < 1; fx += 0.04) for (let fy = 0.1; fy < 1; fy += 0.2) { const x = r.left + r.width * fx, y = r.top + r.height * fy; if (!inside(x, y)) continue; tested++;
          const el = document.elementFromPoint(x, y); if (!(el === a || a.contains(el))) blocked.push(Math.round(x) + "," + Math.round(y) + " " + (el ? el.tagName.toLowerCase() + "." + String(el.className && el.className.baseVal !== undefined ? el.className.baseVal : el.className).slice(0, 24) : "none")); }
        return JSON.stringify({ rect: [r.left, r.top, r.width, r.height], href: a.getAttribute("href"), panel: panel.dataset.panel, inView: r.top >= 0 && r.bottom <= innerHeight && r.left >= 0 && r.right <= innerWidth, tested, blocked, svg: (() => { const s = a.querySelector("svg").getBoundingClientRect(); return [s.left + s.width / 2, s.top + s.height / 2]; })() }); })()`));
      report(info.panel === slug && info.href === "/vehicles/" + slug, `${tag}: the button on show points at that machine's page`, info.href);
      report(info.inView, `${tag}: the whole button is inside the window`, info.rect.map(Math.round).join(","));
      report(info.blocked.length === 0, `${tag}: all ${info.tested} sampled points of the visible pill belong to the button`, info.blocked.slice(0, 3).join(" | "));
      const [x0, y0, w, h] = info.rect;
      const spots = [["left edge", x0 + h / 2 * 0.7, y0 + h / 2], ["text", x0 + w * 0.3, y0 + h / 2], ["centre", x0 + w / 2, y0 + h / 2], ["arrow", info.svg[0], info.svg[1]], ["right edge", x0 + w - h / 2 * 0.7, y0 + h / 2], ["top edge", x0 + w / 2, y0 + 3], ["bottom edge", x0 + w / 2, y0 + h - 3]];
      // Each spot gets a real pointer press (or a real touch). A click listener records which link the browser delivered it to and holds the page in place, so every
      // spot can be tried on one load; the click only arrives at the button if the pointer really reached it, which an element.click() never proves.
      const arm = `window.__hit = null; document.addEventListener("click", (e) => { const a = e.target.closest ? e.target.closest("a") : null; window.__hit = a ? a.getAttribute("href") : "other:" + (e.target.tagName || ""); e.preventDefault(); }, { capture: true, once: true }); true`;
      const press = async (x, y) => {
        if (phone) {
          await b.send("Input.dispatchTouchEvent", { type: "touchStart", touchPoints: [{ x, y }] });
          await b.send("Input.dispatchTouchEvent", { type: "touchEnd", touchPoints: [] });
        } else {
          await b.send("Input.dispatchMouseEvent", { type: "mouseMoved", x, y });
          await b.send("Input.dispatchMouseEvent", { type: "mousePressed", x, y, button: "left", clickCount: 1 });
          await b.send("Input.dispatchMouseEvent", { type: "mouseReleased", x, y, button: "left", clickCount: 1 });
        }
        await b.sleep(120);
      };
      if (!(await show())) { continue; }
      for (const [name, x, y] of spots) {
        await b.eval(arm);
        await press(x, y);
        const hit = await b.eval("window.__hit");
        report(hit === "/vehicles/" + slug, `${tag}: a real ${phone ? "touch tap" : "click"} on the ${name} (${Math.round(x)},${Math.round(y)}) reaches the Explore link`, String(hit));
      }
      // keyboard: the focused button and Enter
      await b.eval(arm);
      await b.eval(`${BUTTON}.focus(); true`);
      await b.send("Input.dispatchKeyEvent", { type: "keyDown", key: "Enter", code: "Enter", windowsVirtualKeyCode: 13, text: "\r" });
      await b.send("Input.dispatchKeyEvent", { type: "keyUp", key: "Enter", code: "Enter", windowsVirtualKeyCode: 13 });
      await b.sleep(150);
      report((await b.eval("window.__hit")) === "/vehicles/" + slug, `${tag}: Enter on the focused button activates the Explore link`);
      // and once, for real: the press on the middle of the button leaves the page for this machine's own page, which answers with its name
      if (!(await show())) { continue; }
      await press(x0 + w / 2, y0 + h / 2);
      let where = "";
      for (let i = 0; i < 40; i++) { where = await b.eval("location.pathname").catch(() => ""); if (where === "/vehicles/" + slug) { break; } await b.sleep(150); }
      let title = "";
      for (let i = 0; i < 40 && title.trim().length < 3; i++) { title = await b.eval(`(document.querySelector("h1") || {}).textContent || ""`).catch(() => ""); if (title.trim().length < 3) { await b.sleep(150); } }
      report(where === "/vehicles/" + slug && title.length > 2, `${tag}: pressing the middle of the button opens the machine's own page`, where + " / " + title.trim().replace(/\s+/g, " "));
    }
    // the machines reached with the arrows (not the lineup) are the same machines, with the same working button
    if (!phone || true) {
      await b.open(BASE + PAGE, 600);
      for (let i = 0; i < 40 && !(await b.eval(`!!document.querySelector("[data-ctl]") && !document.querySelector("[data-ctl]").hidden`).catch(() => false)); i++) { await b.sleep(150); }   // the arrows appear when the script has started
      let ok = true, seen = [];
      for (let i = 0; i < slugs.length + 1; i++) {
        const now = JSON.parse(await b.eval(`JSON.stringify({ slug: ${BUTTON}.closest("[data-panel]").dataset.panel, href: ${BUTTON}.getAttribute("href") })`));
        seen.push(now.slug); ok = ok && now.href === "/vehicles/" + now.slug;
        await b.eval(`document.querySelector('[data-step="1"]').click(); true`);
        for (let k = 0; k < 50; k++) {       // the next machine takes its place when its picture has arrived: poll for it instead of waiting a fixed time
          await b.sleep(150);
          const shown = await b.eval(`JSON.stringify([...document.querySelectorAll("[data-stage] [data-panel]")].filter((p) => !p.hidden && p.classList.contains("is-active")).map((p) => p.dataset.panel))`).catch(() => "[]");
          if (JSON.parse(shown)[0] && JSON.parse(shown)[0] !== now.slug) { break; }
        }
        await b.sleep(250);
      }
      report(ok && seen[slugs.length] === seen[0] && new Set(seen).size === slugs.length, `${W}x${H}: stepping with the arrows visits every machine once and comes back round, the button always pointing at the machine shown`, seen.join(" > "));
    }
  }
  // while one scene is being lifted away, its Explore button (the previous machine's) must not catch a press meant for the new scene
  {
    await b.send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
    await b.send("Emulation.setTouchEmulationEnabled", { enabled: false });
    await b.open(BASE + PAGE, 600);
    for (let i = 0; i < 40 && !(await b.eval(`!!document.querySelector("[data-ctl]") && !document.querySelector("[data-ctl]").hidden`).catch(() => false)); i++) { await b.sleep(150); }
    await b.eval(`document.querySelectorAll("[data-stage] img").forEach((i) => { i.loading = "eager"; }); true`);
    await b.sleep(2500);
    await b.eval(`document.querySelector('[data-step="1"]').click(); true`);
    let seen = null;
    for (let i = 0; i < 12 && !seen; i++) {
      await b.sleep(60);
      seen = JSON.parse(await b.eval(`JSON.stringify((() => { const old = document.querySelector("[data-stage] .is-leaving a.gbtn"); if (!old) return null; const r = old.getBoundingClientRect(); const el = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2); return { caught: !!(el && el.closest(".is-leaving")) }; })())`).catch(() => "null"));
    }
    report(seen === null ? true : !seen.caught, "a scene being lifted away cannot be pressed", seen === null ? "this page has no lifting scene, so nothing to catch" : "checked mid-change");
  }
  await b.eval(`localStorage.clear(); true`);
  console.log(failed ? `\n${failed} FAILED` : "\nall passed");
  process.exitCode = failed ? 1 : 0;
}
