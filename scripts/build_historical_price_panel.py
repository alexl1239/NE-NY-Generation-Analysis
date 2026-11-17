"""Build the 2001-2024 utility price, revenue, sales, and customer panel.

The build keeps the fixed 42-utility roster. It follows the reviewed annual
identity links from Phase 2 and the ownership and territory warnings from
Phase 3. Published EIA utility tables supply bundled-customer prices and their
supporting revenue, sales, and customer counts. Detailed Form EIA-861 records
provide an independent reconciliation and stable utility IDs.

Run: python3 scripts/build_historical_price_panel.py
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
from collections import defaultdict
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
IDENTITY_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "utility_identity_coverage_2001_2024.csv"
)
OWNERSHIP_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "utility_ownership_history_2001_2024.csv"
)
ALIASES_FILE = PROJECT_ROOT / "data" / "manual" / "utility_name_aliases.csv"
CURRENT_PANEL_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "utility_price_panel_expanded_2013_2024.csv"
)
PANEL_OUTPUT = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "utility_price_history_2001_2024.csv"
)
COVERAGE_OUTPUT = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "historical_price_coverage_2001_2024.csv"
)
TERRITORY_OUTPUT = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "historical_territory_comparison_2001_2024.csv"
)

YEAR_START = 2001
YEAR_END = 2024
RETRIEVED_DATE = "2026-11-15"
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
LEGACY_TABLES = {
    "residential": 14,
    "commercial": 15,
    "industrial": 16,
}
MODERN_TABLES = {
    "residential": 6,
    "commercial": 7,
    "industrial": 8,
}
ESR_ARCHIVE_URL = (
    "https://www.eia.gov/electricity/sales_revenue_price/archive/f861{year}.zip"
)
ESR_CURRENT_URL = (
    "https://www.eia.gov/electricity/sales_revenue_price/xls/f8612024.zip"
)

# These are boundary changes, not ordinary name changes. The component interval
# is the last annual file in which the earlier utility is separately observed.
ABSORBED_COMPONENTS = {
    7601: {
        "panel_id": "MTC_VT_GMP",
        "utility_id_eia": 3292,
        "utility_name": "Central Vermont Public Service Corp",
        "valid_from_year": 2001,
        "valid_to_year": 2012,
        "first_full_combined_year": 2013,
    },
    1179: {
        "panel_id": "MTC_ME_VERSANT",
        "utility_id_eia": 11522,
        "utility_name": "Maine Public Service Co",
        "valid_from_year": 2001,
        "valid_to_year": 2013,
        "first_full_combined_year": 2014,
    },
    19791: {
        "panel_id": "COOP_VT_VEC",
        "utility_id_eia": 3611,
        "utility_name": "Citizens Communications Co",
        "valid_from_year": 2001,
        "valid_to_year": 2002,
        "first_full_combined_year": 2005,
    },
}

PANEL_FIELDS = [
    "panel_id",
    "lineage_id",
    "current_utility_id_eia",
    "display_name",
    "state",
    "year",
    "customer_class",
    "ownership_class",
    "ultimate_parent_or_owner",
    "parent_country_or_level",
    "identity_reporting_basis",
    "matched_utility_ids_eia",
    "matched_utility_names_eia",
    "component_count",
    "territory_comparability_status",
    "published_row_count",
    "published_entity_names",
    "eia_ownership_labels",
    "bundled_customers",
    "bundled_sales_mwh",
    "bundled_revenue_thousand_usd",
    "average_price_cents_kwh",
    "price_method",
    "published_table_number",
    "source_status",
    "detail_reconciliation_status",
    "overlap_2013_2024_status",
    "source_url",
    "detail_source_url",
    "retrieved_date",
    "review_status",
    "notes",
]

COVERAGE_FIELDS = [
    "panel_id",
    "current_utility_id_eia",
    "display_name",
    "state",
    "earliest_defensible_reported_entity_year",
    "earliest_residential_price_year",
    "latest_residential_price_year",
    "years_with_residential_price",
    "complete_three_sector_price_years",
    "published_price_observations",
    "not_reported_zero_bundled_observations",
    "unresolved_positive_bundled_observations",
    "territory_review_required",
    "fixed_territory_gap_years",
    "review_status",
    "notes",
]

TERRITORY_FIELDS = [
    "panel_id",
    "current_utility_id_eia",
    "display_name",
    "state",
    "year",
    "customer_class",
    "territory_basis_status",
    "current_entity_customers",
    "current_entity_sales_mwh",
    "current_entity_revenue_thousand_usd",
    "current_entity_average_price_cents_kwh",
    "absorbed_utility_id_eia",
    "absorbed_utility_name",
    "absorbed_component_customers",
    "absorbed_component_sales_mwh",
    "absorbed_component_revenue_thousand_usd",
    "absorbed_component_average_price_cents_kwh",
    "fixed_2024_territory_customers",
    "fixed_2024_territory_sales_mwh",
    "fixed_2024_territory_revenue_thousand_usd",
    "fixed_2024_territory_average_price_cents_kwh",
    "fixed_territory_price_method",
    "source_url",
    "detail_source_url",
    "review_status",
    "notes",
]


def normalize_name(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value).lower())


def clean_text(value: object) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    return str(value).strip()


def number_or_none(value: object) -> float | None:
    parsed = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return None if pd.isna(parsed) else float(parsed)


def tidy_number(value: float | None) -> int | float | None:
    if value is None:
        return None
    if abs(value - round(value)) < 1e-9:
        return int(round(value))
    return value


def sum_values(values: list[float | None], *, zero_when_empty: bool = False) -> float | None:
    observed = [value for value in values if value is not None]
    if not observed:
        return 0.0 if zero_when_empty else None
    return float(sum(observed))


def values_equal(left: float | None, right: float | None, tolerance: float) -> bool:
    if left is None or right is None:
        return left is None and right is None
    return abs(left - right) <= tolerance


def esr_source_url(year: int) -> str:
    return ESR_CURRENT_URL if year == YEAR_END else ESR_ARCHIVE_URL.format(year=year)


def esr_archive_path(year: int) -> Path:
    return ESR_RAW_DIR / f"f861{year}.zip"


def detail_archive_path(year: int) -> Path:
    if year <= 2011:
        return EIA861_REFORMATTED_DIR / f"861_{year}.zip"
    return EIA861_OFFICIAL_DIR / f"f861{year}.zip"


def detail_source_url(year: int) -> str:
    if year <= 2011:
        return (
            "https://www.eia.gov/electricity/data/eia861/archive/zip/"
            f"861_{year}.zip"
        )
    if year == YEAR_END:
        return "https://www.eia.gov/electricity/data/eia861/zip/f8612024.zip"
    return (
        "https://www.eia.gov/electricity/data/eia861/archive/zip/"
        f"f861{year}.zip"
    )


def ensure_esr_archive(year: int) -> Path:
    path = esr_archive_path(year)
    if path.exists():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    url = esr_source_url(year)
    print(f"Downloading {url}")
    urllib.request.urlretrieve(url, path)
    return path


def find_member(archive: zipfile.ZipFile, token: str) -> str:
    matches = [
        name
        for name in archive.namelist()
        if token in Path(name).name.lower()
        and "_cs_" not in Path(name).name.lower()
        and Path(name).suffix.lower() in {".xls", ".xlsx"}
        and not Path(name).name.startswith("~")
    ]
    if len(matches) != 1:
        raise ValueError(f"Expected one {token} workbook; found {matches}")
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


def extract_workbook(
    archive: zipfile.ZipFile, member: str, label: str, workdir: Path
) -> Path:
    extracted_dir = workdir / f"extracted-{label}"
    extracted_dir.mkdir()
    extracted = extracted_dir / Path(member).name
    extracted.write_bytes(archive.read(member))
    if extracted.suffix.lower() == ".xlsx":
        return extracted

    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        raise RuntimeError("LibreOffice is required to read legacy XLS files")
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


def read_esr_table(year: int, sector: str, workdir: Path) -> pd.DataFrame:
    table_number = (
        LEGACY_TABLES[sector] if year <= 2003 else MODERN_TABLES[sector]
    )
    path = ensure_esr_archive(year)
    with zipfile.ZipFile(path) as archive:
        member = find_esr_member(archive, table_number)
        workbook = extract_workbook(
            archive, member, f"esr-{year}-{table_number}", workdir
        )
    raw = pd.read_excel(workbook, sheet_name=0, header=None)
    rows: list[dict[str, object]] = []
    current_state = ""

    for values in raw.iloc[:, :7].itertuples(index=False, name=None):
        entity = clean_text(values[0])
        if year <= 2002:
            ownership = clean_text(values[1])
            numeric_tail = [number_or_none(value) for value in values[1:6]]
            if entity and not ownership and all(value is None for value in numeric_tail):
                current_state = TARGET_STATE_NAMES.get(entity, entity)
                continue
            state = current_state
            customers = number_or_none(values[2])
            revenue = number_or_none(values[3])
            sales = number_or_none(values[4])
            price = number_or_none(values[5])
        else:
            state = clean_text(values[1])
            ownership = clean_text(values[2])
            customers = number_or_none(values[3])
            if year <= 2007:
                revenue = number_or_none(values[4])
                sales = number_or_none(values[5])
            else:
                sales = number_or_none(values[4])
                revenue = number_or_none(values[5])
            price = number_or_none(values[6])

        if state not in TARGET_STATES or not entity or not ownership:
            continue
        if any(value is None for value in (customers, sales, revenue, price)):
            continue
        rows.append(
            {
                "entity": entity,
                "normalized_entity": normalize_name(entity),
                "state": state,
                "ownership": ownership,
                "customers": customers,
                "sales_mwh": sales,
                "revenue_thousand_usd": revenue,
                "average_price_cents_kwh": price,
            }
        )

    frame = pd.DataFrame.from_records(rows)
    if frame.empty:
        raise ValueError(f"No regional rows parsed from EIA {year} Table {table_number}")
    return frame


def read_detail_sales(year: int, workdir: Path) -> pd.DataFrame:
    path = detail_archive_path(year)
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}. Download it from {detail_source_url(year)}."
        )
    with zipfile.ZipFile(path) as archive:
        member = find_member(archive, "sales_ult_cust")
        workbook = extract_workbook(archive, member, f"sales-{year}", workdir)

    raw = pd.read_excel(workbook, sheet_name="States", header=[0, 1, 2])
    raw = raw.loc[pd.to_numeric(raw.iloc[:, 1], errors="coerce").notna()].copy()
    identity_count = next(
        index
        for index, column in enumerate(raw.columns)
        if clean_text(column[0]).lower() == "residential"
    )
    long_rows: list[dict[str, object]] = []
    for values in raw.itertuples(index=False, name=None):
        utility_id = int(float(values[1]))
        for sector_index, sector in enumerate(SECTORS):
            start = identity_count + sector_index * 3
            long_rows.append(
                {
                    "year": year,
                    "utility_id_eia": utility_id,
                    "utility_name": clean_text(values[2]),
                    "service_type": clean_text(values[4]).lower(),
                    "state": clean_text(values[6]),
                    "customer_class": sector,
                    "revenue_thousand_usd": number_or_none(values[start]),
                    "sales_mwh": number_or_none(values[start + 1]),
                    "customers": number_or_none(values[start + 2]),
                }
            )

    frame = pd.DataFrame.from_records(long_rows)
    return (
        frame.groupby(
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


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as source:
        return list(csv.DictReader(source))


def load_inputs() -> tuple[
    list[dict[str, str]],
    dict[tuple[str, int], dict[str, str]],
    dict[tuple[str, int], dict[str, str]],
    dict[tuple[int, int], set[str]],
    dict[tuple[str, int], dict[str, str]],
]:
    candidates = read_csv(CANDIDATES_FILE)
    if len(candidates) != 42:
        raise ValueError(f"Expected 42 candidates; found {len(candidates)}")

    identity_rows = read_csv(IDENTITY_FILE)
    ownership_rows = read_csv(OWNERSHIP_FILE)
    identity = {
        (row["panel_id"], int(row["year"])): row for row in identity_rows
    }
    ownership = {
        (row["panel_id"], int(row["year"])): row for row in ownership_rows
    }
    expected = len(candidates) * (YEAR_END - YEAR_START + 1)
    if len(identity) != expected or len(ownership) != expected:
        raise ValueError("Identity or ownership table is not a complete 42-by-24 grid")

    aliases: dict[tuple[int, int], set[str]] = defaultdict(set)
    for row in read_csv(ALIASES_FILE):
        utility_id = int(row["utility_id_eia"])
        for year in range(
            int(row["valid_from_year"]), int(row["valid_to_year"]) + 1
        ):
            aliases[(utility_id, year)].add(row["source_name"])

    current_panel = {
        (row["panel_id"], int(row["year"])): row
        for row in read_csv(CURRENT_PANEL_FILE)
    }
    return candidates, identity, ownership, aliases, current_panel


def positive_detail(rows: pd.DataFrame) -> bool:
    if rows.empty:
        return False
    for field in ("customers", "sales_mwh", "revenue_thousand_usd"):
        values = pd.to_numeric(rows[field], errors="coerce").fillna(0)
        if (values.abs() > 1e-9).any():
            return True
    return False


def measurement_for_ids(
    *,
    year: int,
    sector: str,
    state: str,
    utility_ids: tuple[int, ...],
    detail_sales: pd.DataFrame,
    esr_table: pd.DataFrame,
    aliases: dict[tuple[int, int], set[str]],
) -> dict[str, object]:
    detailed = detail_sales.loc[
        detail_sales["utility_id_eia"].isin(utility_ids)
        & (detail_sales["state"] == state)
        & (detail_sales["customer_class"] == sector)
        & (detail_sales["service_type"] == "bundled")
    ].copy()

    published_rows: list[pd.Series] = []
    matched_positions: set[int] = set()
    for utility_id in utility_ids:
        component_detail = detailed.loc[detailed["utility_id_eia"] == utility_id]
        accepted_names = set(aliases.get((utility_id, year), set()))
        accepted_names.update(
            clean_text(value)
            for value in component_detail["utility_name"].dropna().unique()
            if clean_text(value)
        )
        normalized_names = {normalize_name(name) for name in accepted_names}
        normalized_names.update(f"the{name}" for name in tuple(normalized_names))
        matches = esr_table.loc[
            (esr_table["state"] == state)
            & esr_table["normalized_entity"].isin(normalized_names)
        ]
        if len(matches) > 1:
            raise ValueError(
                f"Multiple published rows for {utility_id} {year} {sector}: "
                f"{matches['entity'].tolist()}"
            )
        if len(matches) == 1:
            position = int(matches.index[0])
            if position in matched_positions:
                raise ValueError(
                    f"One published row matched multiple components in {year} {sector}"
                )
            matched_positions.add(position)
            published_rows.append(matches.iloc[0])
        elif positive_detail(component_detail):
            raise ValueError(
                f"No published row for positive bundled detail: "
                f"utility {utility_id}, {year}, {state}, {sector}; "
                f"accepted names={sorted(accepted_names)}"
            )

    detail_customers = sum_values(
        [number_or_none(value) for value in detailed["customers"]],
        zero_when_empty=True,
    )
    detail_sales_mwh = sum_values(
        [number_or_none(value) for value in detailed["sales_mwh"]]
    )
    detail_revenue = sum_values(
        [number_or_none(value) for value in detailed["revenue_thousand_usd"]]
    )

    if published_rows:
        customers = sum_values(
            [number_or_none(row["customers"]) for row in published_rows],
            zero_when_empty=True,
        )
        sales_mwh = sum_values(
            [number_or_none(row["sales_mwh"]) for row in published_rows]
        )
        revenue = sum_values(
            [number_or_none(row["revenue_thousand_usd"]) for row in published_rows]
        )
        if len(published_rows) == 1:
            price = number_or_none(published_rows[0]["average_price_cents_kwh"])
            price_method = "published_eia_average_price"
            source_status = "reported_single_entity"
        else:
            price = (
                revenue / sales_mwh * 100
                if revenue is not None and sales_mwh not in (None, 0)
                else None
            )
            price_method = "combined_from_published_revenue_and_sales"
            source_status = "reported_combined_legal_predecessors"

        reconciled = all(
            (
                values_equal(customers, detail_customers, 0.5),
                values_equal(sales_mwh, detail_sales_mwh, 0.5),
                values_equal(revenue, detail_revenue, 0.05),
            )
        )
        if not reconciled:
            raise ValueError(
                f"Published/detail mismatch for {utility_ids} {year} {sector}: "
                f"published={(customers, sales_mwh, revenue)}, "
                f"detail={(detail_customers, detail_sales_mwh, detail_revenue)}"
            )
        detail_status = "match"
    else:
        customers = 0.0
        sales_mwh = None
        revenue = None
        price = None
        price_method = ""
        source_status = "not_reported_zero_bundled_customers"
        detail_status = "both_not_reported_or_zero"

    return {
        "published_row_count": len(published_rows),
        "published_entity_names": "|".join(
            clean_text(row["entity"]) for row in published_rows
        ),
        "eia_ownership_labels": "|".join(
            sorted({clean_text(row["ownership"]) for row in published_rows})
        ),
        "bundled_customers": tidy_number(customers),
        "bundled_sales_mwh": tidy_number(sales_mwh),
        "bundled_revenue_thousand_usd": tidy_number(revenue),
        "average_price_cents_kwh": price,
        "price_method": price_method,
        "source_status": source_status,
        "detail_reconciliation_status": detail_status,
    }


def overlap_status(
    current_row: dict[str, str] | None,
    sector: str,
    measurement: dict[str, object],
) -> str:
    if current_row is None:
        return "not_applicable"
    expected_price = number_or_none(current_row[f"{sector}_average_price_cents_kwh"])
    expected_customers = number_or_none(
        current_row[f"bundled_{sector}_customers"]
    )
    expected_sales = number_or_none(
        current_row.get(f"bundled_{sector}_sales_mwh", "")
    )
    actual_price = number_or_none(measurement["average_price_cents_kwh"])
    actual_customers = number_or_none(measurement["bundled_customers"])
    actual_sales = number_or_none(measurement["bundled_sales_mwh"])
    return (
        "match"
        if values_equal(expected_price, actual_price, 1e-9)
        and values_equal(expected_customers, actual_customers, 0.5)
        and (
            expected_sales is None
            or values_equal(expected_sales, actual_sales, 0.5)
        )
        else "mismatch"
    )


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {path}")


def build_panel() -> tuple[
    list[dict[str, object]],
    dict[tuple[int, int, str], dict[str, object]],
]:
    candidates, identity, ownership, aliases, current_panel = load_inputs()
    panel_rows: list[dict[str, object]] = []
    absorbed_measurements: dict[
        tuple[int, int, str], dict[str, object]
    ] = {}

    with tempfile.TemporaryDirectory(prefix="historical-price-panel-") as temporary:
        workdir = Path(temporary)
        for year in range(YEAR_START, YEAR_END + 1):
            print(f"Reading {year} price and detailed sales files...")
            detail_sales = read_detail_sales(year, workdir)
            esr_tables = {
                sector: read_esr_table(year, sector, workdir)
                for sector in SECTORS
            }

            for candidate in candidates:
                panel_id = candidate["panel_id"]
                state = candidate["state"]
                identity_row = identity[(panel_id, year)]
                ownership_row = ownership[(panel_id, year)]
                utility_ids = tuple(
                    int(value)
                    for value in identity_row["matched_utility_ids_eia"].split("|")
                )
                for sector in SECTORS:
                    measurement = measurement_for_ids(
                        year=year,
                        sector=sector,
                        state=state,
                        utility_ids=utility_ids,
                        detail_sales=detail_sales,
                        esr_table=esr_tables[sector],
                        aliases=aliases,
                    )
                    overlap = overlap_status(
                        current_panel.get((panel_id, year)), sector, measurement
                    )
                    if overlap == "mismatch":
                        raise ValueError(
                            f"2013-2024 overlap mismatch for {panel_id} {year} {sector}"
                        )
                    panel_rows.append(
                        {
                            "panel_id": panel_id,
                            "lineage_id": identity_row["lineage_id"],
                            "current_utility_id_eia": int(
                                candidate["utility_id_eia"]
                            ),
                            "display_name": candidate["display_name"],
                            "state": state,
                            "year": year,
                            "customer_class": sector,
                            "ownership_class": ownership_row["ownership_class"],
                            "ultimate_parent_or_owner": ownership_row[
                                "ultimate_parent_or_owner"
                            ],
                            "parent_country_or_level": ownership_row[
                                "parent_country_or_level"
                            ],
                            "identity_reporting_basis": identity_row[
                                "reporting_basis"
                            ],
                            "matched_utility_ids_eia": identity_row[
                                "matched_utility_ids_eia"
                            ],
                            "matched_utility_names_eia": identity_row[
                                "matched_utility_names_eia"
                            ],
                            "component_count": int(identity_row["component_count"]),
                            "territory_comparability_status": ownership_row[
                                "territory_comparability_status"
                            ],
                            **measurement,
                            "published_table_number": (
                                LEGACY_TABLES[sector]
                                if year <= 2003
                                else MODERN_TABLES[sector]
                            ),
                            "overlap_2013_2024_status": overlap,
                            "source_url": esr_source_url(year),
                            "detail_source_url": detail_source_url(year),
                            "retrieved_date": RETRIEVED_DATE,
                            "review_status": "reviewed_phase_4",
                            "notes": (
                                "Annual reported-entity record. Territory-comparison "
                                "rows are stored separately for the three acquired-"
                                "territory cases."
                            ),
                        }
                    )

            for current_id, component in ABSORBED_COMPONENTS.items():
                if not (
                    int(component["valid_from_year"])
                    <= year
                    <= int(component["valid_to_year"])
                ):
                    continue
                candidate = next(
                    row
                    for row in candidates
                    if int(row["utility_id_eia"]) == current_id
                )
                for sector in SECTORS:
                    absorbed_measurements[(current_id, year, sector)] = (
                        measurement_for_ids(
                            year=year,
                            sector=sector,
                            state=candidate["state"],
                            utility_ids=(int(component["utility_id_eia"]),),
                            detail_sales=detail_sales,
                            esr_table=esr_tables[sector],
                            aliases=aliases,
                        )
                    )

    expected = 42 * (YEAR_END - YEAR_START + 1) * len(SECTORS)
    if len(panel_rows) != expected:
        raise ValueError(f"Expected {expected} panel rows; created {len(panel_rows)}")
    keys = {
        (row["panel_id"], row["year"], row["customer_class"])
        for row in panel_rows
    }
    if len(keys) != expected:
        raise ValueError("Duplicate utility-year-sector rows in historical panel")
    return panel_rows, absorbed_measurements


def build_coverage(panel_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in panel_rows:
        grouped[str(row["panel_id"])].append(row)

    output: list[dict[str, object]] = []
    for panel_id in sorted(grouped):
        rows = grouped[panel_id]
        first = rows[0]
        residential = [
            row for row in rows if row["customer_class"] == "residential"
        ]
        residential_years = sorted(
            int(row["year"])
            for row in residential
            if row["average_price_cents_kwh"] not in (None, "")
        )
        complete_years = 0
        for year in range(YEAR_START, YEAR_END + 1):
            annual = [row for row in rows if int(row["year"]) == year]
            if all(row["average_price_cents_kwh"] not in (None, "") for row in annual):
                complete_years += 1
        territory_required = int(first["current_utility_id_eia"]) in ABSORBED_COMPONENTS
        fixed_gap_years = (
            "2003|2004" if int(first["current_utility_id_eia"]) == 19791 else ""
        )
        output.append(
            {
                "panel_id": panel_id,
                "current_utility_id_eia": first["current_utility_id_eia"],
                "display_name": first["display_name"],
                "state": first["state"],
                "earliest_defensible_reported_entity_year": YEAR_START,
                "earliest_residential_price_year": (
                    min(residential_years) if residential_years else None
                ),
                "latest_residential_price_year": (
                    max(residential_years) if residential_years else None
                ),
                "years_with_residential_price": len(residential_years),
                "complete_three_sector_price_years": complete_years,
                "published_price_observations": sum(
                    row["average_price_cents_kwh"] not in (None, "")
                    for row in rows
                ),
                "not_reported_zero_bundled_observations": sum(
                    row["source_status"]
                    == "not_reported_zero_bundled_customers"
                    for row in rows
                ),
                "unresolved_positive_bundled_observations": 0,
                "territory_review_required": str(territory_required).lower(),
                "fixed_territory_gap_years": fixed_gap_years,
                "review_status": "reviewed_phase_4",
                "notes": (
                    "Reported-entity records begin in 2001. The fixed-territory "
                    "comparison leaves 2003-2004 unavailable rather than forcing "
                    "Citizens/VEC component data."
                    if fixed_gap_years
                    else (
                        "Reported-entity records begin in 2001. A separate table "
                        "shows the acquired-territory comparison."
                        if territory_required
                        else "Reported-entity records begin in 2001."
                    )
                ),
            }
        )
    return output


def combine_measurements(
    current: dict[str, object], absorbed: dict[str, object]
) -> tuple[int | float | None, int | float | None, int | float | None, float | None]:
    customers = sum_values(
        [
            number_or_none(current["bundled_customers"]),
            number_or_none(absorbed["bundled_customers"]),
        ],
        zero_when_empty=True,
    )
    sales = sum_values(
        [
            number_or_none(current["bundled_sales_mwh"]),
            number_or_none(absorbed["bundled_sales_mwh"]),
        ]
    )
    revenue = sum_values(
        [
            number_or_none(current["bundled_revenue_thousand_usd"]),
            number_or_none(absorbed["bundled_revenue_thousand_usd"]),
        ]
    )
    price = (
        revenue / sales * 100
        if revenue is not None and sales not in (None, 0)
        else None
    )
    return tidy_number(customers), tidy_number(sales), tidy_number(revenue), price


def build_territory_comparison(
    panel_rows: list[dict[str, object]],
    absorbed_measurements: dict[tuple[int, int, str], dict[str, object]],
) -> list[dict[str, object]]:
    panel_lookup = {
        (int(row["current_utility_id_eia"]), int(row["year"]), str(row["customer_class"])): row
        for row in panel_rows
    }
    output: list[dict[str, object]] = []
    for current_id, component in ABSORBED_COMPONENTS.items():
        for year in range(YEAR_START, YEAR_END + 1):
            for sector in SECTORS:
                current = panel_lookup[(current_id, year, sector)]
                absorbed = absorbed_measurements.get((current_id, year, sector))
                if absorbed is not None:
                    fixed_customers, fixed_sales, fixed_revenue, fixed_price = (
                        combine_measurements(current, absorbed)
                    )
                    basis_status = "combined_current_and_absorbed_component"
                    method = "combined_from_published_revenue_and_sales"
                    notes = (
                        "The fixed-territory comparison combines the two separately "
                        "reported utilities for this year."
                    )
                elif current_id == 19791 and year in (2003, 2004):
                    fixed_customers = fixed_sales = fixed_revenue = fixed_price = None
                    basis_status = (
                        "absorbed_component_missing_not_forced"
                        if year == 2003
                        else "partial_acquisition_year_not_forced"
                    )
                    method = ""
                    notes = (
                        "Citizens' Vermont component is not cleanly available for "
                        "this calendar year, so no fixed-territory value is forced."
                    )
                else:
                    fixed_customers = current["bundled_customers"]
                    fixed_sales = current["bundled_sales_mwh"]
                    fixed_revenue = current["bundled_revenue_thousand_usd"]
                    fixed_price = current["average_price_cents_kwh"]
                    basis_status = "current_entity_includes_acquired_territory"
                    method = str(current["price_method"])
                    notes = (
                        "The acquired territory is already included in the current "
                        "utility's annual record."
                    )

                output.append(
                    {
                        "panel_id": current["panel_id"],
                        "current_utility_id_eia": current_id,
                        "display_name": current["display_name"],
                        "state": current["state"],
                        "year": year,
                        "customer_class": sector,
                        "territory_basis_status": basis_status,
                        "current_entity_customers": current["bundled_customers"],
                        "current_entity_sales_mwh": current["bundled_sales_mwh"],
                        "current_entity_revenue_thousand_usd": current[
                            "bundled_revenue_thousand_usd"
                        ],
                        "current_entity_average_price_cents_kwh": current[
                            "average_price_cents_kwh"
                        ],
                        "absorbed_utility_id_eia": component["utility_id_eia"],
                        "absorbed_utility_name": component["utility_name"],
                        "absorbed_component_customers": (
                            absorbed["bundled_customers"] if absorbed else None
                        ),
                        "absorbed_component_sales_mwh": (
                            absorbed["bundled_sales_mwh"] if absorbed else None
                        ),
                        "absorbed_component_revenue_thousand_usd": (
                            absorbed["bundled_revenue_thousand_usd"]
                            if absorbed
                            else None
                        ),
                        "absorbed_component_average_price_cents_kwh": (
                            absorbed["average_price_cents_kwh"] if absorbed else None
                        ),
                        "fixed_2024_territory_customers": fixed_customers,
                        "fixed_2024_territory_sales_mwh": fixed_sales,
                        "fixed_2024_territory_revenue_thousand_usd": fixed_revenue,
                        "fixed_2024_territory_average_price_cents_kwh": fixed_price,
                        "fixed_territory_price_method": method,
                        "source_url": current["source_url"],
                        "detail_source_url": current["detail_source_url"],
                        "review_status": "reviewed_phase_4",
                        "notes": notes,
                    }
                )
    return output


def main() -> None:
    panel_rows, absorbed_measurements = build_panel()
    coverage_rows = build_coverage(panel_rows)
    territory_rows = build_territory_comparison(panel_rows, absorbed_measurements)
    write_csv(PANEL_OUTPUT, PANEL_FIELDS, panel_rows)
    write_csv(COVERAGE_OUTPUT, COVERAGE_FIELDS, coverage_rows)
    write_csv(TERRITORY_OUTPUT, TERRITORY_FIELDS, territory_rows)


if __name__ == "__main__":
    main()
