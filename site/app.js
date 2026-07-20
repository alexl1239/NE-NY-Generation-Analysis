const UTILITY_FUEL_ORDER = ["Gas", "Hydro", "Oil", "Other", "Solar"];
const UTILITY_FUEL_COLOR_VARS = {
  Gas: "--fuel-gas",
  Hydro: "--fuel-hydro",
  Oil: "--fuel-oil",
  Other: "--fuel-other",
  Solar: "--fuel-solar",
};

const REGIONAL_FUEL_ORDER = [
  "Coal",
  "Gas",
  "Hydro",
  "Nuclear",
  "Oil",
  "Solar",
  "Waste",
  "Wind",
];
const REGIONAL_FUEL_COLOR_VARS = {
  Coal: "--grid-coal",
  Gas: "--grid-gas",
  Hydro: "--grid-hydro",
  Nuclear: "--grid-nuclear",
  Oil: "--grid-oil",
  Solar: "--grid-solar",
  Waste: "--grid-waste",
  Wind: "--grid-wind",
};

const UTILITY_CHARTS = [
  { key: "NYSEG", canvasId: "chart-nyseg" },
  { key: "NSTAR Electric", canvasId: "chart-eversource" },
  { key: "Con Edison", canvasId: "chart-conedison" },
  { key: "United Illuminating", canvasId: "chart-unitedilluminating" },
];

const REGIONAL_CHARTS = [
  { key: "NYISO", canvasId: "chart-nyiso" },
  { key: "ISO-NE", canvasId: "chart-isone" },
];

const RESIDENTIAL_RATE_UTILITIES = [
  { key: "NYSEG", colorVar: "--rate-nyseg" },
  { key: "NSTAR Electric", colorVar: "--rate-nstar" },
  { key: "Con Edison", colorVar: "--rate-conedison" },
  { key: "United Illuminating", colorVar: "--rate-unitedilluminating" },
];

const totalLabelsPlugin = {
  id: "totalLabels",
  afterDatasetsDraw(chart) {
    const opts = chart.options.plugins?.totalLabels;
    if (!opts?.totals) return;
    const { ctx } = chart;
    const meta = chart.getDatasetMeta(0);
    const yTop = chart.scales.y.getPixelForValue(100);
    ctx.save();
    ctx.font = "11px system-ui, -apple-system, sans-serif";
    ctx.fillStyle = opts.color;
    ctx.textAlign = "center";
    ctx.textBaseline = "bottom";
    meta.data.forEach((bar, index) => {
      const label = opts.totals[index];
      if (!label) return;
      ctx.fillText(label, bar.x, yTop - 4);
    });
    ctx.restore();
  },
};
Chart.register(totalLabelsPlugin);

