# Phase 3: ownership-change history

Phase 3 turns the original four ownership examples into a reviewed event
register for the fixed 42-utility sample. It also assigns a parent and ownership
class to every utility-year from 2001 through 2024. This phase does not build
prices, estimate effects, or update the website.

## What was completed

- Reviewed 20 utility-event rows representing 18 distinct transactions or
  consolidations.
- Linked every event to a company, regulator, or SEC source.
- Built 1,008 annual ownership rows: 42 utilities by 24 years.
- Kept the year-end ownership rule: the owner in place on December 31 is the
  owner for that calendar year, while the following year is the first complete
  post-closing year.
- Separated clean ownership-class changes from same-class parent changes,
  legal consolidations, and acquired predecessor territories.

## The clean ownership-class changes

There are nine clean utility-event rows representing seven transactions:

1. Emera acquired Bangor Hydro in 2001.
2. National Grid acquired Niagara Mohawk in 2002.
3. Gaz Metro acquired Green Mountain Power in 2007.
4. Iberdrola acquired Energy East in 2008, changing the parent of NYSEG,
   Central Maine Power, and Rochester Gas & Electric.
5. Fortis acquired Central Hudson in 2013.
6. Iberdrola acquired UIL Holdings, including United Illuminating, in 2015.
7. PPL acquired Narragansett Electric, now Rhode Island Energy, in 2022.

“Clean” here has a narrow meaning: the parent and ownership class changed while
the utility ID and service territory did not. It means the row is eligible for
later research design review, not that it automatically proves a causal effect.
The 2001 Bangor and 2002 Niagara Mohawk events have very short pre-event windows
inside a 2001-forward panel, which will limit their usefulness in later models.

## Other real changes that should not be pooled with the clean cases

Four events changed the parent without changing the ownership class:

- Energy East acquired RGS Energy and RG&E in 2002: DOM to DOM.
- Northeast Utilities and NSTAR combined in 2012: DOM to DOM.
- Algonquin acquired Granite State Electric from National Grid in 2012:
  MTC to MTC.
- ENMAX acquired Emera Maine, later renamed Versant Power, in 2020:
  MTC to MTC.

Seven additional rows change a legal identity, service territory, or absorbed
predecessor. They remain in the register because they matter for data
comparability, but they are not clean ownership comparisons.

## Territory changes found during the review

The current EIA ID alone does not reproduce a fixed 2024 service territory in
three cases:

- Green Mountain Power later absorbed Central Vermont Public Service.
- Versant's predecessor Bangor Hydro later absorbed Maine Public Service.
- Vermont Electric Cooperative materially expanded by acquiring Citizens'
  Vermont electric division.

These are now explicit in `utility_lineage.csv` and in the annual ownership
table's `territory_comparability_status`. Citizens appears in the official
2001-2002 EIA retail files but is absent from the 2003 reformatted file, so the
project does not force a 2003 predecessor match. Phase 4 should compare both
the reported-entity approach and a fixed-territory aggregation where the
official records support it.

## Files

- `data/manual/ownership_events.csv` — one row for each utility affected by a
  reviewed transaction or consolidation.
- `data/manual/ownership_event_sources.csv` — the official source register.
- `data/processed/utility_ownership_history_2001_2024.csv` — one owner record
  for each utility and year.
- `scripts/build_ownership_history.py` — rebuilds and validates all three
  Phase 3 tables.
- `tests/test_ownership_history.py` — checks timing, event classification,
  sources, annual completeness, and territory warnings.

## Phase 4 status

Phase 4 extracted the annual price, revenue, sales, and customer records and
applied the identity instructions and territory warnings recorded here. See
[`historical-price-panel-phase-4.md`](historical-price-panel-phase-4.md). The
website remains on the existing 2013-2024 data until the later website-update
phase.
