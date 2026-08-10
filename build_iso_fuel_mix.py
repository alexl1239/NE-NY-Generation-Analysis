"""Build annual NYISO and ISO-NE generation-mix context for 2013-2024.

The source measurements are plant-level net generation reported on EIA Form 923,
standardized by PUDL. Plants are assigned to a balancing authority using the annual
EIA-860 plant table. The result is regional generation, not the electricity purchased
by any individual utility and not a complete accounting of imports or retail supply.

Run: python3 build_iso_fuel_mix.py
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import duckdb
import pandas as pd


PROJECT_ROOT = Path(__file__).parent
RAW_CACHE_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "eia923"
    / "pudl_iso_generation_by_fuel_2013_2024.csv"
)
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "iso_fuel_mix_2013_2024.csv"
CROSSCHECK_INPUT = PROJECT_ROOT / "data" / "manual" / "iso_fuel_mix_crosschecks.csv"
CROSSCHECK_OUTPUT = (
    PROJECT_ROOT / "data" / "processed" / "iso_fuel_mix_crosschecks_2024.csv"
)
SITE_CSV_OUTPUT = PROJECT_ROOT / "site" / "data" / "iso_fuel_mix.csv"
SITE_JSON_OUTPUT = PROJECT_ROOT / "site" / "data" / "iso_fuel_mix.json"
SITE_JS_OUTPUT = PROJECT_ROOT / "site" / "data" / "iso_fuel_mix.js"

YEAR_START = 2013
YEAR_END = 2024
RETRIEVED_DATE = "2026-08-09"

GENERATION_FUEL_URL = (
    "https://s3.us-west-2.amazonaws.com/pudl.catalyst.coop/stable/"
    "out_eia923__yearly_generation_fuel_combined.parquet"
)
PLANTS_URL = (
    "https://s3.us-west-2.amazonaws.com/pudl.catalyst.coop/stable/"
    "core_eia860__scd_plants.parquet"
)
EIA_923_SOURCE_URL = "https://www.eia.gov/electricity/data/eia923/"
PUDL_EIA923_DOCS_URL = (
    "https://catalystcoop-pudl.readthedocs.io/en/stable/"
    "data_sources/eia923.html"
)

REGIONS = {"NYIS": "NYISO", "ISNE": "ISO-NE"}
FUEL_LABELS = {
    "coal": "Coal",
    "gas": "Natural gas",
    "hydro": "Hydro",
    "nuclear": "Nuclear",
    "oil": "Oil",
    "solar": "Solar",
    "waste": "Waste and biomass",
    "wind": "Wind",
}
FUEL_ORDER = tuple(FUEL_LABELS)

OUTPUT_FIELDS = [
    "region",
    "balancing_authority_code_eia",
    "year",
    "fuel",
    "net_generation_mwh",
    "share_pct",
    "positive_generation_total_mwh",
    "excluded_nonpositive_generation_mwh",
    "status",
    "source_report",
    "eia_source_url",
    "pudl_source_url",
    "pudl_documentation_url",
    "definition_note",
    "retrieved_date",
]


def load_raw() -> pd.DataFrame:
    """Load or cache the two balancing-authority aggregates from PUDL."""
    if RAW_CACHE_FILE.exists():
        raw = pd.read_csv(RAW_CACHE_FILE)
    else:
        codes = ", ".join(f"'{code}'" for code in REGIONS)
        query = f"""
            SELECT
                CAST(EXTRACT(YEAR FROM g.report_date) AS INTEGER) AS year,
                p.balancing_authority_code_eia,
                COALESCE(
                    g.fuel_type_code_pudl,
                    g.energy_source_code,
                    'unknown'
                ) AS fuel,
                SUM(g.net_generation_mwh) AS net_generation_mwh
            FROM read_parquet('{GENERATION_FUEL_URL}') g
            JOIN read_parquet('{PLANTS_URL}') p
              ON g.plant_id_eia = p.plant_id_eia
             AND g.report_date = p.report_date
            WHERE EXTRACT(YEAR FROM g.report_date)
                  BETWEEN {YEAR_START} AND {YEAR_END}
              AND p.balancing_authority_code_eia IN ({codes})
            GROUP BY 1, 2, 3
            ORDER BY 2, 1, 3
        """
        raw = duckdb.connect().execute(query).df()
        RAW_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        raw.to_csv(RAW_CACHE_FILE, index=False)
        print(f"Cached {len(raw)} regional source rows at {RAW_CACHE_FILE}")

    required = {
        "year",
        "balancing_authority_code_eia",
        "fuel",
        "net_generation_mwh",
    }
    missing = required - set(raw.columns)
    if missing:
        raise ValueError(f"ISO fuel-mix cache is missing columns: {sorted(missing)}")
    return raw


def build_records(raw: pd.DataFrame) -> list[dict[str, object]]:
    """Create a balanced region-year-fuel grid and transparent percentage shares."""
    raw = raw.copy()
    raw["year"] = raw["year"].astype(int)
    raw["net_generation_mwh"] = pd.to_numeric(
        raw["net_generation_mwh"], errors="raise"
    )

    unknown_codes = set(raw["balancing_authority_code_eia"]) - set(REGIONS)
    if unknown_codes:
        raise ValueError(f"Unexpected balancing-authority codes: {sorted(unknown_codes)}")
    unexpected_fuels = set(raw["fuel"]) - {*FUEL_ORDER, "other"}
    if unexpected_fuels:
        raise ValueError(f"Unexpected PUDL fuel groups: {sorted(unexpected_fuels)}")

    other = raw[raw["fuel"] == "other"]
    if (other["net_generation_mwh"] > 0).any():
        raise ValueError("The excluded PUDL 'other' group contains positive generation")

    lookup = {
        (row.balancing_authority_code_eia, int(row.year), str(row.fuel)): float(
            row.net_generation_mwh
        )
        for row in raw.itertuples(index=False)
    }

    records: list[dict[str, object]] = []
    for ba_code, region in REGIONS.items():
        for year in range(YEAR_START, YEAR_END + 1):
            values = {
                fuel: lookup.get((ba_code, year, fuel), 0.0)
                for fuel in FUEL_ORDER
            }
            if any(value < 0 for value in values.values()):
                raise ValueError(f"Negative displayed generation for {region} {year}")
            total = sum(values.values())
            if total <= 0:
                raise ValueError(f"No positive generation total for {region} {year}")
            excluded = lookup.get((ba_code, year, "other"), 0.0)
            for fuel in FUEL_ORDER:
                value = values[fuel]
                records.append(
                    {
                        "region": region,
                        "balancing_authority_code_eia": ba_code,
                        "year": year,
                        "fuel": FUEL_LABELS[fuel],
                        "net_generation_mwh": round(value, 3),
                        "share_pct": round(100 * value / total, 6),
                        "positive_generation_total_mwh": round(total, 3),
                        "excluded_nonpositive_generation_mwh": round(excluded, 3),
                        "status": "Derived from reported EIA net generation",
                        "source_report": "EIA Form 923, Power Plant Operations Report",
                        "eia_source_url": EIA_923_SOURCE_URL,
                        "pudl_source_url": GENERATION_FUEL_URL,
                        "pudl_documentation_url": PUDL_EIA923_DOCS_URL,
                        "definition_note": (
                            "Net generation at plants assigned to the NYIS or ISNE "
                            "balancing authority in the annual EIA plant table. This "
                            "is regional generation, not an individual utility's "
                            "purchased power mix, and it excludes imports."
                        ),
                        "retrieved_date": RETRIEVED_DATE,
                    }
                )

    expected = len(REGIONS) * (YEAR_END - YEAR_START + 1) * len(FUEL_ORDER)
    if len(records) != expected:
        raise ValueError(f"Expected {expected} chart rows; built {len(records)}")
    return records


def build_crosschecks(records: list[dict[str, object]]) -> list[dict[str, object]]:
    """Compare 2024 EIA/PUDL totals with totals published by each ISO."""
    with CROSSCHECK_INPUT.open(newline="") as source:
        checks = list(csv.DictReader(source))
    totals = {
        (record["region"], int(record["year"])): float(
            record["positive_generation_total_mwh"]
        )
        for record in records
    }
    output = []
    for check in checks:
        key = (check["region"], int(check["year"]))
        pudl_total_gwh = totals[key] / 1000
        iso_total_gwh = float(check["iso_reported_total_gwh"])
        output.append(
            {
                **check,
                "eia_pudl_total_gwh": round(pudl_total_gwh, 3),
                "difference_pct_of_iso_total": round(
                    100 * (pudl_total_gwh - iso_total_gwh) / iso_total_gwh,
                    6,
                ),
                "comparison_note": (
                    "The totals are close but are not expected to match exactly "
                    "because EIA plant/balancing-area accounting differs from ISO "
                    "market and resource accounting. No ISO value is substituted."
                ),
            }
        )
    return output


def write_outputs(records: list[dict[str, object]]) -> None:
    for output in (OUTPUT_FILE, SITE_CSV_OUTPUT):
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("w", newline="") as target:
            writer = csv.DictWriter(target, fieldnames=OUTPUT_FIELDS)
            writer.writeheader()
            writer.writerows(records)
        print(f"Wrote {len(records)} rows to {output}")

    SITE_JSON_OUTPUT.write_text(json.dumps(records, indent=2) + "\n")
    SITE_JS_OUTPUT.write_text(
        "window.NE_NY_ISO_FUEL_MIX = " + json.dumps(records, indent=2) + ";\n"
    )
    print(f"Wrote site data to {SITE_JSON_OUTPUT} and {SITE_JS_OUTPUT}")

    crosschecks = build_crosschecks(records)
    with CROSSCHECK_OUTPUT.open("w", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=list(crosschecks[0]))
        writer.writeheader()
        writer.writerows(crosschecks)
    print(f"Wrote {len(crosschecks)} source cross-checks to {CROSSCHECK_OUTPUT}")


def main() -> None:
    records = build_records(load_raw())
    write_outputs(records)


if __name__ == "__main__":
    main()
