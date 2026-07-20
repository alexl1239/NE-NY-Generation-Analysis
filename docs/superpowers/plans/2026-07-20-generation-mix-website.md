# Generation Mix Website Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a static website showing generation-source-mix trends (2020–2024)
for 4 NE/NY utilities, sourced from PUDL, deployed via GitHub Pages.

**Architecture:** A standalone Python script (`build_data.py`) queries PUDL's
EIA-923 parquet file via DuckDB and writes a precomputed JSON file. A static
HTML/CSS/JS site (no framework, no build step) reads that JSON and renders one
100%-stacked-bar chart per utility with Chart.js. A GitHub Actions workflow deploys
the site's folder to GitHub Pages on every push to `main`.

**Tech Stack:** Python 3 (duckdb, pandas), stdlib `unittest`, plain HTML/CSS/JS,
Chart.js (via CDN), GitHub Actions (`actions/upload-pages-artifact`,
`actions/deploy-pages`).

## Global Constraints

- Utilities are fixed by exact `utility_id_eia`, not name-pattern matching:
  NYSEG = `13511`, Eversource = `54913` (PUDL name: "NSTAR Electric Company"),
  Con Edison = `4226`, United Illuminating = `19497`.
- Years: 2020–2024 inclusive.
- PUDL source file:
  `https://s3.us-west-2.amazonaws.com/pudl.catalyst.coop/stable/out_eia923__yearly_generation_fuel_combined.parquet`
- No parent-company consolidation, no joint-ownership allocation — raw as-reported
  generation per utility ID only. The NSTAR→Eversource label is a rename of the
  same legal entity, not a rollup.
- Exclude non-positive `net_generation_mwh` rows before computing each fuel's
  share of a utility's yearly total (matches the original diagnostic notebook's
  treatment).
- No JS framework, no npm/build step for the site.
- Chart colors (dataviz skill's validated categorical palette, slots 1–5, fixed
  order, never cycled):

  | Fuel | Light | Dark |
  |---|---|---|
  | Gas | `#2a78d6` | `#3987e5` |
  | Hydro | `#008300` | `#008300` |
  | Oil | `#e87ba4` | `#d55181` |
  | Other | `#eda100` | `#c98500` |
  | Solar | `#1baf7a` | `#199e70` |

- Chart chrome tokens (light / dark): surface `#fcfcfb` / `#1a1a19`, page
  `#f9f9f7` / `#0d0d0d`, primary ink `#0b0b0b` / `#ffffff`, secondary ink
  `#52514e` / `#c3c2b7`, muted ink `#898781` (both), gridline `#e1e0d9` / `#2c2c2a`,
  border `rgba(11,11,11,0.10)` / `rgba(255,255,255,0.10)`.

---

## Task 1: Data pipeline core logic (`build_records`)

**Files:**
- Create: `build_data.py`
- Create: `tests/test_build_data.py`

**Interfaces:**
- Produces: `build_records(df: pandas.DataFrame) -> list[dict]` where `df` has
  columns `utility_id_eia` (int), `year` (int), `fuel` (str), `mwh` (float).
  Returns a list of dicts with keys `utility` (str), `year` (int), `fuel` (str,
  title-cased), `mwh` (float), `share_pct` (float), one per (utility, year, fuel)
  with positive `mwh`.
- Produces: `UTILITIES: dict[int, str]` mapping `utility_id_eia` → display name.
- Produces: `PUDL_FILE: str`, `YEAR_START: int`, `YEAR_END: int` module constants.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_build_data.py`:

```python
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from build_data import build_records


