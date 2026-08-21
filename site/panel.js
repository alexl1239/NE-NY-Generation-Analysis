const OWNERSHIP_ORDER = ["MTC", "DOM", "COOP"];
const OWNERSHIP_DESCRIPTIONS = {
  MTC: "Foreign or multinational ultimate parent",
  DOM: "US-based investor-owned ultimate parent",
  COOP: "Local non-shareholder ownership",
};
const CUSTOMER_CLASS_LABELS = {
  residential: "Residential",
  commercial: "Commercial",
  industrial: "Industrial",
};
// BLS annual CPI-U, all items, U.S. city average, rebased to 2013 = 100.
// Constant-2024 prices use published price × CPI(2024) / CPI(year).
const CPI_U_ANNUAL_2013_100 = {
  2013: 100.0,
  2014: 101.622,
  2015: 101.743,
  2016: 103.027,
  2017: 105.221,
  2018: 107.791,
  2019: 109.745,
  2020: 111.098,
  2021: 116.318,
  2022: 125.626,
  2023: 130.797,
  2024: 134.655,
};
const PRICE_BASIS_LABELS = {
  nominal: "published cents",
  real_2024: "inflation-adjusted 2024 cents",
};
const CT_CASE_STUDY_UTILITY_IDS = [4176, 19497, 54913, 11804, 4226, 13511];
const CT_CASE_STUDY_NAMES = {
  4176: "Eversource Connecticut (CL&P)",
  19497: "United Illuminating",
  54913: "NSTAR Electric (Eversource)",
  11804: "Massachusetts Electric (National Grid)",
  4226: "Con Edison (CECONY)",
  13511: "NYSEG",
};
const ROE_SHORT_NAMES = {
  4176: "CL&P",
  19497: "United Illuminating",
  54913: "NSTAR",
  11804: "Massachusetts Electric",
  4226: "Con Edison",
  13511: "NYSEG",
};
const ROE_STATE_PAIRS = [
  {
    state: "Connecticut",
    abbreviation: "CT",
    regulator: "Connecticut PURA",
    domId: 4176,
    mtcId: 19497,
  },
  {
    state: "Massachusetts",
    abbreviation: "MA",
    regulator: "Massachusetts DPU",
    domId: 54913,
    mtcId: 11804,
  },
  {
    state: "New York",
    abbreviation: "NY",
    regulator: "New York PSC",
    domId: 4226,
    mtcId: 13511,
  },
];
const CT_ROE_MINIMUM = 0.08;
const CT_ROE_MAXIMUM = 0.11;
const UTILITY_ORDER = [
  "MTC_NY_NIMO",
  "MTC_MA_MECO",
  "MTC_NY_NYSEG",
  "MTC_ME_CMP",
  "MTC_NY_RGE",
  "MTC_CT_UI",
  "MTC_NY_CENTHUD",
  "MTC_VT_GMP",
  "MTC_ME_VERSANT",
  "MTC_NH_LIBERTY",
  "DOM_NY_CECONY",
  "DOM_MA_NSTAR",
  "DOM_CT_CLP",
  "DOM_NH_PSNH",
  "DOM_RI_RIE",
  "DOM_NY_ORU",
  "DOM_NH_UNITIL",
  "DOM_MA_FITCHBURG",
  "DOM_NY_FIRSTENERGY",
  "DOM_NY_FISHERS",
  "COOP_NH_NHEC",
  "COOP_VT_VEC",
  "COOP_MA_TAUNTON",
  "COOP_MA_READING",
  "COOP_MA_CHICOPEE",
  "COOP_MA_PEABODY",
  "COOP_CT_WALLINGFORD",
  "COOP_CT_NORWICH",
  "COOP_VT_BURLINGTON",
  "COOP_NY_FAIRPORT",
];
const EXPECTED_PANEL_ROWS = UTILITY_ORDER.length * 12;
const SHORT_NAMES = {
  MTC_NY_NIMO: "Niagara Mohawk",
  MTC_MA_MECO: "Massachusetts Electric",
  MTC_NY_NYSEG: "NYSEG",
  MTC_ME_CMP: "Central Maine Power",
  MTC_NY_RGE: "Rochester Gas & Electric",
  MTC_CT_UI: "United Illuminating",
  MTC_NY_CENTHUD: "Central Hudson",
  MTC_VT_GMP: "Green Mountain Power",
  MTC_ME_VERSANT: "Versant Power",
  MTC_NH_LIBERTY: "Liberty Utilities",
  DOM_NY_CECONY: "Con Edison (CECONY)",
  DOM_MA_NSTAR: "NSTAR Electric",
  DOM_CT_CLP: "Connecticut Light & Power",
  DOM_NH_PSNH: "Public Service Co. of NH",
  DOM_RI_RIE: "Rhode Island Energy",
  DOM_NY_ORU: "Orange & Rockland",
  DOM_NH_UNITIL: "Unitil Energy Systems",
  DOM_MA_FITCHBURG: "Fitchburg Gas & Electric",
  DOM_NY_FIRSTENERGY: "FirstEnergy Pennsylvania",
  DOM_NY_FISHERS: "Fishers Island Electric",
  COOP_NH_NHEC: "NH Electric Cooperative",
  COOP_VT_VEC: "VT Electric Cooperative",
  COOP_MA_TAUNTON: "Taunton Municipal Lighting",
  COOP_MA_READING: "Reading Municipal Light",
  COOP_MA_CHICOPEE: "Chicopee Electric Light",
  COOP_MA_PEABODY: "Peabody Municipal Light",
  COOP_CT_WALLINGFORD: "Wallingford Electric",
  COOP_CT_NORWICH: "Norwich Public Utilities",
  COOP_VT_BURLINGTON: "Burlington Electric",
  COOP_NY_FAIRPORT: "Fairport Municipal",
};
const METRICS = {
  price: {
    key: "price",
    kind: "sector-price",
    formatValue: (value) => formatPrice(value),
    formatAxis: (value) => `${value}¢`,
  },
  coverage: {
    key: "coverage",
    kind: "sector-coverage",
    formatValue: (value) => `${Number(value).toFixed(1)}%`,
    formatAxis: (value) => `${value}%`,
  },
  saidi: {
    key: "saidi",
    kind: "reliability",
    label: "SAIDI: total outage minutes per customer",
    keys: {
      "without-major-events": "saidi_wo_major_event_days_minutes",
      "with-major-events": "saidi_w_major_event_days_minutes",
    },
    formatValue: (value) => `${Number(value).toFixed(1)} min/customer`,
    baseDescription:
      "SAIDI is the total number of sustained-outage minutes experienced by the average customer during the year.",
  },
  saifi: {
    key: "saifi",
    kind: "reliability",
    label: "SAIFI: outages per customer",
    keys: {
      "without-major-events": "saifi_wo_major_event_days_customers",
      "with-major-events": "saifi_w_major_event_days_customers",
    },
    formatValue: (value) => `${Number(value).toFixed(2)} outages/customer`,
    baseDescription:
      "SAIFI is the number of sustained outages experienced by the average customer during the year.",
  },
  caidi: {
    key: "caidi",
    kind: "reliability",
    label: "CAIDI: restoration minutes per outage",
    keys: {
      "without-major-events": "caidi_wo_major_event_days_minutes",
      "with-major-events": "caidi_w_major_event_days_minutes",
    },
    formatValue: (value) => `${Number(value).toFixed(1)} min/outage`,
    baseDescription:
      "CAIDI is the average restoration time for a sustained outage. PUDL derives it as SAIDI divided by SAIFI from the utility-reported EIA values.",
  },
};
const RELIABILITY_SCOPE_LABELS = {
  "without-major-events": "excluding major events",
  "with-major-events": "including major events",
};
const ISO_REGIONS = ["NYISO", "ISO-NE"];
const ISO_FUEL_ORDER = [
  "Coal",
  "Oil",
  "Natural gas",
  "Nuclear",
  "Hydro",
  "Waste and biomass",
  "Wind",
  "Solar",
];
const ISO_FUEL_SLUGS = {
  Coal: "coal",
  Oil: "oil",
  "Natural gas": "gas",
  Nuclear: "nuclear",
  Hydro: "hydro",
  "Waste and biomass": "waste",
  Wind: "wind",
  Solar: "solar",
};
const REVIEWED_DISPLAY_RULES = {};
const OWNERSHIP_CHANGE_EXPLANATIONS = {
  MTC_CT_UI:
    "Avangrid completed its acquisition of UIL Holdings on December 16, 2015. Under the project’s end-of-year rule, United Illuminating is coded MTC from 2016 because Avangrid’s ultimate parent is Iberdrola in Spain.",
  DOM_RI_RIE:
    "PPL completed its acquisition of Narragansett Electric from National Grid on May 25, 2022. Under the project’s end-of-year rule, the utility is coded DOM from 2022 because PPL is US-based.",
};
const SVG_NS = "http://www.w3.org/2000/svg";

function createElement(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
}

function svgElement(tag, attributes = {}) {
  const element = document.createElementNS(SVG_NS, tag);
  for (const [name, value] of Object.entries(attributes)) {
    element.setAttribute(name, value);
  }
  return element;
}

function formatPrice(value) {
  return `${Number(value).toFixed(2)}¢/kWh`;
}

function priceForBasis(value, year, priceBasis) {
  if (!isNumber(value) || priceBasis === "nominal") return value;
  return value * (CPI_U_ANNUAL_2013_100[2024] / CPI_U_ANNUAL_2013_100[year]);
}

function formatInteger(value) {
  return Number(value).toLocaleString("en-US", { maximumFractionDigits: 0 });
}

function isNumber(value) {
  return typeof value === "number" && Number.isFinite(value);
}

function formatReliabilityAxis(value) {
  if (value >= 1000) {
    const thousands = value / 1000;
    return `${Number.isInteger(thousands) ? thousands : thousands.toFixed(1)}k`;
  }
  if (value > 0 && value < 10 && !Number.isInteger(value)) {
    return value.toFixed(1);
  }
  return String(value);
}

function isReliabilityFieldExcluded(record, field) {
  const exclusions = record.reliability?.analysis_excluded_fields;
  return Boolean(exclusions) && exclusions.split("|").includes(field);
}

function niceMaximum(value) {
  if (!isNumber(value) || value <= 0) return 1;
  const magnitude = 10 ** Math.floor(Math.log10(value));
  const normalized = value / magnitude;
  const steps = [1, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10];
  const step = steps.find((candidate) => candidate >= normalized) ?? 10;
  return step * magnitude;
}

function resolveMetric(baseMetric, records, reliabilityScope, customerClass) {
  if (["sector-price", "sector-coverage"].includes(baseMetric.kind)) {
    const customerLabel = CUSTOMER_CLASS_LABELS[customerClass];
    const customerLabelLower = customerLabel.toLowerCase();
    const bundledCustomerKey = `bundled_${customerClass}_customers`;
    const totalCustomerKey = `total_distribution_${customerClass}_customers`;
    const isPrice = baseMetric.kind === "sector-price";
    const valueKey = isPrice
      ? `${customerClass}_average_price_cents_kwh`
      : `bundled_${customerClass}_customer_share_pct`;
    const valueFor = (record) => record[valueKey];
    const values = records.map(valueFor).filter(isNumber);
    const maximum = isPrice ? niceMaximum(Math.max(...values)) : 100;
    return {
      ...baseMetric,
      kind: isPrice ? "price" : "coverage",
      valueKey,
      valueFor,
      customerClass,
      customerLabel,
      bundledCustomerKey,
      totalCustomerKey,
      label: isPrice
        ? `Bundled ${customerLabelLower} average price`
        : `Bundled ${customerLabelLower} customer coverage`,
      minimum: 0,
      maximum,
      ticks: [0, maximum / 2, maximum],
      description: isPrice
        ? `EIA’s published average price for bundled ${customerLabelLower} service, in cents per kWh. The project does not calculate this price. Every utility chart uses the same 0–${formatReliabilityAxis(
            maximum
          )}¢ scale.`
        : `Bundled ${customerLabelLower} customers as a share of bundled plus delivery-only ${customerLabelLower} customers. Customer counts come from EIA/PUDL; only this percentage is project-derived. Every chart uses the same 0–100% scale.`,
    };
  }

  const valueKey = baseMetric.keys[reliabilityScope];
  const valueFor = (record) =>
    isReliabilityFieldExcluded(record, valueKey)
      ? null
      : record.reliability?.[valueKey] ?? null;
  const values = records.map(valueFor).filter(isNumber);
  const displayRule = REVIEWED_DISPLAY_RULES[`${baseMetric.key}:${reliabilityScope}`];
  const maximum = displayRule?.maximum ?? niceMaximum(Math.max(...values));
  const scopeLabel = RELIABILITY_SCOPE_LABELS[reliabilityScope];
  const scopeExplanation =
    reliabilityScope === "without-major-events"
      ? "Major events are removed under the reporting method used by each utility."
      : "Major events are included, so major storms can create large annual spikes.";
  return {
    ...baseMetric,
    valueKey,
    valueFor,
    reliabilityScope,
    minimum: 0,
    maximum,
    ticks: [0, maximum / 2, maximum],
    formatAxis: formatReliabilityAxis,
    displayRule,
    description: `${baseMetric.baseDescription} This view is ${scopeLabel}. ${scopeExplanation} Every utility chart uses the same 0–${formatReliabilityAxis(
      maximum
    )} scale.${displayRule ? ` ${displayRule.note}` : ""}`,
  };
}

