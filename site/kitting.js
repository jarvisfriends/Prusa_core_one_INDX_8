/* Bins and labels: sort the hardware into Gridfinity bins, one set per phase, from what the
   builder says they own. Runs entirely in the page. Data comes from plan/kits.yaml, which
   tools/build.py embeds as window.KITS; the option state comes from app.js (window.PLAN). */
(function () {
  "use strict";
  var KITS = window.KITS, PLAN = window.PLAN;
  if (!KITS || !PLAN) return;
  var KEY = PLAN.key + "-kit";
  var root = document.getElementById("kitting");
  if (!root) return;

  /* ---- what the builder owns; limits keep the inputs sane ---- */
  var LIM = { cols: [1, 12], rows: [1, 12], count: [0, 40], len: [2, 8], comp: [2, 16], bins: [0, 500] };
  var DEF = { on: false, boxes: [{ cols: 4, rows: 5, count: 4 }], trays: [{ len: 4, comp: 8, count: 0 }], bins: { "1x1": 100, "1x2": 20, "2x2": 10 } };
  var cfg = JSON.parse(JSON.stringify(DEF));
  try {
    var saved = JSON.parse(localStorage.getItem(KEY) || "null");
    if (saved && typeof saved === "object") cfg = clean(saved);
  } catch (e) {}
  function clamp(v, lim, dflt) { v = parseInt(v, 10); if (isNaN(v)) v = dflt; return Math.min(lim[1], Math.max(lim[0], v)); }
  function clean(c) {
    var out = JSON.parse(JSON.stringify(DEF));
    out.on = !!c.on;
    if (Array.isArray(c.boxes) && c.boxes.length) out.boxes = c.boxes.slice(0, 4).map(function (b) { return { cols: clamp(b.cols, LIM.cols, 4), rows: clamp(b.rows, LIM.rows, 5), count: clamp(b.count, LIM.count, 0) }; });
    if (Array.isArray(c.trays) && c.trays.length) out.trays = c.trays.slice(0, 4).map(function (t) { return { len: clamp(t.len, LIM.len, 4), comp: clamp(t.comp, LIM.comp, 8), count: clamp(t.count, LIM.count, 0) }; });
    if (c.bins && typeof c.bins === "object") Object.keys(out.bins).forEach(function (k) { out.bins[k] = clamp(c.bins[k], LIM.bins, out.bins[k]); });
    return out;
  }
  function save() { try { localStorage.setItem(KEY, JSON.stringify(cfg)); } catch (e) {} if (PLAN.kitChanged) PLAN.kitChanged(cfg); }
  window.KITTING = { get: function () { return cfg; }, set: function (c) { cfg = clean(c); save(); draw(); } };

  /* ---- the plan ---- */
  function slots(size) { var p = size.split("x"); return (+p[0]) * (+p[1]); }
  function visible(item) { return PLAN.applies(item.when, item.unless); }
  function phaseNum(pid) { return KITS.phases.findIndex(function (p) { return p.id === pid; }); }
  function phaseName(pid) { var p = KITS.phases.find(function (x) { return x.id === pid; }); return p ? p.name : pid; }
  function line1(b) {
    var name = b.label || b.part, q = b.qty;
    if (typeof q === "number" && name.indexOf("x" + q) < 0) return "P" + phaseNum(b.phase) + " " + name + " x" + q;
    return "P" + phaseNum(b.phase) + " " + name;
  }
  function line2(b) {
    if (b.line2) return b.line2;
    var rows = (b.rows || []).join(" "), steps = (b.steps || []).join(" ");
    return rows && steps ? rows + "  " + steps : rows || steps;
  }
  function shortLabel(b) {
    if (b.short) return b.short;
    var name = (b.label || b.part).replace(/^(Keep|Kept) /, ""), q = b.qty;
    return typeof q === "number" && name.indexOf("x" + q) < 0 ? name + " x" + q : name;
  }

  function compute() {
    var bins = KITS.bins.filter(visible).map(function (b) { return Object.assign({ size: "1x1" }, b); });
    var byPhase = {};
    bins.forEach(function (b) { (byPhase[b.phase] = byPhase[b.phase] || []).push(b); });
    var order = KITS.phases.map(function (p) { return p.id; }).filter(function (id) { return byPhase[id]; });

    // trays: the builder's divided bins, largest compartment count first, replace 1x1 bins of one phase
    var trayTypes = cfg.trays.filter(function (t) { return t.count > 0; }).sort(function (a, b) { return b.comp - a.comp; });
    var trayStock = trayTypes.map(function (t) { return { len: t.len, comp: t.comp, left: t.count }; });
    var trays = [];
    order.forEach(function (pid) {
      var small = byPhase[pid].filter(function (b) { return b.size === "1x1" && b.tray !== false; });
      var letter = 0;
      while (small.length >= 5) {
        var stock = trayStock.find(function (t) { return t.left > 0; });
        if (!stock) break;
        var group = small.splice(0, stock.comp);
        stock.left--;
        var tray = { id: "t" + pid.slice(1) + String.fromCharCode(97 + letter), phase: pid, size: "1x" + stock.len, label: "Tray " + String.fromCharCode(65 + letter),
                     part: "Divided tray", kind: "tray", compartments: group, comp: stock.comp };
        letter++;
        trays.push(tray);
        group.forEach(function (b) { b.inTray = tray.id; });
      }
    });
    order.forEach(function (pid) {
      var rebuilt = [], seen = {};
      byPhase[pid].forEach(function (b) {
        if (b.inTray) { if (!seen[b.inTray]) { seen[b.inTray] = 1; rebuilt.push(trays.find(function (t) { return t.id === b.inTray; })); } }
        else rebuilt.push(b);
      });
      byPhase[pid] = rebuilt;
    });

    // boxes: largest phase first into the first open box with room; a new box is the smallest type that fits
    var need = {}; order.forEach(function (pid) { need[pid] = byPhase[pid].reduce(function (s, b) { return s + slots(b.size); }, 0); });
    var types = cfg.boxes.map(function (b, i) { return { i: i, cap: b.cols * b.rows, cols: b.cols, rows: b.rows, left: b.count }; }).sort(function (a, b) { return a.cap - b.cap; });
    var boxes = [], unplaced = [];
    order.slice().sort(function (a, b) { return need[b] - need[a] || phaseNum(a) - phaseNum(b); }).forEach(function (pid) {
      var home = boxes.find(function (bx) { return bx.used + need[pid] <= bx.cap; });
      if (!home) {
        var t = types.find(function (ty) { return ty.left > 0 && ty.cap >= need[pid]; });
        if (!t) { unplaced.push(pid); return; }
        t.left--;
        home = { cap: t.cap, cols: t.cols, rows: t.rows, used: 0, phases: [] };
        boxes.push(home);
      }
      home.phases.push(pid); home.used += need[pid];
    });
    boxes.forEach(function (bx) { bx.phases.sort(function (a, b) { return phaseNum(a) - phaseNum(b); }); });
    boxes.sort(function (a, b) { return phaseNum(a.phases[0]) - phaseNum(b.phases[0]); });

    // bins needed by size, against what the builder owns
    var needBySize = {};
    order.forEach(function (pid) { byPhase[pid].forEach(function (b) { if (b.kind !== "tray") needBySize[b.size] = (needBySize[b.size] || 0) + 1; }); });
    KITS.spares.forEach(function (s) { needBySize[s.size] = (needBySize[s.size] || 0) + 1; });
    return { byPhase: byPhase, order: order, trays: trays, boxes: boxes, unplaced: unplaced, need: need, needBySize: needBySize,
             binCount: order.reduce(function (n, pid) { return n + byPhase[pid].length; }, 0),
             slotCount: order.reduce(function (n, pid) { return n + need[pid]; }, 0) };
  }

  /* ---- labels ---- */
  function labels(r) {
    var out = [];
    r.boxes.forEach(function (bx, i) { out.push(["BOX " + (i + 1), bx.phases.map(function (p) { return "P" + phaseNum(p) + " " + phaseName(p); }).join(" + "), "box"]); });
    KITS.spares.forEach(function (s) { out.push([s.label, s.part, s.size]); });
    r.order.forEach(function (pid) {
      r.byPhase[pid].forEach(function (b) {
        if (b.compartments) {
          out.push([line1(b), b.compartments.length + " compartments, see the list", b.size]);
          b.compartments.forEach(function (c, n) { out.push([(n + 1) + " " + shortLabel(c), "", "slot"]); });
        } else out.push([line1(b), line2(b), b.size]);
      });
    });
    return out;
  }
  function csv(rows) {
    function q(s) { s = String(s); return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s; }
    return "line1,line2,size\n" + rows.map(function (r) { return r.map(q).join(","); }).join("\n") + "\n";
  }

  /* ---- drawing ---- */
  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function num(name, idx, key, val, lim, label) {
    return '<label class="num"><span>' + esc(label) + '</span><input type="number" inputmode="numeric" min="' + lim[0] + '" max="' + lim[1] + '" step="1" value="' + val + '" data-list="' + name + '" data-i="' + idx + '" data-k="' + key + '"></label>';
  }
  function draw() {
    var on = cfg.on;
    var h = ['<label class="kit-on"><input type="checkbox" id="kit-on"' + (on ? " checked" : "") + '> <span class="opt-name">Sort the hardware into Gridfinity bins</span></label>'];
    if (!on) { root.innerHTML = h.join(""); wire(); return; }
    h.push('<p class="sheet-note">Say what you own and the plan sorts every fastener and every piece of kept hardware into bins, one set per phase, so only the current phase\'s box is open on the bench. Fill the bins in Phase 0; it doubles as the kit inventory. Your answers are saved with your ticks.</p>');
    h.push('<div class="kit-form">');
    h.push('<fieldset><legend>Containers (grid of 1x1 slots)</legend>');
    cfg.boxes.forEach(function (b, i) {
      h.push('<div class="kit-row">' + num("boxes", i, "cols", b.cols, LIM.cols, "wide") + num("boxes", i, "rows", b.rows, LIM.rows, "deep") + num("boxes", i, "count", b.count, LIM.count, "how many") + (cfg.boxes.length > 1 ? '<button type="button" data-del="boxes" data-i="' + i + '">Remove</button>' : "") + "</div>");
    });
    if (cfg.boxes.length < 4) h.push('<button type="button" data-add="boxes">Another container size</button>');
    h.push("</fieldset>");
    h.push('<fieldset><legend>Divided bins (1 wide, split into compartments)</legend>');
    cfg.trays.forEach(function (t, i) {
      h.push('<div class="kit-row">' + num("trays", i, "len", t.len, LIM.len, "units long") + num("trays", i, "comp", t.comp, LIM.comp, "compartments") + num("trays", i, "count", t.count, LIM.count, "how many") + (cfg.trays.length > 1 ? '<button type="button" data-del="trays" data-i="' + i + '">Remove</button>' : "") + "</div>");
    });
    if (cfg.trays.length < 4) h.push('<button type="button" data-add="trays">Another divided bin size</button>');
    h.push("</fieldset>");
    h.push('<fieldset><legend>Plain bins you own</legend><div class="kit-row">' + num("bins", 0, "1x1", cfg.bins["1x1"], LIM.bins, "1x1") + num("bins", 0, "1x2", cfg.bins["1x2"], LIM.bins, "1x2") + num("bins", 0, "2x2", cfg.bins["2x2"], LIM.bins, "2x2") + "</div></fieldset>");
    h.push("</div>");

    var r = compute();
    var sizes = Object.keys(r.needBySize).sort();
    var shortBins = sizes.filter(function (s) { return cfg.bins[s] !== undefined && cfg.bins[s] < r.needBySize[s]; });
    h.push('<div class="kit-summary">');
    h.push("<p><strong>" + r.binCount + " bins</strong> (" + r.trays.length + " of them divided), " + r.slotCount + " slots of 1x1, in <strong>" + r.boxes.length + " container" + (r.boxes.length === 1 ? "" : "s") + "</strong>. Plus " +
           KITS.spares.map(function (s) { return "<strong>" + esc(s.label) + "</strong> (" + s.size + ")"; }).join(" and ") + ", which stay out the whole time.</p>");
    h.push("<p>Plain bins needed: " + sizes.map(function (s) { return s + " ×" + r.needBySize[s]; }).join(", ") + ".</p>");
    if (shortBins.length) h.push('<p class="kit-warn">You are short of ' + shortBins.map(function (s) { return (r.needBySize[s] - cfg.bins[s]) + " × " + s; }).join(" and ") + ". Add divided bins, or put two small bins' worth in one and label both.</p>");
    if (r.unplaced.length) h.push('<p class="kit-warn">Not enough containers for ' + r.unplaced.map(function (p) { return "P" + phaseNum(p) + " " + esc(phaseName(p)) + " (" + r.need[p] + " slots)"; }).join(", ") + ". Add a container, or a divided bin to shrink that phase.</p>");
    h.push("</div>");

    h.push('<h4>Containers</h4><p class="sheet-note">Only the current phase\'s container is open. A container can hold phases that are not next to each other; it is opened again when its next phase comes. The Phase 3 bins fill during the teardown and are emptied into the phase bins at the end of it.</p><ol class="kit-boxes">');
    r.boxes.forEach(function (bx) {
      h.push("<li><b>" + bx.cols + "×" + bx.rows + ", " + bx.used + " of " + bx.cap + " slots:</b> " + bx.phases.map(function (p) { return "P" + phaseNum(p) + " " + esc(phaseName(p)) + " (" + r.need[p] + ")"; }).join(", ") + "</li>");
    });
    h.push("</ol>");

    h.push('<h4>What is open per phase</h4>');
    r.order.forEach(function (pid) {
      h.push('<details class="kit-phase"><summary><b>P' + phaseNum(pid) + " " + esc(phaseName(pid)) + "</b> · " + r.byPhase[pid].length + " bins, " + r.need[pid] + " slots</summary>");
      h.push('<div class="tablewrap"><table class="kit-table"><thead><tr><th>Label</th><th>Contents</th><th>From</th><th>Rows and steps</th><th>Size</th></tr></thead><tbody>');
      r.byPhase[pid].forEach(function (b) {
        if (b.compartments) {
          h.push("<tr class=\"tray\"><td><b>" + esc(line1(b)) + "</b></td><td>" + b.compartments.length + " compartments</td><td></td><td></td><td>" + esc(b.size) + "</td></tr>");
          b.compartments.forEach(function (c, n) {
            h.push("<tr class=\"comp\"><td>" + (n + 1) + " " + esc(shortLabel(c)) + "</td><td>" + esc(c.part) + (c.qty !== undefined ? " · " + esc(c.qty) : "") + (c.text ? '<span class="by"> ' + esc(c.text) + "</span>" : "") + "</td><td>" + esc(c.kind) + (c.source ? ": " + esc(c.source) : "") + "</td><td>" + esc(line2(c)) + "</td><td>slot</td></tr>");
          });
        } else {
          h.push("<tr><td><b>" + esc(line1(b)) + "</b></td><td>" + esc(b.part) + (b.qty !== undefined ? " · " + esc(b.qty) : "") + (b.text ? '<span class="by"> ' + esc(b.text) + "</span>" : "") + "</td><td>" + esc(b.kind) + (b.source ? ": " + esc(b.source) : "") + "</td><td>" + esc(line2(b)) + "</td><td>" + esc(b.size) + "</td></tr>");
        }
      });
      h.push("</tbody></table></div></details>");
    });

    var labs = labels(r);
    h.push('<h4>Labels</h4><p class="sheet-note">' + labs.length + ' labels for 12 mm tape: line 1 is the phase and contents, line 2 the row codes and manual steps, so a bin leads you back to its rows. Copy the list for a label printer, or print the sheet at 100 % and cut it.</p>');
    h.push('<div class="kit-actions"><button type="button" id="kit-copy">Copy labels as CSV</button><button type="button" id="kit-print">Print the label sheet</button><span id="kit-msg" role="status"></span></div>');
    h.push('<div class="label-sheet" id="label-sheet">');
    labs.forEach(function (l) {
      var size = l[2], units = size === "box" ? 1 : size === "slot" ? 0.5 : +size.split("x")[1];
      var w = size === "slot" ? 19 : 36 * units + (units - 1) * 6;
      h.push('<div class="lab' + (size === "slot" ? " one" : "") + '" style="width:' + w + 'mm"><b>' + esc(l[0]) + "</b>" + (l[1] ? "<span>" + esc(l[1]) + "</span>" : "") + "</div>");
    });
    h.push("</div>");
    root.innerHTML = h.join("");
    wire();
    fit();
    root._csv = csv(labs);
  }
  function fit() {
    [].forEach.call(root.querySelectorAll(".lab b, .lab span"), function (el) {
      var size = parseFloat(getComputedStyle(el).fontSize);
      el.style.fontSize = "";
      size = parseFloat(getComputedStyle(el).fontSize);
      while (el.scrollWidth > el.clientWidth && size > 5) { size -= 0.5; el.style.fontSize = size + "px"; }
    });
  }
  function wire() {
    var onBox = document.getElementById("kit-on");
    onBox.addEventListener("change", function () { cfg.on = onBox.checked; save(); draw(); });
    [].forEach.call(root.querySelectorAll("input[type=number]"), function (inp) {
      inp.addEventListener("change", function () {
        var list = inp.getAttribute("data-list"), i = +inp.getAttribute("data-i"), k = inp.getAttribute("data-k");
        var lim = list === "bins" ? LIM.bins : LIM[k];
        var v = clamp(inp.value, lim, lim[0]);
        inp.value = v;
        if (list === "bins") cfg.bins[k] = v; else cfg[list][i][k] = v;
        save(); draw();
      });
    });
    [].forEach.call(root.querySelectorAll("button[data-add]"), function (btn) {
      btn.addEventListener("click", function () {
        var list = btn.getAttribute("data-add");
        cfg[list].push(list === "boxes" ? { cols: 4, rows: 4, count: 1 } : { len: 4, comp: 8, count: 1 });
        save(); draw();
      });
    });
    [].forEach.call(root.querySelectorAll("button[data-del]"), function (btn) {
      btn.addEventListener("click", function () { cfg[btn.getAttribute("data-del")].splice(+btn.getAttribute("data-i"), 1); save(); draw(); });
    });
    var copy = document.getElementById("kit-copy"), print = document.getElementById("kit-print"), msg = document.getElementById("kit-msg");
    if (copy) copy.addEventListener("click", function () {
      function fallback() {
        var ta = document.createElement("textarea"); ta.value = root._csv; ta.setAttribute("aria-label", "Labels as CSV"); ta.rows = 6; ta.style.width = "100%";
        copy.parentNode.appendChild(ta); ta.focus(); ta.select(); msg.textContent = "Select all and copy from the box below.";
      }
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(root._csv).then(function () { msg.textContent = "Copied " + root._csv.split("\n").length + " lines."; }, fallback);
      else fallback();
    });
    if (print) print.addEventListener("click", function () {
      document.body.classList.add("print-labels");
      var done = function () { document.body.classList.remove("print-labels"); window.removeEventListener("afterprint", done); };
      window.addEventListener("afterprint", done);
      setTimeout(function () { window.print(); setTimeout(done, 1500); }, 50);
      msg.textContent = "If nothing happened, your browser does not allow printing from here: open the page on GitHub Pages.";
    });
  }
  if (PLAN.onOptionsChange) PLAN.onOptionsChange(function () { if (cfg.on) draw(); });
  draw();
})();
