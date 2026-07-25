/* Report UI helpers beyond declarative HTMX attributes. */

function initFindingRows(root = document) {
  root.querySelectorAll(".finding-summary").forEach((row) => {
    if (row.dataset.bound === "1") {
      return;
    }
    row.dataset.bound = "1";

    const toggle = () => {
      const group = row.closest(".finding-group");
      if (!group) {
        return;
      }
      const opening = !row.classList.contains("finding-expanded");
      group.querySelectorAll(".finding-detail").forEach((detail) => {
        detail.classList.toggle("hidden", !opening);
      });
      const message = row.querySelector(".finding-message");
      if (message) {
        message.classList.toggle("line-clamp-2", !opening);
      }
      row.setAttribute("aria-expanded", opening ? "true" : "false");
      row.classList.toggle("finding-expanded", opening);
    };

    row.addEventListener("click", toggle);
    row.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        toggle();
      }
    });
  });
}

function formatElapsed(ms) {
  const seconds = Math.max(0, Math.floor(ms / 1000));
  if (seconds < 60) {
    return `${seconds}s`;
  }
  const minutes = Math.floor(seconds / 60);
  const rem = seconds % 60;
  return `${minutes}m ${rem}s`;
}

function initElapsed(root = document) {
  root.querySelectorAll("[data-started-at]").forEach((el) => {
    const started = Date.parse(el.dataset.startedAt || "");
    const label = el.querySelector("[data-elapsed]");
    if (!Number.isFinite(started) || !label) {
      return;
    }
    const tick = () => {
      label.textContent = `elapsed ${formatElapsed(Date.now() - started)}`;
    };
    tick();
    if (el.dataset.elapsedTimer) {
      return;
    }
    el.dataset.elapsedTimer = "1";
    window.setInterval(tick, 1000);
  });
}

async function initCharts(root = document) {
  if (typeof Chart === "undefined") {
    return;
  }
  const host = root.querySelector("[data-charts]");
  if (!host) {
    return;
  }
  const runId = host.dataset.runId;
  const branch = host.dataset.branch || "";
  if (!runId) {
    return;
  }
  const [overviewRes, trendsRes] = await Promise.all([
    fetch(`/api/runs/${encodeURIComponent(runId)}/overview`),
    fetch(`/api/runs/trends?branch=${encodeURIComponent(branch)}&limit=20`),
  ]);
  if (!overviewRes.ok) {
    return;
  }
  const overview = await overviewRes.json();
  const trends = trendsRes.ok ? await trendsRes.json() : { runs: [] };

  const severityEl = document.getElementById("chart-severity");
  if (severityEl && !severityEl.dataset.charted) {
    severityEl.dataset.charted = "1";
    const sev = overview.by_severity || {};
    new Chart(severityEl, {
      type: "doughnut",
      data: {
        labels: ["error", "warning", "info"],
        datasets: [
          {
            data: [sev.error || 0, sev.warning || 0, sev.info || 0],
            backgroundColor: ["#b91c1c", "#d97706", "#0284c7"],
          },
        ],
      },
      options: { plugins: { legend: { position: "bottom" } } },
    });
  }

  const hotspotsEl = document.getElementById("chart-hotspots");
  if (hotspotsEl && !hotspotsEl.dataset.charted) {
    hotspotsEl.dataset.charted = "1";
    const hotspots = overview.hotspots || [];
    new Chart(hotspotsEl, {
      type: "bar",
      data: {
        labels: hotspots.map((h) => h.file),
        datasets: [
          {
            label: "Findings",
            data: hotspots.map((h) => h.count),
            backgroundColor: "#0f766e",
          },
        ],
      },
      options: {
        indexAxis: "y",
        plugins: { legend: { display: false } },
        scales: { x: { beginAtZero: true } },
      },
    });
  }

  const trendEl = document.getElementById("chart-trend");
  if (trendEl && !trendEl.dataset.charted) {
    trendEl.dataset.charted = "1";
    const runs = trends.runs || [];
    new Chart(trendEl, {
      type: "line",
      data: {
        labels: runs.map((r) => (r.started_at || "").slice(0, 10)),
        datasets: [
          {
            label: "Findings",
            data: runs.map((r) => r.finding_count || 0),
            borderColor: "#0f766e",
            tension: 0.2,
          },
        ],
      },
      options: {
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true } },
      },
    });
  }
}

document.addEventListener("DOMContentLoaded", () => {
  initFindingRows();
  initElapsed();
  initCharts();
  initSuiteCheckFilter();
});

function initSuiteCheckFilter() {
  const suiteSelect = document.getElementById("suite_id");
  const checkSelect = document.getElementById("check");
  if (!(suiteSelect instanceof HTMLSelectElement) || !(checkSelect instanceof HTMLSelectElement)) {
    return;
  }
  const sync = () => {
    const suite = suiteSelect.value;
    let keepValue = "";
    Array.from(checkSelect.options).forEach((option) => {
      if (!option.value) {
        option.hidden = false;
        option.disabled = false;
        return;
      }
      const match = option.dataset.suite === suite;
      option.hidden = !match;
      option.disabled = !match;
      if (match && option.value === checkSelect.value) {
        keepValue = option.value;
      }
    });
    checkSelect.value = keepValue;
  };
  suiteSelect.addEventListener("change", sync);
  sync();
}

document.body.addEventListener("htmx:afterSwap", (event) => {
  const el = event.detail.elt;
  if (!(el instanceof HTMLElement)) {
    return;
  }
  if (el.dataset.runComplete === "1" && el.dataset.runId) {
    window.location.replace(`/?run_id=${encodeURIComponent(el.dataset.runId)}`);
  }
  initFindingRows(el);
  initElapsed(el);
});