function isOffScale(value, metric) {
  return Boolean(metric.displayRule) && isNumber(value) && value > metric.maximum;
}

function plottedValue(value, metric) {
  return isOffScale(value, metric) ? metric.maximum : value;
}

function coveragePercent(record, metric) {
  if (!metric.customerClass) return null;
  return record[`bundled_${metric.customerClass}_customer_share_pct`];
}

function hasMinorityCoverage(record, metric) {
  const coverage = coveragePercent(record, metric);
  return isNumber(coverage) && coverage < 50;
}

function formatReportingStandard(value) {
  if (value === "ieee_standard") return "IEEE";
  if (value === "other_standard") return "Non-IEEE";
  return "not reported";
}

function formatYearRange(firstYear, lastYear) {
  return firstYear === lastYear ? String(firstYear) : `${firstYear}–${lastYear}`;
}

function median(values) {
  const sorted = [...values].sort((a, b) => a - b);
  const middle = Math.floor(sorted.length / 2);
  if (sorted.length % 2) return sorted[middle];
  return (sorted[middle - 1] + sorted[middle]) / 2;
}

function ownershipTransitions(records) {
  const transitions = [];
  for (let index = 1; index < records.length; index += 1) {
    const previous = records[index - 1];
    const current = records[index];
    if (previous.ownership !== current.ownership) {
      transitions.push({
        year: current.year,
        from: previous.ownership,
        to: current.ownership,
      });
    }
  }
  return transitions;
}

function reportingTransitions(records) {
  const transitions = [];
  let previous = null;
  for (const record of records) {
    const standard = record.reliability?.reporting_standard;
    if (!standard) continue;
    if (previous && previous.standard !== standard) {
      transitions.push({
        year: record.year,
        from: previous.standard,
        to: standard,
      });
    }
    previous = { year: record.year, standard };
  }
  return transitions;
}

function reportingSegments(records) {
  const segments = [];
  for (const record of records) {
    const standard = record.reliability?.reporting_standard;
    if (!standard) continue;
    const previous = segments[segments.length - 1];
    if (
      previous &&
      previous.standard === standard &&
      previous.lastYear === record.year - 1
    ) {
      previous.lastYear = record.year;
    } else {
      segments.push({
        standard,
        firstYear: record.year,
        lastYear: record.year,
      });
    }
  }
  return segments
    .map(
      (segment) =>
        `${formatReportingStandard(segment.standard)} ${formatYearRange(
          segment.firstYear,
          segment.lastYear
        )}`
    )
    .join("; ");
}

function detailText(record, metric) {
  const value = metric.valueFor(record);
  if (!isNumber(value)) {
    if (
      metric.kind === "reliability" &&
      isReliabilityFieldExcluded(record, metric.valueKey)
    ) {
      return `${record.year} · Withheld from chart\nSource conflict documented in the reliability audit`;
    }
    return `${record.year} · Not reported by EIA`;
  }
  if (metric.kind === "coverage") {
    const coverageFlag = hasMinorityCoverage(record, metric)
      ? " — minority coverage"
      : "";
    return `${record.year} · ${metric.formatValue(
      value
    )}\n${formatInteger(record[metric.bundledCustomerKey])} of ${formatInteger(
      record[metric.totalCustomerKey]
    )} ${metric.customerClass} customers bundled${coverageFlag}`;
  }
  if (metric.kind === "reliability") {
    const offScaleFlag = isOffScale(value, metric) ? "*" : "";
    const standard = formatReportingStandard(
      record.reliability?.reporting_standard
    );
    return `${record.year} · ${metric.formatValue(value)}${offScaleFlag}\n${standard} method · ${formatInteger(
      record.reliability.reliability_customers
    )} customers reported`;
  }
  const coverage = coveragePercent(record, metric);
  const coverageFlag = hasMinorityCoverage(record, metric)
    ? " — minority coverage"
    : "";
  return `${record.year} · ${metric.formatValue(value)}\n${formatInteger(
    record[metric.bundledCustomerKey]
  )} of ${formatInteger(record[metric.totalCustomerKey])} ${
    metric.customerClass
  } customers bundled (${Number(coverage).toFixed(1)}%)${coverageFlag}`;
}

function buildMiniChart(records, metric) {
  const width = 220;
  const height = 132;
  const margin = { top: 9, right: 9, bottom: 24, left: 31 };
  const plotWidth = width - margin.left - margin.right;
  const plotHeight = height - margin.top - margin.bottom;
  const firstYear = records[0].year;
  const lastYear = records[records.length - 1].year;
  const x = (year) =>
    margin.left + ((year - firstYear) / (lastYear - firstYear)) * plotWidth;
  const y = (value) =>
    margin.top +
    plotHeight -
    ((value - metric.minimum) /
      (metric.maximum - metric.minimum)) *
      plotHeight;

  const svg = svgElement("svg", {
    viewBox: `0 0 ${width} ${height}`,
    role: "img",
    "aria-label": `${SHORT_NAMES[records[0].panel_id]} ${metric.label}, ${firstYear} to ${lastYear}`,
  });

  for (const tick of metric.ticks) {
    const tickY = y(tick);
    svg.appendChild(
      svgElement("line", {
        class: "mini-chart__gridline",
        x1: margin.left,
        x2: width - margin.right,
        y1: tickY,
        y2: tickY,
      })
    );
    const label = svgElement("text", {
      class: "mini-chart__axis-label",
      x: margin.left - 6,
      y: tickY + 3,
      "text-anchor": "end",
    });
    label.textContent = metric.formatAxis(tick);
    svg.appendChild(label);
  }

  for (const year of [firstYear, lastYear]) {
    const label = svgElement("text", {
      class: "mini-chart__axis-label",
      x: x(year),
      y: height - 7,
      "text-anchor": year === firstYear ? "start" : "end",
    });
    label.textContent = year;
    svg.appendChild(label);
  }

  const transitions = ownershipTransitions(records);
  for (const transition of transitions) {
    const marker = svgElement("line", {
      class: "mini-chart__change-line",
      x1: x(transition.year),
      x2: x(transition.year),
      y1: margin.top,
      y2: margin.top + plotHeight,
    });
    const markerTitle = svgElement("title");
    markerTitle.textContent = `Ownership changes from ${transition.from} to ${transition.to} in ${transition.year}`;
    marker.appendChild(markerTitle);
    svg.appendChild(marker);
  }

  const methodTransitions =
    metric.kind === "reliability" ? reportingTransitions(records) : [];
  for (const transition of methodTransitions) {
    const marker = svgElement("line", {
      class: "mini-chart__method-line",
      x1: x(transition.year),
      x2: x(transition.year),
      y1: margin.top,
      y2: margin.top + plotHeight,
    });
    const markerTitle = svgElement("title");
    markerTitle.textContent = `Reporting method changes from ${formatReportingStandard(
      transition.from
    )} to ${formatReportingStandard(transition.to)} in ${transition.year}`;
    marker.appendChild(markerTitle);
    svg.appendChild(marker);
  }

  const pathParts = [];
  let previousYear = null;
  for (const record of records) {
    const value = metric.valueFor(record);
    if (!isNumber(value)) {
      previousYear = null;
      continue;
    }
    const command = previousYear === record.year - 1 ? "L" : "M";
    pathParts.push(
      `${command} ${x(record.year).toFixed(2)} ${y(
        plottedValue(value, metric)
      ).toFixed(2)}`
    );
    previousYear = record.year;
  }
  if (pathParts.length) {
    svg.appendChild(
      svgElement("path", { class: "mini-chart__line", d: pathParts.join(" ") })
    );
  }

  const points = [];
  for (const record of records) {
    const value = metric.valueFor(record);
    if (!isNumber(value)) continue;
    const offScale = isOffScale(value, metric);
    const minorityCoverage = metric.kind === "price" && hasMinorityCoverage(record, metric);
    const point = svgElement("circle", {
      class: `mini-chart__point ownership-fill--${record.ownership.toLowerCase()}${
        offScale ? " mini-chart__point--off-scale" : ""
      }${
        minorityCoverage ? " mini-chart__point--low-coverage" : ""
      }`,
      cx: x(record.year),
      cy: y(plottedValue(value, metric)),
      r: 4.25,
      tabindex: "0",
      role: "img",
      "aria-label": detailText(record, metric),
    });
    const title = svgElement("title");
    title.textContent = detailText(record, metric);
    point.appendChild(title);
    points.push({ point, record });
    svg.appendChild(point);
    if (offScale) {
      const label = svgElement("text", {
        class: "mini-chart__offscale-label",
        x: x(record.year) + 6,
        y: margin.top - 2,
      });
      label.textContent = `↑ ${formatInteger(value)}*`;
      svg.appendChild(label);
    }
  }

  return { svg, points, transitions, methodTransitions };
}

function buildUtilityPanel(records, metric) {
  const first = records[0];
  const latest = records[records.length - 1];
  const latestValueNumber = metric.valueFor(latest);
  const latestValueText = isNumber(latestValueNumber)
    ? metric.formatValue(latestValueNumber)
    : "Not reported";
  const article = createElement("article", "utility-panel");

  const header = createElement("header", "utility-panel__header");
  const titleBlock = createElement("div");
  titleBlock.appendChild(
    createElement("h4", "utility-panel__title", SHORT_NAMES[first.panel_id])
  );
  titleBlock.appendChild(
    createElement("p", "utility-panel__state", `${first.state} · EIA ${first.utility_id_eia}`)
  );
  const latestValue = createElement(
    "p",
    "utility-panel__latest",
    latestValueText
  );
  latestValue.appendChild(createElement("span", "utility-panel__latest-year", "2024"));
  latestValue.setAttribute(
    "aria-label",
    `2024 value ${latestValueText}`
  );
  header.append(titleBlock, latestValue);
  article.appendChild(header);

  const chart = buildMiniChart(records, metric);
  article.appendChild(chart.svg);

  const detail = createElement("p", "utility-panel__detail", detailText(latest, metric));
  for (const { point, record } of chart.points) {
    const showDetail = () => {
      detail.textContent = detailText(record, metric);
    };
    point.addEventListener("mouseenter", showDetail);
    point.addEventListener("focus", showDetail);
    point.addEventListener("click", showDetail);
  }
  article.appendChild(detail);

  article.appendChild(
    createElement(
      "p",
      "utility-panel__owner",
      `2024 parent/owner: ${latest.parent_or_owner}`
    )
  );

  const ownershipNote = createElement("p", "utility-panel__change");
  if (chart.transitions.length) {
    const transition = chart.transitions[0];
    ownershipNote.appendChild(
      document.createTextNode(
        `Ownership: ${transition.from} → ${transition.to} in ${transition.year} `
      )
    );
    const explanation = OWNERSHIP_CHANGE_EXPLANATIONS[first.panel_id];
    if (explanation) {
      const help = createElement("span", "ownership-help");
      const helpId = `ownership-help-${first.panel_id.toLowerCase()}`;
      const button = createElement("button", "ownership-help__button", "?");
      button.type = "button";
      button.setAttribute("aria-label", `Explain the ownership change for ${SHORT_NAMES[first.panel_id]}`);
      button.setAttribute("aria-describedby", helpId);
      const tooltip = createElement("span", "ownership-help__text");
      tooltip.id = helpId;
      tooltip.setAttribute("role", "tooltip");
      tooltip.appendChild(document.createTextNode(`${explanation} `));
      if (latest.ownership_history_source_url) {
        const source = createElement("a", "", "Official source");
        source.href = latest.ownership_history_source_url;
        source.target = "_blank";
        source.rel = "noopener";
        tooltip.appendChild(source);
      }
      help.append(button, tooltip);
      ownershipNote.appendChild(help);
    }
  } else {
    const historyNote = latest.ownership_history_note || "";
    const hasSpecificHistory = !historyNote.includes("throughout the proposed panel");
    ownershipNote.appendChild(
      document.createTextNode(
        hasSpecificHistory
          ? historyNote
          : `Ownership: ${latest.ownership} throughout 2013–2024`
      )
    );
  }
  article.appendChild(ownershipNote);

  if (metric.kind === "reliability") {
    const available = records.filter((record) =>
      isNumber(metric.valueFor(record))
    ).length;
    const excluded = records.filter((record) =>
      isReliabilityFieldExcluded(record, metric.valueKey)
    ).length;
    const methodText = reportingSegments(records) || "reporting method unavailable";
    const exclusionText = excluded
      ? ` · ${excluded} published value${excluded === 1 ? "" : "s"} omitted because ${
          excluded === 1 ? "it conflicts" : "they conflict"
        } with a regulator filing`
      : "";
    article.appendChild(
      createElement(
        "p",
        "utility-panel__method",
        `${available}/12 values · ${methodText}${exclusionText}`
      )
    );
  }
  return article;
}

