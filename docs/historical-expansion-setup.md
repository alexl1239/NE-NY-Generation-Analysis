# Historical expansion setup

## Working conclusion

Use **2001-2024** as the initial target period for the ownership-price extension.
Form EIA-861 contains utility-level sales, revenue, customer, and identity data
before 2001, but 2001 is the earliest common boundary for the following sources:

- Excel editions of EIA's utility-level Electric Sales, Revenue, and Average
  Price tables;
- EIA-861 service-territory records; and
- PUDL's standardized EIA-861 annual sales data.

The first build will preserve the validated 2013-2024 panel and add earlier
years alongside it. It will not overwrite the existing processed files until
the overlap reproduces the current results.

## Files created for the expansion

- `data/manual/historical_source_coverage.csv` records source availability,
  schema breaks, intended uses, and required checks.
- `data/manual/ownership_events.csv` records one affected utility per ownership
  transaction. It begins with four events already supported by primary sources.
- `data/manual/utility_lineage.csv` provides the stable identifiers needed to
  connect utility names and EIA IDs across transactions and consolidations.

The ownership and lineage files are review registers. Analysis-ready annual
ownership rows will be generated from them after the historical review.

## Ownership timing rules

Each event retains two treatment dates:

1. `year_end_treatment_year` follows the existing project rule and assigns the
   owner in place on December 31.
2. `first_full_treatment_year` begins with the first complete calendar year
   after closing and is the preferred timing for annual-price causal models.

Keeping both prevents a transaction that closes late in a year from treating
the entire year's price outcome as post-acquisition.

The register also distinguishes `parent_changed` from
`ownership_class_changed`. A foreign parent changing to another foreign parent
is a real ownership event even when the MTC category remains unchanged.

## Scope decisions

- Price, revenue, sales, customers, utility identity, service territory, and
  ownership history are part of the first historical build.
- Reliability remains a 2013-forward supplemental outcome because EIA's
  reliability schedule begins in 2013.
- ISO/RTO fields do not define the pre-2010 sample because EIA added those fields
  in 2010. Earlier regional inclusion will use state and service-territory data.
- Years before 2001 remain a possible later extension. They require separate
  handling of PDF tables and older raw-file schemas.

## Representative-year gate completed

The 2001, 2002, 2003, 2012, and 2013 schema pilot is complete. It confirms
three published-table layouts, stable utility IDs and service-type fields in
the detailed files, the 2003 sector-definition change, and exact reproduction
of all current 2013 utility-sector results. See
[`historical-schema-pilot.md`](historical-schema-pilot.md) for the findings.

The early-year identity review, ownership-change register, and annual
2001-2024 price ingest are complete. The Phase 4 build uses the reviewed
identity instructions, ownership timing, and territory warnings rather than
assuming that every current EIA ID represents an unchanged service territory.
See [`historical-price-panel-phase-4.md`](historical-price-panel-phase-4.md).
The event-window and research-design reviews are now complete through Phase 6.
They identify usable treated utility-sector rows and transparent potential-
control pools without estimating causal effects. See
[`research-design-phase-6.md`](research-design-phase-6.md).

## Official source pages

- EIA-861 detailed data: <https://www.eia.gov/electricity/data/eia861/>
- Electric Sales, Revenue, and Average Price:
  <https://www.eia.gov/electricity/sales_revenue_price/>
- PUDL data sources: <https://docs.catalyst.coop/pudl/en/stable/data_sources/>
- BLS CPI-U annual history:
  <https://www.bls.gov/regions/northeast/data/consumerpriceindex_us_table.htm>
