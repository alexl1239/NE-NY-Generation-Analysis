# Reliability Coverage Audit: 2013–2024

**Status:** Direct-source validation and targeted regulator checks integrated into the findings website  
**Sample:** 30 selected utilities × 12 years = 360 expected utility-year rows  
**Primary source:** [EIA Form 861 reliability data](https://www.eia.gov/electricity/data/eia861/)  
**Standardized table:** [PUDL `core_eia861__yearly_reliability`](https://catalystcoop-pudl.readthedocs.io/en/stable/data_sources/eia861.html)

## What was collected

The audit uses the utility-level Distribution System Reliability responses from
Form EIA-861. Utilities report SAIDI and SAIFI and identify whether they use the
IEEE standard or another method. EIA explicitly allows either choice. PUDL
standardizes the annual files and provides CAIDI as SAIDI divided by SAIFI.

For each utility-year, the audit retains:

- SAIDI, SAIFI, and CAIDI including major event days
- SAIDI, SAIFI, and CAIDI excluding major event days
- The available measures that include major events but remove loss-of-supply events
- Reporting standard (`ieee_standard` or `other_standard`)
- Number of customers included in the reliability calculation
- Outage-recording and interruption-definition fields
- Direct links to the annual EIA source archive and the PUDL table

No missing observation is filled, interpolated, or copied from an adjacent year.

## How the PUDL rows were handled

The filtered PUDL table contains 642 rows. It generally provides two possible rows
per utility-year: one slot for the IEEE method and one for another method. Usually
only one of those rows contains customers or reliability measures. The script keeps
the single populated row and rejects a utility-year if more than one populated
standard row appears.

The processed audit then creates the complete expected 360-row utility-year grid so
that an absent source row remains visible as `not_reported`.

As a direct source check, all 12 official EIA reliability workbooks from 2013 through
2024 were downloaded and compared with PUDL for all 30 selected utilities. The check
compared 2,841 available standard, customer-count, SAIDI, SAIFI, and CAIDI fields.
All 2,841 matched the official EIA workbook values. All 39 missing utility-years are
absent from both sources. The result is saved in
`data/processed/reliability_source_validation_2013_2024.csv` and can be reproduced
with `validate_reliability_sources.py`.

## Verified coverage results

- **321 of 360** expected utility-years have a populated EIA/PUDL reliability row.
- **Peabody Municipal Light Plant** and **Fishers Island Electric** have no populated
  row in 2013–2024.
- **FirstEnergy Pennsylvania Electric** has a row only in 2024 because the current
  EIA entity began after a legal consolidation; predecessor IDs are not stitched in.
- **Taunton Municipal Lighting Plant** is missing 2013–2015, and **Central Hudson**
  is missing 2014.
- **305** rows have SAIDI including major events and **294** have SAIDI excluding
  major events.
- **318** rows have SAIFI including major events and **295** have SAIFI excluding
  major events.
- PUDL CAIDI agrees with SAIDI divided by SAIFI wherever all three fields are
  available, within the rounding precision of the published table.

Additional mechanical checks found:

- No negative reliability values.
- No case where a utility's including-major-events SAIDI or SAIFI is smaller than
  its corresponding excluding-major-events value.
- No case where a loss-of-supply-removed value is larger than the corresponding
  all-events value.
- No duplicate populated utility-year reporting rows.

These checks establish that the project copied and organized the published data
correctly. They do not prove that every value originally submitted by a utility was
free of a reporting or entry error.

The website uses a second, metric-specific analysis layer. Original EIA/PUDL values
remain unchanged in the audit, but a value can be withheld from a chart when an
independent regulator filing provides concrete evidence of a source conflict. This
currently affects only NSTAR Electric in 2017 and 2023. After those exclusions, the
website shows 304 including-major-event SAIDI values, 293 excluding-major-event SAIDI
values, 317 including-major-event SAIFI values, 293 excluding-major-event SAIFI
values, 304 including-major-event CAIDI values, and 289 excluding-major-event CAIDI
values.

Important missing or incomplete patterns include:

| Utility | Year(s) | What is missing |
|---|---:|---|
| Peabody Municipal Light Plant | 2013–2024 | No populated reliability row |
| Fishers Island Electric | 2013–2024 | No populated reliability row |
| FirstEnergy Pennsylvania Electric | 2013–2023 | Current EIA entity not yet reported |
| Taunton Municipal Lighting Plant | 2013–2015 | No populated reliability row |
| Central Hudson | 2014 | No populated reliability row |
| Chicopee Electric Light | 2013–2024 | Excluding-major-events measures are not reported |
| Burlington Electric Department | 2013–2024 | Most duration measures are not reported |
| Reading Municipal Light Department | Several years | Some including- or excluding-major-events measures are not reported |
| Vermont Electric Cooperative | 2013–2014 | SAIDI and CAIDI, both with and without major events |
| Wallingford Electric Division | 2013 | SAIDI, SAIFI, and CAIDI including major events; the excluding-major-events values are present |

## Reporting-standard comparability

The reporting method is not constant for the whole sample:

- Six utilities switch methods during the panel:
  - Central Hudson: IEEE in 2013 and 2015, another method in 2016–2023, IEEE in 2024;
    2014 is missing
  - Fairport: other method through 2016; IEEE from 2017
  - Massachusetts Electric: IEEE in 2013–2014, other method in 2015–2020, IEEE from 2021
  - NYSEG: other method in 2013–2014, IEEE in 2015–2016, other method from 2017
  - United Illuminating: IEEE in 2013, other method in 2014–2023, IEEE in 2024
  - Unitil Energy Systems: other method in 2013; IEEE from 2014

This does not prove that the values are wrong. EIA permits utilities to use a method
other than IEEE, so `other_standard` is a definition/comparability limit rather than
an error flag. Every populated non-IEEE row in this project matches the official EIA
workbook. The website retains those values for within-utility description and labels
the method. Its ownership overview now reports simple annual unweighted medians with
the usable-utility count, explicitly as a descriptive summary. Apparent changes around
a method transition can partly reflect a change in measurement rules.

## Independent regulator cross-checks

The independent checks are recorded in
`data/manual/reliability_independent_checks.csv`. They are intentionally separate
from the direct EIA/PUDL comparison because a regulator's service-quality definition
may not be identical to the EIA schedule.

- **Connecticut Light & Power, 2017–2021:** A [Connecticut PURA management audit](https://portal.ct.gov/-/media/pura/1---website-media/eversource-management-audit-public.pdf?hash=284B093EE0D939A2ABD61731C0B58586&rev=beac01ab144c40c4956b3eaea4df5cff)
  provides non-major-event SAIDI, SAIFI, and CAIDI. The 2017, 2019, and 2021 values
  match EIA at the report's displayed precision; 2018 is close. The audit's 2020
  values differ from EIA, so the project records the difference but does not choose a
  replacement without evidence about the reporting vintage.
- **NSTAR Electric, 2017:** EIA and PUDL contain routine SAIDI of 74.3 and SAIFI of
  0.070, which produces CAIDI of about 1,061.43.
  [NSTAR's Massachusetts DPU filing](https://eeaonline.eea.state.ma.us/dpu/fileroom/#/dockets/docket/5574)
  reports SAIFI near 0.94 under its state service-quality and IEEE series. Those
  different definitions are not substituted into EIA, but they provide enough
  evidence to withhold the EIA routine SAIFI and derived routine CAIDI from the
  charts.
- **NSTAR Electric, 2023:** The EIA/PUDL row exactly duplicates Connecticut Light &
  Power's 2023 customer count and all six displayed reliability metrics. NSTAR's
  [Massachusetts DPU filing](https://eeaonline.eea.state.ma.us/dpu/fileroom/#/dockets/docket/11270)
  instead reports an IEEE-1366-2003 series of 48.021 SAIDI,
  0.662 SAIFI, and 72.534 CAIDI, with 1,468,015 customers in the supporting event-day
  analysis. The project preserves the EIA row but withholds all of its 2023
  reliability measures from analysis.

Other large observations are not automatically treated as errors. Taunton's routine
SAIFI of 5.321 in 2021, Wallingford's routine CAIDI of about 284.31 in 2013, and large
including-major-event storm spikes all match the official EIA workbooks and pass the
mechanical checks. They remain visible.

## Files

- Build script: `build_reliability_audit.py`
- Direct-source validation script: `validate_reliability_sources.py`
- Processed audit: `data/processed/reliability_coverage_audit_2013_2024.csv`
- Direct-source validation results:
  `data/processed/reliability_source_validation_2013_2024.csv`
- Independent regulator-check register:
  `data/manual/reliability_independent_checks.csv`
- Focused tests: `tests/test_reliability_audit.py`
- Filtered PUDL source cache: `data/raw/eia861/pudl_reliability_top10_2013_2024.csv`
  (kept locally and excluded from Git with the rest of `data/raw`)

The website now includes SAIDI, SAIFI, and CAIDI in the existing utility panels. It
defaults to excluding major events and allows the viewer to switch to including
major events. Missing or source-conflicted values remain blank, lines break at gaps,
reporting standards appear in point details, and ownership-row reliability medians
remain separate from the individual utility rows. The overview can show annual
unweighted ownership medians, with sample counts and a mixed-method warning. Each
panel states when a source-conflicted value was withheld. No published EIA value is
overwritten, weighted, or silently recoded.
