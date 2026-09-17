# Data dictionary

This dictionary is generated from the CSV files included in the professor handoff. It records each file's actual headers, row count, observed data type, missing-value count, range, and examples. The field-level table is in [`data-dictionary.csv`](data-dictionary.csv).

Run `python3 scripts/build_data_dictionary.py --check` to confirm that the dictionary still matches every delivered CSV. The check fails if a file, field, row count, or observed value profile changes without rebuilding the dictionary.

## Key definitions

The analytical ownership rule is applied in this order:

1. `MTC`: investor-owned utility with a foreign or multinational ultimate parent.
2. `DOM`: investor-owned utility with a U.S.-based ultimate parent or shareholders. DOM is the model reference category.
3. `SOE`: utility owned directly by a state government or state-level public entity.
4. `COOP`: local, municipal, member-owned, cooperative, or community-owned utility that is not shareholder-owned.

No utility in either selected sample is coded SOE. `legal_ownership_description` retains the legal form so municipal utilities remain distinguishable from member-owned cooperatives inside the broader COOP category. Annual ownership is the owner in place on December 31 of the row's year.

- `SAIDI`: average outage-duration minutes per customer.
- `SAIFI`: average outage interruptions per customer.
- `CAIDI`: average minutes per interruption, derived in the standardized PUDL table as SAIDI divided by SAIFI.
- `routine`: excludes major-event days.
- Blank cells remain missing. The build does not replace an unavailable value with zero.

## How to read the field-level CSV

`observed_type`, counts, ranges, and examples describe the frozen files in this package. They do not claim that future versions of an upstream source must have the same range. Numeric EIA identifiers are labeled as identifiers so they are not mistaken for measurements.

## Delivered CSV inventory

| File | Role | Rows | Columns |
| --- | --- | ---: | ---: |
| `data/manual/iso_fuel_mix_crosschecks.csv` | Manually reviewed cross-check | 2 | 7 |
| `data/manual/reliability_independent_checks.csv` | Manually reviewed cross-check | 7 | 14 |
| `data/processed/expanded_utility_candidates_2024.csv` | Analysis-ready output | 42 | 15 |
| `data/processed/iso_fuel_mix_2013_2024.csv` | Analysis-ready output | 192 | 15 |
| `data/processed/iso_fuel_mix_crosschecks_2024.csv` | Analysis-ready output | 2 | 10 |
| `data/processed/ownership_price_summary_2013_2024.csv` | Analysis-ready output | 216 | 17 |
| `data/processed/price_panel_model_analysis.csv` | Analysis-ready output | 504 | 34 |
| `data/processed/reliability_coverage_audit_2013_2024.csv` | Analysis-ready output | 360 | 59 |
| `data/processed/reliability_panel_model_analysis.csv` | Analysis-ready output | 360 | 13 |
| `data/processed/reliability_source_validation_2013_2024.csv` | Analysis-ready output | 360 | 11 |
| `data/processed/roe_annual_pilot_2013_2024.csv` | Analysis-ready output | 72 | 23 |
| `data/processed/roe_ownership_sources.csv` | Analysis-ready output | 7 | 9 |
| `data/processed/roe_rate_case_events.csv` | Analysis-ready output | 25 | 17 |
| `data/processed/roe_source_register.csv` | Analysis-ready output | 37 | 8 |
| `data/processed/utility_panel_candidates_2024.csv` | Analysis-ready output | 30 | 20 |
| `data/processed/utility_price_panel_2013_2024.csv` | Analysis-ready output | 360 | 54 |
| `data/processed/utility_price_panel_expanded_2013_2024.csv` | Analysis-ready output | 504 | 37 |
| `data/raw/eia861/pudl_reliability_top10_2013_2024.csv` | Frozen source input | 642 | 22 |
| `data/raw/eia923/pudl_iso_generation_by_fuel_2013_2024.csv` | Frozen source input | 216 | 4 |
| `data/raw/eia_esr/pudl_customer_coverage_expanded_2013_2024.csv` | Frozen source input | 2,208 | 6 |
| `data/raw/eia_esr/pudl_customer_coverage_top10_2013_2024.csv` | Frozen source input | 1,698 | 6 |
| `data/raw/pudl_eia861_ne_ny_2024_roster.csv` | Frozen source input | 55 | 7 |
| `site/data/iso_fuel_mix.csv` | Browser-ready copy | 192 | 15 |
| `site/data/ownership_price_summary.csv` | Browser-ready copy | 216 | 17 |
| `site/data/price_panel_model_analysis.csv` | Browser-ready copy | 504 | 34 |
| `site/data/reliability_panel.csv` | Browser-ready copy | 360 | 59 |
| `site/data/reliability_panel_model_analysis.csv` | Browser-ready copy | 360 | 13 |
| `site/data/roe_case_study.csv` | Browser-ready copy | 72 | 42 |
| `site/data/roe_source_register.csv` | Browser-ready copy | 37 | 8 |
| `site/data/utility_price_panel.csv` | Browser-ready copy | 360 | 54 |
| `site/data/utility_price_panel_expanded.csv` | Browser-ready copy | 504 | 37 |

## Interpretation notes

The price and reliability samples are selected project panels, not random samples of every utility in the region. The models show associations rather than causal effects. Regional fuel mix and the matched-state authorized-ROE pilot are supplementary context, not explanatory variables in the headline models.

For the rules behind each field, use [`statistical-models.md`](statistical-models.md), [`reliability-coverage-audit.md`](reliability-coverage-audit.md), [`iso-fuel-mix-methodology.md`](iso-fuel-mix-methodology.md), and [`ct-roe-pilot-methodology.md`](ct-roe-pilot-methodology.md).
