# Phase 6: research-design inputs and potential controls

Phase 6 converts the reviewed ownership events into fixed pre/post windows and
evaluates every utility in the 42-utility roster as a potential comparison. It
does not estimate an ownership effect, use price movements to choose controls,
or update the website.

## Event-sector roles

Every ownership change continues to be reviewed separately for residential,
commercial, and industrial prices.

- **Primary:** four consecutive price years before the closing year and four
  beginning with the first full post-closing year.
- **Sensitivity:** the same construction with the shorter two-year window
  available for Narragansett Electric's 2022 transaction.
- **Excluded:** no control pool is built when the price window is insufficient
  or the published bundled price represents an extremely thin customer base.

The closing year remains outside both price periods because it combines part
of the year under the old owner with part under the new owner.

The resulting 27 event-sector rows contain:

- 15 primary four-year-window rows;
- 3 short-window sensitivity rows; and
- 9 excluded rows.

The 15 primary rows are residential, commercial, and industrial observations
for Green Mountain Power, NYSEG, Rochester Gas & Electric, Central Hudson, and
United Illuminating. Narragansett Electric's three sectors remain sensitivity
rows because only 2023 and 2024 are complete post-closing years.

## Customer-base screen

Phase 5 checked whether a price was published continuously. Phase 6 also checks
whether that bundled price represents more than an extremely small number of
customers. The screen requires more than 100 bundled customers in every
selected residential or commercial year and more than 5 in every selected
industrial year.

This is a practical extreme-thinness rule, not a statistical-significance
cutoff. It prevents a price based on a handful of customers from being called a
utility-wide primary outcome.

The screen changes two Phase 5 classifications. Central Maine Power has a
continuous residential and commercial price series around its 2008 ownership
change, but the selected residential years contain as few as 27 bundled
customers and the commercial years as few as 6. Both rows are therefore
excluded from the Phase 6 primary design. CMP's industrial row was already
excluded because its immediate price series is missing.

No other primary treated row fails this screen. Green Mountain Power's
industrial series is the smallest retained treated industrial case, with at
least 24 bundled industrial customers in the selected window.

## Potential-control rule

For each of the 18 primary or sensitivity event-sector rows, all 42 roster
utilities are evaluated. A utility enters the potential-control pool only when
all of the following are true:

1. It is not affected by the same transaction.
2. Its ownership class stays constant and matches the treated utility's class
   before the transaction.
3. It has no reviewed ownership, parent, identity, consolidation, or territory
   event during the full event span.
4. Its recorded parent, identity basis, and territory basis remain stable.
5. It has a published price in every selected year for the same customer
   class.
6. It passes the same extreme-thinness customer-base screen.

The script records every failed rule instead of silently dropping the utility.
The pool is not a final matched control group. No price level, price change, or
post-event outcome is used to determine eligibility.

## Geographic tiers

Eligible controls are organized without removing broader alternatives:

1. **Tier 1:** same state as the treated utility;
2. **Tier 2:** same regional market, but a different state; and
3. **Tier 3:** the other regional market in the NY/New England sample.

New York utilities are assigned to NYISO. Utilities in Connecticut, Maine,
Massachusetts, New Hampshire, Rhode Island, and Vermont are assigned to ISO-NE.

Across all 18 event-sector designs, there are 132 eligible control-candidate
rows: 27 same-state, 39 same-market, and 66 cross-market. These are repeated
event-specific evaluations, not 132 different utilities. Each primary design
has between 5 and 8 eligible controls; each Narragansett sensitivity design has
between 9 and 10.

## Files

- `data/processed/ownership_research_design_events_2001_2024.csv` contains one
  row for every reviewed ownership event and customer class, including the
  selected window, customer-base screen, and control-pool counts.
- `data/processed/ownership_research_design_control_pool_2001_2024.csv` contains
  every one of the 756 event-sector-control evaluations and the explicit reason
  for each inclusion or exclusion.
- `scripts/build_research_design_inputs.py` rebuilds both tables from the Phase
  5 event review, annual ownership history, and historical price panel.
- `tests/test_research_design_inputs.py` checks event roles, window timing,
  customer-base rules, control eligibility, geographic tiers, and the absence
  of outcome-based matching.

## Phase 7 handoff

Phase 7 adds an Extended Historical Data website page for the full 2001-2024 panel.
It summarizes historical prices, annual ownership, and event-window readiness
without selecting a final statistical specification or making a causal claim.
See `docs/november-data-extension-phase-7.md`.
