// Team Valkyrie | the seven vehicle pages (Stage B) | progressive enhancement only. Every part of the page works without this file:
// every picture is a link to its full size, the viewer shows its first picture and lists the rest as links, the next machine is a plain link.
(function () {
  "use strict";

  function each(list, fn) { Array.prototype.forEach.call(list, fn); }
  var FADE = 640;   // the longest crossfade of the viewer, in step with the stylesheet
  var motionOn = function () { return document.documentElement.classList.contains("motion-on"); };
  var clamp01 = function (v) { return Math.max(0, Math.min(1, v)); };

  // run `fn` once the picture has arrived and been decoded (or after a moment on a slow link): a slide is never shown as a blank frame
  function whenReady(img, fn) {
    var done = false;
    var once = function () { if (!done) { done = true; fn(); } };
    if (!img) { once(); return; }
    var decode = function () { if (img.decode) { img.decode().then(once, once); } else { once(); } };
    if (img.complete && img.naturalWidth) { decode(); }
    else { img.addEventListener("load", decode, { once: true }); img.addEventListener("error", once, { once: true }); }
    window.setTimeout(once, 8000);
  }

  // a picture that cannot be fetched leaves its tinted frame, never a broken-image icon
  document.addEventListener("error", function (e) { if (e.target && e.target.classList && e.target.classList.contains("gshot")) { e.target.classList.add("is-broken"); } }, true);
  window.addEventListener("load", function () {
    each(document.querySelectorAll(".gshot"), function (img) { if (img.complete && img.naturalWidth === 0 && img.currentSrc) { img.classList.add("is-broken"); } });
  });

  // ---- The viewer: one large picture, the rest as thumbnails -------------------------------------------------------
  var viewer = document.querySelector("[data-viewer]");
  if (viewer) {
    var slides = [].slice.call(viewer.querySelectorAll("[data-slide]"));
    var thumbs = [].slice.call(viewer.querySelectorAll("[data-thumb]"));
    var lightbox = [].slice.call(viewer.querySelectorAll("[data-gallery] a[data-lightbox]"));
    var caption = viewer.querySelector("[data-caption]");
    var index = viewer.querySelector("[data-index]");
    var captions = [];
    try { captions = JSON.parse(caption.getAttribute("data-captions") || "[]"); } catch (e) { captions = []; }
    var at = 0, goal = 0, wanted = 0, hideTimer = null;

    var select = function (n) {
      var to = (n + slides.length) % slides.length;
      if (to === goal && goal === at) { return; }
      goal = to;
      var next = slides[to];
      var img = next.querySelector("img");
      if (img && img.loading === "lazy") { img.loading = "eager"; }
      var token = ++wanted;
      thumbs.forEach(function (t, i) { if (i === to) { t.setAttribute("aria-current", "true"); } else { t.removeAttribute("aria-current"); } });   // the thumbnail answers at once
      whenReady(img, function () {
        if (token !== wanted || to === at) { return; }
        var from = slides[at];
        window.clearTimeout(hideTimer);
        slides.forEach(function (s) { if (s !== next && s !== from && !s.hidden) { s.hidden = true; s.classList.remove("is-active"); } });
        next.hidden = false;
        void next.offsetWidth;
        next.classList.add("is-active");
        from.classList.remove("is-active");
        hideTimer = window.setTimeout(function () { from.hidden = true; }, FADE + 60);
        if (caption) { caption.textContent = captions[to] || (img && img.getAttribute("alt")) || ""; }
        if (index) { index.textContent = String(to + 1); }
        at = to;
      });
    };
    thumbs.forEach(function (t, i) {
      t.addEventListener("click", function (e) { e.preventDefault(); select(i); });
      t.addEventListener("pointerenter", function () { var im = slides[i].querySelector("img"); if (im && im.loading === "lazy") { im.loading = "eager"; } });
    });
    var prev = viewer.querySelector("[data-prev]"), nextBtn = viewer.querySelector("[data-next]");
    if (prev) { prev.addEventListener("click", function () { select(goal - 1); }); }
    if (nextBtn) { nextBtn.addEventListener("click", function () { select(goal + 1); }); }
    viewer.addEventListener("keydown", function (e) {
      if (e.key === "ArrowLeft") { e.preventDefault(); select(goal - 1); }
      if (e.key === "ArrowRight") { e.preventDefault(); select(goal + 1); }
    });
    // the large picture opens the site's own image viewer (full size, previous and next, Esc), starting at this picture
    var open = viewer.querySelector("[data-open]");
    var swiped = false;
    if (open && lightbox.length) { open.addEventListener("click", function () { if (swiped) { swiped = false; return; } lightbox[at].click(); }); }
    // a swipe on the picture moves to the next or the previous one
    var frame = viewer.querySelector(".vd-viewer__frame");
    var sx = null;
    if (frame) {
      frame.addEventListener("pointerdown", function (e) { sx = e.pointerType === "mouse" ? null : e.clientX; });
      frame.addEventListener("pointerup", function (e) {
        if (sx === null) { return; }
        var dx = e.clientX - sx;
        sx = null;
        if (Math.abs(dx) > 48) { swiped = true; select(dx < 0 ? goal + 1 : goal - 1); window.setTimeout(function () { swiped = false; }, 400); }
      });
    }
  }

  // ---- The slow drift of a picture against the scroll (--dp, 0 to 1), only while it is in the window and only when motion is allowed ------------------
  var drifting = [].slice.call(document.querySelectorAll("[data-drift]"));
  var seen = new Set();
  var frameId = 0;
  var update = function () {
    frameId = 0;
    var vh = window.innerHeight || 800;
    seen.forEach(function (el) {
      var r = el.getBoundingClientRect();
      el.style.setProperty("--dp", clamp01((vh - r.top) / (vh + r.height)).toFixed(3));
    });
  };
  var schedule = function () { if (!frameId && seen.size) { frameId = window.requestAnimationFrame(update); } };
  if ("IntersectionObserver" in window && drifting.length) {
    var watch = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { if (e.isIntersecting) { seen.add(e.target); } else { seen.delete(e.target); } });
      schedule();
    }, { rootMargin: "80px 0px" });
    var armed = false;
    var arm = function () { if (armed || !motionOn()) { return; } armed = true; drifting.forEach(function (el) { watch.observe(el); }); };
    var disarm = function () { armed = false; watch.disconnect(); seen.clear(); drifting.forEach(function (el) { el.style.removeProperty("--dp"); }); };
    document.addEventListener("tv:motion", function () { if (motionOn()) { arm(); schedule(); } else { disarm(); } });
    window.addEventListener("scroll", schedule, { passive: true });
    window.addEventListener("resize", schedule);
    var begin = function () { arm(); schedule(); };
    if (document.readyState !== "complete") { document.addEventListener("DOMContentLoaded", begin); } else { begin(); }   // after the site's own script has set the motion class
  }

  // ---- Leaving for the next machine: its picture is the one that grows into that page's opening (Chrome's cross-document view transitions) ---------
  window.addEventListener("pageswap", function (e) {
    if (!e.viewTransition || !e.activation || !e.activation.entry) { return; }
    var next = document.querySelector(".vd-next__stage");
    if (!next) { return; }
    var target = new URL(e.activation.entry.url).pathname;
    var hero = document.querySelector(".vd-hero__art");
    if (new URL(next.href, location.href).pathname === target) {
      var art = next.querySelector(".vd-next__art");
      if (hero) { hero.style.viewTransitionName = "none"; }
      if (art) { art.style.viewTransitionName = "vehicle-art"; }
    }
  });
})();
