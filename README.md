# Utility Ownership, Prices, and Reliability

This project asks whether utility ownership is associated with electricity
prices and routine outage duration in New York and New England from 2013–2024.
It uses published price data for 42 utilities and a source-audited reliability
panel for 30 utilities.

## Main findings

- COOP utilities have lower adjusted residential, commercial, and industrial
  prices than DOM utilities in this selected sample.
- MTC utilities have a clearly lower adjusted commercial price than DOM
  utilities. The residential and industrial MTC estimates point lower, but
  their 95% confidence intervals include zero.
- The reliability model does not show a clear ownership difference in routine
  SAIDI; both ownership confidence intervals include zero.

These are associations, not causal effects. The samples are selected rather
than random, and the models do not control every difference in regulation,
customer mix, infrastructure, or weather.

The website also retains two supplementary context checks: regional NYISO and
ISO-NE generation mix, and matched-state price/authorized-ROE comparisons.

## Repository guide

- `site/`: public website and browser-ready data
- `scripts/`: core build and validation programs used by the reproducible analysis
- `data/processed/`: analysis-ready tables and exact model outputs
- `data/manual/`: manually reviewed cross-check registers
- `data/raw/`: separately shared source archive; excluded from Git because of size
- `docs/`: methods, source-audit notes, environment instructions, and data dictionary
- `tests/`: automated data, model, and website checks
- `tools/`: optional, special-purpose packaging and figure-export workflows
- `outputs/`: ignored generated artifacts from optional tools

The complete field-level inventory is in
[`docs/data-dictionary.csv`](docs/data-dictionary.csv), with a short reading guide
in [`docs/data-dictionary.md`](docs/data-dictionary.md).

The planned 2001–2024 historical extension starts in
[`docs/historical-expansion-setup.md`](docs/historical-expansion-setup.md). The
representative-year file check is documented in
[`docs/historical-schema-pilot.md`](docs/historical-schema-pilot.md), and the
reviewed Phase 2 utility-history connections are in
[`docs/utility-history-phase-2.md`](docs/utility-history-phase-2.md). The
reviewed Phase 3 ownership events, annual owner assignments, and territory
warnings are in
[`docs/ownership-history-phase-3.md`](docs/ownership-history-phase-3.md).
The completed Phase 4 historical price, revenue, sales, customer, and territory
tables are documented in
[`docs/historical-price-panel-phase-4.md`](docs/historical-price-panel-phase-4.md).
The Phase 5 review of consecutive price coverage around clean ownership changes
is in
[`docs/event-window-review-phase-5.md`](docs/event-window-review-phase-5.md).
The Phase 6 fixed event windows, customer-base screen, and transparent
potential-control pools are in
[`docs/research-design-phase-6.md`](docs/research-design-phase-6.md).
The Phase 7 Extended Historical Data page for the full 2001–2024 panel is
documented in
[`docs/november-data-extension-phase-7.md`](docs/november-data-extension-phase-7.md).
It presents both published nominal prices and inflation-adjusted 2024 prices,
without adding a new causal analysis.

## Rebuild and verify

Place the separately shared `data/raw/` folder in the repository, then run:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 scripts/rebuild_project.py --check-only
python3 scripts/rebuild_project.py
python3 scripts/build_data_dictionary.py --check
```

The full rebuild is offline. It regenerates the processed and website data in
dependency order and then runs the complete test suite. See
[`docs/environment.md`](docs/environment.md) for tested software versions and
[`data/raw/README.md`](data/raw/README.md) for the required source-file layout.
When working in a Git checkout, `git diff --check` is an additional whitespace
check; it is not needed in the extracted professor package.

## Audit trail

- Price: annual EIA Electric Sales, Revenue, and Average Price Tables 6–8
- Reliability: EIA Form 861, standardized through PUDL and checked against the
  official annual workbooks
- Regional generation: EIA Form 923 plant generation, grouped by balancing
  authority through PUDL
- Authorized ROE: cited state-regulator decisions and official filings

Detailed model assumptions are in
[`docs/statistical-models.md`](docs/statistical-models.md).

## Optional workflows

Special-purpose exports are intentionally outside the normal rebuild. See
[`tools/README.md`](tools/README.md) for the professor handoff packager and the
paper-ready JPEG exporter. These tools consume the core project outputs but do
not add generated documents or images to the tracked analysis or public site.
