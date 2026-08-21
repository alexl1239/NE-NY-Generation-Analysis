"""Build the focused 10,000-customer expanded price robustness check.

The balanced 30-utility panel remains the presentation sample. This script applies a
pre-declared 2024 size threshold to the regional EIA/PUDL roster, copies the same
published EIA Tables 6-8 prices, and reruns the existing unweighted ownership-price
model. It does not create new individual-utility website panels.

Run with the project Python environment that includes DuckDB when the local expanded
coverage cache has not yet been created:

    python3 build_expanded_price_check.py
"""

from __future__ import annotations

import csv
import json
import tempfile
from collections import Counter
from pathlib import Path

import pandas as pd

import build_price_panel as price_panel
from build_price_models import CUSTOMER_CLASSES, fit_model


PROJECT_ROOT = Path(__file__).resolve().parent
ROSTER_INPUT = PROJECT_ROOT / "data" / "raw" / "pudl_eia861_ne_ny_2024_roster.csv"
SELECTED_CANDIDATES_INPUT = (
    PROJECT_ROOT / "data" / "processed" / "utility_panel_candidates_2024.csv"
)
COVERAGE_CACHE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "eia_esr"
    / "pudl_customer_coverage_expanded_2013_2024.csv"
)
CANDIDATES_OUTPUT = (
    PROJECT_ROOT / "data" / "processed" / "expanded_utility_candidates_2024.csv"
)
PANEL_OUTPUT = (
    PROJECT_ROOT / "data" / "processed" / "utility_price_panel_expanded_2013_2024.csv"
)
RESULT_OUTPUT = (
    PROJECT_ROOT / "data" / "processed" / "expanded_price_model_results.json"
)
SITE_RESULT_JSON = PROJECT_ROOT / "site" / "data" / "expanded_price_model_results.json"
SITE_RESULT_JS = PROJECT_ROOT / "site" / "data" / "expanded_price_model_results.js"

MINIMUM_RESIDENTIAL_CUSTOMERS_2024 = 10_000
EXPECTED_OWNERSHIP_COUNTS = {"MTC": 11, "DOM": 8, "COOP": 23}
NONSHAREHOLDER_ENTITY_TYPES = {"Cooperative", "Municipal", "Political Subdivision"}
NANTUCKET_UTILITY_ID = 13206
NANTUCKET_OWNERSHIP_SOURCE = (
    "https://www.nationalgridus.com/News/2023/11/"
    "National-Grid-Submits-Comprehensive-Performance-Investment-Plan-as-Part-of-"
    "Rate-Review-to-Build-a-Smarter%2C-Stronger%2C-Cleaner%2C-and-More-Equitable-"
    "Energy-Future/"
)
REGIONAL_ROSTER_SOURCE = (
    "https://s3.us-west-2.amazonaws.com/pudl.catalyst.coop/stable/"
    "core_eia861__yearly_sales.parquet"
)

# Aliases required only by utilities added to the 30-utility presentation sample.
EXPANDED_NAME_ALIASES: dict[int, tuple[str, ...]] = {}

CANDIDATE_FIELDS = [
    "panel_id",
    "utility_id_eia",
    "utility_name_eia",
    "display_name",
    "state",
    "ownership_2024",
    "eia_entity_type",
    "residential_customers_2024",
    "ultimate_parent_or_owner_2024",
    "parent_country_or_level",
    "ownership_history_note",
    "ownership_source_url",
    "selection_rule",
    "pudl_source_url",
]


def load_selected_candidates() -> dict[int, dict[str, str]]:
    with SELECTED_CANDIDATES_INPUT.open(newline="") as source:
        return {
            int(row["utility_id_eia"]): row for row in csv.DictReader(source)
        }


