# Statistical models

The models ask whether ownership groups differ after broad state and year
differences are considered. They estimate associations, not causal effects.

The ownership rule is applied in order: MTC for an investor-owned utility with
a foreign or multinational ultimate parent; DOM for an investor-owned utility
with a U.S.-based parent or shareholders; SOE for direct state-government or
state-level public ownership; and COOP for local, municipal, member-owned,
cooperative, or community ownership that is not shareholder-owned. DOM is the
model reference category. No selected utility is coded SOE.

`legal_ownership_description` preserves the legal form so municipal utilities
remain distinguishable from member-owned cooperatives within the COOP category.
Annual ownership is assigned from the owner in place on December 31 of each year.

## Price model

Separate models are run for residential, commercial, and industrial bundled
average prices:

> constant-2024 price = ownership + state + year

Each available utility-year in the 42-utility regional panel counts once.
Prices are EIA published cents per kWh converted to constant 2024 cents with
annual CPI-U. Uncertainty uses CR1 standard errors clustered by utility.

| Customer class | N | Comparison with DOM | Estimate | 95% confidence interval | p-value |
| --- | ---: | --- | ---: | ---: | ---: |
| Residential | 500 | MTC | -4.06¢ | -8.55 to 0.42 | 0.075 |
| Residential | 500 | COOP | -10.87¢ | -15.16 to -6.57 | <0.001 |
| Commercial | 500 | MTC | -4.09¢ | -7.53 to -0.64 | 0.021 |
| Commercial | 500 | COOP | -7.06¢ | -10.36 to -3.76 | <0.001 |
| Industrial | 477 | MTC | -2.09¢ | -6.53 to 2.35 | 0.346 |
| Industrial | 477 | COOP | -6.64¢ | -10.27 to -3.01 | 0.001 |

Negative estimates indicate a lower adjusted price than DOM. The COOP
confidence intervals remain below zero in all three customer classes. The MTC
interval remains below zero only for commercial prices.

The website also reports a smaller matched-sample check that adds routine
SAIDI and reliability-reporting method. It is a sensitivity check, not the
headline model.

## Reliability model

The reliability model uses the reviewed 30-utility panel:

> routine SAIDI = ownership + state + year + reporting method

Routine SAIDI excludes major-event days. The model includes 293 usable
utility-years from 26 utilities and clusters uncertainty by utility.

| Comparison with DOM | Estimate | 95% confidence interval | p-value |
| --- | ---: | ---: | ---: |
| MTC | +40.97 minutes | -10.70 to 92.64 | 0.115 |
| COOP | +38.75 minutes | -45.35 to 122.86 | 0.352 |

Both intervals include zero, so this sample does not establish a clear
ownership difference in routine outage duration.

## Limits

- Utilities were selected by project rules; they are not a random or complete
  regional sample.
- State and year indicators do not account for every regulatory, customer,
  infrastructure, contract, or weather difference.
- Reliability reporting definitions can differ even after a reporting-method
  indicator is included.
- Accurate unusual observations are retained. Only source-audited exclusions
  are applied.
- Statistical uncertainty is not proof for or against causation.
- Regional generation mix and authorized ROE are supplementary context and are
  not predictors in the headline models.

## Reproduction

```bash
python3 scripts/build_price_panel_models.py
python3 scripts/build_reliability_models.py
python3 -m unittest tests/test_price_panel_models.py tests/test_reliability_models.py
```

Exact machine-readable outputs are stored in
`data/processed/price_panel_model_results.json` and
`data/processed/reliability_panel_model_results.json`.
