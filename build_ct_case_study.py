#!/usr/bin/env python3
"""Build the matched-state price-and-authorized-ROE website dataset."""

from __future__ import annotations

import csv
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
PRICE_PATH = PROJECT_ROOT / "data" / "processed" / "utility_price_panel_2013_2024.csv"
ROE_PATH = PROJECT_ROOT / "data" / "processed" / "roe_annual_pilot_2013_2024.csv"
SOURCE_PATH = PROJECT_ROOT / "data" / "processed" / "roe_source_register.csv"
SITE_DATA_DIR = PROJECT_ROOT / "site" / "data"

UTILITY_IDS = {4176, 19497, 54913, 11804, 4226, 13511}
OUTPUT_FIELDS = [
    "panel_id",
    "utility_id_eia",
    "display_name",
    "state",
    "year",
    "ownership",
    "residential_average_price_cents_kwh",
    "residential_bundled_customer_share_pct",
    "commercial_average_price_cents_kwh",
    "commercial_bundled_customer_share_pct",
    "industrial_average_price_cents_kwh",
    "industrial_bundled_customer_share_pct",
    "price_source_report",
    "price_source_url",
    "price_retrieved_date",
    "residential_price_source_table",
    "commercial_price_source_table",
    "industrial_price_source_table",
    "coverage_source_url",
    "coverage_flag_rule",
    "base_authorized_roe",
    "performance_adjustment_bps",
    "effective_authorized_roe",
    "actual_earned_roe",
    "actual_minus_effective_bps",
    "approved_equity_ratio",
    "approved_rate_base_million_usd",
    "authorized_equity_return_million_usd",
    "approved_distribution_revenue_requirement_million_usd",
    "equity_return_share_of_revenue_requirement",
    "docket",
    "roe_source_ids",
    "roe_primary_source_title",
    "roe_primary_source_url",
    "roe_primary_source_location",
    "actual_roe_source_ids",
    "roe_source_status",
    "roe_annualization_note",
    "ownership_source_ids",
    "ownership_source_url",
    "ownership_history_source_url",
    "ownership_history_note",
]

