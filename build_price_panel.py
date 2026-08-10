"""Build the selected-utility price panel from published EIA tables.

Prices are copied from the ``Average Price (cents/kWh)`` columns in Tables 6,
7, and 8 of EIA's annual *Electric Sales, Revenue, and Average Price* report.
They are not recalculated from revenue and sales.

The script expects the official EIA files in ``data/raw/eia_esr``. Annual
archives use the names ``f861YYYY.zip``. Missing files are downloaded from the
URLs below.

Run: python3 build_price_panel.py
"""

from __future__ import annotations

import csv
import json
import re
import shutil
import subprocess
import tempfile
import urllib.request
import zipfile
from pathlib import Path

import duckdb
import pandas as pd


PROJECT_ROOT = Path(__file__).parent
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "eia_esr"
CANDIDATES_FILE = PROJECT_ROOT / "data" / "processed" / "utility_panel_candidates_2024.csv"
PANEL_OUTPUT = PROJECT_ROOT / "data" / "processed" / "utility_price_panel_2013_2024.csv"
SITE_CSV_OUTPUT = PROJECT_ROOT / "site" / "data" / "utility_price_panel.csv"
SITE_JSON_OUTPUT = PROJECT_ROOT / "site" / "data" / "utility_price_panel.json"
SITE_JS_OUTPUT = PROJECT_ROOT / "site" / "data" / "utility_price_panel.js"
COVERAGE_CACHE_FILE = RAW_DIR / "pudl_customer_coverage_top10_2013_2024.csv"

YEAR_START = 2013
YEAR_END = 2024
RETRIEVED_DATE = "2026-08-08"
MINORITY_COVERAGE_THRESHOLD_PCT = 50.0
SECTORS = {
    "residential": {"table_number": 6, "label": "Residential"},
    "commercial": {"table_number": 7, "label": "Commercial"},
    "industrial": {"table_number": 8, "label": "Industrial"},
}

# EIA occasionally changes or truncates an entity label while retaining the same
# utility ID. These are name aliases only; they do not join predecessor IDs.
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

CURRENT_ARCHIVE_URL = (
    "https://www.eia.gov/electricity/sales_revenue_price/xls/f8612024.zip"
)
ARCHIVE_URL = (
    "https://www.eia.gov/electricity/sales_revenue_price/archive/f861{year}.zip"
)
PUDL_SALES_URL = (
    "https://s3.us-west-2.amazonaws.com/pudl.catalyst.coop/stable/"
    "core_eia861__yearly_sales.parquet"
)

BASE_OUTPUT_FIELDS = [
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
    "eia_ownership_label",
]
SECTOR_OUTPUT_FIELDS = [
    field
    for sector in SECTORS
    for field in (
        f"{sector}_average_price_cents_kwh",
        f"bundled_{sector}_customers",
        f"bundled_{sector}_sales_mwh",
        f"pudl_bundled_{sector}_customers",
        f"delivery_only_{sector}_customers",
        f"total_distribution_{sector}_customers",
        f"bundled_{sector}_customer_share_pct",
        f"{sector}_coverage_flag",
        f"{sector}_source_status",
        f"{sector}_source_table",
        f"{sector}_coverage_reconciliation",
    )
]
OUTPUT_FIELDS = BASE_OUTPUT_FIELDS + SECTOR_OUTPUT_FIELDS + [
    "coverage_source_status",
    "coverage_source_url",
    "coverage_flag_rule",
    "source_report",
    "source_url",
    "retrieved_date",
    "ownership_history_note",
    "ownership_source_url",
    "ownership_history_source_url",
]


def normalize_name(value: object) -> str:
    """Normalize punctuation and spacing for a strict utility-name match."""
    return re.sub(r"[^a-z0-9]+", "", str(value).lower())


def source_url(year: int) -> str:
    if year == YEAR_END:
        return CURRENT_ARCHIVE_URL
    return ARCHIVE_URL.format(year=year)


def raw_file(year: int) -> Path:
    return RAW_DIR / f"f861{year}.zip"


def ensure_source_file(year: int) -> Path:
    """Download an official source only when the local raw copy is absent."""
    path = raw_file(year)
    if path.exists():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading EIA {year} price source...")
    urllib.request.urlretrieve(source_url(year), path)
    return path


