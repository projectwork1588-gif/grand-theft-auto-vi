// Team Valkyrie | /regions | progressive enhancement only. Every region is a plain section with plain links, and every picture is a plain link to its full size;
// nothing here is needed to read or use a page. This adds one thing, on the landing: a compact index that appears once the opening has scrolled away and marks the
// region in view.
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
})();
