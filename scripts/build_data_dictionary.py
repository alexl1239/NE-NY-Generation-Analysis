#!/usr/bin/env python3
"""Build the professor-facing CSV inventory and field-level data dictionary."""

from __future__ import annotations

import argparse
import csv
import io
import re
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from rebuild_project import PROJECT_ROOT, required_inputs


DICTIONARY_CSV = PROJECT_ROOT / "docs" / "data-dictionary.csv"
DICTIONARY_MD = PROJECT_ROOT / "docs" / "data-dictionary.md"

IDENTIFIER_FIELDS = {
    "event_id",
    "ownership_source_id",
    "panel_id",
    "source_id",
    "utility_id_eia",
}

DESCRIPTIONS = {
    "panel_id": "Stable project identifier used to join the same utility across project files.",
    "utility_id_eia": "EIA-assigned utility identifier; this is an identifier, not a measured quantity.",
    "utility_name_eia": "Utility name as published by EIA.",
    "display_name": "Short utility name used on the website.",
    "state": "Two-letter U.S. state abbreviation for the observation.",
    "year": "Calendar or report year represented by the row.",
    "report_date": "Report year from the standardized PUDL source.",
    "ownership": "Ownership category assigned for the row's year: MTC, DOM, SOE, or COOP.",
    "ownership_2024": "Ownership category assigned as of 2024: MTC, DOM, SOE, or COOP.",
    "legal_ownership_description": "Legal ownership form retained separately from the four-category analytical code.",
    "ownership_time_varies_2013_2024": "Flag showing whether the project's ownership category changes during 2013–2024.",
    "residential_average_price_cents_kwh": "Published residential average revenue per kilowatt-hour, in nominal cents per kWh.",
    "commercial_average_price_cents_kwh": "Published commercial average revenue per kilowatt-hour, in nominal cents per kWh.",
    "industrial_average_price_cents_kwh": "Published industrial average revenue per kilowatt-hour, in nominal cents per kWh.",
    "real_residential_price_2024_cents_kwh": "Residential average price converted to constant 2024 cents per kWh for modeling.",
    "real_commercial_price_2024_cents_kwh": "Commercial average price converted to constant 2024 cents per kWh for modeling.",
    "real_industrial_price_2024_cents_kwh": "Industrial average price converted to constant 2024 cents per kWh for modeling.",
    "reliability_customers": "Customers included in the utility's reported reliability calculation.",
    "routine_saidi_minutes": "SAIDI excluding major-event days after the documented source-audit exclusions are applied.",
    "routine_saidi_per_100_minutes": "Routine SAIDI divided by 100 for model coefficient scaling.",
    "reporting_standard": "Reliability method reported for the row: IEEE, another standard, or missing.",
    "standard": "Reliability method in the standardized PUDL source.",
    "saidi_w_major_event_days_minutes": "System Average Interruption Duration Index including major-event days, in minutes per customer.",
    "saidi_wo_major_event_days_minutes": "System Average Interruption Duration Index excluding major-event days, in minutes per customer.",
    "saifi_w_major_event_days_customers": "System Average Interruption Frequency Index including major-event days, in interruptions per customer.",
    "saifi_wo_major_event_days_customers": "System Average Interruption Frequency Index excluding major-event days, in interruptions per customer.",
    "caidi_w_major_event_days_minutes": "Customer Average Interruption Duration Index including major-event days, in minutes per interruption.",
    "caidi_wo_major_event_days_minutes": "Customer Average Interruption Duration Index excluding major-event days, in minutes per interruption.",
    "included_primary_model": "Boolean flag showing whether the row enters the primary reliability model.",
    "analysis_use": "Row-level reliability use category assigned by the audit rules.",
    "analysis_excluded_fields": "Semicolon-delimited fields withheld from analysis after documented source review.",
    "official_eia_validation_status": "Result of comparing the standardized row with the official annual EIA workbook.",
    "fields_compared": "Number of populated reliability fields compared with the official EIA workbook.",
    "mismatch_count": "Number of compared fields that differ from the official EIA workbook.",
    "validation_status": "Summary result of the official-source comparison.",
    "balancing_authority_code_eia": "EIA balancing-authority code used to assign regional generation.",
    "fuel": "Fuel group used in the regional generation chart.",
    "net_generation_mwh": "Annual net electricity generation in megawatt-hours.",
    "share_pct": "Fuel's share of the year's positive generation total, in percent.",
    "positive_generation_total_mwh": "Sum of the nonnegative fuel groups used as the share denominator, in megawatt-hours.",
    "excluded_nonpositive_generation_mwh": "Zero or negative generation excluded from the 100% chart stack but retained for audit.",
    "base_authorized_roe": "Regulator-approved return on equity before a separately stated applicable adjustment.",
    "performance_adjustment_bps": "Applicable annual authorized-ROE adjustment in basis points; one basis point is 0.01 percentage point.",
    "effective_authorized_roe": "Base authorized ROE plus the documented adjustment applicable to the row.",
    "actual_earned_roe": "Realized return on equity reported in an official filing; it is not substituted for authorized ROE.",
    "approved_equity_ratio": "Approved common-equity share of the capital structure.",
    "approved_rate_base_million_usd": "Approved rate base for the cited rate year, in millions of U.S. dollars.",
    "authorized_equity_return_million_usd": "Derived rate base times equity ratio times effective authorized ROE, in millions of U.S. dollars.",
    "approved_distribution_revenue_requirement_million_usd": "Approved annual distribution revenue requirement, in millions of U.S. dollars.",
    "source_ids": "Semicolon-delimited source identifiers that resolve to the ROE source register.",
    "source_id": "Unique identifier for one record in the ROE source register.",
    "source_url": "URL recorded for the cited source.",
    "eia_source_file_url": "URL of the official annual EIA source archive.",
    "pudl_source_url": "URL of the standardized PUDL source or data access route.",
    "retrieved_date": "Date the frozen source extract was retrieved.",
}

