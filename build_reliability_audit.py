"""Build a reliability coverage audit for the 30 selected utilities.

The underlying SAIDI and SAIFI values are reported by utilities on Form EIA-861.
This script reads PUDL's standardized ``core_eia861__yearly_reliability`` table,
preserves PUDL's reported/derived fields, and creates one row for every selected
utility-year from 2013 through 2024. Missing observations remain missing.

The processed audit is also bundled for the local findings website after preserving
missing observations and reporting-definition flags.

Run: python3 build_reliability_audit.py
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import duckdb
import pandas as pd

from build_price_panel import load_candidates, ownership_for, parent_for


PROJECT_ROOT = Path(__file__).parent
RAW_CACHE_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "eia861"
    / "pudl_reliability_top10_2013_2024.csv"
)
OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "reliability_coverage_audit_2013_2024.csv"
)
DIRECT_VALIDATION_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "reliability_source_validation_2013_2024.csv"
)
INDEPENDENT_CHECK_FILE = (
    PROJECT_ROOT
    / "data"
    / "manual"
    / "reliability_independent_checks.csv"
)
SITE_CSV_OUTPUT = PROJECT_ROOT / "site" / "data" / "reliability_panel.csv"
SITE_JSON_OUTPUT = PROJECT_ROOT / "site" / "data" / "reliability_panel.json"
SITE_JS_OUTPUT = PROJECT_ROOT / "site" / "data" / "reliability_panel.js"

YEAR_START = 2013
YEAR_END = 2024
RETRIEVED_DATE = "2026-08-08"

EIA_SOURCE_PAGE = "https://www.eia.gov/electricity/data/eia861/"
PUDL_DOCUMENTATION_URL = (
    "https://catalystcoop-pudl.readthedocs.io/en/stable/"
    "data_sources/eia861.html"
)
PUDL_RELIABILITY_URL = (
    "https://s3.us-west-2.amazonaws.com/pudl.catalyst.coop/stable/"
    "core_eia861__yearly_reliability.parquet"
)

METRIC_FIELDS = [
    "saidi_w_major_event_days_minutes",
    "saidi_wo_major_event_days_minutes",
    "saidi_w_major_event_days_minus_loss_of_service_minutes",
    "saifi_w_major_event_days_customers",
    "saifi_wo_major_event_days_customers",
    "saifi_w_major_event_days_minus_loss_of_service_customers",
    "caidi_w_major_event_days_minutes",
    "caidi_wo_major_event_days_minutes",
    "caidi_w_major_event_days_minus_loss_of_service_minutes",
]

DISPLAY_METRIC_FIELDS = [
    "saidi_w_major_event_days_minutes",
    "saidi_wo_major_event_days_minutes",
    "saifi_w_major_event_days_customers",
    "saifi_wo_major_event_days_customers",
    "caidi_w_major_event_days_minutes",
    "caidi_wo_major_event_days_minutes",
]

RAW_FIELDS = [
    "report_date",
    "utility_id_eia",
    "utility_name_eia",
    "state",
    "standard",
    "customers",
    "entity_type",
    "short_form",
    "highest_distribution_voltage_kv",
    "inactive_accounts_included",
    "momentary_interruption_definition",
    "outages_recorded_automatically",
    *METRIC_FIELDS,
    "data_maturity",
]

OUTPUT_FIELDS = [
    "panel_id",
    "utility_id_eia",
    "utility_name_eia",
    "display_name",
    "state",
    "year",
    "ownership",
    "ownership_2024",
    "parent_or_owner",
    "parent_country_or_level",
    "reliability_row_status",
    "reporting_standard",
    "standard_changed_during_panel",
    "comparability_status",
    "reliability_customers",
    "entity_type",
    "short_form",
    "highest_distribution_voltage_kv",
    "inactive_accounts_included",
    "momentary_interruption_definition",
    "outages_recorded_automatically",
    *METRIC_FIELDS,
    "reported_metric_count",
    "display_metrics_complete",
    "caidi_source_status",
    "official_eia_validation_status",
    "analysis_use",
    "analysis_excluded_fields",
    "independent_crosscheck_status",
    "independent_crosscheck_scope",
    "independent_crosscheck_saidi",
    "independent_crosscheck_saifi",
    "independent_crosscheck_caidi",
    "independent_crosscheck_customer_count",
    "independent_crosscheck_source_title",
    "independent_crosscheck_source_url",
    "independent_crosscheck_additional_source_url",
    "independent_crosscheck_source_location",
    "independent_crosscheck_note",
    "review_status",
    "quality_note",
    "source_status",
    "source_report",
    "source_schedule",
    "eia_source_page",
    "eia_source_file_url",
    "pudl_source_url",
    "pudl_documentation_url",
    "data_maturity",
    "retrieved_date",
]


def eia_source_file_url(year: int) -> str:
    """Return the official annual EIA-861 archive URL."""
    if year == YEAR_END:
        return "https://www.eia.gov/electricity/data/eia861/zip/f8612024.zip"
    return (
        "https://www.eia.gov/electricity/data/eia861/archive/zip/"
        f"f861{year}.zip"
    )


def load_raw_reliability(candidates: list[dict[str, str]]) -> pd.DataFrame:
    """Load and locally cache the selected rows from PUDL's EIA-861 table."""
    if RAW_CACHE_FILE.exists():
        raw = pd.read_csv(RAW_CACHE_FILE)
    else:
        utility_ids = ", ".join(candidate["utility_id_eia"] for candidate in candidates)
        query = f"""
            SELECT {", ".join(RAW_FIELDS)}
            FROM read_parquet('{PUDL_RELIABILITY_URL}')
            WHERE EXTRACT(YEAR FROM report_date) BETWEEN {YEAR_START} AND {YEAR_END}
              AND utility_id_eia IN ({utility_ids})
            ORDER BY utility_id_eia, report_date, state, standard
        """
        raw = duckdb.connect().execute(query).df()
        RAW_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        raw.to_csv(RAW_CACHE_FILE, index=False)
        print(f"Cached {len(raw)} filtered PUDL rows at {RAW_CACHE_FILE}")

    missing_columns = set(RAW_FIELDS) - set(raw.columns)
    if missing_columns:
        raise ValueError(
            f"Reliability cache is missing columns: {sorted(missing_columns)}"
        )

    raw["report_date"] = pd.to_datetime(raw["report_date"])
    raw["year"] = raw["report_date"].dt.year.astype(int)
    raw["utility_id_eia"] = raw["utility_id_eia"].astype(int)
    return raw


