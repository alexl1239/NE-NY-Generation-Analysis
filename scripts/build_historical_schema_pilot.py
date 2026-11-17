"""Build the representative-year schema pilot for the historical price extension.

The pilot uses five years selected to expose the material source changes:
2001, 2002, 2003, 2012, and 2013. It inspects both the published EIA
Electric Sales, Revenue, and Average Price tables and the detailed Form EIA-861
sales and utility files. The 2013 rows are checked against the existing
validated 42-utility price panel.

Run: python3 scripts/build_historical_schema_pilot.py
"""

from __future__ import annotations

import csv
import math
import re
import shutil
import subprocess
import tempfile
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ESR_RAW_DIR = PROJECT_ROOT / "data" / "raw" / "eia_esr"
EIA861_OFFICIAL_DIR = PROJECT_ROOT / "data" / "raw" / "eia861" / "official"
EIA861_REFORMATTED_DIR = (
    PROJECT_ROOT / "data" / "raw" / "eia861" / "reformatted"
)
CANDIDATES_FILE = (
    PROJECT_ROOT / "data" / "processed" / "expanded_utility_candidates_2024.csv"
)
CURRENT_PANEL_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "utility_price_panel_expanded_2013_2024.csv"
)
SCHEMA_OUTPUT = (
    PROJECT_ROOT / "data" / "processed" / "historical_schema_pilot.csv"
)
PRICE_OUTPUT = (
    PROJECT_ROOT / "data" / "processed" / "historical_price_schema_pilot.csv"
)

PILOT_YEARS = (2001, 2002, 2003, 2012, 2013)
RETRIEVED_DATE = "2026-11-13"
TARGET_STATES = {"CT", "MA", "ME", "NH", "NY", "RI", "VT"}
TARGET_STATE_NAMES = {
    "Connecticut": "CT",
    "Maine": "ME",
    "Massachusetts": "MA",
    "New Hampshire": "NH",
    "New York": "NY",
    "Rhode Island": "RI",
    "Vermont": "VT",
}
SECTORS = ("residential", "commercial", "industrial")
SECTOR_LABELS = {
    "residential": "Residential",
    "commercial": "Commercial",
    "industrial": "Industrial",
}
ESR_TABLES = {
    2001: {"residential": 14, "commercial": 15, "industrial": 16},
    2002: {"residential": 14, "commercial": 15, "industrial": 16},
    2003: {"residential": 14, "commercial": 15, "industrial": 16},
    2012: {"residential": 6, "commercial": 7, "industrial": 8},
    2013: {"residential": 6, "commercial": 7, "industrial": 8},
}

ESR_ARCHIVE_URL = (
    "https://www.eia.gov/electricity/sales_revenue_price/archive/f861{year}.zip"
)
EIA861_ORIGINAL_URL = (
    "https://www.eia.gov/electricity/data/eia861/archive/zip/f861{year}.zip"
)
EIA861_REFORMATTED_URL = (
    "https://www.eia.gov/electricity/data/eia861/archive/zip/861_{year}.zip"
)

DETAIL_SPECS = {
    2001: {
        "archive": EIA861_REFORMATTED_DIR / "861_2001.zip",
        "url": EIA861_REFORMATTED_URL.format(year=2001),
        "sales_member": "2001/Sales_Ult_Cust_2001.xlsx",
        "utility_member": "2001/Utility_Data_2001.xlsx",
    },
    2002: {
        "archive": EIA861_REFORMATTED_DIR / "861_2002.zip",
        "url": EIA861_REFORMATTED_URL.format(year=2002),
        "sales_member": "2002/Sales_Ult_Cust_2002.xlsx",
        "utility_member": "2002/Utility_Data_2002.xlsx",
    },
    2003: {
        "archive": EIA861_REFORMATTED_DIR / "861_2003.zip",
        "url": EIA861_REFORMATTED_URL.format(year=2003),
        "sales_member": "2003/Sales_Ult_Cust_2003.xlsx",
        "utility_member": "2003/Utility_Data_2003.xlsx",
    },
    2012: {
        "archive": EIA861_OFFICIAL_DIR / "f8612012.zip",
        "url": EIA861_ORIGINAL_URL.format(year=2012),
        "sales_member": "Sales_Ult_Cust_2012.xlsx",
        "utility_member": "utility_data_2012.xls",
    },
    2013: {
        "archive": EIA861_OFFICIAL_DIR / "f8612013.zip",
        "url": EIA861_ORIGINAL_URL.format(year=2013),
        "sales_member": "Sales_Ult_Cust_2013.xls",
        "utility_member": "Utility_Data_2013.xls",
    },
}

