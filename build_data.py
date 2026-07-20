"""Build site/data/generation_mix.json from PUDL's EIA-923 yearly
generation-fuel table.

Run: python3 build_data.py
"""
import json
from pathlib import Path

import duckdb
import pandas as pd

PUDL_FILE = (
    "https://s3.us-west-2.amazonaws.com/"
    "pudl.catalyst.coop/stable/"
    "out_eia923__yearly_generation_fuel_combined.parquet"
)

YEAR_START = 2020
YEAR_END = 2024

# utility_id_eia -> display name. 54913 is recorded in PUDL as "NSTAR Electric
# Company" -- the same legal entity as Eversource under an older name, not a
# parent-company rollup.
UTILITIES = {
    13511: "NYSEG",
    54913: "Eversource",
    4226: "Con Edison",
    19497: "United Illuminating",
}

OUTPUT_PATH = Path(__file__).parent / "site" / "data" / "generation_mix.json"


def fetch_generation(con):
    utility_ids = ", ".join(str(uid) for uid in UTILITIES)
    query = f"""
        SELECT
            CAST(EXTRACT(YEAR FROM report_date) AS INTEGER) AS year,
            utility_id_eia,
            COALESCE(fuel_type_code_pudl, energy_source_code, 'unknown') AS fuel,
            SUM(net_generation_mwh) AS mwh
        FROM read_parquet('{PUDL_FILE}')
        WHERE EXTRACT(YEAR FROM report_date) BETWEEN {YEAR_START} AND {YEAR_END}
          AND utility_id_eia IN ({utility_ids})
        GROUP BY 1, 2, 3
    """
    return con.execute(query).df()


def build_records(df):
    df = df.copy()
    df["utility"] = df["utility_id_eia"].map(UTILITIES)
    df["fuel"] = df["fuel"].astype(str).str.replace("_", " ", regex=False).str.title()

    positive = df[df["mwh"] > 0].copy()
    positive["total_mwh"] = positive.groupby(["year", "utility"])["mwh"].transform("sum")
    positive["share_pct"] = 100 * positive["mwh"] / positive["total_mwh"]

    records = positive[["utility", "year", "fuel", "mwh", "share_pct"]].sort_values(
        ["utility", "year", "fuel"]
    )
    return records.to_dict(orient="records")


def main():
    con = duckdb.connect()
    try:
        con.execute("LOAD httpfs")
    except duckdb.Error:
        con.execute("INSTALL httpfs")
        con.execute("LOAD httpfs")

    df = fetch_generation(con)
    if df.empty:
        raise ValueError("No generation records returned for the target utilities/years.")

    records = build_records(df)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w") as f:
        json.dump(records, f, indent=2)

    print(f"Wrote {len(records)} records to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
