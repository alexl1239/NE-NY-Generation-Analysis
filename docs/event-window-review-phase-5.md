# Phase 5: ownership-event window review

Phase 5 checks whether each clean ownership change has enough consecutive
published-price observations before and after the transaction for later
research-design work. It does not estimate an ownership effect, select a
control group, or update the website.

## Readiness rule

The review uses the first full calendar year after closing as the first
post-event year. The closing year is excluded from both sides because it mixes
the old and new owners within one annual price observation.

Each utility and customer class is classified separately:

- **Ready:** at least four consecutive published-price years immediately before
  the closing year and at least four beginning with the first full post-closing
  year.
- **Limited:** at least two consecutive years on both sides, but fewer than four
  on one side.
- **Insufficient:** fewer than two consecutive years on either side.

Four years is a practical data-readiness screen for examining pre-event trends
and several post-event years. It is not a statistical-significance cutoff and
does not by itself make an event causal.

## Findings

The nine clean utility-event rows produce 27 utility-sector reviews across
seven transactions:

- 17 utility-sector rows are ready.
- 3 are limited.
- 7 are insufficient.

Three transactions are ready in all three reviewed customer classes:

1. Gaz Metro's 2007 acquisition of Green Mountain Power.
2. Fortis's 2013 acquisition of Central Hudson.
3. Iberdrola's 2015 acquisition of UIL Holdings, including United Illuminating.

Iberdrola's 2008 acquisition of Energy East is ready for eight of its nine
utility-sector rows. Central Maine Power's industrial series is not ready
because no published bundled industrial price exists immediately before or
after the event. The later reappearance of that series is not used to bridge
the gap.

PPL's 2022 acquisition of Narragansett Electric is limited because only 2023
and 2024 are complete post-closing years. The Bangor Hydro 2001 and Niagara
Mohawk 2002 acquisitions are not ready because the panel contains no clean
multi-year pre-event window after excluding the closing year.

## Files

- `data/processed/ownership_event_window_review_2001_2024.csv` contains one row
  for each clean utility event and customer class.
- `data/processed/ownership_transaction_window_summary_2001_2024.csv` summarizes
  the seven distinct transactions without hiding mixed sector coverage.
- `scripts/build_event_window_review.py` rebuilds both tables from the reviewed
  ownership events and Phase 4 price panel.
- `tests/test_event_window_review.py` checks timing, counts, classifications,
  gaps, and source links.

## Phase 6 status

Phase 6 constructed the fixed event windows and evaluated all 42 utilities as
potential controls under explicit ownership, event, data-continuity, customer-
base, identity, and territory rules. The customer-base review also found that
Central Maine Power's apparently continuous residential and commercial series
around 2008 represent extremely few bundled customers, so those rows are not
promoted to the primary design. See
[`research-design-phase-6.md`](research-design-phase-6.md).

Phase 7 can now prepare professor-facing descriptive tables and the
website-ready historical data package without estimating causal effects.
