"""Compare selected PUDL reliability rows with official EIA-861 workbooks.

The coverage audit uses PUDL to standardize annual EIA-861 files. This script
performs a direct source check for 2013–2024 across all 30 selected utilities.
It compares the active reporting standard, customers, SAIDI, SAIFI, and CAIDI.

Run: python3 validate_reliability_sources.py
"""

from __future__ import annotations

import csv
import io
import math
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

from build_price_panel import load_candidates
from build_reliability_audit import (
    PUDL_RELIABILITY_URL,
    RETRIEVED_DATE,
    eia_source_file_url,
    load_raw_reliability,
)


PROJECT_ROOT = Path(__file__).parent
OFFICIAL_RAW_DIR = PROJECT_ROOT / "data" / "raw" / "eia861" / "official"
OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "reliability_source_validation_2013_2024.csv"
)
VALIDATION_YEARS = tuple(range(2013, 2025))

# Column locations in EIA's Reliability_States worksheet. The two numbers are
# the IEEE and other-standard column positions, respectively.
EIA_COLUMN_MAP = {
    "saidi_w_major_event_days_minutes": (5, 17),
    "saifi_w_major_event_days_customers": (6, 18),
    "caidi_w_major_event_days_minutes": (7, 19),
    "saidi_wo_major_event_days_minutes": (8, 20),
    "saifi_wo_major_event_days_customers": (9, 21),
    "caidi_wo_major_event_days_minutes": (10, 22),
    "saidi_w_major_event_days_minus_loss_of_service_minutes": (11, None),
    "saifi_w_major_event_days_minus_loss_of_service_customers": (12, None),
    "caidi_w_major_event_days_minus_loss_of_service_minutes": (13, None),
    "customers": (14, 23),
}

OUTPUT_FIELDS = [
    "year",
    "utility_id_eia",
    "display_name",
    "eia_reporting_standard",
    "pudl_reporting_standard",
    "fields_compared",
    "mismatch_count",
    "validation_status",
    "eia_source_file_url",
    "pudl_source_url",
    "retrieved_date",
]


def ensure_official_archive(year: int) -> Path:
    path = OFFICIAL_RAW_DIR / f"f861{year}.zip"
    if path.exists():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading official EIA-861 {year} archive...")
    urllib.request.urlretrieve(eia_source_file_url(year), path)
    return path


def read_official_reliability(year: int) -> pd.DataFrame:
    with zipfile.ZipFile(ensure_official_archive(year)) as archive:
        members = [
            name
            for name in archive.namelist()
            if Path(name).name.lower() == f"reliability_{year}.xlsx"
        ]
        if len(members) != 1:
            raise ValueError(
                f"Expected one Reliability_{year}.xlsx workbook; found {members}"
            )
        workbook = archive.read(members[0])
    return pd.read_excel(
        io.BytesIO(workbook),
        sheet_name="Reliability_States",
        header=None,
    )


def as_number(value: object) -> float | None:
    number = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return None if pd.isna(number) else float(number)


def numbers_match(left: float | None, right: float | None) -> bool:
    if left is None or right is None:
        return left is None and right is None
    return math.isclose(left, right, rel_tol=0, abs_tol=1e-9)


def build_validation() -> list[dict[str, object]]:
    candidates = load_candidates()
    selected_ids = {int(candidate["utility_id_eia"]) for candidate in candidates}
    candidate_by_id = {
        int(candidate["utility_id_eia"]): candidate for candidate in candidates
    }
    pudl = load_raw_reliability(candidates)
    results: list[dict[str, object]] = []

    for year in VALIDATION_YEARS:
        official = read_official_reliability(year)
        official_ids = pd.to_numeric(official.iloc[:, 1], errors="coerce")
        for utility_id in sorted(selected_ids):
            source_rows = official.loc[official_ids == utility_id]
            pudl_year_rows = pudl[
                (pudl["utility_id_eia"] == utility_id) & (pudl["year"] == year)
            ]
            if source_rows.empty and pudl_year_rows.empty:
                results.append(
                    {
                        "year": year,
                        "utility_id_eia": utility_id,
                        "display_name": candidate_by_id[utility_id]["display_name"],
                        "eia_reporting_standard": "not_reported",
                        "pudl_reporting_standard": "not_reported",
                        "fields_compared": 0,
                        "mismatch_count": 0,
                        "validation_status": "matching_absence",
                        "eia_source_file_url": eia_source_file_url(year),
                        "pudl_source_url": PUDL_RELIABILITY_URL,
                        "retrieved_date": RETRIEVED_DATE,
                    }
                )
                continue
            if len(source_rows) != 1:
                raise ValueError(
                    f"EIA {year}: expected one row for utility {utility_id}; "
                    f"found {len(source_rows)}"
                )
            source_row = source_rows.iloc[0]
            # EIA's 2019 workbook inserts a Short Form column before the
            # reliability fields. The other years in this panel do not.
            source_column_offset = 1 if year == 2019 else 0
            eia_standard = (
                "ieee_standard"
                if as_number(source_row.iloc[14 + source_column_offset]) is not None
                else "other_standard"
            )
            pudl_rows = pudl[
                (pudl["utility_id_eia"] == utility_id)
                & (pudl["year"] == year)
                & (pudl["standard"] == eia_standard)
            ]
            if len(pudl_rows) != 1:
                raise ValueError(
                    f"PUDL {year}: expected one {eia_standard} row for utility "
                    f"{utility_id}; found {len(pudl_rows)}"
                )
            pudl_row = pudl_rows.iloc[0]

            compared = 0
            mismatches: list[str] = []
            standard_index = 0 if eia_standard == "ieee_standard" else 1
            for field, column_positions in EIA_COLUMN_MAP.items():
                column_position = column_positions[standard_index]
                if column_position is None:
                    continue
                column_position += source_column_offset
                eia_value = as_number(source_row.iloc[column_position])
                pudl_value = as_number(pudl_row[field])
                compared += 1
                if not numbers_match(eia_value, pudl_value):
                    mismatches.append(
                        f"{field}: EIA={eia_value}, PUDL={pudl_value}"
                    )

            results.append(
                {
                    "year": year,
                    "utility_id_eia": utility_id,
                    "display_name": candidate_by_id[utility_id]["display_name"],
                    "eia_reporting_standard": eia_standard,
                    "pudl_reporting_standard": str(pudl_row["standard"]),
                    "fields_compared": compared,
                    "mismatch_count": len(mismatches),
                    "validation_status": (
                        "exact_match" if not mismatches else "mismatch: " + "; ".join(mismatches)
                    ),
                    "eia_source_file_url": eia_source_file_url(year),
                    "pudl_source_url": PUDL_RELIABILITY_URL,
                    "retrieved_date": RETRIEVED_DATE,
                }
            )

    mismatched = [row for row in results if row["mismatch_count"]]
    if mismatched:
        raise ValueError(f"Official EIA/PUDL mismatches found: {mismatched}")
    return results


def write_output(records: list[dict[str, object]]) -> None:
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_FILE.open("w", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(records)
    print(
        f"Wrote {len(records)} source checks ({sum(int(row['fields_compared']) for row in records)} "
        f"field comparisons) to {OUTPUT_FILE}"
    )


def main() -> None:
    write_output(build_validation())


if __name__ == "__main__":
    main()