UNIT_RULES = (
    ("_million_usd", "million USD"),
    ("_cents_kwh", "cents per kWh"),
    ("_pct", "percent"),
    ("_mwh", "MWh"),
    ("_gwh", "GWh"),
    ("_minutes", "minutes"),
    ("_bps", "basis points"),
    ("_kv", "kilovolts"),
)


def dictionary_csv_paths() -> list[Path]:
    """Return every CSV that will be described and delivered in the handoff."""
    paths = set(PROJECT_ROOT.glob("data/manual/*.csv"))
    paths.update(PROJECT_ROOT.glob("data/processed/*.csv"))
    paths.update(PROJECT_ROOT.glob("site/data/*.csv"))
    paths.update(path for path in required_inputs() if path.suffix.lower() == ".csv")
    return sorted(path for path in paths if path.is_file())


def role_for(path: Path) -> str:
    relative = path.relative_to(PROJECT_ROOT).as_posix()
    if relative.startswith("data/raw/"):
        return "Frozen source input"
    if relative.startswith("data/manual/"):
        return "Manually reviewed cross-check"
    if relative.startswith("data/processed/"):
        return "Analysis-ready output"
    if relative.startswith("site/data/"):
        return "Browser-ready copy"
    raise ValueError(f"Unrecognized data role: {relative}")


def read_csv(path: Path) -> tuple[list[str], list[list[str]]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.reader(handle))
    if not rows:
        raise ValueError(f"CSV is empty: {path.relative_to(PROJECT_ROOT)}")
    header, body = rows[0], rows[1:]
    if len(header) != len(set(header)):
        raise ValueError(f"Duplicate headers: {path.relative_to(PROJECT_ROOT)}")
    for row_number, row in enumerate(body, start=2):
        if len(row) != len(header):
            raise ValueError(
                f"Ragged row in {path.relative_to(PROJECT_ROOT)} at line {row_number}: "
                f"expected {len(header)} fields, found {len(row)}"
            )
    return header, body


def parse_decimal(value: str) -> Decimal | None:
    try:
        return Decimal(value)
    except InvalidOperation:
        return None


def observed_type(field: str, values: list[str]) -> str:
    nonmissing = [value.strip() for value in values if value.strip()]
    if field in IDENTIFIER_FIELDS:
        return "identifier"
    if not nonmissing:
        return "empty"
    lowered = {value.lower() for value in nonmissing}
    if lowered <= {"true", "false"}:
        return "boolean"
    if all(re.fullmatch(r"[+-]?\d+", value) for value in nonmissing):
        return "integer"
    if all(parse_decimal(value) is not None for value in nonmissing):
        return "number"
    if all(re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) for value in nonmissing):
        return "date"
    return "text"


