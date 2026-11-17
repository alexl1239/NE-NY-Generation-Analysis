# Phase 2: utility history connections

Phase 2 connects the 42 reported utilities in the current project roster to the
names and EIA utility IDs used in the older annual files. It does not build the
price panel, run an analysis, or change the website.

## What was completed

- Reviewed every annual Form EIA-861 utility and retail-sales file from 2001
  through 2024.
- Created a complete 42-utility by 24-year coverage check: 1,008 rows.
- Recorded every annual reported-name period, plus the early published-table
  spellings needed to match municipal systems.
- Resolved the two current IDs that do not extend cleanly to 2001.

All 42 current reported utility identities have an official annual EIA
connection back to 2001. This was not assumed in advance: each year is marked
as covered only when all required IDs appear in both the utility file and the
retail-sales file.

Phase 3 later found three material territory expansions involving Green
Mountain Power, Versant, and Vermont Electric Cooperative. Their absorbed
predecessor utilities are now recorded in the lineage file, but they are not
silently substituted into this Phase 2 annual-identity check. Phase 4 must make
the fixed-territory aggregation decision explicitly.

## The two real predecessor cases

### NSTAR Electric

The current EIA ID, `54913`, begins in 2007. The 2001-2006 service territory is
the combination of three retail distribution utilities:

- `1998` — Boston Edison Company
- `2886` — Cambridge Electric Light Company
- `4089` — Commonwealth Electric Company

The merger source also names Canal Electric, but Canal was a wholesale company.
It is therefore not included in the retail-price connection.

### Unitil Energy Systems

The current EIA ID, `24590`, first appears in the 2002 identity file. Unitil's
merger completed in December 2002, however, and the 2002 annual retail records
still report the full distribution territory under the two predecessor IDs:

- `4148` — Concord Electric Company
- `6077` — Exeter & Hampton Electric Company

For that reason, the price expansion should combine the two predecessor records
in 2001 and 2002, then use current ID `24590` beginning in 2003. This keeps the
annual data faithful to what EIA actually published.

## Name changes that are not company changes

The early files often reverse municipal word order, such as `City of Taunton`
versus `Taunton City of`. These are accepted reported-name variants, not new
utilities or ownership changes. The reviewed name file contains 15 exact
published-table variants for 2001-2002, as well as the names printed in every
annual EIA utility and sales file.

## Files

- `data/manual/utility_lineage.csv` — 50 reviewed identity records: 42 current
  IDs, five legal predecessors resolved in Phase 2, and three absorbed-territory
  components added during Phase 3.
- `data/manual/utility_name_aliases.csv` — reported names and the years in which
  each name appears. An “alias” here simply means another printed name for the
  same EIA identity.
- `data/processed/utility_identity_coverage_2001_2024.csv` — one row for every
  current utility and year, showing which ID or combination of IDs covers it.
- `scripts/build_utility_identity_history.py` — rebuilds the three tables from
  the official annual EIA archives and the two reviewed merger connections.
- `tests/test_utility_identity_history.py` — checks completeness, uniqueness,
  the predecessor years, and the early name variants.

## Later-phase status

Phase 3 now provides the broader ownership-change register, verified parent
companies and closing dates, and warnings for acquired territories. Phase 4
used both phases to extract and combine the historical price records; its
results are documented in
[`historical-price-panel-phase-4.md`](historical-price-panel-phase-4.md). The
website remains on its existing 2013-2024 data until the later website-update
phase.
