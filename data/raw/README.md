# Raw source archive

This directory is intentionally excluded from Git because the local source
archive is about 144 MB. The professor handoff ZIP includes only the required
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
