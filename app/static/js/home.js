// Team Valkyrie | Home | the picture challenge ("How well do you know Leonida?"). Progressive enhancement only: without this file the section is three plain links.
// Five of Rockstar's own pictures, one at a time. The data is server-rendered JSON in an attribute (the same database rows the Characters, Leonida and Garage pages show; the site allows no inline script blocks); every picture address is rebuilt here
// from Rockstar's image prefix and checked against it again, every name is set with textContent, and nothing is requested until the section is near the window.
(function () {
  "use strict";
  var root = document.querySelector("[data-quiz]");
  if (!root) { return; }
  var ui = root.querySelector("[data-quiz-ui]");
  var raw = root.getAttribute("data-quiz-data");
  if (!raw || !ui) { return; }
  var data;
  try { data = JSON.parse(raw); } catch (e) { return; }
  var prefix = root.getAttribute("data-prefix") || "";
  if (prefix.indexOf("https://www.rockstargames.com/") !== 0 || !data || !data.pools || !data.answers) { return; }

  var KINDS = Object.keys(data.pools).filter(function (k) { return data.answers[k] && data.pools[k].length; });
  if (KINDS.length < 2) { return; }
  var ASK = { people: "Who is this?", places: "Which place is this?", machines: "Which machine is this?" };
  var LEAD = { people: "Rockstar files this picture under ", places: "Rockstar files this picture under ", machines: "it is the " };
  var MORE = { people: "Read the profile", places: "Explore the place", machines: "Open its page" };
  var SAFE_NAME = /^[A-Za-z0-9._~%+-]+$/;

  var $ = function (name) { return root.querySelector("[data-quiz-" + name + "]"); };
  var frame = $("img").parentNode, img = $("img"), veil = $("veil");
  var roundEl = $("round"), scoreEl = $("score"), askEl = $("ask"), optionsEl = $("options");
  var revealEl = $("reveal"), verdictEl = $("verdict"), lineEl = $("line"), whoEl = $("who"), linkEl = $("link"), nextBtn = $("next");
  var endEl = $("end"), totalEl = $("total"), noteEl = $("note"), againBtn = $("again");

  var total = Math.min(parseInt(root.getAttribute("data-rounds"), 10) || 5, 5);
  var rounds = [], at = 0, score = 0, started = false, answered = false;

  function shuffle(list) {
    for (var i = list.length - 1; i > 0; i--) { var j = Math.floor(Math.random() * (i + 1)); var t = list[i]; list[i] = list[j]; list[j] = t; }
    return list;
  }
  function address(path) {
    return SAFE_NAME.test(path) ? prefix + path + "?akim=1&imdensity=1&imwidth=960" : null;
  }
  function optionsFor(kind, answer) {
    var others = shuffle(Object.keys(data.answers[kind]).filter(function (s) { return s !== answer; })).slice(0, 3);
    return shuffle([answer].concat(others));
  }
  function plan() {
    var order = shuffle(KINDS.slice()), kinds = [], i;
    for (i = 0; i < total; i++) { kinds.push(order[i % order.length]); }
    shuffle(kinds);
    var taken = {};
    rounds = kinds.map(function (kind) {
      var pool = data.pools[kind].filter(function (q) { return !taken[kind + ":" + q.a]; });
      if (!pool.length) { pool = data.pools[kind]; }
      var q = pool[Math.floor(Math.random() * pool.length)];
      taken[kind + ":" + q.a] = true;
      return { kind: kind, path: q.p, answer: q.a, options: optionsFor(kind, q.a), url: address(q.p) };
    }).filter(function (r) { return r.url; });
  }

  function setText(el, text) { el.textContent = text; }
  function show(el, on) { el.hidden = !on; }

  function load(round, done) {
    frame.classList.remove("is-loaded");
    img.alt = "";
    var probe = new Image();
    probe.referrerPolicy = "no-referrer";
    probe.onload = function () { img.src = round.url; frame.classList.add("is-loaded"); done(true); };
    probe.onerror = function () { done(false); };
    probe.src = round.url;
  }
  function warmNext() {
    var next = rounds[at + 1];
    if (next && !next.warm) { next.warm = true; var p = new Image(); p.referrerPolicy = "no-referrer"; p.src = next.url; }
  }

  function render() {
    var round = rounds[at];
    answered = false;
    show(revealEl, false); show(endEl, false);
    setText(roundEl, "Picture " + (at + 1) + " of " + rounds.length);
    setText(scoreEl, score + " right");
    setText(askEl, ASK[round.kind] || "Who or what is this?");
    optionsEl.textContent = "";
    round.options.forEach(function (slug) {
      var b = document.createElement("button");
      b.type = "button"; b.className = "quiz__opt"; b.setAttribute("data-slug", slug);
      b.textContent = data.answers[round.kind][slug].n;
      b.addEventListener("click", function () { answer(slug); });
      optionsEl.appendChild(b);
    });
    var failed = false;
    load(round, function (ok) {
      if (ok) { warmNext(); return; }
      if (failed) { return; }
      failed = true;                                  // a picture Rockstar no longer serves: carry on with the next one instead of showing an empty frame
      rounds.splice(at, 1);
      if (!rounds.length) { ui.hidden = true; root.classList.add("is-broken"); return; }
      if (at >= rounds.length) { finish(); } else { render(); }
    });
  }

  function answer(slug) {
    if (answered) { return; }
    answered = true;
    var round = rounds[at], info = data.answers[round.kind][slug], truth = data.answers[round.kind][round.answer], right = slug === round.answer;
    if (right) { score += 1; }
    [].slice.call(optionsEl.querySelectorAll(".quiz__opt")).forEach(function (b) {
      var s = b.getAttribute("data-slug");
      b.disabled = true;
      if (s === round.answer) { b.classList.add("is-right"); } else if (s === slug) { b.classList.add("is-wrong"); }
    });
    img.alt = "Rockstar’s picture: " + truth.n;
    setText(scoreEl, score + " right");
    verdictEl.className = "quiz__verdict " + (right ? "is-right" : "is-wrong");
    setText(verdictEl, (right ? "Right: " : "Not quite: ") + LEAD[round.kind] + truth.n + ".");
    setText(lineEl, (truth.t && round.kind !== "places" ? truth.t + ". " : "") + truth.s);
    var here = (truth.b || []).slice(0, 2);
    if (here.length) {
      setText(whoEl, "Rockstar’s own text places " + here.map(function (b) { return b.n; }).join(" and ") + " here: " + here.map(function (b) { return b.t.replace(/\.$/, ""); }).join("; ") + ".");
      show(whoEl, true);
    } else { show(whoEl, false); }
    if (truth.h && truth.h.charAt(0) === "/" && truth.h.charAt(1) !== "/") { linkEl.setAttribute("href", truth.h); linkEl.hidden = false; } else { linkEl.hidden = true; }
    setText(linkEl, (MORE[round.kind] || "Read more") + ": " + truth.n);
    setText(nextBtn, at + 1 >= rounds.length ? "See your result" : "Next picture");
    show(revealEl, true);
    nextBtn.focus({ preventScroll: true });
  }

  function finish() {
    show(revealEl, false);
    optionsEl.textContent = "";
    setText(roundEl, "Done");
    setText(scoreEl, score + " right");
    setText(askEl, "Your result");
    var n = rounds.length;
    setText(totalEl, "You named " + score + " of " + n + ".");
    setText(noteEl, score === n ? "Every one. Leonida has no secrets from you." : score >= Math.ceil(n / 2) ? "Well spotted. The people, places and machines above have more to show you." : "Leonida has more to show you: start with the people, the places or the machines.");
    show(endEl, true);
    totalEl.setAttribute("tabindex", "-1");
    totalEl.focus({ preventScroll: true });
  }

  nextBtn.addEventListener("click", function () {
    at += 1;
    if (at >= rounds.length) { finish(); } else { render(); askEl.focus({ preventScroll: true }); }
  });
  againBtn.addEventListener("click", function () { start(); askEl.focus({ preventScroll: true }); });

  function start() {
    at = 0; score = 0;
    plan();
    if (!rounds.length) { ui.hidden = true; return; }
    render();
  }

  ui.hidden = false;
  // nothing is requested until the section is near the window (about a screen away), and then one picture at a time
  var begin = function () { if (!started) { started = true; start(); } };
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      if (entries.some(function (e) { return e.isIntersecting; })) { io.disconnect(); begin(); }
    }, { rootMargin: "100% 0px 100% 0px" });
    io.observe(root);
  } else { begin(); }
})();
