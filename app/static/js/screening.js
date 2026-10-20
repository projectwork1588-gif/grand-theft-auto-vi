/* The Screening (/media): four small jobs, and the page is complete without any of them.
   1. The programme rail marks the reel you are in and keeps it in view.
   2. A picture that cannot be loaded from Rockstar is shown as an empty frame, not a broken icon.
   3. A deep link such as /media#shot-jason-duval-07 opens that picture in the site's own viewer, and the address follows the viewer as you move through the pictures.
   4. "View all N" (and a large picture that stands for its chapter) opens the viewer on the real picture link kept in the chapter's closed thumbnail sheet.
   The viewer and the trailer player are the site's own (site.js); nothing here replaces them. */
(function () {
  "use strict";
  var root = document.querySelector("[data-screening]");
  if (!root) { return; }

  // ---- 1. the programme rail
  var rail = root.querySelector("[data-rail]");
  if (rail) {
    var links = [].slice.call(rail.querySelectorAll("[data-rail-link]"));
    var targets = links.map(function (a) { return document.getElementById(a.getAttribute("data-rail-link")); });
    var current = null;
    var mark = function () {
      var line = (parseFloat(getComputedStyle(document.documentElement).getPropertyValue("--header-h")) || 72) + rail.offsetHeight + 24;
      var at = -1;
      targets.forEach(function (el, i) { if (el && el.getBoundingClientRect().top <= line) { at = i; } });
      if (at === current) { return; }
      current = at;
      links.forEach(function (a, i) {
        if (i === at) { a.setAttribute("aria-current", "true"); } else { a.removeAttribute("aria-current"); }
      });
      var list = rail.querySelector("ol");
      if (list && list.scrollWidth > list.clientWidth) {
        var a = links[Math.max(at, 0)];
        list.scrollTo({ left: at < 0 ? 0 : a.offsetLeft - (list.clientWidth - a.offsetWidth) / 2, behavior: "auto" });
      }
    };
    var queued = false;
    var onScroll = function () {
      if (queued) { return; }
      queued = true;
      requestAnimationFrame(function () { queued = false; mark(); });
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    mark();
  }

  // ---- 2. a picture Rockstar no longer serves
  var broken = function (img) {
    var holder = img.closest(".sc-tile, .sc-sheet__tile, .sc-film__poster, .sc-clip__art, .sc-open__art");
    if (holder) { holder.classList.add("is-broken"); }
  };
  [].slice.call(root.querySelectorAll("img.sc-img")).forEach(function (img) {
    if (img.complete && img.naturalWidth === 0 && img.currentSrc) { broken(img); }
    img.addEventListener("error", function () { broken(img); });
  });

  // ---- 3. deep links into the viewer
  var dialog = document.getElementById("image-dialog");
  var shown = dialog && dialog.querySelector("[data-image]");
  var caption = dialog && dialog.querySelector("[data-caption]");
  if (dialog && shown) {
    var byHref = {};
    [].slice.call(root.querySelectorAll("a[data-lightbox][id]")).forEach(function (a) { byHref[a.href] = a.id; });
    var clear = function () {
      if (location.hash) { history.replaceState(null, "", location.pathname + location.search); }
    };
    var openFromHash = function () {
      var id = location.hash.length > 1 ? decodeURIComponent(location.hash.slice(1)) : "";
      var link = id ? document.getElementById(id) : null;
      if (link && link.matches("a[data-lightbox]") && !dialog.open) {
        var chapter = link.closest(".sc-ch, .sc-section");      // a picture that is not drawn (behind "View all") still puts its chapter on the screen
        if (chapter && !link.getClientRects().length) { chapter.scrollIntoView(); }
        link.click();
      }
    };
    // "View all N" starts the viewer on the chapter's first picture, in the same group as every picture of the chapter
    [].slice.call(root.querySelectorAll("[data-open]")).forEach(function (opener) {
      opener.addEventListener("click", function (e) {
        var target = document.getElementById(opener.getAttribute("data-open"));
        if (target) { e.preventDefault(); target.click(); }
      });
    });
    // the address follows the viewer: replaceState, so Back leaves the page rather than stepping through pictures
    new MutationObserver(function () {
      var id = dialog.open ? byHref[shown.src] : null;
      if (id && location.hash !== "#" + id) { history.replaceState(null, "", "#" + id); }
    }).observe(shown, { attributes: true, attributeFilter: ["src"] });
    dialog.addEventListener("close", clear);
    shown.addEventListener("error", function () {
      if (caption && dialog.open && shown.getAttribute("src")) { caption.textContent = caption.textContent + " \u00b7 this picture could not be loaded from Rockstar"; }
    });
    // site.js attaches its click handlers during the same load: wait until it has
    document.addEventListener("DOMContentLoaded", openFromHash);
    window.addEventListener("hashchange", openFromHash);
  }
})();
