# Residential base-rate comparison, 2020-2024

## Scope

This dataset compares the four operating utilities already used in the project:

| EIA utility ID | Project label | Legal operating utility | State |
|---:|---|---|---|
| 4226 | Con Edison | Consolidated Edison Company of New York, Inc. | NY |
| 13511 | NYSEG | New York State Electric & Gas Corporation | NY |
| 54913 | NSTAR Electric | NSTAR Electric Company d/b/a Eversource Energy | MA |
| 19497 | United Illuminating | The United Illuminating Company | CT |

The comparison is at the regulated operating-utility level, not the publicly traded parent-company level. For example, NSTAR Electric is the Massachusetts electric utility used here; Eversource's Connecticut utility is not substituted for it.

## Comparable rate definition

For each utility and year, the dataset records the ordinary residential tariff in force at the end of the calendar year:

- fixed customer or basic-service charge, in dollars per month;
- base distribution or delivery energy charge, in dollars per kWh; and
- an illustrative monthly base-delivery bill at 700 kWh, calculated as fixed charge + 700 x base energy charge.

The modeled bill is not a customer's total electric bill. It excludes generation supply, transmission, taxes, public-benefit charges, revenue-decoupling adjustments, make-whole charges, and other riders or reconciling mechanisms. It is included only to put utilities with different fixed and volumetric rate designs on one consistent usage basis.

## Time convention and utility-specific notes

- The observation is a December 31 snapshot, using the latest applicable residential base rate in each calendar year.
- Con Edison uses SC 1 Rate I. For the 2024 year-end snapshot, the winter/all-kWh rate is used; the summer block above 250 kWh is not applicable on December 31.
- NYSEG uses SC 1. The Energy Charge is used without the separately stated Make-Whole Energy Charge or other riders.
- NSTAR Electric uses R-1 Residential and only the Base Distribution column. The 2023 annual return did not include the needed tariff schedule, so the D.P.U. 22-22 approved compliance tariff is used.
- United Illuminating uses Rate R. Only the Basic Service fixed charge and base Distribution per-kWh charge are used.

## Source handling notes

- Con Edison values come from the historical SC 1 tariff leaves downloaded for the relevant years.
- NYSEG's 2020-2022 values come from Appendix CC, Schedule A1. The 2023-2024 values come from the official March 2024 historical SC 1 tariff. The locally downloaded current consolidated tariff has subsequently been updated through 2026 and is not treated as the historical 2023-2024 source.
- NSTAR values come from Massachusetts annual-return tariff supplements for 2020-2022 and 2024, plus the approved D.P.U. 22-22 compliance tariff for 2023.
- United Illuminating values come from its annual published rate schedules.

Full source filenames, page or tariff-leaf references, and official URLs are included in the workbook's `Sources` sheet.
