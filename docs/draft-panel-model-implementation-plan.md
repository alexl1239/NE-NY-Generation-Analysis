# Draft panel model: staged implementation plan

> **Superseded on August 31, 2026.** The public results page now focuses only on
> price. Its headline models use the 42-utility regional sample with ownership,
> state, and year. A smaller matched-sample check compares the same rows without and
> with routine SAIDI. CAIDI price models and reliability-outcome regressions are no
> longer displayed on that page. The material below preserves the earlier plan for
> project history.

## Purpose

Build a small, clearly labeled draft that demonstrates the panel-model approach
discussed by the professors. The draft is meant to help choose the final research
design. It is not intended to be the final model or evidence that ownership causes
electricity prices.

The work will appear on a separate website page. The existing observed-data overview
will remain the default presentation.

## Decisions made for the draft

- Use the reviewed 2013–2024 data already in the project.
- Use the 30 utilities with matched price and reliability coverage for the primary
  comparison.
- Analyze residential, commercial, and industrial prices separately.
- Convert published bundled prices to constant 2024 cents per kWh.
- Use DOM as the reference ownership group and estimate differences for MTC and COOP.
- Represent the electricity market with an ISO-NE versus NYISO indicator. This is a
  market indicator, not a utility-specific fuel mix.
- Include year indicators to account for general changes affecting all utilities in
  each year.
- Cluster statistical uncertainty by utility because the same utility appears in
  multiple years. Clustering by ISO is not defensible with only two ISOs.
- Give every utility-year equal weight. Do not customer-weight the model.
- Retain accurate unusual observations. Remove a value only if the source audit shows
  that it is erroneous or incomparable.
- Leave ROI/ROE out of the draft model because the current source-audited coverage is
  limited and cooperatives do not have a directly comparable authorized shareholder
  return.
- Describe results as associations, not causal effects.

## Model structure

The draft will show three simple versions for each customer class:

1. **Baseline:** inflation-adjusted price = ownership + ISO + year.
2. **SAIDI version:** baseline variables + routine SAIDI.
3. **CAIDI alternative:** baseline variables + routine CAIDI.

SAIDI and CAIDI will not appear in the same model. CAIDI is derived from SAIDI and
SAIFI, so putting both in one equation could make the results harder to interpret and
needlessly unstable.

A small secondary analysis will treat routine SAIDI or CAIDI as the outcome:

> reliability = ownership + ISO + year

This follows the professors' suggestion that reliability may also be a dependent
variable. It remains separate from the question of whether reliability helps explain
price.

## Stage 1 — Confirm the analysis sample

### Work

- Match the existing price and reviewed reliability files by utility and year.
- Confirm ownership, state, ISO, year, and customer-class price fields.
- Apply the reliability exclusions already documented in the audit.
- Report missing values and the actual number of usable utility-years for each model.
- Confirm that the ISO assignment is NYISO for New York and ISO-NE for the New
  England states.

### Deliverable

A reproducible analysis table and a short coverage summary. Raw source files will not
be edited.

### Checkpoint

Stop if matching substantially reduces the sample or leaves an ownership group with
too little coverage. Do not compensate by silently filling missing values.

## Stage 2 — Build the baseline price models

### Work

- Run separate residential, commercial, and industrial models.
- Estimate the MTC and COOP price differences from DOM.
- Calculate 95% uncertainty ranges, p-values, overall R-squared, observations, and
  utility count.
- Use utility-clustered uncertainty and year indicators.

### Deliverable

A machine-readable results file and a plain-language summary of the three baseline
models.

### Checkpoint

Verify that each model has enough observations, that its design is mathematically
identified, and that the results reproduce when the build script is rerun.

## Stage 3 — Add the focused reliability comparisons

### Work

- Add routine SAIDI to each price model.
- Replace SAIDI with routine CAIDI in a separate alternative model.
- Compare the ownership estimates with the baseline estimates.
- Run the small secondary models with SAIDI and CAIDI as outcomes.

### Deliverable

A comparison showing whether the estimated ownership-price difference becomes
larger, smaller, or essentially unchanged when reliability is added.

### Checkpoint

Do not interpret a reliability coefficient as causal. If SAIDI and CAIDI versions
give conflicting results, report the conflict instead of selecting the preferred
result.

## Stage 4 — Run two decision checks

These checks will be kept compact and will not become additional headline models.

### State-versus-ISO check

Repeat the price models with state indicators replacing the ISO indicator. State and
ISO cannot be included together because NYISO contains the New York utilities and
ISO-NE contains the New England utilities.

If the ownership results change substantially, flag the choice of market versus state
controls as an unresolved professor decision.

### Expanded-price check

Use the existing 42-utility price-only sample as secondary context for the baseline
ownership result. Do not present it as a reliability model until reliability data for
those additional utilities are reviewed.

### Deliverable

A short “What changes under other reasonable choices?” note. These checks will be
collapsed by default on the website.

## Stage 5 — Build the separate draft page

### Page structure

1. A prominent **Draft—not final or causal** label.
2. A one-paragraph explanation of the question.
3. A customer-type selector for residential, commercial, and industrial prices.
4. A simple visual comparing the baseline, SAIDI, and CAIDI ownership estimates.
5. One plain-English finding that updates with the selected customer class.
6. The sample size, utility count, R-squared, and p-values.
7. A small reliability-as-outcome section.
8. A “What this does not prove” box.
9. Expandable model details and downloadable results for professor review.

The page will explain that a coefficient is an estimated relationship, a p-value
describes uncertainty, and R-squared measures the fit of the whole model. R-squared
will not be described as the individual contribution of a particular variable.

### Navigation

Add a **Draft panel model** link to the project overview. The observed-data overview
will remain the default landing page.

### Checkpoint

Review the new page alongside the old adjusted interface before deleting or replacing
anything.

## Stage 6 — Remove superseded presentation code

Only after the new page is verified:

- Remove the old adjusted-model interface from the main overview if it duplicates or
  conflicts with the new page.
- Replace the removed interface with a short description and link to the draft page.
- Remove JavaScript and styling that are no longer referenced.
- Keep raw data and reproducible historical result files unless they are confirmed to
  be unused generated duplicates.
- Keep the observed charts, utility histories, ROE visual evidence, regional context,
  sources, and earlier-analysis archive.

This stage is cleanup, not a redesign of the rest of the website.

## Stage 7 — Validate and hand off the draft

### Checks

- Rebuild every result from the documented source files.
- Confirm coefficients, uncertainty ranges, p-values, and R-squared calculations.
- Test all three customer-class views and both reliability measures.
- Confirm the default overview still works.
- Confirm downloads match the displayed results.
- Review every written finding against the actual numeric output.
- Publish only after the tests pass.

### Final deliverable

A working draft page that professors can use to decide:

- whether reliability belongs in the price model;
- whether SAIDI or CAIDI is the more useful measure;
- whether ISO or state controls are more appropriate;
- whether the 30-utility matched sample is adequate for the paper's purpose; and
- whether the next major investment should be distribution-tariff collection or a
  larger acquisition-based causal analysis.

## Explicitly outside this draft

- No difference-in-differences or causal ownership claim.
- No expansion before 2013.
- No new reliability collection for the 42-utility sample.
- No new distribution-tariff dataset.
- No ROE regression.
- No customer weighting, automatic outlier removal, simulation, machine learning, or
  forecasting.

Those tasks should be considered only after the professors review the draft results.
