const currentYear = new Date().getFullYear();
const springTab = document.querySelector("#spring-tab");
const fallTab = document.querySelector("#fall-tab");
const springPanel = document.querySelector("#spring-panel");
const fallPanel = document.querySelector("#fall-panel");
const yearPicker = document.querySelector("#year-picker");
const comparisonYear = document.querySelector("#comparison-year");
let fallLoaded = false;
let resizeTimer;

document.querySelectorAll("[data-current-year]").forEach((element) => {
  element.textContent = currentYear;
});

for (let year = 2000; year < currentYear; year += 1) {
  const option = document.createElement("option");
  option.value = String(year);
  option.textContent = String(year);
  comparisonYear.append(option);
}
comparisonYear.value = String(Math.max(2000, currentYear - 1));

function firstError(errors, key, fallback) {
  return errors?.[key] || fallback;
}

function setStatus(id, message, kind = "") {
  const element = document.querySelector(`#${id}`);
  element.textContent = message;
  element.className = `status ${kind}`.trim();
  element.hidden = !message;
}

async function fetchJson(url) {
  const response = await fetch(url, { headers: { Accept: "application/json" } });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.error || `Request failed (${response.status})`);
  }
  return payload;
}

function fitCharts(panel) {
  panel.querySelectorAll(".js-plotly-plot").forEach((element) => {
    const containerWidth = element.clientWidth;
    const plotWidth = element._fullLayout?.width;
    if (
      containerWidth > 0
      && plotWidth
      && Math.abs(plotWidth - containerWidth) > 1
    ) {
      Plotly.relayout(element, { width: containerWidth });
    }
  });
}

function visiblePanel() {
  return springPanel.hidden ? fallPanel : springPanel;
}

function scheduleVisibleChartFit() {
  window.clearTimeout(resizeTimer);
  resizeTimer = window.setTimeout(() => fitCharts(visiblePanel()), 100);
}

function renderFigure(containerId, figure, displayModeBar) {
  if (!figure) {
    return false;
  }
  const container = document.querySelector(`#${containerId}`);
  const layout = { ...(figure.layout || {}), autosize: true };
  delete layout.width;
  Plotly.react(container, figure.data || [], layout, {
    responsive: false,
    displayModeBar,
    displaylogo: false,
  }).then(() => fitCharts(container.closest(".tab-panel")));
  return true;
}

async function loadIceOff(year) {
  setStatus("ice-off-status", "Loading snow and air temperature data...");
  comparisonYear.disabled = true;
  yearPicker.querySelector("button").disabled = true;
  try {
    const data = await fetchJson(
      `/api/ice-off?comparison_year=${encodeURIComponent(year)}`,
    );
    if (renderFigure("ice-off-chart", data.figure, false)) {
      setStatus("ice-off-status", "");
    } else {
      setStatus(
        "ice-off-status",
        firstError(
          data.errors,
          "ice_off",
          "Snow depth and air temperature data are unavailable.",
        ),
        "info",
      );
    }
  } catch (error) {
    setStatus("ice-off-status", error.message, "warning");
  } finally {
    comparisonYear.disabled = false;
    yearPicker.querySelector("button").disabled = false;
  }
}

async function loadIceHistory() {
  try {
    const data = await fetchJson("/api/ice-history");
    if (renderFigure("ice-history-chart", data.figure, false)) {
      setStatus("ice-history-status", "");
    } else {
      setStatus(
        "ice-history-status",
        firstError(
          data.errors,
          "ice_history",
          "Ice history data is unavailable.",
        ),
        "info",
      );
    }
  } catch (error) {
    setStatus("ice-history-status", error.message, "warning");
  }
}

async function loadLakeTurnover() {
  if (fallLoaded) {
    return;
  }
  fallLoaded = true;
  setStatus("thermocline-status", "Loading thermocline data...");
  setStatus(
    "lake-temperature-status",
    "Loading lake surface temperature data...",
  );
  try {
    const data = await fetchJson("/api/lake-turnover");
    if (renderFigure("thermocline-chart", data.thermocline_figure, true)) {
      setStatus("thermocline-status", "");
    } else {
      setStatus(
        "thermocline-status",
        firstError(
          data.errors,
          "thermocline",
          "Thermocline data is unavailable.",
        ),
        "info",
      );
    }
    if (
      renderFigure(
        "lake-temperature-chart",
        data.lake_temperature_figure,
        true,
      )
    ) {
      setStatus("lake-temperature-status", "");
    } else {
      setStatus(
        "lake-temperature-status",
        firstError(
          data.errors,
          "lake_surface_temperature",
          "Lake surface temperature data is unavailable.",
        ),
        "info",
      );
    }
  } catch (error) {
    setStatus("thermocline-status", error.message, "warning");
    setStatus("lake-temperature-status", error.message, "warning");
    fallLoaded = false;
  }
}

function activateTab(tab) {
  const showSpring = tab === "spring";
  springTab.setAttribute("aria-selected", String(showSpring));
  fallTab.setAttribute("aria-selected", String(!showSpring));
  springPanel.hidden = !showSpring;
  fallPanel.hidden = showSpring;
  const panel = showSpring ? springPanel : fallPanel;
  fitCharts(panel);
  if (!showSpring) {
    loadLakeTurnover();
  }
}

springTab.addEventListener("click", () => activateTab("spring"));
fallTab.addEventListener("click", () => activateTab("fall"));
yearPicker.addEventListener("submit", (event) => {
  event.preventDefault();
  loadIceOff(comparisonYear.value);
});
window.addEventListener("resize", scheduleVisibleChartFit);

Promise.allSettled([
  loadIceOff(comparisonYear.value),
  loadIceHistory(),
]);
