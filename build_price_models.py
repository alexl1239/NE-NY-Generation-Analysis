"""Build simple ownership-price panel models for the research website.

The model is intentionally limited to the project's main question:

    real price = ownership indicators + state indicators + year indicators

DOM is the ownership reference group. Prices are converted to constant 2024 cents
with annual CPI-U. Ordinary least squares is unweighted, and uncertainty uses a
CR1 cluster-robust covariance matrix with utility as the cluster. Separate models
are estimated for residential, commercial, and industrial prices.

Run: python3 build_price_models.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent
INPUT = PROJECT_ROOT / "data" / "processed" / "utility_price_panel_2013_2024.csv"
PROCESSED_OUTPUT = (
    PROJECT_ROOT / "data" / "processed" / "ownership_price_model_results.json"
)
SITE_JSON_OUTPUT = PROJECT_ROOT / "site" / "data" / "ownership_price_model_results.json"
SITE_JS_OUTPUT = PROJECT_ROOT / "site" / "data" / "ownership_price_model_results.js"

CUSTOMER_CLASSES = ("residential", "commercial", "industrial")
OWNERSHIP_TERMS = ("MTC", "COOP")

# BLS annual CPI-U, all items, U.S. city average, rebased to 2013 = 100.
CPI_U_ANNUAL_2013_100 = {
    2013: 100.000,
    2014: 101.622,
    2015: 101.743,
    2016: 103.027,
    2017: 105.221,
    2018: 107.791,
    2019: 109.745,
    2020: 111.098,
    2021: 116.318,
    2022: 125.626,
    2023: 130.797,
    2024: 134.655,
}

# Two-sided 95% Student-t critical values for the cluster counts in this panel.
T_CRITICAL_95 = {
    10: 2.228139,
    11: 2.200985,
    12: 2.178813,
    13: 2.160369,
    14: 2.144787,
    15: 2.131450,
    16: 2.119905,
    17: 2.109816,
    18: 2.100922,
    19: 2.093024,
    20: 2.085963,
    21: 2.079614,
    22: 2.073873,
    23: 2.068658,
    24: 2.063899,
    25: 2.059539,
    26: 2.055529,
    27: 2.051831,
    28: 2.048407,
    29: 2.045230,
    30: 2.042272,
    31: 2.039513,
    32: 2.036933,
    33: 2.034515,
    34: 2.032245,
    35: 2.030108,
    36: 2.028094,
    37: 2.026192,
    38: 2.024394,
    39: 2.022691,
    40: 2.021075,
    41: 2.019541,
}


def build_design_matrix(frame: pd.DataFrame) -> tuple[np.ndarray, list[str]]:
    """Return an intercept, ownership indicators, state controls, and year controls."""

    columns: list[np.ndarray] = [np.ones(len(frame), dtype=float)]
    names = ["intercept"]

    for ownership in OWNERSHIP_TERMS:
        columns.append((frame["ownership"] == ownership).to_numpy(dtype=float))
        names.append(f"ownership_{ownership}")

    # Alphabetically first state and earliest year are omitted reference categories.
    for state in sorted(frame["state"].unique())[1:]:
        columns.append((frame["state"] == state).to_numpy(dtype=float))
        names.append(f"state_{state}")
    for year in sorted(frame["year"].unique())[1:]:
        columns.append((frame["year"] == year).to_numpy(dtype=float))
        names.append(f"year_{year}")

    return np.column_stack(columns), names


def cluster_robust_covariance(
    design: np.ndarray,
    residuals: np.ndarray,
    clusters: np.ndarray,
) -> np.ndarray:
    """Calculate the conventional CR1 utility-clustered covariance matrix."""

    bread = np.linalg.inv(design.T @ design)
    meat = np.zeros((design.shape[1], design.shape[1]), dtype=float)
    unique_clusters = np.unique(clusters)
    for cluster in unique_clusters:
        mask = clusters == cluster
        score = design[mask].T @ residuals[mask]
        meat += np.outer(score, score)

    observation_count, parameter_count = design.shape
    cluster_count = len(unique_clusters)
    correction = (cluster_count / (cluster_count - 1)) * (
        (observation_count - 1) / (observation_count - parameter_count)
    )
    return correction * bread @ meat @ bread


def fit_model(
    panel: pd.DataFrame,
    customer_class: str,
    coverage_rule: str,
) -> dict[str, object]:
    price_column = f"{customer_class}_average_price_cents_kwh"
    coverage_column = f"bundled_{customer_class}_customer_share_pct"
    frame = panel.loc[panel[price_column].notna()].copy()
    if coverage_rule == "majority_coverage":
        frame = frame.loc[frame[coverage_column] >= 50].copy()

    frame["real_price_2024_cents_kwh"] = frame[price_column] * frame["year"].map(
        lambda year: CPI_U_ANNUAL_2013_100[2024] / CPI_U_ANNUAL_2013_100[int(year)]
    )
    design, names = build_design_matrix(frame)
    outcome = frame["real_price_2024_cents_kwh"].to_numpy(dtype=float)
    rank = int(np.linalg.matrix_rank(design))
    if rank != design.shape[1]:
        raise ValueError(
            f"Design matrix is rank deficient for {customer_class} {coverage_rule}: "
            f"rank {rank}, columns {design.shape[1]}"
        )

    coefficients = np.linalg.lstsq(design, outcome, rcond=None)[0]
    residuals = outcome - design @ coefficients
    covariance = cluster_robust_covariance(
        design,
        residuals,
        frame["panel_id"].to_numpy(),
    )
    standard_errors = np.sqrt(np.diag(covariance))
    cluster_count = int(frame["panel_id"].nunique())
    degrees_of_freedom = cluster_count - 1
    if degrees_of_freedom not in T_CRITICAL_95:
        raise ValueError(
            f"Add the 95% t critical value for {degrees_of_freedom} degrees of freedom"
        )
    critical_value = T_CRITICAL_95[degrees_of_freedom]

    total_sum_squares = float(np.sum((outcome - outcome.mean()) ** 2))
    residual_sum_squares = float(residuals @ residuals)
    r_squared = 1 - residual_sum_squares / total_sum_squares

    ownership_results = []
    for ownership in OWNERSHIP_TERMS:
        index = names.index(f"ownership_{ownership}")
        estimate = float(coefficients[index])
        standard_error = float(standard_errors[index])
        confidence_low = estimate - critical_value * standard_error
        confidence_high = estimate + critical_value * standard_error
        ownership_results.append(
            {
                "ownership": ownership,
                "reference_ownership": "DOM",
                "estimate_cents_kwh": estimate,
                "standard_error": standard_error,
                "confidence_95_low": confidence_low,
                "confidence_95_high": confidence_high,
                "confidence_interval_excludes_zero": bool(
                    confidence_low > 0 or confidence_high < 0
                ),
            }
        )

    return {
        "customer_class": customer_class,
        "coverage_rule": coverage_rule,
        "observation_count": int(len(frame)),
        "utility_cluster_count": cluster_count,
        "parameter_count": int(design.shape[1]),
        "design_rank": rank,
        "r_squared": float(r_squared),
        "ownership_results": ownership_results,
    }


def build_results() -> dict[str, object]:
    panel = pd.read_csv(INPUT)
    if len(panel) != 360:
        raise ValueError(f"Expected 360 utility-year rows, found {len(panel)}")

    models = []
    for customer_class in CUSTOMER_CLASSES:
        models.append(fit_model(panel, customer_class, "all_published"))
        models.append(fit_model(panel, customer_class, "majority_coverage"))

    return {
        "title": "Ownership and inflation-adjusted utility price",
        "source_data": "data/processed/utility_price_panel_2013_2024.csv",
        "price_source": "EIA Electric Sales, Revenue, and Average Price",
        "cpi_source": "https://www.bls.gov/pir/spm/spm_chart_2025data.htm",
        "cpi_u_annual_2013_100": CPI_U_ANNUAL_2013_100,
        "inflation_formula": "published price multiplied by CPI-U(2024) divided by CPI-U(year)",
        "outcome": "EIA bundled average price in constant 2024 cents per kWh",
        "model": "Unweighted OLS with ownership, state, and year indicators",
        "reference_ownership": "DOM",
        "uncertainty": "95% CR1 confidence intervals clustered by utility, using a t critical value with clusters minus one degrees of freedom",
        "interpretation_limit": "Associational, not causal",
        "coverage_rules": {
            "all_published": "Every nonmissing EIA-published price",
            "majority_coverage": "Published prices covering at least 50% of bundled plus delivery-only customers in the same customer class",
        },
        "models": models,
    }


def write_results(results: dict[str, object]) -> None:
    payload = json.dumps(results, indent=2, sort_keys=False, allow_nan=False) + "\n"
    for output in (PROCESSED_OUTPUT, SITE_JSON_OUTPUT):
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload)
    SITE_JS_OUTPUT.write_text(
        "window.NE_NY_OWNERSHIP_PRICE_MODEL_RESULTS = "
        + json.dumps(results, separators=(",", ":"), allow_nan=False)
        + ";\n"
    )


if __name__ == "__main__":
    write_results(build_results())
