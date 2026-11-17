# Raw source archive

This directory is intentionally excluded from Git because the local source
archive is about 180 MB. The professor handoff ZIP includes only the required
paths listed below. Older base-rate PDFs and duplicate extracts in the local
folder are not needed for the current rebuild. Do not include `.DS_Store` files.

The normal rebuild reads these frozen files and does not need the internet.
Keeping the local copies matters: several upstream URLs use a `stable` label
but can still change when the publisher revises old records.

## Required layout

- `eia_esr/f8612013.zip` through `eia_esr/f8612024.zip`: annual EIA-861
  Electric Sales, Revenue, and Average Price archives used for the price panel.
- `eia_esr/pudl_customer_coverage_top10_2013_2024.csv`: frozen PUDL customer
  counts for the reviewed 30-utility panel.
- `eia_esr/pudl_customer_coverage_expanded_2013_2024.csv`: frozen PUDL
  customer counts for the 42-utility threshold check.
- `pudl_eia861_ne_ny_2024_roster.csv`: frozen 2024 regional utility roster used
  to apply the 10,000-residential-customer rule.
- `eia861/official/f8612013.zip` through `eia861/official/f8612024.zip`:
  official EIA-861 archives used to compare every selected reliability value
  directly with the source workbooks.
- `eia861/pudl_reliability_top10_2013_2024.csv`: frozen standardized PUDL
  reliability rows used by the coverage audit.
- `eia923/pudl_iso_generation_by_fuel_2013_2024.csv`: frozen PUDL EIA-923
  generation aggregates for NYISO and ISO-NE.

The EIA/PUDL price and reliability files were retrieved on August 8, 2026. The
ISO fuel-mix cache was retrieved on August 9, 2026. Those dates are also stored
in the generated records.

## Historical schema pilot

The representative-year pilot additionally uses these official EIA archives:

- `eia_esr/f8612001.zip`, `f8612002.zip`, `f8612003.zip`, `f8612012.zip`, and
  `f8612013.zip` for the published utility-price tables;
- `eia861/reformatted/861_2001.zip`, `861_2002.zip`, and `861_2003.zip` for the
  EIA-reformatted detailed sales and utility files;
- `eia861/official/f8612012.zip` and `f8612013.zip` for the later detailed-file
  layouts.

These pilot archives were retrieved on November 13, 2026. They are required by
`scripts/build_historical_schema_pilot.py`, but they are not part of the normal
2013–2024 rebuild.

## Phase 2 utility-history review

The reviewed utility-history build uses the complete annual identity and
retail-sales sequence:

- `eia861/reformatted/861_2001.zip` through `861_2011.zip`;
- `eia861/official/f8612012.zip` through `f8612024.zip`.

The additional 2004-2011 archives were retrieved on November 13, 2026. The
script `scripts/build_utility_identity_history.py` checks both the utility file
and the state-specific retail-sales file before marking a utility-year as
covered. These archives are not yet part of the normal 2013-2024 rebuild.

## Phase 3 ownership review

Phase 3 adds no new raw downloads. It uses the Phase 2 annual EIA sequence plus
the official company, regulator, and SEC links recorded in
`data/manual/ownership_event_sources.csv`. The reviewed sources support closing
dates, parent changes, consolidations, and the three material acquired-territory
cases that Phase 4 must handle explicitly.

## Phase 4 historical price panel

The Phase 4 build uses the complete published price-table sequence:

- `eia_esr/f8612001.zip` through `f8612024.zip`;
- `eia861/reformatted/861_2001.zip` through `861_2011.zip`;
- `eia861/official/f8612012.zip` through `f8612024.zip`.

The 2004-2011 published price archives were retrieved on November 15, 2026.
The remaining archives retain the dates recorded in the earlier sections.
`scripts/build_historical_price_panel.py` uses the published utility tables for
prices and their supporting revenue, sales, and customer counts, then checks
them against the detailed Form EIA-861 files. These historical archives remain
outside the normal 2013-2024 website rebuild until the later website-update
phase.