def load_expanded_candidates() -> list[dict[str, object]]:
    """Apply the pre-declared size rule and classify the 42 eligible utilities."""

    roster = pd.read_csv(ROSTER_INPUT)
    roster = roster.loc[
        roster["residential_customers_2024"]
        >= MINIMUM_RESIDENTIAL_CUSTOMERS_2024
    ].copy()
    selected = load_selected_candidates()
    candidates: list[dict[str, object]] = []

    for row in roster.sort_values(
        "residential_customers_2024", ascending=False
    ).itertuples(index=False):
        utility_id = int(row.utility_id_eia)
        states = str(row.states).split("|")
        if len(states) != 1:
            raise ValueError(
                f"Expanded candidate {utility_id} reports multiple states: {states}"
            )
        state = states[0]
        existing = selected.get(utility_id)
        if existing:
            ownership = existing["ownership_2024"]
            panel_id = existing["panel_id"]
            display_name = existing["display_name"]
            parent = existing["ultimate_parent_or_owner_2024"]
            parent_level = existing["parent_country_or_level"]
            history_note = existing["ownership_history_note"]
            ownership_source = existing["ownership_source_url"]
        elif utility_id == NANTUCKET_UTILITY_ID:
            ownership = "MTC"
            panel_id = "MTC_MA_NANTUCKET"
            display_name = "Nantucket Electric"
            parent = "National Grid plc"
            parent_level = "United Kingdom"
            history_note = "MTC throughout 2013-2024 under National Grid plc"
            ownership_source = NANTUCKET_OWNERSHIP_SOURCE
        elif row.eia_entity_type in NONSHAREHOLDER_ENTITY_TYPES:
            ownership = "COOP"
            panel_id = f"COOP_{state}_{utility_id}"
            display_name = str(row.utility_name_eia)
            parent = f"Local {str(row.eia_entity_type).lower()} ownership"
            parent_level = "Local/non-shareholder"
            history_note = (
                "Classified as local non-shareholder ownership; annual EIA ownership "
                "labels are validated while building the panel"
            )
            ownership_source = REGIONAL_ROSTER_SOURCE
        else:
            raise ValueError(
                f"Eligible investor-owned utility {utility_id} lacks a documented "
                "DOM/MTC classification"
            )

        candidates.append(
            {
                "panel_id": panel_id,
                "utility_id_eia": utility_id,
                "utility_name_eia": str(row.utility_name_eia),
                "display_name": display_name,
                "state": state,
                "ownership_2024": ownership,
                "eia_entity_type": str(row.eia_entity_type),
                "residential_customers_2024": int(row.residential_customers_2024),
                "ultimate_parent_or_owner_2024": parent,
                "parent_country_or_level": parent_level,
                "ownership_history_note": history_note,
                "ownership_source_url": ownership_source,
                "selection_rule": (
                    "At least 10,000 residential customers in the 2024 regional "
                    "EIA/PUDL roster"
                ),
                "pudl_source_url": REGIONAL_ROSTER_SOURCE,
            }
        )

    counts = Counter(str(row["ownership_2024"]) for row in candidates)
    if len(candidates) != 42 or dict(counts) != EXPECTED_OWNERSHIP_COUNTS:
        raise ValueError(
            f"Expected 42 expanded candidates {EXPECTED_OWNERSHIP_COUNTS}; "
            f"found {len(candidates)} {dict(counts)}"
        )
    return candidates


def ownership_for(candidate: dict[str, object], year: int) -> str:
    selected = load_selected_candidates().get(int(candidate["utility_id_eia"]))
    if selected:
        return price_panel.ownership_for(selected, year)
    return str(candidate["ownership_2024"])


