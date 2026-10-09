// Team Valkyrie | GTA VI fan project | progressive enhancement only. Every page works without this file.
(function () {
  "use strict";

  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // ---- Header turns solid after the hero; mobile menu toggle -----------------------------------
  var header = document.querySelector("[data-header]");
  if (header && !header.classList.contains("site-header--solid")) {
    var onScroll = function () { header.classList.toggle("is-solid", window.scrollY > 40); };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  var toggle = document.querySelector("[data-nav-toggle]");
  var nav = document.querySelector("[data-nav]");
  if (toggle && nav) {
    var setOpen = function (open) {
      toggle.setAttribute("aria-expanded", String(open));
      nav.classList.toggle("is-open", open);
      if (header) { header.classList.toggle("is-solid", open || window.scrollY > 40); }
    };
    toggle.addEventListener("click", function () { setOpen(toggle.getAttribute("aria-expanded") !== "true"); });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && toggle.getAttribute("aria-expanded") === "true") { setOpen(false); toggle.focus(); }
    });
    nav.addEventListener("click", function (e) { if (e.target.closest("a")) { setOpen(false); } });
  }

  // ---- Scroll reveal ---------------------------------------------------------------------------
  var reveals = document.querySelectorAll(".reveal");
  if (reveals.length) {
    if (reduceMotion || !("IntersectionObserver" in window)) {
      reveals.forEach(function (el) { el.classList.add("is-visible"); });
    } else {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) { entry.target.classList.add("is-visible"); io.unobserve(entry.target); }
        });
      }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
      reveals.forEach(function (el) { io.observe(el); });
    }
  }

  // ---- Official images that fail to load fall back to original artwork -------------------------
  function markBroken(img) {
    var frame = img.closest(".media");
    if (frame) { frame.classList.add("is-broken"); }
  }
  var mediaImages = document.querySelectorAll(".media__img");
  mediaImages.forEach(function (img) {
    img.addEventListener("error", function () { markBroken(img); });
  });
  // Images that failed before the listener existed. Checked after load: before that, an image whose
  // srcset has not been resolved yet can report complete with a width of zero.
  window.addEventListener("load", function () {
    mediaImages.forEach(function (img) {
      if (img.complete && img.naturalWidth === 0 && img.currentSrc) { markBroken(img); }
    });
  });

  // ---- Filters: submit when a select changes (the Apply button still works without JS) ---------
  document.querySelectorAll("form.filters select").forEach(function (select) {
    select.addEventListener("change", function () { select.form.submit(); });
  });

  // ---- Dialogs: official trailer player and image viewer ---------------------------------------
  var videoDialog = document.getElementById("video-dialog");
  var imageDialog = document.getElementById("image-dialog");

  function closeOnBackdrop(dialog) {
    dialog.addEventListener("click", function (e) { if (e.target === dialog) { dialog.close(); } });
    dialog.querySelectorAll("[data-close]").forEach(function (btn) {
      btn.addEventListener("click", function () { dialog.close(); });
    });
  }

  if (videoDialog && typeof videoDialog.showModal === "function") {
    closeOnBackdrop(videoDialog);
    var playerBox = videoDialog.querySelector("[data-player]");
    var videoCaption = videoDialog.querySelector("[data-caption]");
    videoDialog.addEventListener("close", function () { playerBox.textContent = ""; }); // stops playback
    document.querySelectorAll("[data-video]").forEach(function (trigger) {
      trigger.addEventListener("click", function () {
        var frame = document.createElement("iframe");
        frame.src = trigger.getAttribute("data-video");
        frame.title = trigger.getAttribute("data-title") || "Official video";
        frame.allow = "autoplay; fullscreen; picture-in-picture";
        playerBox.textContent = "";
        playerBox.appendChild(frame);
        videoCaption.textContent = (trigger.getAttribute("data-title") || "") + " | Official video, played from Rockstar's own player. " +
          "Copyright Rockstar Games / Take-Two Interactive.";
        videoDialog.showModal();
      });
    });
  }

  if (imageDialog && typeof imageDialog.showModal === "function") {
    closeOnBackdrop(imageDialog);
    var bigImage = imageDialog.querySelector("[data-image]");
    var imageCaption = imageDialog.querySelector("[data-caption]");
    document.querySelectorAll("a[data-lightbox]").forEach(function (link) {
      link.addEventListener("click", function (e) {
        e.preventDefault();
        bigImage.src = link.href;
        bigImage.alt = link.getAttribute("data-caption") || "";
        imageCaption.textContent = (link.getAttribute("data-caption") || "") + " | Official image, shown from Rockstar's own site. Copyright Rockstar Games / Take-Two Interactive.";
        imageDialog.showModal();
      });
    });
    imageDialog.addEventListener("close", function () { bigImage.removeAttribute("src"); });
  }
})();
