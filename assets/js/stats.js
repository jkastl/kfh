// Page counts with GoatCounter: no cookies, no personal data. Copied from
// jkastl.github.io/shared/stats.js; per that repo's README, a site in its own
// repo keeps its own copy. Does nothing off *.github.io, so local previews
// never count.
(function () {
  var code = "jkastl"; // GoatCounter site code: https://jkastl.goatcounter.com
  if (!code || !/\.github\.io$/.test(location.hostname)) return;
  var endpoint = "https://" + code + ".goatcounter.com/count";
  window.goatcounter = window.goatcounter || {};
  window.goatcounter.endpoint = endpoint;
  var s = document.createElement("script");
  s.async = true;
  s.src = "https://gc.zgo.at/count.v4.js";
  s.integrity = "sha384-nRw6qfbWyJha9LhsOtSb2YJDyZdKvvCFh0fJYlkquSFjUxp9FVNugbfy8q1jdxI+";
  s.crossOrigin = "anonymous";
  s.setAttribute("data-goatcounter", endpoint);
  document.head.appendChild(s);
})();
