# Historical schema pilot

## Result

The representative-year gate passes with an era-aware parser. The historical
price extension can begin in 2001, but the published report tables do not use
one layout across the full period.

- 2001 and 2002 publish residential, commercial, and industrial utility prices
  in Tables 14–16. State names appear as marker rows rather than as a field on
  every utility row.
- 2003 still uses Tables 14–16, but adds a two-letter state column.
- 2012 and 2013 use Tables 6–8 with the same seven-column structure used by the
  current price-panel parser.
- The detailed Form EIA-861 sales workbooks retain utility IDs, state,
  ownership, service type, revenue, sales, and customer counts in every pilot
  year.
- The fourth customer sector changes from `OTHER` in 2001–2002 to
  `TRANSPORTATION` beginning in 2003. The three modeled customer classes are
  present throughout.
- ISO/RTO fields are absent in the 2001–2003 utility files and present in the
  2012–2013 utility files. They therefore cannot define the early-period
  regional sample.

The parser reproduces all 126 current 2013 utility-sector results for the
42-utility panel. Every matched published price row also reconciles to the
corresponding detailed EIA-861 bundled revenue, sales, and customer counts.

## Coverage findings

| Year | Current IDs present | Published rows matched | Name-alias review | Lineage review |
| ---: | ---: | ---: | ---: | ---: |
| 2001 | 40 of 42 | 74 of 126 | 14 utilities | 2 utilities |
| 2002 | 41 of 42 | 112 of 126 | 1 utility | 1 utility |
| 2003 | 41 of 42 | 114 of 126 | 0 utilities | 1 utility |
| 2012 | 42 of 42 | 118 of 126 | 0 utilities | 0 utilities |
| 2013 | 42 of 42 | 118 of 126 | 0 utilities | 0 utilities |

The unmatched 2012 and 2013 utility-sector rows are genuine cases where the
published bundled table has no row, not parser failures. The 2013 missingness
exactly matches the existing validated panel.

The early-year review has two separate causes:

1. Some 2001 municipal names use a different word order in the published
   report than in the detailed file. These require name aliases, not new
   utility lineages.
2. Current utility IDs 54913 and 24590 are absent from at least one early pilot
   year. These require predecessor-ID research before a balanced historical
   panel can be built.

## Reproduce

Run:

```bash
python3 scripts/build_historical_schema_pilot.py
```

The script writes:

- `data/processed/historical_schema_pilot.csv`, the 25-row source and parser
  audit;
- `data/processed/historical_price_schema_pilot.csv`, the 630-row
  utility-year-sector pilot and 2013 overlap check.

The raw archives remain excluded from Git. Their required locations are listed
in `data/raw/README.md`.

## Next implementation step

Build the annual 2001–2024 price ingest using the three confirmed schema eras.
Before treating the panel as analysis-ready, add the 2001 name aliases and
resolve the predecessor IDs for 54913 and 24590 in the utility-lineage register.
The ownership-event search can then proceed against stable annual utility
lineages rather than names alone.

## Official sources

- EIA Electric Sales, Revenue, and Average Price:
  <https://www.eia.gov/electricity/sales_revenue_price/>
- Form EIA-861 detailed data and historical reformatted files:
  <https://www.eia.gov/electricity/data/eia861/>
