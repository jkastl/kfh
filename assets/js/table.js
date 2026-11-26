// People table: filter by text/branch/conflict and sort by column. No dependencies.
(function () {
  var table = document.getElementById("people");
  if (!table) return;
  var tbody = table.tBodies[0];
  var rows = Array.prototype.slice.call(tbody.rows);
  var text = document.getElementById("f-text");
  var branch = document.getElementById("f-branch");
  var differs = document.getElementById("f-differs");
  var count = document.getElementById("f-count");

  function fold(s) { return s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase(); }
  rows.forEach(function (r) { r._text = fold(r.textContent); });

  // Restore filters from the URL (?q=…&branch=…&differs=1) so views can be linked.
  var params = new URLSearchParams(location.search);
  if (params.get("q")) text.value = params.get("q");
  if (params.get("branch")) branch.value = params.get("branch");
  if (params.get("differs") === "1") differs.checked = true;

  function apply() {
    var terms = fold(text.value).split(/\s+/).filter(Boolean);
    var b = branch.value, d = differs.checked, n = 0;
    rows.forEach(function (r) {
      var ok = (!b || r.dataset.branch === b) && (!d || r.dataset.differs === "1") &&
        terms.every(function (t) { return r._text.indexOf(t) !== -1; });
      r.hidden = !ok;
      if (ok) n++;
    });
    count.textContent = n === rows.length ? rows.length + " people" : n + " of " + rows.length + " people";
    var p = new URLSearchParams();
    if (text.value) p.set("q", text.value);
    if (b) p.set("branch", b);
    if (d) p.set("differs", "1");
    var qs = p.toString();
    history.replaceState(null, "", qs ? "?" + qs : location.pathname);
  }
  [text, branch, differs].forEach(function (el) { el.addEventListener("input", apply); el.addEventListener("change", apply); });
  apply();

  // Sorting
  var headers = Array.prototype.slice.call(table.tHead.rows[0].cells);
  table.tHead.addEventListener("click", function (e) {
    var btn = e.target.closest("button[data-col]");
    if (!btn) return;
    var col = +btn.dataset.col, num = btn.hasAttribute("data-num");
    var th = btn.parentNode;
    var dir = th.getAttribute("aria-sort") === "ascending" ? "descending" : "ascending";
    headers.forEach(function (h) { h.removeAttribute("aria-sort"); });
    th.setAttribute("aria-sort", dir);
    var sign = dir === "ascending" ? 1 : -1;
    function key(r) {
      var c = r.cells[col];
      var v = c.dataset.sort !== undefined ? c.dataset.sort : c.textContent;
      return num ? parseFloat(v) || 0 : fold(v);
    }
    rows.sort(function (a, b) {
      var ka = key(a), kb = key(b);
      if (ka < kb) return -sign;
      if (ka > kb) return sign;
      return 0;
    });
    rows.forEach(function (r) { tbody.appendChild(r); });
  });
})();
