(() => {
  "use strict";

  const results = window.NE_NY_DRAFT_PANEL_MODEL_RESULTS;
  if (!results) return;

  const customerClasses = ["residential", "commercial", "industrial"];
  const specifications = ["baseline", "saidi", "caidi"];
  const classLabel = {
    residential: "Residential",
    commercial: "Commercial",
    industrial: "Industrial",
  };
  const specificationLabel = {
    baseline: "Ownership + ISO + year",
    saidi: "+ routine SAIDI",
    caidi: "+ routine CAIDI",
  };

  function modelFor(customerClass, specification, geographicControl = "iso") {
    const source = geographicControl === "iso"
      ? results.price_models
      : results.decision_checks.state_control_models;
    return source.find((model) => (
      model.customer_class === customerClass
      && model.specification === specification
    ));
  }

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

  function percent(value) {
    return `${(value * 100).toFixed(1)}%`;
  }

  function coefficientCell(row, unit = "¢") {
    return `
      <span class="draft-table-estimate">${signed(row.estimate)}${unit}</span>
      <span class="draft-table-detail">[${signed(row.confidence_95_low)}, ${signed(row.confidence_95_high)}] · ${pValue(row.p_value)}</span>`;
  }

  function renderPriceResults() {
    const body = document.getElementById("draft-price-results-table");
    body.innerHTML = customerClasses.flatMap((customerClass) => (
      specifications.map((specification) => {
        const model = modelFor(customerClass, specification);
        const mtc = coefficient(model, "ownership_MTC");
        const coop = coefficient(model, "ownership_COOP");
        const iso = coefficient(model, "iso_ISONE");
        const reliability = specification === "baseline"
          ? null
          : coefficient(
            model,
            specification === "saidi"
              ? "routine_saidi_per_100_minutes"
              : "routine_caidi_per_10_minutes",
          );
        return `
          <tr>
            <th scope="row">${classLabel[customerClass]}</th>
            <td>${specificationLabel[specification]}</td>
            <td class="numeric-cell">${model.observation_count}</td>
            <td class="numeric-cell">${model.utility_cluster_count}</td>
            <td>${coefficientCell(mtc)}</td>
            <td>${coefficientCell(coop)}</td>
            <td>${coefficientCell(iso)}</td>
            <td>${reliability ? coefficientCell(reliability) : "—"}</td>
            <td class="numeric-cell">${percent(model.r_squared)}</td>
          </tr>`;
      })
    )).join("");

    const largestChange = Math.max(
      ...Object.values(results.diagnostics.ownership_coefficient_changes).flatMap(
        (customerClass) => Object.values(customerClass).flatMap((ownership) => [
          Math.abs(ownership.saidi_change_from_baseline),
          Math.abs(ownership.caidi_change_from_baseline),
        ]),
      ),
    );
    document.getElementById("draft-price-summary").textContent =
      `Adding routine SAIDI or CAIDI changes any ownership coefficient by no more than ${largestChange.toFixed(2)} cents per kWh. Neither reliability term has p<0.05 in a price model.`;
  }

  function renderSensitivityResults() {
    const body = document.getElementById("draft-sensitivity-results-table");
    body.innerHTML = customerClasses.flatMap((customerClass) => {
      const iso = modelFor(customerClass, "baseline", "iso");
      const state = modelFor(customerClass, "baseline", "state");
      const expanded = results.decision_checks.expanded_price_models.find(
        (model) => model.customer_class === customerClass,
      );
      return [
        { model: iso, sample: "Matched reliability sample", control: "ISO + year" },
        { model: state, sample: "Matched reliability sample", control: "State + year" },
        { model: expanded, sample: "Expanded price-only sample", control: "ISO + year" },
      ].map(({ model, sample, control }) => `
        <tr>
          <th scope="row">${classLabel[customerClass]}</th>
          <td>${sample}</td>
          <td>${control}</td>
          <td class="numeric-cell">${model.observation_count}</td>
          <td class="numeric-cell">${model.utility_cluster_count}</td>
          <td>${coefficientCell(coefficient(model, "ownership_MTC"))}</td>
          <td>${coefficientCell(coefficient(model, "ownership_COOP"))}</td>
          <td class="numeric-cell">${percent(model.r_squared)}</td>
        </tr>`).join("");
    }).join("");

    document.getElementById("draft-sensitivity-summary").textContent =
      "MTC and COOP coefficients remain negative when state indicators replace the ISO indicator and in the expanded 42-utility price-only sample. Exact coefficient sizes vary across specifications.";
  }

  function reliabilityModelFor(metric, geographicControl) {
    const source = geographicControl === "iso"
      ? results.reliability_outcome_models
      : results.decision_checks.state_control_reliability_outcome_models;
    return source.find((model) => model.specification === metric);
  }

  function renderReliabilityResults() {
    const body = document.getElementById("draft-reliability-results-table");
    body.innerHTML = ["saidi", "caidi"].flatMap((metric) => (
      ["iso", "state"].map((control) => {
        const model = reliabilityModelFor(metric, control);
        return `
          <tr>
            <th scope="row">${metric.toUpperCase()}</th>
            <td>${control === "iso" ? "ISO + year" : "State + year"}</td>
            <td class="numeric-cell">${model.observation_count}</td>
            <td class="numeric-cell">${model.utility_cluster_count}</td>
            <td>${coefficientCell(coefficient(model, "ownership_MTC"), " min")}</td>
            <td>${coefficientCell(coefficient(model, "ownership_COOP"), " min")}</td>
            <td class="numeric-cell">${percent(model.r_squared)}</td>
          </tr>`;
      })
    )).join("");

    const isoSaidi = coefficient(reliabilityModelFor("saidi", "iso"), "ownership_MTC");
    const stateSaidi = coefficient(reliabilityModelFor("saidi", "state"), "ownership_MTC");
    document.getElementById("draft-reliability-summary").textContent =
      `The MTC–DOM SAIDI estimate is ${signed(isoSaidi.estimate)} minutes with ISO controls (${pValue(isoSaidi.p_value)}) and ${signed(stateSaidi.estimate)} minutes with state controls (${pValue(stateSaidi.p_value)}). The change in size and statistical uncertainty makes this result sensitive to the geographic specification. CAIDI ownership differences have p≥0.05 in both versions.`;
  }

  const columnLabels = {
    panel_id: "Panel ID",
    utility_id_eia: "EIA utility ID",
    display_name: "Utility",
    state: "State",
    iso_market: "ISO",
    year: "Year",
    ownership: "Ownership",
    ownership_2024: "2024 ownership",
    reporting_standard: "Reporting standard",
    reporting_other_standard: "Other standard",
    reliability_row_status: "Reliability status",
    reliability_customers: "Reliability customers",
    routine_saidi_minutes: "Routine SAIDI (min)",
    routine_saidi_per_100_minutes: "SAIDI / 100",
    routine_caidi_minutes: "Routine CAIDI (min)",
    routine_caidi_per_10_minutes: "CAIDI / 10",
    residential_average_price_cents_kwh: "Residential price (nominal ¢/kWh)",
    real_residential_price_2024_cents_kwh: "Residential price (2024 ¢/kWh)",
    bundled_residential_customer_share_pct: "Residential bundled share (%)",
    included_residential_common_sample: "In residential model sample",
    commercial_average_price_cents_kwh: "Commercial price (nominal ¢/kWh)",
    real_commercial_price_2024_cents_kwh: "Commercial price (2024 ¢/kWh)",
    bundled_commercial_customer_share_pct: "Commercial bundled share (%)",
    included_commercial_common_sample: "In commercial model sample",
    industrial_average_price_cents_kwh: "Industrial price (nominal ¢/kWh)",
    real_industrial_price_2024_cents_kwh: "Industrial price (2024 ¢/kWh)",
    bundled_industrial_customer_share_pct: "Industrial bundled share (%)",
    included_industrial_common_sample: "In industrial model sample",
    analysis_excluded_fields: "Missing model fields",
    source_report: "Price source",
    source_url: "Price source URL",
    source_file_url: "Reliability source URL",
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
    if (value === "True" || value === "False") return value === "True" ? "Yes" : "No";
    if (column === "source_url" || column === "source_file_url") {
      const label = column === "source_url" ? "Price source" : "Reliability source";
      return `<a href="${escapeHtml(value)}" target="_blank" rel="noopener">${label}</a>`;
    }
    const number = Number(value);
    if (
      Number.isFinite(number)
      && !["panel_id", "utility_id_eia", "year"].includes(column)
    ) {
      return number.toLocaleString(undefined, { maximumFractionDigits: 3 });
    }
    return escapeHtml(value);
  }

  async function renderAnalysisData() {
    const status = document.getElementById("draft-data-status");
    try {
      const response = await fetch("data/draft_panel_model_analysis.csv");
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const parsed = parseCsv(await response.text());
      const columns = parsed.shift();
      const rows = parsed.filter((row) => row.some((value) => value !== ""));
      const head = document.getElementById("draft-data-head");
      const body = document.getElementById("draft-data-body");
      const search = document.getElementById("draft-data-search");

      head.innerHTML = `<tr>${columns.map((column) => (
        `<th scope="col">${escapeHtml(columnLabels[column] || column)}</th>`
      )).join("")}</tr>`;

      function drawRows() {
        const query = search.value.trim().toLowerCase();
        const visible = query
          ? rows.filter((row) => row.join(" ").toLowerCase().includes(query))
          : rows;
        body.innerHTML = visible.map((row) => `
          <tr>${columns.map((column, index) => (
            `<td>${displayValue(column, row[index] || "")}</td>`
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

  renderPriceResults();
  renderSensitivityResults();
  renderReliabilityResults();
  renderAnalysisData();
})();
