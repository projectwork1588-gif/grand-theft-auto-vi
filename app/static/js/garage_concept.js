// Team Valkyrie | Garage concept (Stage A.3) | progressive enhancement only. Every part works without this file:
// the index is a row of links to each vehicle's page, the collection is a plain GET form, each machine in it is one link.
(function () {
  "use strict";

  function each(list, fn) { Array.prototype.forEach.call(list, fn); }
  var LEAVE = 900;   // how long the scene being replaced stays under the one arriving: the length of the opening frame, in step with garage_concept.css
  var params = new URLSearchParams(window.location.search);

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

  // ---- The opening ----------------------------------------------------------------------------------------------
  // The machines take turns on their own, 01 to 07 and round to 01, each held for a few seconds, and the visitor can choose any at any time.
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

    var elapsed = 0;   // how long the scene on show has been held, in milliseconds (the automatic clock; a choice sets it back to nothing)

    var show = function (slug, auto) {
      var next = panels[slug];
      if (!next || (slug === current && slug === heading)) { return; }
      heading = slug;
      elapsed = 0;
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
        next.classList.add("is-active", "is-entering");   // the opening plays while this class is on, and leaves nothing behind when it is off
        window.setTimeout(function () { next.classList.remove("is-entering"); }, 1000);
        current = slug;
        elapsed = 0;                                     // the dwell starts when the scene is actually on show
        stage.setAttribute("data-vehicle", slug);
        stage.setAttribute("data-plate", next.getAttribute("data-plate") || "");   // where the title of the page sits depends on the composition
        picks.forEach(function (a) {
          if (a.getAttribute("data-pick") === slug) { a.setAttribute("aria-current", "true"); } else { a.removeAttribute("aria-current"); }
        });
        var chosen = stage.querySelector('[data-pick="' + slug + '"]');                    // on a phone the index is a row that scrolls: keep the chosen name in view
        var list = chosen && chosen.closest(".gx-index__list");
        if (list && list.scrollWidth > list.clientWidth) { var cr = chosen.getBoundingClientRect(), lr = list.getBoundingClientRect(); list.scrollBy({ left: cr.left + cr.width / 2 - (lr.left + lr.width / 2), behavior: "smooth" }); }
        if (live && !auto) { live.textContent = "Showing the " + ((next.querySelector(".plate") || {}).textContent || slug); }   // only a choice is announced, never the clock
        kick();
      });
    };
    var step = function (by, auto) { show(order[(order.indexOf(heading) + by + order.length) % order.length], auto); };

    // ---- the clock -------------------------------------------------------------------------------------------------
    // The scene is held for DWELL milliseconds and then the next one takes its place. The clock only runs while nothing says otherwise: the
    // visitor has paused it, a pointer or keyboard is on the scene's words, the index or the controls, the opening is off screen, the tab is
    // hidden, or the next picture has not arrived yet. It never scrolls the page.
    var dwellSeconds = parseFloat(params.get("dwell"));
    var DWELL = (dwellSeconds >= 2 && dwellSeconds <= 30 ? dwellSeconds : 5) * 1000;
    var saveData = !!(navigator.connection && navigator.connection.saveData);
    var motionOn = function () { return document.documentElement.classList.contains("motion-on"); };
    var userPaused = true;      // settled when the page is ready (the site's own script decides whether motion is on): with motion off, or on request, it starts paused; Play still works
    var holding = { pointer: false, focus: false, touchUntil: 0 };
    var visible = true;
    var rafId = 0, last = 0;
    var playBtn = stage.querySelector("[data-playpause]");

    var canRun = function () {
      return !userPaused && visible && !document.hidden && !holding.pointer && !holding.focus && performance.now() > holding.touchUntil && heading === current;
    };
    var paint = function () {
      stage.style.setProperty("--p", Math.min(1, elapsed / DWELL).toFixed(3));
      stage.classList.toggle("is-paused", userPaused);
      if (playBtn) {
        playBtn.setAttribute("aria-pressed", userPaused ? "true" : "false");
        playBtn.setAttribute("aria-label", userPaused ? "Resume the showcase" : "Pause the showcase");
      }
    };
    var frame = function (now) {
      rafId = 0;
      var dt = Math.min(100, now - last);
      last = now;
      if (canRun()) {
        elapsed += dt;
        if (elapsed >= DWELL * 0.55 && order.length > 1) { warm(order[(order.indexOf(current) + 1) % order.length]); }   // fetch only the next picture, and only when it is nearly time
        if (elapsed >= DWELL) { elapsed = 0; step(1, true); }
        paint();
      }
      if (canRun()) { rafId = window.requestAnimationFrame(frame); }
    };
    var kick = function () { if (!rafId && canRun()) { last = performance.now(); rafId = window.requestAnimationFrame(frame); } };
    window.__gxClock = function () { return { elapsed: elapsed, dwell: DWELL, userPaused: userPaused, running: !!rafId, current: current, holding: holding, visible: visible }; };

    if (playBtn) { playBtn.hidden = false; }
    paint();
    if (playBtn) {
      playBtn.addEventListener("click", function () {
        userPaused = !userPaused;
        if (!userPaused) { elapsed = 0; }
        paint();
        kick();
        if (live) { live.textContent = userPaused ? "The showcase is paused." : "The showcase is running."; }
      });
    }

    // the clock waits while a pointer is over, or focus is in, the words of the scene or the index (the pause button is part of it); a touch holds it for a few seconds
    var interactive = ".gx-copy, .gx-index";
    stage.addEventListener("pointerover", function (e) { if (e.pointerType === "mouse" && e.target.closest && e.target.closest(interactive)) { holding.pointer = true; } });
    stage.addEventListener("pointerout", function (e) {
      if (e.pointerType !== "mouse") { return; }
      var to = e.relatedTarget;
      holding.pointer = !!(to && to.closest && to.closest(interactive) && stage.contains(to));
      kick();
    });
    stage.addEventListener("pointerdown", function (e) { if (e.pointerType !== "mouse" && e.target.closest && e.target.closest(interactive)) { holding.touchUntil = performance.now() + 5000; window.setTimeout(kick, 5100); } });
    stage.addEventListener("focusin", function (e) { if (e.target.closest && e.target.closest(interactive)) { holding.focus = true; } });
    stage.addEventListener("focusout", function (e) { var to = e.relatedTarget; holding.focus = !!(to && to.closest && to.closest(interactive) && stage.contains(to)); kick(); });
    document.addEventListener("visibilitychange", kick);
    if ("IntersectionObserver" in window) {
      new IntersectionObserver(function (entries) { visible = entries[entries.length - 1].intersectionRatio >= 0.35; kick(); }, { threshold: [0, 0.35, 0.6, 1] }).observe(stage);
    }
    document.addEventListener("tv:motion", function () {          // the site's own motion switch: off pauses it, on lets it run again
      if (!motionOn()) { userPaused = true; } else if (params.get("autoplay") !== "0") { userPaused = false; elapsed = 0; }
      paint(); kick();
    });
    var settle = function () { userPaused = params.get("autoplay") === "0" || saveData || !motionOn(); paint(); kick(); };
    if (document.readyState !== "complete") { document.addEventListener("DOMContentLoaded", settle); } else { settle(); }   // after the site's own script has set the motion class (it runs just before DOMContentLoaded)

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

    // the first scene has its picture; the next is fetched only when it is nearly time (see the clock), never all seven at once
  }

  // ---- The collection --------------------------------------------------------------------------------------------
  // Everything below is decoration or convenience; without it every chapter is complete, still and readable.
  var motionOn = function () { return document.documentElement.classList.contains("motion-on"); };
  var clamp01 = function (v) { return Math.max(0, Math.min(1, v)); };

  // One shared scroll loop, running only while a stage's photograph is in the window: it sets how far the picture has travelled through the window (--dp, 0 to 1),
  // which drives the slow drift of the photograph against the scroll.
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
    var arm = function () {
      if (armed || !motionOn()) { return; }
      armed = true;
      drifting.forEach(function (el) { watch.observe(el); });
    };
    var disarm = function () {
      armed = false;
      watch.disconnect();
      seen.clear();
      drifting.forEach(function (el) { el.style.removeProperty("--dp"); });
    };
    document.addEventListener("tv:motion", function () { if (motionOn()) { arm(); schedule(); } else { disarm(); } });
    window.addEventListener("scroll", schedule, { passive: true });
    window.addEventListener("resize", schedule);
    var begin = function () { arm(); schedule(); };
    if (document.readyState !== "complete") { document.addEventListener("DOMContentLoaded", begin); } else { begin(); }   // after the site's own script has set the motion class
  }

  // The chapters as a slim index at the right edge: lit for the chapter in view, shown while the collection is on screen
  var chapterRail = document.querySelector("[data-chapter-rail]");
  var chapters = [].slice.call(document.querySelectorAll(".gx-chapter"));
  if (chapterRail && chapters.length && "IntersectionObserver" in window) {
    chapterRail.hidden = false;
    var links = {};
    each(chapterRail.querySelectorAll("a[data-for]"), function (a) { links[a.getAttribute("data-for")] = a; });
    var share = {};
    var mark = function () {
      var best = null;
      Object.keys(share).forEach(function (k) { if (share[k] > 0 && (best === null || share[k] > share[best])) { best = k; } });
      Object.keys(links).forEach(function (k) { if (k === best) { links[k].setAttribute("aria-current", "true"); } else { links[k].removeAttribute("aria-current"); } });
    };
    var chapterWatch = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { share[e.target.getAttribute("data-chapter")] = e.isIntersecting ? e.intersectionRect.height : 0; });
      mark();
    }, { threshold: [0, 0.05, 0.1, 0.25, 0.5, 0.75, 1], rootMargin: "-14% 0px -14% 0px" });
    chapters.forEach(function (c) { chapterWatch.observe(c); });
    var coll = document.querySelector(".gx-coll");
    if (coll) { new IntersectionObserver(function (entries) { chapterRail.classList.toggle("is-on", entries[entries.length - 1].isIntersecting); }, { rootMargin: "-35% 0px -10% 0px" }).observe(coll); }
  }

  // The strip of customs and classics: previous and next, the arrow keys, and a mouse drag; touch and trackpad scroll it natively
  each(document.querySelectorAll("[data-strip]"), function (railEl) {
    var wrap = railEl.closest(".gx-customs");
    var cells = [].slice.call(railEl.querySelectorAll(".gx-customs__cell"));
    var ctl = wrap && wrap.querySelector("[data-strip-ctl]");
    var now = wrap && wrap.querySelector("[data-strip-now]");
    var prev = wrap && wrap.querySelector('[data-strip-step="-1"]');
    var next = wrap && wrap.querySelector('[data-strip-step="1"]');
    if (ctl) { ctl.hidden = false; }
    var pad = function () { return parseFloat(getComputedStyle(railEl).paddingLeft || "0"); };
    var index = function () {
      var edge = railEl.scrollLeft + pad() + railEl.clientWidth * 0.3, at = 0;
      cells.forEach(function (c, i) { if (c.offsetLeft <= edge) { at = i; } });
      return at;
    };
    var sync = function () {
      var max = railEl.scrollWidth - railEl.clientWidth;
      if (now) { now.textContent = String(railEl.scrollLeft >= max - 4 ? cells.length : index() + 1); }
      if (prev) { prev.disabled = railEl.scrollLeft <= 4; }
      if (next) { next.disabled = railEl.scrollLeft >= max - 4; }
    };
    var go = function (by) {
      var to = Math.max(0, Math.min(cells.length - 1, index() + by));
      railEl.scrollTo({ left: cells[to].offsetLeft - pad(), behavior: motionOn() ? "smooth" : "auto" });
    };
    if (prev) { prev.addEventListener("click", function () { go(-1); }); }
    if (next) { next.addEventListener("click", function () { go(1); }); }
    railEl.addEventListener("scroll", sync, { passive: true });
    window.addEventListener("resize", sync);
    railEl.addEventListener("keydown", function (e) {
      if (e.key === "ArrowRight") { e.preventDefault(); go(1); }
      if (e.key === "ArrowLeft") { e.preventDefault(); go(-1); }
    });
    var down = null;
    railEl.addEventListener("pointerdown", function (e) { if (e.pointerType === "mouse" && e.button === 0) { down = { x: e.clientX, left: railEl.scrollLeft }; } });
    window.addEventListener("pointermove", function (e) {
      if (!down) { return; }
      var dx = e.clientX - down.x;
      if (Math.abs(dx) > 4) { railEl.classList.add("is-dragging"); }
      railEl.scrollLeft = down.left - dx;
    });
    window.addEventListener("pointerup", function () { down = null; window.setTimeout(function () { railEl.classList.remove("is-dragging"); }, 0); });
    sync();
  });

  // ---- Leaving for a vehicle's page: the chosen picture is the one that grows into it (garage.css) ----------------
  window.addEventListener("pageswap", function (e) {
    if (!e.viewTransition || !e.activation || !e.activation.entry) { return; }
    var match = /^\/vehicles\/([a-z0-9-]+)\/?$/.exec(new URL(e.activation.entry.url).pathname);
    if (!match) { return; }
    var href = '[href="/vehicles/' + match[1] + '"]';
    var scene = document.querySelector('.gx-scene.is-active[data-panel="' + match[1] + '"] .gx-art');
    var chapter = document.querySelector('.gx-f' + href + ' .gx-f__art') || document.querySelector('.gx-d' + href + ' .gx-d__pic') || document.querySelector('.gx-m' + href + ' .gx-pic--main');
    var onScreen = function (el) { if (!el) { return false; } var r = el.getBoundingClientRect(); return r.bottom > 0 && r.top < window.innerHeight; };
    var art = onScreen(scene) ? scene : (chapter || scene);   // the picture the visitor pressed: the opening's if it is in the window, otherwise the chapter's
    if (art) { art.style.viewTransitionName = "vehicle-art"; }
  });

  // ---- The collection: sorting applies as soon as it is chosen ------------------------------------------------------
  each(document.querySelectorAll("[data-autosubmit]"), function (select) {
    select.addEventListener("change", function () { if (select.form) { select.form.submit(); } });
  });
})();
