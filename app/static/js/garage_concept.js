// Team Valkyrie | Garage concept (Stage A.2) | progressive enhancement only. Every part works without this file:
// the index is a row of links to each vehicle's page, the collection is a plain GET form, each machine in it is one link.
(function () {
  "use strict";

  function each(list, fn) { Array.prototype.forEach.call(list, fn); }
  var LEAVE = 1000;  // how long the scene being replaced stays under the one arriving: the length of the opening frame, in step with garage_concept.css

  // run `fn` once the picture has arrived and been decoded (or after a moment, so a slow connection still gets the page)
  function whenReady(img, fn) {
    var done = false;
    var once = function () { if (!done) { done = true; fn(); } };
    if (!img) { once(); return; }
    var decode = function () { if (img.decode) { img.decode().then(once, once); } else { once(); } };
    if (img.complete && img.naturalWidth) { decode(); }
    else { img.addEventListener("load", decode, { once: true }); img.addEventListener("error", once, { once: true }); }
    window.setTimeout(once, 1200);
  }

  // a picture that cannot be fetched leaves its tinted frame, never a broken-image icon
  document.addEventListener("error", function (e) { if (e.target && e.target.classList && e.target.classList.contains("gshot")) { e.target.classList.add("is-broken"); } }, true);
  window.addEventListener("load", function () {
    each(document.querySelectorAll(".gshot"), function (img) { if (img.complete && img.naturalWidth === 0 && img.currentSrc) { img.classList.add("is-broken"); } });
  });

  // ---- The opening: choose a machine from the index ---------------------------------------------------------------
  // Nothing moves by itself: the scene changes only when the visitor asks (click, tap, the arrows, a swipe, the arrow keys).
  // The new scene opens as a frame that grows out of its own number in the index until it fills the window; the one it replaces stays beneath it.
  var stage = document.querySelector("[data-stage]");
  if (stage) {
    var panels = {};
    each(stage.querySelectorAll("[data-panel]"), function (p) { panels[p.getAttribute("data-panel")] = p; });
    var picks = [].slice.call(stage.querySelectorAll("[data-pick]"));
    var order = picks.map(function (a) { return a.getAttribute("data-pick"); });
    var live = stage.querySelector("[data-stage-live]");
    var current = (picks.filter(function (a) { return a.getAttribute("aria-current") === "true"; })[0] || picks[0]).getAttribute("data-pick");
    var heading = current;
    var requested = 0;
    var timers = {};
    stage.setAttribute("data-vehicle", current);
    each(stage.querySelectorAll("[data-ctl]"), function (c) { c.hidden = false; });   // the arrows only exist when script can make them work

    var warm = function (slug) {
      var img = panels[slug] && panels[slug].querySelector("img");
      if (img && img.loading === "lazy") { img.loading = "eager"; }
    };

    // where, as a share of the scene's picture, the frame starts: at the new machine's number in the index
    var origin = function (slug, panel) {
      var tick = stage.querySelector('[data-pick="' + slug + '"]');
      var art = panel.querySelector(".gx-art");
      if (!tick || !art) { return [96, 50]; }
      var t = tick.getBoundingClientRect(), a = art.getBoundingClientRect();
      if (!a.width || !a.height) { return [96, 50]; }
      var clamp = function (v) { return Math.max(4, Math.min(96, v)); };
      return [clamp(((t.left + t.width / 2 - a.left) / a.width) * 100), clamp(((t.top + t.height / 2 - a.top) / a.height) * 100)];
    };

    var show = function (slug) {
      var next = panels[slug];
      if (!next || (slug === current && slug === heading)) { return; }
      heading = slug;
      warm(slug);
      var token = ++requested;
      whenReady(next.querySelector("img"), function () {
        if (token !== requested || slug === current) { return; }
        Object.keys(panels).forEach(function (key) {
          var panel = panels[key];
          if (key === slug) { return; }
          window.clearTimeout(timers[key]);
          if (panel.classList.contains("is-active")) { panel.classList.add("is-leaving"); }
          panel.classList.remove("is-active");
          if (!panel.hidden) {
            timers[key] = window.setTimeout(function () { panel.hidden = true; panel.classList.remove("is-leaving"); }, LEAVE + 100);
          }
        });
        window.clearTimeout(timers[slug]);
        next.classList.remove("is-leaving");
        next.hidden = false;
        var o = origin(slug, next);
        next.style.setProperty("--ox", o[0].toFixed(1));
        next.style.setProperty("--oy", o[1].toFixed(1));
        void next.offsetWidth;                           // laid out as the small frame before it grows, so the opening can play
        next.classList.add("is-active");
        current = slug;
        stage.setAttribute("data-vehicle", slug);
        stage.setAttribute("data-plate", next.getAttribute("data-plate") || "");   // where the title of the page sits depends on the composition
        picks.forEach(function (a) {
          if (a.getAttribute("data-pick") === slug) { a.setAttribute("aria-current", "true"); } else { a.removeAttribute("aria-current"); }
        });
        var chosen = stage.querySelector('[data-pick="' + slug + '"]');                    // on a phone the index is a row that scrolls: keep the chosen name in view
        var list = chosen && chosen.closest(".gx-index__list");
        if (list && list.scrollWidth > list.clientWidth) { var cr = chosen.getBoundingClientRect(), lr = list.getBoundingClientRect(); list.scrollBy({ left: cr.left + cr.width / 2 - (lr.left + lr.width / 2), behavior: "smooth" }); }
        if (live) { live.textContent = "Showing the " + ((next.querySelector(".plate") || {}).textContent || slug); }
      });
    };
    var step = function (by) { show(order[(order.indexOf(heading) + by + order.length) % order.length]); };

    picks.forEach(function (a, i) {
      a.addEventListener("click", function (e) {
        if (e.metaKey || e.ctrlKey || e.shiftKey || e.button) { return; }   // a new tab still opens the vehicle's own page
        e.preventDefault();
        show(a.getAttribute("data-pick"));
      });
      a.addEventListener("pointerenter", function () { warm(a.getAttribute("data-pick")); });
      a.addEventListener("focus", function () { warm(a.getAttribute("data-pick")); });
      a.addEventListener("keydown", function (e) {
        var to = null;
        if (e.key === "ArrowRight" || e.key === "ArrowDown") { to = (i + 1) % picks.length; }
        if (e.key === "ArrowLeft" || e.key === "ArrowUp") { to = (i - 1 + picks.length) % picks.length; }
        if (e.key === "Home") { to = 0; }
        if (e.key === "End") { to = picks.length - 1; }
        if (to === null) { return; }
        e.preventDefault();
        picks[to].focus();
        show(order[to]);
      });
    });
    each(stage.querySelectorAll("[data-step]"), function (b) {
      b.addEventListener("click", function () { step(parseInt(b.getAttribute("data-step"), 10)); });
    });

    // a swipe across the scene moves to the next or the previous machine (touch and pen; a mouse has the index and the arrows)
    var surface = stage.querySelector("[data-surface]");
    var startX = null, startY = null;
    if (surface) {
      surface.addEventListener("pointerdown", function (e) { if (e.pointerType === "mouse") { startX = null; return; } startX = e.clientX; startY = e.clientY; });
      surface.addEventListener("pointerup", function (e) {
        if (startX === null) { return; }
        var dx = e.clientX - startX, dy = e.clientY - startY;
        startX = null;
        if (Math.abs(dx) > 56 && Math.abs(dx) > Math.abs(dy) * 1.4) { step(dx < 0 ? 1 : -1); }
      });
    }

    // once the page has settled, fetch the next scene's picture quietly (not on phones or with data saver)
    var idle = window.requestIdleCallback || function (fn) { return window.setTimeout(fn, 1500); };
    var thrifty = (navigator.connection && navigator.connection.saveData) || !window.matchMedia("(hover: hover)").matches;
    window.addEventListener("load", function () { if (!thrifty) { idle(function () { if (order[1]) { warm(order[1]); } }); } });
  }

  // ---- Leaving for a vehicle's page: the chosen picture is the one that grows into it (garage.css) ----------------
  window.addEventListener("pageswap", function (e) {
    if (!e.viewTransition || !e.activation || !e.activation.entry) { return; }
    var match = /^\/vehicles\/([a-z0-9-]+)\/?$/.exec(new URL(e.activation.entry.url).pathname);
    if (!match) { return; }
    var art = document.querySelector('.gx-m[href="/vehicles/' + match[1] + '"] .gx-pic--main') ||
              document.querySelector('.gx-scene.is-active[data-panel="' + match[1] + '"] .gx-art');
    if (art) { art.style.viewTransitionName = "vehicle-art"; }
  });

  // ---- The collection: sorting applies as soon as it is chosen ------------------------------------------------------
  each(document.querySelectorAll("[data-autosubmit]"), function (select) {
    select.addEventListener("change", function () { if (select.form) { select.form.submit(); } });
  });
})();
