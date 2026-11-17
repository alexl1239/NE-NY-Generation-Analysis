(() => {
  "use strict";

  const pricePayload = window.NE_NY_NOVEMBER_EXTENSION_PRICE_HISTORY;
  const designPayload = window.NE_NY_NOVEMBER_EXTENSION_RESEARCH_DESIGN;
  const trendStatus = document.getElementById("extension-trend-status");
  const utilityStatus = document.getElementById("extension-utility-status");

  if (!pricePayload || !designPayload) {
    const message = "The historical extension data could not be loaded.";
    trendStatus.hidden = false;
    utilityStatus.hidden = false;
    trendStatus.textContent = message;
    utilityStatus.textContent = message;
    return;
  }

  const rows = pricePayload.records;
  const designRows = designPayload.records;
  const ownershipOrder = ["MTC", "DOM", "COOP"];
  const ownershipLabels = {
    MTC: "Foreign or multinational parent (MTC)",
    DOM: "U.S.-owned investor utility (DOM)",
    COOP: "Local non-shareholder ownership (COOP)",
  };
  const customerLabels = {
    residential: "Residential",
    commercial: "Commercial",
    industrial: "Industrial",
  };
  const yearStart = pricePayload.metadata.year_start;
  const yearEnd = pricePayload.metadata.year_end;
  const constantDollarYear = pricePayload.metadata.constant_dollar_year;
  const cpiU = pricePayload.metadata.cpi_u_annual_2013_100;
  const priceBasisLabels = {
    nominal: "published nominal cents",
    real_2024: "inflation-adjusted 2024 cents",
  };
  const years = Array.from(
    { length: yearEnd - yearStart + 1 },
    (_, index) => yearStart + index,
  );

  const rootStyle = getComputedStyle(document.documentElement);
  const colors = {
    MTC: rootStyle.getPropertyValue("--ownership-mtc").trim() || "#256a9b",
    DOM: rootStyle.getPropertyValue("--ownership-dom").trim() || "#b95716",
    COOP: rootStyle.getPropertyValue("--ownership-coop").trim() || "#2f7a3d",
    grid: rootStyle.getPropertyValue("--gridline").trim() || "#e1e0d9",
    ink: rootStyle.getPropertyValue("--ink-secondary").trim() || "#52514e",
  };

  function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, (character) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#039;",
    })[character]);
  }

  function median(values) {
    if (!values.length) return null;
    const sorted = [...values].sort((left, right) => left - right);
    const middle = Math.floor(sorted.length / 2);
    return sorted.length % 2
      ? sorted[middle]
      : (sorted[middle - 1] + sorted[middle]) / 2;
  }

  function formatPrice(value) {
    return value == null ? "—" : `${Number(value).toFixed(2)}¢`;
  }

  function formatCustomers(value) {
    return value == null ? "—" : Number(value).toLocaleString();
  }

  function priceForBasis(value, year, priceBasis) {
    if (value == null || priceBasis === "nominal") return value;
    return value * (cpiU[constantDollarYear] / cpiU[year]);
  }

  function roundMaximum(value) {
    if (!Number.isFinite(value) || value <= 0) return 10;
    const magnitude = 10 ** Math.floor(Math.log10(value));
    return Math.ceil(value / magnitude) * magnitude;
  }

  function linePath(points, xScale, yScale) {
    let previousYear = null;
    return points.map((point) => {
      const command = previousYear == null || point.year !== previousYear + 1 ? "M" : "L";
      previousYear = point.year;
      return `${command}${xScale(point.year).toFixed(1)},${yScale(point.value).toFixed(1)}`;
    }).join(" ");
  }

  function chartFrame(maximum, ariaLabel) {
    const width = 980;
    const height = 390;
    const margin = { top: 30, right: 28, bottom: 52, left: 66 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;
    const xScale = (year) => (
      margin.left + ((year - yearStart) / (yearEnd - yearStart)) * innerWidth
    );
    const yScale = (value) => margin.top + innerHeight - (value / maximum) * innerHeight;
    const xTicks = [yearStart, 2005, 2010, 2015, 2020, yearEnd]
      .filter((year, index, tickYears) => (
        year >= yearStart && year <= yearEnd && tickYears.indexOf(year) === index
      ));
    const yTicks = Array.from({ length: 6 }, (_, index) => (maximum / 5) * index);
    const grid = yTicks.map((tick) => `
      <line x1="${margin.left}" x2="${width - margin.right}" y1="${yScale(tick)}" y2="${yScale(tick)}" stroke="${colors.grid}" />
      <text x="${margin.left - 12}" y="${yScale(tick) + 4}" text-anchor="end" class="extension-svg-label">${tick.toFixed(tick < 10 ? 1 : 0)}¢</text>`).join("");
    const labels = xTicks.map((tick) => `
      <text x="${xScale(tick)}" y="${height - 18}" text-anchor="middle" class="extension-svg-label">${tick}</text>`).join("");
    return { width, height, margin, xScale, yScale, grid, labels, ariaLabel };
  }

  function showTrendDetail(point, ownership, customerClass, priceBasis, chart) {
    const detail = document.getElementById("extension-trend-detail");
    const pointKey = `${ownership}-${point.year}`;
    detail.innerHTML = `
      <p class="extension-point-detail__year">${point.year} · ${escapeHtml(customerLabels[customerClass])} · ${escapeHtml(priceBasisLabels[priceBasis])}</p>
      <dl>
        <div><dt>Ownership group</dt><dd>${escapeHtml(ownershipLabels[ownership])}</dd></div>
        <div><dt>Median price</dt><dd>${formatPrice(point.value)}/kWh</dd></div>
        <div><dt>Utilities included</dt><dd>${point.count.toLocaleString()}</dd></div>
        <div><dt>Observed range</dt><dd>${formatPrice(point.minimum)}–${formatPrice(point.maximum)}/kWh</dd></div>
      </dl>`;
    chart.querySelectorAll(".extension-trend-point").forEach((chartPoint) => {
      const selected = chartPoint.dataset.trendKey === pointKey;
      chartPoint.classList.toggle("is-selected", selected);
      chartPoint.setAttribute("aria-pressed", String(selected));
    });
  }

  function renderTrend(customerClass, priceBasis) {
    const chart = document.getElementById("extension-trend-chart");
    const selected = rows.filter((row) => (
      row.customer_class === customerClass && row.average_price_cents_kwh != null
    ));
    const series = ownershipOrder.map((ownership) => ({
      ownership,
      points: years.map((year) => {
        const values = selected
          .filter((row) => row.year === year && row.ownership_class === ownership)
          .map((row) => priceForBasis(
            row.average_price_cents_kwh,
            row.year,
            priceBasis,
          ));
        return {
          year,
          value: median(values),
          count: values.length,
          minimum: values.length ? Math.min(...values) : null,
          maximum: values.length ? Math.max(...values) : null,
        };
      }).filter((point) => point.value != null),
    }));
    const maximum = roundMaximum(Math.max(...series.flatMap((item) => item.points.map((point) => point.value))) * 1.08);
    const frame = chartFrame(
      maximum,
      `${customerLabels[customerClass]} median bundled prices by ownership in ${priceBasisLabels[priceBasis]}, ${yearStart} to ${yearEnd}`,
    );
    const lines = series.map(({ ownership, points }) => `
      <path d="${linePath(points, frame.xScale, frame.yScale)}" fill="none" stroke="${colors[ownership]}" stroke-width="3" />
      ${points.map((point) => `
        <circle class="extension-trend-point" data-trend-key="${ownership}-${point.year}" cx="${frame.xScale(point.year)}" cy="${frame.yScale(point.value)}" r="5" fill="${colors[ownership]}" tabindex="0" role="button" aria-pressed="false" aria-label="${ownershipLabels[ownership]}, ${point.year}, median ${point.value.toFixed(2)} cents per kilowatt-hour, ${point.count} utilities, range ${point.minimum.toFixed(2)} to ${point.maximum.toFixed(2)} cents">
          <title>${ownershipLabels[ownership]} · ${point.year}\nMedian: ${point.value.toFixed(2)}¢/kWh\nUtilities: ${point.count}\nRange: ${point.minimum.toFixed(2)}–${point.maximum.toFixed(2)}¢/kWh</title>
        </circle>`).join("")}`).join("");
    chart.innerHTML = `
      <svg viewBox="0 0 ${frame.width} ${frame.height}" role="img" aria-label="${escapeHtml(frame.ariaLabel)}">
        ${frame.grid}
        ${frame.labels}
        ${lines}
      </svg>`;

    series.forEach(({ ownership, points }) => {
      points.forEach((point) => {
        const chartPoint = chart.querySelector(
          `[data-trend-key="${ownership}-${point.year}"]`,
        );
        const selectPoint = () => showTrendDetail(
          point,
          ownership,
          customerClass,
          priceBasis,
          chart,
        );
        chartPoint.addEventListener("pointerenter", selectPoint);
        chartPoint.addEventListener("click", selectPoint);
        chartPoint.addEventListener("focus", selectPoint);
        chartPoint.addEventListener("keydown", (event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            selectPoint();
          }
        });
      });
    });
    document.getElementById("extension-trend-detail").innerHTML =
      "<p>Hover over or select a chart point to view its median, group size, and observed range.</p>";
  }

  const utilitySelect = document.getElementById("extension-utility");
  const utilities = [...new Map(rows.map((row) => [row.panel_id, {
    panelId: row.panel_id,
    name: row.display_name,
    state: row.state,
  }])).values()].sort((left, right) => (
    left.state.localeCompare(right.state) || left.name.localeCompare(right.name)
  ));
  const highlightedEvents = new Map(designRows.map((event) => [event.treated_panel_id, event]));
  const utilityOption = (utility) => {
    const event = highlightedEvents.get(utility.panelId);
    const label = event
      ? ` · ${event.year_end_treatment_year}: ${event.old_ownership_class} → ${event.new_ownership_class}`
      : "";
    return `<option value="${escapeHtml(utility.panelId)}">${escapeHtml(utility.state)} · ${escapeHtml(utility.name)}${escapeHtml(label)}</option>`;
  };
  utilitySelect.innerHTML = `<optgroup label="Highlighted ownership changes">${utilities
    .filter((utility) => highlightedEvents.has(utility.panelId)).map(utilityOption).join("")}</optgroup>
    <optgroup label="Other utilities">${utilities
    .filter((utility) => !highlightedEvents.has(utility.panelId)).map(utilityOption).join("")}</optgroup>`;
  utilitySelect.value = utilities.some((utility) => utility.panelId === "MTC_VT_GMP")
    ? "MTC_VT_GMP"
    : utilities[0].panelId;

  function eventRoleLabel(role) {
    const labels = {
      primary_4_year_window: "a four-year window is available on each side",
      sensitivity_2_year_window: "only a two-year window is available on each side",
      excluded_insufficient_price_window: "the planned price window is not available",
      excluded_extremely_thin_customer_base: "the bundled-customer series is extremely thin",
    };
    return labels[role] || role.replaceAll("_", " ");
  }

  function showPointDetail(row, customerClass, priceBasis, chart) {
    const detail = document.getElementById("extension-point-detail");
    const displayedPrice = priceForBasis(
      row.average_price_cents_kwh,
      row.year,
      priceBasis,
    );
    detail.innerHTML = `
      <p class="extension-point-detail__year">${row.year} · ${escapeHtml(customerLabels[customerClass])} · ${escapeHtml(priceBasisLabels[priceBasis])}</p>
      <dl>
        <div><dt>Price</dt><dd>${formatPrice(displayedPrice)}/kWh</dd></div>
        <div><dt>Bundled customers</dt><dd>${formatCustomers(row.bundled_customers)}</dd></div>
        <div><dt>Ownership</dt><dd>${escapeHtml(row.ownership_class)}</dd></div>
        <div><dt>Parent or owner</dt><dd>${escapeHtml(row.ultimate_parent_or_owner)}</dd></div>
      </dl>`;
    chart.querySelectorAll(".extension-history-point").forEach((point) => {
      const selected = Number(point.dataset.historyYear) === row.year;
      point.classList.toggle("is-selected", selected);
      point.setAttribute("aria-pressed", String(selected));
    });
  }

  function renderUtility(customerClass, priceBasis) {
    const panelId = utilitySelect.value;
    const utilityRows = rows
      .filter((row) => row.panel_id === panelId && row.customer_class === customerClass)
      .sort((left, right) => left.year - right.year);
    const available = utilityRows.filter((row) => row.average_price_cents_kwh != null);
    const chart = document.getElementById("extension-utility-chart");
    const utilityName = utilityRows[0]?.display_name || "Selected utility";

    if (!available.length) {
      chart.innerHTML = '<p class="chart-status">No published price is available for this utility and customer class.</p>';
      document.getElementById("extension-point-detail").innerHTML =
        '<p>No published point is available for this selection.</p>';
    } else {
      const displayedRows = available.map((row) => ({
        row,
        value: priceForBasis(row.average_price_cents_kwh, row.year, priceBasis),
      }));
      const maximum = roundMaximum(
        Math.max(...displayedRows.map((item) => item.value)) * 1.1,
      );
      const frame = chartFrame(
        maximum,
        `${utilityName} ${customerLabels[customerClass]} bundled prices in ${priceBasisLabels[priceBasis]}, ${yearStart} to ${yearEnd}`,
      );
      const path = linePath(
        displayedRows.map(({ row, value }) => ({ year: row.year, value })),
        frame.xScale,
        frame.yScale,
      );
      const event = designRows.find((row) => (
        row.treated_panel_id === panelId && row.customer_class === customerClass
      ));
      const eventMarker = event ? `
        <line x1="${frame.xScale(event.year_end_treatment_year)}" x2="${frame.xScale(event.year_end_treatment_year)}" y1="${frame.margin.top}" y2="${frame.height - frame.margin.bottom}" class="extension-event-marker" />
        <text x="${frame.xScale(event.year_end_treatment_year) + 6}" y="${frame.margin.top + 14}" class="extension-svg-label extension-event-label">Ownership change ${event.year_end_treatment_year}</text>` : "";
      const points = displayedRows.map(({ row, value }) => `
        <circle class="extension-history-point" data-history-year="${row.year}" cx="${frame.xScale(row.year)}" cy="${frame.yScale(value)}" r="6" fill="${colors[row.ownership_class]}" tabindex="0" role="button" aria-pressed="false" aria-label="${row.year}, ${value.toFixed(2)} cents per kilowatt-hour in ${priceBasisLabels[priceBasis]}, ${row.ownership_class}, ${formatCustomers(row.bundled_customers)} bundled customers">
          <title>${row.year} · ${value.toFixed(2)}¢/kWh (${priceBasisLabels[priceBasis]})\n${row.ownership_class} · ${row.ultimate_parent_or_owner}\nBundled customers: ${formatCustomers(row.bundled_customers)}</title>
        </circle>`).join("");
      chart.innerHTML = `
        <svg viewBox="0 0 ${frame.width} ${frame.height}" role="img" aria-label="${escapeHtml(frame.ariaLabel)}">
          ${frame.grid}
          ${frame.labels}
          ${eventMarker}
          <path d="${path}" fill="none" stroke="${colors.ink}" stroke-width="2.5" />
          ${points}
        </svg>`;

      available.forEach((row) => {
        const point = chart.querySelector(`[data-history-year="${row.year}"]`);
        const selectPoint = () => showPointDetail(
          row,
          customerClass,
          priceBasis,
          chart,
        );
        point.addEventListener("click", selectPoint);
        point.addEventListener("pointerenter", selectPoint);
        point.addEventListener("focus", selectPoint);
        point.addEventListener("keydown", (event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            selectPoint();
          }
        });
      });
      showPointDetail(
        available[available.length - 1],
        customerClass,
        priceBasis,
        chart,
      );
    }

    const missingCount = utilityRows.length - available.length;
    const event = designRows.find((row) => (
      row.treated_panel_id === panelId && row.customer_class === customerClass
    ));
    const eventText = event
      ? ` Ownership change: ${event.closing_date}; ${eventRoleLabel(event.phase6_window_role)}.`
      : " No reviewed ownership-class change in this period.";
    document.getElementById("extension-utility-summary").textContent =
      `${utilityName}: ${available.length} of ${years.length} prices available; ${missingCount} missing.${eventText}`;
    if (panelId === "MTC_ME_VERSANT") {
      document.getElementById("extension-utility-summary").textContent += " The gap reflects unavailable bundled-service prices in this EIA series, not an absence of utility operations or all published rates. Residential bundled-customer counts are zero in 2003–2014. Maine reports electricity supply and delivery separately; those other measures are not substituted here. The utility territory also expanded in 2014.";
    }
  }

  function renderBasisNote(priceBasis) {
    const note = document.getElementById("extension-basis-note");
    note.textContent = priceBasis === "real_2024"
      ? "Prices are converted to 2024 cents using annual U.S. CPI-U: published price × CPI-U(2024) / CPI-U(year). The page is descriptive and does not report a causal estimate."
      : "Published nominal cents per kWh, without an inflation adjustment. The page is descriptive and does not report a causal estimate.";
  }

  function renderAll() {
    const customerClass = document.getElementById("extension-customer-class").value;
    const priceBasis = document.getElementById("extension-price-basis").value;
    renderBasisNote(priceBasis);
    renderTrend(customerClass, priceBasis);
    renderUtility(customerClass, priceBasis);
    renderSmallPanels(customerClass, priceBasis);
    const events = [...new Set(designRows.map((row) => row.event_id))];
    document.querySelectorAll(".extension-event-list article").forEach((article, index) => {
      let cell = article.querySelector(".extension-event-result");
      if (!cell) {
        const description = document.createElement("div");
        while (article.firstChild) description.appendChild(article.firstChild);
        article.appendChild(description);
        cell = document.createElement("div");
        cell.className = "extension-event-result";
        article.appendChild(cell);
      }
      const event = designRows.find((row) => row.event_id === events[index] && row.customer_class === customerClass);
      if (!event || event.before_real_2024 === "" || event.before_real_2024 == null) {
        cell.textContent = event?.phase6_window_role === "excluded_extremely_thin_customer_base"
          ? `Comparison omitted: the published bundled price covers as few as ${formatCustomers(event.treated_min_bundled_customers_selected_years)} ${customerClass} customers in the selected years. This small group does not adequately represent the utility’s customers.`
          : "Comparison omitted: too few consecutive years of published prices before or after the acquisition.";
        return;
      }
      const signed = (value) => `${Number(value) >= 0 ? "+" : ""}${Number(value).toFixed(2)}¢`;
      const before = Number(event.before_real_2024);
      const after = Number(event.after_real_2024);
      const pre = event.selected_pre_years.split("|");
      const post = event.selected_post_years.split("|");
      const relative = Number(event.relative_change_real_2024);
      cell.innerHTML = `<strong>${customerLabels[customerClass]} prices</strong>
        <p>Before (${pre[0]}–${pre.at(-1)}): <strong>${formatPrice(before)}</strong><br>
        After (${post[0]}–${post.at(-1)}): <strong>${formatPrice(after)}</strong></p>
        <p>This utility’s change: ${signed(after-before)}<br>
        Average change at ${event.eligible_control_count} utilities without an ownership change: ${signed(event.comparison_change_real_2024)}</p>
        <p><strong>${Math.abs(relative).toFixed(2)}¢ ${relative >= 0 ? "higher" : "lower"} than the change at comparison utilities.</strong></p>
        <small>All prices are inflation-adjusted 2024 cents/kWh.${event.phase6_window_role.includes("sensitivity") ? " Short comparison: only two full years on each side." : ""}</small>
        <details><summary>View comparison utilities</summary><ul>${event.eligible_control_panel_ids.split("|").map((id) => `<li>${escapeHtml(utilities.find((utility) => utility.panelId === id)?.name || id)}</li>`).join("")}</ul></details>`;
    });
  }

  function renderSmallPanels(customerClass, priceBasis) {
    const container = document.getElementById("extension-small-panels");
    container.innerHTML = "";
    const maximum = roundMaximum(Math.max(...rows.filter((row) =>
      highlightedEvents.has(row.panel_id) && row.customer_class === customerClass && row.average_price_cents_kwh != null
    ).map((row) => priceForBasis(row.average_price_cents_kwh, row.year, priceBasis))) * 1.1);
    highlightedEvents.forEach((event, panelId) => {
      const utility = utilities.find((item) => item.panelId === panelId);
      const points = rows.filter((row) => row.panel_id === panelId && row.customer_class === customerClass && row.average_price_cents_kwh != null).sort((a, b) => a.year-b.year);
      const frame = chartFrame(maximum, `${utility.name}: ${customerLabels[customerClass]}, ${priceBasisLabels[priceBasis]}`);
      const panel = document.createElement("article");
      panel.innerHTML = `<h3>${escapeHtml(utility.name)}</h3><p>${event.year_end_treatment_year}: <strong>${event.old_ownership_class} → ${event.new_ownership_class}</strong></p>
        <svg viewBox="0 0 ${frame.width} ${frame.height}" role="img" aria-label="${escapeHtml(frame.ariaLabel)}">${frame.grid}${frame.labels}
        <line x1="${frame.xScale(event.year_end_treatment_year)}" x2="${frame.xScale(event.year_end_treatment_year)}" y1="${frame.margin.top}" y2="${frame.height-frame.margin.bottom}" class="extension-event-marker" />
        <path d="${linePath(points.map((row) => ({year: row.year, value: priceForBasis(row.average_price_cents_kwh, row.year, priceBasis)})), frame.xScale, frame.yScale)}" fill="none" stroke="${colors.ink}" stroke-width="2.5" />
        ${points.map((row, index) => `<circle data-index="${index}" cx="${frame.xScale(row.year)}" cy="${frame.yScale(priceForBasis(row.average_price_cents_kwh, row.year, priceBasis))}" r="6" fill="${colors[row.ownership_class]}" tabindex="0" role="button" aria-label="${row.year}: ${formatPrice(priceForBasis(row.average_price_cents_kwh, row.year, priceBasis))}"><title>${row.year}: ${formatPrice(priceForBasis(row.average_price_cents_kwh, row.year, priceBasis))}</title></circle>`).join("")}</svg><p class="extension-small-detail" aria-live="polite">Select a point for details. Dashed line: acquisition year.</p>`;
      panel.querySelectorAll("circle").forEach((point) => {
        const show = () => {
          const row = points[Number(point.dataset.index)];
          panel.querySelector(".extension-small-detail").textContent = `${row.year}: ${formatPrice(priceForBasis(row.average_price_cents_kwh, row.year, priceBasis))}/kWh · ${formatCustomers(row.bundled_customers)} bundled customers · ${row.ownership_class}`;
        };
        ["click", "pointerenter", "focus"].forEach((type) => point.addEventListener(type, show));
        point.addEventListener("keydown", (key) => { if (key.key === "Enter" || key.key === " ") { key.preventDefault(); show(); } });
      });
      container.appendChild(panel);
      if (panelId === "MTC_ME_VERSANT") {
        const note = document.createElement("p");
        note.textContent = "Gap: no published bundled-service price in the intervening years. This does not mean the utility stopped reporting all data. Maine supply and delivery rates are separate measures. Territory expanded in 2014.";
        panel.appendChild(note);
      }
    });
  }

  document.getElementById("extension-price-basis").addEventListener("change", renderAll);
  document.getElementById("extension-customer-class").addEventListener("change", renderAll);
  utilitySelect.addEventListener("change", renderAll);
  renderAll();
})();
