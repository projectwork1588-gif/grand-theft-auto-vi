// Minimal Chrome DevTools driver with no npm dependencies (Node 22+ for the built-in WebSocket).
// Usage: node scripts/qa/cdp.mjs <script.mjs>   (the script default-exports async (b) => { ... })
// b offers size(w, h, mobile), open(url, waitMs), eval(js), shot(path, {full, clip}), colorScheme(reduced), on(handler) for protocol events, sleep(ms).
// Set CHROME_PATH to a Chrome or Edge executable if it is not in a standard location. Developer tooling only.
import { spawn } from "node:child_process";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { pathToFileURL } from "node:url";

import { existsSync } from "node:fs";
const CANDIDATES = [
  process.env.CHROME_PATH,
  "C:/Program Files/Google/Chrome/Application/chrome.exe",
  "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
  "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
  "/usr/bin/google-chrome", "/usr/bin/chromium", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
].filter(Boolean);
const CHROME = CANDIDATES.find((p) => existsSync(p));
if (!CHROME) { console.error("No Chrome or Edge found. Set CHROME_PATH."); process.exit(2); }

export async function launch() {
  const dir = mkdtempSync(join(tmpdir(), "cdp-"));
  const port = 9300 + Math.floor(Math.random() * 500);
  const proc = spawn(CHROME, [
    "--headless=new", `--remote-debugging-port=${port}`, `--user-data-dir=${dir}`,
    "--no-first-run", "--no-default-browser-check", "--hide-scrollbars", "--disable-gpu",
    "--force-device-scale-factor=1", "about:blank",
  ], { stdio: "ignore" });
  let target;
  for (let i = 0; i < 60; i++) {
    try {
      const list = await (await fetch(`http://127.0.0.1:${port}/json`)).json();
      target = list.find((t) => t.type === "page");
      if (target) break;
    } catch {}
    await new Promise((r) => setTimeout(r, 250));
  }
  if (!target) throw new Error("chrome did not start");
  const ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
  let id = 0; const pending = new Map(); const listeners = [];
  ws.onmessage = (m) => {
    const d = JSON.parse(m.data);
    if (d.id && pending.has(d.id)) { const { res, rej } = pending.get(d.id); pending.delete(d.id); d.error ? rej(new Error(d.error.message)) : res(d.result); }
    else if (d.method) listeners.forEach((l) => l(d));
  };
  const send = (method, params = {}) => new Promise((res, rej) => { const i = ++id; pending.set(i, { res, rej }); ws.send(JSON.stringify({ id: i, method, params })); });
  await send("Page.enable"); await send("Runtime.enable");
  const api = {
    send,
    async size(width, height, mobile = false) {
      await send("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile });
    },
    async colorScheme(reduced = false) {
      await send("Emulation.setEmulatedMedia", { features: [{ name: "prefers-reduced-motion", value: reduced ? "reduce" : "no-preference" }] });
    },
    async open(url, wait = 900) {
      const loaded = new Promise((res) => { const l = (d) => { if (d.method === "Page.loadEventFired") { listeners.splice(listeners.indexOf(l), 1); res(); } }; listeners.push(l); });
      await send("Page.navigate", { url });
      await Promise.race([loaded, new Promise((r) => setTimeout(r, 15000))]);
      await new Promise((r) => setTimeout(r, wait));
    },
    async eval(expr) {
      const r = await send("Runtime.evaluate", { expression: expr, awaitPromise: true, returnByValue: true });
      if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description || r.exceptionDetails.text);
      return r.result.value;
    },
    async shot(path, { full = false, clip } = {}) {
      const params = { format: "jpeg", quality: 86, captureBeyondViewport: full || !!clip };
      if (clip) params.clip = { ...clip, scale: 1 };
      if (full) {
        const m = await send("Page.getLayoutMetrics");
        const h = Math.ceil(m.cssContentSize.height), w = Math.ceil(m.cssContentSize.width);
        params.clip = { x: 0, y: 0, width: w, height: Math.min(h, 12000), scale: 1 };
      }
      const r = await send("Page.captureScreenshot", params);
      writeFileSync(path, Buffer.from(r.data, "base64"));
    },
    on(handler) { listeners.push(handler); },
    async sleep(ms) { await new Promise((r) => setTimeout(r, ms)); },
    close() { try { ws.close(); } catch {} proc.kill(); },
  };
  return api;
}

if (process.argv[2]) {
  const mod = await import(pathToFileURL(process.argv[2]).href);
  const b = await launch();
  try { await mod.default(b); } finally { b.close(); }
  process.exit(process.exitCode || 0);
}