class TestBuildRecords(unittest.TestCase):
    def test_computes_share_pct_per_utility_year(self):
        df = pd.DataFrame(
            [
                {"utility_id_eia": 13511, "year": 2020, "fuel": "hydro", "mwh": 75.0},
                {"utility_id_eia": 13511, "year": 2020, "fuel": "oil", "mwh": 25.0},
            ]
        )
        records = build_records(df)
        by_fuel = {r["fuel"]: r for r in records}
        self.assertAlmostEqual(by_fuel["Hydro"]["share_pct"], 75.0)
        self.assertAlmostEqual(by_fuel["Oil"]["share_pct"], 25.0)
        self.assertEqual(by_fuel["Hydro"]["utility"], "NYSEG")
        self.assertEqual(by_fuel["Hydro"]["year"], 2020)

    def test_excludes_non_positive_generation_from_share_calc(self):
        df = pd.DataFrame(
            [
                {"utility_id_eia": 4226, "year": 2022, "fuel": "gas", "mwh": 100.0},
                {"utility_id_eia": 4226, "year": 2022, "fuel": "other", "mwh": -5.0},
            ]
        )
        records = build_records(df)
        fuels = {r["fuel"] for r in records}
        self.assertEqual(fuels, {"Gas"})
        self.assertAlmostEqual(records[0]["share_pct"], 100.0)

    def test_titlecases_and_replaces_underscores_in_fuel_names(self):
        df = pd.DataFrame(
            [{"utility_id_eia": 19497, "year": 2021, "fuel": "waste_heat", "mwh": 10.0}]
        )
        records = build_records(df)
        self.assertEqual(records[0]["fuel"], "Waste Heat")

    def test_maps_nstar_id_to_eversource_label(self):
        df = pd.DataFrame(
            [{"utility_id_eia": 54913, "year": 2023, "fuel": "solar", "mwh": 5.0}]
        )
        records = build_records(df)
        self.assertEqual(records[0]["utility"], "Eversource")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 tests/test_build_data.py -v`
Expected: `ModuleNotFoundError: No module named 'build_data'` (file doesn't exist yet).

- [ ] **Step 3: Implement `build_data.py`**

Create `build_data.py`:

```python
"""Build site/data/generation_mix.json from PUDL's EIA-923 yearly
generation-fuel table.

Run: python3 build_data.py
"""
import json
from pathlib import Path

import duckdb
import pandas as pd

PUDL_FILE = (
    "https://s3.us-west-2.amazonaws.com/"
    "pudl.catalyst.coop/stable/"
    "out_eia923__yearly_generation_fuel_combined.parquet"
)

YEAR_START = 2020
YEAR_END = 2024

# utility_id_eia -> display name. 54913 is recorded in PUDL as "NSTAR Electric
# Company" -- the same legal entity as Eversource under an older name, not a
# parent-company rollup.
UTILITIES = {
    13511: "NYSEG",
    54913: "Eversource",
    4226: "Con Edison",
    19497: "United Illuminating",
}

OUTPUT_PATH = Path(__file__).parent / "site" / "data" / "generation_mix.json"


def fetch_generation(con):
    utility_ids = ", ".join(str(uid) for uid in UTILITIES)
    query = f"""
        SELECT
            CAST(EXTRACT(YEAR FROM report_date) AS INTEGER) AS year,
            utility_id_eia,
            COALESCE(fuel_type_code_pudl, energy_source_code, 'unknown') AS fuel,
            SUM(net_generation_mwh) AS mwh
        FROM read_parquet('{PUDL_FILE}')
        WHERE EXTRACT(YEAR FROM report_date) BETWEEN {YEAR_START} AND {YEAR_END}
          AND utility_id_eia IN ({utility_ids})
        GROUP BY 1, 2, 3
    """
    return con.execute(query).df()


def build_records(df):
    df = df.copy()
    df["utility"] = df["utility_id_eia"].map(UTILITIES)
    df["fuel"] = df["fuel"].astype(str).str.replace("_", " ", regex=False).str.title()

    positive = df[df["mwh"] > 0].copy()
    positive["total_mwh"] = positive.groupby(["year", "utility"])["mwh"].transform("sum")
    positive["share_pct"] = 100 * positive["mwh"] / positive["total_mwh"]

    records = positive[["utility", "year", "fuel", "mwh", "share_pct"]].sort_values(
        ["utility", "year", "fuel"]
    )
    return records.to_dict(orient="records")


