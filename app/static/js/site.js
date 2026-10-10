// Team Valkyrie | GTA VI fan guide | progressive enhancement only. Every page works without this file.
(function () {
  "use strict";

  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var saveData = !!(navigator.connection && navigator.connection.saveData);
  var calm = reduceMotion || saveData; // no autoplaying video; the user can still press play
  var coarse = window.matchMedia("(hover: none)").matches;

  function ready(el) { return el && typeof el.play === "function"; }
  function safePlay(video) {
    if (!ready(video)) { return; }
    var p = video.play();
    if (p && typeof p.catch === "function") { p.catch(function () { /* blocked or interrupted: the still image stays */ }); }
  }

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

  // ---- Hero: the picture drifts slower than the page, the lockup fades as you leave -------------
  var heroBg = document.querySelector("[data-hero-bg]");
  var heroContent = document.querySelector("[data-hero-content]");
  if (heroBg && heroContent && !reduceMotion) {
    var heroTick = false;
    var heroFrame = function () {
      heroTick = false;
      var y = window.scrollY;
      var limit = window.innerHeight * 1.1;
      if (y > limit) { return; }
      heroBg.style.setProperty("transform", "translate3d(0," + Math.round(y * 0.22) + "px,0)");
      heroContent.style.setProperty("transform", "translate3d(0," + Math.round(y * -0.08) + "px,0)");
      heroContent.style.setProperty("opacity", String(Math.max(0, 1 - y / (window.innerHeight * 0.75))));
    };
    window.addEventListener("scroll", function () {
      if (!heroTick) { heroTick = true; window.requestAnimationFrame(heroFrame); }
    }, { passive: true });
  }

  // ---- Waypoint: a radar-style dial that lists the chapters of the page -------------------------
  (function waypoint() {
    var wp = document.querySelector("[data-waypoint]");
    if (!wp) { return; }
    var chapters = [].slice.call(document.querySelectorAll("[data-chapter][id]"));
    if (chapters.length < 3) { return; }
    var list = wp.querySelector("[data-wp-list]");
    var dial = wp.querySelector("[data-wp-toggle]");
    var indexEl = wp.querySelector("[data-wp-index]");
    var links = chapters.map(function (chapter, i) {
      var li = document.createElement("li");
      var a = document.createElement("a");
      var num = document.createElement("span");
      num.textContent = ("0" + (i + 1)).slice(-2);
      a.appendChild(num);
      a.appendChild(document.createTextNode(chapter.getAttribute("data-chapter")));
      a.href = "#" + chapter.id;
      li.appendChild(a);
      list.appendChild(li);
      return a;
    });

    var open = function (state) {
      dial.setAttribute("aria-expanded", String(state));
      list.hidden = !state;
    };
    dial.addEventListener("click", function () { open(dial.getAttribute("aria-expanded") !== "true"); });
    list.addEventListener("click", function (e) { if (e.target.closest("a")) { open(false); } });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && dial.getAttribute("aria-expanded") === "true") { open(false); dial.focus(); }
    });
    document.addEventListener("click", function (e) { if (!wp.contains(e.target)) { open(false); } });

    var setActive = function (i) {
      links.forEach(function (a, n) {
        if (n === i) { a.setAttribute("aria-current", "true"); } else { a.removeAttribute("aria-current"); }
      });
      indexEl.textContent = ("0" + (i + 1)).slice(-2);
    };
    setActive(0);

    if ("IntersectionObserver" in window) {
      var spy = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) { setActive(chapters.indexOf(entry.target)); }
        });
      }, { rootMargin: "-45% 0px -50% 0px" });
      chapters.forEach(function (c) { spy.observe(c); });
    }

    // Step aside for the footer so it never covers the links there.
    var footer = document.querySelector(".site-footer");
    if (footer && "IntersectionObserver" in window) {
      new IntersectionObserver(function (entries) {
        var away = entries[0].isIntersecting;
        wp.classList.toggle("is-away", away);
        if (away) { open(false); }
      }).observe(footer);
    }

    // Stay out of the way of the opening screen.
    var showWhenScrolled = function () {
      var show = window.scrollY > window.innerHeight * 0.55;
      if (wp.hidden === show) {
        wp.hidden = !show;
        if (!show) { open(false); }
      }
    };
    showWhenScrolled();
    window.addEventListener("scroll", showWhenScrolled, { passive: true });
  })();

  // ---- Cast stage: one frame, eight people. A short reel plays through; a name holds on a person ---
  (function castStage() {
    var root = document.querySelector("[data-cast]");
    if (!root) { return; }
    var items = [].slice.call(root.querySelectorAll("[data-cast-item]"));
    if (!items.length) { return; }
    var still = root.querySelector("[data-still]");
    var video = root.querySelector("[data-video-stage]");
    var caption = root.querySelector(".cast__caption");
    var roleEl = caption.querySelector("[data-role]");
    var nameEl = caption.querySelector("[data-name]");
    var summaryEl = caption.querySelector("[data-summary]");
    var linkEl = caption.querySelector("[data-link]");
    var pauseBtn = root.querySelector("[data-toggle]");
    var wholeBtn = root.querySelector("[data-play-reel]");
    var reelSrc = root.getAttribute("data-reel");
    var segments = items.map(function (it) {
      return it.hasAttribute("data-start") ? { start: parseFloat(it.getAttribute("data-start")), end: parseFloat(it.getAttribute("data-end")) } : null;
    });

    var state = { index: 0, whole: !!reelSrc, motion: !calm, visible: false, current: "" };
    var timer = null;
    var raf = 0;

    if (still) { still.addEventListener("error", function () { still.hidden = true; }); }

    function showItem(i) {
      state.index = i;
      items.forEach(function (it, n) {
        var on = n === i;
        it.classList.toggle("is-active", on);
        it.setAttribute("aria-pressed", String(on));
      });
      var it = items[i];
      roleEl.textContent = it.getAttribute("data-role");
      nameEl.textContent = it.getAttribute("data-name");
      summaryEl.textContent = it.getAttribute("data-summary");
      if (linkEl) { linkEl.setAttribute("href", it.getAttribute("data-href")); }
      if (!reduceMotion) {
        caption.classList.remove("is-switching");
        void caption.offsetWidth; // restart the entrance
        caption.classList.add("is-switching");
      }
      var image = it.getAttribute("data-image");
      if (still && image && still.getAttribute("src") !== image) {
        still.classList.add("is-switching");
        window.clearTimeout(timer);
        timer = window.setTimeout(function () {
          still.hidden = false;
          still.src = image;
          still.classList.remove("is-switching");
        }, reduceMotion ? 0 : 180);
      }
    }

    function load(src) {
      if (!video || state.current === src) { return; }
      state.current = src;
      video.classList.remove("is-ready");
      video.src = src;
      video.loop = true;
      video.load();
    }

    function useReel() {
      state.whole = true;
      if (wholeBtn) { wholeBtn.hidden = true; }
      if (!video || !reelSrc) { return; }
      load(reelSrc);
      var begin = function () { video.currentTime = 0; apply(); };
      if (video.readyState >= 1) { begin(); } else { video.addEventListener("loadedmetadata", begin, { once: true }); }
    }

    function useClip(i) {
      state.whole = false;
      if (wholeBtn && reelSrc) { wholeBtn.hidden = false; }
      var clip = items[i].getAttribute("data-clip");
      if (video && clip) { load(clip); apply(); }
    }

    // Whole-reel mode: keep the name list and caption in step with the picture.
    function follow() {
      raf = 0;
      if (!state.whole || !video || video.paused) { return; }
      var t = video.currentTime;
      for (var n = 0; n < segments.length; n++) {
        var s = segments[n];
        if (s && t >= s.start && t < s.end) {
          if (n !== state.index) { showItem(n); }
          break;
        }
      }
      raf = window.requestAnimationFrame(follow);
    }

    function apply() {
      if (!video) { return; }
      var play = state.motion && state.visible && !document.hidden;
      if (play) {
        safePlay(video);
        if (!raf && state.whole) { raf = window.requestAnimationFrame(follow); }
      } else {
        video.pause();
      }
      if (pauseBtn) {
        pauseBtn.textContent = state.motion ? "Pause" : "Play";
        pauseBtn.setAttribute("aria-pressed", String(!state.motion));
      }
    }

    if (video) {
      video.addEventListener("playing", function () {
        video.classList.add("is-ready");
        if (state.whole && !raf) { raf = window.requestAnimationFrame(follow); }
      });
      video.addEventListener("error", function () { video.classList.remove("is-ready"); });
    }

    items.forEach(function (it, i) {
      it.addEventListener("click", function () {
        showItem(i);
        if (it.hasAttribute("data-clip") && video) {
          useClip(i);
        } else if (video) {
          video.pause();
        }
        // Touch screens and keyboards: a second press on the same name opens the profile.
      });
    });
    if (pauseBtn) {
      pauseBtn.addEventListener("click", function () {
        state.motion = !state.motion;
        if (state.motion && video && !state.current) { reelSrc ? useReel() : useClip(state.index); }
        apply();
      });
    }
    if (wholeBtn) {
      wholeBtn.addEventListener("click", function () {
        state.motion = true;
        useReel();
      });
    }

    if ("IntersectionObserver" in window && video) {
      var watch = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          state.visible = entry.isIntersecting;
          if (state.visible && state.motion && !state.current) {
            if (reelSrc) { useReel(); } else { useClip(state.index); }
          }
          apply();
        });
      }, { threshold: 0.35 });
      watch.observe(root.querySelector(".cast__stage"));
    }
    document.addEventListener("visibilitychange", apply);
    // Only start fetching video once the person has seen the stage (preload is "none").
    if (calm) { apply(); }
  })();

  // ---- Region explorer: hover, focus or tap a region to preview it; choose to step inside -------
  (function regionExplorer() {
    var root = document.querySelector("[data-regions]");
    if (!root) { return; }
    var views = [].slice.call(root.querySelectorAll("[data-region-view]"));
    var tabs = [].slice.call(root.querySelectorAll("[data-region-tab]"));
    if (views.length < 2 || views.length !== tabs.length) { return; }
    var current = 0;

    function activate(i) {
      if (i === current) { return; }
      current = i;
      views.forEach(function (view, n) {
        var on = n === i;
        view.classList.toggle("is-active", on);
        view.setAttribute("aria-hidden", String(!on));
        if ("inert" in view) { view.inert = !on; }
      });
      tabs.forEach(function (tab, n) {
        tab.classList.toggle("is-active", n === i);
        if (n === i) { tab.setAttribute("aria-current", "true"); } else { tab.removeAttribute("aria-current"); }
      });
    }
    views.forEach(function (view, n) {
      if (n !== 0) { view.setAttribute("aria-hidden", "true"); if ("inert" in view) { view.inert = true; } }
    });
    tabs[0].setAttribute("aria-current", "true");

    tabs.forEach(function (tab, n) {
      if (!coarse) {
        tab.addEventListener("mouseenter", function () { activate(n); });
      }
      tab.addEventListener("focus", function () { activate(n); });
      tab.addEventListener("click", function (e) {
        // On touch screens the first tap previews, the second opens the page.
        if (coarse && current !== n) { e.preventDefault(); activate(n); }
      });
    });
  })();

  // ---- Garage showroom: swipe, drag or use the arrows -------------------------------------------
  (function showroom() {
    var root = document.querySelector("[data-showroom]");
    if (!root) { return; }
    var track = root.querySelector(".showroom__track");
    var prev = document.querySelector("[data-showroom-prev]");
    var next = document.querySelector("[data-showroom-next]");
    var bar = document.querySelector("[data-showroom-progress]");

    function step(dir) {
      var item = track.querySelector(".showroom__item");
      var amount = item ? item.getBoundingClientRect().width + 24 : track.clientWidth * 0.8;
      track.scrollBy({ left: dir * amount, behavior: reduceMotion ? "auto" : "smooth" });
    }
    function update() {
      var max = track.scrollWidth - track.clientWidth;
      var at = max <= 0 ? 0 : track.scrollLeft / max;
      if (bar) {
        var visible = track.clientWidth / track.scrollWidth;
        bar.style.setProperty("width", Math.round((visible + (1 - visible) * at) * 100) + "%");
      }
      if (prev) { prev.disabled = track.scrollLeft < 8; }
      if (next) { next.disabled = track.scrollLeft > max - 8; }
    }
    if (prev) { prev.addEventListener("click", function () { step(-1); }); }
    if (next) { next.addEventListener("click", function () { step(1); }); }
    track.addEventListener("scroll", function () { window.requestAnimationFrame(update); }, { passive: true });
    track.addEventListener("keydown", function (e) {
      if (e.key === "ArrowRight") { e.preventDefault(); step(1); }
      if (e.key === "ArrowLeft") { e.preventDefault(); step(-1); }
    });
    window.addEventListener("resize", update);
    update();

    // Mouse drag, for desktop (touch scrolls natively).
    var down = false, startX = 0, startLeft = 0, moved = false;
    track.addEventListener("pointerdown", function (e) {
      if (e.pointerType !== "mouse" || e.button !== 0) { return; }
      down = true; moved = false; startX = e.clientX; startLeft = track.scrollLeft;
    });
    window.addEventListener("pointermove", function (e) {
      if (!down) { return; }
      var dx = e.clientX - startX;
      if (Math.abs(dx) > 6) { moved = true; track.style.setProperty("scroll-snap-type", "none"); }
      if (moved) { track.scrollLeft = startLeft - dx; }
    });
    window.addEventListener("pointerup", function () {
      if (!down) { return; }
      down = false;
      track.style.removeProperty("scroll-snap-type");
    });
    track.addEventListener("click", function (e) { if (moved) { e.preventDefault(); moved = false; } }, true);
  })();

  // ---- Short muted loops on detail pages: play in view, pause out of view -----------------------
  (function loops() {
    var videos = [].slice.call(document.querySelectorAll("video[data-loop]"));
    if (!videos.length) { return; }
    videos.forEach(function (video) {
      var src = video.getAttribute("data-src");
      var loaded = false;
      var label = document.querySelector('[data-loop-toggle="' + video.id + '"]');
      var wanted = !calm;
      function sync(visible) {
        if (visible && wanted && !document.hidden) {
          if (!loaded) { video.src = src; loaded = true; }
          safePlay(video);
        } else {
          video.pause();
        }
        if (label) { label.textContent = wanted ? "Pause" : "Play"; }
      }
      video.addEventListener("playing", function () { video.classList.add("is-ready"); });
      var visibleNow = false;
      if ("IntersectionObserver" in window) {
        new IntersectionObserver(function (entries) {
          entries.forEach(function (entry) { visibleNow = entry.isIntersecting; sync(visibleNow); });
        }, { threshold: 0.3 }).observe(video);
      } else {
        visibleNow = true;
        sync(true);
      }
      if (label) {
        label.hidden = false;
        label.textContent = wanted ? "Pause" : "Play";
        label.addEventListener("click", function () { wanted = !wanted; sync(visibleNow); });
      }
      document.addEventListener("visibilitychange", function () { sync(visibleNow); });
    });
  })();

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
        videoCaption.textContent = (trigger.getAttribute("data-title") || "") + " | Official video from Rockstar Games.";
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
        imageCaption.textContent = (link.getAttribute("data-caption") || "") + " | Official image from Rockstar Games.";
        imageDialog.showModal();
      });
    });
    imageDialog.addEventListener("close", function () { bigImage.removeAttribute("src"); });
  }
})();