def is_active_source_row(row: pd.Series) -> bool:
    """Identify the populated standard row in PUDL's two-row layout."""
    fields = ["customers", *METRIC_FIELDS]
    return any(pd.notna(row[field]) for field in fields)


def python_value(value: object) -> object:
    """Convert pandas missing/scalar values to CSV-safe Python values."""
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def comparability_status(
    active_row: pd.Series | None,
    standard_changed: bool,
) -> str:
    if active_row is None:
        return "missing"
    if standard_changed:
        return "reporting_standard_changes_during_panel"
    if active_row["standard"] == "ieee_standard":
        return "consistent_ieee_standard"
    return "consistent_other_standard"


def load_direct_validation() -> dict[tuple[int, int], str]:
    """Load the reproducible official EIA-to-PUDL comparison results."""
    if not DIRECT_VALIDATION_FILE.exists():
        return {}
    validation = pd.read_csv(DIRECT_VALIDATION_FILE)
    required = {
        "utility_id_eia",
        "year",
        "validation_status",
        "mismatch_count",
    }
    missing = required - set(validation.columns)
    if missing:
        raise ValueError(f"Direct validation file is missing columns: {sorted(missing)}")
    if validation.duplicated(["utility_id_eia", "year"]).any():
        raise ValueError("Direct validation file contains duplicate utility-years")
    if validation["mismatch_count"].fillna(0).astype(int).ne(0).any():
        raise ValueError("Direct validation file contains official EIA/PUDL mismatches")
    return {
        (int(row.utility_id_eia), int(row.year)): str(row.validation_status)
        for row in validation.itertuples(index=False)
    }


