# Simple ownership-price model

## Question

After accounting for state and year, are inflation-adjusted electricity prices
different at MTC, DOM, and COOP utilities in the selected 30-utility sample?

This is a preliminary association check. It does not prove that ownership causes a
price difference.

## Model

The project runs the same simple model separately for residential, commercial, and
industrial prices:

> inflation-adjusted price = ownership group + state + year

- DOM is the reference group.
- MTC and COOP estimates are therefore differences from DOM in cents per kWh.
- Prices are EIA bundled average prices converted to constant 2024 cents using annual
  CPI-U.
- Every usable utility-year counts once; there are no customer or revenue weights.
- State indicators account for persistent price differences among states.
- Year indicators account for changes shared across utilities in a given year.
- The 95% uncertainty ranges use CR1 standard errors clustered by utility, so repeated
  years for the same utility are not treated as fully independent.
- Ownership is coded for each year, preserving the documented ownership changes for
  United Illuminating and Narragansett Electric.

The model is ordinary least squares (OLS). It has 20 estimated parameters: an
intercept, two ownership indicators, six state indicators, and eleven year indicators.
The design matrix has full rank in every reported model.

## Primary results

All EIA-published bundled prices are used when the relevant price is present.

| Customer type | Comparison with DOM | Estimated difference | 95% range | Plain reading |
| --- | --- | ---: | ---: | --- |
| Residential | MTC | -7.07¢/kWh | -13.30 to -0.84 | Lower; range stays below zero |
| Residential | COOP | -12.05¢/kWh | -18.24 to -5.85 | Lower; range stays below zero |
| Commercial | MTC | -6.01¢/kWh | -9.93 to -2.10 | Lower; range stays below zero |
| Commercial | COOP | -7.72¢/kWh | -11.97 to -3.47 | Lower; range stays below zero |
| Industrial | MTC | -2.62¢/kWh | -7.16 to 1.93 | Uncertain; range crosses zero |
| Industrial | COOP | -6.11¢/kWh | -9.99 to -2.24 | Lower; range stays below zero |

Usable sample sizes are 347 utility-years from 30 utilities for residential and
commercial prices, and 324 utility-years from 29 utilities for industrial prices.

The clearest simple reading is that the model still shows lower residential and
commercial prices for both MTC and COOP utilities after state and year are accounted
for. Industrial estimates point in the same direction, but the MTC comparison is too
uncertain to call a clear difference.

## Coverage sensitivity check

The model was repeated using only prices covering at least 50% of bundled plus
delivery-only customers in the same customer class. All six ownership estimates keep
the same lower-price direction. This check is reported as a sensitivity result rather
than a second main model because the 50% rule is a project screen, not an EIA quality
standard.

## Limits

- The 30 utilities were selected as large utilities within the three 2024 ownership
  groups. They are not a random or complete sample of the region.
- State and year controls do not account for every reason prices differ. Utility size,
  customer mix, generation contracts, rate design, regulation, and other factors may
  still matter.
- The model does not test ROE. The matched-state ROE section remains a separate,
  descriptive mechanism check because the source-audited ROE sample is small.
- A utility fixed-effect is not included because it would absorb the nearly stable
  ownership categories that this model is trying to compare.
- Statistical uncertainty is not the same as proof of causation.

## Reproduction

Run:

```bash
python3 build_price_models.py
python3 -m unittest tests/test_price_models.py
```

The build script reads
`data/processed/utility_price_panel_2013_2024.csv` and writes the reviewed result to
`data/processed/ownership_price_model_results.json` plus the website JSON and
JavaScript copies in `site/data/`.
