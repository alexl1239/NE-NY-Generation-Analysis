# Matched-State Authorized-ROE Pilot

**Status:** Preliminary source-audited pilot
**Utilities:** CL&P and United Illuminating in Connecticut; NSTAR and Massachusetts Electric in Massachusetts; Con Edison and NYSEG in New York
**Years:** 2013-2024
**Regulators:** Connecticut Public Utilities Regulatory Authority (PURA), Massachusetts Department of Public Utilities (DPU), and New York Public Service Commission (PSC)

## Purpose

This pilot tests a practical way to investigate the professors' proposed shareholder-return mechanism before collecting rate cases for the full investor-owned sample. It places one domestic investor-owned utility and one multinational-owned utility under the same regulator in each of three states. The within-state pairing keeps regulatory and market context more similar than a cross-state comparison.

The pilot does not test whether return on equity causes higher customer prices. It first establishes which regulatory quantities can be collected consistently and what each one means.

## Variables

- `base_authorized_roe` is the regulator-approved return on the equity-funded share of rate base before a separately stated penalty or adjustment.
- `performance_adjustment_bps` records a penalty only when the record supports applying it to that annual observation. One basis point is 0.01 percentage point.
- `effective_authorized_roe` is calculated as base authorized ROE plus the applicable basis-point adjustment.
- `actual_earned_roe` is the utility's realized return reported in an official filing. It is not substituted for authorized ROE.
- `approved_equity_ratio` is the shareholder-funded share of the approved capital structure.
- `approved_rate_base_million_usd` is the rate base reported for the particular rate year in a decision.
- `authorized_equity_return_million_usd` is a derived authorized common-equity return component:

  `approved rate base × approved equity ratio × effective authorized ROE`

  This is not shareholder compensation or dividends, a retail price, a bill, or the utility's total profit.
- `approved_distribution_revenue_requirement_million_usd` is the annual distribution revenue requirement reported for a particular rate year.

## Time assignment

The annual table records the authorized rate in force at the end of each calendar year. This is a transparent first-pass convention, not an annual average. A mid-year decision is therefore assigned to that year with an explanatory note.

The website pairs this year-end ROE snapshot with EIA's full-calendar-year average price only as a simple descriptive check. The two measures are not treated as perfectly time-aligned.

Decision-year dollar inputs remain attached to the specific rate year reported in the source. They are not silently carried forward. A blank means not found, not reported for that year, or not applicable; it never means zero.

## Treatment of storm-response penalties

The 2014 CL&P decision imposed a temporary 15-basis-point reduction for one year. Company filings show that the reduction affected 2015 and ended for 2016, so the annual series records 9.02% effective ROE for 2015 and returns to the 9.17% base rate in 2016.

PURA's 2021 Tropical Storm Isaias order required future-proceeding reductions of 90 basis points for Eversource and 15 basis points for UI. The order did not immediately replace the ROE then in force. Those values are therefore retained in the event register but are not subtracted from the 2021 annual observations.

UI's August 2023 final decision is treated separately. The controlling final decision used a 9.10% base ROE, 47 basis points of combined adjustments, and an 8.63% effective ROE. Earlier proposed-final materials cited different figures and are not used in the annual series.

## Ownership

CL&P, NSTAR, and Con Edison are coded `DOM` throughout the pilot. Massachusetts Electric and NYSEG are coded `MTC` throughout. UI is coded `DOM` through 2015 and `MTC` from 2016, following the project's existing annual ownership convention after the Iberdrola/UIL combination closed in December 2015. The displayed matched pairs use each utility's 2024 ownership.

## Source hierarchy

The source register prioritizes:

1. PURA, Massachusetts DPU, and New York PSC final decisions and official regulator pages.
2. State consumer advocate and attorney general filings.
3. SEC-filed utility disclosures.
4. Official company ownership materials.

Each annual row and event uses source IDs that resolve to a source location. The former company-hosted copy of PURA Docket 16-06-04 now returns a 404, so the website uses a stable SEC filing to corroborate the 9.10% ROE and 50% equity ratio. The official PURA final-decision database remains the audit route for the decision's detailed rate-year tables.

## What is ready and what remains

Ready:

- A 72-row annual pilot for six utilities from 2013 through 2024.
- A separate event register so future orders are not confused with rates already in force.
- Base, effective, and actual ROE kept as distinct concepts.
- Formula-derived equity-return components only where official rate base and equity-share inputs are available.

Not yet ready:

- A claim that ROE explains the observed retail-price difference.
- A representative comparison of all `MTC` and `DOM` utilities.
- A complete decomposition of customer bills into supply, delivery, taxes, and other components.
- A regression using ROE.

The three matched-state comparisons are ready to present as preliminary evidence. A wider ROE panel should be collected only if ROE becomes a central variable in the later statistical model.