function renderMatrix(records, metric) {
  const target = document.getElementById("utility-matrix");
  target.replaceChildren();
  const recordsByUtility = new Map();
  for (const record of records) {
    if (!recordsByUtility.has(record.panel_id)) recordsByUtility.set(record.panel_id, []);
    recordsByUtility.get(record.panel_id).push(record);
  }
  for (const utilityRecords of recordsByUtility.values()) {
    utilityRecords.sort((a, b) => a.year - b.year);
  }

  for (const ownership of OWNERSHIP_ORDER) {
    const row = createElement("section", `ownership-row ownership-row--${ownership.toLowerCase()}`);
    const utilityIds = UTILITY_ORDER.filter((utilityId) => {
      const utilityRecords = recordsByUtility.get(utilityId);
      return utilityRecords?.[utilityRecords.length - 1].ownership_2024 === ownership;
    });
    const latestRecords = utilityIds.map((utilityId) => {
      const utilityRecords = recordsByUtility.get(utilityId);
      return utilityRecords[utilityRecords.length - 1];
    });
    const latestValues = latestRecords.map(metric.valueFor).filter(isNumber);
    const rowHeader = createElement("header", "ownership-row__header");
    const heading = createElement("div", "ownership-row__heading");
    const title = createElement("h3", "ownership-row__title");
    title.append(
      createElement(
        "i",
        `ownership-swatch ownership-swatch--${ownership.toLowerCase()}`
      ),
      document.createTextNode(ownership)
    );
    heading.append(
      title,
      createElement("p", "ownership-row__description", OWNERSHIP_DESCRIPTIONS[ownership])
    );
    let summaryText;
    if (metric.kind === "reliability") {
      const latestStandards = new Set(
        latestRecords
          .map((record) => record.reliability?.reporting_standard)
          .filter(Boolean)
      );
      const methodDescription =
        latestStandards.size > 1
          ? "mixed IEEE/Non-IEEE reporting"
          : `${formatReportingStandard([...latestStandards][0])} reporting`;
      summaryText = `${utilityIds.length} utilities · 2024 data for ${latestValues.length}/${utilityIds.length} · ${methodDescription}`;
    } else if (metric.kind === "price") {
      summaryText = `${utilityIds.length} utilities · 2024 data for ${latestValues.length}/${utilityIds.length} · see ownership comparison above`;
    } else {
      summaryText = `${utilityIds.length} utilities · 2024 coverage median ${metric.formatValue(
        median(latestValues)
      )} · range ${metric.formatValue(Math.min(...latestValues))}–${metric.formatValue(
        Math.max(...latestValues)
      )}`;
    }
    const summary = createElement(
      "p",
      "ownership-row__summary",
      summaryText
    );
    rowHeader.append(heading, summary);
    row.appendChild(rowHeader);

    const charts = createElement("div", "ownership-row__charts");
    for (const utilityId of utilityIds) {
      charts.appendChild(buildUtilityPanel(recordsByUtility.get(utilityId), metric));
    }
    row.appendChild(charts);
    target.appendChild(row);
  }
}

function metricFinding(records, metric) {
  if (metric.kind === "price") {
    const available = records.filter((record) =>
      isNumber(metric.valueFor(record))
    ).length;
    const minorityCoverage = records.filter(
      (record) => isNumber(metric.valueFor(record)) && hasMinorityCoverage(record, metric)
    ).length;
    const missing = records.length - available;
    const missingNote = missing
      ? ` ${missing} utility-years are blank because the annual EIA table has no published bundled price for that utility and class.`
      : "";
    return `${available} of ${records.length} utility-years have an EIA-published bundled ${metric.customerClass} price; ${minorityCoverage} cover less than half of customers in that class and are outlined in orange.${missingNote} Switch to customer coverage to inspect the exact shares. No published price is changed.`;
  }

  if (metric.kind === "reliability") {
    const available = records.filter((record) =>
      isNumber(metric.valueFor(record))
    ).length;
    const scopeNote =
      metric.reliabilityScope === "without-major-events"
        ? "This view removes major events under each utility’s reported method and is intended to describe routine reliability."
        : "This view includes major events and therefore shows the large spikes customers can experience during major storms.";
    const excluded = records.filter((record) =>
      isReliabilityFieldExcluded(record, metric.valueKey)
    ).length;
    const exclusionNote = excluded
      ? ` ${excluded} published value${excluded === 1 ? " is" : "s are"} omitted because ${
          excluded === 1 ? "it conflicts" : "they conflict"
        } with a regulator filing; ${excluded === 1 ? "it remains" : "they remain"} in the audit.`
      : "";
    const changedMethods = new Set(
      records
        .filter((record) => record.reliability?.standard_changed_during_panel)
        .map((record) => record.panel_id)
    ).size;
    return `${available} of ${records.length} utility-years have this value.${exclusionNote} ${scopeNote} Lines stop at missing or withheld years. ${changedMethods} utilities change reporting method during 2013–2024. The ownership overview reports simple annual medians with sample counts, while these panels preserve each utility separately.`;
  }

  const latest = records
    .filter((record) => record.year === 2024)
    .filter((record) => isNumber(metric.valueFor(record)));
  const lowest = [...latest].sort(
    (a, b) => metric.valueFor(a) - metric.valueFor(b)
  )[0];
  const highest = [...latest].sort(
    (a, b) => metric.valueFor(b) - metric.valueFor(a)
  )[0];
  return `Bundled ${metric.customerClass} coverage is uneven across the selected utilities. In 2024 it ranges from ${metric.formatValue(
    metric.valueFor(lowest)
  )} at ${SHORT_NAMES[lowest.panel_id]} to ${metric.formatValue(
    metric.valueFor(highest)
  )} at ${SHORT_NAMES[highest.panel_id]}. This is a coverage warning, not an adjustment to the published price.`;
}

function priceComparisonDetailText(record, coverageRule, priceBasis) {
  const count = Number(record.included_utility_count);
  if (!count) {
    return `${record.year} · No selected utilities meet the 50% coverage rule`;
  }
  const minorityCount = Number(record.minority_coverage_count);
  const customerClass = CUSTOMER_CLASS_LABELS[record.customer_class].toLowerCase();
  const minorityNote =
    coverageRule === "all_published" && minorityCount > 0
      ? `\nLow coverage: ${minorityCount} of ${count} utilities ${
          minorityCount === 1 ? "reports" : "report"
        } a bundled price covering fewer than half of ${
          minorityCount === 1 ? "its" : "their"
        } ${customerClass} customers`
      : "";
  return `${record.year} · median ${formatPrice(
    record.median_value
  )} · ${PRICE_BASIS_LABELS[priceBasis]}\nrange ${formatPrice(
    record.minimum_value
  )}–${formatPrice(record.maximum_value)} · ${count} utilit${
    count === 1 ? "y" : "ies"
  }${minorityNote}`;
}

function reliabilityComparisonDetailText(record, metric) {
  const count = Number(record.included_utility_count);
  const available = Number(record.available_utility_count);
  if (!count) {
    return `${record.year} · No usable values reported`;
  }
  const methodNote =
    record.reporting_method_count > 1
      ? "mixed IEEE/Non-IEEE methods"
      : `${formatReportingStandard(record.reporting_standard)} method`;
  return `${record.year} · median ${metric.formatValue(
    record.median_value
  )}\n${count} of ${available} utilities · ${methodNote}`;
}

function validComparisonSegments(records) {
  const segments = [];
  let current = [];
  for (const record of records) {
    if (isNumber(record.median_value)) {
      current.push(record);
    } else if (current.length) {
      segments.push(current);
      current = [];
    }
  }
  if (current.length) segments.push(current);
  return segments;
}

function priceSummaryForBasis(records, priceBasis) {
  return records.map((record) => ({
    ...record,
    median_value: priceForBasis(
      record.median_price_cents_kwh,
      record.year,
      priceBasis
    ),
    minimum_value: priceForBasis(
      record.minimum_price_cents_kwh,
      record.year,
      priceBasis
    ),
    maximum_value: priceForBasis(
      record.maximum_price_cents_kwh,
      record.year,
      priceBasis
    ),
    available_utility_count: record.published_price_count,
  }));
}

function reliabilitySummaryRecords(records, metric) {
  const summary = [];
  for (let year = 2013; year <= 2024; year += 1) {
    for (const ownership of OWNERSHIP_ORDER) {
      const groupRecords = records.filter(
        (record) => record.year === year && record.ownership === ownership
      );
      const usable = groupRecords.filter((record) =>
        isNumber(metric.valueFor(record))
      );
      const values = usable.map(metric.valueFor);
      const standards = [
        ...new Set(
          usable
            .map((record) => record.reliability?.reporting_standard)
            .filter(Boolean)
        ),
      ];
      summary.push({
        year,
        ownership,
        median_value: values.length ? median(values) : null,
        minimum_value: values.length ? Math.min(...values) : null,
        maximum_value: values.length ? Math.max(...values) : null,
        included_utility_count: values.length,
        available_utility_count: groupRecords.length,
        reporting_method_count: standards.length,
        reporting_standard: standards.length === 1 ? standards[0] : null,
      });
    }
  }
  return summary;
}

function buildOwnershipComparisonCard(records, ownership, config) {
  const width = 340;
  const height = 222;
  const margin = { top: 10, right: 12, bottom: 28, left: 38 };
  const plotWidth = width - margin.left - margin.right;
  const plotHeight = height - margin.top - margin.bottom;
  const minimumYear = 2013;
  const maximumYear = 2024;
  const x = (year) =>
    margin.left + ((year - minimumYear) / (maximumYear - minimumYear)) * plotWidth;
  const y = (value) =>
    margin.top + plotHeight - (Number(value) / config.maximum) * plotHeight;

  const card = createElement(
    "article",
    `ownership-comparison-card ownership-comparison-card--${ownership.toLowerCase()}`
  );
  const title = createElement("h3", "ownership-comparison-card__title");
  title.append(
    createElement(
      "i",
      `ownership-swatch ownership-swatch--${ownership.toLowerCase()}`
    ),
    document.createTextNode(ownership)
  );
  card.appendChild(title);
  card.appendChild(
    createElement(
      "p",
      "ownership-comparison-card__description",
      OWNERSHIP_DESCRIPTIONS[ownership]
    )
  );

  const svg = svgElement("svg", {
    class: "ownership-comparison-chart",
    viewBox: `0 0 ${width} ${height}`,
    role: "img",
    "aria-label": `${ownership} selected-sample ${config.ariaLabel}, 2013 to 2024`,
  });

  for (const tick of config.ticks) {
    const tickY = y(tick);
    svg.appendChild(
      svgElement("line", {
        class: "ownership-comparison-chart__gridline",
        x1: margin.left,
        x2: width - margin.right,
        y1: tickY,
        y2: tickY,
      })
    );
    const label = svgElement("text", {
      class: "ownership-comparison-chart__axis-label",
      x: margin.left - 6,
      y: tickY + 3,
      "text-anchor": "end",
    });
    label.textContent = config.formatAxis(tick);
    svg.appendChild(label);
  }

  for (const year of [2013, 2016, 2020, 2024]) {
    const label = svgElement("text", {
      class: "ownership-comparison-chart__axis-label",
      x: x(year),
      y: height - 7,
      "text-anchor": year === 2013 ? "start" : year === 2024 ? "end" : "middle",
    });
    label.textContent = year;
    svg.appendChild(label);
  }

  const segments = validComparisonSegments(records);
  for (const segment of segments) {
    if (config.showRange && segment.length > 1) {
      const upper = segment.map(
        (record, index) =>
          `${index === 0 ? "M" : "L"} ${x(record.year).toFixed(2)} ${y(
            record.maximum_value
          ).toFixed(2)}`
      );
      const lower = [...segment]
        .reverse()
        .map(
          (record) =>
            `L ${x(record.year).toFixed(2)} ${y(
              record.minimum_value
            ).toFixed(2)}`
        );
      svg.appendChild(
        svgElement("path", {
          class: `ownership-comparison-chart__range ownership-comparison-chart__range--${ownership.toLowerCase()}`,
          d: `${upper.join(" ")} ${lower.join(" ")} Z`,
        })
      );
    }
    const medianPath = segment
      .map(
        (record, index) =>
          `${index === 0 ? "M" : "L"} ${x(record.year).toFixed(2)} ${y(
            record.median_value
          ).toFixed(2)}`
      )
      .join(" ");
    svg.appendChild(
      svgElement("path", {
        class: `ownership-comparison-chart__median ownership-comparison-chart__median--${ownership.toLowerCase()}`,
        d: medianPath,
      })
    );
  }

  const latestRecord = records.find((record) => record.year === 2024);
  const detail = createElement(
    "p",
    "ownership-comparison-card__detail",
    config.detailFor(latestRecord)
  );
  for (const record of records) {
    if (!isNumber(record.median_value)) continue;
    const flagged = config.flagged(record);
    const point = svgElement("circle", {
      class: `ownership-comparison-chart__point ownership-fill--${ownership.toLowerCase()}${
        flagged ? " ownership-comparison-chart__point--flagged" : ""
      }`,
      cx: x(record.year),
      cy: y(record.median_value),
      r: 4.5,
      tabindex: "0",
      role: "img",
      "aria-label": config.detailFor(record),
    });
    const pointTitle = svgElement("title");
    pointTitle.textContent = config.detailFor(record);
    point.appendChild(pointTitle);
    const showDetail = () => {
      detail.textContent = config.detailFor(record);
    };
    point.addEventListener("mouseenter", showDetail);
    point.addEventListener("focus", showDetail);
    point.addEventListener("click", showDetail);
    svg.appendChild(point);
  }
  card.append(svg, detail);
  return card;
}