def load_independent_checks() -> dict[tuple[int, int], dict[str, object]]:
    """Load regulator/utility checks used for targeted analysis flags."""
    checks = pd.read_csv(INDEPENDENT_CHECK_FILE, keep_default_na=False)
    required = {
        "utility_id_eia",
        "year",
        "crosscheck_status",
        "analysis_excluded_fields",
        "source_scope",
        "source_saidi",
        "source_saifi",
        "source_caidi",
        "source_customer_count",
        "source_title",
        "source_url",
        "additional_source_url",
        "source_location",
        "source_note",
    }
    missing = required - set(checks.columns)
    if missing:
        raise ValueError(
            f"Independent reliability checks are missing columns: {sorted(missing)}"
        )
    if checks.duplicated(["utility_id_eia", "year"]).any():
        raise ValueError("Independent reliability checks contain duplicate utility-years")
    return {
        (int(row["utility_id_eia"]), int(row["year"])): row.to_dict()
        for _, row in checks.iterrows()
    }


def analysis_use_status(
    active_row: pd.Series | None,
    standard_changed: bool,
    independent_check: dict[str, object] | None,
) -> str:
    if active_row is None:
        return "missing_in_source"
    if independent_check and independent_check["analysis_excluded_fields"]:
        return "source_conflict_with_targeted_exclusions"
    if any(pd.isna(active_row[field]) for field in DISPLAY_METRIC_FIELDS):
        return "descriptive_only_incomplete_metrics"
    if standard_changed:
        return "descriptive_only_reporting_standard_change"
    if active_row["standard"] == "other_standard":
        return "descriptive_only_non_ieee_method"
    return "ready_for_descriptive_use"


def independent_number(
    independent_check: dict[str, object] | None,
    field: str,
) -> float | None:
    if not independent_check:
        return None
    value = str(independent_check[field]).strip()
    return float(value) if value else None


def quality_fields(
    active_row: pd.Series | None,
    standard_changed: bool,
    independent_check: dict[str, object] | None,
) -> tuple[str, str]:
    """Return a review status and factual audit note for one utility-year."""
    if active_row is None:
        return (
            "missing_in_source",
            "No populated reliability row appears in the PUDL EIA-861 table.",
        )

    notes: list[str] = []
    missing_metrics = [
        field for field in DISPLAY_METRIC_FIELDS if pd.isna(active_row[field])
    ]
    if missing_metrics:
        notes.append("Missing display fields: " + ", ".join(missing_metrics) + ".")
    excluded_fields = (
        str(independent_check["analysis_excluded_fields"])
        if independent_check
        else ""
    )
    if excluded_fields:
        notes.append(str(independent_check["source_note"]))
    if standard_changed:
        notes.append(
            "This utility changes between IEEE and other reporting standards "
            "during 2013-2024."
        )
    elif active_row["standard"] == "other_standard":
        notes.append(
            "Utility reports using a non-IEEE method allowed by EIA; retain for "
            "within-utility description, but do not pool directly with IEEE rows."
        )

    if excluded_fields:
        return "source_conflict_withheld_from_analysis", " ".join(notes)
    if missing_metrics:
        return "incomplete_metrics", " ".join(notes)
    if standard_changed:
        return "descriptive_only_method_change", " ".join(notes)
    if active_row["standard"] == "other_standard":
        return "descriptive_only_non_ieee_method", " ".join(notes)
    return "ready_for_descriptive_use", "No coverage or definition flag in this audit."