def main():
    con = duckdb.connect()
    try:
        con.execute("LOAD httpfs")
    except duckdb.Error:
        con.execute("INSTALL httpfs")
        con.execute("LOAD httpfs")

    df = fetch_generation(con)
    if df.empty:
        raise ValueError("No generation records returned for the target utilities/years.")

    records = build_records(df)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w") as f:
        json.dump(records, f, indent=2)

    print(f"Wrote {len(records)} records to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 tests/test_build_data.py -v`
Expected: 4 tests, all `ok`, final line `OK`.

- [ ] **Step 5: Commit**

```bash
git add build_data.py tests/test_build_data.py
git commit -m "Add generation mix data pipeline with unit tests"
```

---

## Task 2: Generate and commit the dataset

**Files:**
- Create: `site/data/generation_mix.json` (generated by running `build_data.py`)

**Interfaces:**
- Consumes: `main()` from `build_data.py` (Task 1).
- Produces: `site/data/generation_mix.json` — a JSON array of records
  `{"utility": str, "year": int, "fuel": str, "mwh": float, "share_pct": float}`,
  consumed by `site/app.js` in Task 3.

- [ ] **Step 1: Run the pipeline against real PUDL data**

Run: `python3 build_data.py`
Expected: Output ending in `Wrote N records to .../site/data/generation_mix.json`
(this will take a little while — it's pulling from a remote parquet file over
DuckDB's httpfs). If duckdb or pandas aren't installed: `pip3 install duckdb pandas`
first.

- [ ] **Step 2: Validate the generated data**

Run:

```bash
python3 - <<'EOF'
import json
from collections import defaultdict

with open("site/data/generation_mix.json") as f:
    records = json.load(f)

utilities = {r["utility"] for r in records}
years = {r["year"] for r in records}
assert utilities == {"NYSEG", "Eversource", "Con Edison", "United Illuminating"}, utilities
assert years == {2020, 2021, 2022, 2023, 2024}, years

totals = defaultdict(float)
for r in records:
    totals[(r["utility"], r["year"])] += r["share_pct"]

for key, total in totals.items():
    assert abs(total - 100.0) < 0.01, f"{key}: {total}"

print(f"OK: {len(records)} records, {len(utilities)} utilities, {len(years)} years, all shares sum to 100%")
EOF
```

Expected: `OK: N records, 4 utilities, 5 years, all shares sum to 100%` with no
`AssertionError`.

- [ ] **Step 3: Commit**

```bash
git add site/data/generation_mix.json
git commit -m "Generate 2020-2024 generation mix dataset"
```

---

## Task 3: Build the static site

**Files:**
- Create: `site/index.html`
- Create: `site/styles.css`
- Create: `site/app.js`

**Interfaces:**
- Consumes: `site/data/generation_mix.json` (Task 2) — fetched at runtime via
  `fetch("data/generation_mix.json")`.
- Consumes: CSS custom properties defined in `styles.css`
  (`--fuel-gas`, `--fuel-hydro`, `--fuel-oil`, `--fuel-other`, `--fuel-solar`,
  `--surface`, `--gridline`, `--ink-secondary`) — read by `app.js` via
  `getComputedStyle`.

- [ ] **Step 1: Create `site/index.html`**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>NE/NY Utility Generation Mix, 2020–2024</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <header class="page-header">
    <h1>Generation Source Mix: NE &amp; NY Utilities, 2020–2024</h1>
    <p class="subtitle">
      Net generation reported directly under each utility's own name in
      PUDL's EIA-923 yearly generation-fuel table, 2020–2024.
    </p>
  </header>

  <main>
    <section class="charts" aria-label="Per-utility generation mix charts">
      <div class="chart-card">
        <h2>NYSEG</h2>
        <div class="chart-wrap"><canvas id="chart-nyseg"></canvas></div>
      </div>
      <div class="chart-card">
        <h2>Eversource</h2>
        <div class="chart-wrap"><canvas id="chart-eversource"></canvas></div>
      </div>
      <div class="chart-card">
        <h2>Con Edison</h2>
        <div class="chart-wrap"><canvas id="chart-conedison"></canvas></div>
      </div>
      <div class="chart-card">
        <h2>United Illuminating</h2>
        <div class="chart-wrap"><canvas id="chart-unitedilluminating"></canvas></div>
      </div>
    </section>

    <section class="methodology">
      <h2>Methodology &amp; caveats</h2>
      <ul>
        <li><strong>Data source:</strong> PUDL's <code>out_eia923__yearly_generation_fuel_combined</code> table (EIA Form 923), queried via DuckDB.</li>
        <li><strong>Years:</strong> 2020–2024.</li>
        <li><strong>Utilities:</strong> filtered by exact EIA utility ID, not name matching, to avoid mixing in unrelated same-named subsidiaries (e.g. Con Edison's merchant generation arm).</li>
        <li><strong>Eversource:</strong> PUDL records this utility's generation under its older name, "NSTAR Electric Company" — the same legal entity, renamed here for continuity.</li>
        <li><strong>Limitation:</strong> this shows generation reported directly under each utility's own name only. It does not allocate joint-ownership plants or roll up parent/subsidiary companies, so it is not the full generation mix delivered to retail customers — several of these utilities own little direct generation today and buy most of their power on the wholesale market.</li>
      </ul>
    </section>
  </main>

  <footer class="page-footer">
    <p><a href="https://github.com/alexl1239/NE-NY-Generation-Analysis" target="_blank" rel="noopener">View source on GitHub</a></p>
  </footer>

  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script>
  <script src="app.js"></script>
</body>
</html>
```

- [ ] **Step 2: Create `site/styles.css`**

```css
:root {
  color-scheme: light;
  --surface: #fcfcfb;
  --page: #f9f9f7;
  --ink-primary: #0b0b0b;
  --ink-secondary: #52514e;
  --ink-muted: #898781;
  --gridline: #e1e0d9;
  --border: rgba(11, 11, 11, 0.10);

  --fuel-gas: #2a78d6;
  --fuel-hydro: #008300;
  --fuel-oil: #e87ba4;
  --fuel-other: #eda100;
  --fuel-solar: #1baf7a;
}

@media (prefers-color-scheme: dark) {
  :root {
    color-scheme: dark;
    --surface: #1a1a19;
    --page: #0d0d0d;
    --ink-primary: #ffffff;
    --ink-secondary: #c3c2b7;
    --ink-muted: #898781;
    --gridline: #2c2c2a;
    --border: rgba(255, 255, 255, 0.10);

    --fuel-gas: #3987e5;
    --fuel-hydro: #008300;
    --fuel-oil: #d55181;
    --fuel-other: #c98500;
    --fuel-solar: #199e70;
  }
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
  background: var(--page);
  color: var(--ink-primary);
}

.page-header {
  padding: 2.5rem 1.5rem 1.5rem;
  max-width: 960px;
  margin: 0 auto;
}

.page-header h1 {
  margin: 0 0 0.5rem;
  font-size: 1.75rem;
}

.subtitle {
  color: var(--ink-secondary);
  margin: 0;
  max-width: 640px;
}

main {
  max-width: 960px;
  margin: 0 auto;
  padding: 0 1.5rem 3rem;
}

.charts {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(380px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2.5rem;
}

.chart-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 1rem 1.25rem 1.5rem;
}

.chart-card h2 {
  margin: 0 0 0.75rem;
  font-size: 1.1rem;
  color: var(--ink-primary);
}

.chart-wrap {
  position: relative;
  height: 280px;
}

.methodology {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 1.5rem;
}

.methodology h2 {
  margin-top: 0;
  font-size: 1.1rem;
}

.methodology ul {
  color: var(--ink-secondary);
  line-height: 1.6;
  padding-left: 1.25rem;
}

.methodology code {
  background: var(--gridline);
  padding: 0.1rem 0.3rem;
  border-radius: 4px;
  font-size: 0.9em;
}

.page-footer {
  text-align: center;
  padding: 1.5rem;
  color: var(--ink-muted);
}

.page-footer a {
  color: var(--ink-secondary);
}
```

- [ ] **Step 3: Create `site/app.js`**

```js
const FUEL_ORDER = ["Gas", "Hydro", "Oil", "Other", "Solar"];

const FUEL_COLOR_VARS = {
  Gas: "--fuel-gas",
  Hydro: "--fuel-hydro",
  Oil: "--fuel-oil",
  Other: "--fuel-other",
  Solar: "--fuel-solar",
};

const UTILITY_CHARTS = [
  { utility: "NYSEG", canvasId: "chart-nyseg" },
  { utility: "Eversource", canvasId: "chart-eversource" },
  { utility: "Con Edison", canvasId: "chart-conedison" },
  { utility: "United Illuminating", canvasId: "chart-unitedilluminating" },
];

function cssVar(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

function groupByUtility(records) {
  const grouped = new Map();
  for (const record of records) {
    if (!grouped.has(record.utility)) grouped.set(record.utility, []);
    grouped.get(record.utility).push(record);
  }
  return grouped;
}

function buildDatasets(records, years) {
  const surfaceColor = cssVar("--surface");
  return FUEL_ORDER.map((fuel) => {
    const byYear = new Map(
      records.filter((r) => r.fuel === fuel).map((r) => [r.year, r.share_pct])
    );
    return {
      label: fuel,
      data: years.map((year) => byYear.get(year) ?? 0),
      backgroundColor: cssVar(FUEL_COLOR_VARS[fuel]),
      borderColor: surfaceColor,
      borderWidth: 2,
      borderRadius: 4,
      borderSkipped: false,
    };
  });
}

function renderChart(canvasId, records, years) {
  const canvas = document.getElementById(canvasId);
  const ctx = canvas.getContext("2d");
  const gridline = cssVar("--gridline");
  const inkSecondary = cssVar("--ink-secondary");

  return new Chart(ctx, {
    type: "bar",
    data: {
      labels: years,
      datasets: buildDatasets(records, years),
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
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
            label: (context) => `${context.dataset.label}: ${context.parsed.y.toFixed(1)}%`,
          },
        },
      },
    },
  });
}

async function main() {
  const response = await fetch("data/generation_mix.json");
  const records = await response.json();
  const years = [...new Set(records.map((r) => r.year))].sort();
  const grouped = groupByUtility(records);

  for (const { utility, canvasId } of UTILITY_CHARTS) {
    renderChart(canvasId, grouped.get(utility) ?? [], years);
  }
}

main();
```

- [ ] **Step 4: Serve the site locally and verify it loads without errors**

Run: `python3 -m http.server 8000 --directory site` (leave running)
In another terminal: `curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/index.html`
Expected: `200`

- [ ] **Step 5: Visually verify the charts render correctly**

Use the `run` skill (or open `http://localhost:8000` in a browser directly) to
confirm: all 4 charts render as 100%-stacked bar charts with 5 years on the
x-axis, a legend with 5 fuels at the bottom, no browser console errors, and
values roughly matching the JSON (e.g. Eversource should show ~100% solar across
all years, per the raw data pulled during planning). Stop the local server
afterward (`Ctrl+C` in its terminal, or kill the background process).

- [ ] **Step 6: Commit**

```bash
git add site/index.html site/styles.css site/app.js
git commit -m "Add static site with per-utility generation mix charts"
```

---

## Task 4: Deploy to GitHub Pages

**Files:**
- Create: `.github/workflows/deploy-pages.yml`

**Interfaces:**
- Consumes: the `site/` directory (Tasks 2–3) as the Pages artifact root.

- [ ] **Step 1: Create the deploy workflow**

Create `.github/workflows/deploy-pages.yml`:

```yaml
name: Deploy site to GitHub Pages

on:
  push:
    branches: ["main"]
    paths:
      - "site/**"
      - ".github/workflows/deploy-pages.yml"
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      - name: Upload site artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: site
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/deploy-pages.yml
git commit -m "Add GitHub Pages deploy workflow"
```

- [ ] **Step 3: Push to GitHub**

Run: `git push origin main`
(Confirm with the user before pushing, per repo conventions — this makes the
workflow file live and, combined with Step 4 below, triggers a public deploy.)

- [ ] **Step 4: Enable GitHub Pages (manual, one-time, user-confirmed)**

In the GitHub repo → Settings → Pages → "Build and deployment" → Source: select
"GitHub Actions". If the repo is private, confirm the account plan supports
private-repo Pages, or make the repo public — check with the user before changing
repo visibility.

- [ ] **Step 5: Verify the deployed site**

After the Actions run completes (check the repo's Actions tab), fetch the Pages
URL shown in Settings → Pages (format:
`https://<username>.github.io/<repo-name>/`) and confirm it returns the page
with working charts.
