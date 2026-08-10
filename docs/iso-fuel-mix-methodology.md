# Regional Generation Mix: 2013–2024

**Purpose:** Supporting context for the utility ownership-price comparison  
**Regions:** NYISO (`NYIS`) and ISO New England (`ISNE`) balancing areas  
**Primary source:** [EIA Form 923](https://www.eia.gov/electricity/data/eia923/)  
**Standardization:** [PUDL EIA-923 outputs](https://catalystcoop-pudl.readthedocs.io/en/stable/data_sources/eia923.html)

## What the charts measure

The charts show annual net generation reported by power plants assigned to the
`NYIS` or `ISNE` balancing-authority code in the annual EIA plant table. Generation
comes from PUDL's standardized
`out_eia923__yearly_generation_fuel_combined` table, and the annual balancing-area
assignment comes from `core_eia860__scd_plants`.

This is a consistent federal-data series for 2013–2024. It is not generation owned by
the 30 selected utilities, and it is not a reconstruction of the electricity that any
individual utility purchased or delivered.

## Transformation

For each region and year, reported net generation is summed into eight PUDL fuel
groups: coal, natural gas, hydro, nuclear, oil, solar, waste and biomass, and wind.
Each displayed share is that fuel group's net generation divided by the sum of the
eight nonnegative groups.

PUDL's `other` group is zero or slightly negative throughout this sample. It is
excluded from the percentage stack because a negative segment cannot be represented
in a 100% stacked chart. The excluded amount is retained with every processed row and
is less than 0.02% of annual positive generation in every region-year. No missing
fuel share is imputed.

## Independent 2024 checks

The 2024 EIA/PUDL totals were compared with each ISO's own annual publication:

| Region | EIA/PUDL total | ISO-published total | Difference |
|---|---:|---:|---:|
| ISO-NE | 108,813.841 GWh | 108,599 GWh | +0.198% |
| NYISO | 134,954.327 GWh | 131,052 GWh | +2.978% |

ISO New England's total comes from Figure 1-1 and the accompanying text in its
[2024 Air Emissions Report](https://www.iso-ne.com/static-assets/documents/100028/final-2024-air-emission-report.pdf).
NYISO's total comes from Figure 23 of its
[2025 Power Trends report](https://www.nyiso.com/documents/20142/2223020/2025-Power-Trends.pdf/).

The values are close but are not expected to be identical. EIA assigns plant
generation to balancing areas, while the ISO reports use their own market and
resource-accounting definitions. The project does not replace either series or imply
that they are identical.

## Interpretation limits

- Imports are not included in the EIA plant-generation stack.
- Behind-the-meter and ISO market accounting may differ from EIA plant reporting.
- The regional mix does not identify a utility's power contracts, hedges, or owned
  generation.
- Utilities with different ownership types often share the same ISO conditions.
  Therefore, the charts provide regional cost context but cannot by themselves
  explain an ownership-price difference.

## Reproducible outputs

- Build script: `build_iso_fuel_mix.py`
- Processed data: `data/processed/iso_fuel_mix_2013_2024.csv`
- ISO cross-checks: `data/processed/iso_fuel_mix_crosschecks_2024.csv`
- Website data: `site/data/iso_fuel_mix.csv`, `.json`, and `.js`
