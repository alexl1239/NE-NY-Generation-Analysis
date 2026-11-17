#!/usr/bin/env python3
"""Build browser-ready data for the full historical-extension page."""

from __future__ import annotations

import csv
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PRICE_INPUT = (
    PROJECT_ROOT / "data" / "processed" / "utility_price_history_2001_2024.csv"
)
DESIGN_INPUT = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "ownership_research_design_events_2001_2024.csv"
)
CONTROL_INPUT = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "ownership_research_design_control_pool_2001_2024.csv"
)
SITE_DATA = PROJECT_ROOT / "site" / "data"
EXTENSION_YEAR_START = 2001
EXTENSION_YEAR_END = 2024

# BLS annual CPI-U, all items, U.S. city average, rebased to 2013 = 100.
# The 2013-2024 values exactly match the existing project price model.
CPI_U_ANNUAL_2013_100 = {
    2001: 76.023,
    2002: 77.225,
    2003: 78.985,
    2004: 81.088,
    2005: 83.835,
    2006: 86.540,
    2007: 89.004,
    2008: 92.422,
    2009: 92.093,
    2010: 93.604,
    2011: 96.558,
    2012: 98.556,
    2013: 100.000,
    2014: 101.622,
    2015: 101.743,
    2016: 103.027,
    2017: 105.221,
    2018: 107.791,
    2019: 109.745,
    2020: 111.098,
    2021: 116.318,
    2022: 125.626,
    2023: 130.797,
    2024: 134.655,
}

PRICE_CSV = SITE_DATA / "november_extension_price_history.csv"
PRICE_JSON = SITE_DATA / "november_extension_price_history.json"
PRICE_JS = SITE_DATA / "november_extension_price_history.js"
DESIGN_CSV = SITE_DATA / "november_extension_research_design.csv"
DESIGN_JSON = SITE_DATA / "november_extension_research_design.json"
DESIGN_JS = SITE_DATA / "november_extension_research_design.js"
CONTROL_CSV = SITE_DATA / "november_extension_control_pool.csv"

PRICE_FIELDS = [
    "panel_id",
    "current_utility_id_eia",
    "display_name",
    "state",
    "year",
    "customer_class",
    "ownership_class",
    "ultimate_parent_or_owner",
    "bundled_customers",
    "bundled_sales_mwh",
    "bundled_revenue_thousand_usd",
    "average_price_cents_kwh",
    "territory_comparability_status",
    "source_status",
    "price_method",
    "source_url",
]

DESIGN_FIELDS = [
    "event_id",
    "transaction_id",
    "treated_panel_id",
    "treated_utility",
    "treated_state",
    "treated_market",
    "customer_class",
    "closing_date",
    "year_end_treatment_year",
    "first_full_treatment_year",
    "old_ownership_class",
    "new_ownership_class",
    "phase5_readiness_status",
    "phase6_window_role",
    "selected_pre_years",
    "selected_post_years",
    "treated_min_bundled_customers_selected_years",
    "treated_customer_base_screen_status",
    "eligible_control_count",
    "tier_1_same_state_count",
    "tier_2_same_market_count",
    "tier_3_cross_market_count",
]

