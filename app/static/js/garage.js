// Team Valkyrie | Garage (Gate 3B) | progressive enhancement only. Every Garage page works without this file:
// the lineup links open each vehicle's page, the showroom is a plain GET form, the gallery thumbnails open the full pictures.
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
  // Nothing here moves by itself: the picture changes only when the visitor asks (click, tap, or the arrow keys).
  var stage = document.querySelector("[data-stage]");
  if (stage) {
    var panels = {};
    each(stage.querySelectorAll("[data-panel]"), function (p) { panels[p.getAttribute("data-panel")] = p; });
    var picks = [].slice.call(stage.querySelectorAll("[data-pick]"));
    var live = stage.querySelector("[data-stage-live]");
    var current = (picks.filter(function (a) { return a.getAttribute("aria-current") === "true"; })[0] || picks[0]).getAttribute("data-pick");
    var timers = {};
    var requested = 0;

    var warm = function (slug) {   // ask for the picture early, so the change never waits on the network
      var panel = panels[slug];
      var img = panel && panel.querySelector("img");
      if (img && img.loading === "lazy") { img.loading = "eager"; }
    };

    var show = function (slug) {
      var next = panels[slug];
      if (!next || slug === current) { return; }
      warm(slug);
      var img = next.querySelector("img");
      var token = ++requested;
      var go = function () {
        if (token !== requested) { return; }               // a later choice has replaced this one
        Object.keys(panels).forEach(function (key) {
          var panel = panels[key];
          if (key === slug) { return; }
          panel.classList.remove("is-active");
          if (!panel.hidden) {
            window.clearTimeout(timers[key]);
            timers[key] = window.setTimeout(function () { panel.hidden = true; }, FADE + 60);
          }
        });
        window.clearTimeout(timers[slug]);
        next.hidden = false;
        void next.offsetWidth;                             // the panel must be laid out before it can fade in
        next.classList.add("is-active");
        current = slug;
        picks.forEach(function (a) {
          if (a.getAttribute("data-pick") === slug) { a.setAttribute("aria-current", "true"); } else { a.removeAttribute("aria-current"); }
        });
        if (live) { live.textContent = "Showing the " + (next.querySelector(".stage__name") || {}).textContent; }
      };
      whenReady(img, go);
    };

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
        show(picks[to].getAttribute("data-pick"));
      });
    });

    // once the page has settled, fetch the next machine's picture quietly (not on phones or with data saver: there it loads when chosen)
    var idle = window.requestIdleCallback || function (fn) { return window.setTimeout(fn, 1500); };
    var thrifty = (navigator.connection && navigator.connection.saveData) || !window.matchMedia("(hover: hover)").matches;
    window.addEventListener("load", function () {
      if (thrifty) { return; }
      idle(function () { if (picks[1]) { warm(picks[1].getAttribute("data-pick")); } });
    });
    picks.forEach(function (a) { a.addEventListener("pointerdown", function () { warm(a.getAttribute("data-pick")); }); });
  }

  // ---- Leaving for a vehicle's page: the chosen picture is the one that grows into it (see garage.css) -------------
  window.addEventListener("pageswap", function (e) {
    if (!e.viewTransition || !e.activation || !e.activation.entry) { return; }
    var match = /^\/vehicles\/([a-z0-9-]+)\/?$/.exec(new URL(e.activation.entry.url).pathname);
    if (!match) { return; }
    var art = document.querySelector('.gcard__link[href="/vehicles/' + match[1] + '"] .gcard__art') ||
              document.querySelector('.stage__panel.is-active[data-panel="' + match[1] + '"] .stage__art') ||
              document.querySelector('.gtile[href="/vehicles/' + match[1] + '"] .gtile__art');
    if (art) { art.style.viewTransitionName = "vehicle-art"; }
  });

  // ---- The showroom: sorting applies as soon as it is chosen (the Search button still works without this) --------
  each(document.querySelectorAll("[data-autosubmit]"), function (select) {
    select.addEventListener("change", function () { if (select.form) { select.form.submit(); } });
  });

  // ---- A vehicle's showcase: one large picture, the rest as thumbnails ------------------------------------------
  var viewer = document.querySelector("[data-viewer]");
  if (viewer) {
    var slides = [].slice.call(viewer.querySelectorAll("[data-slide]"));
    var thumbs = [].slice.call(viewer.querySelectorAll("[data-thumb]"));
    var lightbox = [].slice.call(viewer.querySelectorAll("[data-gallery] a[data-lightbox]"));
    var caption = viewer.querySelector("[data-caption]");
    var counter = viewer.querySelector("[data-index]");
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
        if (counter) { counter.textContent = String(to + 1); }
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
    var frame = viewer.querySelector(".viewer__frame");
    var startX = null;
    if (frame) {
      frame.addEventListener("pointerdown", function (e) { startX = e.pointerType === "mouse" ? null : e.clientX; });
      frame.addEventListener("pointerup", function (e) {
        if (startX === null) { return; }
        var dx = e.clientX - startX;
        startX = null;
        if (Math.abs(dx) > 48) { swiped = true; select(dx < 0 ? goal + 1 : goal - 1); window.setTimeout(function () { swiped = false; }, 400); }
      });
    }
  }
})();
