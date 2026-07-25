/** Minimal Chart.js stand-in for SHIPGATE_UI_TEST=1 (no CDN). */
(function (global) {
  function Chart(el) {
    if (el && el.dataset) {
      el.dataset.charted = "1";
    }
    this.el = el;
  }
  Chart.prototype.destroy = function destroy() {};
  global.Chart = Chart;
})(typeof window !== "undefined" ? window : globalThis);
