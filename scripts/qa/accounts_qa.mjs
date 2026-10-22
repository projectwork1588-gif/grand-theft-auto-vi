// Accounts and favourites in a real browser: register, save on all four kinds, the list, sign out, sign in again, remove, change password, CSRF and layout.
//   python scripts/qa/run_accounts_qa.py        (starts a TEST-configured server on its own port, proves the database is a *_test one, then runs this)
//   TL_BASE=http://127.0.0.1:5083 node scripts/qa/cdp.mjs scripts/qa/accounts_qa.mjs     (only against a server started that way: it CREATES accounts)
// This script creates accounts, so it refuses to run unless the server says it is the QA server (the page <meta name="qa-database"> is not used: run_accounts_qa.py is the guard).
const BASE = process.env.TL_BASE || "http://127.0.0.1:5083";
const USER = "tt_qa" + Math.random().toString(36).slice(2, 8);
const PASSWORD = "correct horse battery staple";
const NEW_PASSWORD = "another long passphrase 42";
let failed = 0;
let lastLabel = "start";
const report = (ok, label, d = "") => { lastLabel = label; if (!ok) { failed++; } console.log((ok ? "PASS  " : "FAIL  ") + label + (d ? "  (" + d + ")" : "")); };

export default async function (b) {
  if (process.env.QA_SERVER_VERIFIED !== "1") { console.log("FAIL  refusing to create accounts: run this through scripts/qa/run_accounts_qa.py, which verifies the database first"); process.exitCode = 1; return; }
  const problems = [];
  let inKnownNavigation = false, knownNavigationExceptions = 0;
  b.on((d) => {
    if (d.method === "Runtime.exceptionThrown") {
      const text = d.params.exceptionDetails.exception?.description || d.params.exceptionDetails.text || "";
      // KNOWN, PRE-EXISTING, NOT AN ACCOUNT FLOW: clicking "next vehicle" (a genuine page-to-page navigation, identical on main) makes Chrome report a browser-generated
      // ViewTransition abort in about a third of clicks. Counted and printed on its own line; ONLY while that one click is being made. Every other exception fails the run.
      if (inKnownNavigation && /ViewTransition opt-in disabled/.test(text)) { knownNavigationExceptions++; return; }
      problems.push("exception (after: " + lastLabel + "): " + text);
    }
    if (d.method === "Runtime.consoleAPICalled" && d.params.type === "error") { problems.push("console: " + (d.params.args || []).map((a) => a.value || a.description).join(" ")); }
    if (d.method === "Network.loadingFailed" && !d.params.canceled) { problems.push("failed: " + d.params.errorText + " " + (d.params.type || "")); }
  });
  await b.send("Network.enable");
  const REDUCED = process.env.QA_REDUCED_MOTION === "1";      // QA_REDUCED_MOTION=1: the visitor's system asks for reduced motion (the view-transition CSS is then off)
  await b.colorScheme(REDUCED);
  console.log(`INFO  mode: prefers-reduced-motion = ${REDUCED ? "reduce" : "no-preference"}`);
  await b.size(1440, 900, false);
  const text = async () => b.eval("document.body.innerText");
  const path = async () => b.eval("location.pathname");
  const html = async (sel) => b.eval(`(document.querySelector(${JSON.stringify(sel)}) || {}).outerHTML || ''`);
  const fill = async (name, value) => b.eval(`(() => { const i = document.querySelector('[name=${name}]'); i.value = ${JSON.stringify(value)}; return !!i; })()`);
  // Press a control and wait until the browser has really loaded the page that follows (a marker set on the old document disappears with it), instead of sleeping a fixed time.
  const press = async (sel) => {
    await b.eval(`window.__qaMarker = 1; document.querySelector(${JSON.stringify(sel)}).click()`);
    const t0 = Date.now();
    while (Date.now() - t0 < 20000) { await b.sleep(100); let gone = false; try { gone = await b.eval("typeof window.__qaMarker === 'undefined' && document.readyState === 'complete'"); } catch (e) { gone = false; } if (gone) { break; } }
    await b.sleep(400);
    return Date.now() - t0;
  };
  const submit = async (sel = "form.acct-form button[type=submit]") => press(sel);
  const go = async (url, wait = 1200) => { await b.open(BASE + url, wait); if (process.env.QA_TRACE) { console.log("TRACE", url, "->", await b.eval("location.pathname"), await b.eval("document.title")); } };

  await b.open(BASE + "/about", 300);                     // warm-up: the first navigation of a fresh browser
  console.log("INFO  browser reached", await b.eval("location.href"), "title:", await b.eval("document.title"));
  // ---- signed out: the public site is unchanged and offers the way in
  await go("/characters/jason-duval");
  report((await b.eval("!!document.querySelector('.fav a.fav__btn[href=\"/login\"]')")), "signed out: the character page offers 'Sign in to save'");
  report(!(await b.eval("!!document.querySelector('.fav form')")), "signed out: no Save form (and so no token) is rendered");
  report((await b.eval("document.cookie")) === "" , "signed out: no cookie was set by browsing");
  await go("/");
  report((await b.eval("[...document.querySelectorAll('#site-menu a')].some((a) => a.getAttribute('href') === '/login') && [...document.querySelectorAll('#site-menu a')].some((a) => a.getAttribute('href') === '/register')")), "signed out: the menu has Sign in and Create an account");
  await go("/account/favourites");
  report((await path()) === "/login", "signed out: the favourites page sends you to Sign in", await path());

  // ---- register (form posts, no script needed)
  await go("/register");
  report(await b.eval("!!document.querySelector('label[for=username]') && !!document.querySelector('label[for=password]') && document.querySelector('#password').autocomplete === 'new-password'"), "register: labelled fields with the right autocomplete");
  await fill("username", USER); await fill("password", "short"); await fill("password_confirm", "short");
  await b.eval("document.querySelectorAll('input').forEach((i) => { i.removeAttribute('minlength'); })");
  await submit();
  report((await path()) === "/register" && /at least 10/i.test(await text()) && (await b.eval("document.querySelector('[role=alert]') !== null")), "register: a short password shows a readable error (role=alert) and keeps the username", await path());
  report((await b.eval("document.querySelector('#username').value")) === USER && (await b.eval("document.querySelector('#password').value")) === "", "register: the username is kept, the password is not");
  await fill("username", USER); await fill("password", PASSWORD); await fill("password_confirm", "does not match at all");
  await b.eval("document.querySelectorAll('input').forEach((i) => { i.removeAttribute('minlength'); })");
  await submit();
  report(/not the same/i.test(await text()), "register: mismatched confirmation is explained");
  await fill("username", USER); await fill("password", PASSWORD); await fill("password_confirm", PASSWORD);
  await submit();
  report((await path()) === "/account/favourites" && (await text()).toLowerCase().includes(USER), "register: success lands on the favourites page, signed in", await path());
  report(/Your account is ready/.test(await text()), "register: a status message confirms it");
  const cookies = (await b.send("Network.getAllCookies")).cookies.filter((c) => c.name === "tv_session");
  report(cookies.length === 1 && cookies[0].httpOnly && cookies[0].sameSite === "Lax", "session cookie is HttpOnly and SameSite=Lax", JSON.stringify(cookies.map((c) => ({ httpOnly: c.httpOnly, sameSite: c.sameSite, secure: c.secure }))));
  report(!(await b.eval("document.cookie")).includes("tv_session"), "script cannot read the session cookie");

  // ---- duplicate username (a second browser context is not available, so sign out first)
  // ---- save on every kind
  const targets = [["/characters/jason-duval", "characters"], ["/vehicles/grotti-cheetah", "vehicles"], ["/locations/bayfront-studio-lot", "locations"], ["/missions/harbour-lights", "missions"]];
  for (const [url, kind] of targets) {
    await go(url);
    report(await b.eval("document.querySelector('.fav').dataset.saved === 'false'"), `${kind}: starts as Save`);
    await press(".fav form button");
    report((await path()) === url && (await b.eval("document.querySelector('.fav').dataset.saved === 'true'")) && /saved to your favourites/i.test(await text()), `${kind}: pressing Save keeps the page and shows Saved with a message`, await path());
  }
  await go("/account/favourites");
  report((await b.eval("document.querySelectorAll('.acct-list li').length")) === 4 && /4 saved/.test(await text()), "the list shows all four saved items");
  await b.open(BASE + "/account/favourites", 1200);
  report((await b.eval("document.querySelectorAll('.acct-list li').length")) === 4, "a reload shows the same four (persisted in MySQL)");

  // ---- sign out (from the menu), the page forgets the account
  await b.eval("document.querySelector('[data-nav-toggle]').click()"); await b.sleep(500);
  report((await b.eval("!!document.querySelector('#site-menu .site-menu__linkbtn')")), "the menu has a Sign out button");
  await press("#site-menu .site-menu__linkbtn");
  report((await path()) === "/" && !(await text()).toLowerCase().includes(USER), "sign out: back on the home page, account no longer shown");
  await go("/account/favourites");
  report((await path()) === "/login", "after sign out the favourites page asks for sign in");

  // ---- wrong password, then right password: everything is still there
  await fill("username", USER); await fill("password", "the wrong password!!"); await submit();
  report((await path()) === "/login" && /do not match/i.test(await text()) && (await b.eval("document.querySelector('[role=alert]') !== null")), "sign in: a wrong password gives one generic, readable error");
  await fill("username", "tt_nobody_" + USER.slice(-4)); await fill("password", "the wrong password!!"); await submit();
  report(/do not match/i.test(await text()), "sign in: an unknown username gives the same message");
  await fill("username", USER); await fill("password", PASSWORD); await submit();
  report((await path()) === "/account/favourites" && (await b.eval("document.querySelectorAll('.acct-list li').length")) === 4, "sign in again: the four favourites are still there");
  for (const [url] of targets) { await go(url, 700); if (!(await b.eval("document.querySelector('.fav').dataset.saved === 'true'"))) { report(false, "saved state after sign in: " + url); } }
  report(true, "the four pages show Saved after signing in again");

  // ---- remove from the list
  await go("/account/favourites");
  await press(".acct-list li form button");
  report((await path()) === "/account/favourites" && (await b.eval("document.querySelectorAll('.acct-list li').length")) === 3, "Remove on the list takes one off (3 left)");

  // ---- CSRF in the browser
  const noToken = await b.eval("fetch('/logout', { method: 'POST', credentials: 'same-origin' }).then((r) => r.status)");
  report(noToken === 400, "a POST without the token is refused (400)", String(noToken));
  const noTokenFav = await b.eval("fetch('/favourites/characters/jason-duval', { method: 'POST', credentials: 'same-origin' }).then((r) => r.status)");
  report(noTokenFav === 400, "saving without the token is refused (400)", String(noTokenFav));
  await go("/account/favourites", 600);
  report((await b.eval("document.querySelectorAll('.acct-list li').length")) === 3, "and nothing changed");

  // ---- Save and Remove on a vehicle page, repeatedly: the form posts, is sent back to the SAME page, and (without reduced motion) used to raise a browser-generated
  // ---- "ViewTransition" console exception. Count what the browser reports during just this loop.
  {
    const before = problems.length; let toggled = 0;
    for (let i = 1; i <= 6; i++) {
      await go("/vehicles/grotti-cheetah", 700);
      const was = await b.eval("document.querySelector('.fav').dataset.saved");
      await press(".fav form button"); toggled++;
      const now = await b.eval("document.querySelector('.fav').dataset.saved");
      if (was === now) { report(false, `vehicle page, press ${i}: the Save/Saved state did not change`, `${was} -> ${now}`); }
      await press(".fav form button"); toggled++;
    }
    const mine = problems.slice(before);
    report(mine.length === 0, `vehicle page: ${toggled} Save/Remove form posts (post, redirect to the same page) raise no console or page error [${REDUCED ? "reduced motion" : "transitions allowed"}]`, mine.slice(0, 2).join(" | "));
    await go("/account/favourites", 600);
    report((await b.eval("document.querySelectorAll('.acct-list li').length")) === 3, "after the loop the list is unchanged (3 saved)");
    // genuine navigation still works: from a vehicle to the next one (a different address, so its transition is still prepared)
    await go("/vehicles/grotti-cheetah", 900);
    const nextHref = await b.eval("(document.querySelector('.vd-next__stage') || { getAttribute: () => '' }).getAttribute('href')");
    inKnownNavigation = true;
    await press(".vd-next__stage"); await b.sleep(1500);
    inKnownNavigation = false;
    report(!!nextHref && (await path()) === nextHref && (await b.eval("!!document.querySelector('.fav')")), "navigation to the next vehicle still works", `${nextHref} -> ${await path()}`);
  }

  // ---- change password
  await go("/account/password");
  await fill("current_password", "not my password at all"); await fill("new_password", NEW_PASSWORD); await fill("new_password_confirm", NEW_PASSWORD); await submit();
  report((await path()) === "/account/password" && /not your current password/i.test(await text()), "change password: a wrong current password is refused with a message");
  await fill("current_password", PASSWORD); await fill("new_password", NEW_PASSWORD); await fill("new_password_confirm", NEW_PASSWORD); await submit();
  report((await path()) === "/account/favourites" && /password has been changed/i.test(await text()), "change password: success, still signed in");
  await b.eval("document.querySelector('[data-nav-toggle]').click()"); await b.sleep(400);
  await press("#site-menu .site-menu__linkbtn");
  await go("/login");
  await fill("username", USER); await fill("password", PASSWORD); await submit();
  report((await path()) === "/login", "after the change the old password no longer works");
  await fill("username", USER); await fill("password", NEW_PASSWORD); await submit();
  report((await path()) === "/account/favourites" && (await b.eval("document.querySelectorAll('.acct-list li').length")) === 3, "the new password works and the favourites are intact");

  // ---- layout and touch size, desktop and phone
  for (const [W, H, mobile] of [[1440, 900, false], [820, 1180, false], [390, 844, true], [360, 740, true]]) {
    await b.size(W, H, mobile);
    for (const url of ["/login", "/register", "/account/favourites", "/account/password", "/characters/jason-duval", "/vehicles/grotti-cheetah", "/locations/bayfront-studio-lot", "/missions/harbour-lights"]) {
      await go(url, 900);
      const r = JSON.parse(await b.eval(`JSON.stringify((() => { const over = Math.max(document.documentElement.scrollWidth, document.body.scrollWidth) - innerWidth;
        const fav = document.querySelector('.fav__btn'); const f = fav ? fav.getBoundingClientRect() : null;
        const btn = document.querySelector('form.acct-form button, .acct-actions .btn'); const bb = btn ? btn.getBoundingClientRect() : null;
        return { over, fav: f ? { w: Math.round(f.width), h: Math.round(f.height), inside: f.left >= 0 && f.right <= innerWidth } : null, btn: bb ? Math.round(bb.height) : null }; })())`));
      const needsFav = /\/(characters|vehicles|locations|missions)\//.test(url);
      report(r.over <= 0 && (!needsFav || (r.fav && r.fav.inside && r.fav.h >= 40)) && (r.btn === null || r.btn >= 40), `${W}x${H} ${url}: no horizontal overflow; controls on screen and a touch-sized`, JSON.stringify(r));
    }
  }
  await b.size(1440, 900, false);
  console.log(`INFO  known pre-existing issue (not caused by accounts; same on main): ${knownNavigationExceptions} ViewTransition console exception(s) during the one genuine "next vehicle" navigation [${REDUCED ? "reduced motion" : "transitions allowed"}]`);
  report(problems.length === 0, "no console, page or request errors during the whole run", problems.slice(0, 3).join(" | "));
  console.log(failed ? `\n${failed} FAILED` : "\nall passed");
  process.exitCode = failed ? 1 : 0;
}