def unit_for(field: str) -> str:
    if field in {"year", "report_date", "start_year", "end_year"}:
        return "year"
    if field in {"base_authorized_roe", "effective_authorized_roe", "actual_earned_roe", "approved_equity_ratio", "equity_return_share_of_revenue_requirement"}:
        return "proportion (1.0 = 100%)"
    if field.startswith("saifi_"):
        return "interruptions per customer"
    for suffix, unit in UNIT_RULES:
        if field.endswith(suffix):
            return unit
    return ""


def description_for(field: str) -> str:
    if field in DESCRIPTIONS:
        return DESCRIPTIONS[field]
    label = field.replace("_", " ")
    if field.startswith("included_"):
        return f"Boolean flag showing whether the row is included for {label.removeprefix('included ')}."
    if field.endswith("_url"):
        return f"URL recorded for {label.removesuffix(' url')}."
    if field.endswith("_source_ids"):
        return f"Source identifiers recorded for {label.removesuffix(' source ids')}."
    if field.endswith("_status"):
        return f"Categorical status for {label.removesuffix(' status')}."
    if field.endswith("_flag"):
        return f"Categorical flag for {label.removesuffix(' flag')}."
    if field.endswith("_note"):
        return f"Text note about {label.removesuffix(' note')}."
    if field.endswith("_count"):
        return f"Count of {label.removesuffix(' count')}."
    return f"Column for {label}."


def clean_example(value: str) -> str:
    value = re.sub(r"\s+", " ", value.strip())
    return value if len(value) <= 90 else value[:87] + "..."


def summarize_values(field: str, values: list[str]) -> dict[str, str | int]:
    stripped = [value.strip() for value in values]
    nonmissing = [value for value in stripped if value]
    kind = observed_type(field, values)
    minimum = ""
    maximum = ""
    if kind in {"integer", "number"} and nonmissing:
        decimals = [Decimal(value) for value in nonmissing]
        minimum = format(min(decimals), "f")
        maximum = format(max(decimals), "f")
    elif kind == "date" and nonmissing:
        parsed = [date.fromisoformat(value) for value in nonmissing]
        minimum = min(parsed).isoformat()
        maximum = max(parsed).isoformat()

    examples: list[str] = []
    for value in nonmissing:
        example = clean_example(value)
        if example not in examples:
            examples.append(example)
        if len(examples) == 3:
            break

    return {
        "observed_type": kind,
        "nonmissing_count": len(nonmissing),
        "missing_count": len(stripped) - len(nonmissing),
        "unique_count": len(set(nonmissing)),
        "observed_min": minimum,
        "observed_max": maximum,
        "example_values": " | ".join(examples),
    }