def find_table_member(archive: zipfile.ZipFile, table_number: int) -> str:
    valid_names = {
        f"table{table_number}.xls",
        f"table{table_number}.xlsx",
        f"table_{table_number}.xls",
        f"table_{table_number}.xlsx",
    }
    candidates = [
        name
        for name in archive.namelist()
        if Path(name).name.lower() in valid_names
    ]
    if len(candidates) != 1:
        raise ValueError(
            f"Expected one Table {table_number} workbook; found {candidates}"
        )
    return candidates[0]


def convert_xls(source: Path, year: int, table_number: int, workdir: Path) -> Path:
    """Convert EIA's 2013-2014 legacy XLS workbooks for modern readers."""
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        raise RuntimeError(
            f"EIA {year} Table {table_number} is an XLS workbook. "
            "LibreOffice/soffice is required to convert it before reading."
        )
    converted_dir = workdir / f"converted-{year}-{table_number}"
    profile_dir = workdir / f"soffice-profile-{year}-{table_number}"
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
            str(source),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    converted = converted_dir / f"{source.stem}.xlsx"
    if not converted.exists():
        raise FileNotFoundError(f"Conversion did not create {converted}")
    return converted


def table_workbook(year: int, table_number: int, workdir: Path) -> Path:
    source = ensure_source_file(year)
    with zipfile.ZipFile(source) as archive:
        member = find_table_member(archive, table_number)
        suffix = Path(member).suffix.lower()
        extracted = workdir / f"table-{table_number}-{year}{suffix}"
        extracted.write_bytes(archive.read(member))
    if suffix == ".xls":
        return convert_xls(extracted, year, table_number, workdir)
    return extracted


def read_eia_table(year: int, table_number: int, workdir: Path) -> pd.DataFrame:
    workbook = table_workbook(year, table_number, workdir)
    raw = pd.read_excel(workbook, sheet_name=f"Table {table_number}", header=2)
    if raw.shape[1] < 7:
        raise ValueError(
            f"EIA {year} Table {table_number} has only {raw.shape[1]} columns"
        )
    table = raw.iloc[:, :7].copy()
    table.columns = [
        "entity",
        "state",
        "eia_ownership_label",
        "customers",
        "sales_mwh",
        "revenue_thousand_usd",
        "average_price_cents_kwh",
    ]
    table["state"] = table["state"].astype(str).str.strip()
    table["normalized_entity"] = table["entity"].map(normalize_name)
    return table


def numeric_or_none(value: object) -> float | None:
    parsed = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return None if pd.isna(parsed) else float(parsed)


def ownership_for(candidate: dict[str, str], year: int) -> str:
    utility_id = int(candidate["utility_id_eia"])
    if utility_id == 19497:  # United Illuminating
        return "DOM" if year <= 2015 else "MTC"
    if utility_id == 13214:  # Narragansett Electric / Rhode Island Energy
        return "MTC" if year <= 2021 else "DOM"
    return candidate["ownership_2024"]


def parent_for(candidate: dict[str, str], year: int) -> tuple[str, str]:
    utility_id = int(candidate["utility_id_eia"])
    if utility_id == 19497 and year <= 2015:
        return "UIL Holdings Corporation", "United States"
    if utility_id == 13214 and year <= 2021:
        return "National Grid plc", "United Kingdom"
    if utility_id == 1179 and year <= 2019:
        return "Emera Inc.", "Canada"
    return (
        candidate["ultimate_parent_or_owner_2024"],
        candidate["parent_country_or_level"],
    )


def load_candidates() -> list[dict[str, str]]:
    with CANDIDATES_FILE.open(newline="") as source:
        candidates = list(csv.DictReader(source))
    expected = 30
    if len(candidates) != expected:
        raise ValueError(
            f"Expected {expected} selected utilities (10 per ownership group); "
            f"found {len(candidates)}"
        )
    return candidates


