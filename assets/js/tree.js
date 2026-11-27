// Interactive descendant tree. Vanilla JS + SVG, no dependencies.
// Data: tree.json = {root, nodes: {id: {n name, y years, s sex, b branch, sp [spouse names],
//   c [[childId, marriageOrder]], f founder?, u uncertain?}}}
(function () {
  var svg = document.getElementById("tree");
  var wrap = document.getElementById("tree-wrap");
  if (!svg) return;
  var NS = "http://www.w3.org/2000/svg";
  var W = 196, H = 50, GX = 44, GY = 10; // node size and gaps
  var data, nodes, parent = {}, expanded = {}, focusId = null;
  var view = { x: 20, y: 20, k: 1 };
  var g = el("g", { "class": "viewport" });
  svg.appendChild(g);

  function el(name, attrs, text) {
    var e = document.createElementNS(NS, name);
    for (var a in attrs) e.setAttribute(a, attrs[a]);
    if (text != null) e.textContent = text;
    return e;
  }
  function clip(s, n) { return s.length > n ? s.slice(0, n - 1) + "…" : s; }

  fetch("tree.json").then(function (r) { return r.json(); }).then(function (d) {
    data = d; nodes = d.nodes;
    Object.keys(nodes).forEach(function (id) {
      nodes[id].c = nodes[id].c.filter(function (c) { return nodes[c[0]]; });
      nodes[id].c.forEach(function (c) { parent[c[0]] = id; });
    });
    var names = document.getElementById("tree-names");
    Object.keys(nodes).sort(function (a, b) { return nodes[a].n.localeCompare(nodes[b].n); }).forEach(function (id) {
      names.appendChild(el2("option", { value: label(id) }));
    });
    var q = new URLSearchParams(location.search).get("focus");
    defaults();
    if (q && nodes[q]) { reveal(q); focusId = q; }
    render();
    if (focusId) centerOn(focusId, 1); else home();
  });

  // Fit the default view; on a small screen, where that would be unreadable, centre on the
  // last opened ancestor (Thomas Kastl) instead.
  function home() {
    fit();
    if (view.k < 0.55) {
      var id = data.root;
      while (expanded[id] && nodes[id].c.length === 1) id = nodes[id].c[0][0];
      centerOn(id, 0.8);
      view.x = Math.min(view.x, 10); apply();
    }
  }

  function el2(name, attrs) { var e = document.createElement(name); for (var a in attrs) e.setAttribute(a, attrs[a]); return e; }
  function label(id) { var n = nodes[id]; return n.n + (n.y ? " (" + n.y + ")" : ""); }

  // Default view: the chain from the root down to the brothers, brothers closed.
  function defaults() {
    expanded = {};
    var id = data.root;
    while (id) {
      expanded[id] = true;
      if (nodes[id].c.some(function (c) { return nodes[c[0]].f; })) break;
      var next = nodes[id].c.length === 1 ? nodes[id].c[0][0] : null;
      id = next;
    }
  }
  function reveal(id) { var p = parent[id]; while (p) { expanded[p] = true; p = parent[p]; } }

  // ---- layout (tidy tree, root at left)
  var pos = {};
  function layout() {
    pos = {};
    var slot = 0;
    (function place(id, depth) {
      var n = nodes[id], kids = expanded[id] ? n.c : [];
      if (!kids.length) {
        pos[id] = { x: depth * (W + GX), y: slot * (H + GY) };
        slot++;
      } else {
        kids.forEach(function (c) { place(c[0], depth + 1); });
        var first = pos[kids[0][0]], last = pos[kids[kids.length - 1][0]];
        pos[id] = { x: depth * (W + GX), y: (first.y + last.y) / 2 };
      }
    })(data.root, 0);
  }

  function render() {
    layout();
    while (g.firstChild) g.removeChild(g.firstChild);
    var links = el("g", { "class": "links" }), boxes = el("g", { "class": "nodes" });
    g.appendChild(links); g.appendChild(boxes);
    Object.keys(pos).forEach(function (id) {
      var n = nodes[id], p = pos[id];
      if (expanded[id]) {
        n.c.forEach(function (c) {
          var q = pos[c[0]];
          var x1 = p.x + W, y1 = p.y + H / 2, x2 = q.x, y2 = q.y + H / 2, mx = x1 + GX / 2;
          links.appendChild(el("path", {
            d: "M" + x1 + "," + y1 + "H" + mx + "V" + y2 + "H" + x2,
            "class": c[1] > 1 ? "link second" : "link"
          }));
        });
      }
      var cls = "node" + (n.f ? " founder" : "") + (id === focusId ? " focus" : "") + (n.u ? " uncertain" : "");
      var grp = el("g", { "class": cls, transform: "translate(" + p.x + "," + p.y + ")" });
      var a = el("a", { href: "../people/" + id + "/" });
      a.appendChild(el("title", {}, label(id) + (n.sp.length ? " — married " + n.sp.join("; ") : "")));
      a.appendChild(el("rect", { width: W, height: H, rx: 5 }));
      a.appendChild(el("text", { x: 10, y: 19, "class": "nm" }, clip(n.n, 25)));
      var sub = [n.y, n.sp.length ? "m. " + n.sp.join(", ") : ""].filter(Boolean).join(" · ");
      a.appendChild(el("text", { x: 10, y: 37, "class": "sub" }, clip(sub, 34)));
      grp.appendChild(a);
      if (n.c.length) {
        var t = el("g", { "class": "toggle", transform: "translate(" + (W + 2) + "," + (H / 2) + ")", tabindex: 0, role: "button",
          "aria-label": (expanded[id] ? "Close" : "Open") + " the family of " + n.n, "aria-expanded": expanded[id] ? "true" : "false" });
        t.appendChild(el("rect", { x: 0, y: -10, width: expanded[id] ? 20 : 30, height: 20, rx: 10 }));
        t.appendChild(el("text", { x: expanded[id] ? 10 : 15, y: 4, "text-anchor": "middle" }, expanded[id] ? "−" : "+" + n.c.length));
        t.addEventListener("click", function (e) { e.stopPropagation(); toggle(id); });
        t.addEventListener("keydown", function (e) { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); toggle(id); } });
        grp.appendChild(t);
      }
      boxes.appendChild(grp);
    });
    apply();
  }

  function toggle(id) {
    var before = pos[id];
    var sx = before.x * view.k + view.x, sy = before.y * view.k + view.y;
    expanded[id] = !expanded[id];
    render();
    var after = pos[id]; // keep the toggled node where it was on screen
    view.x = sx - after.x * view.k; view.y = sy - after.y * view.k;
    apply();
    var again = Array.prototype.slice.call(g.querySelectorAll(".toggle")).filter(function (n) {
      return n.getAttribute("aria-label").indexOf(nodes[id].n) !== -1;
    })[0];
    if (again) again.focus();
  }

  // ---- pan & zoom
  function apply() { g.setAttribute("transform", "translate(" + view.x + "," + view.y + ") scale(" + view.k + ")"); }
  function zoomAt(f, cx, cy) {
    var k = Math.max(0.15, Math.min(2.5, view.k * f));
    f = k / view.k;
    view.x = cx - (cx - view.x) * f; view.y = cy - (cy - view.y) * f; view.k = k;
    apply();
  }
  function bbox() {
    var xs = [], ys = [];
    Object.keys(pos).forEach(function (id) { xs.push(pos[id].x); ys.push(pos[id].y); });
    return { x0: Math.min.apply(0, xs), y0: Math.min.apply(0, ys), x1: Math.max.apply(0, xs) + W + 40, y1: Math.max.apply(0, ys) + H };
  }
  function fit() {
    var b = bbox(), w = wrap.clientWidth, h = wrap.clientHeight;
    var k = Math.min(1.1, (w - 30) / (b.x1 - b.x0), (h - 30) / (b.y1 - b.y0));
    view.k = Math.max(0.15, k);
    view.x = (w - (b.x1 - b.x0) * view.k) / 2 - b.x0 * view.k;
    view.y = (h - (b.y1 - b.y0) * view.k) / 2 - b.y0 * view.k;
    apply();
  }
  function centerOn(id, k) {
    if (k) view.k = k;
    var p = pos[id];
    view.x = wrap.clientWidth / 2 - (p.x + W / 2) * view.k;
    view.y = wrap.clientHeight / 2 - (p.y + H / 2) * view.k;
    apply();
  }

  var pointers = {}, drag = null, moved = false, pinch = null;
  svg.addEventListener("pointerdown", function (e) {
    if (e.target.closest(".toggle")) return;
    pointers[e.pointerId] = { x: e.clientX, y: e.clientY };
    var ids = Object.keys(pointers);
    if (ids.length === 1) { drag = { x: e.clientX, y: e.clientY, vx: view.x, vy: view.y }; moved = false; }
    if (ids.length === 2) {
      var a = pointers[ids[0]], b = pointers[ids[1]];
      pinch = { d: Math.hypot(a.x - b.x, a.y - b.y), k: view.k };
      drag = null;
    }
  });
  svg.addEventListener("pointermove", function (e) {
    if (!pointers[e.pointerId]) return;
    pointers[e.pointerId] = { x: e.clientX, y: e.clientY };
    var ids = Object.keys(pointers);
    if (pinch && ids.length === 2) {
      var a = pointers[ids[0]], b = pointers[ids[1]], r = svg.getBoundingClientRect();
      var d = Math.hypot(a.x - b.x, a.y - b.y);
      zoomAt((pinch.k * d / pinch.d) / view.k, (a.x + b.x) / 2 - r.left, (a.y + b.y) / 2 - r.top);
      moved = true;
    } else if (drag) {
      var dx = e.clientX - drag.x, dy = e.clientY - drag.y;
      if (!moved && Math.abs(dx) + Math.abs(dy) > 5) { moved = true; svg.setPointerCapture(e.pointerId); svg.classList.add("dragging"); }
      if (moved) { view.x = drag.vx + dx; view.y = drag.vy + dy; apply(); }
    }
  });
  function up(e) {
    delete pointers[e.pointerId];
    if (Object.keys(pointers).length < 2) pinch = null;
    if (!Object.keys(pointers).length) { drag = null; svg.classList.remove("dragging"); }
  }
  svg.addEventListener("pointerup", up);
  svg.addEventListener("pointercancel", up);
  svg.addEventListener("click", function (e) { if (moved) { e.preventDefault(); moved = false; } }, true);
  svg.addEventListener("wheel", function (e) {
    e.preventDefault();
    var r = svg.getBoundingClientRect();
    zoomAt(Math.exp(-e.deltaY * 0.0015), e.clientX - r.left, e.clientY - r.top);
  }, { passive: false });

  // ---- toolbar
  document.querySelector(".tree-tools").addEventListener("click", function (e) {
    var b = e.target.closest("button[data-act]");
    if (!b || !data) return;
    var act = b.dataset.act, w = wrap.clientWidth / 2, h = wrap.clientHeight / 2;
    if (act === "in") zoomAt(1.25, w, h);
    else if (act === "out") zoomAt(0.8, w, h);
    else if (act === "fit") fit();
    else if (act === "brothers") { defaults(); focusId = null; render(); home(); }
    else if (act === "expand") { Object.keys(nodes).forEach(function (id) { expanded[id] = true; }); render(); fit(); }
  });
  // Find: Return (or the keyboard's Search key) and picking a suggestion both jump to the person
  // and close the on-screen keyboard. "change" alone is unreliable on phones.
  var find = document.getElementById("tree-find");
  function lookup(v) {
    v = v.trim().toLowerCase();
    if (!v) return null;
    var ids = Object.keys(nodes);
    return ids.filter(function (i) { return label(i).toLowerCase() === v; })[0] ||
      ids.filter(function (i) { return nodes[i].n.toLowerCase().indexOf(v) !== -1; })[0] || null;
  }
  function go(id) {
    reveal(id); focusId = id; render(); centerOn(id, Math.max(view.k, 0.9));
    find.setCustomValidity("");
    find.blur();
  }
  find.form.addEventListener("submit", function (e) {
    e.preventDefault();
    if (!data) return;
    var id = lookup(find.value);
    if (id) go(id);
    else if (find.value.trim()) { find.setCustomValidity("No one by that name in the tree."); find.reportValidity(); }
  });
  find.addEventListener("input", function () {
    find.setCustomValidity("");
    if (!data) return;
    // A picked suggestion fills in an exact "Name (years)" label.
    var v = find.value.trim().toLowerCase();
    var id = Object.keys(nodes).filter(function (i) { return label(i).toLowerCase() === v; })[0];
    if (id) go(id);
  });
})();