function priceComparisonFinding(records, customerClass, coverageRule, priceBasis) {
  const latest = records
    .filter((record) => record.year === 2024 && Number(record.included_utility_count) > 0)
    .sort((a, b) => b.median_value - a.median_value);
  const ranking = latest
    .map((record) => `${record.ownership} ${formatPrice(record.median_value)}`)
    .join(", then ");
  const leaderCounts = new Map();
  for (let year = 2013; year <= 2024; year += 1) {
    const yearRecords = records.filter(
      (record) => record.year === year && Number(record.included_utility_count) > 0
    );
    if (!yearRecords.length) continue;
    const leader = [...yearRecords].sort(
      (a, b) => b.median_value - a.median_value
    )[0].ownership;
    leaderCounts.set(leader, (leaderCounts.get(leader) || 0) + 1);
  }
  const leaderText = [...leaderCounts.entries()]
    .sort((a, b) => b[1] - a[1])
    .map(([ownership, count]) =>
      count === 12
        ? `${ownership} has the highest ${customerClass} median in all 12 years`
        : `${ownership} has the highest ${customerClass} median in ${count} of 12 years`
    )
    .join("; ");
  const totalPublished = latest.reduce(
    (sum, record) => sum + Number(record.published_price_count),
    0
  );
  const totalIncluded = latest.reduce(
    (sum, record) => sum + Number(record.included_utility_count),
    0
  );
  const totalMinority = latest.reduce(
    (sum, record) => sum + Number(record.minority_coverage_count),
    0
  );
  const sampleNote =
    coverageRule === "all_published"
      ? `All ${totalPublished} published 2024 prices are included; ${totalMinority} of them cover fewer than half of customers and are outlined in orange.`
      : `${totalIncluded} of ${totalPublished} published 2024 prices each cover at least half of customers.`;
  const emptyRows = records.filter(
    (record) => Number(record.included_utility_count) === 0
  );
  const emptyNote = emptyRows.length
    ? ` ${emptyRows
        .map((record) => `${record.ownership} ${record.year}`)
        .join(", ")} is blank because no selected utility meets the rule.`
    : "";
  const basisNote =
    priceBasis === "real_2024"
      ? "Prices are expressed in 2024 cents; the inflation adjustment changes comparisons over time, not rankings within the same year."
      : "Prices are the nominal values published for each year.";
  return `${leaderText}. The selected-sample 2024 ranking is ${ranking}. ${sampleNote}${emptyNote} ${basisNote} This is descriptive, not causal.`;
}

function reliabilityComparisonFinding(records, metric, panelRecords) {
  const latest = records
    .filter((record) => record.year === 2024 && record.included_utility_count > 0)
    .sort((a, b) => a.median_value - b.median_value);
  const ranking = latest
    .map(
      (record) =>
        `${record.ownership} ${metric.formatValue(record.median_value)} (${record.included_utility_count}/${record.available_utility_count})`
    )
    .join(", then ");
  const highestCounts = new Map();
  for (let year = 2013; year <= 2024; year += 1) {
    const yearRecords = records.filter(
      (record) => record.year === year && record.included_utility_count > 0
    );
    if (yearRecords.length !== OWNERSHIP_ORDER.length) continue;
    const highest = [...yearRecords].sort(
      (a, b) => b.median_value - a.median_value
    )[0].ownership;
    highestCounts.set(highest, (highestCounts.get(highest) || 0) + 1);
  }
  const [mostOftenHighest, highestYears] = [...highestCounts.entries()].sort(
    (a, b) => b[1] - a[1]
  )[0];
  const changedMethods = new Set(
    panelRecords
      .filter((record) => record.reliability?.standard_changed_during_panel)
      .map((record) => record.panel_id)
  ).size;
  return `Lower is better. The 2024 median ranking is ${ranking}. ${mostOftenHighest} has the highest annual group median in ${highestYears} of 12 years. Values are ${RELIABILITY_SCOPE_LABELS[metric.reliabilityScope]}. ${changedMethods} utilities change reporting method, so this is a clear descriptive pattern, not proof that ownership caused the difference.`;
}

function setupOwnershipComparison(summaryRecords, panelRecords) {
  const status = document.getElementById("ownership-comparison-status");
  if (!Array.isArray(summaryRecords) || summaryRecords.length !== 216) {
    status.hidden = false;
    status.textContent = "The ownership price summary did not load.";
    return;
  }
  if (!Array.isArray(panelRecords) || panelRecords.length !== EXPECTED_PANEL_ROWS) {
    status.hidden = false;
    status.textContent = "The ownership reliability summary did not load.";
    return;
  }
  const measureSelect = document.getElementById("comparison-measure");
  const customerClassControl = document.getElementById(
    "comparison-customer-class-control"
  );
  const customerClassSelect = document.getElementById("comparison-customer-class");
  const coverageRuleControl = document.getElementById(
    "comparison-coverage-rule-control"
  );
  const coverageRuleSelect = document.getElementById("comparison-coverage-rule");
  const priceBasisControl = document.getElementById("comparison-price-basis-control");
  const priceBasisSelect = document.getElementById("comparison-price-basis");
  const reliabilityScopeControl = document.getElementById(
    "comparison-reliability-scope-control"
  );
  const reliabilityScopeSelect = document.getElementById(
    "comparison-reliability-scope"
  );
  const rangeLegend = document.getElementById("comparison-range-legend");
  const coverageLegend = document.getElementById("comparison-coverage-legend");
  const charts = document.getElementById("ownership-comparison-charts");
  const finding = document.getElementById("ownership-comparison-finding");

  const render = () => {
    const isPrice = measureSelect.value === "price";
    customerClassControl.hidden = !isPrice;
    coverageRuleControl.hidden = !isPrice;
    priceBasisControl.hidden = !isPrice;
    reliabilityScopeControl.hidden = isPrice;
    rangeLegend.hidden = !isPrice;
    coverageLegend.hidden = !isPrice;

    let selected;
    let config;
    if (isPrice) {
      const customerClass = customerClassSelect.value;
      const coverageRule = coverageRuleSelect.value;
      const priceBasis = priceBasisSelect.value;
      selected = priceSummaryForBasis(
        summaryRecords
          .filter(
            (record) =>
              record.customer_class === customerClass &&
              record.coverage_rule === coverageRule
          )
          .sort((a, b) => a.year - b.year),
        priceBasis
      );
      const maximum = niceMaximum(
        Math.max(...selected.map((record) => record.maximum_value).filter(isNumber))
      );
      config = {
        maximum,
        ticks: [0, maximum / 2, maximum],
        formatAxis: (value) => `${formatReliabilityAxis(value)}¢`,
        ariaLabel: `annual median bundled ${customerClass} price and observed range`,
        showRange: true,
        flagged: (record) =>
          coverageRule === "all_published" &&
          Number(record.minority_coverage_count) > 0,
        detailFor: (record) =>
          priceComparisonDetailText(record, coverageRule, priceBasis),
      };
      finding.textContent = priceComparisonFinding(
        selected,
        customerClass,
        coverageRule,
        priceBasis
      );
    } else {
      const metric = resolveMetric(
        METRICS[measureSelect.value],
        panelRecords,
        reliabilityScopeSelect.value,
        "residential"
      );
      selected = reliabilitySummaryRecords(panelRecords, metric);
      const maximum = niceMaximum(
        Math.max(...selected.map((record) => record.median_value).filter(isNumber))
      );
      config = {
        maximum,
        ticks: [0, maximum / 2, maximum],
        formatAxis: formatReliabilityAxis,
        ariaLabel: `annual median ${metric.label.toLowerCase()}`,
        showRange: false,
        flagged: () => false,
        detailFor: (record) => reliabilityComparisonDetailText(record, metric),
      };
      finding.textContent = reliabilityComparisonFinding(
        selected,
        metric,
        panelRecords
      );
    }

    charts.replaceChildren();
    for (const ownership of OWNERSHIP_ORDER) {
      charts.appendChild(
        buildOwnershipComparisonCard(
          selected.filter((record) => record.ownership === ownership),
          ownership,
          config
        )
      );
    }
  };
  measureSelect.addEventListener("change", render);
  customerClassSelect.addEventListener("change", () => {
    const utilityCustomerClass = document.getElementById("customer-class");
    if (utilityCustomerClass.value !== customerClassSelect.value) {
      utilityCustomerClass.value = customerClassSelect.value;
      utilityCustomerClass.dispatchEvent(new Event("change"));
    }
    const caseStudyCustomerClass = document.getElementById(
      "ct-case-customer-class"
    );
    if (
      caseStudyCustomerClass &&
      caseStudyCustomerClass.value !== customerClassSelect.value
    ) {
      caseStudyCustomerClass.value = customerClassSelect.value;
      caseStudyCustomerClass.dispatchEvent(new Event("change"));
    }
    render();
  });
  coverageRuleSelect.addEventListener("change", render);
  priceBasisSelect.addEventListener("change", render);
  reliabilityScopeSelect.addEventListener("change", render);
  render();
}

function formatSignedCents(value, digits = 2) {
  const number = Number(value);
  const sign = number > 0 ? "+" : number < 0 ? "−" : "";
  return `${sign}${Math.abs(number).toFixed(digits)}¢/kWh`;
}

function setupComparisonTabs() {
  const observedTab = document.getElementById("observed-comparison-tab");
  const adjustedTab = document.getElementById("adjusted-comparison-tab");
  const observedPanel = document.getElementById("observed-comparison-panel");
  const adjustedPanel = document.getElementById("adjusted-comparison-panel");
  const tabs = [observedTab, adjustedTab];

  const activate = (tab) => {
    const showAdjusted = tab === adjustedTab;
    observedPanel.hidden = showAdjusted;
    adjustedPanel.hidden = !showAdjusted;
    for (const item of tabs) {
      const selected = item === tab;
      item.classList.toggle("is-active", selected);
      item.setAttribute("aria-selected", String(selected));
      item.tabIndex = selected ? 0 : -1;
    }
  };

  observedTab.addEventListener("click", () => activate(observedTab));
  adjustedTab.addEventListener("click", () => activate(adjustedTab));
  tabs.forEach((tab, index) => {
    tab.addEventListener("keydown", (event) => {
      if (!['ArrowLeft', 'ArrowRight'].includes(event.key)) return;
      event.preventDefault();
      const direction = event.key === "ArrowRight" ? 1 : -1;
      const next = tabs[(index + direction + tabs.length) % tabs.length];
      activate(next);
      next.focus();
    });
  });
  activate(observedTab);
}

function ownershipModelDomain(models) {
  const effects = models.flatMap((model) => model.ownership_results || []);
  const lowest = Math.min(...effects.map((effect) => effect.confidence_95_low));
  const highest = Math.max(...effects.map((effect) => effect.confidence_95_high));
  return {
    minimum: Math.min(-5, Math.floor((lowest - 1) / 5) * 5),
    maximum: Math.max(5, Math.ceil((highest + 1) / 5) * 5),
  };
}

