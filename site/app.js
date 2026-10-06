/* Behaviour for the built page: saved ticks, picture loading, picture viewer.
   The page is fully rendered by tools/build.py; nothing here creates content. */
(function () {
  "use strict";
  var KEY = "indx-c1-8t-plan-v1"; // storage key for ticks; row ids in plan/*.yaml are the values
  var wrap = document.getElementById("wrap");
  var nav = document.getElementById("navlinks");
  var boxes = [].slice.call(document.querySelectorAll(".step input[type=checkbox]"));
  var state = {};
  try { state = JSON.parse(localStorage.getItem(KEY) || "{}") || {}; } catch (e) { state = {}; }
  function saveLocal() { try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {} }

  /* ---- "Your build" options: each toggles a class on .wrap; generated CSS hides rows that do not apply ---- */
  var optBoxes = [].slice.call(document.querySelectorAll("input[data-opt]"));
  var opts = {};
  optBoxes.forEach(function (b) { opts[b.getAttribute("data-opt")] = b.checked; }); // defaults from plan/options.yaml
  try {
    var savedOpts = JSON.parse(localStorage.getItem(KEY + "-opts") || "null");
    if (savedOpts) Object.keys(opts).forEach(function (k) { if (typeof savedOpts[k] === "boolean") opts[k] = savedOpts[k]; });
  } catch (e) {}
  function saveOpts() { try { localStorage.setItem(KEY + "-opts", JSON.stringify(opts)); } catch (e) {} }
  function applyOpts() {
    optBoxes.forEach(function (b) {
      var k = b.getAttribute("data-opt");
      b.checked = !!opts[k];
      wrap.classList.toggle("on-" + k, !!opts[k]);
    });
  }
  function applies(el) {
    var w = el.getAttribute("data-when"), u = el.getAttribute("data-unless");
    if (w && !w.split(" ").every(function (k) { return opts[k]; })) return false;
    if (u && u.split(" ").some(function (k) { return opts[k]; })) return false;
    return true;
  }

  function paint() {
    var done = 0, total = 0, per = {};
    boxes.forEach(function (b) {
      var on = !!state[b.getAttribute("data-id")], li = b.closest(".step"), ph = li.getAttribute("data-phase");
      b.checked = on;
      li.classList.toggle("checked", on);
      if (!applies(li)) return; // rows hidden by an option do not count
      total++;
      per[ph] = per[ph] || [0, 0];
      per[ph][1]++;
      if (on) { done++; per[ph][0]++; }
    });
    document.getElementById("progress-n").textContent = done;
    document.getElementById("progress-d").textContent = total;
    [].forEach.call(nav.querySelectorAll("a"), function (a) {
      var c = per[a.getAttribute("data-phase")];
      a.classList.toggle("done", !!c && c[0] === c[1]);
    });
  }

  var syncEl = document.getElementById("sync");
  function say(t) { syncEl.textContent = t; }

  /* ---- account sync (only inside a claude.ai artifact; otherwise ticks stay in this browser) ---- */
  var docRef = null, writing = false, dirty = false, timer = null, dead = false, retried = false;
  function body() { return { checked: Object.keys(state).filter(function (k) { return state[k]; }).sort(), options: opts }; }
  function flush() {
    if (!docRef || dead || writing || !dirty) return;
    writing = true; dirty = false;
    docRef.set(body()).then(function () {
      writing = false; retried = false; say("Ticks and choices sync to your account."); if (dirty) flush();
    }, function (e) {
      writing = false;
      var code = e && e.code;
      if ((code === "unavailable" || !code) && !retried) { retried = true; dirty = true; setTimeout(flush, 1500 + Math.random() * 1500); return; }
      if (code === "unavailable" || code === "resource_exhausted") { dirty = true; say("Sync is paused. Ticks are saved in this browser."); return; }
      dead = true; say("Ticks are saved in this browser only.");
    });
  }
  function queue() { if (!docRef || dead) return; dirty = true; clearTimeout(timer); timer = setTimeout(flush, 700); }
  function changed() { saveLocal(); paint(); queue(); }

  boxes.forEach(function (b) {
    b.addEventListener("change", function () {
      var id = b.getAttribute("data-id");
      if (b.checked) state[id] = true; else delete state[id];
      changed();
    });
  });

  optBoxes.forEach(function (b) {
    b.addEventListener("change", function () {
      opts[b.getAttribute("data-opt")] = b.checked;
      saveOpts(); applyOpts(); paint(); queue();
    });
  });
  applyOpts();

  /* ---- view toggles (per browser) ---- */
  function toggle(id, cls, storeKey, invert) {
    var el = document.getElementById(id);
    try { var v = localStorage.getItem(KEY + storeKey); if (v !== null) el.checked = v === "1"; } catch (e) {}
    function apply() { document.body.classList.toggle(cls, invert ? !el.checked : el.checked); }
    el.addEventListener("change", function () { apply(); try { localStorage.setItem(KEY + storeKey, el.checked ? "1" : "0"); } catch (e) {} });
    apply();
  }
  toggle("hide-done", "hide-done", "-hide", false);
  toggle("show-pics", "no-pics", "-pics", true);

  var reset = document.getElementById("reset"), armed = null;
  reset.addEventListener("click", function () {
    if (!armed) { reset.textContent = "Really clear all?"; armed = setTimeout(function () { armed = null; reset.textContent = "Clear ticks"; }, 4000); return; }
    clearTimeout(armed); armed = null; reset.textContent = "Clear ticks"; state = {}; changed();
  });

  paint();

  /* ---- pictures: each step has one strip image; every .pic shows one 4:3 cell of it ---- */
  function cellStyle(el, src, n, i) {
    el.style.backgroundImage = 'url("' + src + '")';
    el.style.backgroundSize = (n * 100) + "% 100%";
    el.style.backgroundPosition = (n > 1 ? (i / (n - 1)) * 100 : 0) + "% 0";
  }
  function load(group) {
    if (group.getAttribute("data-loaded")) return;
    group.setAttribute("data-loaded", "1");
    var src = group.getAttribute("data-img"), n = +group.getAttribute("data-n");
    [].forEach.call(group.querySelectorAll(".pic"), function (p, i) { cellStyle(p, src, n, i); });
  }
  var groups = [].slice.call(document.querySelectorAll(".pics"));
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) { load(en.target); io.unobserve(en.target); } });
    }, { rootMargin: "700px 0px" });
    groups.forEach(function (g) { io.observe(g); });
  } else {
    groups.forEach(load);
  }

  /* ---- picture viewer ---- */
  var lb = document.getElementById("lb"), lbImg = document.getElementById("lb-img"), lbCap = document.getElementById("lb-cap");
  var lbPrev = document.getElementById("lb-prev"), lbNext = document.getElementById("lb-next"), lbClose = document.getElementById("lb-close");
  var cur = null, opener = null;
  function show() {
    cellStyle(lbImg, cur.src, cur.n, cur.i);
    lbCap.textContent = cur.label + " · picture " + (cur.i + 1) + " of " + cur.n;
    lbPrev.disabled = cur.i === 0;
    lbNext.disabled = cur.i === cur.n - 1;
  }
  function open(pic) {
    var g = pic.parentNode;
    load(g);
    opener = pic;
    cur = { src: g.getAttribute("data-img"), n: +g.getAttribute("data-n"), i: +pic.getAttribute("data-i"), label: g.getAttribute("data-label") };
    lb.hidden = false;
    show();
    lbClose.focus();
  }
  function close() { lb.hidden = true; cur = null; if (opener) opener.focus(); }
  function step(d) { if (!cur) return; var i = cur.i + d; if (i < 0 || i >= cur.n) return; cur.i = i; show(); }
  document.addEventListener("click", function (e) {
    var pic = e.target.closest ? e.target.closest(".pic") : null;
    if (pic) { open(pic); return; }
    if (e.target === lb || e.target === lbImg) close();
  });
  lbClose.addEventListener("click", close);
  lbPrev.addEventListener("click", function () { step(-1); });
  lbNext.addEventListener("click", function () { step(1); });
  document.addEventListener("keydown", function (e) {
    if (lb.hidden) return;
    if (e.key === "Escape") close();
    else if (e.key === "ArrowLeft") step(-1);
    else if (e.key === "ArrowRight") step(1);
  });

  /* ---- connect account sync ---- */
  (function connect() {
    if (!window.claude || typeof window.claude.use !== "function") return;
    Promise.all([window.claude.use("db"), window.claude.use("user")]).then(function (r) {
      var db = r[0], user = r[1];
      if (!db || !user) return null;
      return user.id().then(function (id) {
        if (!id) return;
        docRef = db.doc("data/users/" + id + "/progress");
        docRef.onSnapshot(function (snap) {
          if (dead) return;
          if (!snap.exists) { say("Ticks and choices sync to your account."); return; }
          if (snap.metadata && snap.metadata.hasPendingWrites) return;
          if (writing || dirty) return;
          var d = snap.data() || {}, next = {};
          (Array.isArray(d.checked) ? d.checked : []).forEach(function (k) { if (typeof k === "string") next[k] = true; });
          state = next; saveLocal();
          if (d.options && typeof d.options === "object") {
            Object.keys(opts).forEach(function (k) { if (typeof d.options[k] === "boolean") opts[k] = d.options[k]; });
            saveOpts(); applyOpts();
          }
          paint(); say("Ticks and choices sync to your account.");
        }, function () { dead = true; say("Ticks are saved in this browser only."); });
      });
    }).catch(function () {});
  })();
})();