def load_customer_coverage(candidates: list[dict[str, str]]) -> pd.DataFrame:
    """Load reported bundled and delivery-only customer counts by sector."""
    if COVERAGE_CACHE_FILE.exists():
        coverage = pd.read_csv(COVERAGE_CACHE_FILE)
    else:
        utility_ids = ", ".join(candidate["utility_id_eia"] for candidate in candidates)
        customer_classes = ", ".join(f"'{sector}'" for sector in SECTORS)
        query = f"""
            SELECT
                CAST(EXTRACT(YEAR FROM report_date) AS INTEGER) AS year,
                utility_id_eia,
                state,
                customer_class,
                service_type,
                SUM(customers) AS customers
            FROM read_parquet('{PUDL_SALES_URL}')
            WHERE EXTRACT(YEAR FROM report_date) BETWEEN {YEAR_START} AND {YEAR_END}
              AND utility_id_eia IN ({utility_ids})
              AND customer_class IN ({customer_classes})
              AND service_type IN ('bundled', 'delivery')
            GROUP BY 1, 2, 3, 4, 5
            ORDER BY 2, 1, 4, 5
        """
        coverage = duckdb.connect().execute(query).df()
        COVERAGE_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        coverage.to_csv(COVERAGE_CACHE_FILE, index=False)
        print(f"Cached {len(coverage)} PUDL customer-count rows at {COVERAGE_CACHE_FILE}")

    required = {
        "year",
        "utility_id_eia",
        "state",
        "customer_class",
        "service_type",
        "customers",
    }
    if not required.issubset(coverage.columns):
        raise ValueError(
            f"Coverage cache is missing columns: {sorted(required - set(coverage.columns))}"
        )
    coverage["year"] = coverage["year"].astype(int)
    coverage["utility_id_eia"] = coverage["utility_id_eia"].astype(int)
    return coverage


def customer_coverage_lookup(
    candidates: list[dict[str, str]],
) -> dict[tuple[int, str, int, str], dict[str, int]]:
    coverage = load_customer_coverage(candidates)
    pivot = coverage.pivot_table(
        index=["utility_id_eia", "state", "year", "customer_class"],
        columns="service_type",
        values="customers",
        aggfunc="sum",
        fill_value=0,
    ).reset_index()
    for service_type in ("bundled", "delivery"):
        if service_type not in pivot:
            pivot[service_type] = 0

    lookup: dict[tuple[int, str, int, str], dict[str, int]] = {}
    for row in pivot.itertuples(index=False):
        key = (
            int(row.utility_id_eia),
            str(row.state),
            int(row.year),
            str(row.customer_class),
        )
        bundled = int(row.bundled)
        delivery = int(row.delivery)
        lookup[key] = {
            "bundled": bundled,
            "delivery": delivery,
            "total": bundled + delivery,
        }
    return lookup


