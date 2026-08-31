# Research Plan: Utility Ownership, Electricity Prices, and Related Outcomes

**Status:** Working plan for the preliminary findings website  
**Geographic scope:** New York and New England  
**Initial analysis:** Published bundled residential, commercial, and industrial average prices plus reliability  
**Current samples:** 42 utilities for regional price EDA; 30 reviewed utilities for
reliability and individual histories, 2013–2024

## 1. Purpose

The immediate deliverable is a clear, interactive website for presenting preliminary
data and findings to the professors supervising this research. It is not the final
paper and should not imply that early associations are causal results.

The broader research question is:

> Do electricity prices differ across utility ownership types in New York and New
> England, and what observable factors might help explain those differences?

Possible explanatory factors include authorized return on equity, reliability, fuel
mix, utility size, and regulatory or market context. These will be added one at a time
only after the price and ownership data are validated.

## 2. Working principles

1. **Use published data whenever it already exists.** Prefer official EIA, FERC,
   state regulator, ISO, and utility-company publications over reconstructing a
   measure independently.
2. **Do not reinvent published statistics.** For example, use EIA's published average
   retail price when available. Revenue divided by sales may be used as a validation
   check, but not presented as a novel price estimate.
3. **Keep every result traceable.** Each manually coded or collected value must have a
   source document or URL, date, and explanatory note.
4. **Separate reported, derived, and coded data.** The website and datasets should
   make clear which values came directly from a source, which are simple calculations,
   and which are research classifications.
5. **Add one analysis at a time.** Complete and validate a small result before adding
   another outcome, explanatory variable, or model.
6. **Prefer transparent summaries over complicated methods.** Use straightforward
   comparisons and conventional panel models only when the underlying data support
   them.
7. **Do not fill gaps by assumption.** Missing or ambiguous observations remain
   missing or flagged for review. They are never silently inferred.
8. **Preserve limitations.** Differences in retail-choice markets, reporting
   conventions, utility size, and regulatory treatment must be disclosed beside the
   relevant finding.

## 3. Settled scope and definitions

### Geography

The project covers utilities in:

- Connecticut
- Maine
- Massachusetts
- New Hampshire
- Rhode Island
- Vermont
- New York

### Unit of observation

The main panel unit will be the **regulated operating utility in a state and year**.
Prices, customers, reliability, and operational data should be attached to the entity
that reports those values. Ownership is assigned from that entity's ultimate parent
or public owner for the relevant year.

Utility reorganizations, mergers, name changes, and parent changes must be recorded
rather than treated as simple renames without verification.

### Ownership categories

The analytical ownership variable is limited to exactly four values:

| Code | Meaning | Coding rule |
|---|---|---|
| `MTC` | Multi-national or trans-national | Investor-owned utility whose ultimate parent is foreign or multinational |
| `DOM` | Domestic shareholder-owned / investor-owned | Investor-owned utility whose ultimate parent is based in the United States |
| `COOP` | Local cooperative / community-owned / non-shareholder | Local, municipal, member-owned, cooperative, or community-owned utility that is not shareholder-owned |
| `SOE` | State-owned enterprise | Utility owned directly by a state government or state-level public entity |

Apply the categories in this order:

1. Foreign or multinational ultimate parent: `MTC`.
2. Otherwise, investor-owned with a US parent or shareholders: `DOM`.
3. Otherwise, directly state-owned: `SOE`.
4. Otherwise, local, municipal, member-owned, cooperative, or community-owned:
   `COOP`.

The project will retain a separate `legal_ownership_description` field so that, for
example, a municipal utility can be distinguished from a legal cooperative even
though both are coded `COOP` for this analysis. No additional analytical ownership
category will be created.

### Price terminology

The first price outcome is EIA's published **average price for utility bundled retail
sales**, reported by utility and customer class in cents per kWh. The project copies
EIA's published average-price field rather than recalculating it from revenue and
sales. This is a full-service or bundled price, not an individual tariff or rate
schedule.

