# Phase 7: Extended Historical Data website page

## Purpose

The Extended Historical Data page follows the fixed 42-utility roster from 2001
through 2024. It combines the newly added early history with the latest reviewed
project year in one continuous presentation.

The page is descriptive. It does not run a new regression or claim that an
ownership change caused a price change.

The price-basis control switches every chart between published nominal EIA
bundled average revenue per kWh and inflation-adjusted 2024 cents. The
inflation adjustment uses the same annual BLS CPI-U series and formula as the
existing price model.

## What the page shows

- the original 42-utility roster from 2001 through 2024;
- 2,903 published bundled-price observations across residential, commercial,
  and industrial customers;
- interactive annual median prices by the ownership class that applied in each
  year, including group size and observed range;
- an interactive utility history whose points report the exact price, bundled
  customers, ownership class, and parent; and
- a short sourced explanation for each of the nine reviewed ownership changes.

The nine changes are Versant Power in 2001, Niagara Mohawk in 2002, Green
Mountain Power in 2007, Central Maine Power in 2008, NYSEG in 2008, Rochester
Gas & Electric in 2008, Central Hudson in 2013, United Illuminating in 2015,
and Rhode Island Energy in 2022.

## Page-specific exports

The files in `site/data/november_extension_*` contain the full historical page
inputs:

- 3,024 possible utility-year-customer rows for 2001-2024, including explicit
  missing prices;
- 27 ownership-event/customer-class review rows for the nine changes; and
- 756 potential-control audit rows for the 18 event/customer-class windows
  that passed the Phase 6 readiness screen.

## Rebuild and verify

```bash
python3 scripts/build_november_extension_site.py
python3 -m unittest tests.test_november_extension_site
node --check site/november-data-extension.js
```

The page is `site/november-data-extension.html`. The main overview, price, and
reliability pages link to it in their navigation.
