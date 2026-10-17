// What the Garage downloads, and whether each picture is the right size for where it is drawn.
//   NET_OUT=review/x/network-analysis.txt node scripts/qa/cdp.mjs scripts/qa/garage_network.mjs
// For each route / window / pixel density it records, from Chrome's own network events (not the resource-timing list, which hides cache hits and
// joins files whose names share a prefix):
//   * every request for a picture, with whether it went to the network, was served from the cache, or was a repeat of an earlier request;
//   * for every picture in view or near it: the width the browser chose from the srcset, the width the picture is drawn at (CSS pixels x density),
//     and the ratio between them (1.0 is exact; under 1 is soft, over 2 is a larger download than needed);
//   * a classification of every repeat: the same file asked for twice in one load is either avoidable (the page asks twice) or normal (a
//     different size of the same picture, a cached file revalidated).
import { writeFileSync } from "node:fs";
const BASE = process.env.TL_BASE || "http://127.0.0.1:5057";
const OUT = process.env.NET_OUT || "review/network-analysis.txt";
const ROUTES = ["/vehicles", "/vehicles/grotti-cheetah", "/vehicles/vapid-dominator-buggy", "/vehicles/shitzu-squalo", "/vehicles/vapid-ganado", "/vehicles/dinka-enduro", "/vehicles/crest-kayak"];
const SETUPS = [[390, 844, 3], [390, 844, 2], [820, 1180, 2], [1440, 900, 1], [1440, 900, 2], [1920, 1080, 1]];
const imw = (u) => Number((/imwidth=(\d+)/.exec(u) || [])[1] || 0);
const base = (u) => u.split("?")[0];

export default async function (b) {
  const lines = [];
  const say = (s = "") => { lines.push(s); console.log(s); };
  let reqs = [];
  b.on((d) => {
    const p = d.params || {};
    if (d.method === "Network.requestWillBeSent" && p.type === "Image") reqs.push({ id: p.requestId, url: p.request.url, t: p.timestamp, redirect: !!p.redirectResponse, initiator: p.initiator && p.initiator.type });
    if (d.method === "Network.responseReceived" && p.type === "Image") { const r = reqs.find((x) => x.id === p.requestId); if (r) { r.status = p.response.status; r.cache = p.response.fromDiskCache || p.response.fromPrefetchCache ? "cache" : "network"; r.mime = p.response.mimeType; } }
    if (d.method === "Network.loadingFinished") { const r = reqs.find((x) => x.id === p.requestId); if (r) r.bytes = p.encodedDataLength; }
  });
  await b.send("Network.enable");
  let totalAvoidable = 0;
  const worst = [];
  for (const [w, h, dpr] of SETUPS) {
    await b.send("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: dpr, mobile: w < 700 });
    await b.send("Network.clearBrowserCache");
    say(`\n=== ${w}x${h} at ${dpr}x ===`);
    for (const route of ROUTES) {
      reqs = [];
      await b.open(BASE + "/about", 100);
      reqs = [];
      await b.open(BASE + route, 3500);
      // the pictures that are in the window or near it at first load (the rest are lazy and not fetched)
      const pics = JSON.parse(await b.eval(`JSON.stringify([...document.images].filter(i => i.currentSrc && i.getClientRects().length).map(i => { const r = i.getBoundingClientRect(); const cs = getComputedStyle(i); return { src: i.currentSrc, w: r.width, h: r.height, nat: i.naturalWidth, zoom: parseFloat(cs.getPropertyValue("--z")) || 1, lazy: i.loading, cls: i.className.toString().slice(0, 24), top: Math.round(r.top) }; }))`));
      const net = reqs.filter((r) => r.cache === "network");
      const hits = reqs.filter((r) => r.cache === "cache");
      const byUrl = new Map();
      reqs.forEach((r) => byUrl.set(r.url, (byUrl.get(r.url) || 0) + 1));
      const repeats = [...byUrl].filter(([, n]) => n > 1);
      const byFile = new Map();
      net.forEach((r) => { const k = base(r.url); byFile.set(k, (byFile.get(k) || new Set()).add(imw(r.url))); });
      const sizes = [...byFile].filter(([, s]) => s.size > 1);
      const kb = Math.round(net.reduce((a, r) => a + (r.bytes || 0), 0) / 1024);
      say(`${route}: ${reqs.length} picture requests (${net.length} from the network, ${hits.length} from cache), ${kb} KB; the same address asked for more than once: ${repeats.length}; the same picture fetched at two sizes: ${sizes.length}`);
      for (const [u, n] of repeats) { const rs = reqs.filter((r) => r.url === u); say(`    REPEAT x${n} ${u.split("/").pop().slice(0, 60)} [${rs.map((r) => r.cache + "/" + r.initiator).join(", ")}]`); if (rs.filter((r) => r.cache === "network").length > 1) totalAvoidable++; }
      for (const [f, s] of sizes) say(`    TWO SIZES ${f.split("/").pop().slice(0, 50)}: ${[...s].join(" and ")} px (a different crop, or the viewer's larger copy)`);
      // size selection
      const rows = pics.filter((p) => imw(p.src)).map((p) => {
        const need = p.w * dpr;                       // the pixel width the picture is drawn at, in device pixels
        return { chosen: imw(p.src), need: Math.round(need), ratio: imw(p.src) / need, cls: p.cls, top: p.top, nat: p.nat, lazy: p.lazy, file: p.src.split("/").pop().split("?")[0].slice(0, 28) };
      });
      const visible = rows.filter((r) => r.top < h * 1.5);
      for (const r of visible) { worst.push({ route, w, dpr, ...r }); }
      const soft = visible.filter((r) => r.ratio < 0.9), big = visible.filter((r) => r.ratio > 2);
      say(`    picture sizes near the window: ${visible.length}; chosen/needed ratio min ${Math.min(...visible.map((r) => r.ratio)).toFixed(2)}, max ${Math.max(...visible.map((r) => r.ratio)).toFixed(2)}; softer than drawn (<0.9): ${soft.length}; more than twice needed (>2): ${big.length}`);
      for (const r of [...soft, ...big].slice(0, 6)) say(`      ${r.ratio < 0.9 ? "SOFT" : "BIG "} ${r.cls.padEnd(22)} ${r.file}: chose ${r.chosen}px, drawn ${r.need}px (ratio ${r.ratio.toFixed(2)}), natural ${r.nat}`);
    }
  }
  say(`\nAvoidable repeats (same address fetched from the network twice in one load): ${totalAvoidable}`);
  const ratios = worst.map((r) => r.ratio).sort((a, c) => a - c);
  const med = ratios[Math.floor(ratios.length / 2)];
  say(`Across all ${worst.length} measured pictures: chosen/needed ratio median ${med.toFixed(2)}, 10th percentile ${ratios[Math.floor(ratios.length * 0.1)].toFixed(2)}, 90th percentile ${ratios[Math.floor(ratios.length * 0.9)].toFixed(2)}`);
  writeFileSync(OUT, lines.join("\n") + "\n");
}