def load_customer_coverage(candidates: list[dict[str, object]]) -> pd.DataFrame:
    if COVERAGE_CACHE.exists():
        coverage = pd.read_csv(COVERAGE_CACHE)
    else:
        try:
            import duckdb
        except ImportError as error:
            raise RuntimeError(
                "DuckDB is required once to create the expanded PUDL coverage cache"
            ) from error
        utility_ids = ", ".join(str(row["utility_id_eia"]) for row in candidates)
        customer_classes = ", ".join(
            f"'{sector}'" for sector in price_panel.SECTORS
        )
        query = f"""
            SELECT
                CAST(EXTRACT(YEAR FROM report_date) AS INTEGER) AS year,
                utility_id_eia,
                state,
                customer_class,
                service_type,
                SUM(customers) AS customers
            FROM read_parquet('{price_panel.PUDL_SALES_URL}')
            WHERE EXTRACT(YEAR FROM report_date) BETWEEN 2013 AND 2024
              AND utility_id_eia IN ({utility_ids})
              AND customer_class IN ({customer_classes})
              AND service_type IN ('bundled', 'delivery')
            GROUP BY 1, 2, 3, 4, 5
            ORDER BY 2, 1, 4, 5
        """
        coverage = duckdb.connect().execute(query).df()
        COVERAGE_CACHE.parent.mkdir(parents=True, exist_ok=True)
        coverage.to_csv(COVERAGE_CACHE, index=False)

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
            f"Expanded coverage cache is missing {sorted(required - set(coverage.columns))}"
        )
    coverage["year"] = coverage["year"].astype(int)
    coverage["utility_id_eia"] = coverage["utility_id_eia"].astype(int)
    return coverage


