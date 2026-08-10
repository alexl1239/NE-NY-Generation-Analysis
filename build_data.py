"""Build the chart datasets used by the archived findings page.

The individual JSON files remain the human-readable data outputs. A matching
JavaScript bundle is also written so the charts work when the site is opened
directly from disk, where browsers do not allow ``fetch()`` to read local JSON.

Run: python3 build_data.py
"""
import json
from pathlib import Path

import duckdb
import pandas as pd

GENERATION_FUEL_FILE = (
    "https://s3.us-west-2.amazonaws.com/"
    "pudl.catalyst.coop/stable/"
    "out_eia923__yearly_generation_fuel_combined.parquet"
)

PLANTS_FILE = (
    "https://s3.us-west-2.amazonaws.com/"
    "pudl.catalyst.coop/stable/"
    "core_eia860__scd_plants.parquet"
)

SALES_FILE = (
    "https://s3.us-west-2.amazonaws.com/"
    "pudl.catalyst.coop/stable/"
    "core_eia861__yearly_sales.parquet"
)

YEAR_START = 2020
YEAR_END = 2024

# utility_id_eia -> display name. Each of these is a specific regulated
# operating utility, NOT its parent holding company -- e.g. 54913 is "NSTAR
# Electric", the Massachusetts electric utility subsidiary of Eversource
# Energy. It excludes Connecticut Light & Power, Public Service of New
# Hampshire, and the rest of Eversource's subsidiaries. Similarly "Con Edison"
# here means Consolidated Edison Company of New York (CECONY), not the
# publicly-traded parent Consolidated Edison, Inc. NYSEG and United
# Illuminating are both Avangrid subsidiaries -- not independent competitors
# at the parent-company level.
UTILITIES = {
    13511: "NYSEG",
    54913: "NSTAR Electric",
    4226: "Con Edison",
    19497: "United Illuminating",
}

# balancing_authority_code_eia -> display name. NYSEG/Con Edison sit in NYISO;
# Eversource/United Illuminating sit in ISO-NE. NOTE: the plants table's
# `iso_rto_code` column is only populated for 2010-2012 and is empty for
# 2020-2024 -- `balancing_authority_code_eia` is the field that's actually
# populated for our target years.
REGIONS = {
    "NYIS": "NYISO",
    "ISNE": "ISO-NE",
}

GENERATION_MIX_OUTPUT = Path(__file__).parent / "site" / "data" / "generation_mix.json"
REGIONAL_MIX_OUTPUT = Path(__file__).parent / "site" / "data" / "regional_grid_mix.json"
RESIDENTIAL_RATES_OUTPUT = Path(__file__).parent / "site" / "data" / "residential_rates.json"

BASE_RATES_CSV = Path(__file__).parent / "data" / "processed" / "base_rates_2020_2024.csv"
BASE_RATES_OUTPUT = Path(__file__).parent / "site" / "data" / "base_rates.json"
CHART_DATA_OUTPUT = Path(__file__).parent / "site" / "data" / "chart_data.js"


def fetch_generation(con):
    utility_ids = ", ".join(str(uid) for uid in UTILITIES)
    query = f"""
        SELECT
            CAST(EXTRACT(YEAR FROM report_date) AS INTEGER) AS year,
            utility_id_eia,
            COALESCE(fuel_type_code_pudl, energy_source_code, 'unknown') AS fuel,
            SUM(net_generation_mwh) AS mwh
        FROM read_parquet('{GENERATION_FUEL_FILE}')
        WHERE EXTRACT(YEAR FROM report_date) BETWEEN {YEAR_START} AND {YEAR_END}
          AND utility_id_eia IN ({utility_ids})
        GROUP BY 1, 2, 3
    """
    return con.execute(query).df()


def fetch_regional_generation(con):
    ba_codes = ", ".join(f"'{code}'" for code in REGIONS)
    query = f"""
        SELECT
            CAST(EXTRACT(YEAR FROM g.report_date) AS INTEGER) AS year,
            p.balancing_authority_code_eia,
            COALESCE(g.fuel_type_code_pudl, g.energy_source_code, 'unknown') AS fuel,
            SUM(g.net_generation_mwh) AS mwh
        FROM read_parquet('{GENERATION_FUEL_FILE}') g
        JOIN read_parquet('{PLANTS_FILE}') p
          ON g.plant_id_eia = p.plant_id_eia AND g.report_date = p.report_date
        WHERE EXTRACT(YEAR FROM g.report_date) BETWEEN {YEAR_START} AND {YEAR_END}
          AND p.balancing_authority_code_eia IN ({ba_codes})
        GROUP BY 1, 2, 3
    """
    return con.execute(query).df()


