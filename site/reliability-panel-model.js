(() => {
  "use strict";

  const results = window.NE_NY_RELIABILITY_PANEL_MODEL_RESULTS;
  if (!results) return;

  const ownershipOrder = ["MTC", "DOM", "COOP"];
  const ownershipLabel = {
    MTC: "MTC",
    DOM: "DOM",
    COOP: "COOP",
  };

  function signed(value, digits = 1) {
    const formatted = Math.abs(value).toFixed(digits);
    if (value > 0) return `+${formatted}`;
    if (value < 0) return `−${formatted}`;
    return Number(0).toFixed(digits);
  }

  function pValue(value) {
    if (value < 0.001) return "<0.001";
    return value.toFixed(3);
  }

  function renderResults() {
    const model = results.primary_model;
    const body = document.getElementById("reliability-results-table");
    body.innerHTML = model.ownership_results.map((row) => `
      <tr class="${row.confidence_interval_excludes_zero ? "" : "draft-model-row--uncertain"}">
        <th scope="row">${ownershipLabel[row.ownership]}</th>
        <td class="numeric-cell" data-label="Difference from DOM"><span class="draft-table-estimate">${signed(row.estimate)} minutes</span></td>
        <td class="numeric-cell" data-label="95% confidence interval">${signed(row.confidence_95_low)} to ${signed(row.confidence_95_high)}</td>
        <td class="numeric-cell" data-label="p-value">${pValue(row.p_value)}${row.confidence_interval_excludes_zero ? "" : '<span class="draft-table-interpretation">Inconclusive: CI includes 0</span>'}</td>
      </tr>`).join("");

    document.getElementById("reliability-model-summary").textContent =
      `${model.observation_count} utility-years · ${model.utility_cluster_count} utilities · `
      + `model R² ${(model.r_squared * 100).toFixed(1)}%. R² describes the complete model, not ownership alone.`;

    const allIntervalsIncludeZero = model.ownership_results.every(
      (row) => !row.confidence_interval_excludes_zero,
    );
    document.getElementById("reliability-finding").textContent = allIntervalsIncludeZero
      ? "Both point estimates are above DOM, but both confidence intervals include zero. This sample does not show a clear adjusted ownership difference in routine SAIDI. The intervals are wide, so the result is not evidence that the groups are equal."
      : "At least one adjusted ownership confidence interval excludes zero. The estimate remains descriptive because weather and infrastructure are not included.";
  }

  function renderTrend() {
    const target = document.getElementById("reliability-trend-chart");
    const width = 760;
    const height = 300;
    const margin = { top: 18, right: 18, bottom: 38, left: 54 };
    const plotWidth = width - margin.left - margin.right;
    const plotHeight = height - margin.top - margin.bottom;
    const years = [...new Set(results.annual_medians.map((row) => row.year))].sort();
    const maximum = Math.max(...results.annual_medians.map((row) => row.median_saidi_minutes));
    const yMaximum = Math.ceil(maximum / 50) * 50;
    const yTicks = Array.from({ length: 6 }, (_, index) => (yMaximum / 5) * index);
    const xPosition = (year) => margin.left
      + ((year - years[0]) / (years[years.length - 1] - years[0])) * plotWidth;
    const yPosition = (value) => margin.top + plotHeight - (value / yMaximum) * plotHeight;

    const grid = yTicks.map((tick) => {
      const y = yPosition(tick);
      return `
        <line class="reliability-trend-gridline" x1="${margin.left}" y1="${y}" x2="${width - margin.right}" y2="${y}"></line>
        <text class="reliability-trend-axis-label" x="${margin.left - 10}" y="${y + 4}" text-anchor="end">${Math.round(tick)}</text>`;
    }).join("");

    const yearTicks = years.filter((year, index) => index % 2 === 0 || year === years.at(-1));
    const xAxis = yearTicks.map((year) => `
      <text class="reliability-trend-axis-label" x="${xPosition(year)}" y="${height - 12}" text-anchor="middle">${year}</text>`).join("");

    const series = ownershipOrder.map((ownership) => {
      const rows = results.annual_medians
        .filter((row) => row.ownership === ownership)
        .sort((a, b) => a.year - b.year);
      const points = rows.map((row) => `${xPosition(row.year)},${yPosition(row.median_saidi_minutes)}`).join(" ");
      const dots = rows.map((row) => `
        <circle class="reliability-trend-point reliability-trend-point--${ownership.toLowerCase()}" cx="${xPosition(row.year)}" cy="${yPosition(row.median_saidi_minutes)}" r="3">
          <title>${ownership} ${row.year}: ${row.median_saidi_minutes.toFixed(1)} minutes (${row.observation_count} utilities)</title>
        </circle>`).join("");
      return `
        <polyline class="reliability-trend-line reliability-trend-line--${ownership.toLowerCase()}" points="${points}"></polyline>
        ${dots}`;
    }).join("");

    target.innerHTML = `
      <svg class="reliability-trend-svg" viewBox="0 0 ${width} ${height}" role="img" aria-labelledby="reliability-trend-title reliability-trend-description">
        <title id="reliability-trend-title">Annual median routine SAIDI by ownership</title>
        <desc id="reliability-trend-description">Unweighted annual median outage minutes excluding major-event days for MTC, DOM, and COOP utilities from 2013 through 2024.</desc>
        ${grid}
        <text class="reliability-trend-axis-title" transform="translate(15 ${margin.top + plotHeight / 2}) rotate(-90)" text-anchor="middle">Minutes per customer</text>
        ${xAxis}
        ${series}
      </svg>`;
  }

  const visibleColumns = [
    "display_name",
    "state",
    "year",
    "ownership",
    "reporting_standard",
    "reliability_customers",
    "routine_saidi_minutes",
    "included_primary_model",
  ];

  const columnLabels = {
    display_name: "Utility",
    state: "State",
    year: "Year",
    ownership: "Ownership",
    reporting_standard: "Reporting method",
    reliability_customers: "Reliability customers",
    routine_saidi_minutes: "Routine SAIDI (min)",
    included_primary_model: "Used in model",
  };

  function parseCsv(text) {
    const rows = [];
    let row = [];
    let value = "";
    let quoted = false;
    for (let index = 0; index < text.length; index += 1) {
      const character = text[index];
      if (quoted) {
        if (character === '"' && text[index + 1] === '"') {
          value += '"';
          index += 1;
        } else if (character === '"') {
          quoted = false;
        } else {
          value += character;
        }
      } else if (character === '"') {
        quoted = true;
      } else if (character === ",") {
        row.push(value);
        value = "";
      } else if (character === "\n") {
        row.push(value.replace(/\r$/, ""));
        rows.push(row);
        row = [];
        value = "";
      } else {
        value += character;
      }
    }
    if (value || row.length) {
      row.push(value.replace(/\r$/, ""));
      rows.push(row);
    }
    return rows;
  }

  function escapeHtml(value) {
    return value.replace(/[&<>"']/g, (character) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#039;",
    })[character]);
  }

  function displayValue(column, value) {
    if (value === "") return "—";
    if (column === "included_primary_model") return value === "True" ? "Yes" : "No";
    if (column === "reporting_standard") {
      return value === "ieee_standard" ? "IEEE" : value === "other_standard" ? "Other" : "—";
    }
    if (column === "year") return escapeHtml(value);
    const number = Number(value);
    if (Number.isFinite(number)) {
      return number.toLocaleString(undefined, { maximumFractionDigits: 1 });
    }
    return escapeHtml(value);
  }

  async function renderAnalysisData() {
    const status = document.getElementById("reliability-data-status");
    try {
      const response = await fetch("data/reliability_panel_model_analysis.csv");
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const parsed = parseCsv(await response.text());
      const allColumns = parsed.shift();
      const columnIndexes = visibleColumns.map((column) => allColumns.indexOf(column));
      if (columnIndexes.some((index) => index < 0)) throw new Error("Expected model-data column missing");
      const rows = parsed.filter((row) => row.some((value) => value !== ""));
      const head = document.getElementById("reliability-data-head");
      const body = document.getElementById("reliability-data-body");
      const search = document.getElementById("reliability-data-search");

      head.innerHTML = `<tr>${visibleColumns.map((column) => (
        `<th scope="col">${escapeHtml(columnLabels[column])}</th>`
      )).join("")}</tr>`;

      function drawRows() {
        const query = search.value.trim().toLowerCase();
        const visible = query
          ? rows.filter((row) => row.join(" ").toLowerCase().includes(query))
          : rows;
        body.innerHTML = visible.map((row) => `
          <tr>${visibleColumns.map((column, index) => (
            `<td>${displayValue(column, row[columnIndexes[index]] || "")}</td>`
          )).join("")}</tr>`).join("");
        status.textContent = `Showing ${visible.length.toLocaleString()} of ${rows.length.toLocaleString()} rows.`;
      }

      search.addEventListener("input", drawRows);
      drawRows();
    } catch (error) {
      status.innerHTML = "The table could not be loaded in the page. "
        + '<a href="data/reliability_panel_model_analysis.csv">Open the CSV directly</a>.';
    }
  }

  renderTrend();
  renderResults();
  renderAnalysisData();
})();