In states with retail choice, the utility-level bundled measure may cover only the
customers for whom that utility supplied both energy and delivery. It therefore does
not represent every customer connected to the utility's distribution system, and it
cannot be treated as every customer's complete bill. The website retains the EIA
bundled-customer count so unusually narrow coverage can be identified.

Tariff-based bills or delivery charges may be used later as supporting case studies,
but they will not be mixed with EIA average prices or treated as directly equivalent.

## 4. Data provenance standard

Every analytical field will be labeled internally as one of:

- **Reported:** copied from an official published source.
- **Derived:** a transparent calculation from reported fields, such as a median,
  inflation adjustment, percentage change, or customer-weighted mean.
- **Coded:** a research classification, such as ownership type, based on documented
  source evidence.

Manually collected data should use the following minimum schema:

| Field | Description |
|---|---|
| `utility_id_eia` | EIA identifier when available |
| `utility_name` | Regulated operating utility |
| `parent_name` | Ultimate parent or public owner |
| `state` | State associated with the observation |
| `year` | Reporting year, if applicable |
| `effective_date` | Effective date for decisions or tariffs |
| `variable` | Name of the collected measure |
| `value` | Reported value |
| `unit` | Percent, dollars, minutes, etc. |
| `source_title` | Title of filing, decision, report, or webpage |
| `source_url` | Direct source URL when available |
| `source_page_or_table` | Page, table, schedule, or docket reference |
| `retrieved_date` | Date the source was accessed |
| `notes` | Interpretation, ambiguity, or carry-forward treatment |
| `review_status` | Unreviewed, verified, or needs follow-up |

User-scraped data will be imported through a documented CSV or spreadsheet using this
structure. Source documents should be retained when licensing and repository size
make that appropriate.

## 5. Existing work and how it will be used

The repository currently contains a 2020–2024 exploratory website for four operating
utilities. It includes:

- Direct generation reported by each utility
- NYISO and ISO-NE generation mix
- Residential EIA sales-revenue comparisons
- Manually assembled residential base-delivery tariff examples

This work will be preserved as **Previous exploratory findings** rather than used as
the main ownership comparison. Its principal contribution is showing that direct
utility-owned generation can differ substantially from the regional electricity mix
from which distribution utilities obtain power.

The existing code and charts may be reused when accurate, but older labels,
methodology, and source references must be reconciled with this plan before appearing
in the revised presentation.

## 6. Phased research workflow

Each phase should produce a reviewable dataset, validation summary, and website
section before the next phase begins.

### Phase 1: Residential price comparison and panel structure — complete

**Question:** How do published bundled residential prices vary across selected
utilities and ownership types in New York and New England?

Tasks:

1. Obtain EIA's published utility-level bundled residential average price, bundled
   customer count, utility identifier, and state.
2. Exclude power marketers and entities that are not comparable retail distribution
   utilities, using an explicit and saved inclusion rule.
3. Create a documented ownership crosswalk for the remaining utilities.
4. Check duplicates, missing values, unexpected units, and category counts.
5. Present individual utilities first, with group summaries as supporting results.

Initial summaries:

- Number of utilities and customers by ownership category
- Median residential price by ownership category
- Customer-weighted mean residential price by ownership category
- Range and distribution of individual utility prices

These are descriptive findings. They will not be labeled causal.

### Phase 2: Extend prices by customer class and evaluate comparability — data complete

After Phase 1 is verified:

**Current coverage result:** The website now contains EIA-published bundled prices
from Table 6 (residential), Table 7 (commercial), and Table 8 (industrial). Prices are
available for 347 of 360 residential and commercial utility-years and 324 industrial
utility-years. Missing published prices remain blank. All 1,018 populated price-table
customer counts match PUDL exactly. Bundled
coverage remains a separate data-quality metric beside price.

1. Add commercial and industrial average prices as separate outcomes. **Complete.**
2. Compare bundled-customer coverage with each utility's total distribution customer
   count, especially in retail-choice states. **Complete in the website:** exact
   coverage remains visible and published prices below 50% are flagged without being
   changed or removed from the primary view.
3. Assess whether published utility-level bundled prices are sufficiently comparable
   for the main analysis or should be supplemented with regulator/utility bill data.
