// The admin area (Stories and Places) in a real browser: who is let in, the dashboard, the list, create with the keyboard only, validation, edit, the official-content lock, delete with its
// confirmation page, CSRF, and layout and touch size at four widths.
//   python scripts/qa/run_admin_qa.py        (starts a TEST-configured server on its own port, proves the database is a *_test one, makes its test data, then runs this)
//   QA_REDUCED_MOTION=1 python scripts/qa/run_admin_qa.py     (the visitor's system asks for reduced motion)
// This script signs in and creates, edits and deletes stories and places, so it refuses to run unless the runner has verified the server.
const BASE = process.env.TL_BASE || "http://127.0.0.1:5084";
const ADMIN = process.env.QA_ADMIN, USER = process.env.QA_USER, PASSWORD = process.env.QA_PASSWORD, OFFICIAL = process.env.QA_OFFICIAL_SLUG;
const OFFICIAL_PLACE = process.env.QA_OFFICIAL_PLACE, BLOCKED_PLACE = process.env.QA_BLOCKED_PLACE, IMPACT_PLACE = process.env.QA_IMPACT_PLACE, IMPACT_STORY = process.env.QA_IMPACT_STORY;
const PLACE_NAME = "TT QA Place " + Math.random().toString(36).slice(2, 8);
const PLACE_SLUG = "tt-qa-place-" + Math.random().toString(36).slice(2, 8);
const TITLE = "TT QA Story " + Math.random().toString(36).slice(2, 8);
const SLUG = "tt-qa-" + Math.random().toString(36).slice(2, 8);
let failed = 0;
let lastLabel = "start";
const report = (ok, label, d = "") => { lastLabel = label; if (!ok) { failed++; } console.log((ok ? "PASS  " : "FAIL  ") + label + (d ? "  (" + d + ")" : "")); };

