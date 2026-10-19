// Team Valkyrie | /regions | progressive enhancement only. Every region is a plain section with plain links, and every picture is a plain link to its full size;
// nothing here is needed to read or use a page. This adds two things: on the landing, a compact index that appears once the opening has scrolled away and marks the
// region in view; on a region whose pictures are a reel, buttons, a count and a progress line for the row that already scrolls and takes the arrow keys.
(function () {
  "use strict";

  // ---- The landing's compact index -------------------------------------------------------------------------------------------
  var bar = document.querySelector("[data-jump-bar]");
  var intro = document.querySelector(".rg-intro");
  var sections = [].slice.call(document.querySelectorAll("[data-feature]"));
  if (bar && intro && sections.length) {
    var links = [].slice.call(bar.querySelectorAll("[data-jump]"));
    bar.hidden = false;
    var mark = function (slug) {
      links.forEach(function (a) {
        if (a.getAttribute("data-jump") === slug) { a.setAttribute("aria-current", "true"); } else { a.removeAttribute("aria-current"); }
      });
    };
    if (!("IntersectionObserver" in window)) {
      bar.classList.add("is-on");
    } else {
      // shown from the moment the opening is mostly behind the reader until the closing note
      var state = { intro: true, end: false };
      var show = function () { bar.classList.toggle("is-on", !state.intro && !state.end); };
      new IntersectionObserver(function (entries) {
        entries.forEach(function (e) { state.intro = e.intersectionRatio > 0.55; });
        show();
      }, { threshold: [0, 0.55, 1] }).observe(intro);
      var closing = document.querySelector(".rg-source");
      if (closing) {
        new IntersectionObserver(function (entries) {
          entries.forEach(function (e) { state.end = e.isIntersecting; });
          show();
        }, { threshold: 0 }).observe(closing);
      }
      var spy = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) { if (e.isIntersecting) { mark(e.target.getAttribute("data-feature")); } });
      }, { rootMargin: "-45% 0px -50% 0px" });
      sections.forEach(function (s) { spy.observe(s); });
    }
  }

  // ---- A region's reel of pictures -------------------------------------------------------------------------------------------
  var reel = document.querySelector("[data-reel]");
  if (reel) {
    var track = reel.querySelector("[data-reel-track]");
    var ctl = reel.querySelector("[data-reel-ctl]");
    var now = reel.querySelector("[data-reel-now]");
    var fill = reel.querySelector("[data-reel-bar]");
    var slides = [].slice.call(track.children);
    if (track && ctl && slides.length) {
      ctl.hidden = false;
      var current = function () {
        var mid = track.scrollLeft + track.clientWidth / 2, best = 0, gap = Infinity;
        slides.forEach(function (s, i) {
          var d = Math.abs(s.offsetLeft + s.offsetWidth / 2 - mid);
          if (d < gap) { gap = d; best = i; }
        });
        return best;
      };
      var update = function () {
        var i = current();
        if (now) { now.textContent = String(i + 1); }
        var max = track.scrollWidth - track.clientWidth;
        if (fill) { fill.style.setProperty("--dp", String(max > 0 ? Math.max(0.05, track.scrollLeft / max) : 1)); }
      };
      var go = function (n) {
        var to = Math.max(0, Math.min(slides.length - 1, n));
        var s = slides[to];
        var behavior = document.documentElement.classList.contains("motion-on") ? "smooth" : "auto";
        track.scrollTo({ left: s.offsetLeft - (track.clientWidth - s.offsetWidth) / 2, behavior: behavior });
      };
      [].forEach.call(ctl.querySelectorAll("[data-reel-step]"), function (btn) {
        btn.addEventListener("click", function () { go(current() + parseInt(btn.getAttribute("data-reel-step"), 10)); });
      });
      track.addEventListener("scroll", function () { window.requestAnimationFrame(update); }, { passive: true });
      window.addEventListener("resize", update);
      update();
    }
  }
})();
