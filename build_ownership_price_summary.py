"""Build annual ownership-level price summaries for the findings website.

The input prices are the EIA-published bundled-service prices in the processed
utility panel. This script calculates only unweighted medians and observed
minimum-to-maximum ranges. It produces both an all-published-prices view and a
transparent sensitivity view requiring at least 50% bundled-customer coverage.

Run: python3 build_ownership_price_summary.py
"""

from __future__ import annotations

import csv
import json
import statistics
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent
INPUT_FILE = PROJECT_ROOT / "data" / "processed" / "utility_price_panel_2013_2024.csv"
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "ownership_price_summary_2013_2024.csv"
SITE_CSV_OUTPUT = PROJECT_ROOT / "site" / "data" / "ownership_price_summary.csv"
SITE_JSON_OUTPUT = PROJECT_ROOT / "site" / "data" / "ownership_price_summary.json"
SITE_JS_OUTPUT = PROJECT_ROOT / "site" / "data" / "ownership_price_summary.js"

CUSTOMER_CLASSES = ("residential", "commercial", "industrial")
OWNERSHIP_TYPES = ("MTC", "DOM", "COOP")
YEARS = range(2013, 2025)
MINORITY_COVERAGE_THRESHOLD_PCT = 50.0
COVERAGE_RULES = ("all_published", "majority_coverage")

OUTPUT_FIELDS = [
    "customer_class",
    "year",
    "ownership",
    "coverage_rule",
    "coverage_threshold_pct",
    "published_price_count",
    "included_utility_count",
    "minority_coverage_count",
    "excluded_minority_coverage_count",
    "median_price_cents_kwh",
    "minimum_price_cents_kwh",
    "maximum_price_cents_kwh",
    "included_panel_ids",
    "excluded_panel_ids",
    "status",
    "calculation_note",
    "source_data",
]


def optional_float(value: str) -> float | None:
    return None if value == "" else float(value)


def load_panel() -> list[dict[str, str]]:
    with INPUT_FILE.open(newline="") as source:
        rows = list(csv.DictReader(source))
    expected = 30 * len(tuple(YEARS))
    if len(rows) != expected:
        raise ValueError(f"Expected {expected} utility-year rows; found {len(rows)}")
    return rows


def summary_row(
    rows: list[dict[str, str]],
    customer_class: str,
    year: int,
    ownership: str,
    coverage_rule: str,
) -> dict[str, object]:
    price_key = f"{customer_class}_average_price_cents_kwh"
    coverage_key = f"bundled_{customer_class}_customer_share_pct"
    group = [
        row
        for row in rows
        if int(row["year"]) == year
        and row["ownership"] == ownership
        and optional_float(row[price_key]) is not None
    ]
    minority = [
        row for row in group if float(row[coverage_key]) < MINORITY_COVERAGE_THRESHOLD_PCT
    ]
    included = (
        group
        if coverage_rule == "all_published"
        else [
            row
            for row in group
            if float(row[coverage_key]) >= MINORITY_COVERAGE_THRESHOLD_PCT
        ]
    )
    excluded = [row for row in group if row not in included]
    prices = [float(row[price_key]) for row in included]

    return {
        "customer_class": customer_class,
        "year": year,
        "ownership": ownership,
        "coverage_rule": coverage_rule,
        "coverage_threshold_pct": (
            "" if coverage_rule == "all_published" else MINORITY_COVERAGE_THRESHOLD_PCT
        ),
        "published_price_count": len(group),
        "included_utility_count": len(included),
        "minority_coverage_count": len(minority),
        "excluded_minority_coverage_count": len(excluded),
        "median_price_cents_kwh": statistics.median(prices) if prices else "",
        "minimum_price_cents_kwh": min(prices) if prices else "",
        "maximum_price_cents_kwh": max(prices) if prices else "",
        "included_panel_ids": ";".join(sorted(row["panel_id"] for row in included)),
        "excluded_panel_ids": ";".join(sorted(row["panel_id"] for row in excluded)),
        "status": "Derived",
        "calculation_note": (
            "Unweighted median and observed minimum-to-maximum range of "
            "EIA-published bundled prices; utilities are grouped by ownership "
            "in that year. Minority coverage means less than 50% of customers "
            "in the same class are bundled."
        ),
        "source_data": "data/processed/utility_price_panel_2013_2024.csv",
    }


def build_summary() -> list[dict[str, object]]:
    panel = load_panel()
    records = [
        summary_row(panel, customer_class, year, ownership, coverage_rule)
        for customer_class in CUSTOMER_CLASSES
        for coverage_rule in COVERAGE_RULES
        for year in YEARS
        for ownership in OWNERSHIP_TYPES
    ]
    expected = len(CUSTOMER_CLASSES) * len(COVERAGE_RULES) * len(YEARS) * len(OWNERSHIP_TYPES)
    if len(records) != expected:
        raise ValueError(f"Expected {expected} summary rows; created {len(records)}")
    return records


def write_outputs(records: list[dict[str, object]]) -> None:
    for output in (OUTPUT_FILE, SITE_CSV_OUTPUT):
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("w", newline="") as target:
            writer = csv.DictWriter(target, fieldnames=OUTPUT_FIELDS)
            writer.writeheader()
            writer.writerows(records)

    with SITE_JSON_OUTPUT.open("w") as target:
        json.dump(records, target, indent=2)
        target.write("\n")
    SITE_JS_OUTPUT.write_text(
        "window.NE_NY_OWNERSHIP_PRICE_SUMMARY = "
        + json.dumps(records, indent=2)
        + ";\n"
    )
    print(f"Wrote {len(records)} ownership-price summary rows")


def main() -> None:
    write_outputs(build_summary())


if __name__ == "__main__":
    main()
