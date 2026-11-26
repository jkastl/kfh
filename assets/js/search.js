// Client-side search over people and transcribed pages. No dependencies.
(function () {
  var params = new URLSearchParams(location.search);
  var q = (params.get("q") || "").trim();
  var input = document.getElementById("sq");
  var status = document.getElementById("search-status");
  var out = document.getElementById("results");
  if (input) input.value = q;
  if (!q) { status.textContent = "Type a name, place or year."; return; }
  status.textContent = "Searching…";

  // Fold accents and case so "Vsepadly" finds "Všepadly".
  function fold(s) { return s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase(); }
  function escapeHtml(s) {
    return s.replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; });
  }
  var terms = fold(q).split(/\s+/).filter(Boolean);

  function matches(text) {
    var f = fold(text);
    return terms.every(function (t) { return f.indexOf(t) !== -1; });
  }
  // Snippet around the first term, with every term highlighted. Folding keeps string
  // length for these scripts, so indexes in the folded text map onto the original.
  function snippet(text) {
    var f = fold(text), i = f.indexOf(terms[0]);
    var start = Math.max(0, i - 80), end = Math.min(text.length, i + 160);
    var s = text.slice(start, end), fs = f.slice(start, end), html = "", pos = 0;
    var ranges = [];
    terms.forEach(function (t) {
      var j = fs.indexOf(t);
      while (j !== -1) { ranges.push([j, j + t.length]); j = fs.indexOf(t, j + t.length); }
    });
    ranges.sort(function (a, b) { return a[0] - b[0]; });
    ranges.forEach(function (r) {
      if (r[0] < pos) return;
      html += escapeHtml(s.slice(pos, r[0])) + "<mark>" + escapeHtml(s.slice(r[0], r[1])) + "</mark>";
      pos = r[1];
    });
    html += escapeHtml(s.slice(pos));
    return (start > 0 ? "…" : "") + html + (end < text.length ? "…" : "");
  }

  fetch("index.json").then(function (r) { return r.json(); }).then(function (data) {
    var people = data.people.filter(function (p) { return matches(p.t); });
    var pages = data.pages.filter(function (p) { return matches(p.t + " " + p.h); });
    var html = "";
    if (people.length) {
      html += '<h2 class="results-h">People (' + people.length + ")</h2>";
      people.forEach(function (p) {
        html += '<div class="result"><h3><a href="../people/' + p.id + '/index.html">' + escapeHtml(p.n) +
          "</a> <span class=\"yrs\">" + escapeHtml(p.y || "") + "</span></h3></div>";
      });
    }
    if (pages.length) {
      html += '<h2 class="results-h">Book pages (' + pages.length + ")</h2>";
      pages.forEach(function (p) {
        html += '<div class="result"><h3><a href="../book/' + p.s + '/index.html">' + escapeHtml(p.l) +
          (p.h ? " — " + escapeHtml(p.h) : "") + "</a></h3><p>" + snippet(p.t) + "</p></div>";
      });
    }
    out.innerHTML = html;
    var n = people.length + pages.length;
    status.textContent = n ? n + " result" + (n === 1 ? "" : "s") + " for “" + q + "”." : "Nothing found for “" + q + "”.";
  }).catch(function () { status.textContent = "Search could not load. Try reloading the page."; });
})();
