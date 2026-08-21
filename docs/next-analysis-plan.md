# Focused analysis plan and status

## Goal

Test whether the current price finding is reasonably dependable and add a small
reliability comparison without turning the project into a major new study.

The balanced 30-utility overview remains the main presentation and the website
default.

## The two additions

### 1. Expanded price check

Repeat the existing price model for regional utilities with at least **10,000
residential customers in 2024**. The threshold was selected before running this
model. It produces 42 utilities: 11 MTC, 8 DOM, and 23 COOP.

The model remains simple and unweighted. It compares MTC and COOP with DOM after
accounting for state and year. It uses published EIA bundled-service prices adjusted
to 2024 cents. Missing prices stay missing and accurate unusual values are retained.

This is a robustness check. It does not replace the main 30-utility sample.

### 2. Reliability check

Use the already reviewed 30-utility panel to compare routine SAIDI, SAIFI, and CAIDI
between the ownership groups. Run separate unweighted models that account for state,
year, and the utility's EIA reporting method. Use DOM as the reference group.

Reliability is a separate service-quality outcome. This check does not assume that
reliability causes prices or that prices cause reliability.

## Results

- In the 42-utility price check, every MTC and COOP estimate remains below DOM.
- The COOP difference remains clear for residential, commercial, and industrial
  customers.
- The MTC commercial difference remains clear. Its residential and industrial
  uncertainty ranges cross zero, so those two comparisons remain uncertain.
- In the primary reliability models, none of the MTC or COOP differences from DOM is
  clear for routine SAIDI, SAIFI, or CAIDI.
- Reliability results move when storms or reporting samples change. The project
  therefore does not have a stable reliability tradeoff that explains the price
  differences.

These are associations, not proof that ownership causes the differences.

## Intentionally unchanged

- No customer weights
- No automatic outlier deletion
- No ROE regression; ROE remains a visual matched-state example
- No Monte Carlo simulation, machine learning, or forecasting
- No large new set of explanatory variables
- No direct price-reliability causal model

## Presentation

The website keeps the raw 30-utility findings as the default. The adjusted-price tab
shows the existing 30-utility model, one short expanded-sample note, and one short
reliability note. Exact machine-readable results remain available for audit.