function buildOwnershipPriceModelChart(model, domain) {
  const width = 760;
  const height = 235;
  const margin = { top: 38, right: 68, bottom: 50, left: 92 };
  const plotWidth = width - margin.left - margin.right;
  const axisY = height - margin.bottom;
  const x = (value) =>
    margin.left +
    ((value - domain.minimum) / (domain.maximum - domain.minimum)) * plotWidth;
  const svg = svgElement("svg", {
    class: "ownership-price-model-svg",
    viewBox: `0 0 ${width} ${height}`,
    role: "img",
    "aria-label": `${CUSTOMER_CLASS_LABELS[model.customer_class]} adjusted price differences from DOM. ${model.ownership_results
      .map(
        (effect) =>
          `${effect.ownership} ${formatSignedCents(effect.estimate_cents_kwh)} with a 95 percent range from ${formatSignedCents(effect.confidence_95_low)} to ${formatSignedCents(effect.confidence_95_high)}`
      )
      .join(". ")}`,
  });

  for (let tick = domain.minimum; tick <= domain.maximum; tick += 5) {
    const tickX = x(tick);
    svg.appendChild(
      svgElement("line", {
        class:
          tick === 0
            ? "ownership-price-model-svg__zero"
            : "ownership-price-model-svg__gridline",
        x1: tickX,
        x2: tickX,
        y1: margin.top - 8,
        y2: axisY,
      })
    );
    const label = svgElement("text", {
      class: "ownership-price-model-svg__axis-label",
      x: tickX,
      y: height - 21,
      "text-anchor": "middle",
    });
    label.textContent = tick === 0 ? "0 (same as DOM)" : `${tick}¢`;
    svg.appendChild(label);
  }

  model.ownership_results.forEach((effect, index) => {
    const y = 78 + index * 67;
    const ownership = effect.ownership.toLowerCase();
    const rowLabel = svgElement("text", {
      class: "ownership-price-model-svg__row-label",
      x: margin.left - 16,
      y: y + 5,
      "text-anchor": "end",
    });
    rowLabel.textContent = effect.ownership;
    svg.appendChild(rowLabel);

    const lowX = x(effect.confidence_95_low);
    const highX = x(effect.confidence_95_high);
    svg.appendChild(
      svgElement("line", {
        class: `ownership-price-model-svg__interval ownership-price-model-svg__interval--${ownership}`,
        x1: lowX,
        x2: highX,
        y1: y,
        y2: y,
      })
    );
    for (const capX of [lowX, highX]) {
      svg.appendChild(
        svgElement("line", {
          class: `ownership-price-model-svg__cap ownership-price-model-svg__cap--${ownership}`,
          x1: capX,
          x2: capX,
          y1: y - 7,
          y2: y + 7,
        })
      );
    }
    const point = svgElement("circle", {
      class: `ownership-price-model-svg__point ownership-fill--${ownership}`,
      cx: x(effect.estimate_cents_kwh),
      cy: y,
      r: 7,
    });
    const title = svgElement("title");
    title.textContent = `${effect.ownership}: ${formatSignedCents(
      effect.estimate_cents_kwh
    )}; 95% range ${formatSignedCents(effect.confidence_95_low)} to ${formatSignedCents(
      effect.confidence_95_high
    )}`;
    point.appendChild(title);
    svg.appendChild(point);

    const estimateLabel = svgElement("text", {
      class: "ownership-price-model-svg__estimate",
      x: width - 4,
      y: y + 5,
      "text-anchor": "end",
    });
    estimateLabel.textContent = formatSignedCents(effect.estimate_cents_kwh);
    svg.appendChild(estimateLabel);
  });
  return svg;
}

function ownershipPriceModelFinding(model) {
  const effects = Object.fromEntries(
    model.ownership_results.map((effect) => [effect.ownership, effect])
  );
  const mtc = effects.MTC;
  const coop = effects.COOP;
  const customer = CUSTOMER_CLASS_LABELS[model.customer_class].toLowerCase();
  const mtcAmount = Math.abs(mtc.estimate_cents_kwh).toFixed(2);
  const coopAmount = Math.abs(coop.estimate_cents_kwh).toFixed(2);
  if (!mtc.confidence_interval_excludes_zero) {
    return `For ${customer} customers, MTC prices are estimated ${mtcAmount}¢/kWh lower than DOM prices, but the uncertainty line crosses zero, so that difference is uncertain. COOP prices are estimated ${coopAmount}¢ lower, and that range stays below zero. This does not prove ownership caused the price differences.`;
  }
  return `For ${customer} customers, prices are estimated ${mtcAmount}¢/kWh lower at MTC utilities and ${coopAmount}¢ lower at COOP utilities than at DOM utilities, after accounting for state and year. Both uncertainty ranges stay below zero. This does not prove ownership caused the price differences.`;
}

function expandedPriceModelFinding(model) {
  const effects = Object.fromEntries(
    model.ownership_results.map((effect) => [effect.ownership, effect])
  );
  const mtc = effects.MTC;
  const coop = effects.COOP;
  const customer = CUSTOMER_CLASS_LABELS[model.customer_class].toLowerCase();
  const mtcAmount = Math.abs(mtc.estimate_cents_kwh).toFixed(2);
  const coopAmount = Math.abs(coop.estimate_cents_kwh).toFixed(2);
  const rangeDescription = (effect) =>
    effect.confidence_interval_excludes_zero
      ? "stays below zero"
      : "crosses zero, so that comparison is uncertain";
  return `With 42 utilities, ${customer} prices are estimated ${mtcAmount}¢/kWh lower at MTC utilities and ${coopAmount}¢ lower at COOP utilities than at DOM utilities. The MTC range ${rangeDescription(
    mtc
  )}; the COOP range ${rangeDescription(coop)}. The direction is the same as in the main sample.`;
}

function reliabilityModelFinding(results) {
  if (!results || !Array.isArray(results.models)) {
    return "The adjusted reliability check did not load.";
  }
  const primaryModels = results.models.filter(
    (model) =>
      model.event_scope === "without_major_events" &&
      model.reporting_sample === "all_methods"
  );
  const expectedMetrics = new Set(["saidi", "saifi", "caidi"]);
  const complete =
    primaryModels.length === 3 &&
    primaryModels.every(
      (model) =>
        expectedMetrics.has(model.metric) &&
        model.ownership_results?.length === 2
    );
  if (!complete) return "The adjusted reliability check is incomplete.";
  const clearEffects = primaryModels.flatMap(
    (model) =>
      model.ownership_results.filter(
        (effect) => effect.confidence_interval_excludes_zero
      )
  );
  if (clearEffects.length > 0) {
    return "Some adjusted routine-reliability differences remain, but they are not consistent across the reliability measures or sensitivity checks. Reliability does not provide a stable explanation for the price differences.";
  }
  return "After accounting for state, year, and reporting method, none of the routine SAIDI, SAIFI, or CAIDI ownership differences are clear. Results also move when storms or reporting samples change, so reliability does not provide a stable explanation for the price differences.";
}

function renderOwnershipPriceModelTable(model) {
  const tableBody = document.getElementById("ownership-price-model-table");
  tableBody.replaceChildren();
  for (const effect of model.ownership_results) {
    const row = document.createElement("tr");
    const ownershipCell = document.createElement("td");
    ownershipCell.append(
      createElement("i", `ownership-swatch ownership-swatch--${effect.ownership.toLowerCase()}`),
      createElement("strong", "", effect.ownership)
    );
    const estimateCell = createElement(
      "td",
      "numeric-cell",
      formatSignedCents(effect.estimate_cents_kwh)
    );
    const rangeCell = createElement(
      "td",
      "numeric-cell",
      `${formatSignedCents(effect.confidence_95_low)} to ${formatSignedCents(
        effect.confidence_95_high
      )}`
    );
    const readingCell = createElement(
      "td",
      "",
      effect.confidence_interval_excludes_zero
        ? "Range stays below zero"
        : "Range crosses zero; uncertain"
    );
    row.append(ownershipCell, estimateCell, rangeCell, readingCell);
    tableBody.appendChild(row);
  }
}

function setupOwnershipPriceModel(
  results,
  expandedResults,
  reliabilityResults
) {
  setupComparisonTabs();
  const status = document.getElementById("ownership-price-model-status");
  if (!results || !Array.isArray(results.models) || results.models.length !== 6) {
    status.hidden = false;
    status.textContent = "The adjusted ownership-price results did not load.";
    return;
  }
  const primaryModels = results.models.filter(
    (model) => model.coverage_rule === "all_published"
  );
  if (primaryModels.length !== 3) {
    status.hidden = false;
    status.textContent = "The three adjusted customer-price results are incomplete.";
    return;
  }

  const domain = ownershipModelDomain(primaryModels);
  const customerClassSelect = document.getElementById("model-customer-class");
  const observedCustomerClassSelect = document.getElementById(
    "comparison-customer-class"
  );
  const chart = document.getElementById("ownership-price-model-chart");
  const finding = document.getElementById("ownership-price-model-finding");
  const title = document.getElementById("ownership-price-model-title");
  const method = document.getElementById("ownership-price-model-method");
  const expandedFinding = document.getElementById(
    "expanded-price-check-finding"
  );
  const reliabilityFinding = document.getElementById(
    "reliability-model-finding"
  );
  const expandedModels = Array.isArray(expandedResults?.models)
    ? expandedResults.models.filter(
        (model) => model.coverage_rule === "all_published"
      )
    : [];

  reliabilityFinding.textContent = reliabilityModelFinding(reliabilityResults);

  const render = () => {
    const model = primaryModels.find(
      (candidate) => candidate.customer_class === customerClassSelect.value
    );
    title.textContent = `Adjusted ${model.customer_class} price difference from DOM`;
    chart.replaceChildren(buildOwnershipPriceModelChart(model, domain));
    finding.textContent = ownershipPriceModelFinding(model);
    const expandedModel = expandedModels.find(
      (candidate) => candidate.customer_class === customerClassSelect.value
    );
    expandedFinding.textContent = expandedModel
      ? expandedPriceModelFinding(expandedModel)
      : "The expanded-sample check did not load.";
    renderOwnershipPriceModelTable(model);
    method.textContent = `${model.observation_count} utility-year prices from ${model.utility_cluster_count} utilities, 2013–2024. Prices are inflation-adjusted to 2024 cents. Technically, this is an unweighted OLS model with ownership, state, and year indicators; 95% ranges use standard errors clustered by utility. DOM is the reference group.`;
  };

  customerClassSelect.addEventListener("change", () => {
    if (observedCustomerClassSelect.value !== customerClassSelect.value) {
      observedCustomerClassSelect.value = customerClassSelect.value;
      observedCustomerClassSelect.dispatchEvent(new Event("change"));
    }
    render();
  });
  observedCustomerClassSelect.addEventListener("change", () => {
    if (customerClassSelect.value !== observedCustomerClassSelect.value) {
      customerClassSelect.value = observedCustomerClassSelect.value;
      render();
    }
  });
  render();
}

function formatTWh(valueMwh) {
  return `${(Number(valueMwh) / 1_000_000).toFixed(1)} TWh`;
}

function isoFuelDetailText(record) {
  return `${record.year} · ${record.fuel} ${Number(record.share_pct).toFixed(
    1
  )}%\n${formatTWh(record.net_generation_mwh)} of ${formatTWh(
    record.positive_generation_total_mwh
  )} regional plant generation`;
}

function buildIsoFuelMixCard(records, region) {
  const width = 520;
  const height = 264;
  const margin = { top: 12, right: 12, bottom: 30, left: 40 };
  const plotWidth = width - margin.left - margin.right;
  const plotHeight = height - margin.top - margin.bottom;
  const years = [...new Set(records.map((record) => record.year))].sort(
    (a, b) => a - b
  );
  const byKey = new Map(
    records.map((record) => [`${record.year}:${record.fuel}`, record])
  );
  const step = plotWidth / years.length;
  const barWidth = step * 0.72;
  const x = (index) => margin.left + index * step + (step - barWidth) / 2;
  const y = (share) => margin.top + plotHeight - (share / 100) * plotHeight;

  const card = createElement("article", "iso-fuel-mix-card");
  card.appendChild(createElement("h3", "iso-fuel-mix-card__title", region));
  const baCode = records[0].balancing_authority_code_eia;
  card.appendChild(
    createElement(
      "p",
      "iso-fuel-mix-card__description",
      `EIA balancing-authority code ${baCode} · share of annual plant generation`
    )
  );

  const svg = svgElement("svg", {
    class: "iso-fuel-mix-chart",
    viewBox: `0 0 ${width} ${height}`,
    role: "img",
    "aria-label": `${region} annual generation shares by fuel, 2013 to 2024`,
  });
  for (const tick of [0, 50, 100]) {
    const tickY = y(tick);
    svg.appendChild(
      svgElement("line", {
        class: "iso-fuel-mix-chart__gridline",
        x1: margin.left,
        x2: width - margin.right,
        y1: tickY,
        y2: tickY,
      })
    );
    const label = svgElement("text", {
      class: "iso-fuel-mix-chart__axis-label",
      x: margin.left - 7,
      y: tickY + 4,
      "text-anchor": "end",
    });
    label.textContent = `${tick}%`;
    svg.appendChild(label);
  }

  const latestRecords = records
    .filter((record) => record.year === Math.max(...years))
    .sort((a, b) => b.share_pct - a.share_pct);
  const latestTotal = latestRecords[0].positive_generation_total_mwh;
  const detail = createElement(
    "p",
    "iso-fuel-mix-card__detail",
    `${Math.max(...years)} · ${formatTWh(latestTotal)} of plant generation\nLargest sources: ${latestRecords
      .slice(0, 3)
      .map((record) => `${record.fuel} ${Number(record.share_pct).toFixed(1)}%`)
      .join(" · ")}`
  );

  years.forEach((year, index) => {
    let cumulativeShare = 0;
    for (const fuel of ISO_FUEL_ORDER) {
      const record = byKey.get(`${year}:${fuel}`);
      if (!record) throw new Error(`Missing ${region} ${year} ${fuel} record`);
      const share = Number(record.share_pct);
      const nextShare = cumulativeShare + share;
      if (share > 0) {
        const rect = svgElement("rect", {
          class: `iso-fuel-mix-chart__segment iso-fuel--${ISO_FUEL_SLUGS[fuel]}`,
          x: x(index),
          y: y(nextShare),
          width: barWidth,
          height: Math.max(0, y(cumulativeShare) - y(nextShare)),
          tabindex: "0",
          role: "img",
          "aria-label": isoFuelDetailText(record),
        });
        const title = svgElement("title");
        title.textContent = isoFuelDetailText(record);
        rect.appendChild(title);
        const showDetail = () => {
          detail.textContent = isoFuelDetailText(record);
        };
        rect.addEventListener("mouseenter", showDetail);
        rect.addEventListener("focus", showDetail);
        rect.addEventListener("click", showDetail);
        svg.appendChild(rect);
      }
      cumulativeShare = nextShare;
    }
    if ([2013, 2016, 2020, 2024].includes(year)) {
      const label = svgElement("text", {
        class: "iso-fuel-mix-chart__axis-label",
        x: x(index) + barWidth / 2,
        y: height - 8,
        "text-anchor": "middle",
      });
      label.textContent = year;
      svg.appendChild(label);
    }
  });

  card.append(svg, detail);
  return card;
}