def build_audit() -> list[dict[str, object]]:
    candidates = load_candidates()
    raw = load_raw_reliability(candidates)
    direct_validation = load_direct_validation()
    independent_checks = load_independent_checks()
    raw["active_source_row"] = raw.apply(is_active_source_row, axis=1)
    active = raw[raw["active_source_row"]].copy()

    duplicate_counts = active.groupby(["utility_id_eia", "year"]).size()
    duplicate_counts = duplicate_counts[duplicate_counts > 1]
    if not duplicate_counts.empty:
        raise ValueError(
            "Multiple populated reliability-standard rows found for utility-years: "
            f"{duplicate_counts.to_dict()}"
        )

    standards_by_utility = {
        int(utility_id): set(group["standard"].dropna())
        for utility_id, group in active.groupby("utility_id_eia")
    }
    active_lookup = {
        (int(row.utility_id_eia), int(row.year)): row
        for _, row in active.iterrows()
    }

    records: list[dict[str, object]] = []
    for candidate in candidates:
        utility_id = int(candidate["utility_id_eia"])
        standard_changed = len(standards_by_utility.get(utility_id, set())) > 1
        for year in range(YEAR_START, YEAR_END + 1):
            active_row = active_lookup.get((utility_id, year))
            independent_check = independent_checks.get((utility_id, year))
            parent, parent_country = parent_for(candidate, year)
            review_status, quality_note = quality_fields(
                active_row,
                standard_changed,
                independent_check,
            )

            metrics = {
                field: (
                    python_value(active_row[field]) if active_row is not None else None
                )
                for field in METRIC_FIELDS
            }
            reported_metric_count = sum(value is not None for value in metrics.values())
            display_complete = all(metrics[field] is not None for field in DISPLAY_METRIC_FIELDS)
            caidi_available = any(
                metrics[field] is not None
                for field in (
                    "caidi_w_major_event_days_minutes",
                    "caidi_wo_major_event_days_minutes",
                    "caidi_w_major_event_days_minus_loss_of_service_minutes",
                )
            )

            records.append(
                {
                    "panel_id": candidate["panel_id"],
                    "utility_id_eia": utility_id,
                    "utility_name_eia": candidate["utility_name_eia"],
                    "display_name": candidate["display_name"],
                    "state": candidate["state"],
                    "year": year,
                    "ownership": ownership_for(candidate, year),
                    "ownership_2024": candidate["ownership_2024"],
                    "parent_or_owner": parent,
                    "parent_country_or_level": parent_country,
                    "reliability_row_status": (
                        "reported" if active_row is not None else "not_reported"
                    ),
                    "reporting_standard": (
                        python_value(active_row["standard"])
                        if active_row is not None
                        else None
                    ),
                    "standard_changed_during_panel": standard_changed,
                    "comparability_status": comparability_status(
                        active_row,
                        standard_changed,
                    ),
                    "reliability_customers": (
                        python_value(active_row["customers"])
                        if active_row is not None
                        else None
                    ),
                    "entity_type": (
                        python_value(active_row["entity_type"])
                        if active_row is not None
                        else None
                    ),
                    "short_form": (
                        python_value(active_row["short_form"])
                        if active_row is not None
                        else None
                    ),
                    "highest_distribution_voltage_kv": (
                        python_value(active_row["highest_distribution_voltage_kv"])
                        if active_row is not None
                        else None
                    ),
                    "inactive_accounts_included": (
                        python_value(active_row["inactive_accounts_included"])
                        if active_row is not None
                        else None
                    ),
                    "momentary_interruption_definition": (
                        python_value(active_row["momentary_interruption_definition"])
                        if active_row is not None
                        else None
                    ),
                    "outages_recorded_automatically": (
                        python_value(active_row["outages_recorded_automatically"])
                        if active_row is not None
                        else None
                    ),
                    **metrics,
                    "reported_metric_count": reported_metric_count,
                    "display_metrics_complete": display_complete,
                    "caidi_source_status": (
                        "Derived by PUDL as SAIDI divided by SAIFI"
                        if caidi_available
                        else "Unavailable because a component is missing"
                    ),
                    "official_eia_validation_status": direct_validation.get(
                        (utility_id, year),
                        "validation_not_run",
                    ),
                    "analysis_use": analysis_use_status(
                        active_row,
                        standard_changed,
                        independent_check,
                    ),
                    "analysis_excluded_fields": (
                        independent_check["analysis_excluded_fields"]
                        if independent_check
                        else ""
                    ),
                    "independent_crosscheck_status": (
                        independent_check["crosscheck_status"]
                        if independent_check
                        else "not_independently_checked"
                    ),
                    "independent_crosscheck_scope": (
                        independent_check["source_scope"]
                        if independent_check
                        else ""
                    ),
                    "independent_crosscheck_saidi": independent_number(
                        independent_check,
                        "source_saidi",
                    ),
                    "independent_crosscheck_saifi": independent_number(
                        independent_check,
                        "source_saifi",
                    ),
                    "independent_crosscheck_caidi": independent_number(
                        independent_check,
                        "source_caidi",
                    ),
                    "independent_crosscheck_customer_count": independent_number(
                        independent_check,
                        "source_customer_count",
                    ),
                    "independent_crosscheck_source_title": (
                        independent_check["source_title"]
                        if independent_check
                        else ""
                    ),
                    "independent_crosscheck_source_url": (
                        independent_check["source_url"]
                        if independent_check
                        else ""
                    ),
                    "independent_crosscheck_additional_source_url": (
                        independent_check["additional_source_url"]
                        if independent_check
                        else ""
                    ),
                    "independent_crosscheck_source_location": (
                        independent_check["source_location"]
                        if independent_check
                        else ""
                    ),
                    "independent_crosscheck_note": (
                        independent_check["source_note"]
                        if independent_check
                        else ""
                    ),
                    "review_status": review_status,
                    "quality_note": quality_note,
                    "source_status": (
                        "Utility-reported EIA-861 data standardized by PUDL"
                        if active_row is not None
                        else "Not reported in the PUDL EIA-861 reliability table"
                    ),
                    "source_report": "EIA Form 861, Annual Electric Power Industry Report",
                    "source_schedule": "Distribution System Reliability",
                    "eia_source_page": EIA_SOURCE_PAGE,
                    "eia_source_file_url": eia_source_file_url(year),
                    "pudl_source_url": PUDL_RELIABILITY_URL,
                    "pudl_documentation_url": PUDL_DOCUMENTATION_URL,
                    "data_maturity": (
                        python_value(active_row["data_maturity"])
                        if active_row is not None
                        else None
                    ),
                    "retrieved_date": RETRIEVED_DATE,
                }
            )

    expected = len(candidates) * (YEAR_END - YEAR_START + 1)
    if len(records) != expected:
        raise ValueError(f"Expected {expected} audit rows; built {len(records)}")
    keys = {(record["panel_id"], record["year"]) for record in records}
    if len(keys) != expected:
        raise ValueError("Duplicate utility-year rows found in reliability audit")
    return sorted(records, key=lambda row: (str(row["panel_id"]), int(row["year"])))


def write_output(records: list[dict[str, object]]) -> None:
    for output in (OUTPUT_FILE, SITE_CSV_OUTPUT):
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("w", newline="") as target:
            writer = csv.DictWriter(target, fieldnames=OUTPUT_FIELDS)
            writer.writeheader()
            writer.writerows(records)
        print(f"Wrote {len(records)} rows to {output}")

    with SITE_JSON_OUTPUT.open("w") as target:
        json.dump(records, target, indent=2)
        target.write("\n")
    SITE_JS_OUTPUT.write_text(
        "window.NE_NY_RELIABILITY_PANEL = " + json.dumps(records, indent=2) + ";\n"
    )
    print(f"Wrote site data to {SITE_JSON_OUTPUT} and {SITE_JS_OUTPUT}")


def main() -> None:
    write_output(build_audit())


if __name__ == "__main__":
    main()