# Published-table aliases already used by the validated 2013-2024 parser.
PRICE_NAME_ALIASES = {
    1179: ("Versant Power", "Emera Maine"),
    26510: (
        "Liberty Utilities (Granite State Electri",
        "Liberty Utilities (Granite State Electric) Corp",
        "Granite State Electric Co",
    ),
    6374: (
        "Fitchburg Gas & Elec Light Co",
        "Fitchburg Gas and Electric Light Company",
    ),
}

SCHEMA_FIELDS = [
    "year",
    "source_family",
    "source_role",
    "customer_class",
    "archive_filename",
    "workbook_member",
    "worksheet",
    "published_table_number",
    "schema_era",
    "source_row_count",
    "regional_row_count",
    "source_column_count",
    "utility_id_available",
    "state_field_mode",
    "service_type_values",
    "fourth_sector_label",
    "iso_rto_fields_available",
    "candidate_utility_ids_present",
    "candidate_utility_count",
    "parser_status",
    "source_url",
    "retrieved_date",
    "notes",
]

PRICE_FIELDS = [
    "panel_id",
    "utility_id_eia",
    "display_name",
    "state",
    "year",
    "customer_class",
    "utility_id_present_in_utility_data",
    "utility_id_present_in_sales_data",
    "detailed_bundled_row_present",
    "detailed_utility_name",
    "detailed_bundled_customers",
    "detailed_bundled_sales_mwh",
    "detailed_bundled_revenue_thousand_usd",
    "esr_table_number",
    "esr_match_status",
    "esr_entity_name",
    "esr_ownership_label",
    "esr_customers",
    "esr_sales_mwh",
    "esr_revenue_thousand_usd",
    "esr_average_price_cents_kwh",
    "recalculated_average_price_cents_kwh",
    "published_minus_recalculated_price",
    "detail_reconciliation_status",
    "current_2013_price_cents_kwh",
    "current_2013_customers",
    "current_2013_sales_mwh",
    "current_2013_overlap_status",
    "name_alias_review_needed",
    "lineage_review_needed",
    "source_url",
    "detail_source_url",
]


def normalize_name(value: object) -> str:
    """Normalize punctuation and spacing for strict annual name matching."""
    return re.sub(r"[^a-z0-9]+", "", str(value).lower())


def clean_text(value: object) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    return str(value).strip()


def number_or_none(value: object) -> float | None:
    parsed = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return None if pd.isna(parsed) else float(parsed)


def int_or_none(value: object) -> int | None:
    parsed = number_or_none(value)
    return None if parsed is None else int(round(parsed))


def values_equal(left: float | None, right: float | None, tolerance: float) -> bool:
    if left is None or right is None:
        return left is None and right is None
    return abs(left - right) <= tolerance


def ensure_download(url: str, path: Path) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {url}")
    urllib.request.urlretrieve(url, path)


def find_member(archive: zipfile.ZipFile, expected: str) -> str:
    expected_lower = expected.lower()
    matches = [
        name
        for name in archive.namelist()
        if name.lower() == expected_lower
        or Path(name).name.lower() == Path(expected).name.lower()
    ]
    if len(matches) != 1:
        raise ValueError(f"Expected one archive member {expected}; found {matches}")
    return matches[0]


def find_esr_member(archive: zipfile.ZipFile, table_number: int) -> str:
    valid_names = {
        f"table{table_number}.xls",
        f"table{table_number}.xlsx",
        f"table_{table_number}.xls",
        f"table_{table_number}.xlsx",
    }
    matches = [
        name
        for name in archive.namelist()
        if Path(name).name.lower() in valid_names
    ]
    if len(matches) != 1:
        raise ValueError(
            f"Expected one published Table {table_number}; found {matches}"
        )
    return matches[0]


