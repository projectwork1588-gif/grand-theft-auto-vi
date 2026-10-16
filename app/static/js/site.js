// Team Valkyrie | GTA VI fan guide | progressive enhancement only. Every page works without this file.
(function () {
  "use strict";

  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var saveData = !!(navigator.connection && navigator.connection.saveData);

  // ---- Motion policy ---------------------------------------------------------------------------
  // Video, the cast reel, the region explorer and the garage move by themselves. A visitor whose system asks for
  // reduced motion (on Windows that is "Show animations" turned off) or who has data saver on is respected, unless
  // they opt in: one click on any "Play" control, or the Motion switch in the menu, is remembered in this browser.
  // The server can set data-autoplay="always" (TV_AUTOPLAY_ALWAYS=1) to start motion regardless of the system setting.
  var autoplayAlways = document.body && document.body.getAttribute("data-autoplay") === "always";
  var motionStore = null;
  try { motionStore = window.localStorage.getItem("tv-motion"); } catch (e) { /* storage unavailable */ }
  var motionBlocked = saveData || (reduceMotion && !autoplayAlways);
  function motionAllowed() { return motionStore === "1" ? true : (motionStore === "0" ? false : !motionBlocked); }
  var calm = !motionAllowed(); // read once by code that only needs the starting state
  function setMotion(on) {
    motionStore = on ? "1" : "0";
    try { window.localStorage.setItem("tv-motion", motionStore); } catch (e) { /* ignore */ }
    document.documentElement.classList.toggle("motion-on", on);
    syncMotionUi();
    document.dispatchEvent(new Event("tv:motion"));
  }
  function syncMotionUi() {
    var allowed = motionAllowed();
    [].forEach.call(document.querySelectorAll("[data-motion-optin]"), function (el) { el.hidden = allowed; });
    [].forEach.call(document.querySelectorAll("[data-motion-toggle]"), function (el) {
      el.setAttribute("aria-pressed", String(allowed));
      var label = el.querySelector("b");
      if (label) { label.textContent = allowed ? "On" : "Off"; }
    });
  }
  document.documentElement.classList.toggle("motion-on", motionAllowed());
  [].forEach.call(document.querySelectorAll("[data-motion-optin]"), function (el) {
    el.addEventListener("click", function () { setMotion(true); });
  });
  [].forEach.call(document.querySelectorAll("[data-motion-toggle]"), function (el) {
    el.addEventListener("click", function () { setMotion(!motionAllowed()); });
  });
  [].forEach.call(document.querySelectorAll("[data-motion-row]"), function (el) { el.hidden = false; });
  syncMotionUi();
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
    var navLabel = toggle.querySelector("[data-nav-label]");
    var setOpen = function (open) {
      toggle.setAttribute("aria-expanded", String(open));
      nav.classList.toggle("is-open", open);
      document.documentElement.classList.toggle("menu-open", open);
      if (navLabel) { navLabel.textContent = open ? "Close" : "Menu"; }
      if (header) { header.classList.toggle("is-solid", open || window.scrollY > 40); }
    };
    toggle.addEventListener("click", function () { setOpen(toggle.getAttribute("aria-expanded") !== "true"); });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && toggle.getAttribute("aria-expanded") === "true") { setOpen(false); toggle.focus(); }
    });
    // A link to a section of the page we are already on closes the menu; a link to another page simply leaves.
    nav.addEventListener("click", function (e) { if (e.target.closest("a")) { setOpen(false); } });
    // Growing past the menu's range (the inline navigation takes over) closes it and unlocks the page.
    var wide = window.matchMedia("(min-width: 1100px)");
    var onWide = function () { if (wide.matches && toggle.getAttribute("aria-expanded") === "true") { setOpen(false); } };
    if (wide.addEventListener) { wide.addEventListener("change", onWide); } else if (wide.addListener) { wide.addListener(onWide); }
    // Tab stays inside the open menu and its button.
    nav.addEventListener("keydown", function (e) {
      if (e.key !== "Tab" || toggle.getAttribute("aria-expanded") !== "true") { return; }
      var links = nav.querySelectorAll("a[href]");
      var first = links[0], last = links[links.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); toggle.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); toggle.focus(); }
    });
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

  // ---- Hero motion poster: its animations run only while the hero is on screen and the tab is visible ----------
  (function heroStage() {
    var stage = document.querySelector("[data-hero-stage]");
    if (!stage) { return; }
    if ("IntersectionObserver" in window) {
      new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) { stage.classList.toggle("is-paused", !entry.isIntersecting); });
      }, { threshold: 0 }).observe(stage);
    }
    document.addEventListener("visibilitychange", function () { stage.classList.toggle("is-hidden", document.hidden); });
  })();

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
      heroContent.style.setProperty("transform", "translate3d(0," + Math.round(y * -0.08) + "px,0)");
      heroContent.style.setProperty("opacity", String(Math.max(0, 1 - y / (window.innerHeight * 0.75))));
    };
    window.addEventListener("scroll", function () {
      if (!heroTick) { heroTick = true; window.requestAnimationFrame(heroFrame); }
    }, { passive: true });
  }

  // ---- Chapter navigation: a quiet rail of dots on wide screens, a progress hairline on phones ------
  // Names appear on hover or keyboard focus only, so the rail never sits over artwork or controls. The same list is
  // added to the header menu ("On this page"), which is how phones jump between sections.
  (function chapterNav() {
    var rail = document.querySelector("[data-rail]");
    var hair = document.querySelector("[data-progress]");
    var chapters = [].slice.call(document.querySelectorAll("[data-chapter][id]"));
    if (!rail || chapters.length < 3) { return; }
    var list = rail.querySelector("[data-rail-list]");
    var pad = function (n) { return ("0" + n).slice(-2); };
    var links = chapters.map(function (chapter, i) {
      var name = chapter.getAttribute("data-chapter");
      var li = document.createElement("li");
      var a = document.createElement("a");
      a.href = "#" + chapter.id;
      a.setAttribute("aria-label", pad(i + 1) + " " + name);
      var label = document.createElement("span");
      label.className = "chapter-rail__label";
      var num = document.createElement("b");
      num.textContent = pad(i + 1);
      label.appendChild(num);
      label.appendChild(document.createTextNode(" " + name));
      a.appendChild(label);
      li.appendChild(a);
      list.appendChild(li);
      return a;
    });

    var side = document.querySelector(".site-menu__side");
    var menuLinks = [];
    if (side) {
      var block = document.createElement("div");
      var title = document.createElement("p");
      title.className = "site-menu__label";
      title.textContent = "On this page";
      var ul = document.createElement("ul");
      ul.className = "site-menu__links";
      chapters.forEach(function (chapter) {
        var li = document.createElement("li");
        var a = document.createElement("a");
        a.href = "#" + chapter.id;
        a.textContent = chapter.getAttribute("data-chapter");
        li.appendChild(a);
        ul.appendChild(li);
        menuLinks.push(a);
      });
      block.appendChild(title);
      block.appendChild(ul);
      side.insertBefore(block, side.children[1] || null);
    }

    var setActive = function (i) {
      links.forEach(function (a, n) {
        if (n === i) { a.setAttribute("aria-current", "true"); } else { a.removeAttribute("aria-current"); }
      });
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

    var footer = document.querySelector(".site-footer");
    var update = function () {
      var away = window.scrollY < window.innerHeight * 0.55;
      if (rail.hidden !== away) { rail.hidden = away; }
      if (hair) {
        var max = document.documentElement.scrollHeight - window.innerHeight;
        var p = max > 0 ? Math.min(1, Math.max(0, window.scrollY / max)) : 0;
        hair.hidden = away;
        hair.firstElementChild.style.setProperty("--progress", String(p));
      }
      if (footer) {
        var r = footer.getBoundingClientRect();
        rail.classList.toggle("is-away", r.top < window.innerHeight);
      }
    };
    update();
    window.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);
  })();

  // ---- Cast stage: one frame, eight people, about three seconds each -----------------------------
  // One reel file is buffered once. Choosing a person seeks straight to that person's segment (keyframes sit
  // at every start, so it is instant) and the reel carries on from there. The reel runs by itself, all eight
  // in order, and loops. There are no control buttons.
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
    var HOLD_BEFORE_END = 0.06; // stop just before the dissolve into the next person
    var segments = items.map(function (it) {
      return it.hasAttribute("data-start") ? { start: parseFloat(it.getAttribute("data-start")), end: parseFloat(it.getAttribute("data-end")) } : null;
    });

    // mode: "reel" plays everyone in order and loops; "single" plays one person once and holds.
    // motion: playback is wanted. held: a single person has reached the end of their segment.
    var state = { index: 0, mode: "reel", motion: motionAllowed(), visible: false, loaded: false, held: false, started: false };
    var timer = null;
    var raf = 0;

    if (still) { still.addEventListener("error", function () { still.hidden = true; }); }

    function render() {
      if (pauseBtn) {
        var label = "Pause";
        if (state.held) { label = "Replay"; } else if (!state.motion) { label = "Play"; }
        pauseBtn.textContent = label;
      }
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

    // Buffer the reel once. Done early when motion is welcome, or on the first explicit request.
    function ensureLoaded() {
      if (!video || !reelSrc || state.loaded) { return; }
      state.loaded = true;
      video.preload = "auto";
      video.src = reelSrc;
      video.load();
    }

    function seekTo(t, then) {
      var go = function () {
        try { video.currentTime = t; } catch (e) { /* not seekable yet */ }
        then();
      };
      if (video.readyState >= 1) { go(); } else { video.addEventListener("loadedmetadata", go, { once: true }); }
    }

    function begin(t) {
      if (!video || !reelSrc) { return; }
      ensureLoaded();
      state.held = false;
      video.loop = state.mode === "reel";
      seekTo(t, function () { play(); });
    }

    function play() {
      if (!video) { return; }
      var tv = window.tvMedia || {};
      var wanted = state.motion && state.visible && !document.hidden && !tv.cinema && !tv.modal;
      if (wanted) {
        safePlay(video);
        armGuard();
        if (!raf) { raf = window.requestAnimationFrame(follow); }
      } else {
        video.pause();
      }
      render();
    }

    function startReel() {
      state.mode = "reel";
      showItem(0);
      begin(0);
    }

    function startPerson(i) {
      var seg = segments[i];
      state.mode = "reel";               // choosing a name jumps there; the reel carries on from that person
      showItem(i);
      if (seg && video && reelSrc) { begin(seg.start); } else { if (video) { video.pause(); } render(); }
    }

    // Keeps the name list and caption in step with the picture, and holds a single person at the end.
    // Called from the frame loop, from timeupdate and from a timer, so the hold never depends on one of them.
    function sync() {
      if (!video) { return false; }
      var t = video.currentTime;
      if (state.mode === "reel") {
        for (var n = 0; n < segments.length; n++) {
          var seg = segments[n];
          if (seg && t >= seg.start && t < seg.end) {
            if (n !== state.index) { showItem(n); }
            break;
          }
        }
        return true;
      }
      var mine = segments[state.index];
      if (mine && !state.held && t >= mine.end - HOLD_BEFORE_END) {
        video.pause();
        try { video.currentTime = Math.max(mine.start, mine.end - HOLD_BEFORE_END - 0.02); } catch (e) { /* ignore */ }
        state.held = true;
        render();
        return false;
      }
      return !state.held;
    }

    function follow() {
      raf = 0;
      if (!video || video.paused) { return; }
      if (sync()) { raf = window.requestAnimationFrame(follow); }
    }

    // A timer is the backstop for the end of a single person's segment (frame loops stop in idle tabs).
    var guard = 0;
    function armGuard() {
      window.clearTimeout(guard);
      var mine = segments[state.index];
      if (state.mode !== "single" || !mine || !video) { return; }
      var left = Math.max(0.05, mine.end - HOLD_BEFORE_END - video.currentTime);
      guard = window.setTimeout(function () { if (!video.paused) { sync(); } }, left * 1000 + 40);
    }

    if (video) {
      // Show the video only once a real frame has been presented, so there is never a black flash.
      var markReady = function () { video.classList.add("is-ready"); };
      video.addEventListener("playing", function () {
        if ("requestVideoFrameCallback" in video) { video.requestVideoFrameCallback(markReady); }
        else { video.addEventListener("timeupdate", markReady, { once: true }); }
        if (!raf) { raf = window.requestAnimationFrame(follow); }
      });
      video.addEventListener("error", function () { video.classList.remove("is-ready"); });
      video.addEventListener("play", function () { window.tvMedia = window.tvMedia || {}; window.tvMedia.cast = true; document.dispatchEvent(new Event("tv:state")); });
      video.addEventListener("pause", function () { window.tvMedia = window.tvMedia || {}; window.tvMedia.cast = false; document.dispatchEvent(new Event("tv:state")); });
      // Yield while a cinematic moment or the trailer overlay is playing, and carry on once they have stopped.
      document.addEventListener("tv:state", function () {
        var tv = window.tvMedia || {};
        if ((tv.cinema || tv.modal) && !video.paused) { video.pause(); }
        else if (!tv.cinema && !tv.modal && state.started && video.paused && state.visible && state.motion && !document.hidden) { play(); }
      });
      video.addEventListener("timeupdate", function () { if (!video.paused) { sync(); } });
      video.addEventListener("seeked", armGuard);
    }

    // Any explicit choice is a request for motion, even when autoplay is off, and it responds at once.
    items.forEach(function (it, i) {
      it.addEventListener("click", function () {
        state.motion = true;
        state.started = true; // an explicit choice always wins over the automatic start
        startPerson(i);
      });
    });
    if (pauseBtn) {
      pauseBtn.addEventListener("click", function () {
        state.started = true;
        if (state.held) {                       // replay the same person from the start
          state.motion = true;
          startPerson(state.index);
          return;
        }
        state.motion = !state.motion;
        if (state.motion && !state.loaded) {
          if (state.mode === "reel") { startReel(); } else { startPerson(state.index); }
        } else {
          play();
        }
      });
    }
    if (reelBtn) {
      reelBtn.addEventListener("click", function () {
        state.motion = true;
        state.started = true;
        startReel();
      });
    }

    if ("IntersectionObserver" in window && video) {
      // Fetch the reel a little before it is seen, so a name responds instantly when chosen.
      new IntersectionObserver(function (entries, obs) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting && motionAllowed()) { ensureLoaded(); obs.disconnect(); }
        });
      }, { rootMargin: "100% 0px 100% 0px" }).observe(root);
      new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          state.visible = entry.isIntersecting;
          if (state.visible && state.motion && !state.started) {
            state.started = true;
            startReel();
          } else {
            play();
          }
        });
      }, { threshold: 0.35 }).observe(root.querySelector(".cast__stage"));
    }
    document.addEventListener("visibilitychange", play);
    // The visitor opted in (or out) of motion: start the reel if it is in view, or stop it.
    document.addEventListener("tv:motion", function () {
      state.motion = motionAllowed();
      if (state.motion && state.visible && !state.started) { state.started = true; startReel(); } else { play(); }
    });
    // A once-a-second reconcile, so a missed event during a quick scroll can never leave the reel frozen.
    window.setInterval(function () {
      if (video && !document.hidden && state.visible && state.motion && state.started && video.paused) { play(); }
    }, 1000);
    render();
  })();

  // ---- The cinematic moments: native video that loops by itself ------------------------------------------
  // Up to three sections, each a plain looping <video> over its own poster, with one discreet speaker icon in the
  // corner (and no play or pause control during normal playback). Rules:
  //  * One video plays at a time: the most visible eligible moment wins; the cast reel and the trailer overlay
  //    count too (window.tvMedia). A once-a-second reconcile recovers from any missed event.
  //  * Muted autoplay when a moment is at least 35 percent in view, paused when it leaves, resumed when revisited.
  //    The loop seam is baked into the file, so the loop is continuous.
  //  * Sound is the visitor's choice: browsers refuse audible autoplay until the page has been interacted with. The
  //    sound button turns it on (faded in), the choice is remembered for the visit, and later moments follow it.
  //  * When motion is not allowed (reduced motion, data saver, or the visitor turned it off) or the browser refuses
  //    to autoplay, a plain "Play footage" button appears (and only then): one press starts everything.
  window.tvMedia = window.tvMedia || { cast: false, cinema: false, modal: false };
  (function cinemas() {
    var roots = [].slice.call(document.querySelectorAll("[data-cinema]"));
    var players = [];
    roots.forEach(function (root) {
      var video = root.querySelector("[data-cinema-video]");
      if (!video) { return; }
      players.push({
        root: root, video: video, toggleBtn: root.querySelector("[data-cinema-toggle]"), soundBtn: root.querySelector("[data-cinema-sound]"),
        ratio: 0, loaded: false, failed: false, refused: false, ramp: 0
      });
    });
    if (!players.length) { return; }

    var slow = !!(navigator.connection && /(^|-)(2g|3g)$/.test(navigator.connection.effectiveType || ""));
    var automatic = function () { return motionAllowed() && !slow; };
    var interacted = false;
    ["pointerdown", "keydown", "touchstart"].forEach(function (name) {
      window.addEventListener(name, function () { interacted = true; }, { once: true, passive: true });
    });
    var activated = function () { return interacted || !!(navigator.userActivation && navigator.userActivation.hasBeenActive); };
    var soundOn = false;
    try { soundOn = window.sessionStorage.getItem("tv-sound") === "1"; } catch (e) { /* storage unavailable */ }

    function ramp(p, to, ms, done) {
      window.clearInterval(p.ramp);
      var from = p.video.volume, steps = Math.max(1, Math.round(ms / 40)), n = 0;
      p.ramp = window.setInterval(function () {
        n += 1;
        p.video.volume = Math.max(0, Math.min(1, from + (to - from) * (n / steps)));
        if (n >= steps) { window.clearInterval(p.ramp); if (done) { done(); } }
      }, 40);
    }

    function labels(p) {
      var suppressed = !automatic() || p.refused;
      var playing = !p.video.paused;
      if (p.toggleBtn) {
        var text = p.toggleBtn.querySelector("[data-tool-label]");
        // Normal playback shows no play or pause control at all; this one exists only when playback is blocked.
        p.toggleBtn.classList.toggle("is-suppressed", suppressed && !playing);
        p.toggleBtn.hidden = !(suppressed && !playing);
        if (text) { text.textContent = "Play footage"; }
      }
      if (p.soundBtn) {
        p.soundBtn.setAttribute("aria-pressed", String(soundOn));
        p.soundBtn.classList.toggle("is-on", soundOn);
      }
    }

    function load(p) {
      if (p.loaded || p.failed) { return; }
      p.loaded = true;
      p.video.preload = "auto";
      p.video.load();
    }

    function start(p) {
      if (!p.video.paused) { return; }
      load(p);
      var withSound = soundOn && activated();
      p.video.muted = !withSound;
      p.video.volume = withSound ? 0 : 1;
      var promise = p.video.play();
      if (promise && typeof promise.catch === "function") {
        promise.catch(function (err) {
          var name = err && err.name;
          if (name === "AbortError") { return; }             // interrupted by a pause (quick scrolling): the reconcile retries
          if (withSound) {                                   // audible playback refused: carry on silently
            p.video.muted = true; p.video.volume = 1;
            safePlay(p.video);
          } else if (name === "NotAllowedError") {           // even muted playback refused: offer a plain Play button
            p.refused = true; labels(p);
          } else if (name === "NotSupportedError") {         // the file cannot be played: the poster stays
            p.failed = true; labels(p);
          }
        });
      }
      if (withSound) { ramp(p, 1, 500); }
    }

    function stop(p) {
      if (p.video.paused) { return; }
      if (!p.video.muted && p.video.volume > 0) { ramp(p, 0, 250, function () { p.video.pause(); p.video.volume = 1; }); }
      else { p.video.pause(); }
    }

    function apply() {
      var best = null;
      var blocked = document.hidden || window.tvMedia.modal || window.tvMedia.cast;
      players.forEach(function (p) {
        if (!blocked && !p.failed && !p.refused && automatic() && p.ratio >= 0.35 && (!best || p.ratio > best.ratio)) { best = p; }
      });
      players.forEach(function (p) { if (p === best) { start(p); } else { stop(p); } });
      window.tvMedia.cinema = players.some(function (p) { return !p.video.paused; });
      players.forEach(labels);
    }

    function toggleSound() {
      soundOn = !soundOn;
      try { window.sessionStorage.setItem("tv-sound", soundOn ? "1" : "0"); } catch (e) { /* ignore */ }
      players.forEach(function (p) {
        if (!p.video.paused) {
          if (soundOn) { p.video.muted = false; p.video.volume = 0; ramp(p, 1, 500); } else { p.video.muted = true; }
        }
        labels(p);
      });
    }

    players.forEach(function (p) {
      p.video.muted = true;
      var tools = p.root.querySelector("[data-cinema-tools]");
      if (tools) { tools.hidden = false; }
      p.video.addEventListener("playing", function () { p.refused = false; p.root.classList.add("is-live"); labels(p); document.dispatchEvent(new Event("tv:state")); });
      p.video.addEventListener("pause", function () {
        window.tvMedia.cinema = players.some(function (q) { return !q.video.paused; });
        labels(p);
        document.dispatchEvent(new Event("tv:state"));
      });
      p.video.addEventListener("error", function () { p.failed = true; p.root.classList.remove("is-live"); apply(); });
      if (p.toggleBtn) {
        // Shown only when footage cannot start by itself: one press starts it (and opts in to motion, remembered).
        p.toggleBtn.addEventListener("click", function () {
          p.refused = false;
          if (!motionAllowed()) { setMotion(true); }
          p.ratio = Math.max(p.ratio, 0.35);
          apply(); start(p);
          labels(p);
        });
      }
      if (p.soundBtn) { p.soundBtn.addEventListener("click", toggleSound); }
    });
    document.addEventListener("keydown", function (e) {
      if ((e.key === "m" || e.key === "M") && !e.ctrlKey && !e.metaKey && !e.altKey && !/input|textarea|select/i.test((e.target.tagName || ""))
          && players.some(function (p) { return !p.video.paused; })) { toggleSound(); }
    });

    if ("IntersectionObserver" in window) {
      var near = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          var p = players.filter(function (q) { return q.root === entry.target; })[0];
          if (p && entry.isIntersecting && automatic()) { load(p); }   // a screen away, so it starts without a stall
        });
      }, { rootMargin: "100% 0px 100% 0px" });
      var seen = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          var p = players.filter(function (q) { return q.root === entry.target; })[0];
          if (p) { p.ratio = entry.isIntersecting ? entry.intersectionRatio : 0; }
        });
        apply();
      }, { threshold: [0, 0.1, 0.2, 0.35, 0.5, 0.65, 0.8, 1] });
      players.forEach(function (p) { near.observe(p.root); seen.observe(p.root); });
    }
    ["pointerdown", "keydown", "touchend"].forEach(function (name) {
      window.addEventListener(name, function () {
        var retry = false;
        players.forEach(function (p) { if (p.refused) { p.refused = false; retry = true; } });
        if (retry) { apply(); }
      }, { passive: true });
    });
    document.addEventListener("visibilitychange", apply);
    document.addEventListener("tv:state", apply);
    document.addEventListener("tv:motion", apply);
    window.addEventListener("pageshow", apply);
    window.addEventListener("focus", apply);
    // Reconcile once a second while the page is visible: recovers from rapid scrolling, a missed observer callback or a
    // handoff between videos that raced, without the visitor ever noticing.
    window.setInterval(function () { if (!document.hidden) { apply(); } }, 1000);
    apply();
  })();

  // ---- Region explorer: moves on by itself every few seconds; hover, focus or tap to choose --------------
  // It advances from region 1 to 6 and around again, only while it is on screen, and never while the visitor is
  // pointing at it. A choice made by hand holds for a full interval before it moves on. When motion is not
  // allowed (reduced motion, data saver) it stays put and offers a plain Auto-play button.
  (function regionExplorer() {
    var root = document.querySelector("[data-regions]");
    if (!root) { return; }
    var views = [].slice.call(root.querySelectorAll("[data-region-view]"));
    var tabs = [].slice.call(root.querySelectorAll("[data-region-tab]"));
    if (views.length < 2 || views.length !== tabs.length) { return; }
    var INTERVAL = 7000;
    var current = 0;
    var visible = false;
    var holding = false;

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

    // One steady tick, not a chain of timers: the interval counts only while the explorer is eligible (motion allowed,
    // on screen, tab visible, nothing holding it). Anything that changes that starts the interval again. A missed
    // event can therefore never stop it for good.
    var dwell = 0, last = Date.now(), wasOk = false;
    function eligible() { return motionAllowed() && !holding && visible && !document.hidden; }
    function restartLine() {
      root.classList.remove("is-timing");
      void root.offsetWidth;                      // restart the progress line under the active tab
      root.classList.add("is-timing");
    }
    function schedule() {
      dwell = 0; last = Date.now(); wasOk = eligible();
      root.classList.toggle("is-held", !wasOk);
      if (wasOk) { restartLine(); }
    }
    window.setInterval(function () {
      var now = Date.now(), dt = Math.min(now - last, 1000);
      last = now;
      var ok = eligible();
      if (ok !== wasOk) { schedule(); return; }
      if (!ok) { return; }
      dwell += dt;
      if (dwell >= INTERVAL) { activate((current + 1) % views.length); schedule(); }
    }, 250);

    views.forEach(function (view, n) {
      if (n !== 0) { view.setAttribute("aria-hidden", "true"); if ("inert" in view) { view.inert = true; } }
    });
    tabs[0].setAttribute("aria-current", "true");
    root.style.setProperty("--auto-ms", INTERVAL + "ms");
    root.classList.toggle("is-auto", motionAllowed());
    document.addEventListener("tv:motion", function () { root.classList.toggle("is-auto", motionAllowed()); schedule(); });

    tabs.forEach(function (tab, n) {
      if (!coarse) {
        tab.addEventListener("mouseenter", function () { activate(n); });
      }
      tab.addEventListener("focus", function () { activate(n); });
      tab.addEventListener("click", function (e) {
        // On touch screens the first tap previews, the second opens the page.
        if (coarse && current !== n) { e.preventDefault(); activate(n); schedule(); }
      });
    });
    // Holding: a pointer that is moving over it, or keyboard focus inside it. A pointer that merely rests there (the
    // page was scrolled under it) lets go after a few seconds, so the explorer does not stall while the visitor reads.
    var leaveTimer = 0;
    function release() { holding = false; window.clearTimeout(leaveTimer); schedule(); }
    function hold() {
      var was = holding;
      holding = true;
      window.clearTimeout(leaveTimer);
      leaveTimer = window.setTimeout(release, 3500);
      if (!was) { schedule(); }
    }
    root.addEventListener("pointermove", function (e) { if (e.pointerType === "mouse") { hold(); } });
    root.addEventListener("mouseleave", release);
    root.addEventListener("focusin", function () {
      var keyboard = document.activeElement && document.activeElement.matches && document.activeElement.matches(":focus-visible");
      if (keyboard) { holding = true; window.clearTimeout(leaveTimer); schedule(); }
    });
    root.addEventListener("focusout", release);
    root.addEventListener("touchstart", function () { schedule(); }, { passive: true });
    document.addEventListener("visibilitychange", schedule);
    if ("IntersectionObserver" in window) {
      new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) { visible = entry.isIntersecting; schedule(); });
      }, { threshold: 0.4 }).observe(root);
    }
  })();

  // ---- Garage showroom: moves through the five vehicles by itself; swipe, drag or use the arrows ---------
  // One vehicle every 7 s while the showroom is on screen. It waits while the visitor hovers or focuses it, and for a
  // full interval after any manual move (arrows, swipe, drag, wheel, keys). At the end it fades back to the first
  // vehicle instead of sweeping across the track. When motion is not allowed it stays put and offers Auto-play.
  (function showroom() {
    var root = document.querySelector("[data-showroom]");
    if (!root) { return; }
    var track = root.querySelector(".showroom__track");
    var prev = document.querySelector("[data-showroom-prev]");
    var next = document.querySelector("[data-showroom-next]");
    var bar = document.querySelector("[data-showroom-progress]");
    var INTERVAL = 7000;
    var visible = false, holding = false, wrapping = false;

    var gliding = 0;
    // A relaxed ease-in-out over about a second, instead of the browser's quick smooth scroll. Snapping is switched
    // off while it runs so the two never fight. Any hand on the track cancels it.
    function glide(to) {
      var from = track.scrollLeft, delta = to - from, t0 = null;
      window.cancelAnimationFrame(gliding);
      if (Math.abs(delta) < 1) { return; }
      if (reduceMotion && motionStore !== "1" && !autoplayAlways) { track.scrollLeft = to; return; }
      track.style.setProperty("scroll-snap-type", "none");
      function frame(t) {
        if (t0 === null) { t0 = t; }
        var k = Math.min(1, (t - t0) / 1100);
        var e = k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2;
        track.scrollLeft = from + delta * e;
        if (k < 1) { gliding = window.requestAnimationFrame(frame); } else { track.style.removeProperty("scroll-snap-type"); }
      }
      gliding = window.requestAnimationFrame(frame);
    }
    function cancelGlide() {
      if (gliding) { window.cancelAnimationFrame(gliding); gliding = 0; track.style.removeProperty("scroll-snap-type"); }
    }
    function step(dir) {
      var item = track.querySelector(".showroom__item");
      var amount = item ? item.getBoundingClientRect().width + 24 : track.clientWidth * 0.8;
      var max = track.scrollWidth - track.clientWidth;
      glide(Math.max(0, Math.min(max, track.scrollLeft + dir * amount)));
    }
    function atEnd() { return track.scrollLeft > track.scrollWidth - track.clientWidth - 8; }
    function update() {
      var max = track.scrollWidth - track.clientWidth;
      var at = max <= 0 ? 0 : track.scrollLeft / max;
      if (bar) {
        var vis = track.clientWidth / track.scrollWidth;
        bar.style.setProperty("width", Math.round((vis + (1 - vis) * at) * 100) + "%");
      }
      if (prev) { prev.disabled = track.scrollLeft < 8; }
      if (next) { next.disabled = track.scrollLeft > max - 8; }
    }

    // The same steady tick as the explorer: the 7 s count only runs while the garage is eligible, and anything that
    // changes that starts it again, so a missed event can never stall it.
    var dwell = 0, last = Date.now(), wasOk = false;
    function eligible() { return motionAllowed() && !holding && visible && !document.hidden && !wrapping; }
    function schedule() { dwell = 0; last = Date.now(); wasOk = eligible(); }
    function advance() {
      if (atEnd()) {
        wrapping = true;
        track.classList.add("is-wrapping");
        window.setTimeout(function () {
          track.scrollTo({ left: 0, behavior: "auto" });
          track.classList.remove("is-wrapping");
          wrapping = false;
          schedule();
        }, 420);
      } else {
        step(1);
      }
      schedule();
    }
    window.setInterval(function () {
      var now = Date.now(), dt = Math.min(now - last, 1000);
      last = now;
      var ok = eligible();
      if (ok !== wasOk) { schedule(); return; }
      if (!ok) { return; }
      dwell += dt;
      if (dwell >= INTERVAL) { advance(); }
    }, 250);
    // Any manual move counts as interaction: the clock restarts, so nothing moves under the visitor's hand.
    function touched() { schedule(); }

    if (prev) { prev.addEventListener("click", function () { step(-1); touched(); }); }
    if (next) { next.addEventListener("click", function () { step(1); touched(); }); }
    track.addEventListener("scroll", function () { window.requestAnimationFrame(update); }, { passive: true });
    track.addEventListener("keydown", function (e) {
      if (e.key === "ArrowRight") { e.preventDefault(); step(1); touched(); }
      if (e.key === "ArrowLeft") { e.preventDefault(); step(-1); touched(); }
    });
    ["wheel", "touchstart", "pointerdown"].forEach(function (name) { track.addEventListener(name, function () { cancelGlide(); touched(); }, { passive: true }); });
    window.addEventListener("resize", update);
    update();

    // Hold while a pointer is moving over the section, or keyboard focus is inside it (the arrows sit in the heading row,
    // so the whole section counts). A pointer that merely rests there lets go after a few seconds.
    var zone = root.closest("section") || root;
    var leaveTimer = 0;
    function release() { holding = false; window.clearTimeout(leaveTimer); schedule(); }
    zone.addEventListener("pointermove", function (e) {
      if (e.pointerType !== "mouse") { return; }
      holding = true;
      window.clearTimeout(leaveTimer);
      leaveTimer = window.setTimeout(release, 3500);
    });
    zone.addEventListener("mouseleave", release);
    zone.addEventListener("focusin", function () {
      var keyboard = document.activeElement && document.activeElement.matches && document.activeElement.matches(":focus-visible");
      if (keyboard) { holding = true; window.clearTimeout(leaveTimer); }
    });
    zone.addEventListener("focusout", release);
    document.addEventListener("visibilitychange", schedule);
    document.addEventListener("tv:motion", schedule);
    if ("IntersectionObserver" in window) {
      new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) { visible = entry.isIntersecting; schedule(); });
      }, { threshold: 0.5 }).observe(root);
    }

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

  // ---- Characters page: the jump bar follows the reader, and the relationship network answers the pointer -------
  (function castNavigation() {
    var nav = document.querySelector("[data-cast-nav]");
    if (nav) {
      var links = [].slice.call(nav.querySelectorAll("a[href^='#']")).filter(function (a) {
        return a.getAttribute("href").length > 1 && !a.hasAttribute("data-open-explore");
      });
      var targets = links.map(function (a) { return document.getElementById(a.getAttribute("href").slice(1)); });
      var list = nav.querySelector("ol");
      var setCurrent = function (id) {
        if (!id && list && list.scrollLeft > 0) { list.scrollTo({ left: 0, behavior: reduceMotion ? "auto" : "smooth" }); }   // nobody marked: the bar goes back to its start
        links.forEach(function (a) {
          var on = a.getAttribute("href") === "#" + id;
          if (on) { a.setAttribute("aria-current", "true"); } else { a.removeAttribute("aria-current"); }
          if (on && list && list.scrollWidth > list.clientWidth) {
            list.scrollTo({ left: a.offsetLeft - (list.clientWidth - a.offsetWidth) / 2, behavior: reduceMotion ? "auto" : "smooth" });
          }
        });
      };
      if (targets.some(Boolean)) {
        // The reading line sits a little above the middle of the screen. The person whose block holds it is marked; where
        // two blocks do, the one that began last wins and, on a tie (side by side), the first. A name the visitor has
        // just chosen stays marked until it has been on screen and has left again, so a click is never contradicted.
        var queued = false, locked = null, lockedAt = 0, lockSeen = false;
        var onScreen = function (t) {
          var r = t.getBoundingClientRect();
          return r.top < window.innerHeight * 0.75 && r.bottom > window.innerHeight * 0.25;
        };
        var evaluate = function () {
          queued = false;
          if (locked) {
            var held = document.getElementById(locked);
            if (held && onScreen(held)) { lockSeen = true; setCurrent(locked); return; }
            if (held && !lockSeen && Date.now() - lockedAt < 2200) { setCurrent(locked); return; }
            locked = null;
          }
          var line = window.innerHeight * 0.45, best = null, bestTop = -Infinity;
          targets.forEach(function (t, i) {
            if (!t) { return; }
            var r = t.getBoundingClientRect();
            if (r.top > line || r.bottom < line) { return; }
            if (r.top > bestTop + 1) { bestTop = r.top; best = links[i].getAttribute("href").slice(1); }
          });
          if (!best) {
            // in a gap between two people the last one stays marked; above the first, nobody is
            var first = targets.filter(Boolean)[0];
            if (first && first.getBoundingClientRect().top <= line) { return; }
          }
          setCurrent(best || "");
        };
        var schedule = function () { if (!queued) { queued = true; window.requestAnimationFrame(evaluate); } };
        links.forEach(function (a) {
          a.addEventListener("click", function () { locked = a.getAttribute("href").slice(1); lockedAt = Date.now(); lockSeen = false; schedule(); });
        });
        window.addEventListener("scroll", schedule, { passive: true });
        window.addEventListener("resize", schedule);
        evaluate();
      }
      var open = nav.querySelector("[data-open-explore]");
      if (open) {
        open.addEventListener("click", function () {
          var panel = document.getElementById("explore");
          if (panel && panel.tagName === "DETAILS") { panel.open = true; }
        });
      }
    }
    var web = document.querySelector("[data-network]");
    if (web) {
      var edges = [].slice.call(web.querySelectorAll(".edge"));
      var light = function (slug) {
        var any = false;
        edges.forEach(function (edge) {
          var on = !!slug && (edge.getAttribute("data-from") === slug || edge.getAttribute("data-to") === slug);
          edge.classList.toggle("is-on", on);
          any = any || on;
        });
        web.classList.toggle("is-focus", any);
      };
      [].forEach.call(web.querySelectorAll(".node"), function (node) {
        var slug = node.getAttribute("data-slug");
        ["mouseenter", "focus"].forEach(function (n) { node.addEventListener(n, function () { light(slug); }); });
        ["mouseleave", "blur"].forEach(function (n) { node.addEventListener(n, function () { light(""); }); });
      });
    }
  })();

  // ---- Motion portraits: one complete playback per genuine visit ------------------------------------------------
  // A sequence is one file: the artwork, a dissolve into the clip, the whole clip at true speed, a dissolve back, the
  // artwork held. It starts on its own still, so there is nothing to match up. Each tile is a small state machine
  // (data-state on the tile):
  //
  //   armed    at its artwork, waiting for a visit
  //   playing  its sequence is running (never more than one tile at a time)
  //   rested   it has played once and rests on the artwork; it stays put for as long as the visitor stays near it
  //
  //   armed -> playing   at least half of the tile is in view for DWELL ms, nothing else is playing, the whole file is
  //                      buffered, and it is this tile's turn (see pick)
  //   playing -> rested  the sequence ended
  //   playing -> armed   the visitor scrolled away mid-way (or motion was switched off, the tab was hidden): it stops and
  //                      returns to a clean artwork, so a half-dissolved frame is never left on screen
  //   rested -> armed    the tile has genuinely left the view (REARM: nearly none of it visible, and the sticky bars
  //                      count as covering the top of the screen): the next visit plays it again
  //
  // Entry needs half the tile, exit needs it almost gone, so a tile hovering at the edge of the screen neither flickers
  // nor replays. When several tiles are in view together they play one after another: rows in the direction the visitor
  // is scrolling, left to right within a row, and each is only ever waiting for the one before it, never skipped.
  (function portraits() {
    var tiles = [].slice.call(document.querySelectorAll("[data-portrait]"));
    if (!tiles.length) { return; }
    window.tvMedia = window.tvMedia || { cast: false, cinema: false, modal: false };
    var players = tiles.map(function (el) {
      var video = el.querySelector("[data-portrait-video]");
      return { el: el, video: video, src: video && video.getAttribute("data-src"), state: "armed", ratio: 0, since: 0, loaded: false, blocked: false };
    }).filter(function (p) { return p.video && p.src; });
    if (!players.length) { return; }

    var DWELL = 380;            // ms a tile must stay at least half in view before its sequence starts
    var ENTER = 0.5;            // share of the tile that must be in view to start
    var KEEP = 0.15;            // below this a running sequence is stopped
    var REARM = 0.02;           // below this a finished tile is armed for the next visit
    var dir = 1, lastY = window.scrollY;
    window.addEventListener("scroll", function () {
      var y = window.scrollY;
      if (Math.abs(y - lastY) > 2) { dir = y > lastY ? 1 : -1; lastY = y; }
    }, { passive: true });

    function setState(p, state) { p.state = state; p.el.setAttribute("data-state", state); }
    function allowed() {
      return motionAllowed() && !document.hidden && !window.tvMedia.cinema && !window.tvMedia.cast && !window.tvMedia.modal;
    }
    function load(p) {
      if (p.loaded) { return; }
      p.loaded = true;
      p.video.preload = "auto";
      p.video.src = p.src;
      p.video.load();
    }
    function toArtwork(p) {                       // stop and go back to the artwork (the file stays cached in the element)
      p.video.pause();
      try { if (p.video.currentTime !== 0) { p.video.currentTime = 0; } } catch (e) { /* not ready */ }
      p.el.classList.remove("is-live", "is-rest");
      setState(p, "armed");
    }
    function finish(p) {                           // it has played to the end: rest on the artwork
      if (p.state === "rested") { return; }
      setState(p, "rested");
      p.el.classList.add("is-rest");
      // rest on the held artwork (older loops end on a black fade-out frame, so step back from the end)
      try { if (p.video.duration > 0.8) { p.video.currentTime = p.video.duration - 0.6; } } catch (e) { /* not seekable */ }
    }
    function start(p) {
      if (p.state === "playing") { return; }
      load(p);
      if (p.video.readyState < 4) { return; }     // wait until the whole sequence can play straight through without stalling
      setState(p, "playing");
      p.el.classList.remove("is-rest");
      var promise = p.video.play();
      if (promise && typeof promise.catch === "function") {
        promise.catch(function (err) {
          if (p.state !== "playing") { return; }
          if (err && err.name === "NotAllowedError") { p.blocked = true; p.el.classList.add("is-blocked"); }   // the still stays, a Play button shows
          toArtwork(p);                            // refused or interrupted before it began: armed again
        });
      }
    }
    function pick(candidates) {
      // rows in the direction of travel, left to right inside a row
      return candidates.map(function (p) {
        var r = p.el.getBoundingClientRect();
        return { p: p, row: Math.round(r.top / 40), left: r.left };
      }).sort(function (a, b) { return a.row !== b.row ? (a.row - b.row) * dir : a.left - b.left; })[0].p;
    }
    function reconcile() {
      var runner = null;
      players.forEach(function (p) {
        if (p.video.ended && p.state === "playing") { finish(p); }
        if (p.state === "playing") {
          if (p.video.paused || !allowed() || p.ratio < KEEP) { toArtwork(p); } else { runner = p; }
        } else if (p.state === "rested" && p.ratio < REARM) {
          toArtwork(p);                            // the visit is over: ready for the next one
        }
      });
      if (!runner && allowed()) {
        var now = Date.now(), ready = [], waiting = false;
        players.forEach(function (p) {
          if (p.state !== "armed" || p.blocked || p.ratio < ENTER) { return; }
          if (now - p.since < DWELL) { waiting = true; return; }
          ready.push(p);
        });
        if (ready.length) { start(pick(ready)); } else if (waiting) { window.setTimeout(reconcile, DWELL + 20); }
      }
      window.tvMedia.portrait = players.some(function (p) { return p.state === "playing"; });
    }
    players.forEach(function (p) {
      p.video.muted = true;
      p.el.setAttribute("data-state", "armed");
      var at = parseFloat(p.video.getAttribute("data-poster-at"));
      var takeover = isNaN(at) ? 0.32 : at;       // the video time at which the clip's own picture replaces the still
      p.video.addEventListener("playing", function () {
        if (takeover === 0) { p.el.classList.add("is-live"); }   // the sequence starts on its still: nothing to wait for
      });
      p.video.addEventListener("timeupdate", function () {
        if (p.state === "playing" && takeover > 0 && p.video.currentTime >= takeover && !p.el.classList.contains("is-live")) { p.el.classList.add("is-live"); }
      });
      p.video.addEventListener("pause", reconcile);
      p.video.addEventListener("canplaythrough", reconcile);
      p.video.addEventListener("seeked", reconcile);
      p.video.addEventListener("ended", function () { if (p.state === "playing") { finish(p); } reconcile(); });
      var button = p.el.querySelector("[data-motion-optin]");
      if (button) {
        button.addEventListener("click", function () { p.blocked = false; p.since = 0; p.el.classList.remove("is-blocked"); window.setTimeout(reconcile, 0); });
      }
    });
    if ("IntersectionObserver" in window) {
      var near = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          var p = players.filter(function (q) { return q.el === entry.target; })[0];
          if (p && entry.isIntersecting && motionAllowed()) { load(p); }
        });
      }, { rootMargin: "60% 0px 60% 0px" });
      // the sticky header and jump bar cover the top of the screen: a tile under them is not in view
      var see = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          var p = players.filter(function (q) { return q.el === entry.target; })[0];
          if (!p) { return; }
          var was = p.ratio >= ENTER;
          p.ratio = entry.isIntersecting ? entry.intersectionRatio : 0;
          if (p.ratio >= ENTER && !was) { p.since = Date.now(); }
        });
        reconcile();
      }, { rootMargin: "-" + (document.querySelector("[data-cast-nav]") ? 120 : 64) + "px 0px 0px 0px", threshold: [0, 0.02, 0.15, 0.3, 0.5, 0.75, 1] });
      players.forEach(function (p) { near.observe(p.el); see.observe(p.el); });
    }
    document.addEventListener("visibilitychange", reconcile);
    document.addEventListener("tv:motion", reconcile);
    document.addEventListener("tv:state", reconcile);
    window.setInterval(function () { if (!document.hidden) { reconcile(); } }, 1000);
    reconcile();
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
    var videoTitle = videoDialog.querySelector("[data-title]");
    videoDialog.addEventListener("close", function () {
      playerBox.textContent = ""; // stops playback
      window.tvMedia = window.tvMedia || {};
      window.tvMedia.modal = false;
      document.dispatchEvent(new Event("tv:state"));
    });
    document.querySelectorAll("[data-video]").forEach(function (trigger) {
      trigger.addEventListener("click", function () {
        var frame = document.createElement("iframe");
        frame.src = trigger.getAttribute("data-video");
        frame.title = trigger.getAttribute("data-title") || "Official video";
        frame.allow = "autoplay; fullscreen; picture-in-picture";
        playerBox.textContent = "";
        playerBox.appendChild(frame);
        if (videoTitle) { videoTitle.textContent = (trigger.getAttribute("data-title") || "").replace(/^Grand Theft Auto VI[:,]?\s*/, ""); }
        videoCaption.textContent = "Official trailer \u00b7 \u00a9 Rockstar Games";
        window.tvMedia = window.tvMedia || {};
        window.tvMedia.modal = true;
        document.dispatchEvent(new Event("tv:state"));
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
