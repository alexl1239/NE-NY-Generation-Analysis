# Phase 4: historical price and customer records

Phase 4 builds the annual price, revenue, electricity-sales, and customer
records needed for the 2001-2024 extension. It keeps the fixed 42-utility
sample. This phase prepares and checks data; it does not estimate an ownership
effect or update the website.

## What was completed

- Parsed every annual EIA *Electric Sales, Revenue, and Average Price* archive
  from 2001 through 2024.
- Used the reviewed Phase 2 identity table to connect current utilities to the
  utility IDs and legal predecessors reported in each annual file.
- Added the Phase 3 owner, ownership class, and territory warning to every
  annual record.
- Produced 3,024 reported-entity records: 42 utilities by 24 years by three
  customer classes.
- Reconciled every positive published record to the corresponding detailed
  Form EIA-861 revenue, sales, and customer counts.
- Reproduced all 1,512 utility-year-sector observations in the existing
  2013-2024 panel.

## Earliest defensible coverage

All 42 reported utility identities are supported beginning in 2001. This does
not mean that every utility sold bundled electricity in every customer class.
The published table correctly omits some utility-sector rows when the detailed
file reports no positive bundled-customer activity.

Forty-one utilities have a published residential price in 2001. Eastern Maine
Electric Cooperative's published bundled residential series begins in 2015;
the earlier annual records are retained as unavailable rather than replaced
with another measure. Across all utilities, years, and the three customer
classes, 2,903 of 3,024 observations have a published bundled price. The other
121 observations have zero bundled customers or no positive bundled row in the
detailed file. There are no unresolved positive bundled-customer records.

## Legal predecessors and acquired territories

NSTAR Electric and Unitil use combined legal-predecessor records in their early
years. Their combined prices are calculated from the sum of the officially
published revenue and sales values, and the method is labeled on every affected
row.

Three utilities have a different issue: their present territory absorbed
another utility. The main panel preserves the utility entity reported in each
year. A separate comparison table shows what happens when the earlier
components are combined to approximate the current territory:

- Green Mountain Power is combined with Central Vermont Public Service through
  2012. Beginning in 2013, the current GMP record contains the combined
  territory.
- Versant's earlier Bangor Hydro record is combined with Maine Public Service
  through 2013. Beginning in 2014, the current record contains the combined
  territory.
- Vermont Electric Cooperative is combined with Citizens' Vermont electric
  division for 2001-2002. The fixed-territory values are left unavailable for
  2003 and the partial acquisition year 2004 because a clean Citizens component
  is not available. The current VEC record is used beginning with the first
  full combined year, 2005.

These territory rows are descriptive data checks. They are not classified as
clean ownership changes.

## Files

- `data/processed/utility_price_history_2001_2024.csv` contains the main
  reported-entity utility-year-sector panel.
- `data/processed/historical_price_coverage_2001_2024.csv` summarizes each
  utility's earliest price year, price coverage, and territory warnings.
- `data/processed/historical_territory_comparison_2001_2024.csv` contains only
  the three acquired-territory comparisons.
- `scripts/build_historical_price_panel.py` rebuilds and validates the Phase 4
  tables.
- `tests/test_historical_price_panel.py` checks row coverage, source
  reconciliation, overlap with the current panel, predecessor combinations,
  and the unforced VEC gap.

## Phase 5 status

Phase 5 reviewed missingness and the consecutive observations available before
and after every clean ownership event. See
[`event-window-review-phase-5.md`](event-window-review-phase-5.md). The website
continues to use the existing 2013-2024 files until the later website-update
phase.

Phase 6 then fixed the usable event windows and screened the transparent
potential-control pools without using price outcomes. See
[`research-design-phase-6.md`](research-design-phase-6.md).

## Official sources

- EIA Electric Sales, Revenue, and Average Price:
  <https://www.eia.gov/electricity/sales_revenue_price/>
- Form EIA-861 detailed files:
  <https://www.eia.gov/electricity/data/eia861/>