def member_workbook(
    archive_path: Path,
    member: str,
    label: str,
    workdir: Path,
) -> Path:
    """Extract a workbook and convert legacy XLS to XLSX when necessary."""
    with zipfile.ZipFile(archive_path) as archive:
        actual_member = find_member(archive, member)
        suffix = Path(actual_member).suffix.lower()
        extracted_dir = workdir / f"extracted-{label}"
        extracted_dir.mkdir()
        extracted = extracted_dir / Path(actual_member).name
        extracted.write_bytes(archive.read(actual_member))

    if suffix == ".xlsx":
        return extracted
    if suffix != ".xls":
        raise ValueError(f"Unsupported workbook type for {actual_member}")

    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        raise RuntimeError(
            f"{actual_member} is an XLS workbook. LibreOffice/soffice is required."
        )
    converted_dir = workdir / f"converted-{label}"
    profile_dir = workdir / f"profile-{label}"
    converted_dir.mkdir()
    subprocess.run(
        [
            soffice,
            f"-env:UserInstallation={profile_dir.resolve().as_uri()}",
            "--headless",
            "--convert-to",
            "xlsx",
            "--outdir",
            str(converted_dir),
            str(extracted),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    converted = converted_dir / f"{extracted.stem}.xlsx"
    if not converted.exists():
        raise FileNotFoundError(f"Conversion did not create {converted}")
    return converted


def esr_workbook(
    year: int, table_number: int, workdir: Path
) -> tuple[Path, str]:
    archive_path = ESR_RAW_DIR / f"f861{year}.zip"
    ensure_download(ESR_ARCHIVE_URL.format(year=year), archive_path)
    with zipfile.ZipFile(archive_path) as archive:
        member = find_esr_member(archive, table_number)
    workbook = member_workbook(
        archive_path,
        member,
        f"esr-{year}-{table_number}",
        workdir,
    )
    return workbook, member


def _valid_esr_record(
    entity: object,
    ownership: object,
    customers: object,
    sales: object,
    average_price: object,
) -> bool:
    return bool(clean_text(entity) and clean_text(ownership)) and all(
        number_or_none(value) is not None
        for value in (customers, sales, average_price)
    )


def read_esr_table(
    year: int, sector: str, workdir: Path
) -> tuple[pd.DataFrame, dict[str, object]]:
    table_number = ESR_TABLES[year][sector]
    workbook, member = esr_workbook(year, table_number, workdir)
    book = pd.ExcelFile(workbook)
    worksheet = book.sheet_names[0]
    records: list[dict[str, object]] = []

    if year <= 2002:
        raw = pd.read_excel(workbook, sheet_name=worksheet, header=None)
        current_state_label = ""
        for values in raw.iloc[7:, :6].itertuples(index=False, name=None):
            entity, ownership, customers, revenue, sales, price = values
            if clean_text(entity) and not clean_text(ownership) and all(
                number_or_none(value) is None
                for value in (customers, revenue, sales, price)
            ):
                current_state_label = clean_text(entity)
                continue
            if not _valid_esr_record(
                entity, ownership, customers, sales, price
            ):
                continue
            records.append(
                {
                    "entity": clean_text(entity),
                    "state": TARGET_STATE_NAMES.get(
                        current_state_label, current_state_label
                    ),
                    "ownership": clean_text(ownership),
                    "customers": number_or_none(customers),
                    "revenue_thousand_usd": number_or_none(revenue),
                    "sales_mwh": number_or_none(sales),
                    "average_price_cents_kwh": number_or_none(price),
                }
            )
        schema_era = "legacy_state_marker_rows"
        state_mode = "state name marker rows"
        source_column_count = 6
        header_rows = 7
    elif year == 2003:
        raw = pd.read_excel(workbook, sheet_name=worksheet, header=None)
        for values in raw.iloc[7:, :7].itertuples(index=False, name=None):
            entity, state, ownership, customers, revenue, sales, price = values
            if not re.fullmatch(r"[A-Z]{2}", clean_text(state)):
                continue
            if not _valid_esr_record(
                entity, ownership, customers, sales, price
            ):
                continue
            records.append(
                {
                    "entity": clean_text(entity),
                    "state": clean_text(state),
                    "ownership": clean_text(ownership),
                    "customers": number_or_none(customers),
                    "revenue_thousand_usd": number_or_none(revenue),
                    "sales_mwh": number_or_none(sales),
                    "average_price_cents_kwh": number_or_none(price),
                }
            )
        schema_era = "legacy_explicit_state_column"
        state_mode = "two-letter state column"
        source_column_count = 7
        header_rows = 7
    else:
        raw = pd.read_excel(workbook, sheet_name=worksheet, header=2)
        table = raw.iloc[:, :7].copy()
        table.columns = [
            "entity",
            "state",
            "ownership",
            "customers",
            "sales_mwh",
            "revenue_thousand_usd",
            "average_price_cents_kwh",
        ]
        for row in table.itertuples(index=False):
            if not re.fullmatch(r"[A-Z]{2}", clean_text(row.state)):
                continue
            if not _valid_esr_record(
                row.entity,
                row.ownership,
                row.customers,
                row.sales_mwh,
                row.average_price_cents_kwh,
            ):
                continue
            records.append(
                {
                    "entity": clean_text(row.entity),
                    "state": clean_text(row.state),
                    "ownership": clean_text(row.ownership),
                    "customers": number_or_none(row.customers),
                    "revenue_thousand_usd": number_or_none(
                        row.revenue_thousand_usd
                    ),
                    "sales_mwh": number_or_none(row.sales_mwh),
                    "average_price_cents_kwh": number_or_none(
                        row.average_price_cents_kwh
                    ),
                }
            )
        schema_era = "modern_table_6_to_8"
        state_mode = "two-letter state column"
        source_column_count = 7
        header_rows = 3

    frame = pd.DataFrame.from_records(records)
    if frame.empty:
        raise ValueError(f"No records parsed from EIA {year} Table {table_number}")
    frame["normalized_entity"] = frame["entity"].map(normalize_name)
    metadata = {
        "year": year,
        "source_family": "eia_esr_published_tables",
        "source_role": "published bundled price",
        "customer_class": sector,
        "archive_filename": f"f861{year}.zip",
        "workbook_member": member,
        "worksheet": worksheet,
        "published_table_number": table_number,
        "schema_era": schema_era,
        "source_row_count": len(frame),
        "regional_row_count": int(frame["state"].isin(TARGET_STATES).sum()),
        "source_column_count": source_column_count,
        "utility_id_available": False,
        "state_field_mode": state_mode,
        "service_type_values": "bundled only",
        "fourth_sector_label": "other" if year <= 2002 else "transportation",
        "iso_rto_fields_available": False,
        "candidate_utility_ids_present": "",
        "candidate_utility_count": "",
        "parser_status": "pass",
        "source_url": ESR_ARCHIVE_URL.format(year=year),
        "retrieved_date": RETRIEVED_DATE,
        "notes": (
            f"Parsed after {header_rows} heading rows; utility IDs are linked "
            "through the detailed EIA-861 files and annual utility names."
        ),
    }
    return frame.loc[frame["state"].isin(TARGET_STATES)].copy(), metadata


def detail_workbook(year: int, role: str, workdir: Path) -> tuple[Path, str]:
    spec = DETAIL_SPECS[year]
    archive_path = Path(spec["archive"])
    ensure_download(str(spec["url"]), archive_path)
    member = str(spec[f"{role}_member"])
    workbook = member_workbook(
        archive_path,
        member,
        f"detail-{year}-{role}",
        workdir,
    )
    return workbook, member


def read_detail_sales(
    year: int,
    candidates: list[dict[str, str]],
    workdir: Path,
) -> tuple[pd.DataFrame, dict[str, object]]:
    workbook, member = detail_workbook(year, "sales", workdir)
    raw = pd.read_excel(
        workbook,
        sheet_name="States",
        header=[0, 1, 2],
    )
    raw = raw.loc[pd.to_numeric(raw.iloc[:, 0], errors="coerce").notna()].copy()
    identity_count = 9 if year >= 2013 else 8
    fourth_sector = clean_text(raw.columns[identity_count + 9][0]).lower()
    long_rows: list[dict[str, object]] = []
    for values in raw.itertuples(index=False, name=None):
        utility_id = int_or_none(values[1])
        if utility_id is None:
            continue
        for sector_index, sector in enumerate(SECTORS):
            start = identity_count + sector_index * 3
            long_rows.append(
                {
                    "year": year,
                    "utility_id_eia": utility_id,
                    "utility_name": clean_text(values[2]),
                    "part": clean_text(values[3]),
                    "service_type": clean_text(values[4]).lower(),
                    "data_type": clean_text(values[5]),
                    "state": clean_text(values[6]),
                    "ownership": clean_text(values[7]),
                    "customer_class": sector,
                    "revenue_thousand_usd": number_or_none(values[start]),
                    "sales_mwh": number_or_none(values[start + 1]),
                    "customers": number_or_none(values[start + 2]),
                }
            )

    long_frame = pd.DataFrame.from_records(long_rows)
    grouped = (
        long_frame.groupby(
            [
                "year",
                "utility_id_eia",
                "state",
                "customer_class",
                "service_type",
            ],
            dropna=False,
            as_index=False,
        )
        .agg(
            utility_name=("utility_name", "first"),
            ownership=("ownership", "first"),
            revenue_thousand_usd=(
                "revenue_thousand_usd",
                lambda values: values.sum(min_count=1),
            ),
            sales_mwh=("sales_mwh", lambda values: values.sum(min_count=1)),
            customers=("customers", lambda values: values.sum(min_count=1)),
        )
        .sort_values(
            ["utility_id_eia", "state", "customer_class", "service_type"]
        )
    )
    candidate_ids = {int(row["utility_id_eia"]) for row in candidates}
    present = set(grouped["utility_id_eia"].astype(int)) & candidate_ids
    service_types = sorted(
        value for value in long_frame["service_type"].dropna().unique() if value
    )
    metadata = {
        "year": year,
        "source_family": "eia861_detailed",
        "source_role": "sales to ultimate customers",
        "customer_class": "residential;commercial;industrial",
        "archive_filename": Path(DETAIL_SPECS[year]["archive"]).name,
        "workbook_member": member,
        "worksheet": "States",
        "published_table_number": "",
        "schema_era": "three_row_grouped_headers",
        "source_row_count": len(raw),
        "regional_row_count": int(raw.iloc[:, 6].isin(TARGET_STATES).sum()),
        "source_column_count": raw.shape[1],
        "utility_id_available": True,
        "state_field_mode": "two-letter state column",
        "service_type_values": ";".join(service_types),
        "fourth_sector_label": fourth_sector,
        "iso_rto_fields_available": False,
        "candidate_utility_ids_present": len(present),
        "candidate_utility_count": len(candidate_ids),
        "parser_status": "pass",
        "source_url": str(DETAIL_SPECS[year]["url"]),
        "retrieved_date": RETRIEVED_DATE,
        "notes": (
            "Utility IDs, service type, state, ownership, revenue, sales, and "
            "customer counts are available in a consistent reformatted layout."
        ),
    }
    return grouped, metadata


def read_detail_utility(
    year: int,
    candidates: list[dict[str, str]],
    workdir: Path,
) -> tuple[pd.DataFrame, dict[str, object]]:
    workbook, member = detail_workbook(year, "utility", workdir)
    raw = pd.read_excel(workbook, sheet_name="States", header=1)
    raw = raw.loc[pd.to_numeric(raw.iloc[:, 0], errors="coerce").notna()].copy()
    utility = pd.DataFrame(
        {
            "year": pd.to_numeric(raw.iloc[:, 0], errors="coerce").astype(int),
            "utility_id_eia": pd.to_numeric(raw.iloc[:, 1], errors="coerce").astype(
                int
            ),
            "utility_name": raw.iloc[:, 2].map(clean_text),
            "state": raw.iloc[:, 3].map(clean_text),
            "ownership": raw.iloc[:, 4].map(clean_text),
        }
    )
    iso_columns = [
        column
        for column in ("CAISO", "ERCOT", "PJM", "NYISO", "MISO", "ISONE")
        if column in raw.columns
    ]
    candidate_ids = {int(row["utility_id_eia"]) for row in candidates}
    present = set(utility["utility_id_eia"]) & candidate_ids
    metadata = {
        "year": year,
        "source_family": "eia861_detailed",
        "source_role": "utility identity",
        "customer_class": "",
        "archive_filename": Path(DETAIL_SPECS[year]["archive"]).name,
        "workbook_member": member,
        "worksheet": "States",
        "published_table_number": "",
        "schema_era": (
            "utility_identity_with_iso_rto_fields"
            if iso_columns
            else "utility_identity_without_iso_rto_fields"
        ),
        "source_row_count": len(utility),
        "regional_row_count": int(utility["state"].isin(TARGET_STATES).sum()),
        "source_column_count": raw.shape[1],
        "utility_id_available": True,
        "state_field_mode": "two-letter utility headquarters state",
        "service_type_values": "",
        "fourth_sector_label": "",
        "iso_rto_fields_available": bool(iso_columns),
        "candidate_utility_ids_present": len(present),
        "candidate_utility_count": len(candidate_ids),
        "parser_status": "pass",
        "source_url": str(DETAIL_SPECS[year]["url"]),
        "retrieved_date": RETRIEVED_DATE,
        "notes": (
            "ISO/RTO indicator columns present: " + ", ".join(iso_columns)
            if iso_columns
            else "No ISO/RTO columns; use state and service territory before 2010."
        ),
    }
    return utility, metadata


def load_candidates() -> list[dict[str, str]]:
    with CANDIDATES_FILE.open(newline="") as source:
        rows = list(csv.DictReader(source))
    if len(rows) != 42:
        raise ValueError(f"Expected 42 expanded candidates; found {len(rows)}")
    return rows


def load_current_2013_panel() -> dict[str, dict[str, str]]:
    with CURRENT_PANEL_FILE.open(newline="") as source:
        rows = [
            row for row in csv.DictReader(source) if int(row["year"]) == 2013
        ]
    if len(rows) != 42:
        raise ValueError(f"Expected 42 current 2013 rows; found {len(rows)}")
    return {row["panel_id"]: row for row in rows}


def detail_value(row: pd.Series | None, field: str) -> float | None:
    if row is None:
        return None
    return number_or_none(row[field])


def build_price_records(
    candidates: list[dict[str, str]],
    current_2013: dict[str, dict[str, str]],
    year: int,
    esr_tables: dict[str, pd.DataFrame],
    detail_sales: pd.DataFrame,
    detail_utility: pd.DataFrame,
) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    utility_ids = set(detail_utility["utility_id_eia"].astype(int))
    sales_ids = set(detail_sales["utility_id_eia"].astype(int))

    for candidate in candidates:
        utility_id = int(candidate["utility_id_eia"])
        state = candidate["state"]
        annual_sales = detail_sales.loc[
            (detail_sales["utility_id_eia"] == utility_id)
            & (detail_sales["state"] == state)
        ]
        annual_names = {
            clean_text(value)
            for value in annual_sales["utility_name"].dropna().unique()
            if clean_text(value)
        }
        accepted_names = {
            candidate["utility_name_eia"],
            *PRICE_NAME_ALIASES.get(utility_id, ()),
            *annual_names,
        }
        normalized_names = {normalize_name(name) for name in accepted_names}

        for sector in SECTORS:
            detail_rows = annual_sales.loc[
                (annual_sales["customer_class"] == sector)
                & (annual_sales["service_type"].str.lower() == "bundled")
            ]
            detail_row = detail_rows.iloc[0] if len(detail_rows) == 1 else None
            if len(detail_rows) > 1:
                raise ValueError(
                    f"Multiple detailed bundled rows for {utility_id} {year} {sector}"
                )

            esr_table = esr_tables[sector]
            matches = esr_table.loc[
                (esr_table["state"] == state)
                & (esr_table["normalized_entity"].isin(normalized_names))
            ]
            if len(matches) == 1:
                esr_row = matches.iloc[0]
                match_status = "matched"
            elif len(matches) == 0:
                esr_row = None
                match_status = "not_matched"
            else:
                esr_row = None
                match_status = "multiple_matches"

            esr_customers = detail_value(esr_row, "customers")
            esr_sales = detail_value(esr_row, "sales_mwh")
            esr_revenue = detail_value(esr_row, "revenue_thousand_usd")
            esr_price = detail_value(esr_row, "average_price_cents_kwh")
            recalculated_price = (
                esr_revenue / esr_sales * 100
                if esr_revenue is not None
                and esr_sales is not None
                and esr_sales != 0
                else None
            )
            price_difference = (
                esr_price - recalculated_price
                if esr_price is not None and recalculated_price is not None
                else None
            )

            if esr_row is not None and detail_row is not None:
                detail_match = all(
                    (
                        values_equal(
                            esr_customers,
                            detail_value(detail_row, "customers"),
                            0.5,
                        ),
                        values_equal(
                            esr_sales,
                            detail_value(detail_row, "sales_mwh"),
                            0.5,
                        ),
                        values_equal(
                            esr_revenue,
                            detail_value(detail_row, "revenue_thousand_usd"),
                            0.05,
                        ),
                    )
                )
                detail_status = "match" if detail_match else "mismatch"
            elif esr_row is None and detail_row is None:
                detail_status = "both_missing"
            elif esr_row is None:
                detail_status = "esr_not_matched"
            else:
                detail_status = "detailed_bundled_row_missing"

            current_price = None
            current_customers = None
            current_sales = None
            overlap_status = "not_applicable"
            if year == 2013:
                current = current_2013[candidate["panel_id"]]
                current_price = number_or_none(
                    current[f"{sector}_average_price_cents_kwh"]
                )
                current_customers = number_or_none(
                    current[f"bundled_{sector}_customers"]
                )
                current_sales = number_or_none(
                    current.get(f"bundled_{sector}_sales_mwh", "")
                )
                pilot_customers = esr_customers if esr_row is not None else 0.0
                overlap_status = (
                    "match"
                    if match_status != "multiple_matches"
                    and values_equal(esr_price, current_price, 1e-9)
                    and values_equal(pilot_customers, current_customers, 0.5)
                    and (
                        current_sales is None
                        or values_equal(esr_sales, current_sales, 0.5)
                    )
                    else "mismatch"
                )

            name_alias_review_needed = (
                detail_row is not None
                and number_or_none(detail_row["customers"]) not in (None, 0)
                and match_status != "matched"
            )
            lineage_review_needed = (
                utility_id not in utility_ids
                or utility_id not in sales_ids
            )
            records.append(
                {
                    "panel_id": candidate["panel_id"],
                    "utility_id_eia": str(utility_id),
                    "display_name": candidate["display_name"],
                    "state": state,
                    "year": year,
                    "customer_class": sector,
                    "utility_id_present_in_utility_data": utility_id
                    in utility_ids,
                    "utility_id_present_in_sales_data": utility_id in sales_ids,
                    "detailed_bundled_row_present": detail_row is not None,
                    "detailed_utility_name": (
                        detail_row["utility_name"] if detail_row is not None else ""
                    ),
                    "detailed_bundled_customers": detail_value(
                        detail_row, "customers"
                    ),
                    "detailed_bundled_sales_mwh": detail_value(
                        detail_row, "sales_mwh"
                    ),
                    "detailed_bundled_revenue_thousand_usd": detail_value(
                        detail_row, "revenue_thousand_usd"
                    ),
                    "esr_table_number": ESR_TABLES[year][sector],
                    "esr_match_status": match_status,
                    "esr_entity_name": (
                        esr_row["entity"] if esr_row is not None else ""
                    ),
                    "esr_ownership_label": (
                        esr_row["ownership"] if esr_row is not None else ""
                    ),
                    "esr_customers": esr_customers,
                    "esr_sales_mwh": esr_sales,
                    "esr_revenue_thousand_usd": esr_revenue,
                    "esr_average_price_cents_kwh": esr_price,
                    "recalculated_average_price_cents_kwh": recalculated_price,
                    "published_minus_recalculated_price": price_difference,
                    "detail_reconciliation_status": detail_status,
                    "current_2013_price_cents_kwh": current_price,
                    "current_2013_customers": current_customers,
                    "current_2013_sales_mwh": current_sales,
                    "current_2013_overlap_status": overlap_status,
                    "name_alias_review_needed": name_alias_review_needed,
                    "lineage_review_needed": lineage_review_needed,
                    "source_url": ESR_ARCHIVE_URL.format(year=year),
                    "detail_source_url": str(DETAIL_SPECS[year]["url"]),
                }
            )
    return records


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {path}")


def build_pilot() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    candidates = load_candidates()
    current_2013 = load_current_2013_panel()
    schema_rows: list[dict[str, object]] = []
    price_rows: list[dict[str, object]] = []

    with tempfile.TemporaryDirectory(prefix="historical-schema-pilot-") as temp:
        workdir = Path(temp)
        for year in PILOT_YEARS:
            esr_tables: dict[str, pd.DataFrame] = {}
            for sector in SECTORS:
                table, metadata = read_esr_table(year, sector, workdir)
                esr_tables[sector] = table
                schema_rows.append(metadata)
            detail_sales, sales_metadata = read_detail_sales(
                year, candidates, workdir
            )
            detail_utility, utility_metadata = read_detail_utility(
                year, candidates, workdir
            )
            schema_rows.extend((sales_metadata, utility_metadata))
            price_rows.extend(
                build_price_records(
                    candidates,
                    current_2013,
                    year,
                    esr_tables,
                    detail_sales,
                    detail_utility,
                )
            )

    expected_schema_rows = len(PILOT_YEARS) * (len(SECTORS) + 2)
    expected_price_rows = len(PILOT_YEARS) * len(candidates) * len(SECTORS)
    if len(schema_rows) != expected_schema_rows:
        raise ValueError(
            f"Expected {expected_schema_rows} schema rows; created {len(schema_rows)}"
        )
    if len(price_rows) != expected_price_rows:
        raise ValueError(
            f"Expected {expected_price_rows} price rows; created {len(price_rows)}"
        )
    overlap = [
        row
        for row in price_rows
        if row["year"] == 2013
        and row["current_2013_overlap_status"] != "match"
    ]
    if overlap:
        sample = overlap[:5]
        raise ValueError(f"2013 overlap check failed for {sample}")
    return schema_rows, price_rows


def print_summary(price_rows: list[dict[str, object]]) -> None:
    for year in PILOT_YEARS:
        rows = [row for row in price_rows if row["year"] == year]
        utilities_with_ids = len(
            {
                row["utility_id_eia"]
                for row in rows
                if row["utility_id_present_in_sales_data"]
            }
        )
        matched = sum(row["esr_match_status"] == "matched" for row in rows)
        reconciled = sum(
            row["detail_reconciliation_status"] == "match" for row in rows
        )
        lineage = len(
            {
                row["utility_id_eia"]
                for row in rows
                if row["lineage_review_needed"]
            }
        )
        aliases = len(
            {
                row["utility_id_eia"]
                for row in rows
                if row["name_alias_review_needed"]
            }
        )
        print(
            f"{year}: IDs present {utilities_with_ids}/42; ESR matches "
            f"{matched}/126; ESR/detail matches {reconciled}; "
            f"alias review {aliases}; lineage review {lineage} utilities"
        )


def main() -> None:
    schema_rows, price_rows = build_pilot()
    write_csv(SCHEMA_OUTPUT, SCHEMA_FIELDS, schema_rows)
    write_csv(PRICE_OUTPUT, PRICE_FIELDS, price_rows)
    print_summary(price_rows)


if __name__ == "__main__":
    main()