NUMERIC_PRICE_FIELDS = {
    "current_utility_id_eia",
    "year",
    "bundled_customers",
    "bundled_sales_mwh",
    "bundled_revenue_thousand_usd",
    "average_price_cents_kwh",
}
NUMERIC_DESIGN_FIELDS = {
    "year_end_treatment_year",
    "first_full_treatment_year",
    "treated_min_bundled_customers_selected_years",
    "eligible_control_count",
    "tier_1_same_state_count",
    "tier_2_same_market_count",
    "tier_3_cross_market_count",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as source:
        return list(csv.DictReader(source))


def select_fields(
    rows: list[dict[str, str]], fields: list[str]
) -> list[dict[str, str]]:
    return [{field: row[field] for field in fields} for row in rows]


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {path}")


def json_rows(
    rows: list[dict[str, str]], numeric_fields: set[str]
) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for row in rows:
        converted: dict[str, object] = {}
        for field, value in row.items():
            if field not in numeric_fields:
                converted[field] = value
            elif value == "":
                converted[field] = None
            elif field in {
                "current_utility_id_eia",
                "year",
                "year_end_treatment_year",
                "first_full_treatment_year",
                "eligible_control_count",
                "tier_1_same_state_count",
                "tier_2_same_market_count",
                "tier_3_cross_market_count",
            }:
                converted[field] = int(float(value))
            else:
                converted[field] = float(value)
        output.append(converted)
    return output


def write_payload(
    json_path: Path,
    js_path: Path,
    global_name: str,
    metadata: dict[str, object],
    records: list[dict[str, object]],
) -> None:
    payload = {"metadata": metadata, "records": records}
    serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    json_path.write_text(serialized + "\n", encoding="utf-8")
    js_path.write_text(f"window.{global_name} = {serialized};\n", encoding="utf-8")
    print(f"Wrote {len(records)} records to {json_path} and {js_path}")


def main() -> None:
    SITE_DATA.mkdir(parents=True, exist_ok=True)
    price_source = read_csv(PRICE_INPUT)
    design_source = read_csv(DESIGN_INPUT)
    control_source = read_csv(CONTROL_INPUT)

    if len(price_source) != 42 * 24 * 3:
        raise ValueError(f"Expected 3,024 historical price rows; found {len(price_source)}")
    if len(design_source) != 27:
        raise ValueError(f"Expected 27 research-design rows; found {len(design_source)}")
    if len(control_source) != 756:
        raise ValueError(f"Expected 756 control evaluations; found {len(control_source)}")

    extension_price_source = [
        row
        for row in price_source
        if EXTENSION_YEAR_START <= int(row["year"]) <= EXTENSION_YEAR_END
    ]
    extension_design_source = [
        row
        for row in design_source
        if int(row["year_end_treatment_year"]) <= EXTENSION_YEAR_END
    ]
    extension_event_ids = {row["event_id"] for row in extension_design_source}
    extension_control_source = [
        row for row in control_source if row["event_id"] in extension_event_ids
    ]

    if len(extension_price_source) != 42 * 24 * 3:
        raise ValueError(
            "Expected 3,024 full-period price rows; "
            f"found {len(extension_price_source)}"
        )
    if len(extension_design_source) != 27:
        raise ValueError(
            "Expected 27 full-period research-design rows; "
            f"found {len(extension_design_source)}"
        )
    if len(extension_control_source) != 756:
        raise ValueError(
            "Expected 756 full-period control evaluations; "
            f"found {len(extension_control_source)}"
        )

    price_rows = select_fields(extension_price_source, PRICE_FIELDS)
    design_rows = select_fields(extension_design_source, DESIGN_FIELDS)
    write_csv(PRICE_CSV, PRICE_FIELDS, price_rows)
    write_csv(DESIGN_CSV, DESIGN_FIELDS, design_rows)

    with CONTROL_CSV.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(
            target,
            fieldnames=list(extension_control_source[0]),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(extension_control_source)
    print(f"Wrote {len(extension_control_source)} rows to {CONTROL_CSV}")

    write_payload(
        PRICE_JSON,
        PRICE_JS,
        "NE_NY_NOVEMBER_EXTENSION_PRICE_HISTORY",
        {
            "title": "Extended historical data price history",
            "year_start": EXTENSION_YEAR_START,
            "year_end": EXTENSION_YEAR_END,
            "utility_count": 42,
            "customer_classes": ["residential", "commercial", "industrial"],
            "price_definition": "EIA bundled average revenue per kWh in nominal cents",
            "constant_dollar_year": 2024,
            "cpi_u_annual_2013_100": CPI_U_ANNUAL_2013_100,
            "inflation_formula": "published price multiplied by CPI-U(2024) divided by CPI-U(year)",
            "published_price_count": sum(
                row["average_price_cents_kwh"] != "" for row in price_rows
            ),
        },
        json_rows(price_rows, NUMERIC_PRICE_FIELDS),
    )
    write_payload(
        DESIGN_JSON,
        DESIGN_JS,
        "NE_NY_NOVEMBER_EXTENSION_RESEARCH_DESIGN",
        {
            "title": "Extended historical data research-design review",
            "year_end": EXTENSION_YEAR_END,
            "ownership_change_count": len(extension_event_ids),
            "event_sector_rows": len(design_rows),
            "primary_rows": sum(
                row["phase6_window_role"] == "primary_4_year_window"
                for row in design_rows
            ),
            "sensitivity_rows": sum(
                row["phase6_window_role"] == "sensitivity_2_year_window"
                for row in design_rows
            ),
            "excluded_rows": sum(
                row["phase6_window_role"].startswith("excluded_")
                for row in design_rows
            ),
            "causal_estimates_included": False,
        },
        json_rows(design_rows, NUMERIC_DESIGN_FIELDS),
    )


if __name__ == "__main__":
    main()
