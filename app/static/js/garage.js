// Team Valkyrie | Garage (Gate 3B) | progressive enhancement only. Every Garage page works without this file:
// the lineup links open each vehicle's page, the collection is a plain GET form, the showcase pictures open full size.
(function () {
  "use strict";

  function each(list, fn) { Array.prototype.forEach.call(list, fn); }
  var FADE = 640; // the longest crossfade, in step with --dur-3; the old picture is taken away a moment after it

  // run `fn` once the picture has arrived and been decoded (or after a moment, so a slow connection still gets the page): a panel
  // is never shown as a blank frame while its picture is still being prepared
  function whenReady(img, fn) {
    var done = false;
    var once = function () { if (!done) { done = true; fn(); } };
    if (!img) { once(); return; }
    var decode = function () { if (img.decode) { img.decode().then(once, once); } else { once(); } };
    if (img.complete && img.naturalWidth) { decode(); }
    else { img.addEventListener("load", decode, { once: true }); img.addEventListener("error", once, { once: true }); }
    window.setTimeout(once, 1200);
  }

  // ---- A picture that cannot be fetched leaves its tinted frame, never a broken-image icon -----------------------
  function markBroken(img) { img.classList.add("is-broken"); }
  document.addEventListener("error", function (e) { if (e.target && e.target.classList && e.target.classList.contains("gshot")) { markBroken(e.target); } }, true);
  window.addEventListener("load", function () {
    each(document.querySelectorAll(".gshot"), function (img) { if (img.complete && img.naturalWidth === 0 && img.currentSrc) { markBroken(img); } });
  });

  // ---- The opening: pick a machine from the lineup --------------------------------------------------------------
  // Nothing here moves by itself: the picture changes only when the visitor asks (click, tap, the arrows, a swipe, the arrow keys).
  var stage = document.querySelector("[data-stage]");
  if (stage) {
    var panels = {};
    each(stage.querySelectorAll("[data-panel]"), function (p) { panels[p.getAttribute("data-panel")] = p; });
    var picks = [].slice.call(stage.querySelectorAll("[data-pick]"));
    var order = picks.map(function (a) { return a.getAttribute("data-pick"); });
    var live = stage.querySelector("[data-stage-live]");
    var counter = stage.querySelector("[data-count]");
    var controls = stage.querySelector("[data-ctl]");
    var current = (picks.filter(function (a) { return a.getAttribute("aria-current") === "true"; })[0] || picks[0]).getAttribute("data-pick");
    var timers = {};
    var requested = 0;
    var heading = current;                                // where the opening is heading: a second click counts from here, not from where it still is
    stage.setAttribute("data-vehicle", current);          // the lineup's lit line takes the tint of the machine on show
    if (controls) { controls.hidden = false; }            // the arrows only exist when script can make them work

    var warm = function (slug) {   // ask for the picture early, so the change never waits on the network
      var panel = panels[slug];
      var img = panel && panel.querySelector("img");
      if (img && img.loading === "lazy") { img.loading = "eager"; }
    };

    var show = function (slug, direction) {
      var next = panels[slug];
      if (!next || (slug === current && slug === heading)) { return; }
      heading = slug;
      warm(slug);
      var img = next.querySelector("img");
      var token = ++requested;
      var dir = direction || (order.indexOf(slug) > order.indexOf(current) ? 1 : -1);
      var go = function () {
        if (token !== requested) { return; }               // a later choice has replaced this one
        if (slug === current) { return; }
        Object.keys(panels).forEach(function (key) {
          var panel = panels[key];
          if (key === slug) { return; }
          if (panel.classList.contains("is-active")) { panel.style.setProperty("--from", (dir * -3) + "%"); }   // the one leaving drifts the other way
          panel.classList.remove("is-active");
          if (!panel.hidden) {
            window.clearTimeout(timers[key]);
            timers[key] = window.setTimeout(function () { panel.hidden = true; }, FADE + 60);
          }
        });
        window.clearTimeout(timers[slug]);
        next.style.setProperty("--from", (dir * 3) + "%");  // the one arriving comes in from the side it was chosen from
        next.hidden = false;
        void next.offsetWidth;                             // the panel must be laid out before it can fade in
        next.classList.add("is-active");
        current = slug;
        stage.setAttribute("data-vehicle", slug);
        picks.forEach(function (a) {
          if (a.getAttribute("data-pick") === slug) { a.setAttribute("aria-current", "true"); } else { a.removeAttribute("aria-current"); }
        });
        if (counter) { counter.textContent = ("0" + (order.indexOf(slug) + 1)).slice(-2); }
        if (live) { live.textContent = "Showing the " + ((next.querySelector(".plate") || {}).textContent || slug); }
      };
      whenReady(img, go);
    };
    var step = function (by) { show(order[(order.indexOf(heading) + by + order.length) % order.length], by > 0 ? 1 : -1); };

    picks.forEach(function (a, i) {
      a.addEventListener("click", function (e) {
        if (e.metaKey || e.ctrlKey || e.shiftKey || e.button) { return; }   // a new tab still opens the vehicle's own page
        e.preventDefault();
        show(a.getAttribute("data-pick"));
      });
      a.addEventListener("pointerenter", function () { warm(a.getAttribute("data-pick")); });
      a.addEventListener("focus", function () { warm(a.getAttribute("data-pick")); });
      a.addEventListener("pointerdown", function () { warm(a.getAttribute("data-pick")); });
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

    // a swipe across the picture moves to the next or the previous machine (touch and pen; a mouse has the arrows)
    var surface = stage.querySelector(".cine__panels");
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

    // a little depth where there is a pointer: the picture and the numeral drift a few pixels against it (the CSS decides whether that happens at all)
    var frameId = 0;
    stage.addEventListener("pointermove", function (e) {
      if (e.pointerType !== "mouse" || frameId) { return; }
      frameId = window.requestAnimationFrame(function () {
        frameId = 0;
        var box = stage.getBoundingClientRect();
        stage.style.setProperty("--mx", (((e.clientX - box.left) / box.width) * 2 - 1).toFixed(3));
        stage.style.setProperty("--my", (((e.clientY - box.top) / box.height) * 2 - 1).toFixed(3));
      });
    });

    // once the page has settled, fetch the next machine's picture quietly (not on phones or with data saver: there it loads when chosen)
    var idle = window.requestIdleCallback || function (fn) { return window.setTimeout(fn, 1500); };
    var thrifty = (navigator.connection && navigator.connection.saveData) || !window.matchMedia("(hover: hover)").matches;
    window.addEventListener("load", function () {
      if (thrifty) { return; }
      idle(function () { if (order[1]) { warm(order[1]); } });
    });
  }

  // ---- Leaving for a vehicle's page: the chosen picture is the one that grows into it (see garage.css) -------------
  window.addEventListener("pageswap", function (e) {
    if (!e.viewTransition || !e.activation || !e.activation.entry) { return; }
    var match = /^\/vehicles\/([a-z0-9-]+)\/?$/.exec(new URL(e.activation.entry.url).pathname);
    if (!match) { return; }
    var art = document.querySelector('.tile__link[href="/vehicles/' + match[1] + '"] .tile__art') ||
              document.querySelector('.scene.is-active[data-panel="' + match[1] + '"] .scene__art') ||
              document.querySelector('.neighbour[href="/vehicles/' + match[1] + '"] .neighbour__art');
    if (art) { art.style.viewTransitionName = "vehicle-art"; }
  });

  // ---- The collection: sorting applies as soon as it is chosen (pressing Enter in the search box still submits without this) ----
  each(document.querySelectorAll("[data-autosubmit]"), function (select) {
    select.addEventListener("change", function () { if (select.form) { select.form.submit(); } });
  });

  // ---- A vehicle's showcase viewer: one large picture, the rest as thumbnails ------------------------------------
  var viewer = document.querySelector("[data-viewer]");
  if (viewer) {
    var slides = [].slice.call(viewer.querySelectorAll("[data-slide]"));
    var thumbs = [].slice.call(viewer.querySelectorAll("[data-thumb]"));
    var lightbox = [].slice.call(viewer.querySelectorAll("[data-gallery] a[data-lightbox]"));
    var caption = viewer.querySelector("[data-caption]");
    var index = viewer.querySelector("[data-index]");
    var at = 0;
    var hideTimer = null;

    var wanted = 0;
    var goal = 0;                                       // where the viewer is heading: a second click counts from here, not from where it still is
    var select = function (n) {
      var to = (n + slides.length) % slides.length;
      if (to === goal && goal === at) { return; }
      goal = to;
      var next = slides[to];
      var img = next.querySelector("img");
      if (img && img.loading === "lazy") { img.loading = "eager"; }
      var token = ++wanted;
      var swap = function () {
        if (token !== wanted || to === at) { return; }
        var from = slides[at];
        window.clearTimeout(hideTimer);
        slides.forEach(function (s) { if (s !== next && s !== from && !s.hidden) { s.hidden = true; s.classList.remove("is-active"); } });
        next.hidden = false;
        void next.offsetWidth;
        next.classList.add("is-active");
        from.classList.remove("is-active");
        hideTimer = window.setTimeout(function () { from.hidden = true; }, FADE + 60);
        thumbs.forEach(function (t, i) { if (i === to) { t.setAttribute("aria-current", "true"); } else { t.removeAttribute("aria-current"); } });
        if (caption && img) { caption.textContent = img.getAttribute("alt") || ""; }
        if (index) { index.textContent = String(to + 1); }
        at = to;
      };
      whenReady(img, swap);
    };

    thumbs.forEach(function (t, i) {
      t.addEventListener("click", function (e) { e.preventDefault(); select(i); });
      t.addEventListener("pointerenter", function () { var im = slides[i].querySelector("img"); if (im && im.loading === "lazy") { im.loading = "eager"; } });
    });
    var prev = viewer.querySelector("[data-prev]");
    var nextBtn = viewer.querySelector("[data-next]");
    if (prev) { prev.addEventListener("click", function () { select(goal - 1); }); }
    if (nextBtn) { nextBtn.addEventListener("click", function () { select(goal + 1); }); }
    viewer.addEventListener("keydown", function (e) {
      if (e.key === "ArrowLeft") { e.preventDefault(); select(goal - 1); }
      if (e.key === "ArrowRight") { e.preventDefault(); select(goal + 1); }
    });

    // the large picture opens the site's own image viewer (full size, previous/next, Esc), starting at this picture
    var open = viewer.querySelector("[data-open]");
    var swiped = false;
    if (open && lightbox.length) { open.addEventListener("click", function () { if (swiped) { swiped = false; return; } lightbox[at].click(); }); }

    // a swipe on the picture moves to the next or previous one
    var surface2 = viewer.querySelector(".viewer__frame");
    var sx = null;
    if (surface2) {
      surface2.addEventListener("pointerdown", function (e) { sx = e.pointerType === "mouse" ? null : e.clientX; });
      surface2.addEventListener("pointerup", function (e) {
        if (sx === null) { return; }
        var dx = e.clientX - sx;
        sx = null;
        if (Math.abs(dx) > 48) { swiped = true; select(dx < 0 ? goal + 1 : goal - 1); window.setTimeout(function () { swiped = false; }, 400); }
      });
    }
  }
})();
