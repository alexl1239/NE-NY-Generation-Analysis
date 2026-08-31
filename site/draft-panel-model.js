(() => {
  "use strict";

  const results = window.NE_NY_DRAFT_PANEL_MODEL_RESULTS;
  if (!results) return;

  const customerClasses = ["residential", "commercial", "industrial"];
  const classLabel = {
    residential: "Residential",
    commercial: "Commercial",
    industrial: "Industrial",
  };

  function coefficient(model, term) {
    return model.coefficients.find((row) => row.term === term);
  }

  function signed(value, digits = 2) {
    const formatted = Math.abs(value).toFixed(digits);
    if (value > 0) return `+${formatted}`;
    if (value < 0) return `−${formatted}`;
    return Number(0).toFixed(digits);
  }

  function pValue(value) {
    if (value < 0.001) return "p<0.001";
    return `p=${value.toFixed(3)}`;
  }

  function coefficientCell(row) {
    return `
      <span class="draft-table-estimate">${signed(row.estimate)}¢</span>
      <span class="draft-table-detail">[${signed(row.confidence_95_low)}, ${signed(row.confidence_95_high)}] · ${pValue(row.p_value)}</span>`;
  }

  function estimateCell(row) {
    return `<span class="draft-table-estimate">${signed(row.estimate)}¢</span>`;
  }

  function modelFor(source, customerClass, specification = "baseline") {
    return source.find((model) => (
      model.customer_class === customerClass
      && model.specification === specification
    ));
  }

  function renderMainPriceResults() {
    const body = document.getElementById("main-price-results-table");
    body.innerHTML = customerClasses.map((customerClass) => {
      const model = modelFor(results.main_price_models, customerClass);
      return `
        <tr>
          <th scope="row">${classLabel[customerClass]}</th>
          <td class="numeric-cell">${model.observation_count}</td>
          <td class="numeric-cell">${model.utility_cluster_count}</td>
          <td>${coefficientCell(coefficient(model, "ownership_MTC"))}</td>
          <td>${coefficientCell(coefficient(model, "ownership_COOP"))}</td>
          <td class="numeric-cell">${(model.r_squared * 100).toFixed(1)}%</td>
        </tr>`;
    }).join("");

    const mtcClear = results.main_price_models
      .filter((model) => coefficient(model, "ownership_MTC").confidence_interval_excludes_zero)
      .map((model) => classLabel[model.customer_class].toLowerCase());
    const coopClear = results.main_price_models.every(
      (model) => coefficient(model, "ownership_COOP").confidence_interval_excludes_zero,
    );
    const mtcText = mtcClear.length
      ? `MTC estimates are below DOM in all three models, but the 95% confidence interval excludes zero only for ${mtcClear.join(" and ")}.`
      : "The MTC confidence intervals include zero in all three models.";
    const coopText = coopClear
      ? "COOP estimates are below DOM and their 95% confidence intervals exclude zero in all three customer classes."
      : "COOP estimates are below DOM, but at least one confidence interval includes zero.";
    document.getElementById("main-price-finding").textContent = `${coopText} ${mtcText}`;
  }

  function renderSaidiComparison() {
    const groups = document.getElementById("saidi-comparison-groups");
    const sections = [];
    const saidiTerms = [];
    let largestChange = 0;

    for (const customerClass of customerClasses) {
      const baseline = modelFor(
        results.saidi_comparison_models,
        customerClass,
        "baseline",
      );
      const withSaidi = modelFor(
        results.saidi_comparison_models,
        customerClass,
        "saidi",
      );
      saidiTerms.push({
        customerClass,
        coefficient: coefficient(withSaidi, "routine_saidi_per_100_minutes"),
      });

      const rows = [];
      for (const ownership of ["MTC", "COOP"]) {
        const withoutRow = coefficient(baseline, `ownership_${ownership}`);
        const withRow = coefficient(withSaidi, `ownership_${ownership}`);
        const change = withRow.estimate - withoutRow.estimate;
        largestChange = Math.max(largestChange, Math.abs(change));
        rows.push(`
          <tr>
            <th scope="row">${ownership}</th>
            <td>${estimateCell(withoutRow)}</td>
            <td>${estimateCell(withRow)}</td>
            <td class="numeric-cell draft-change-cell">${signed(change)}¢</td>
          </tr>`);
      }
      sections.push(`
        <section class="draft-saidi-group" aria-labelledby="saidi-${customerClass}-title">
          <header class="draft-saidi-group__header">
            <h3 id="saidi-${customerClass}-title">${classLabel[customerClass]}</h3>
            <p>${baseline.observation_count} observations · ${baseline.utility_cluster_count} utilities</p>
          </header>
          <table class="ownership-table draft-compact-table">
            <thead>
              <tr>
                <th scope="col">Ownership</th>
                <th scope="col">Without SAIDI</th>
                <th scope="col">With SAIDI</th>
                <th scope="col">Change</th>
              </tr>
            </thead>
            <tbody>${rows.join("")}</tbody>
          </table>
        </section>`);
    }
    groups.innerHTML = sections.join("");

    const saidiSummary = saidiTerms.map(({ customerClass, coefficient: row }) => (
      `${classLabel[customerClass]} ${signed(row.estimate)}¢ per 100 minutes (${pValue(row.p_value)})`
    )).join("; ");
    document.getElementById("saidi-comparison-finding").textContent =
      `Adding SAIDI changes an ownership estimate by at most ${largestChange.toFixed(2)}¢/kWh in this matched sample. SAIDI estimates: ${saidiSummary}.`;
  }

  const visibleColumns = [
    "display_name",
    "state",
    "year",
    "ownership",
    "real_residential_price_2024_cents_kwh",
    "real_commercial_price_2024_cents_kwh",
    "real_industrial_price_2024_cents_kwh",
    "routine_saidi_minutes",
  ];

  const columnLabels = {
    display_name: "Utility",
    state: "State",
    year: "Year",
    ownership: "Ownership",
    real_residential_price_2024_cents_kwh: "Residential price (2024 ¢/kWh)",
    real_commercial_price_2024_cents_kwh: "Commercial price (2024 ¢/kWh)",
    real_industrial_price_2024_cents_kwh: "Industrial price (2024 ¢/kWh)",
    routine_saidi_minutes: "Routine SAIDI (min)",
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
    if (column === "year") return escapeHtml(value);
    const number = Number(value);
    if (Number.isFinite(number)) {
      return number.toLocaleString(undefined, { maximumFractionDigits: 2 });
    }
    return escapeHtml(value);
  }

  async function renderAnalysisData() {
    const status = document.getElementById("draft-data-status");
    try {
      const response = await fetch("data/draft_panel_model_analysis.csv");
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const parsed = parseCsv(await response.text());
      const allColumns = parsed.shift();
      const columnIndexes = visibleColumns.map((column) => allColumns.indexOf(column));
      if (columnIndexes.some((index) => index < 0)) {
        throw new Error("Expected model-data column missing");
      }
      const rows = parsed.filter((row) => row.some((value) => value !== ""));
      const head = document.getElementById("draft-data-head");
      const body = document.getElementById("draft-data-body");
      const search = document.getElementById("draft-data-search");

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
        + '<a href="data/draft_panel_model_analysis.csv">Open the CSV directly</a>.';
    }
  }

  renderMainPriceResults();
  renderSaidiComparison();
  renderAnalysisData();
})();