4. Assess missing years and decide whether a minimum-coverage rule is necessary.
   **Sensitivity implemented:** the ownership comparison can switch between all
   published prices and a project-defined majority-coverage sample requiring at least
   50%. This is not presented as an EIA quality standard.
5. **Complete in the website overview:** allow price medians to switch between the
   published nominal cents and constant 2024 cents using the annual CPI-U. This does
   not alter the underlying EIA values or the within-year ownership ranking.

### Phase 3: Reliability

Add government-published utility reliability measures:

- SAIFI
- SAIDI
- CAIDI

Reporting conventions, including major-event-day and IEEE-standard status, must be
retained. Values with incompatible definitions will not be pooled without a clearly
documented standardization rule.

**Current audit result:** The EIA/PUDL reliability table contains a populated row for
321 of the 360 selected utility-years. Peabody and Fishers Island have no populated
rows in this period; the current FirstEnergy entity is blank before 2024; Taunton is
missing 2013–2015; and Central Hudson is missing 2014. Some populated rows omit
individual measures. Six utilities change between IEEE and other
reporting methods during the panel. These exceptions are preserved in
`data/processed/reliability_coverage_audit_2013_2024.csv` and documented in
`docs/reliability-coverage-audit.md`. SAIDI, SAIFI, and CAIDI are now available in the
website utility panels. The default excludes major events, the alternate view
includes them, missing years remain blank, and reporting-method changes are marked.
The ownership overview adds simple annual unweighted medians with usable-utility
counts; these are labeled descriptive because reporting methods can differ.
All 2,841 comparable fields in the 2013–2024 official EIA workbooks match the PUDL
extract. Targeted regulator checks found source conflicts for NSTAR in 2017 and
2023. The raw EIA/PUDL values remain in the audit, but the affected measures are
withheld from the website charts and later analysis.

### Phase 4: Potential explanations

Add candidate explanations separately rather than all at once:

1. ISO-level annual fuel mix for NYISO and ISO-NE. **Complete as regional
   context:** the website now shows 2013–2024 EIA-923 plant generation grouped by
   annual NYIS and ISNE balancing-authority assignments. Imports and
   utility-specific purchases are explicitly excluded from the interpretation.
2. Utility size and customer composition from existing government data
3. Authorized return on equity for investor-owned utilities. **Six-utility pilot
   complete:** the 2013-2024 source-audited table now includes a `DOM`/`MTC` pair
   under the same regulator in Connecticut (CL&P and UI), Massachusetts (NSTAR and
   Massachusetts Electric), and New York (Con Edison and NYSEG). Base ROE, in-force
   penalties, actual earned ROE, and decision-year dollar inputs remain separate.
4. Utility-owned generation assets when ownership and annual coverage are reliable

Authorized ROE will come from regulator decisions, rate cases, or utility filings.
It is not applicable to `COOP` and `SOE` utilities and must not be entered as zero.
The user may collect these documents manually using the provenance template above.

### Phase 5: Preliminary panel models

The first descriptive panel has been checked. The first ownership-price model is now
implemented and documented in `docs/statistical-models.md`. It is deliberately
conventional and easy to explain:

- Ownership-price associations with separate state and year controls
- Standard errors clustered by utility
- Unweighted primary estimates, so every usable utility-year counts once
- A separate majority-coverage sensitivity check, without adding model weights
- Separate models for residential, commercial, and industrial prices

Because ownership is generally stable over time, a utility fixed-effects model cannot
serve as the primary ownership comparison: fixed effects would absorb the ownership
category. Fixed-effects models may be used separately for questions involving changes
within the same utility.

The ROE mechanism analysis should focus on the `MTC` and `DOM` investor-owned subset.
All model results will be labeled preliminary associations unless the eventual paper
develops a defensible causal identification strategy.

## 7. Findings website plan

The website should resemble a concise academic research presentation rather than a
feature-heavy business dashboard.

### Presentation goals

- State the research question immediately.
- Put the most important finding above the fold.
- Allow professors to inspect individual utilities behind group summaries.
- Keep definitions, sources, sample sizes, and limitations close to each chart.
- Avoid decorative metrics, unnecessary animation, and controls that do not help
  answer the research question.