def build_panel() -> list[dict[str, object]]:
    candidates = load_candidates()
    coverage = customer_coverage_lookup(candidates)
    records: list[dict[str, object]] = []

    with tempfile.TemporaryDirectory(prefix="eia-price-panel-") as temporary:
        workdir = Path(temporary)
        for year in range(YEAR_START, YEAR_END + 1):
            tables = {
                sector: read_eia_table(year, details["table_number"], workdir)
                for sector, details in SECTORS.items()
            }
            for candidate in candidates:
                utility_id = int(candidate["utility_id_eia"])
                parent, parent_country = parent_for(candidate, year)
                record: dict[str, object] = {
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
                    "eia_ownership_label": None,
                    "coverage_source_status": "Derived from reported customer counts",
                    "coverage_source_url": PUDL_SALES_URL,
                    "coverage_flag_rule": (
                        "minority_coverage when the published bundled price covers "
                        "less than 50% of bundled plus delivery-only customers in "
                        "the same customer class; the price is not changed"
                    ),
                    "source_report": "EIA Electric Sales, Revenue, and Average Price",
                    "source_url": source_url(year),
                    "retrieved_date": RETRIEVED_DATE,
                    "ownership_history_note": candidate["ownership_history_note"],
                    "ownership_source_url": candidate["ownership_source_url"],
                    "ownership_history_source_url": candidate["history_source_url"],
                }

                for sector, details in SECTORS.items():
                    table = tables[sector]
                    accepted_names = PRICE_NAME_ALIASES.get(
                        utility_id,
                        (candidate["utility_name_eia"],),
                    )
                    normalized_names = {normalize_name(name) for name in accepted_names}
                    matches = table[
                        (table["state"] == candidate["state"])
                        & table["normalized_entity"].isin(normalized_names)
                    ]
                    if len(matches) > 1:
                        raise ValueError(
                            f"EIA {year} Table {details['table_number']}: multiple "
                            f"matches for {candidate['utility_name_eia']} ({candidate['state']})"
                        )

                    coverage_key = (utility_id, candidate["state"], year, sector)
                    customer_counts = coverage.get(
                        coverage_key,
                        {"bundled": 0, "delivery": 0, "total": 0},
                    )
                    source_row = matches.iloc[0] if len(matches) == 1 else None
                    if source_row is None:
                        if customer_counts["bundled"] != 0:
                            raise ValueError(
                                f"EIA Table {details['table_number']} has no row for "
                                f"{coverage_key}, but PUDL reports "
                                f"{customer_counts['bundled']} bundled customers"
                            )
                        table_bundled_customers = 0
                        price = None
                        sales_mwh = None
                        source_status = "Not reported"
                        reconciliation = (
                            "No EIA table row; PUDL reports zero bundled customers"
                        )
                    else:
                        table_bundled_customers = int(float(source_row["customers"]))
                        if table_bundled_customers != customer_counts["bundled"]:
                            raise ValueError(
                                f"EIA/PUDL bundled-customer mismatch for {coverage_key}: "
                                f"Table {details['table_number']}={table_bundled_customers}, "
                                f"PUDL={customer_counts['bundled']}"
                            )
                        price = numeric_or_none(source_row["average_price_cents_kwh"])
                        sales_value = numeric_or_none(source_row["sales_mwh"])
                        sales_mwh = int(sales_value) if sales_value is not None else None
                        source_status = "Reported" if price is not None else "Not reported"
                        reconciliation = (
                            f"EIA Table {details['table_number']} bundled customers "
                            "match PUDL bundled customers"
                        )
                        if record["eia_ownership_label"] is None:
                            record["eia_ownership_label"] = str(
                                source_row["eia_ownership_label"]
                            )

                    total_customers = customer_counts["total"]
                    bundled_share = (
                        100 * customer_counts["bundled"] / total_customers
                        if total_customers > 0
                        else None
                    )
                    if price is None:
                        coverage_flag = "no_published_price"
                    elif bundled_share < MINORITY_COVERAGE_THRESHOLD_PCT:
                        coverage_flag = "minority_coverage"
                    else:
                        coverage_flag = "majority_coverage"
                    record.update(
                        {
                            f"{sector}_average_price_cents_kwh": price,
                            f"bundled_{sector}_customers": table_bundled_customers,
                            f"bundled_{sector}_sales_mwh": sales_mwh,
                            f"pudl_bundled_{sector}_customers": customer_counts["bundled"],
                            f"delivery_only_{sector}_customers": customer_counts["delivery"],
                            f"total_distribution_{sector}_customers": total_customers,
                            f"bundled_{sector}_customer_share_pct": bundled_share,
                            f"{sector}_coverage_flag": coverage_flag,
                            f"{sector}_source_status": source_status,
                            f"{sector}_source_table": (
                                f"Table {details['table_number']}: Utility Bundled "
                                f"Retail Sales - {details['label']}"
                            ),
                            f"{sector}_coverage_reconciliation": reconciliation,
                        }
                    )

                records.append(record)

    expected = len(candidates) * (YEAR_END - YEAR_START + 1)
    if len(records) != expected:
        raise ValueError(f"Expected {expected} panel rows; created {len(records)}")
    keys = {(record["panel_id"], record["year"]) for record in records}
    if len(keys) != expected:
        raise ValueError("Duplicate utility-year rows found in price panel")
    return sorted(records, key=lambda row: (str(row["panel_id"]), int(row["year"])))


def write_outputs(records: list[dict[str, object]]) -> None:
    for output in (PANEL_OUTPUT, SITE_CSV_OUTPUT):
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
        "window.NE_NY_PRICE_PANEL = " + json.dumps(records, indent=2) + ";\n"
    )
    print(f"Wrote site data to {SITE_JSON_OUTPUT} and {SITE_JS_OUTPUT}")


def main() -> None:
    write_outputs(build_panel())


if __name__ == "__main__":
    main()
