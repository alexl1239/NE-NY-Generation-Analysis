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
- `scripts/`: all build and validation programs
- `data/processed/`: analysis-ready tables and exact model outputs
- `data/manual/`: manually reviewed cross-check registers
- `data/raw/`: separately shared source archive; excluded from Git because of size
- `docs/`: methods, source-audit notes, environment instructions, and data dictionary
- `tests/`: automated data, model, and website checks

For a professor-facing map of the package and its verification steps, start with
[`PROFESSOR_HANDOFF.md`](PROFESSOR_HANDOFF.md). The complete field-level inventory
is in [`docs/data-dictionary.csv`](docs/data-dictionary.csv), with a short reading
guide in [`docs/data-dictionary.md`](docs/data-dictionary.md).

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
