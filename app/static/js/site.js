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

  // ---- Section navigator: a labelled control that names where you are and lists the sections ----
  (function waypoint() {
    var wp = document.querySelector("[data-waypoint]");
    if (!wp) { return; }
    var chapters = [].slice.call(document.querySelectorAll("[data-chapter][id]"));
    if (chapters.length < 3) { return; }
    var list = wp.querySelector("[data-wp-list]");
    var dial = wp.querySelector("[data-wp-toggle]");
    var indexEl = wp.querySelector("[data-wp-index]");
    var nameEl = wp.querySelector("[data-wp-name]");
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
      if (nameEl) { nameEl.textContent = chapters[i].getAttribute("data-chapter"); }
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

  // ---- Cast stage: one frame, eight people. The reel plays through; a name holds on that person ----
  // Both controls exist in the markup from the first paint. The script only changes their state, never
  // their visibility, so "Play whole reel" is available on load and after every selection.
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
    var reelBtn = root.querySelector("[data-play-reel]");
    var reelSrc = root.getAttribute("data-reel");
    var segments = items.map(function (it) {
      return it.hasAttribute("data-start") ? { start: parseFloat(it.getAttribute("data-start")), end: parseFloat(it.getAttribute("data-end")) } : null;
    });

    // mode: "reel" plays every clip in order, "clip" loops the chosen person. motion: playback is wanted.
    var state = { index: 0, mode: reelSrc ? "reel" : "clip", motion: !calm, visible: false, current: "" };
    var timer = null;
    var raf = 0;

    if (still) { still.addEventListener("error", function () { still.hidden = true; }); }

    function render() {
      if (pauseBtn) { pauseBtn.textContent = state.motion ? "Pause" : "Play"; }
      if (reelBtn) {
        var on = state.mode === "reel";
        reelBtn.classList.toggle("is-active", on);
        reelBtn.setAttribute("aria-pressed", String(on));
      }
    }

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

    // Rewind to the start of whatever is loaded and play it (when it is wanted and visible).
    function playFromStart() {
      if (!video) { return; }
      var go = function () {
        try { video.currentTime = 0; } catch (e) { /* not seekable yet */ }
        apply();
      };
      if (video.readyState >= 1) { go(); } else { video.addEventListener("loadedmetadata", go, { once: true }); }
    }

    function startReel() {
      state.mode = "reel";
      if (video && reelSrc) { load(reelSrc); }
      showItem(0);
      render();
      playFromStart();
    }

    function startClip(i) {
      var clip = items[i].getAttribute("data-clip");
      state.mode = "clip";
      showItem(i);
      if (video && clip) { load(clip); render(); playFromStart(); } else { if (video) { video.pause(); } render(); }
    }

    // Whole-reel mode: keep the name list and caption in step with the picture.
    function follow() {
      raf = 0;
      if (state.mode !== "reel" || !video || video.paused) { return; }
      var t = video.currentTime;
      for (var n = 0; n < segments.length; n++) {
        var seg = segments[n];
        if (seg && t >= seg.start && t < seg.end) {
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
        if (!raf && state.mode === "reel") { raf = window.requestAnimationFrame(follow); }
      } else {
        video.pause();
      }
      render();
    }

    if (video) {
      video.addEventListener("playing", function () {
        video.classList.add("is-ready");
        if (state.mode === "reel" && !raf) { raf = window.requestAnimationFrame(follow); }
      });
      video.addEventListener("error", function () { video.classList.remove("is-ready"); });
    }

    // Choosing a person is an explicit request for motion, even when autoplay is off.
    items.forEach(function (it, i) {
      it.addEventListener("click", function () {
        state.motion = true;
        startClip(i);
      });
    });
    if (pauseBtn) {
      pauseBtn.addEventListener("click", function () {
        state.motion = !state.motion;
        if (state.motion && video && !state.current) {
          if (state.mode === "reel" && reelSrc) { startReel(); } else { startClip(state.index); }
        } else {
          apply();
        }
      });
    }
    if (reelBtn) {
      reelBtn.addEventListener("click", function () {
        state.motion = true;
        startReel();
      });
    }

    if ("IntersectionObserver" in window && video) {
      var watch = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          state.visible = entry.isIntersecting;
          if (state.visible && state.motion && !state.current) {
            if (state.mode === "reel" && reelSrc) { startReel(); } else { startClip(state.index); }
          } else {
            apply();
          }
        });
      }, { threshold: 0.35 });
      watch.observe(root.querySelector(".cast__stage"));
    }
    document.addEventListener("visibilitychange", apply);
    render();
  })();

  // ---- The signature moment: nine seconds of Rockstar's Trailer 1 in YouTube's embedded player --------
  // Nothing is downloaded or hosted. The player (YouTube's own IFrame API, privacy-enhanced domain) is only
  // created when the section is close to the screen, plays muted, pauses when scrolled away, and is never
  // started automatically for visitors who prefer reduced motion or have data saver on.
  (function signatureMoment() {
    var root = document.querySelector("[data-moment]");
    if (!root) { return; }
    var mount = root.querySelector("[data-moment-player]");
    var toggleBtn = root.querySelector("[data-moment-toggle]");
    var soundBtn = root.querySelector("[data-moment-sound]");
    var videoId = root.getAttribute("data-youtube");
    var start = parseFloat(root.getAttribute("data-start"));
    var end = parseFloat(root.getAttribute("data-end"));
    if (!/^[A-Za-z0-9_-]{11}$/.test(videoId || "") || !(end > start)) { return; }

    var player = null;
    var phase = "idle"; // idle, loading, ready, failed
    var state = { motion: !calm, visible: false, muted: true };
    var poll = 0;

    function setButtons() {
      if (toggleBtn) {
        toggleBtn.hidden = phase === "failed";
        toggleBtn.textContent = state.motion ? "Pause" : "Play the footage";
      }
      if (soundBtn) {
        soundBtn.hidden = phase !== "ready";
        soundBtn.textContent = state.muted ? "Sound on" : "Sound off";
        soundBtn.setAttribute("aria-pressed", String(!state.muted));
      }
    }

    function loadApi(done) {
      if (window.YT && window.YT.Player) { done(); return; }
      var previous = window.onYouTubeIframeAPIReady;
      window.onYouTubeIframeAPIReady = function () {
        if (typeof previous === "function") { previous(); }
        done();
      };
      var tag = document.createElement("script");
      tag.src = "https://www.youtube.com/iframe_api";
      tag.async = true;
      tag.onerror = function () { phase = "failed"; setButtons(); };
      document.head.appendChild(tag);
    }

    function wrap() {
      root.classList.add("is-dip");
      try { player.seekTo(start, true); } catch (e) { /* player not ready */ }
      window.setTimeout(function () { root.classList.remove("is-dip"); }, 420);
    }

    function tick() {
      if (!player || typeof player.getCurrentTime !== "function") { return; }
      if (player.getPlayerState() !== 1) { return; } // only while it is really playing
      var t = player.getCurrentTime();
      if (t >= end - 0.1 || t < start - 1.5) { wrap(); return; }
      if (t >= end - 0.45) { root.classList.add("is-dip"); }
      // Show the player only once it is inside the chosen nine seconds, never the frames before them.
      if (!root.classList.contains("is-live") && t >= start - 0.05) { root.classList.add("is-live"); }
    }

    function wanted() { return state.motion && state.visible && !document.hidden; }

    function apply() {
      if (!player || phase !== "ready") { return; }
      try {
        if (wanted()) { player.playVideo(); } else { player.pauseVideo(); }
      } catch (e) { /* ignore */ }
      setButtons();
    }

    function create() {
      if (phase !== "idle") { return; }
      phase = "loading";
      loadApi(function () {
        var holder = document.createElement("div");
        mount.appendChild(holder);
        player = new window.YT.Player(holder, {
          host: "https://www.youtube-nocookie.com",
          videoId: videoId,
          playerVars: {
            autoplay: 0, controls: 0, disablekb: 1, fs: 0, iv_load_policy: 3, modestbranding: 1,
            playsinline: 1, rel: 0, cc_load_policy: 0, origin: window.location.origin
          },
          events: {
            onReady: function () {
              phase = "ready";
              var frame = player.getIframe();
              if (frame) {
                frame.setAttribute("tabindex", "-1");
                frame.setAttribute("title", root.getAttribute("aria-label") || "Official footage");
              }
              player.mute();
              poll = window.setInterval(tick, 120);
              // Cue at the exact start (fractional seconds), then play when it is wanted and visible.
              if (wanted()) {
                player.loadVideoById({ videoId: videoId, startSeconds: start });
              } else {
                player.cueVideoById({ videoId: videoId, startSeconds: start });
              }
              setButtons();
            },
            onStateChange: function (e) {
              if (e.data === 0) { wrap(); try { player.playVideo(); } catch (err) { /* ignore */ } }
              if (e.data === 5) { apply(); } // cued: play now if it is wanted
            },
            onError: function () {
              phase = "failed";
              root.classList.remove("is-live");
              window.clearInterval(poll);
              setButtons();
            }
          }
        });
      });
    }

    if (toggleBtn) {
      toggleBtn.addEventListener("click", function () {
        state.motion = !state.motion;
        if (state.motion && phase === "idle") { create(); }
        apply();
        setButtons();
      });
    }
    if (soundBtn) {
      soundBtn.addEventListener("click", function () {
        state.muted = !state.muted;
        try {
          if (state.muted) { player.mute(); } else { player.unMute(); player.setVolume(70); }
        } catch (e) { /* ignore */ }
        setButtons();
      });
    }

    if ("IntersectionObserver" in window) {
      new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting && state.motion) { create(); } // arrives early so it is ready when seen
        });
      }, { rootMargin: "120% 0px 120% 0px" }).observe(root);
      new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) { state.visible = entry.isIntersecting; apply(); });
      }, { threshold: 0.25 }).observe(root);
    }
    document.addEventListener("visibilitychange", apply);
    setButtons();
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
        videoCaption.textContent = (trigger.getAttribute("data-title") || "") + " · official video, © Rockstar Games";
        videoDialog.showModal();
      });
    });
  }

  if (imageDialog && typeof imageDialog.showModal === "function") {
    closeOnBackdrop(imageDialog);
    var bigImage = imageDialog.querySelector("[data-image]");
    var imageCaption = imageDialog.querySelector("[data-caption]");
    var imageCount = imageDialog.querySelector("[data-count]");
    var prevBtn = imageDialog.querySelector("[data-lb-prev]");
    var nextBtn = imageDialog.querySelector("[data-lb-next]");
    var group = [];
    var at = 0;

    var showImage = function (n) {
      at = (n + group.length) % group.length;
      var link = group[at];
      var text = link.getAttribute("data-caption") || "";
      bigImage.src = link.href;
      bigImage.alt = text;
      imageCaption.textContent = text + " · © Rockstar Games";
      imageCount.textContent = group.length > 1 ? (at + 1) + " / " + group.length : "";
      prevBtn.hidden = nextBtn.hidden = group.length < 2;
    };

    document.querySelectorAll("a[data-lightbox]").forEach(function (link) {
      link.addEventListener("click", function (e) {
        e.preventDefault();
        var holder = link.closest("[data-gallery]");
        group = holder ? [].slice.call(holder.querySelectorAll("a[data-lightbox]")) : [link];
        showImage(group.indexOf(link));
        imageDialog.showModal();
      });
    });
    prevBtn.addEventListener("click", function () { showImage(at - 1); });
    nextBtn.addEventListener("click", function () { showImage(at + 1); });
    imageDialog.addEventListener("keydown", function (e) {
      if (group.length < 2) { return; }
      if (e.key === "ArrowLeft") { e.preventDefault(); showImage(at - 1); }
      if (e.key === "ArrowRight") { e.preventDefault(); showImage(at + 1); }
    });
    imageDialog.addEventListener("close", function () { bigImage.removeAttribute("src"); });
  }
})();
