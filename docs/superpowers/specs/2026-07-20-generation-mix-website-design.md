# Generation Mix Website — Design Spec

**Date:** 2026-07-20
**Status:** Approved

## Purpose

Build a static website presenting the generation source mix (by fuel type) for four
New England / New York utility companies over the past 5 years, for a data science
professor to review. Findings need to be presented clearly with charts — this replaces
the ad-hoc exploratory notebook (`Generation_Mix_Name_Check.ipynb`) as the actual
deliverable. The notebook is left in the repo untouched as historical scratch work and
is not part of the final product.

## Scope

- **Utilities (4, fixed set):**
  - New York State Electric & Gas (NYSEG)
  - Eversource (NSTAR Electric renamed to Eversource — same legal entity, historic name)
  - Consolidated Edison (Con Edison)
  - United Illuminating
- **Years:** 2020–2024 (5 years). PUDL EIA-923 data is expected to have 2020 available;
  2025 is not yet published.
- **Metric:** net generation (MWh) by fuel type, and each fuel's share (%) of that
  utility's total generation per year.
- **Data treatment:** raw, as-reported generation per utility name. No parent-company
  roll-ups and no joint-ownership allocation, **except** merging NSTAR Electric into
  Eversource (a pure rename, not a parent-company consolidation). This limitation is
  disclosed explicitly on the site rather than corrected.
- **Story angle:** per-utility fuel-mix trend over time (not a cross-utility
  side-by-side comparison). One chart per utility.

## Non-goals

- No expansion to utilities beyond the 4 listed.
- No joint-ownership allocation or parent-company consolidation beyond the
  NSTAR→Eversource rename.
- No backend/live queries from the browser — data is precomputed once.
- No build tooling (npm/React/bundlers) — plain HTML/CSS/JS only.

## Architecture

### 1. Data pipeline — `build_data.py`

A standalone Python script (not a notebook) at the repo root:

1. Connects to PUDL's `out_eia923__yearly_generation_fuel_combined.parquet`
   (via DuckDB + httpfs, same source/mechanism as the existing exploratory notebook).
2. Filters to the 4 utilities (by exact `utility_name_eia` match, following the same
   name-matching approach validated in the exploratory notebook) and years 2020–2024.
3. Renames `NSTAR Electric` → `Eversource` before aggregation.
4. Aggregates net generation (MWh) by utility, year, and fuel type
   (`fuel_type_code_pudl`, falling back to `energy_source_code`).
5. Computes each fuel's share (%) of that utility's total positive generation for
   that year.
6. Writes the result to `site/data/generation_mix.json` as an array of records:
   ```json
   [{"utility": "Eversource", "year": 2020, "fuel": "Natural Gas", "mwh": 123456.0, "share_pct": 42.1}, ...]
   ```

Re-running this script is how the data gets refreshed; the website itself never
queries PUDL directly.

### 2. Website — `site/`

Plain static site, no build step:

- `site/index.html` — single page, structure:
  - **Header** — title, one-line description, data source and year range.
  - **Per-utility trend section** — one stacked chart per utility (4 total), each
    showing fuel-mix share by year across 2020–2024. Chart type: 100%-stacked bar
    (clearer for discrete year-over-year comparison than stacked area with only 5
    points).
  - **Methodology / caveats section** — plain-language explanation of: data source
    (PUDL / EIA-923 yearly generation-fuel table), year range, the NSTAR→Eversource
    rename, and the joint-ownership/parent-company limitation.
  - **Footer** — link back to the GitHub repo.
- `site/styles.css` — page styling.
- `site/app.js` — fetches `data/generation_mix.json` and renders the 4 charts via
  Chart.js (loaded from CDN).
- Consistent color-per-fuel-type across all 4 charts, shared legend. Palette and
  accessibility choices follow the project's `dataviz` skill guidance.

### 3. Deployment — GitHub Pages

- Site files live under `/site` in this repo (confirmed location, not `/docs`, since
  `/docs` is now used for spec documents).
- GitHub Pages will need to be enabled in repo settings, pointed at the `/site` folder
  on the default branch (or via a simple GitHub Actions deploy step if folder-based
  Pages isn't available for this repo's plan) — this is a repo-settings change the
  user will confirm/apply, not something done unilaterally.

## Open items resolved during brainstorming

- Medium: static website (not slides/report).
- Scope: exactly the 4 utilities already in the exploratory notebook, not expanded.
- Data treatment: raw as-reported + NSTAR→Eversource rename only.
- Year range: extended from the notebook's 2021–2024 to a full 2020–2024 (5 years).
- Story: per-utility trend, not cross-utility snapshot comparison.
- Build approach: plain HTML/CSS/JS + Chart.js, no framework/build tooling.
- Methodology section: included.
- Old notebook: left as-is, not part of the deliverable.

## Testing / validation

- Sanity-check `generation_mix.json` output: 4 utilities × 5 years × N fuels, shares per
  utility/year sum to ~100%.
- Visual check of the rendered site in a browser (all 4 charts render, legend
  consistent, no console errors).