def fetch_residential_rates(con):
    utility_ids = ", ".join(str(uid) for uid in UTILITIES)
    query = f"""
        SELECT
            CAST(EXTRACT(YEAR FROM report_date) AS INTEGER) AS year,
            utility_id_eia,
            SUM(sales_revenue) AS revenue,
            SUM(sales_mwh) AS mwh
        FROM read_parquet('{SALES_FILE}')
        WHERE EXTRACT(YEAR FROM report_date) BETWEEN {YEAR_START} AND {YEAR_END}
          AND utility_id_eia IN ({utility_ids})
          AND customer_class = 'residential'
        GROUP BY 1, 2
    """
    return con.execute(query).df()


def build_residential_rate_records(df):
    df = df.copy()
    df["utility"] = df["utility_id_eia"].map(UTILITIES)
    df["cents_per_kwh"] = 100 * df["revenue"] / (df["mwh"] * 1000)

    records = df[["utility", "year", "cents_per_kwh"]].sort_values(["utility", "year"])
    return records.to_dict(orient="records")


def build_base_rate_records(df):
    df = df.copy()
    records = df[
        [
            "utility",
            "year",
            "fixed_customer_charge_usd_month",
            "base_distribution_rate_usd_kwh",
            "modeled_base_delivery_bill_usd",
        ]
    ].sort_values(["utility", "year"])
    return records.to_dict(orient="records")


def _build_records(df, id_col, id_map, group_key):
    df = df.copy()
    df[group_key] = df[id_col].map(id_map)
    df["fuel"] = df["fuel"].astype(str).str.replace("_", " ", regex=False).str.title()

    positive = df[df["mwh"] > 0].copy()
    positive["total_mwh"] = positive.groupby(["year", group_key])["mwh"].transform("sum")
    positive["share_pct"] = 100 * positive["mwh"] / positive["total_mwh"]

    records = positive[
        [group_key, "year", "fuel", "mwh", "share_pct", "total_mwh"]
    ].sort_values([group_key, "year", "fuel"])
    return records.to_dict(orient="records")


def build_records(df):
    return _build_records(df, "utility_id_eia", UTILITIES, "utility")


def build_regional_records(df):
    return _build_records(df, "balancing_authority_code_eia", REGIONS, "region")


def _write_json(records, output_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as f:
        json.dump(records, f, indent=2)
    print(f"Wrote {len(records)} records to {output_path}")


def _write_chart_data(datasets, output_path=CHART_DATA_OUTPUT):
    """Write the same chart records as a browser-loadable JavaScript object."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = "window.NE_NY_CHART_DATA = " + json.dumps(datasets, indent=2) + ";\n"
    output_path.write_text(payload)
    print(f"Wrote local chart data bundle to {output_path}")


def main():
    con = duckdb.connect()
    try:
        con.execute("LOAD httpfs")
    except duckdb.Error:
        con.execute("INSTALL httpfs")
        con.execute("LOAD httpfs")

    generation_df = fetch_generation(con)
    if generation_df.empty:
        raise ValueError("No generation records returned for the target utilities/years.")
    generation_records = build_records(generation_df)

    regional_df = fetch_regional_generation(con)
    if regional_df.empty:
        raise ValueError("No generation records returned for the target regions/years.")
    regional_records = build_regional_records(regional_df)

    rates_df = fetch_residential_rates(con)
    if rates_df.empty:
        raise ValueError("No residential rate records returned for the target utilities/years.")
    rate_records = build_residential_rate_records(rates_df)

    base_rates_df = pd.read_csv(BASE_RATES_CSV)
    if base_rates_df.empty:
        raise ValueError(f"No base rate records found in {BASE_RATES_CSV}.")
    base_rate_records = build_base_rate_records(base_rates_df)

    _write_json(generation_records, GENERATION_MIX_OUTPUT)
    _write_json(regional_records, REGIONAL_MIX_OUTPUT)
    _write_json(rate_records, RESIDENTIAL_RATES_OUTPUT)
    _write_json(base_rate_records, BASE_RATES_OUTPUT)
    _write_chart_data(
        {
            "generationRecords": generation_records,
            "regionalRecords": regional_records,
            "rateRecords": rate_records,
            "baseRateRecords": base_rate_records,
        }
    )


if __name__ == "__main__":
    main()
