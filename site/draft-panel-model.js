(() => {
  "use strict";

  const results = window.NE_NY_DRAFT_PANEL_MODEL_RESULTS;
  const customerSelect = document.getElementById("draft-customer-class");
  const reliabilitySelect = document.getElementById("draft-reliability-metric");

  if (!results || !customerSelect || !reliabilitySelect) {
    return;
  }

  const classLabel = {
    residential: "residential",
    commercial: "commercial",
    industrial: "industrial",
  };

  const specificationLabel = {
    baseline: "Baseline",
    saidi: "+ routine SAIDI",
    caidi: "+ routine CAIDI",
  };

  const ownershipLabel = {
    MTC: "MTC vs DOM",
    COOP: "COOP vs DOM",
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

  function reliabilityModelFor(metric, geographicControl = "iso") {
    const source = geographicControl === "iso"
      ? results.reliability_outcome_models
      : results.decision_checks.state_control_reliability_outcome_models;
    return source.find((model) => model.specification === metric);
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

  function clearLabel(row) {
    return row.p_value < 0.05 ? "clear in this draft" : "uncertain";
  }

  function percent(value) {
    return `${Math.round(value * 100)}%`;
  }

  function ownershipRows(customerClass) {
    return ["baseline", "saidi", "caidi"].flatMap((specification) => {
      const model = modelFor(customerClass, specification);
      return ["MTC", "COOP"].map((ownership) => ({
        specification,
        ownership,
        row: coefficient(model, `ownership_${ownership}`),
      }));
    });
  }

  function renderOwnershipChart(customerClass) {
    const container = document.getElementById("draft-ownership-chart");
    const rows = ownershipRows(customerClass);
    const maximum = Math.max(
      1,
      ...rows.flatMap(({ row }) => [
        Math.abs(row.confidence_95_low),
        Math.abs(row.confidence_95_high),
      ]),
    );
    const domain = Math.ceil(maximum / 2) * 2;
    const position = (value) => ((value + domain) / (domain * 2)) * 100;

    const groups = ["MTC", "COOP"].map((ownership) => {
      const groupRows = rows.filter((item) => item.ownership === ownership);
      const rowMarkup = groupRows.map(({ specification, row }) => {
        const left = position(row.confidence_95_low);
        const right = position(row.confidence_95_high);
        const point = position(row.estimate);
        const aria = `${specificationLabel[specification]}: ${ownershipLabel[ownership]} ${signed(row.estimate)} cents per kilowatt-hour; 95 percent range ${signed(row.confidence_95_low)} to ${signed(row.confidence_95_high)}; ${pValue(row.p_value)}.`;
        return `
          <div class="draft-coef-row draft-coef-row--${ownership.toLowerCase()}">
            <span class="draft-coef-model">${specificationLabel[specification]}</span>
            <div class="draft-coef-track" role="img" aria-label="${aria}">
              <i class="draft-coef-zero" style="left:${position(0)}%"></i>
              <i class="draft-coef-interval" style="left:${left}%;width:${Math.max(0.4, right - left)}%"></i>
              <i class="draft-coef-point" style="left:${point}%"></i>
            </div>
            <span class="draft-coef-value">${signed(row.estimate)}¢</span>
          </div>`;
      }).join("");
      return `
        <article class="draft-coef-group">
          <h4>${ownershipLabel[ownership]}</h4>
          ${rowMarkup}
        </article>`;
    }).join("");

    container.innerHTML = `
      <div class="draft-axis-labels" aria-hidden="true">
        <span></span>
        <div><span>−${domain}¢</span><span>0</span><span>+${domain}¢</span></div>
        <span></span>
      </div>
      ${groups}`;
  }

  function renderPriceTable(customerClass) {
    const body = document.getElementById("draft-price-results-table");
    body.innerHTML = ["baseline", "saidi", "caidi"].map((specification) => {
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
      const resultCell = (row) => `
        <span class="draft-table-estimate">${signed(row.estimate)}¢</span>
        <span class="draft-table-p">${pValue(row.p_value)}</span>`;
      return `
        <tr>
          <th scope="row">${specificationLabel[specification]}</th>
          <td>${resultCell(mtc)}</td>
          <td>${resultCell(coop)}</td>
          <td>${resultCell(iso)}</td>
          <td>${reliability ? resultCell(reliability) : "—"}</td>
          <td>${percent(model.r_squared)}</td>
        </tr>`;
    }).join("");
  }

  function renderPriceFinding(customerClass) {
    const baseline = modelFor(customerClass, "baseline");
    const saidi = modelFor(customerClass, "saidi");
    const caidi = modelFor(customerClass, "caidi");
    const changes = results.diagnostics.ownership_coefficient_changes[customerClass];
    const baselineMtc = coefficient(baseline, "ownership_MTC");
    const baselineCoop = coefficient(baseline, "ownership_COOP");
    const saidiTerm = coefficient(saidi, "routine_saidi_per_100_minutes");
    const caidiTerm = coefficient(caidi, "routine_caidi_per_10_minutes");
    const largestChange = Math.max(
      ...["MTC", "COOP"].flatMap((ownership) => [
        Math.abs(changes[ownership].saidi_change_from_baseline),
        Math.abs(changes[ownership].caidi_change_from_baseline),
      ]),
    );

    document.getElementById("draft-price-finding-title").textContent =
      `Reliability does not explain much of the ${classLabel[customerClass]} ownership gap in this draft.`;
    document.getElementById("draft-price-finding").textContent =
      `In the baseline, MTC is estimated at ${signed(baselineMtc.estimate)}¢/kWh and COOP at ${signed(baselineCoop.estimate)}¢/kWh compared with DOM. Adding SAIDI or CAIDI changes either ownership estimate by at most ${largestChange.toFixed(2)}¢/kWh. The SAIDI price term is ${clearLabel(saidiTerm)} (${pValue(saidiTerm.p_value)}), and the CAIDI term is ${clearLabel(caidiTerm)} (${pValue(caidiTerm.p_value)}).`;

    document.getElementById("draft-observation-count").textContent =
      baseline.observation_count.toLocaleString();
    document.getElementById("draft-utility-count").textContent =
      `${baseline.utility_cluster_count} of 30`;
    document.getElementById("draft-baseline-r2").textContent = percent(baseline.r_squared);
    document.getElementById("draft-sample-note").textContent =
      `The ${classLabel[customerClass]} comparison uses ${baseline.observation_count} complete utility-years from ${baseline.utility_cluster_count} utilities: ${baseline.ownership_utility_counts.MTC} MTC, ${baseline.ownership_utility_counts.DOM} DOM, and ${baseline.ownership_utility_counts.COOP} COOP. The other selected utilities remain in the observed-data overview but lack usable reliability coverage for this matched model.`;
  }

  function renderReliability(metric) {
    const isoModel = reliabilityModelFor(metric, "iso");
    const stateModel = reliabilityModelFor(metric, "state");
    const unit = isoModel.outcome_unit;
    const cards = ["MTC", "COOP"].map((ownership) => {
      const row = coefficient(isoModel, `ownership_${ownership}`);
      return `
        <article class="draft-reliability-card draft-reliability-card--${ownership.toLowerCase()}">
          <h3>${ownershipLabel[ownership]}</h3>
          <strong>${signed(row.estimate, 1)} minutes</strong>
          <p>95% range ${signed(row.confidence_95_low, 1)} to ${signed(row.confidence_95_high, 1)}</p>
          <span>${pValue(row.p_value)} · ${clearLabel(row)}</span>
        </article>`;
    }).join("");
    document.getElementById("draft-reliability-cards").innerHTML = cards;

    const isoMtc = coefficient(isoModel, "ownership_MTC");
    const stateMtc = coefficient(stateModel, "ownership_MTC");
    if (metric === "saidi") {
      document.getElementById("draft-reliability-finding").textContent =
        `With the professor-requested ISO market control, MTC utilities are estimated to have ${signed(isoMtc.estimate, 1)} more routine SAIDI minutes than DOM (${pValue(isoMtc.p_value)}). When state controls replace ISO, the estimate falls to ${signed(stateMtc.estimate, 1)} minutes and becomes uncertain (${pValue(stateMtc.p_value)}). That sensitivity means this is not yet a stable ownership finding.`;
    } else {
      document.getElementById("draft-reliability-finding").textContent =
        `The CAIDI ownership differences are uncertain with either ISO or state controls. In this draft, restoration time does not show a stable difference by ownership. Units are ${unit}.`;
    }
  }

  function renderDecisionChecks(customerClass) {
    const isoBaseline = modelFor(customerClass, "baseline", "iso");
    const stateBaseline = modelFor(customerClass, "baseline", "state");
    const isoMtc = coefficient(isoBaseline, "ownership_MTC");
    const isoCoop = coefficient(isoBaseline, "ownership_COOP");
    const stateMtc = coefficient(stateBaseline, "ownership_MTC");
    const stateCoop = coefficient(stateBaseline, "ownership_COOP");
    document.getElementById("draft-state-check").textContent =
      `For ${classLabel[customerClass]} prices, the ISO model estimates MTC at ${signed(isoMtc.estimate)}¢ and COOP at ${signed(isoCoop.estimate)}¢ versus DOM. Replacing ISO with state controls gives ${signed(stateMtc.estimate)}¢ and ${signed(stateCoop.estimate)}¢. The direction is stable, although the exact size changes.`;

    const expanded = results.decision_checks.expanded_price_models.find(
      (model) => model.customer_class === customerClass,
    );
    const expandedMtc = coefficient(expanded, "ownership_MTC");
    const expandedCoop = coefficient(expanded, "ownership_COOP");
    document.getElementById("draft-expanded-check").textContent =
      `The existing price-only expansion covers ${expanded.utility_cluster_count} utilities and keeps both estimates below DOM: ${signed(expandedMtc.estimate)}¢ for MTC and ${signed(expandedCoop.estimate)}¢ for COOP. It cannot test reliability until those additional utilities are audited.`;

    const saidi = modelFor(customerClass, "saidi");
    const caidi = modelFor(customerClass, "caidi");
    const saidiTerm = coefficient(saidi, "routine_saidi_per_100_minutes");
    const caidiTerm = coefficient(caidi, "routine_caidi_per_10_minutes");
    document.getElementById("draft-reliability-price-check").textContent =
      `Neither routine SAIDI (${pValue(saidiTerm.p_value)}) nor routine CAIDI (${pValue(caidiTerm.p_value)}) has a clear price relationship, and the ownership estimates barely move. The current evidence therefore does not support reliability as the main explanation for the price gap.`;
  }

  function renderCustomerClass() {
    const customerClass = customerSelect.value;
    renderPriceFinding(customerClass);
    renderOwnershipChart(customerClass);
    renderPriceTable(customerClass);
    renderDecisionChecks(customerClass);
  }

  customerSelect.addEventListener("change", renderCustomerClass);
  reliabilitySelect.addEventListener("change", () => renderReliability(reliabilitySelect.value));
  renderCustomerClass();
  renderReliability(reliabilitySelect.value);
})();