function setupIsoFuelMix(records) {
  const status = document.getElementById("iso-fuel-mix-status");
  const charts = document.getElementById("iso-fuel-mix-charts");
  const legend = document.getElementById("iso-fuel-mix-legend");
  const expectedRows = ISO_REGIONS.length * 12 * ISO_FUEL_ORDER.length;
  if (!Array.isArray(records) || records.length !== expectedRows) {
    status.hidden = false;
    status.textContent = "The regional generation data did not load.";
    return;
  }

  legend.replaceChildren();
  for (const fuel of ISO_FUEL_ORDER) {
    const item = createElement("span", "iso-fuel-mix-legend__item");
    item.append(
      createElement(
        "i",
        `iso-fuel-mix-legend__swatch iso-fuel--${ISO_FUEL_SLUGS[fuel]}`
      ),
      document.createTextNode(fuel)
    );
    legend.appendChild(item);
  }

  charts.replaceChildren();
  for (const region of ISO_REGIONS) {
    const regionRecords = records
      .filter((record) => record.region === region)
      .sort((a, b) => a.year - b.year);
    charts.appendChild(buildIsoFuelMixCard(regionRecords, region));
  }
}

function formatRoe(value) {
  return `${(Number(value) * 100).toFixed(2)}%`;
}

function formatSignedBasisPoints(value) {
  const numeric = Number(value);
  return `${numeric > 0 ? "+" : ""}${numeric.toFixed(0)} bp`;
}

function caseStudyDocketTransitions(records) {
  const transitions = [];
  for (let index = 1; index < records.length; index += 1) {
    if (records[index].docket !== records[index - 1].docket) {
      transitions.push({ year: records[index].year, docket: records[index].docket });
    }
  }
  return transitions;
}

function caseStudyPath(records, valueFor, x, y) {
  const parts = [];
  let previousYear = null;
  for (const record of records) {
    const value = valueFor(record);
    if (!isNumber(value)) {
      previousYear = null;
      continue;
    }
    parts.push(
      `${previousYear === record.year - 1 ? "L" : "M"} ${x(record.year).toFixed(
        2
      )} ${y(value).toFixed(2)}`
    );
    previousYear = record.year;
  }
  return parts.join(" ");
}

function buildCtCaseChart({
  records,
  title,
  ariaLabel,
  minimum,
  maximum,
  ticks,
  valueFor,
  formatAxis,
  detailFor,
  sourceFor = null,
  actualValueFor = null,
  actualDetailFor = null,
  actualSourceFor = null,
  showRateDecisions = false,
  lowCoverageFor = null,
}) {
  const width = 520;
  const height = 216;
  const margin = { top: 12, right: 14, bottom: 28, left: 46 };
  const plotWidth = width - margin.left - margin.right;
  const plotHeight = height - margin.top - margin.bottom;
  const firstYear = 2013;
  const lastYear = 2024;
  const x = (year) =>
    margin.left + ((year - firstYear) / (lastYear - firstYear)) * plotWidth;
  const y = (value) =>
    margin.top +
    plotHeight -
    ((Number(value) - minimum) / (maximum - minimum)) * plotHeight;

  const block = createElement("div", "ct-case-chart-block");
  block.appendChild(createElement("h4", "ct-case-chart-block__title", title));
  const svg = svgElement("svg", {
    class: "ct-case-chart",
    viewBox: `0 0 ${width} ${height}`,
    role: "img",
    "aria-label": ariaLabel,
  });

  for (const tick of ticks) {
    const tickY = y(tick);
    svg.appendChild(
      svgElement("line", {
        class: "ct-case-chart__gridline",
        x1: margin.left,
        x2: width - margin.right,
        y1: tickY,
        y2: tickY,
      })
    );
    const label = svgElement("text", {
      class: "ct-case-chart__axis-label",
      x: margin.left - 7,
      y: tickY + 4,
      "text-anchor": "end",
    });
    label.textContent = formatAxis(tick);
    svg.appendChild(label);
  }

  for (const year of [2013, 2016, 2020, 2024]) {
    const label = svgElement("text", {
      class: "ct-case-chart__axis-label",
      x: x(year),
      y: height - 7,
      "text-anchor": year === 2013 ? "start" : year === 2024 ? "end" : "middle",
    });
    label.textContent = year;
    svg.appendChild(label);
  }

  if (showRateDecisions) {
    for (const transition of caseStudyDocketTransitions(records)) {
      const marker = svgElement("line", {
        class: "ct-case-chart__decision-line",
        x1: x(transition.year),
        x2: x(transition.year),
        y1: margin.top,
        y2: margin.top + plotHeight,
      });
      const markerTitle = svgElement("title");
      markerTitle.textContent = `${transition.year}: new rate decision, Docket ${transition.docket}`;
      marker.appendChild(markerTitle);
      svg.appendChild(marker);
    }
  }

  const mainPath = caseStudyPath(records, valueFor, x, y);
  if (mainPath) {
    svg.appendChild(
      svgElement("path", { class: "ct-case-chart__line", d: mainPath })
    );
  }

  if (actualValueFor) {
    const actualPath = caseStudyPath(records, actualValueFor, x, y);
    if (actualPath) {
      svg.appendChild(
        svgElement("path", {
          class: "ct-case-chart__line ct-case-chart__line--actual",
          d: actualPath,
        })
      );
    }
  }

  const latestMain = [...records].reverse().find((record) => isNumber(valueFor(record)));
  const detail = createElement("div", "ct-case-chart__detail");
  const showRecordDetail = (record, recordDetailFor, recordSourceFor) => {
    detail.replaceChildren();
    detail.appendChild(
      createElement("span", "ct-case-chart__detail-text", recordDetailFor(record))
    );
    const source = recordSourceFor?.(record);
    if (source?.url) {
      const link = createElement(
        "a",
        "ct-case-chart__source-link",
        `Source for ${record.year}: ${source.label}`
      );
      link.href = source.url;
      link.target = "_blank";
      link.rel = "noopener";
      if (source.location) link.title = source.location;
      detail.appendChild(link);
    }
    for (const chartPoint of svg.querySelectorAll(".ct-case-chart__point--active")) {
      chartPoint.classList.remove("ct-case-chart__point--active");
    }
    const activePoint = svg.querySelector(
      `.ct-case-chart__point[data-year="${record.year}"]`
    );
    activePoint?.classList.add("ct-case-chart__point--active");
  };
  if (latestMain) {
    showRecordDetail(latestMain, detailFor, sourceFor);
  } else {
    detail.textContent = "No documented value";
  }

  for (const record of records) {
    const value = valueFor(record);
    if (isNumber(value)) {
      const lowCoverage = lowCoverageFor?.(record) ?? false;
      const point = svgElement("circle", {
        class: `ct-case-chart__point ownership-fill--${record.ownership.toLowerCase()}${
          lowCoverage ? " ct-case-chart__point--low-coverage" : ""
        }`,
        cx: x(record.year),
        cy: y(value),
        r: 5.5,
        "data-year": record.year,
        tabindex: "0",
        role: "img",
        "aria-label": detailFor(record),
      });
      const pointTitle = svgElement("title");
      pointTitle.textContent = detailFor(record);
      point.appendChild(pointTitle);
      const showDetail = () => {
        showRecordDetail(record, detailFor, sourceFor);
      };
      point.addEventListener("pointerenter", showDetail);
      point.addEventListener("mouseover", showDetail);
      point.addEventListener("focus", showDetail);
      point.addEventListener("click", showDetail);
      svg.appendChild(point);
    }

    if (actualValueFor && isNumber(actualValueFor(record))) {
      const actualPoint = svgElement("circle", {
        class: "ct-case-chart__point ct-case-chart__point--actual",
        cx: x(record.year),
        cy: y(actualValueFor(record)),
        r: 3.8,
        tabindex: "0",
        role: "img",
        "aria-label": actualDetailFor(record),
      });
      const actualTitle = svgElement("title");
      actualTitle.textContent = actualDetailFor(record);
      actualPoint.appendChild(actualTitle);
      const showActualDetail = () => {
        showRecordDetail(record, actualDetailFor, actualSourceFor);
      };
      actualPoint.addEventListener("mouseenter", showActualDetail);
      actualPoint.addEventListener("focus", showActualDetail);
      actualPoint.addEventListener("click", showActualDetail);
      svg.appendChild(actualPoint);
    }
  }

  const availableRecords = records.filter((record) => isNumber(valueFor(record)));
  svg.addEventListener("pointermove", (event) => {
    const bounds = svg.getBoundingClientRect();
    const viewBoxX = ((event.clientX - bounds.left) / bounds.width) * width;
    const approximateYear =
      firstYear + ((viewBoxX - margin.left) / plotWidth) * (lastYear - firstYear);
    const nearestRecord = availableRecords.reduce((nearest, record) =>
      Math.abs(record.year - approximateYear) < Math.abs(nearest.year - approximateYear)
        ? record
        : nearest
    );
    showRecordDetail(nearestRecord, detailFor, sourceFor);
  });

  if (latestMain) showRecordDetail(latestMain, detailFor, sourceFor);

  block.append(svg, detail);
  return block;
}

function ctPriceDetail(record, customerClass) {
  const price = record[`${customerClass}_average_price_cents_kwh`];
  const coverage = record[`${customerClass}_bundled_customer_share_pct`];
  const coverageFlag = coverage < 50 ? " · minority coverage" : "";
  return `${record.year} · ${formatPrice(price)}\n${Number(coverage).toFixed(
    1
  )}% of ${customerClass} customers bundled${coverageFlag}`;
}

function ctAuthorizedRoeDetail(record) {
  const adjustment = isNumber(record.performance_adjustment_bps)
    ? ` · ${formatSignedBasisPoints(record.performance_adjustment_bps)} adjustment`
    : "";
  return `${record.year} · year-end effective ROE ${formatRoe(
    record.effective_authorized_roe
  )}\nBase ${formatRoe(record.base_authorized_roe)}${adjustment}`;
}

function ctActualRoeDetail(record) {
  return `${record.year} · actual earned ROE ${formatRoe(
    record.actual_earned_roe
  )}\nEffective authorized ${formatRoe(
    record.effective_authorized_roe
  )} · gap ${formatSignedBasisPoints(record.actual_minus_effective_bps)}`;
}

function ctOwnershipSummary(records) {
  const transitions = ownershipTransitions(records);
  if (!transitions.length) return `${records[0].ownership} throughout 2013–2024`;
  const transition = transitions[0];
  return `${transition.from} → ${transition.to} in ${transition.year}`;
}