function cssVar(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

function groupBy(records, groupKey) {
  const grouped = new Map();
  for (const record of records) {
    if (!grouped.has(record[groupKey])) grouped.set(record[groupKey], []);
    grouped.get(record[groupKey]).push(record);
  }
  return grouped;
}

function formatMwh(value) {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(0)}K`;
  return value.toFixed(0);
}

function totalsByYear(records, years) {
  const totalByYear = new Map(records.map((r) => [r.year, r.total_mwh]));
  return years.map((year) => totalByYear.get(year) ?? 0);
}

function buildDatasets(records, years, fuelOrder, colorVars) {
  const surfaceColor = cssVar("--surface");
  return fuelOrder.map((fuel) => {
    const rowsByYear = new Map(records.filter((r) => r.fuel === fuel).map((r) => [r.year, r]));
    return {
      label: fuel,
      data: years.map((year) => rowsByYear.get(year)?.share_pct ?? 0),
      mwhByYear: years.map((year) => rowsByYear.get(year)?.mwh ?? 0),
      backgroundColor: cssVar(colorVars[fuel]),
      borderColor: surfaceColor,
      borderWidth: { top: 1, right: 0, bottom: 0, left: 0 },
    };
  });
}

function renderChart(canvasId, records, years, fuelOrder, colorVars) {
  const canvas = document.getElementById(canvasId);
  const ctx = canvas.getContext("2d");
  const gridline = cssVar("--gridline");
  const inkSecondary = cssVar("--ink-secondary");
  const totals = totalsByYear(records, years).map((mwh) => formatMwh(mwh));

  return new Chart(ctx, {
    type: "bar",
    data: {
      labels: years,
      datasets: buildDatasets(records, years, fuelOrder, colorVars),
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      layout: { padding: { top: 20 } },
      scales: {
        x: {
          stacked: true,
          grid: { display: false },
          ticks: { color: inkSecondary },
        },
        y: {
          stacked: true,
          min: 0,
          max: 100,
          grid: { color: gridline },
          ticks: {
            color: inkSecondary,
            callback: (value) => `${value}%`,
          },
        },
      },
      plugins: {
        legend: {
          position: "bottom",
          labels: { color: inkSecondary, boxWidth: 12 },
        },
        tooltip: {
          callbacks: {
            label: (context) => {
              const mwh = context.dataset.mwhByYear[context.dataIndex];
              return `${context.dataset.label}: ${context.parsed.y.toFixed(1)}% (${formatMwh(mwh)} MWh)`;
            },
          },
        },
        totalLabels: { totals, color: inkSecondary },
      },
    },
  });
}

function renderUtilityLineChart(canvasId, records, valueKey, yLabel, tickFormat, tooltipFormat) {
  const canvas = document.getElementById(canvasId);
  const ctx = canvas.getContext("2d");
  const gridline = cssVar("--gridline");
  const inkSecondary = cssVar("--ink-secondary");
  const years = [...new Set(records.map((r) => r.year))].sort();
  const grouped = groupBy(records, "utility");

  const datasets = RESIDENTIAL_RATE_UTILITIES.map(({ key, colorVar }) => {
    const rowsByYear = new Map((grouped.get(key) ?? []).map((r) => [r.year, r]));
    const color = cssVar(colorVar);
    return {
      label: key,
      data: years.map((year) => rowsByYear.get(year)?.[valueKey] ?? null),
      borderColor: color,
      backgroundColor: color,
      pointRadius: 4,
      pointHoverRadius: 6,
      borderWidth: 2,
      tension: 0,
      spanGaps: true,
    };
  });

  return new Chart(ctx, {
    type: "line",
    data: { labels: years, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: inkSecondary },
        },
        y: {
          beginAtZero: true,
          grid: { color: gridline },
          ticks: {
            color: inkSecondary,
            callback: tickFormat,
          },
          title: { display: true, text: yLabel, color: inkSecondary },
        },
      },
      plugins: {
        legend: {
          position: "bottom",
          labels: { color: inkSecondary, boxWidth: 12 },
        },
        tooltip: {
          callbacks: {
            label: (context) => tooltipFormat(context.dataset.label, context.parsed.y),
          },
        },
      },
    },
  });
}

function renderResidentialRateChart(canvasId, records) {
  return renderUtilityLineChart(
    canvasId,
    records,
    "cents_per_kwh",
    "cents / kWh",
    (value) => `${value}¢`,
    (label, value) => `${label}: ${value.toFixed(1)}¢/kWh`
  );
}

function renderBaseRateChart(canvasId, records) {
  return renderUtilityLineChart(
    canvasId,
    records,
    "modeled_base_delivery_bill_usd",
    "modeled bill @ 700 kWh ($/month)",
    (value) => `$${value}`,
    (label, value) => `${label}: $${value.toFixed(2)}/month`
  );
}

function renderSection(records, chartConfigs, groupKey, fuelOrder, colorVars) {
  const years = [...new Set(records.map((r) => r.year))].sort();
  const grouped = groupBy(records, groupKey);

  for (const { key, canvasId } of chartConfigs) {
    renderChart(canvasId, grouped.get(key) ?? [], years, fuelOrder, colorVars);
  }
}

async function main() {
  const [generationResponse, regionalResponse, ratesResponse, baseRatesResponse] = await Promise.all([
    fetch("data/generation_mix.json"),
    fetch("data/regional_grid_mix.json"),
    fetch("data/residential_rates.json"),
    fetch("data/base_rates.json"),
  ]);
  const generationRecords = await generationResponse.json();
  const regionalRecords = await regionalResponse.json();
  const rateRecords = await ratesResponse.json();
  const baseRateRecords = await baseRatesResponse.json();

  renderSection(generationRecords, UTILITY_CHARTS, "utility", UTILITY_FUEL_ORDER, UTILITY_FUEL_COLOR_VARS);
  renderSection(regionalRecords, REGIONAL_CHARTS, "region", REGIONAL_FUEL_ORDER, REGIONAL_FUEL_COLOR_VARS);
  renderResidentialRateChart("chart-residential-rate", rateRecords);
  renderBaseRateChart("chart-base-rate", baseRateRecords);
}

main();