def build_outputs() -> tuple[str, str]:
    inventory: list[dict[str, object]] = []
    dictionary_rows: list[dict[str, object]] = []

    for path in dictionary_csv_paths():
        header, rows = read_csv(path)
        relative = path.relative_to(PROJECT_ROOT).as_posix()
        role = role_for(path)
        inventory.append(
            {
                "dataset_path": relative,
                "dataset_role": role,
                "row_count": len(rows),
                "column_count": len(header),
            }
        )
        for index, field in enumerate(header, start=1):
            profile = summarize_values(field, [row[index - 1] for row in rows])
            dictionary_rows.append(
                {
                    "dataset_path": relative,
                    "dataset_role": role,
                    "row_count": len(rows),
                    "field_order": index,
                    "field_name": field,
                    "description": description_for(field),
                    "unit": unit_for(field),
                    **profile,
                }
            )

    fieldnames = [
        "dataset_path",
        "dataset_role",
        "row_count",
        "field_order",
        "field_name",
        "description",
        "unit",
        "observed_type",
        "nonmissing_count",
        "missing_count",
        "unique_count",
        "observed_min",
        "observed_max",
        "example_values",
    ]
    csv_buffer = io.StringIO(newline="")
    writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(dictionary_rows)

    md_lines = [
        "# Data dictionary",
        "",
        "This dictionary is generated from the CSV files included in the professor handoff. It records each file's actual headers, row count, observed data type, missing-value count, range, and examples. The field-level table is in [`data-dictionary.csv`](data-dictionary.csv).",
        "",
        "Run `python3 scripts/build_data_dictionary.py --check` to confirm that the dictionary still matches every delivered CSV. The check fails if a file, field, row count, or observed value profile changes without rebuilding the dictionary.",
        "",
        "## Key definitions",
        "",
        "The analytical ownership rule is applied in this order:",
        "",
        "1. `MTC`: investor-owned utility with a foreign or multinational ultimate parent.",
        "2. `DOM`: investor-owned utility with a U.S.-based ultimate parent or shareholders. DOM is the model reference category.",
        "3. `SOE`: utility owned directly by a state government or state-level public entity.",
        "4. `COOP`: local, municipal, member-owned, cooperative, or community-owned utility that is not shareholder-owned.",
        "",
        "No utility in either selected sample is coded SOE. `legal_ownership_description` retains the legal form so municipal utilities remain distinguishable from member-owned cooperatives inside the broader COOP category. Annual ownership is the owner in place on December 31 of the row's year.",
        "",
        "- `SAIDI`: average outage-duration minutes per customer.",
        "- `SAIFI`: average outage interruptions per customer.",
        "- `CAIDI`: average minutes per interruption, derived in the standardized PUDL table as SAIDI divided by SAIFI.",
        "- `routine`: excludes major-event days.",
        "- Blank cells remain missing. The build does not replace an unavailable value with zero.",
        "",
        "## How to read the field-level CSV",
        "",
        "`observed_type`, counts, ranges, and examples describe the frozen files in this package. They do not claim that future versions of an upstream source must have the same range. Numeric EIA identifiers are labeled as identifiers so they are not mistaken for measurements.",
        "",
        "## Delivered CSV inventory",
        "",
        "| File | Role | Rows | Columns |",
        "| --- | --- | ---: | ---: |",
    ]
    for item in inventory:
        md_lines.append(
            f"| `{item['dataset_path']}` | {item['dataset_role']} | "
            f"{item['row_count']:,} | {item['column_count']:,} |"
        )
    md_lines.extend(
        [
            "",
            "## Interpretation notes",
            "",
            "The price and reliability samples are selected project panels, not random samples of every utility in the region. The models show associations rather than causal effects. Regional fuel mix and the matched-state authorized-ROE pilot are supplementary context, not explanatory variables in the headline models.",
            "",
            "For the rules behind each field, use [`statistical-models.md`](statistical-models.md), [`reliability-coverage-audit.md`](reliability-coverage-audit.md), [`iso-fuel-mix-methodology.md`](iso-fuel-mix-methodology.md), and [`ct-roe-pilot-methodology.md`](ct-roe-pilot-methodology.md).",
            "",
        ]
    )
    return csv_buffer.getvalue(), "\n".join(md_lines)


def check_current(expected_csv: str, expected_md: str) -> None:
    stale: list[str] = []
    for path, expected in ((DICTIONARY_CSV, expected_csv), (DICTIONARY_MD, expected_md)):
        if not path.is_file() or path.read_text(encoding="utf-8") != expected:
            stale.append(path.relative_to(PROJECT_ROOT).as_posix())
    if stale:
        raise SystemExit(
            "Data dictionary is missing or stale:\n- " + "\n- ".join(stale) +
            "\nRun: python3 scripts/build_data_dictionary.py"
        )
    print(f"Data dictionary check passed: {len(dictionary_csv_paths())} CSV files match.")


def write_outputs(csv_text: str, md_text: str) -> None:
    DICTIONARY_CSV.parent.mkdir(parents=True, exist_ok=True)
    DICTIONARY_CSV.write_text(csv_text, encoding="utf-8")
    DICTIONARY_MD.write_text(md_text, encoding="utf-8")
    print(f"Wrote {DICTIONARY_CSV.relative_to(PROJECT_ROOT)}")
    print(f"Wrote {DICTIONARY_MD.relative_to(PROJECT_ROOT)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if the saved dictionary does not match the delivered CSV files",
    )
    args = parser.parse_args()
    csv_text, md_text = build_outputs()
    if args.check:
        check_current(csv_text, md_text)
    else:
        write_outputs(csv_text, md_text)


if __name__ == "__main__":
    main()