function buildCtDualAxisChart(records, customerClass, priceMaximum) {
  const width = 520;
  const height = 205;
  const margin = { top: 22, right: 48, bottom: 26, left: 46 };
  const plotWidth = width - margin.left - margin.right;
  const plotHeight = height - margin.top - margin.bottom;
  const priceKey = `${customerClass}_average_price_cents_kwh`;
  const coverageKey = `${customerClass}_bundled_customer_share_pct`;
  const customerLabel = CUSTOMER_CLASS_LABELS[customerClass];
  const x = (year) => margin.left + ((year - 2013) / 11) * plotWidth;
  const priceY = (value) =>
    margin.top + plotHeight - (Number(value) / priceMaximum) * plotHeight;
  const roeY = (value) =>
    margin.top +
    plotHeight -
    ((Number(value) - CT_ROE_MINIMUM) / (CT_ROE_MAXIMUM - CT_ROE_MINIMUM)) *
      plotHeight;

  const block = createElement("div", "ct-dual-chart-block");
  const legend = createElement("div", "ct-dual-chart__legend");
  legend.append(
    createElement("span", "ct-dual-chart__legend-item ct-dual-chart__legend-item--price", "Price · left axis"),
    createElement("span", "ct-dual-chart__legend-item ct-dual-chart__legend-item--roe", "Year-end authorized ROE · right axis")
  );
  block.appendChild(legend);

  const svg = svgElement("svg", {
    class: "ct-dual-chart",
    viewBox: `0 0 ${width} ${height}`,
    role: "img",
    "aria-label": `${CT_CASE_STUDY_NAMES[records[0].utility_id_eia]} ${customerClass} full-year average price and year-end authorized return on equity, 2013 to 2024`,
  });

  const leftAxisTitle = svgElement("text", {
    class: "ct-dual-chart__axis-title ct-dual-chart__axis-title--price",
    x: margin.left,
    y: 11,
    "text-anchor": "start",
  });
  leftAxisTitle.textContent = `${customerLabel} price (¢/kWh)`;
  svg.appendChild(leftAxisTitle);
  const rightAxisTitle = svgElement("text", {
    class: "ct-dual-chart__axis-title ct-dual-chart__axis-title--roe",
    x: width - margin.right,
    y: 11,
    "text-anchor": "end",
  });
  rightAxisTitle.textContent = "Year-end ROE";
  svg.appendChild(rightAxisTitle);

  for (const tick of [0, priceMaximum / 2, priceMaximum]) {
    const tickY = priceY(tick);
    svg.appendChild(
      svgElement("line", {
        class: "ct-case-chart__gridline",
        x1: margin.left,
        x2: width - margin.right,
        y1: tickY,
        y2: tickY,
      })
    );
    const label = svgElement("text", {
      class: "ct-dual-chart__axis-label ct-dual-chart__axis-label--price",
      x: margin.left - 7,
      y: tickY + 4,
      "text-anchor": "end",
    });
    label.textContent = `${tick}¢`;
    svg.appendChild(label);
  }

  for (const tick of [0.08, 0.095, 0.11]) {
    const label = svgElement("text", {
      class: "ct-dual-chart__axis-label ct-dual-chart__axis-label--roe",
      x: width - margin.right + 7,
      y: roeY(tick) + 4,
      "text-anchor": "start",
    });
    label.textContent = `${(tick * 100).toFixed(1)}%`;
    svg.appendChild(label);
  }

  for (const year of [2013, 2016, 2020, 2024]) {
    const label = svgElement("text", {
      class: "ct-dual-chart__year-label",
      x: x(year),
      y: height - 6,
      "text-anchor": year === 2013 ? "start" : year === 2024 ? "end" : "middle",
    });
    label.textContent = year;
    svg.appendChild(label);
  }

  const pricePath = matchedStatePath(
    records,
    (record) => record[priceKey],
    x,
    priceY,
    false
  );
  if (pricePath) {
    svg.appendChild(
      svgElement("path", { class: "ct-dual-chart__line ct-dual-chart__line--price", d: pricePath })
    );
  }
  const roePath = matchedStatePath(
    records,
    (record) => record.effective_authorized_roe,
    x,
    roeY,
    true
  );
  if (roePath) {
    svg.appendChild(
      svgElement("path", { class: "ct-dual-chart__line ct-dual-chart__line--roe", d: roePath })
    );
  }

  const detail = createElement("div", "ct-dual-chart__detail");
  const appendSourceLink = (label, url, title) => {
    if (!url) return;
    const link = createElement("a", "ct-dual-chart__source-link", label);
    link.href = url;
    link.target = "_blank";
    link.rel = "noopener";
    if (title) link.title = title;
    detail.appendChild(link);
  };
  const showDetail = (record) => {
    const price = record[priceKey];
    const coverage = record[coverageKey];
    const adjustment = isNumber(record.performance_adjustment_bps)
      ? `; ${formatSignedBasisPoints(record.performance_adjustment_bps)} adjustment`
      : "";
    const coverageText = isNumber(coverage)
      ? `${Number(coverage).toFixed(1)}% bundled coverage${coverage < 50 ? " · below 50%" : ""}`
      : "bundled coverage not reported";
    detail.replaceChildren();
    detail.append(
      createElement(
        "span",
        "ct-dual-chart__detail-main",
        `${record.year} · Full-year price ${isNumber(price) ? formatPrice(price) : "not reported"} · Year-end ROE ${formatRoe(
          record.effective_authorized_roe
        )}`
      ),
      createElement(
        "span",
        "ct-dual-chart__detail-sub",
        `${coverageText} · ${record.ownership} that year${adjustment}`
      )
    );
    appendSourceLink(
      `Price source: ${record.price_source_report}`,
      record.price_source_url,
      record[`${customerClass}_price_source_table`]
    );
    appendSourceLink(
      `ROE source: ${record.roe_primary_source_title}`,
      record.roe_primary_source_url,
      record.roe_primary_source_location
    );
    for (const active of svg.querySelectorAll(".ct-dual-chart__point--active")) {
      active.classList.remove("ct-dual-chart__point--active");
    }
    for (const point of svg.querySelectorAll(`[data-year="${record.year}"]`)) {
      point.classList.add("ct-dual-chart__point--active");
    }
  };

  for (const record of records) {
    const price = record[priceKey];
    if (isNumber(price)) {
      const lowCoverage = record[coverageKey] < 50;
      const point = svgElement("circle", {
        class: `ct-dual-chart__point ct-dual-chart__point--price${
          lowCoverage ? " ct-dual-chart__point--low-coverage" : ""
        }`,
        cx: x(record.year),
        cy: priceY(price),
        r: 4.6,
        "data-year": record.year,
        tabindex: "0",
        role: "img",
        "aria-label": `${record.year} ${customerClass} price ${formatPrice(price)}`,
      });
      const update = () => showDetail(record);
      point.addEventListener("pointerenter", update);
      point.addEventListener("mouseover", update);
      point.addEventListener("focus", update);
      point.addEventListener("click", update);
      svg.appendChild(point);
    }
    if (isNumber(record.effective_authorized_roe)) {
      const size = 7.8;
      const point = svgElement("rect", {
        class: "ct-dual-chart__point ct-dual-chart__point--roe",
        x: x(record.year) - size / 2,
        y: roeY(record.effective_authorized_roe) - size / 2,
        width: size,
        height: size,
        rx: 1.4,
        "data-year": record.year,
        tabindex: "0",
        role: "img",
        "aria-label": `${record.year} year-end authorized ROE ${formatRoe(record.effective_authorized_roe)}`,
      });
      const update = () => showDetail(record);
      point.addEventListener("pointerenter", update);
      point.addEventListener("mouseover", update);
      point.addEventListener("focus", update);
      point.addEventListener("click", update);
      svg.appendChild(point);
    }
  }

  svg.addEventListener("pointermove", (event) => {
    const bounds = svg.getBoundingClientRect();
    const viewBoxX = ((event.clientX - bounds.left) / bounds.width) * width;
    const approximateYear = 2013 + ((viewBoxX - margin.left) / plotWidth) * 11;
    const nearest = records.reduce((best, record) =>
      Math.abs(record.year - approximateYear) < Math.abs(best.year - approximateYear)
        ? record
        : best
    );
    showDetail(nearest);
  });

  showDetail(records[records.length - 1]);
  block.append(svg, detail);
  return block;
}

function buildCtCaseStudyCard(records, customerClass, priceMaximum) {
  const utilityId = records[0].utility_id_eia;
  const latest = records[records.length - 1];
  const priceKey = `${customerClass}_average_price_cents_kwh`;
  const coverageKey = `${customerClass}_bundled_customer_share_pct`;
  const customerLabel = CUSTOMER_CLASS_LABELS[customerClass];
  const card = createElement(
    "article",
    `ct-case-study-card ct-case-study-card--${latest.ownership.toLowerCase()}`
  );
  const header = createElement("header", "ct-case-study-card__header");
  const titleBlock = createElement("div");
  titleBlock.append(
    createElement("h3", "ct-case-study-card__title", CT_CASE_STUDY_NAMES[utilityId]),
    createElement(
      "p",
      "ct-case-study-card__meta",
      `${records[0].state} · EIA ${utilityId} · ${ctOwnershipSummary(records)}`
    )
  );
  const latestSummary = createElement("p", "ct-case-study-card__latest");
  latestSummary.append(
    createElement("strong", "", formatPrice(latest[priceKey])),
    document.createTextNode(` ${customerClass} · year-end ROE ${formatRoe(latest.effective_authorized_roe)}`)
  );
  header.append(titleBlock, latestSummary);
  card.appendChild(header);

  card.appendChild(buildCtDualAxisChart(records, customerClass, priceMaximum));
  return card;
}

function matchedStatePath(records, valueFor, x, y, stepped) {
  const usable = records.filter((record) => isNumber(valueFor(record)));
  if (!usable.length) return "";
  const parts = [
    `M ${x(usable[0].year).toFixed(2)} ${y(valueFor(usable[0])).toFixed(2)}`,
  ];
  for (let index = 1; index < usable.length; index += 1) {
    const previous = usable[index - 1];
    const current = usable[index];
    if (current.year !== previous.year + 1) {
      parts.push(
        `M ${x(current.year).toFixed(2)} ${y(valueFor(current)).toFixed(2)}`
      );
    } else if (stepped) {
      parts.push(
        `L ${x(current.year).toFixed(2)} ${y(valueFor(previous)).toFixed(2)}`,
        `L ${x(current.year).toFixed(2)} ${y(valueFor(current)).toFixed(2)}`
      );
    } else {
      parts.push(
        `L ${x(current.year).toFixed(2)} ${y(valueFor(current)).toFixed(2)}`
      );
    }
  }
  return parts.join(" ");
}

function buildMatchedStateChart({
  series,
  title,
  ariaLabel,
  minimum,
  maximum,
  ticks,
  valueFor,
  formatAxis,
  detailFor,
  sourceFor,
  stepped = false,
  lowCoverageFor = null,
}) {
  const width = 520;
  const height = 178;
  const margin = { top: 10, right: 12, bottom: 25, left: 44 };
  const plotWidth = width - margin.left - margin.right;
  const plotHeight = height - margin.top - margin.bottom;
  const x = (year) => margin.left + ((year - 2013) / 11) * plotWidth;
  const y = (value) =>
    margin.top +
    plotHeight -
    ((Number(value) - minimum) / (maximum - minimum)) * plotHeight;

  const block = createElement("div", "ct-case-chart-block");
  block.appendChild(createElement("h4", "ct-case-chart-block__title", title));
  const svg = svgElement("svg", {
    class: "ct-case-chart ct-case-chart--matched",
    viewBox: `0 0 ${width} ${height}`,
    role: "img",
    "aria-label": ariaLabel,
  });

  for (const tick of ticks) {
    const tickY = y(tick);
    svg.appendChild(
      svgElement("line", {
        class: "ct-case-chart__gridline",
        x1: margin.left,
        x2: width - margin.right,
        y1: tickY,
        y2: tickY,
      })
    );
    const label = svgElement("text", {
      class: "ct-case-chart__axis-label",
      x: margin.left - 7,
      y: tickY + 4,
      "text-anchor": "end",
    });
    label.textContent = formatAxis(tick);
    svg.appendChild(label);
  }

  for (const year of [2013, 2016, 2020, 2024]) {
    const label = svgElement("text", {
      class: "ct-case-chart__axis-label",
      x: x(year),
      y: height - 6,
      "text-anchor": year === 2013 ? "start" : year === 2024 ? "end" : "middle",
    });
    label.textContent = year;
    svg.appendChild(label);
  }

  const detail = createElement("div", "ct-case-chart__detail");
  const showDetail = (item, record) => {
    detail.replaceChildren();
    detail.appendChild(
      createElement("span", "ct-case-chart__detail-text", detailFor(item, record))
    );
    const source = sourceFor(item, record);
    if (source?.url) {
      const link = createElement(
        "a",
        "ct-case-chart__source-link",
        `Source for ${record.year}: ${source.label}`
      );
      link.href = source.url;
      link.target = "_blank";
      link.rel = "noopener";
      if (source.location) link.title = source.location;
      detail.appendChild(link);
    }
    for (const active of svg.querySelectorAll(".ct-case-chart__point--active")) {
      active.classList.remove("ct-case-chart__point--active");
    }
    svg
      .querySelector(
        `.ct-case-chart__point[data-utility-id="${item.utilityId}"][data-year="${record.year}"]`
      )
      ?.classList.add("ct-case-chart__point--active");
  };

  for (const item of series) {
    const path = matchedStatePath(item.records, valueFor, x, y, stepped);
    if (path) {
      svg.appendChild(
        svgElement("path", {
          class: `ct-case-chart__line ct-case-chart__line--${item.ownership.toLowerCase()}`,
          d: path,
        })
      );
    }
    for (const record of item.records) {
      const value = valueFor(record);
      if (!isNumber(value)) continue;
      const lowCoverage = lowCoverageFor?.(record) ?? false;
      const point = svgElement("circle", {
        class: `ct-case-chart__point ct-case-chart__point--${item.ownership.toLowerCase()}${
          lowCoverage ? " ct-case-chart__point--low-coverage" : ""
        }`,
        cx: x(record.year),
        cy: y(value),
        r: 4.6,
        "data-utility-id": item.utilityId,
        "data-year": record.year,
        tabindex: "0",
        role: "img",
        "aria-label": detailFor(item, record),
      });
      const pointTitle = svgElement("title");
      pointTitle.textContent = detailFor(item, record);
      point.appendChild(pointTitle);
      const update = () => showDetail(item, record);
      point.addEventListener("pointerenter", update);
      point.addEventListener("mouseover", update);
      point.addEventListener("focus", update);
      point.addEventListener("click", update);
      svg.appendChild(point);
    }
  }

  const defaultItem = series[0];
  const defaultRecord = [...defaultItem.records]
    .reverse()
    .find((record) => isNumber(valueFor(record)));
  if (defaultRecord) showDetail(defaultItem, defaultRecord);
  else detail.textContent = "No documented value";

  block.append(svg, detail);
  return block;
}