def customer_coverage_lookup(
    candidates: list[dict[str, object]],
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
    return {
        (
            int(row.utility_id_eia),
            str(row.state),
            int(row.year),
            str(row.customer_class),
        ): {
            "bundled": int(row.bundled),
            "delivery": int(row.delivery),
            "total": int(row.bundled + row.delivery),
        }
        for row in pivot.itertuples(index=False)
    }


def accepted_names(candidate: dict[str, object]) -> tuple[str, ...]:
    utility_id = int(candidate["utility_id_eia"])
    return (
        price_panel.PRICE_NAME_ALIASES.get(utility_id)
        or EXPANDED_NAME_ALIASES.get(utility_id)
        or (str(candidate["utility_name_eia"]),)
    )


def build_panel() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    candidates = load_expanded_candidates()
    coverage = customer_coverage_lookup(candidates)
    records: list[dict[str, object]] = []

    with tempfile.TemporaryDirectory(prefix="expanded-price-check-") as temporary:
        workdir = Path(temporary)
        for year in range(2013, 2025):
            tables = {
                sector: price_panel.read_eia_table(
                    year, details["table_number"], workdir
                )
                for sector, details in price_panel.SECTORS.items()
            }
            for candidate in candidates:
                utility_id = int(candidate["utility_id_eia"])
                state = str(candidate["state"])
                record: dict[str, object] = {
                    "panel_id": candidate["panel_id"],
                    "utility_id_eia": utility_id,
                    "utility_name_eia": candidate["utility_name_eia"],
                    "display_name": candidate["display_name"],
                    "state": state,
                    "year": year,
                    "ownership": ownership_for(candidate, year),
                    "ownership_2024": candidate["ownership_2024"],
                    "eia_entity_type_2024": candidate["eia_entity_type"],
                    "residential_customers_2024": candidate[
                        "residential_customers_2024"
                    ],
                    "selection_rule": candidate["selection_rule"],
                    "source_report": "EIA Electric Sales, Revenue, and Average Price",
                    "source_url": price_panel.source_url(year),
                    "ownership_source_url": candidate["ownership_source_url"],
                }
                annual_labels: set[str] = set()

                for sector, details in price_panel.SECTORS.items():
                    table = tables[sector]
                    normalized_names = {
                        price_panel.normalize_name(name)
                        for name in accepted_names(candidate)
                    }
                    matches = table[
                        (table["state"] == state)
                        & table["normalized_entity"].isin(normalized_names)
                    ]
                    if len(matches) > 1:
                        raise ValueError(
                            f"EIA {year} Table {details['table_number']} has multiple "
                            f"matches for {candidate['utility_name_eia']}"
                        )
                    counts = coverage.get(
                        (utility_id, state, year, sector),
                        {"bundled": 0, "delivery": 0, "total": 0},
                    )
                    source_row = matches.iloc[0] if len(matches) == 1 else None
                    if source_row is None:
                        if counts["bundled"] != 0:
                            raise ValueError(
                                f"Missing EIA {year} Table {details['table_number']} "
                                f"name match for {utility_id} {candidate['utility_name_eia']} "
                                f"with {counts['bundled']} PUDL bundled customers"
                            )
                        price = None
                        source_bundled = 0
                        source_status = "Not reported"
                    else:
                        source_bundled = int(float(source_row["customers"]))
                        if source_bundled != counts["bundled"]:
                            raise ValueError(
                                f"EIA/PUDL customer mismatch for {utility_id} {state} "
                                f"{year} {sector}: {source_bundled} vs {counts['bundled']}"
                            )
                        price = price_panel.numeric_or_none(
                            source_row["average_price_cents_kwh"]
                        )
                        source_status = "Reported" if price is not None else "Not reported"
                        annual_labels.add(str(source_row["eia_ownership_label"]))

                    total = counts["total"]
                    bundled_share = 100 * counts["bundled"] / total if total else None
                    if price is None:
                        coverage_flag = "no_published_price"
                    elif bundled_share < 50:
                        coverage_flag = "minority_coverage"
                    else:
                        coverage_flag = "majority_coverage"
                    record.update(
                        {
                            f"{sector}_average_price_cents_kwh": price,
                            f"bundled_{sector}_customers": source_bundled,
                            f"delivery_only_{sector}_customers": counts["delivery"],
                            f"total_distribution_{sector}_customers": total,
                            f"bundled_{sector}_customer_share_pct": bundled_share,
                            f"{sector}_coverage_flag": coverage_flag,
                            f"{sector}_source_status": source_status,
                        }
                    )

                if len(annual_labels) > 1:
                    raise ValueError(
                        f"Conflicting EIA ownership labels for {utility_id} {year}: "
                        f"{sorted(annual_labels)}"
                    )
                annual_label = next(iter(annual_labels), None)
                if (
                    candidate["ownership_2024"] == "COOP"
                    and annual_label == "Investor Owned"
                ):
                    raise ValueError(
                        f"Expanded COOP candidate {utility_id} is Investor Owned in {year}"
                    )
                record["eia_ownership_label"] = annual_label
                records.append(record)

    if len(records) != 42 * 12:
        raise ValueError(f"Expected 504 expanded utility-years, found {len(records)}")
    return candidates, records


def build_results(panel: pd.DataFrame) -> dict[str, object]:
    models = []
    for customer_class in CUSTOMER_CLASSES:
        models.append(fit_model(panel, customer_class, "all_published"))
        models.append(fit_model(panel, customer_class, "majority_coverage"))
    return {
        "title": "Expanded-sample ownership and inflation-adjusted utility price check",
        "purpose": "Robustness check; does not replace the balanced 30-utility overview",
        "sampling_rule": "At least 10,000 residential customers in the 2024 regional EIA/PUDL roster",
        "candidate_count": 42,
        "ownership_counts_2024": EXPECTED_OWNERSHIP_COUNTS,
        "years": "2013-2024",
        "outcome": "EIA bundled average price in constant 2024 cents per kWh",
        "model": "Unweighted OLS with ownership, state, and year indicators",
        "reference_ownership": "DOM",
        "uncertainty": "95% CR1 confidence intervals clustered by utility, using a t critical value with clusters minus one degrees of freedom",
        "interpretation_limit": "Associational, not causal",
        "source_data": str(PANEL_OUTPUT.relative_to(PROJECT_ROOT)),
        "models": models,
    }


def write_outputs(
    candidates: list[dict[str, object]], records: list[dict[str, object]]
) -> None:
    CANDIDATES_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(candidates)[CANDIDATE_FIELDS].to_csv(CANDIDATES_OUTPUT, index=False)
    panel = pd.DataFrame(records)
    panel.to_csv(PANEL_OUTPUT, index=False)
    results = build_results(panel)
    payload = json.dumps(results, indent=2, allow_nan=False) + "\n"
    RESULT_OUTPUT.write_text(payload)
    SITE_RESULT_JSON.parent.mkdir(parents=True, exist_ok=True)
    SITE_RESULT_JSON.write_text(payload)
    SITE_RESULT_JS.write_text(
        "window.NE_NY_EXPANDED_PRICE_MODEL_RESULTS = "
        + json.dumps(results, separators=(",", ":"), allow_nan=False)
        + ";\n"
    )


if __name__ == "__main__":
    write_outputs(*build_panel())