NUMERIC_FIELDS = {
    "utility_id_eia": int,
    "year": int,
    "residential_average_price_cents_kwh": float,
    "residential_bundled_customer_share_pct": float,
    "commercial_average_price_cents_kwh": float,
    "commercial_bundled_customer_share_pct": float,
    "industrial_average_price_cents_kwh": float,
    "industrial_bundled_customer_share_pct": float,
    "base_authorized_roe": float,
    "performance_adjustment_bps": float,
    "effective_authorized_roe": float,
    "actual_earned_roe": float,
    "actual_minus_effective_bps": float,
    "approved_equity_ratio": float,
    "approved_rate_base_million_usd": float,
    "authorized_equity_return_million_usd": float,
    "approved_distribution_revenue_requirement_million_usd": float,
    "equity_return_share_of_revenue_requirement": float,
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def optional_number(value: str, converter):
    return None if value == "" else converter(value)


def build_rows() -> list[dict[str, object]]:
    source_by_id = {
        row["source_id"]: row
        for row in read_csv(SOURCE_PATH)
    }
    prices = {
        (int(row["utility_id_eia"]), int(row["year"])): row
        for row in read_csv(PRICE_PATH)
        if int(row["utility_id_eia"]) in UTILITY_IDS
    }
    roe_rows = [
        row for row in read_csv(ROE_PATH)
        if int(row["utility_id_eia"]) in UTILITY_IDS
    ]
    assert len(prices) == 72
    assert len(roe_rows) == 72

    output = []
    for roe in roe_rows:
        key = (int(roe["utility_id_eia"]), int(roe["year"]))
        price = prices[key]
        primary_source_id = roe["source_ids"].split(";")[0].strip()
        primary_source = source_by_id[primary_source_id]
        combined = {
            "panel_id": price["panel_id"],
            "utility_id_eia": roe["utility_id_eia"],
            "display_name": roe["display_name"],
            "state": roe["state"],
            "year": roe["year"],
            "ownership": roe["ownership"],
            "residential_average_price_cents_kwh": price["residential_average_price_cents_kwh"],
            "residential_bundled_customer_share_pct": price["bundled_residential_customer_share_pct"],
            "commercial_average_price_cents_kwh": price["commercial_average_price_cents_kwh"],
            "commercial_bundled_customer_share_pct": price["bundled_commercial_customer_share_pct"],
            "industrial_average_price_cents_kwh": price["industrial_average_price_cents_kwh"],
            "industrial_bundled_customer_share_pct": price["bundled_industrial_customer_share_pct"],
            "price_source_report": price["source_report"],
            "price_source_url": price["source_url"],
            "price_retrieved_date": price["retrieved_date"],
            "residential_price_source_table": price["residential_source_table"],
            "commercial_price_source_table": price["commercial_source_table"],
            "industrial_price_source_table": price["industrial_source_table"],
            "coverage_source_url": price["coverage_source_url"],
            "coverage_flag_rule": price["coverage_flag_rule"],
            "base_authorized_roe": roe["base_authorized_roe"],
            "performance_adjustment_bps": roe["performance_adjustment_bps"],
            "effective_authorized_roe": roe["effective_authorized_roe"],
            "actual_earned_roe": roe["actual_earned_roe"],
            "actual_minus_effective_bps": roe["actual_minus_effective_bps"],
            "approved_equity_ratio": roe["approved_equity_ratio"],
            "approved_rate_base_million_usd": roe["approved_rate_base_million_usd"],
            "authorized_equity_return_million_usd": roe["authorized_equity_return_million_usd"],
            "approved_distribution_revenue_requirement_million_usd": roe["approved_distribution_revenue_requirement_million_usd"],
            "equity_return_share_of_revenue_requirement": roe["equity_return_share_of_revenue_requirement"],
            "docket": roe["docket"],
            "roe_source_ids": roe["source_ids"],
            "roe_primary_source_title": primary_source["source_title"],
            "roe_primary_source_url": primary_source["source_url"],
            "roe_primary_source_location": primary_source["source_location"],
            "actual_roe_source_ids": roe["actual_roe_source_ids"],
            "roe_source_status": roe["source_status"],
            "roe_annualization_note": roe["annualization_note"],
            "ownership_source_ids": roe["ownership_source_ids"],
            "ownership_source_url": price["ownership_source_url"],
            "ownership_history_source_url": price["ownership_history_source_url"],
            "ownership_history_note": price["ownership_history_note"],
        }
        for field, converter in NUMERIC_FIELDS.items():
            combined[field] = optional_number(str(combined[field]), converter)
        output.append(combined)

    output.sort(key=lambda row: (int(row["utility_id_eia"]), int(row["year"])))
    expected_keys = {
        (utility_id, year)
        for utility_id in UTILITY_IDS
        for year in range(2013, 2025)
    }
    assert {(row["utility_id_eia"], row["year"]) for row in output} == expected_keys
    return output


def write_outputs(rows: list[dict[str, object]]) -> None:
    SITE_DATA_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = SITE_DATA_DIR / "roe_case_study.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    js_path = SITE_DATA_DIR / "roe_case_study.js"
    js_path.write_text(
        "window.NE_NY_ROE_CASE_STUDY = "
        + json.dumps(rows, ensure_ascii=False, separators=(",", ":"))
        + ";\n",
        encoding="utf-8",
    )

    source_rows = read_csv(SOURCE_PATH)
    source_output = SITE_DATA_DIR / "roe_source_register.csv"
    with source_output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=source_rows[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(source_rows)


def main() -> None:
    rows = build_rows()
    write_outputs(rows)
    print(f"Wrote {len(rows)} matched-state utility-year rows")


if __name__ == "__main__":
    main()