function buildCtStateCard(pair, byUtility, customerClass, priceMaximum) {
  const priceKey = `${customerClass}_average_price_cents_kwh`;
  const coverageKey = `${customerClass}_bundled_customer_share_pct`;
  const customerLabel = CUSTOMER_CLASS_LABELS[customerClass];
  const series = [
    { utilityId: pair.domId, ownership: "DOM", records: byUtility.get(pair.domId) },
    { utilityId: pair.mtcId, ownership: "MTC", records: byUtility.get(pair.mtcId) },
  ].map((item) => ({
    ...item,
    name: CT_CASE_STUDY_NAMES[item.utilityId],
    shortName: ROE_SHORT_NAMES[item.utilityId],
    latest: item.records[item.records.length - 1],
  }));

  const card = createElement("article", "ct-case-study-card ct-case-study-card--state");
  const header = createElement("header", "ct-case-study-card__header");
  const titleBlock = createElement("div");
  titleBlock.append(
    createElement("h3", "ct-case-study-card__title", pair.state),
    createElement(
      "p",
      "ct-case-study-card__meta",
      `${pair.regulator} · matched by 2024 ownership`
    )
  );
  header.appendChild(titleBlock);
  card.appendChild(header);

  const legend = createElement("div", "ct-state-series", "");
  for (const item of series) {
    const legendItem = createElement(
      "div",
      `ct-state-series__item ct-state-series__item--${item.ownership.toLowerCase()}`
    );
    legendItem.append(
      createElement("i", "ct-state-series__line"),
      createElement("strong", "", item.shortName),
      createElement(
        "span",
        "",
        `${item.ownership} · ${formatPrice(item.latest[priceKey])} · ROE ${formatRoe(
          item.latest.effective_authorized_roe
        )}`
      )
    );
    legend.appendChild(legendItem);
  }
  card.appendChild(legend);

  const ownershipChange = series
    .map((item) => ({ item, summary: ctOwnershipSummary(item.records) }))
    .find(({ summary }) => summary.includes("→"));
  if (ownershipChange) {
    card.appendChild(
      createElement(
        "p",
        "ct-state-series__note",
        `${ownershipChange.item.shortName}: ${ownershipChange.summary}. The matched label uses 2024 ownership.`
      )
    );
  }

  card.appendChild(
    buildMatchedStateChart({
      series,
      title: `Published bundled ${customerLabel.toLowerCase()} price`,
      ariaLabel: `${pair.state} DOM and MTC bundled ${customerClass} prices, 2013 to 2024`,
      minimum: 0,
      maximum: priceMaximum,
      ticks: [0, priceMaximum / 2, priceMaximum],
      valueFor: (record) => record[priceKey],
      formatAxis: (value) => `${value}¢`,
      detailFor: (item, record) =>
        `${item.name} · ${item.ownership} series\n${ctPriceDetail(record, customerClass)}`,
      sourceFor: (_item, record) => ({
        url: record.price_source_url,
        label: record.price_source_report,
        location: "EIA annual source file",
      }),
      lowCoverageFor: (record) => record[coverageKey] < 50,
    })
  );
  card.appendChild(
    buildMatchedStateChart({
      series,
      title: "Authorized return on equity",
      ariaLabel: `${pair.state} DOM and MTC authorized return on equity, 2013 to 2024`,
      minimum: CT_ROE_MINIMUM,
      maximum: CT_ROE_MAXIMUM,
      ticks: [0.08, 0.095, 0.11],
      valueFor: (record) => record.effective_authorized_roe,
      formatAxis: (value) => `${(value * 100).toFixed(1)}%`,
      detailFor: (item, record) =>
        `${item.name} · ${record.ownership} in ${record.year}\n${ctAuthorizedRoeDetail(record)}`,
      sourceFor: (_item, record) => ({
        url: record.roe_primary_source_url,
        label: record.roe_primary_source_title,
        location: record.roe_primary_source_location,
      }),
      stepped: true,
    })
  );
  return card;
}

function ctCaseStudyFinding(records, customerClass) {
  const latest = records.filter((record) => record.year === 2024);
  const priceKey = `${customerClass}_average_price_cents_kwh`;
  const customerLabel = CUSTOMER_CLASS_LABELS[customerClass].toLowerCase();
  const pairs = [
    { state: "Connecticut", domId: 4176, mtcId: 19497, domName: "CL&P", mtcName: "UI" },
    { state: "Massachusetts", domId: 54913, mtcId: 11804, domName: "NSTAR", mtcName: "Massachusetts Electric" },
    { state: "New York", domId: 4226, mtcId: 13511, domName: "Con Edison", mtcName: "NYSEG" },
  ];
  const comparisons = pairs.map((pair) => {
    const dom = latest.find((record) => record.utility_id_eia === pair.domId);
    const mtc = latest.find((record) => record.utility_id_eia === pair.mtcId);
    const priceDifference = mtc[priceKey] - dom[priceKey];
    const roeDifference = (mtc.effective_authorized_roe - dom.effective_authorized_roe) * 100;
    return {
      ...pair,
      priceDifference,
      roeDifference,
      text: `${pair.state}: ${pair.mtcName} (MTC) was ${Math.abs(priceDifference).toFixed(
        2
      )}¢/kWh ${priceDifference >= 0 ? "higher" : "lower"} than ${pair.domName} (DOM), while its year-end authorized ROE was ${Math.abs(
        roeDifference
      ).toFixed(2)} percentage points ${roeDifference >= 0 ? "higher" : "lower"}.`,
    };
  });
  const lowerRoeStates = comparisons
    .filter((comparison) => comparison.roeDifference < 0)
    .map((comparison) => comparison.state);
  const higherPriceStates = comparisons
    .filter((comparison) => comparison.priceDifference > 0)
    .map((comparison) => comparison.state);
  const lowerPriceStates = comparisons
    .filter((comparison) => comparison.priceDifference < 0)
    .map((comparison) => comparison.state);
  const takeaway = lowerRoeStates.length === comparisons.length && higherPriceStates.length && lowerPriceStates.length
    ? `The MTC utility has the lower year-end ROE in all three states, but its ${customerLabel} price is higher in ${higherPriceStates.join(" and ")} and lower in ${lowerPriceStates.join(" and ")}. That does not fit a simple higher-ROE, higher-price story.`
    : `The three state comparisons do not show one consistent relationship between year-end authorized ROE and ${customerLabel} price.`;
  return `2024 matched-state snapshot. ${comparisons.map((comparison) => comparison.text).join(" ")} ${takeaway} Prices are full-year averages and ROE is measured at year-end. This is a useful check on a simple ROE explanation, but three pairs cannot establish causation.`;
}

function setupCtCaseStudy(records) {
  const status = document.getElementById("ct-case-study-status");
  const charts = document.getElementById("ct-case-study-charts");
  const finding = document.getElementById("ct-case-study-finding");
  const customerClassSelect = document.getElementById("ct-case-customer-class");
  if (!Array.isArray(records) || records.length !== 72) {
    status.hidden = false;
    status.textContent = "The matched-state rate-case data did not load.";
    return;
  }

  const byUtility = new Map();
  for (const utilityId of CT_CASE_STUDY_UTILITY_IDS) {
    const utilityRecords = records
      .filter((record) => record.utility_id_eia === utilityId)
      .sort((a, b) => a.year - b.year);
    if (utilityRecords.length !== 12) {
      status.hidden = false;
      status.textContent = "The matched-state rate-case data are missing annual rows.";
      return;
    }
    byUtility.set(utilityId, utilityRecords);
  }

  const render = () => {
    const customerClass = customerClassSelect.value;
    const priceKey = `${customerClass}_average_price_cents_kwh`;
    const prices = records.map((record) => record[priceKey]).filter(isNumber);
    const priceMaximum = niceMaximum(Math.max(...prices));
    charts.replaceChildren();
    for (const utilityId of CT_CASE_STUDY_UTILITY_IDS) {
      charts.appendChild(
        buildCtCaseStudyCard(byUtility.get(utilityId), customerClass, priceMaximum)
      );
    }
    finding.textContent = ctCaseStudyFinding(records, customerClass);
  };

  customerClassSelect.addEventListener("change", () => {
    const comparisonCustomerClass = document.getElementById(
      "comparison-customer-class"
    );
    if (comparisonCustomerClass.value !== customerClassSelect.value) {
      comparisonCustomerClass.value = customerClassSelect.value;
      comparisonCustomerClass.dispatchEvent(new Event("change"));
    }
    render();
  });
  render();
}

function mergePanelData(priceRecords, reliabilityRecords) {
  const reliabilityByKey = new Map();
  for (const record of reliabilityRecords) {
    const key = `${record.panel_id}:${record.year}`;
    if (reliabilityByKey.has(key)) {
      throw new Error(`Duplicate reliability row for ${key}`);
    }
    reliabilityByKey.set(key, record);
  }
  return priceRecords.map((record) => {
    const key = `${record.panel_id}:${record.year}`;
    const reliability = reliabilityByKey.get(key);
    if (!reliability) throw new Error(`Missing reliability audit row for ${key}`);
    return { ...record, reliability };
  });
}

function main() {
  const priceRecords = window.NE_NY_PRICE_PANEL;
  const ownershipSummaryRecords = window.NE_NY_OWNERSHIP_PRICE_SUMMARY;
  const reliabilityRecords = window.NE_NY_RELIABILITY_PANEL;
  const isoFuelMixRecords = window.NE_NY_ISO_FUEL_MIX;
  const ctRoeCaseStudyRecords = window.NE_NY_ROE_CASE_STUDY;
  const ownershipPriceModelResults =
    window.NE_NY_OWNERSHIP_PRICE_MODEL_RESULTS;
  const expandedPriceModelResults =
    window.NE_NY_EXPANDED_PRICE_MODEL_RESULTS;
  const ownershipReliabilityModelResults =
    window.NE_NY_OWNERSHIP_RELIABILITY_MODEL_RESULTS;
  setupCtCaseStudy(ctRoeCaseStudyRecords);
  setupIsoFuelMix(isoFuelMixRecords);
  const status = document.getElementById("matrix-status");
  if (!Array.isArray(priceRecords) || priceRecords.length !== EXPECTED_PANEL_ROWS) {
    status.hidden = false;
    status.textContent = "The utility price panel data did not load.";
    return;
  }
  if (!Array.isArray(reliabilityRecords) || reliabilityRecords.length !== EXPECTED_PANEL_ROWS) {
    status.hidden = false;
    status.textContent = "The utility reliability panel data did not load.";
    return;
  }
  let records;
  try {
    records = mergePanelData(priceRecords, reliabilityRecords);
  } catch (error) {
    status.hidden = false;
    status.textContent = "The price and reliability panel rows could not be matched.";
    return;
  }
  setupOwnershipComparison(ownershipSummaryRecords, records);
  setupOwnershipPriceModel(
    ownershipPriceModelResults,
    expandedPriceModelResults,
    ownershipReliabilityModelResults
  );
  const metricSelect = document.getElementById("panel-metric");
  const customerClassControl = document.getElementById("customer-class-control");
  const customerClassSelect = document.getElementById("customer-class");
  const scopeControl = document.getElementById("reliability-scope-control");
  const scopeSelect = document.getElementById("reliability-scope");
  const description = document.getElementById("metric-description");
  const finding = document.getElementById("metric-finding");

  const render = () => {
    const baseMetric = METRICS[metricSelect.value];
    const metric = resolveMetric(
      baseMetric,
      records,
      scopeSelect.value,
      customerClassSelect.value
    );
    customerClassControl.hidden = metric.kind === "reliability";
    scopeControl.hidden = metric.kind !== "reliability";
    description.textContent = metric.description;
    renderMatrix(records, metric);
    finding.textContent = metricFinding(records, metric);
  };
  metricSelect.addEventListener("change", render);
  customerClassSelect.addEventListener("change", () => {
    const comparisonCustomerClass = document.getElementById(
      "comparison-customer-class"
    );
    if (comparisonCustomerClass.value !== customerClassSelect.value) {
      comparisonCustomerClass.value = customerClassSelect.value;
      comparisonCustomerClass.dispatchEvent(new Event("change"));
    }
    render();
  });
  scopeSelect.addEventListener("change", render);
  render();
}

main();
