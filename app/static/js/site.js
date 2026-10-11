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
      heroBg.style.setProperty("transform", "translate3d(0," + Math.round(Math.min(y * 0.1, heroBg.offsetHeight * 0.07)) + "px,0)");
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

  // ---- Cast stage: one frame, eight people, about four seconds each -----------------------------
  // One reel file is buffered once. Choosing a person seeks straight to that person's segment (keyframes sit
  // at every start, so it is instant), plays it once and holds on the final frame. "Play whole reel" runs
  // all eight in order and loops. Both controls are in the markup from the first paint and are never hidden:
  // the script only changes their state.
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
    var state = { index: 0, mode: "reel", motion: !calm, visible: false, loaded: false, held: false, started: false };
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
      state.mode = "single";
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
      document.addEventListener("tv:state", function () { if (window.tvMedia.cinema && !video.paused) { video.pause(); } });
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
          if (entry.isIntersecting && !calm) { ensureLoaded(); obs.disconnect(); }
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
    render();
  })();

  // ---- The cinematic moments: native video, muted, started and stopped by scrolling ---------------------
  // Up to three sections, each a plain <video> over its own poster. No third-party player. Rules:
  //  * One video plays at a time: the most visible eligible section wins; the cast reel and the trailer overlay
  //    count too (window.tvMedia).
  //  * Muted autoplay on entry, paused on exit. A moment plays once and holds its last frame; Replay is offered.
  //  * Sound is the visitor's choice. Browsers refuse audible autoplay until the page has been interacted with, so
  //    nothing is unmuted before a deliberate click on Enable sound. The choice is remembered for the visit, and
  //    later moments then start with sound (faded in) where the browser allows it.
  //  * Reduced motion, data saver and slow connections get the poster and a Play button; nothing autoplays.
  window.tvMedia = window.tvMedia || { cast: false, cinema: false, modal: false };
  (function cinemas() {
    var roots = [].slice.call(document.querySelectorAll("[data-cinema]"));
    var players = [];
    roots.forEach(function (root) {
      var video = root.querySelector("[data-cinema-video]");
      if (!video) { return; }
      players.push({
        root: root, video: video,
        toggleBtn: root.querySelector("[data-cinema-toggle]"), toggleLabel: root.querySelector("[data-cinema-toggle-label]"),
        soundBtn: root.querySelector("[data-cinema-sound]"), soundLabel: root.querySelector("[data-cinema-sound-label]"),
        ratio: 0, loaded: false, failed: false, ended: false, userPaused: false, requested: false, ramp: 0
      });
    });
    if (!players.length) { return; }

    var slow = !!(navigator.connection && /(^|-)(2g|3g)$/.test(navigator.connection.effectiveType || ""));
    var automatic = !calm && !slow;
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
      var v = p.video;
      var playing = !v.paused && !v.ended;
      if (p.toggleBtn) {
        p.toggleBtn.hidden = p.failed;
        p.toggleBtn.classList.toggle("is-paused", !playing && !p.ended);
        p.toggleBtn.classList.toggle("is-ended", p.ended);
        var text = p.ended ? "Replay" : (playing ? "Pause" : "Play");
        p.toggleBtn.setAttribute("aria-label", p.ended ? "Replay the footage" : (playing ? "Pause the footage" : "Play the footage"));
        if (p.toggleLabel) { p.toggleLabel.textContent = text; }
      }
      if (p.soundBtn) {
        p.soundBtn.hidden = p.failed || (!p.loaded && automatic);
        p.soundBtn.setAttribute("aria-pressed", String(soundOn));
        if (p.soundLabel) { p.soundLabel.textContent = soundOn ? "Sound on" : "Enable sound"; }
      }
    }

    function load(p) {
      if (p.loaded || p.failed) { return; }
      p.loaded = true;
      p.video.preload = "auto";
      p.video.load();
    }

    function start(p) {
      if (!p.video.paused || p.ended || p.video.ended) { return; }   // a finished moment holds its last frame
      load(p);
      var withSound = soundOn && activated();
      p.video.muted = !withSound;
      p.video.volume = withSound ? 0 : 1;
      var promise = p.video.play();
      if (promise && typeof promise.catch === "function") {
        promise.catch(function () {
          if (withSound) {          // the browser refused audible playback: carry on silently
            p.video.muted = true; p.video.volume = 1;
            safePlay(p.video);
          }
        });
      }
      if (withSound) { ramp(p, 1, 400); }
      window.tvMedia.cinema = true;
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
        var eligible = !blocked && !p.failed && !p.ended && !p.userPaused && p.ratio >= 0.35 && (automatic || p.requested);
        if (eligible && (!best || p.ratio > best.ratio)) { best = p; }
      });
      players.forEach(function (p) {
        if (p === best) { start(p); } else { stop(p); }
      });
      window.tvMedia.cinema = players.some(function (p) { return !p.video.paused; });
      players.forEach(labels);
    }

    players.forEach(function (p) {
      var v = p.video;
      v.muted = true;
      v.addEventListener("playing", function () { p.root.classList.add("is-live"); labels(p); document.dispatchEvent(new Event("tv:state")); });
      v.addEventListener("pause", function () {
        // The browser fires pause just before ended: note the end first so nothing restarts a finished moment.
        if (v.ended || (v.duration && v.currentTime >= v.duration - 0.05)) { p.ended = true; p.root.classList.add("is-ended"); }
        window.tvMedia.cinema = players.some(function (q) { return !q.video.paused; });
        labels(p);
        document.dispatchEvent(new Event("tv:state"));
      });
      v.addEventListener("volumechange", function () { labels(p); });
      v.addEventListener("ended", function () {
        p.ended = true;
        p.root.classList.add("is-ended");
        window.tvMedia.cinema = false;
        labels(p);
        apply();
      });
      v.addEventListener("error", function () { p.failed = true; p.root.classList.remove("is-live"); labels(p); apply(); });

      if (p.toggleBtn) {
        p.toggleBtn.addEventListener("click", function () {
          p.requested = true;
          if (p.ended) {                       // replay from the start
            p.ended = false; p.userPaused = false;
            p.root.classList.remove("is-ended");
            try { v.currentTime = 0; } catch (e) { /* not seekable yet */ }
            apply(); start(p); return;
          }
          if (!v.paused) { p.userPaused = true; v.pause(); }
          else { p.userPaused = false; p.ratio = Math.max(p.ratio, 0.35); apply(); start(p); }
          labels(p);
        });
      }
      if (p.soundBtn) {
        p.soundBtn.addEventListener("click", function () {
          soundOn = !soundOn;
          try { window.sessionStorage.setItem("tv-sound", soundOn ? "1" : "0"); } catch (e) { /* ignore */ }
          players.forEach(function (q) {
            if (q.video.paused) { return; }
            if (soundOn) { q.video.muted = false; q.video.volume = 0; ramp(q, 1, 400); } else { q.video.muted = true; }
          });
          if (soundOn && p.video.paused && !p.ended) { p.userPaused = false; p.requested = true; start(p); }
          players.forEach(labels);
        });
      }
    });

    if ("IntersectionObserver" in window) {
      var near = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          var p = players.filter(function (q) { return q.root === entry.target; })[0];
          if (p && entry.isIntersecting && automatic) { load(p); }
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
    document.addEventListener("visibilitychange", apply);
    document.addEventListener("tv:state", apply);
    players.forEach(labels);
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
