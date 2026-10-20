// The shared dialogs' Close button, in a real browser (the image viewer and the video player that base.html gives every page).
//   TL_BASE=http://127.0.0.1:5059 node scripts/qa/cdp.mjs scripts/qa/dialog_close_qa.mjs        (exit status 1 on any failure)
// On Home, a character page, the Garage and a vehicle page, Leonida and a region page, Media, Music and Stories, at desktop (1440) and phone (390) width: wherever a page has an image or a
// video opener, the dialog opens, its Close button is drawn whole, on the screen and the topmost thing at its place (not clipped by the dialog's own box), the button closes it, and Escape
// closes it. Pages with no opener are listed, not failed. Also checks that none of those pages throws a script error.
const BASE = process.env.TL_BASE || "http://127.0.0.1:5063";
let failed = 0;
const report = (ok, label, d = "") => { if (!ok) failed++; console.log((ok ? "PASS  " : "FAIL  ") + label + (d ? "  (" + d + ")" : "")); };
export default async function (b) {
  const problems = [];
  b.on((d) => {
    if (d.method === "Runtime.exceptionThrown") problems.push("exception: " + (d.params.exceptionDetails.exception?.description || d.params.exceptionDetails.text));
  });
  await b.send("Network.enable");
  await b.open(BASE + "/about", 100);
  await b.eval(`localStorage.setItem("tv-motion", "1"); true`);
  const key = async (k, code, vk) => { await b.send("Input.dispatchKeyEvent", { type: "keyDown", key: k, code, windowsVirtualKeyCode: vk }); await b.send("Input.dispatchKeyEvent", { type: "keyUp", key: k, code, windowsVirtualKeyCode: vk }); };
  const close = (id) => b.eval(`(() => { const c = document.querySelector("#${id} [data-close]"); if (!c) return "none"; const r = c.getBoundingClientRect(); const top = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2); const cs = getComputedStyle(c); return (top === c || c.contains(top)) && r.top >= 0 && r.bottom <= innerHeight && r.left >= 0 && r.right <= innerWidth && r.width >= 32 && r.height >= 32 && cs.visibility !== "hidden" && cs.display !== "none" ? "ok" : "hidden " + JSON.stringify([Math.round(r.top), Math.round(r.left), Math.round(r.width), Math.round(r.height)]) + " top=" + (top && top.tagName); })()`);
  const first = async (sel) => b.eval(`(() => { const e = document.querySelector(${JSON.stringify(sel)}); return e ? true : false; })()`);
  // pick real detail pages from the lists
  const link = async (listPath, prefix) => { await b.open(BASE + listPath, 300); return b.eval(`(() => { const a = [...document.querySelectorAll("a[href]")].map((x) => x.getAttribute("href")).find((h) => h.indexOf(${JSON.stringify(prefix)}) === 0 && h.length > ${prefix.length}); return a || null; })()`); };
  const detailVeh = await link("/vehicles", "/vehicles/");
  const pages = ["/", "/characters", "/characters/jason-duval", "/vehicles", detailVeh, "/regions", "/regions/vice-city", "/media", "/music", "/missions"].filter(Boolean);
  for (const [W, H] of [[1440, 900], [390, 844]]) {
    await b.send("Emulation.setDeviceMetricsOverride", { width: W, height: H, deviceScaleFactor: 1, mobile: W < 700 });
    for (const p of pages) {
      await b.open(BASE + p, 1500);
      const hasImg = await first("a[data-lightbox]"), hasVid = await first("[data-video]");
      const tag = `${W}px ${p}`;
      if (!hasImg && !hasVid) { console.log(`INFO  ${tag}: no image or video dialog opener on this page`); continue; }
      for (const [kind, sel, id] of [["image", "a[data-lightbox]", "image-dialog"], ["video", "[data-video]", "video-dialog"]]) {
        if (!(await first(sel))) { continue; }
        await b.eval(`(() => { const e = document.querySelector(${JSON.stringify(sel)}); e.scrollIntoView({ block: "center" }); e.click(); })()`); await b.sleep(900);
        const open = await b.eval(`document.getElementById("${id}").open`);
        const vis = open ? await close(id) : "dialog did not open";
        report(open && vis === "ok", `${tag}: ${kind} dialog opens and its Close button is drawn, whole, on screen and the topmost thing`, String(vis));
        if (open) {
          await b.eval(`document.querySelector("#${id} [data-close]").click(); true`); await b.sleep(500);
          report(!(await b.eval(`document.getElementById("${id}").open`)), `${tag}: ${kind} dialog: the Close button closes it`);
          await b.eval(`(() => { const e = document.querySelector(${JSON.stringify(sel)}); e.click(); })()`); await b.sleep(700);
          await key("Escape", "Escape", 27); await b.sleep(400);
          report(!(await b.eval(`document.getElementById("${id}").open`)), `${tag}: ${kind} dialog: Escape closes it`);
        }
      }
    }
  }
  report(problems.length === 0, "no script errors on any of those pages", problems.slice(0, 2).join(" | "));
  console.log(failed ? `\n${failed} FAILED` : "\nall passed");
  process.exitCode = failed ? 1 : 0;
}
