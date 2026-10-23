/* Command palette (Stage 4B). Ctrl/Cmd+K, "/" outside a text field, or the header Search icon opens a native <dialog>; ">" switches it to commands.
   Everything the visitor sees is built with createElement and textContent, never innerHTML. Addresses come from the server (/api/v1/search, or the commands the page
   renders) and are used only if they are a path on this site. Without JavaScript the header icon is a plain link to /search. */
(function () {
  "use strict";
  var dialog = document.getElementById("palette");
  if (!dialog || typeof dialog.showModal !== "function") { return; }
  var input = dialog.querySelector("[data-palette-input]");
  var list = dialog.querySelector("[data-palette-list]");
  var status = dialog.querySelector("[data-palette-status]");
  var allLink = dialog.querySelector("[data-palette-all]");
  var closeButton = dialog.querySelector("[data-palette-close]");
  var commandTemplate = dialog.querySelector("[data-palette-commands]");
  var searchUrl = allLink.getAttribute("href");

  var API = "/api/v1/search";
  var LIMIT = 8;
  var DEBOUNCE_MS = 120;
  var MIN_CHARS = 1;
  var CACHE_SIZE = 20;

  var commands = [];
  if (commandTemplate) {
    [].forEach.call(commandTemplate.content.querySelectorAll("li"), function (li) {
      commands.push({ name: li.getAttribute("data-name"), href: li.getAttribute("data-href"), action: li.getAttribute("data-action") });
    });
  }

  var items = [];          // what the list shows: { el, href, action }
  var active = -1;
  var lastFocus = null;
  var timer = null;
  var controller = null;
  var cache = new Map();
  var sequence = 0;

  function isLocalPath(href) { return typeof href === "string" && href.charAt(0) === "/" && href.charAt(1) !== "/" && href.charAt(1) !== "\\"; }
  function fold(text) { return String(text).toLowerCase(); }
  var pageLive = null;
  function announcePage(text) {
    if (!pageLive) { pageLive = el("p", "visually-hidden"); pageLive.setAttribute("role", "status"); pageLive.setAttribute("aria-live", "polite"); document.body.appendChild(pageLive); }
    pageLive.textContent = "";
    window.setTimeout(function () { pageLive.textContent = text; }, 30);
  }
  function announce(text) { status.textContent = ""; window.setTimeout(function () { status.textContent = text; }, 30); }

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) { node.className = className; }
    if (text !== undefined) { node.textContent = text; }
    return node;
  }

  /* text with the matching words in <mark>, built from text nodes */
  function highlight(parent, text, terms) {
    var lower = fold(text), spans = [];
    terms.forEach(function (term) {
      if (!term) { return; }
      var from = 0, at;
      while ((at = lower.indexOf(term, from)) !== -1) { spans.push([at, at + term.length]); from = at + term.length; }
    });
    spans.sort(function (a, b) { return a[0] - b[0]; });
    var merged = [];
    spans.forEach(function (s) {
      if (merged.length && s[0] <= merged[merged.length - 1][1]) { merged[merged.length - 1][1] = Math.max(merged[merged.length - 1][1], s[1]); } else { merged.push(s); }
    });
    var position = 0;
    merged.forEach(function (s) {
      if (s[0] > position) { parent.appendChild(document.createTextNode(text.slice(position, s[0]))); }
      parent.appendChild(el("mark", "", text.slice(s[0], s[1])));
      position = s[1];
    });
    if (position < text.length) { parent.appendChild(document.createTextNode(text.slice(position))); }
  }

  /* ---------------------------------------------------------------- the list */
  function clearList() { list.textContent = ""; items = []; setActive(-1); input.setAttribute("aria-expanded", "false"); }

  function setActive(index) {
    if (active >= 0 && items[active]) { items[active].el.classList.remove("is-active"); items[active].el.setAttribute("aria-selected", "false"); }
    active = index;
    if (index >= 0 && items[index]) {
      var item = items[index].el;
      item.classList.add("is-active");
      item.setAttribute("aria-selected", "true");
      input.setAttribute("aria-activedescendant", item.id);
      if (item.scrollIntoView) { item.scrollIntoView({ block: "nearest" }); }
    } else {
      input.removeAttribute("aria-activedescendant");
    }
  }

  function addItem(entry, className) {
    var li = el("li", "palette__item " + (className || ""));
    li.id = "palette-option-" + items.length;
    li.setAttribute("role", "option");
    li.setAttribute("aria-selected", "false");
    var link = el("a", "palette__link");
    link.tabIndex = -1;
    entry.build(link);
    li.appendChild(link);
    if (isLocalPath(entry.href)) { link.setAttribute("href", entry.href); }
    var record = { el: li, href: entry.href, action: entry.action };
    li.addEventListener("mousemove", function () { var i = items.indexOf(record); if (i !== active) { setActive(i); } });
    link.addEventListener("click", function (event) {
      if (entry.action) { event.preventDefault(); run(record, event); return; }
      if (event.ctrlKey || event.metaKey || event.shiftKey || event.button !== 0) { return; }     // let the browser open it elsewhere
      var target = new URL(link.href, window.location.href);
      if (target.pathname === window.location.pathname && target.search === window.location.search) { close(); }
    });
    list.appendChild(li);
    items.push(record);
  }

  function showResults(results, query) {
    clearList();
    var terms = query.split(/\s+/).map(fold).filter(Boolean);
    results.forEach(function (hit) {
      if (!isLocalPath(hit.url)) { return; }
      addItem({
        href: hit.url,
        build: function (link) {
          link.appendChild(el("span", "palette__kind", hit.kind_label));
          link.appendChild(document.createTextNode(" "));
          var main = el("span", "palette__main");
          var title = el("span", "palette__title"); highlight(title, hit.title, terms); main.appendChild(title);
          if (hit.detail) { var detail = el("span", "palette__detail"); highlight(detail, hit.detail, terms); main.appendChild(detail); }
          link.appendChild(main);
          link.appendChild(document.createTextNode(" "));
          link.appendChild(el("span", "palette__tag", hit.status_label || ""));
        },
      });
    });
    if (items.length) {
      input.setAttribute("aria-expanded", "true");
      setActive(0);
      announce(items.length + (items.length === 1 ? " result. " : " results. ") + results[0].title + ", " + results[0].kind_label + ".");
    } else {
      list.appendChild(el("li", "palette__note", "Nothing found for “" + query + "”. Press Enter to search the whole site."));
      announce("No results.");
    }
  }

  function showNote(text, speak) {
    clearList();
    list.appendChild(el("li", "palette__note", text));
    if (speak) { announce(speak); }
  }

  function showCommands(filter) {
    clearList();
    var needle = fold(filter.trim());
    commands.filter(function (c) { return !needle || fold(c.name).indexOf(needle) !== -1; }).forEach(function (c) {
      addItem({ href: c.href, action: c.action, build: function (link) { link.appendChild(el("span", "palette__kind", "Command")); link.appendChild(document.createTextNode(" ")); link.appendChild(el("span", "palette__main", c.name)); } }, "palette__item--command");
    });
    if (items.length) {
      input.setAttribute("aria-expanded", "true");
      setActive(0);
      announce(items.length + (items.length === 1 ? " command." : " commands."));
    } else {
      list.appendChild(el("li", "palette__note", "No command matches."));
      announce("No command matches.");
    }
  }

  function showQuick() {
    clearList();
    commands.filter(function (c) { return !c.action && c.href !== searchUrl; }).slice(0, 7).forEach(function (c) {
      addItem({ href: c.href, build: function (link) { link.appendChild(el("span", "palette__kind", "Go to")); link.appendChild(document.createTextNode(" ")); link.appendChild(el("span", "palette__main", c.name.replace(/^Go to /, ""))); } }, "palette__item--command");
    });
    input.setAttribute("aria-expanded", items.length ? "true" : "false");
    setActive(items.length ? 0 : -1);
    announce("Start typing to search. Type > for commands.");
  }

  /* ---------------------------------------------------------------- running things */
  function run(record, event) {
    if (!record) { return; }
    if (record.action === "motion") {
      var toggle = document.querySelector("[data-motion-toggle]");
      close();
      if (toggle) {
        toggle.click();
        announcePage("Motion and footage are now " + (toggle.getAttribute("aria-pressed") === "true" ? "on" : "off") + ".");
      }
      return;
    }
    if (!isLocalPath(record.href)) { return; }
    if (event && (event.ctrlKey || event.metaKey)) { window.open(record.href, "_blank", "noopener"); return; }
    go(record.href);
  }

  /* a link to another section of the page you are on does not reload it, so the dialog has to close itself */
  function go(href) {
    var target = new URL(href, window.location.href);
    if (target.pathname === window.location.pathname && target.search === window.location.search) { close(); }
    window.location.assign(href);
  }

  function fullSearchUrl(query) { return searchUrl + (query ? "?q=" + encodeURIComponent(query) : "") + "#results"; }

  /* ---------------------------------------------------------------- typing */
  function remember(key, value) { cache.set(key, value); if (cache.size > CACHE_SIZE) { cache.delete(cache.keys().next().value); } }

  function update() {
    var raw = input.value;
    allLink.setAttribute("href", fullSearchUrl(raw.charAt(0) === ">" ? "" : raw.trim()));
    if (timer) { window.clearTimeout(timer); timer = null; }
    if (controller) { controller.abort(); controller = null; }
    if (raw.charAt(0) === ">") { showCommands(raw.slice(1)); return; }
    var query = raw.replace(/\s+/g, " ").trim();
    if (query.length < MIN_CHARS) { showQuick(); return; }
    if (cache.has(query)) { showResults(cache.get(query), query); return; }
    timer = window.setTimeout(function () { search(query); }, DEBOUNCE_MS);
  }

  function search(query) {
    var mine = ++sequence;
    controller = typeof AbortController === "function" ? new AbortController() : null;
    var url = API + "?limit=" + LIMIT + "&q=" + encodeURIComponent(query);
    window.fetch(url, { headers: { Accept: "application/json" }, credentials: "same-origin", signal: controller ? controller.signal : undefined })
      .then(function (response) {
        if (response.status === 400) { return { results: [] }; }                // a query the server will not take (too many words): the page says why
        if (!response.ok) { throw new Error("search failed"); }
        return response.json();
      })
      .then(function (body) {
        if (mine !== sequence || input.value.charAt(0) === ">") { return; }
        remember(query, body.results || []);
        showResults(body.results || [], query);
      })
      .catch(function (error) {
        if (error && error.name === "AbortError") { return; }
        if (mine !== sequence) { return; }
        showNote("Search is not available right now. Press Enter to use the search page.", "Search is not available.");
      });
  }

  /* ---------------------------------------------------------------- open and close */
  function open(trigger) {
    if (dialog.open) { return; }
    lastFocus = trigger || document.activeElement;
    dialog.showModal();
    input.value = "";
    update();
    input.focus();
  }

  function close() {
    if (dialog.open) { dialog.close(); }
  }

  dialog.addEventListener("close", function () {
    if (timer) { window.clearTimeout(timer); timer = null; }
    if (controller) { controller.abort(); controller = null; }
    sequence++;
    var back = lastFocus && document.contains(lastFocus) && typeof lastFocus.focus === "function" ? lastFocus : document.querySelector("[data-palette-open]");
    if (back) { back.focus(); }
    lastFocus = null;
  });

  dialog.addEventListener("click", function (event) { if (event.target === dialog) { close(); } });       // a click on the backdrop
  closeButton.addEventListener("click", close);
  input.addEventListener("input", update);

  input.addEventListener("keydown", function (event) {
    if (event.isComposing) { return; }
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      if (!items.length) { return; }
      event.preventDefault();
      var step = event.key === "ArrowDown" ? 1 : -1;
      setActive((active + step + items.length) % items.length);
    } else if (event.key === "Enter") {
      event.preventDefault();
      if (active >= 0 && items[active]) { run(items[active], event); return; }
      var raw = input.value.trim();
      if (raw && raw.charAt(0) !== ">") { go(fullSearchUrl(raw.replace(/\s+/g, " "))); }
    }
  });

  /* ---------------------------------------------------------------- the ways in */
  function editable(target) {
    if (!target || !target.tagName) { return false; }
    var tag = target.tagName.toLowerCase();
    return tag === "input" || tag === "textarea" || tag === "select" || target.isContentEditable || target.getAttribute("role") === "textbox";
  }
  function otherModalOpen() { return [].some.call(document.querySelectorAll("dialog[open]"), function (d) { return d !== dialog; }); }

  document.addEventListener("keydown", function (event) {
    if (event.defaultPrevented || event.isComposing) { return; }
    var key = event.key;
    if ((event.ctrlKey || event.metaKey) && !event.altKey && !event.shiftKey && key && key.toLowerCase() === "k") {
      if (otherModalOpen()) { return; }
      event.preventDefault();                                   // browsers use Ctrl+K for their own search or address bar
      if (dialog.open) { close(); } else { open(document.activeElement); }
    } else if (key === "/" && !event.ctrlKey && !event.metaKey && !event.altKey && !dialog.open && !editable(event.target) && !otherModalOpen()) {
      event.preventDefault();
      open(document.activeElement);
    }
  });

  [].forEach.call(document.querySelectorAll("[data-palette-open]"), function (trigger) {
    trigger.addEventListener("click", function (event) {
      if (event.ctrlKey || event.metaKey || event.shiftKey || event.button !== 0) { return; }            // a new tab still goes to /search
      event.preventDefault();
      open(trigger);
    });
  });
}());