export default async function (b) {
  if (process.env.QA_SERVER_VERIFIED !== "1" || !ADMIN || !USER) { console.log("FAIL  refusing to run: use scripts/qa/run_admin_qa.py, which verifies the database and makes the test accounts first"); process.exitCode = 1; return; }
  const problems = [];
  b.on((d) => {
    if (d.method === "Runtime.exceptionThrown") { problems.push("exception (after: " + lastLabel + "): " + (d.params.exceptionDetails.exception?.description || d.params.exceptionDetails.text)); }
    if (d.method === "Runtime.consoleAPICalled" && d.params.type === "error") { problems.push("console: " + (d.params.args || []).map((a) => a.value || a.description).join(" ")); }
    // A request the page itself made that failed. The deliberate error pages (403/400) are page responses, not failed requests, so they do not count here.
    if (d.method === "Network.loadingFailed" && !d.params.canceled) { problems.push("failed: " + d.params.errorText + " " + (d.params.type || "")); }
  });
  await b.send("Network.enable");
  const REDUCED = process.env.QA_REDUCED_MOTION === "1";
  await b.colorScheme(REDUCED);
  console.log(`INFO  mode: prefers-reduced-motion = ${REDUCED ? "reduce" : "no-preference"}`);
  await b.size(1440, 900, false);
  // textContent, not innerText: the site's headings and tags are text-transform: uppercase, which innerText would report as capitals.
  const text = async () => b.eval("document.body.textContent");
  const heading = async () => b.eval("document.querySelector('h1').textContent.trim()");
  // The branded 403 page (Stage 4A): the h1 says "Restricted area"; the code and the standard name stay in the eyebrow and the browser title. All three must be there.
  const isForbidden = async () => b.eval("(() => { const h = document.querySelector(\"h1\"), e = document.querySelector(\".error-page .eyebrow\"); return !!h && !!e && h.textContent.trim() === \"Restricted area\" && /Error 403/.test(e.textContent) && /Forbidden/.test(e.textContent) && /Forbidden/.test(document.title); })()");
  const path = async () => b.eval("location.pathname");
  const q = async (sel) => b.eval(`!!document.querySelector(${JSON.stringify(sel)})`);
  const fill = async (name, value) => b.eval(`(() => { const i = document.querySelector('[name="${name}"]'); if (!i) return false; i.value = ${JSON.stringify(value)}; return true; })()`);
  const press = async (sel) => {
    await b.eval(`window.__qaMarker = 1; document.querySelector(${JSON.stringify(sel)}).click()`);
    const t0 = Date.now();
    while (Date.now() - t0 < 20000) { await b.sleep(100); let gone = false; try { gone = await b.eval("typeof window.__qaMarker === 'undefined' && document.readyState === 'complete'"); } catch (e) { gone = false; } if (gone) { break; } }
    await b.sleep(400);
  };
  const go = async (url, wait = 900) => b.open(BASE + url, wait);
  const key = async (k, code, vk, text) => { await b.send("Input.dispatchKeyEvent", { type: "keyDown", key: k, code, windowsVirtualKeyCode: vk, ...(text ? { text } : {}) }); await b.send("Input.dispatchKeyEvent", { type: "keyUp", key: k, code, windowsVirtualKeyCode: vk }); };
  const tab = async () => key("Tab", "Tab", 9);
  const typeText = async (s) => b.send("Input.insertText", { text: s });
  // Tab (like a keyboard-only user) until the element matching `sel` has focus; returns the number of presses, or -1 if it was never reached.
  const tabTo = async (sel, max = 80) => {
    for (let n = 0; n <= max; n++) { if (await b.eval(`document.activeElement && document.activeElement.matches(${JSON.stringify(sel)})`)) { return n; } await tab(); }
    return -1;
  };
  const signIn = async (name) => {
    await go("/login");
    await fill("username", name); await fill("password", PASSWORD);
    await press("form.acct-form button[type=submit]");
  };
  const signOut = async () => {
    await go("/account/favourites");
    await b.eval("document.querySelector('[data-nav-toggle]').click()"); await b.sleep(400);
    await press("#site-menu .site-menu__linkbtn");
  };

  await go("/about", 300);                                   // warm-up: the first navigation of a fresh browser
  console.log("INFO  browser reached", await b.eval("location.href"));

  // ---- signed out
  await go("/admin");
  report((await path()) === "/login", "signed out: /admin sends you to Sign in", await path());
  await go("/admin/stories/new");
  report((await path()) === "/login", "signed out: /admin/stories/new sends you to Sign in", await path());

  // ---- an ordinary account is turned away
  await signIn(USER);
  await go("/account/favourites");
  report(!(await q("a[href='/admin']")), "ordinary account: no Admin link on the favourites page");
  await go("/admin");
  report((await path()) === "/admin" && (await isForbidden()) && (await text()).includes("administrators"), "ordinary account: /admin answers 403 (Forbidden)", await heading());
  await go("/admin/stories/new");
  report((await isForbidden()), "ordinary account: the new-story page is 403 too");
  await go(`/admin/stories/${OFFICIAL}/delete`);
  report((await isForbidden()), "ordinary account: the delete page is 403 too");
  await signOut();

  // ---- the administrator
  await signIn(ADMIN);
  await go("/account/favourites");
  report(await q("a[href='/admin']"), "administrator: the favourites page offers the Admin link");
  await press("a[href='/admin']");
  report((await path()) === "/admin" && (await heading()) === "Dashboard", "administrator: the Admin link opens the dashboard", await path());
  report((await b.eval("document.querySelectorAll('table').length")) === 4 && /Rows per table/.test(await text()) && /Most saved stories/.test(await text()), "dashboard: four tables of counts and the two lists");
  report((await b.eval("document.querySelector('.adm-table--compact tbody th').scope")) === "row" && (await b.eval("!!document.querySelector('table caption')")), "dashboard: tables have captions and row headers");

  // ---- the list
  await go("/admin/stories?per_page=50");
  report((await b.eval("document.querySelectorAll('.adm-table tbody tr').length")) >= 6, "list: the five seeded stories and the QA official story are listed");
  report(/Read-only \(official\)/.test(await b.eval(`document.querySelector('.adm-table tbody tr:has(a[href="/missions/${OFFICIAL}"])').textContent`)) && !(await q(`a[href="/admin/stories/${OFFICIAL}/edit"]`)), "list: the official story is marked read-only and has no Edit or Delete");
  await go("/admin/stories?q=harbour");
  report((await b.eval("document.querySelectorAll('.adm-table tbody tr').length")) === 1, "list: the search narrows the list");

  // ---- create, with the keyboard only
  await go("/admin/stories/new", 1000);
  report(await b.eval("document.activeElement && document.activeElement.id === 'title'"), "create: the title field has focus when the page opens");
  const unlabeled = await b.eval("[...document.querySelectorAll('form.adm-form input:not([type=hidden]), form.adm-form select, form.adm-form textarea')].filter((e) => !(e.labels && e.labels.length) && !e.getAttribute('aria-label')).map((e) => e.name)");
  report(unlabeled.length === 0, "create: every form control has a label", JSON.stringify(unlabeled));
  report(!(await q("input[name=slug][type=hidden]")) && !(await q("option[value=official]")), "create: the label list never offers 'official'");
  await typeText(TITLE);
  const toSlug = await tabTo("#slug"); await typeText(SLUG);
  const toSummary = await tabTo("#summary"); await typeText("Typed with the keyboard only.");
  const toSynopsis = await tabTo("#synopsis"); await typeText("A synopsis that was typed without touching the mouse.");
  const toChar = await tabTo("#characters__jason-duval"); await key(" ", "Space", 32, " ");
  const toNote = await tabTo("#characters_note__jason-duval"); await typeText("The driver");
  const toPlace = await tabTo("#locations__bayfront-studio-lot"); await key(" ", "Space", 32, " ");
  const toMain = await tabTo("select[name=primary_location]"); await key("ArrowDown", "ArrowDown", 40);        // the 'Main place' list is the next stop after the place checkboxes
  const mainChosen = await b.eval("document.querySelector('select[name=primary_location]').value");
  report([toSlug, toSummary, toSynopsis, toChar, toNote, toPlace, toMain].every((n) => n >= 0), "create: every control is reachable with Tab, in a sensible order (the arrow key picks the main place)", JSON.stringify([toSlug, toSummary, toSynopsis, toChar, toNote, toPlace, toMain, mainChosen]));
  report(mainChosen === "bayfront-studio-lot", "create: the arrow key chose the main place", String(mainChosen));
  const toSubmit = await tabTo("form.adm-form button[type=submit]");
  await b.eval("window.__qaMarker = 1"); await key("Enter", "Enter", 13, String.fromCharCode(13));
  for (let i = 0; i < 100; i++) { await b.sleep(100); if (await b.eval("typeof window.__qaMarker === 'undefined' && document.readyState === 'complete'")) break; }
  await b.sleep(400);
  report(toSubmit >= 0 && (await path()) === "/admin/stories" && /The story was created/.test(await text()), "create: Enter on the button creates the story and returns to the list with a message", await path());
  report((await text()).includes(TITLE), "create: the new story is in the list");
  await go(`/missions/${SLUG}`);
  report((await text()).includes(TITLE) && (await text()).includes("The driver"), "create: the public story page shows it with its character link");

  // ---- validation: errors are readable and nothing typed is lost
  await go("/admin/stories/new");
  await fill("title", "TT QA Invalid " + Math.random().toString(36).slice(2, 6)); await fill("summary", ""); await fill("synopsis", "x");
  await b.eval("document.querySelector('#characters__lucia-caminos').click()");
  await press("form.adm-form button[type=submit]");
  report((await b.eval("document.querySelector('#form-errors') && document.querySelector('#form-errors').getAttribute('role')")) === "alert" && (await b.eval("document.querySelector('#summary').getAttribute('aria-invalid')")) === "true", "validation: an error summary (role=alert) and the field are marked invalid");
  report((await b.eval("document.querySelector('#summary-note').textContent")).length > 5 && (await b.eval("document.querySelector('#title').value")).startsWith("TT QA Invalid"), "validation: the message is next to the field and the typed title is kept");
  report(await b.eval("document.querySelector('#characters__lucia-caminos').checked"), "validation: the ticked character is still ticked");
  report(/characters_note__lucia-caminos/.test(await b.eval("[...document.querySelectorAll('#form-errors a')].map((a) => a.getAttribute('href')).join(' ')").then((s) => s.replace('#', ''))), "validation: the missing role note is listed too");

  // ---- edit
  await go(`/admin/stories/${SLUG}/edit`);
  report((await b.eval("document.querySelector('#title').value")) === TITLE && (await b.eval("document.querySelector('#characters__jason-duval').checked")) && !(await q("input[name=slug]")), "edit: the form shows the current values and the slug is not editable");
  await fill("title", TITLE + " (edited)"); await b.eval("document.querySelector('#characters__jason-duval').click()"); await b.eval("document.querySelector('#vehicles__grotti-cheetah').click()");
  await fill("vehicles_note__grotti-cheetah", "The getaway car");
  await press("form.adm-form button[type=submit]");
  report((await path()) === "/admin/stories" && /The story was saved/.test(await text()) && (await text()).includes(TITLE + " (edited)"), "edit: saving returns to the list with the new title", await path());
  await go(`/missions/${SLUG}`);
  report((await text()).includes("The getaway car") && !(await text()).includes("The driver"), "edit: the public page shows the replaced links");

  // ---- the official story is locked
  await go(`/admin/stories/${OFFICIAL}/edit`);
  report((await isForbidden()), "official: its edit page is 403 for an administrator");
  await go(`/admin/stories/${OFFICIAL}/delete`);
  report((await isForbidden()), "official: its delete page is 403 for an administrator");

  // ---- CSRF: a form without its token is refused
  await go(`/admin/stories/${SLUG}/edit`);
  await b.eval("document.querySelector('form.adm-form input[name=csrf_token]').remove()");
  await press("form.adm-form button[type=submit]");
  report(/could not be checked/.test(await text()), "csrf: a form posted without its token is refused with a clear message");
  await go(`/missions/${SLUG}`);
  report((await text()).includes(TITLE + " (edited)"), "csrf: and nothing was changed");

  // ---- delete: a confirmation page first
  await go(`/admin/stories/${SLUG}/delete`);
  report((await heading()) === "Delete this story?" && /1 character link|0 character links/.test(await text()) && /1 vehicle link/.test(await text()), "delete: the page names the story and counts what would go");
  await press("a.btn--ghost[href='/admin/stories']");
  await go(`/missions/${SLUG}`);
  report((await text()).includes(TITLE + " (edited)"), "delete: 'Keep it' deletes nothing");
  await go(`/admin/stories/${SLUG}/delete`);
  await press("form.adm-actions button.adm-danger");
  report((await path()) === "/admin/stories" && /was deleted/.test(await text()), "delete: the button deletes it and returns to the list with a message", await path());
  await go(`/missions/${SLUG}`);
  report(/404|Not Found/i.test(await b.eval("document.querySelector('.eyebrow, h1').textContent")), "delete: its public page is gone (404)");

  // ======================================================================== Places
  // ---- the list
  await go("/admin/places?per_page=50");
  report((await b.eval("document.querySelectorAll('.adm-table tbody tr').length")) >= 8, "places list: the seeded places and the QA places are listed");
  report(/Read-only \(official\)/.test(await b.eval(`document.querySelector('.adm-table tbody tr:has(a[href="/locations/${OFFICIAL_PLACE}"])').textContent`)) && !(await q(`a[href="/admin/places/${OFFICIAL_PLACE}/edit"]`)), "places list: the official place is marked read-only and has no Edit or Delete");
  await go("/admin/places?q=neon");
  report((await b.eval("document.querySelectorAll('.adm-table tbody tr').length")) >= 1 && (await text()).toLowerCase().includes("neon row"), "places list: the search narrows the list");
  await go("/admin/places?region=vice-city&per_page=50");
  report(await b.eval("[...document.querySelectorAll('.adm-table tbody tr td:nth-child(2)')].every((c) => c.textContent.trim() === 'Vice City') && document.querySelectorAll('.adm-table tbody tr').length > 0"), "places list: the region filter shows only that region");

  // ---- create a place, with the keyboard only
  await go("/admin/places/new", 1000);
  report(await b.eval("document.activeElement && document.activeElement.id === 'name'"), "place create: the name field has focus when the page opens");
  const unlabeledPlace = await b.eval("[...document.querySelectorAll('form.adm-form input:not([type=hidden]), form.adm-form select, form.adm-form textarea')].filter((e) => !(e.labels && e.labels.length) && !e.getAttribute('aria-label')).map((e) => e.name)");
  report(unlabeledPlace.length === 0, "place create: every form control has a label", JSON.stringify(unlabeledPlace));
  report((await b.eval("document.querySelectorAll('#region option').length")) === 7 && !(await q("option[value=official]")), "place create: the region list offers the six regions, and the label list never offers 'official'");
  await typeText(PLACE_NAME);
  const pSlug = await tabTo("#slug"); await typeText(PLACE_SLUG);
  const pRegion = await tabTo("#region"); await key("ArrowDown", "ArrowDown", 40);
  const regionChosen = await b.eval("document.querySelector('#region').value");
  const pSummary = await tabTo("#summary"); await typeText("Typed with the keyboard only.");
  const pDescription = await tabTo("#description"); await typeText("A description that was typed without touching the mouse.");
  const pSubmit = await tabTo("form.adm-form button[type=submit]");
  report([pSlug, pRegion, pSummary, pDescription, pSubmit].every((n) => n >= 0) && regionChosen !== "", "place create: every control is reachable with Tab, and the arrow key chose a region", JSON.stringify([pSlug, pRegion, pSummary, pDescription, pSubmit, regionChosen]));
  await b.eval("window.__qaMarker = 1"); await key("Enter", "Enter", 13, String.fromCharCode(13));
  for (let i = 0; i < 100; i++) { await b.sleep(100); if (await b.eval("typeof window.__qaMarker === 'undefined' && document.readyState === 'complete'")) break; }
  await b.sleep(400);
  report((await path()) === "/admin/places" && /The place was created/.test(await text()) && (await text()).includes(PLACE_NAME), "place create: Enter on the button creates it and the list shows it with a message", await path());
  await go(`/locations/${PLACE_SLUG}`);
  report((await text()).includes(PLACE_NAME), "place create: the public place page shows it");

  // ---- validation
  await go("/admin/places/new");
  await fill("name", "ab"); await fill("summary", ""); await fill("description", "x");
  await press("form.adm-form button[type=submit]");
  report((await b.eval("document.querySelector('#form-errors') && document.querySelector('#form-errors').getAttribute('role')")) === "alert" && (await b.eval("document.querySelector('#region').getAttribute('aria-invalid')")) === "true" && (await b.eval("document.querySelector('#name').getAttribute('aria-invalid')")) === "true", "place validation: an error summary (role=alert) and the region and name fields are marked invalid");
  report((await b.eval("document.querySelector('#region-note').textContent")).length > 5 && (await b.eval("document.querySelector('#name').value")) === "ab", "place validation: the message is next to the field and what was typed is kept");

  // ---- edit (including moving to another region)
  await go(`/admin/places/${PLACE_SLUG}/edit`);
  const regionBefore = await b.eval("document.querySelector('#region').value");
  report((await b.eval("document.querySelector('#name').value")) === PLACE_NAME && regionBefore !== "" && !(await q("input[name=slug]")), "place edit: the form shows the current values and the slug is not editable");
  await fill("name", PLACE_NAME + " (edited)");
  await b.eval("(() => { const s = document.querySelector('#region'); const other = [...s.options].find((o) => o.value && o.value !== s.value); s.value = other.value; return true; })()");
  const regionAfter = await b.eval("document.querySelector('#region').value");
  await press("form.adm-form button[type=submit]");
  report((await path()) === "/admin/places" && /The place was saved/.test(await text()) && (await text()).includes(PLACE_NAME + " (edited)"), "place edit: saving returns to the list with the new name", await path());
  await go(`/admin/places/${PLACE_SLUG}/edit`);
  report((await b.eval("document.querySelector('#region').value")) === regionAfter && regionAfter !== regionBefore, "place edit: the place is now in the other region", regionBefore + " -> " + regionAfter);

  // ---- the official place is locked
  await go(`/admin/places/${OFFICIAL_PLACE}/edit`);
  report((await isForbidden()), "official place: its edit page is 403 for an administrator");
  await go(`/admin/places/${OFFICIAL_PLACE}/delete`);
  report((await isForbidden()), "official place: its delete page is 403 for an administrator");

  // ---- a place an official character lives at cannot be deleted
  await go(`/admin/places/${BLOCKED_PLACE}/delete`);
  report(/cannot be deleted/i.test(await heading()) && /official character/.test(await text()) && !(await q("button.adm-danger")), "blocked delete: the page says an official character lives there and offers no Delete button");

  // ---- CSRF
  await go(`/admin/places/${PLACE_SLUG}/edit`);
  await b.eval("document.querySelector('form.adm-form input[name=csrf_token]').remove()");
  await press("form.adm-form button[type=submit]");
  report(/could not be checked/.test(await text()), "place csrf: a form posted without its token is refused with a clear message");
  await go(`/locations/${PLACE_SLUG}`);
  report((await text()).includes(PLACE_NAME + " (edited)"), "place csrf: and nothing was changed");

  // ---- delete: the confirmation page tells the truth first
  await go(`/admin/places/${IMPACT_PLACE}/delete`);
  const impactText = await text();
  report((await heading()) === "Delete this place?" && /1 character will have no home place/.test(impactText) && /1 story link /.test(impactText) && /1 saved favourite /.test(impactText) && /1 media link /.test(impactText), "place delete: the page counts the resident, the story link, the favourite and the media link");
  await press("a.btn--ghost[href='/admin/places']");
  await go(`/locations/${IMPACT_PLACE}`);
  report(!/404|Not Found/i.test(await b.eval("document.querySelector('.eyebrow, h1').textContent")), "place delete: 'Keep it' deletes nothing");
  await go(`/admin/places/${IMPACT_PLACE}/delete`);
  await press("form.adm-actions button.adm-danger");
  report((await path()) === "/admin/places" && /was deleted/.test(await text()), "place delete: the button deletes it and returns to the list with a message", await path());
  await go(`/locations/${IMPACT_PLACE}`);
  report(/404|Not Found/i.test(await b.eval("document.querySelector('.eyebrow, h1').textContent")), "place delete: its public page is gone (404)");
  await go(`/missions/${IMPACT_STORY}`);
  report(!/404|Not Found/i.test(await b.eval("document.querySelector('.eyebrow, h1').textContent")), "place delete: the story that linked it still opens");

  // ---- layout and touch size
  await go(`/admin/stories/new`);
  await fill("title", "TT QA Layout " + Math.random().toString(36).slice(2, 6)); await fill("slug", "tt-qa-layout-" + Math.random().toString(36).slice(2, 6)); await fill("summary", "s"); await fill("synopsis", "s");
  await press("form.adm-form button[type=submit]");
  const layoutSlug = await b.eval("(document.querySelector('.adm-table tbody th a') || {}).getAttribute ? document.querySelector('.adm-table tbody .adm-slug').textContent : ''");
  for (const [W, H, mobile] of [[1440, 900, false], [820, 1180, false], [390, 844, true], [360, 740, true]]) {
    await b.size(W, H, mobile);
    for (const url of ["/admin", "/admin/stories?per_page=50", "/admin/stories/new", `/admin/stories/${layoutSlug}/edit`, `/admin/stories/${layoutSlug}/delete`, "/admin/places?per_page=50", "/admin/places/new", `/admin/places/${PLACE_SLUG}/edit`, `/admin/places/${PLACE_SLUG}/delete`, `/admin/places/${BLOCKED_PLACE}/delete`]) {
      await go(url, 900);
      const r = JSON.parse(await b.eval(`JSON.stringify((() => {
        const over = Math.max(document.documentElement.scrollWidth, document.body.scrollWidth) - innerWidth;
        const small = [...document.querySelectorAll('main a.btn, main button.btn, form.adm-form input[type=text], form.adm-form select, form.adm-form textarea, .adm-link-row label')].filter((e) => { const s = getComputedStyle(e); const p = e.getBoundingClientRect(); return s.display !== 'none' && p.width > 0 && p.height > 0 && p.height < 40 && !e.classList.contains('visually-hidden'); }).map((e) => (e.id || e.className || e.tagName) + ':' + Math.round(e.getBoundingClientRect().height));
        const off = [...document.querySelectorAll('main a, main button, main input, main select, main textarea')].filter((e) => { const p = e.getBoundingClientRect(); return p.width > 0 && (p.left < -1 || p.right > innerWidth + 1) && !e.closest('.adm-table-wrap'); }).length;
        return { over, small: small.slice(0, 4), off }; })())`));
      report(r.over <= 0 && r.small.length === 0 && r.off === 0, `${W}x${H} ${url.replace(layoutSlug, '<story>').replace(PLACE_SLUG, '<place>').replace(BLOCKED_PLACE, '<blocked place>')}: no horizontal overflow; controls on screen and at least 40px tall`, JSON.stringify(r));
    }
  }
  await b.size(1440, 900, false);
  await go(`/admin/stories/${layoutSlug}/delete`);
  await press("form.adm-actions button.adm-danger");
  report((await path()) === "/admin/stories" && !(await text()).includes(layoutSlug), "cleanup: the layout test story was deleted through the page");
  await go(`/admin/places/${PLACE_SLUG}/delete`);
  await press("form.adm-actions button.adm-danger");
  report((await path()) === "/admin/places" && !(await text()).includes(PLACE_SLUG), "cleanup: the QA place was deleted through the page");
  report(problems.length === 0, "no console, page or request errors during the whole run", problems.slice(0, 3).join(" | "));
  console.log(failed ? `\n${failed} FAILED` : "\nall passed");
  process.exitCode = failed ? 1 : 0;
}