### Initial Phase 1 page

The first complete page will contain:

1. **Header:** research question and "preliminary findings" status.
2. **Scope:** 2013–2024 bundled residential, commercial, and industrial service in
   New York and New England.
3. **Primary interactive chart:** a three-row small-multiples matrix, with one row
   each for `MTC`, `DOM`, and `COOP`, and ten fixed utility panels per ownership
   group in a two-by-five grid. Each utility panel shows the full 2013–2024 time
   series.
4. **Ownership comparison:** before the individual utility panels, show three
   ownership summary charts using annual unweighted medians and observed minimum-to-
   maximum ranges. Provide separate customer-class and coverage-sensitivity controls.
   Flag annual medians that include at least one minority-coverage observation.
5. **Comparison rules:** keep a common vertical scale across all utilities for the
   selected metric. Keep utilities in fixed positions based on their 2024 category;
   mark ownership changes inside the relevant utility panel rather than moving the
   panel between rows.
6. **Row and panel context:** show the selected-sample utility count and available
   2024 observations beside each ownership-row heading. Put the annual ownership
   medians and ranges in the dedicated comparison above rather than repeating a weak
   one-year summary in every row. Put state, EIA ID, 2024 parent or owner,
   and ownership-history notes directly inside each utility panel rather than in a
   separate long roster.
7. **Metric controls:** use one page-level customer-type selector for residential,
   commercial, and industrial views, plus one measure selector that switches all 30
   panels together between bundled price, bundled customer coverage, SAIFI, SAIDI,
   and CAIDI. Reliability includes a separate major-event treatment control.
8. **Point details:** lead with year and exact value. For prices and coverage, show
   the relevant bundled-customer count; for reliability, show reporting method and
   reported reliability-customer count. Keep repeated ownership and source-audit
   language in the surrounding panel and methods text.
9. **Interpretation:** short description of the visible pattern without causal
   language.
10. **Methods and sources:** inclusion rule, field definitions, source links, and known
   limitations.
11. **Previous exploratory findings:** link or expandable section preserving the
   current four-utility generation work.

Later sections will be added only when their datasets are ready. The site should not
display empty or speculative pages for reliability, ROE, or regression findings.

### Visual character

- Clean, restrained, and readable on a projector
- Clear type hierarchy and generous spacing
- Consistent ownership colors across every chart
- Direct labels where possible
- Accessible contrast and keyboard-readable controls
- Plain-language annotations instead of dense statistical notation
- Downloadable data and direct source links

The existing static HTML, CSS, JavaScript, and Chart.js architecture is adequate unless
a concrete limitation appears. A new framework is not required for the planned
interactivity.

## 8. Quality checks before publishing a finding

For every website section:

1. Confirm the source is official or explain why a secondary source was necessary.
2. Preserve the original downloaded data separately from processed data.
3. Record the retrieval date and dataset version or reporting year.
4. Validate units and definitions against the source documentation.
5. Check utility IDs, names, states, mergers, and duplicates.
6. Document inclusion and exclusion decisions.
7. Report sample sizes and missingness.
8. Reconcile derived values against published totals when possible.
9. Ensure chart text does not overstate descriptive findings.
10. Keep the transformation code reproducible and covered by focused tests.

## 9. Items intentionally deferred

The following are not required for the first website result:

- A causal claim about ownership
- Full-sample authorized ROE collection beyond the four-utility matched-state pilot
- Utility-owned generation allocation
- Tariff scraping for every utility
- Complex econometric specifications
- Forecasting or machine learning
- A redesign requiring a front-end framework

## 10. Immediate next milestone

The immediate milestone is to present and review the first ownership-price model with
faculty. Keep the selected-sample price result and the small ROE comparison separate
from causal language. Expand the model only if the faculty discussion identifies a
specific missing explanation worth testing.

Reliability remains available as a descriptive outcome. The flagged Eversource
observations have been reviewed and the affected measures withheld. IEEE and
Non-IEEE observations should remain visibly distinguished and should not be pooled
as if their reporting definitions were identical.
