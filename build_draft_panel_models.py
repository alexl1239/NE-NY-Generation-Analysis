"""Build the professor-facing draft panel models and analysis table.

This is deliberately a decision aid, not a causal model. The primary price
specifications use the same complete-case rows so that changes in the ownership
coefficients are not caused by changing samples:

    real price = ownership + ISO + year + reporting-method indicator
    real price = baseline terms + routine SAIDI
    real price = baseline terms + routine CAIDI

Prices are modeled separately for residential, commercial, and industrial
customers. State-control versions and the existing 42-utility price-only sample are
stored as compact decision checks. Routine SAIDI and CAIDI are also modeled as
separate outcomes, following the professors' proposed dependent variables.

Run: python3 build_draft_panel_models.py
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from build_price_models import (
    CPI_U_ANNUAL_2013_100,
    CUSTOMER_CLASSES,
    OWNERSHIP_TERMS,
    T_CRITICAL_95,
    cluster_robust_covariance,
)


PROJECT_ROOT = Path(__file__).resolve().parent
PRICE_INPUT = PROJECT_ROOT / "data" / "processed" / "utility_price_panel_2013_2024.csv"
EXPANDED_PRICE_INPUT = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "utility_price_panel_expanded_2013_2024.csv"
)
RELIABILITY_INPUT = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "reliability_coverage_audit_2013_2024.csv"
)

PROCESSED_ANALYSIS_OUTPUT = (
    PROJECT_ROOT / "data" / "processed" / "draft_panel_model_analysis.csv"
)
PROCESSED_RESULTS_OUTPUT = (
    PROJECT_ROOT / "data" / "processed" / "draft_panel_model_results.json"
)
SITE_ANALYSIS_OUTPUT = PROJECT_ROOT / "site" / "data" / "draft_panel_model_analysis.csv"
SITE_RESULTS_OUTPUT = PROJECT_ROOT / "site" / "data" / "draft_panel_model_results.json"
SITE_RESULTS_JS_OUTPUT = (
    PROJECT_ROOT / "site" / "data" / "draft_panel_model_results.js"
)

SAIDI_FIELD = "saidi_wo_major_event_days_minutes"
CAIDI_FIELD = "caidi_wo_major_event_days_minutes"
SAIDI_ANALYSIS_FIELD = "routine_saidi_minutes"
CAIDI_ANALYSIS_FIELD = "routine_caidi_minutes"
REPORTING_TERM = "reporting_other_standard"

TERM_LABELS = {
    "intercept": "Intercept",
    "ownership_MTC": "MTC compared with DOM",
    "ownership_COOP": "COOP compared with DOM",
    "iso_ISONE": "ISO-NE compared with NYISO",
    REPORTING_TERM: "Other reporting method compared with IEEE",
    "routine_saidi_per_100_minutes": "100 additional routine SAIDI minutes",
    "routine_caidi_per_10_minutes": "10 additional routine CAIDI minutes",
}


def _beta_continued_fraction(a: float, b: float, x: float) -> float:
    """Evaluate the incomplete-beta continued fraction.

    This is the standard Lentz-algorithm form used in numerical references. It keeps
    the project self-contained because SciPy is not a project dependency.
    """

    max_iterations = 300
    epsilon = 3e-14
    floor = 1e-300
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < floor:
        d = floor
    d = 1.0 / d
    value = d

    for iteration in range(1, max_iterations + 1):
        twice = 2 * iteration
        numerator = (
            iteration * (b - iteration) * x / ((qam + twice) * (a + twice))
        )
        d = 1.0 + numerator * d
        if abs(d) < floor:
            d = floor
        c = 1.0 + numerator / c
        if abs(c) < floor:
            c = floor
        d = 1.0 / d
        value *= d * c

        numerator = -(
            (a + iteration)
            * (qab + iteration)
            * x
            / ((a + twice) * (qap + twice))
        )
        d = 1.0 + numerator * d
        if abs(d) < floor:
            d = floor
        c = 1.0 + numerator / c
        if abs(c) < floor:
            c = floor
        d = 1.0 / d
        change = d * c
        value *= change
        if abs(change - 1.0) < epsilon:
            return value

    raise ArithmeticError("Incomplete-beta calculation did not converge")


def regularized_incomplete_beta(a: float, b: float, x: float) -> float:
    """Return the regularized incomplete beta I_x(a, b)."""

    if not 0.0 <= x <= 1.0:
        raise ValueError(f"Incomplete-beta x must be in [0, 1], found {x}")
    if x == 0.0:
        return 0.0
    if x == 1.0:
        return 1.0

    front = math.exp(
        math.lgamma(a + b)
        - math.lgamma(a)
        - math.lgamma(b)
        + a * math.log(x)
        + b * math.log1p(-x)
    )
    if x < (a + 1.0) / (a + b + 2.0):
        value = front * _beta_continued_fraction(a, b, x) / a
    else:
        value = 1.0 - front * _beta_continued_fraction(b, a, 1.0 - x) / b
    return min(1.0, max(0.0, value))


def student_t_two_sided_p_value(t_statistic: float, degrees_of_freedom: int) -> float:
    """Return the exact two-sided Student-t p-value via the beta identity."""

    if degrees_of_freedom <= 0:
        raise ValueError("Student-t degrees of freedom must be positive")
    if not math.isfinite(t_statistic):
        return 0.0
    x = degrees_of_freedom / (degrees_of_freedom + t_statistic**2)
    return regularized_incomplete_beta(degrees_of_freedom / 2.0, 0.5, x)


def field_is_excluded(row: pd.Series, field: str) -> bool:
    excluded = row.get("analysis_excluded_fields")
    if pd.isna(excluded) or not str(excluded).strip():
        return False
    return field in str(excluded).split("|")


def iso_market(state: str) -> str:
    return "NYISO" if state == "NY" else "ISO-NE"


def add_real_prices(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy()
    factors = output["year"].map(
        lambda year: CPI_U_ANNUAL_2013_100[2024]
        / CPI_U_ANNUAL_2013_100[int(year)]
    )
    for customer_class in CUSTOMER_CLASSES:
        published = f"{customer_class}_average_price_cents_kwh"
        real = f"real_{customer_class}_price_2024_cents_kwh"
        output[real] = output[published] * factors
    return output


def build_analysis_table() -> pd.DataFrame:
    price = pd.read_csv(PRICE_INPUT)
    reliability = pd.read_csv(RELIABILITY_INPUT)
    if len(price) != 360 or price["panel_id"].nunique() != 30:
        raise ValueError("Expected the reviewed 30-utility, 360-row price panel")
    if len(reliability) != 360 or reliability["panel_id"].nunique() != 30:
        raise ValueError("Expected the reviewed 30-utility, 360-row reliability audit")

    reliability[SAIDI_ANALYSIS_FIELD] = reliability[SAIDI_FIELD].where(
        reliability[SAIDI_FIELD].notna()
        & ~reliability.apply(field_is_excluded, axis=1, field=SAIDI_FIELD)
    )
    reliability[CAIDI_ANALYSIS_FIELD] = reliability[CAIDI_FIELD].where(
        reliability[CAIDI_FIELD].notna()
        & ~reliability.apply(field_is_excluded, axis=1, field=CAIDI_FIELD)
    )

    reliability_columns = [
        "panel_id",
        "year",
        "reporting_standard",
        "analysis_excluded_fields",
        "reliability_row_status",
        "reliability_customers",
        SAIDI_ANALYSIS_FIELD,
        CAIDI_ANALYSIS_FIELD,
        "source_file_url",
    ]
    if "source_file_url" not in reliability.columns:
        reliability = reliability.rename(
            columns={"eia_source_file_url": "source_file_url"}
        )

    analysis = price.merge(
        reliability[reliability_columns],
        on=["panel_id", "year"],
        how="left",
        validate="one_to_one",
    )
    if analysis["reporting_standard"].isna().all():
        raise ValueError("Price and reliability panels did not match")
    analysis["iso_market"] = analysis["state"].map(iso_market)
    analysis["routine_saidi_per_100_minutes"] = (
        analysis[SAIDI_ANALYSIS_FIELD] / 100.0
    )
    analysis["routine_caidi_per_10_minutes"] = (
        analysis[CAIDI_ANALYSIS_FIELD] / 10.0
    )
    analysis[REPORTING_TERM] = (
        analysis["reporting_standard"] == "other_standard"
    ).astype(float)
    analysis = add_real_prices(analysis)

    for customer_class in CUSTOMER_CLASSES:
        real_price = f"real_{customer_class}_price_2024_cents_kwh"
        analysis[f"included_{customer_class}_common_sample"] = (
            analysis[
                [
                    real_price,
                    SAIDI_ANALYSIS_FIELD,
                    CAIDI_ANALYSIS_FIELD,
                    "reporting_standard",
                ]
            ]
            .notna()
            .all(axis=1)
        )

    selected_columns = [
        "panel_id",
        "utility_id_eia",
        "display_name",
        "state",
        "iso_market",
        "year",
        "ownership",
        "ownership_2024",
        "reporting_standard",
        REPORTING_TERM,
        "reliability_row_status",
        "reliability_customers",
        SAIDI_ANALYSIS_FIELD,
        "routine_saidi_per_100_minutes",
        CAIDI_ANALYSIS_FIELD,
        "routine_caidi_per_10_minutes",
    ]
    for customer_class in CUSTOMER_CLASSES:
        selected_columns.extend(
            [
                f"{customer_class}_average_price_cents_kwh",
                f"real_{customer_class}_price_2024_cents_kwh",
                f"bundled_{customer_class}_customer_share_pct",
                f"included_{customer_class}_common_sample",
            ]
        )
    selected_columns.extend(
        [
            "analysis_excluded_fields",
            "source_report",
            "source_url",
            "source_file_url",
        ]
    )
    return analysis[selected_columns].sort_values(["panel_id", "year"])


def build_design_matrix(
    frame: pd.DataFrame,
    geo_control: str,
    reliability_predictor: str | None,
    include_reporting_method: bool,
) -> tuple[np.ndarray, list[str]]:
    columns: list[np.ndarray] = [np.ones(len(frame), dtype=float)]
    names = ["intercept"]

    for ownership in OWNERSHIP_TERMS:
        columns.append((frame["ownership"] == ownership).to_numpy(dtype=float))
        names.append(f"ownership_{ownership}")

    if geo_control == "iso":
        columns.append((frame["iso_market"] == "ISO-NE").to_numpy(dtype=float))
        names.append("iso_ISONE")
    elif geo_control == "state":
        for state in sorted(frame["state"].unique())[1:]:
            columns.append((frame["state"] == state).to_numpy(dtype=float))
            names.append(f"state_{state}")
    else:
        raise ValueError(f"Unknown geographic control: {geo_control}")

    if include_reporting_method:
        columns.append(frame[REPORTING_TERM].to_numpy(dtype=float))
        names.append(REPORTING_TERM)

    if reliability_predictor:
        columns.append(frame[reliability_predictor].to_numpy(dtype=float))
        names.append(reliability_predictor)

    for year in sorted(frame["year"].unique())[1:]:
        columns.append((frame["year"] == year).to_numpy(dtype=float))
        names.append(f"year_{year}")
    return np.column_stack(columns), names


def fit_model(
    frame: pd.DataFrame,
    *,
    model_id: str,
    outcome_column: str,
    outcome_label: str,
    outcome_unit: str,
    customer_class: str | None,
    specification: str,
    geo_control: str,
    reliability_predictor: str | None,
    include_reporting_method: bool,
) -> dict[str, object]:
    design, names = build_design_matrix(
        frame,
        geo_control,
        reliability_predictor,
        include_reporting_method,
    )
    outcome = frame[outcome_column].to_numpy(dtype=float)
    rank = int(np.linalg.matrix_rank(design))
    if rank != design.shape[1]:
        raise ValueError(
            f"Rank-deficient design for {model_id}: {rank}/{design.shape[1]}"
        )

    coefficients = np.linalg.lstsq(design, outcome, rcond=None)[0]
    residuals = outcome - design @ coefficients
    covariance = cluster_robust_covariance(
        design, residuals, frame["panel_id"].to_numpy()
    )
    variances = np.diag(covariance)
    if np.any(variances < -1e-10):
        raise ValueError(f"Negative coefficient variance in {model_id}")
    standard_errors = np.sqrt(np.maximum(variances, 0.0))
    cluster_count = int(frame["panel_id"].nunique())
    degrees_of_freedom = cluster_count - 1
    if degrees_of_freedom not in T_CRITICAL_95:
        raise ValueError(f"Missing 95% t critical value for {degrees_of_freedom} df")
    critical_value = T_CRITICAL_95[degrees_of_freedom]

    coefficient_results = []
    for index, term in enumerate(names):
        estimate = float(coefficients[index])
        standard_error = float(standard_errors[index])
        if standard_error == 0:
            t_statistic = math.copysign(math.inf, estimate) if estimate else 0.0
        else:
            t_statistic = estimate / standard_error
        p_value = student_t_two_sided_p_value(t_statistic, degrees_of_freedom)
        low = estimate - critical_value * standard_error
        high = estimate + critical_value * standard_error
        coefficient_results.append(
            {
                "term": term,
                "label": TERM_LABELS.get(
                    term,
                    term.replace("year_", "Year ").replace("state_", "State "),
                ),
                "estimate": estimate,
                "standard_error": standard_error,
                "t_statistic": float(t_statistic),
                "p_value": float(p_value),
                "confidence_95_low": float(low),
                "confidence_95_high": float(high),
                "confidence_interval_excludes_zero": bool(low > 0 or high < 0),
            }
        )

    total_sum_squares = float(np.sum((outcome - outcome.mean()) ** 2))
    residual_sum_squares = float(residuals @ residuals)
    r_squared = 1.0 - residual_sum_squares / total_sum_squares
    observation_count, parameter_count = design.shape
    adjusted_r_squared = 1.0 - (1.0 - r_squared) * (
        (observation_count - 1) / (observation_count - parameter_count)
    )

    return {
        "model_id": model_id,
        "customer_class": customer_class,
        "specification": specification,
        "outcome_column": outcome_column,
        "outcome_label": outcome_label,
        "outcome_unit": outcome_unit,
        "geographic_control": geo_control,
        "reliability_predictor": reliability_predictor,
        "observation_count": int(observation_count),
        "utility_cluster_count": cluster_count,
        "ownership_observation_counts": {
            str(key): int(value)
            for key, value in frame["ownership"].value_counts().sort_index().items()
        },
        "ownership_utility_counts": {
            str(key): int(value)
            for key, value in frame.groupby("ownership")["panel_id"]
            .nunique()
            .sort_index()
            .items()
        },
        "parameter_count": int(parameter_count),
        "design_rank": rank,
        "cluster_degrees_of_freedom": degrees_of_freedom,
        "r_squared": float(r_squared),
        "adjusted_r_squared": float(adjusted_r_squared),
        "coefficients": coefficient_results,
    }


def price_models(analysis: pd.DataFrame) -> list[dict[str, object]]:
    models = []
    specifications = (
        ("baseline", None),
        ("saidi", "routine_saidi_per_100_minutes"),
        ("caidi", "routine_caidi_per_10_minutes"),
    )
    for customer_class in CUSTOMER_CLASSES:
        sample_flag = f"included_{customer_class}_common_sample"
        frame = analysis.loc[analysis[sample_flag]].copy()
        outcome = f"real_{customer_class}_price_2024_cents_kwh"
        for specification, reliability_predictor in specifications:
            models.append(
                fit_model(
                    frame,
                    model_id=f"{customer_class}_iso_{specification}",
                    outcome_column=outcome,
                    outcome_label=(
                        f"Inflation-adjusted {customer_class} bundled average price"
                    ),
                    outcome_unit="2024 cents per kWh",
                    customer_class=customer_class,
                    specification=specification,
                    geo_control="iso",
                    reliability_predictor=reliability_predictor,
                    include_reporting_method=True,
                )
            )
    return models


def state_sensitivity_models(analysis: pd.DataFrame) -> list[dict[str, object]]:
    models = []
    specifications = (
        ("baseline", None),
        ("saidi", "routine_saidi_per_100_minutes"),
        ("caidi", "routine_caidi_per_10_minutes"),
    )
    for customer_class in CUSTOMER_CLASSES:
        frame = analysis.loc[
            analysis[f"included_{customer_class}_common_sample"]
        ].copy()
        outcome = f"real_{customer_class}_price_2024_cents_kwh"
        for specification, reliability_predictor in specifications:
            models.append(
                fit_model(
                    frame,
                    model_id=f"{customer_class}_state_{specification}",
                    outcome_column=outcome,
                    outcome_label=(
                        f"Inflation-adjusted {customer_class} bundled average price"
                    ),
                    outcome_unit="2024 cents per kWh",
                    customer_class=customer_class,
                    specification=specification,
                    geo_control="state",
                    reliability_predictor=reliability_predictor,
                    include_reporting_method=True,
                )
            )
    return models


def reliability_outcome_models(
    analysis: pd.DataFrame,
    geo_control: str = "iso",
) -> list[dict[str, object]]:
    configs = (
        (
            "saidi",
            SAIDI_ANALYSIS_FIELD,
            "Routine SAIDI",
            "minutes per customer",
        ),
        (
            "caidi",
            CAIDI_ANALYSIS_FIELD,
            "Routine CAIDI",
            "minutes per interruption",
        ),
    )
    models = []
    for metric, outcome, label, unit in configs:
        frame = analysis.loc[
            analysis[outcome].notna() & analysis["reporting_standard"].notna()
        ].copy()
        models.append(
            fit_model(
                frame,
                model_id=f"reliability_outcome_{geo_control}_{metric}",
                outcome_column=outcome,
                outcome_label=label,
                outcome_unit=unit,
                customer_class=None,
                specification=metric,
                geo_control=geo_control,
                reliability_predictor=None,
                include_reporting_method=True,
            )
        )
    return models


def expanded_price_models() -> list[dict[str, object]]:
    expanded = add_real_prices(pd.read_csv(EXPANDED_PRICE_INPUT))
    expanded["iso_market"] = expanded["state"].map(iso_market)
    models = []
    for customer_class in CUSTOMER_CLASSES:
        outcome = f"real_{customer_class}_price_2024_cents_kwh"
        frame = expanded.loc[expanded[outcome].notna()].copy()
        models.append(
            fit_model(
                frame,
                model_id=f"expanded_{customer_class}_iso_baseline",
                outcome_column=outcome,
                outcome_label=(
                    f"Inflation-adjusted {customer_class} bundled average price"
                ),
                outcome_unit="2024 cents per kWh",
                customer_class=customer_class,
                specification="baseline",
                geo_control="iso",
                reliability_predictor=None,
                include_reporting_method=False,
            )
        )
    return models


def coefficient(model: dict[str, object], term: str) -> dict[str, object]:
    for row in model["coefficients"]:  # type: ignore[index]
        if row["term"] == term:
            return row
    raise KeyError(f"{term} not found in {model['model_id']}")


def build_diagnostics(
    analysis: pd.DataFrame,
    models: list[dict[str, object]],
) -> dict[str, object]:
    common_samples = {}
    correlations = {}
    for customer_class in CUSTOMER_CLASSES:
        frame = analysis.loc[
            analysis[f"included_{customer_class}_common_sample"]
        ]
        common_samples[customer_class] = {
            "observation_count": int(len(frame)),
            "utility_count": int(frame["panel_id"].nunique()),
            "ownership_utility_counts": {
                str(key): int(value)
                for key, value in frame.groupby("ownership")["panel_id"]
                .nunique()
                .sort_index()
                .items()
            },
        }
        correlations[customer_class] = float(
            frame[[SAIDI_ANALYSIS_FIELD, CAIDI_ANALYSIS_FIELD]].corr().iloc[0, 1]
        )

    coefficient_changes = {}
    for customer_class in CUSTOMER_CLASSES:
        class_models = {
            str(model["specification"]): model
            for model in models
            if model["customer_class"] == customer_class
        }
        coefficient_changes[customer_class] = {}
        for ownership in OWNERSHIP_TERMS:
            term = f"ownership_{ownership}"
            baseline = float(coefficient(class_models["baseline"], term)["estimate"])
            coefficient_changes[customer_class][ownership] = {
                "baseline_estimate": baseline,
                "saidi_estimate": float(
                    coefficient(class_models["saidi"], term)["estimate"]
                ),
                "caidi_estimate": float(
                    coefficient(class_models["caidi"], term)["estimate"]
                ),
                "saidi_change_from_baseline": float(
                    coefficient(class_models["saidi"], term)["estimate"] - baseline
                ),
                "caidi_change_from_baseline": float(
                    coefficient(class_models["caidi"], term)["estimate"] - baseline
                ),
            }

    return {
        "selected_panel_rows": int(len(analysis)),
        "selected_panel_utilities": int(analysis["panel_id"].nunique()),
        "selected_panel_years": [
            int(analysis["year"].min()),
            int(analysis["year"].max()),
        ],
        "selected_panel_ownership_counts_2024": {
            str(key): int(value)
            for key, value in analysis.drop_duplicates("panel_id")["ownership_2024"]
            .value_counts()
            .sort_index()
            .items()
        },
        "common_samples": common_samples,
        "routine_saidi_caidi_correlation": correlations,
        "ownership_coefficient_changes": coefficient_changes,
    }


def build_results(analysis: pd.DataFrame | None = None) -> dict[str, object]:
    if analysis is None:
        analysis = build_analysis_table()
    primary_models = price_models(analysis)
    state_models = state_sensitivity_models(analysis)
    reliability_models = reliability_outcome_models(analysis, "iso")
    reliability_state_models = reliability_outcome_models(analysis, "state")
    expanded_models = expanded_price_models()
    return {
        "title": "Draft panel model: ownership, reliability, and price",
        "status": "Preliminary decision aid; not final and not causal",
        "years": "2013-2024",
        "selected_utility_count": 30,
        "primary_sample_rule": (
            "Same complete-case utility-years with a published customer-class price, "
            "usable routine SAIDI, usable routine CAIDI, and a known reliability "
            "reporting method"
        ),
        "reference_categories": {
            "ownership": "DOM",
            "iso_market": "NYISO",
            "reporting_method": "ieee_standard",
            "year": 2013,
        },
        "price_outcome": "EIA bundled average price in constant 2024 cents per kWh",
        "reliability_definitions": {
            "saidi": "Routine outage minutes per customer, excluding major event days",
            "caidi": "Routine minutes per interruption, excluding major event days",
        },
        "primary_price_models": (
            "Unweighted pooled panel OLS with ownership, ISO, year, and reliability-"
            "reporting-method indicators; SAIDI and CAIDI enter separately"
        ),
        "state_sensitivity": "State indicators replace the ISO indicator",
        "expanded_price_check": (
            "Price-only baseline using the existing 42-utility sample selected with "
            "at least 10,000 residential customers in 2024"
        ),
        "uncertainty": (
            "CR1 standard errors clustered by utility; two-sided Student-t p-values "
            "and 95% intervals use clusters minus one degrees of freedom"
        ),
        "weighting": "Each usable utility-year counts once; no customer weighting",
        "outlier_rule": (
            "No automatic deletion; only source-audited exclusions are applied"
        ),
        "interpretation_limit": (
            "Associational, not causal. Reliability and ownership may both reflect "
            "regulation, geography, infrastructure, customer mix, and other omitted "
            "factors."
        ),
        "roi_roe_note": (
            "ROI/ROE is not included because audited coverage is limited and "
            "cooperatives do not have a directly comparable authorized shareholder "
            "return."
        ),
        "source_data": [
            str(PRICE_INPUT.relative_to(PROJECT_ROOT)),
            str(RELIABILITY_INPUT.relative_to(PROJECT_ROOT)),
            str(EXPANDED_PRICE_INPUT.relative_to(PROJECT_ROOT)),
        ],
        "cpi_u_annual_2013_100": CPI_U_ANNUAL_2013_100,
        "diagnostics": build_diagnostics(analysis, primary_models),
        "price_models": primary_models,
        "reliability_outcome_models": reliability_models,
        "decision_checks": {
            "state_control_models": state_models,
            "state_control_reliability_outcome_models": reliability_state_models,
            "expanded_price_models": expanded_models,
        },
    }


def write_outputs(analysis: pd.DataFrame, results: dict[str, object]) -> None:
    csv_payload = analysis.to_csv(index=False, lineterminator="\n")
    for output in (PROCESSED_ANALYSIS_OUTPUT, SITE_ANALYSIS_OUTPUT):
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(csv_payload)

    json_payload = json.dumps(results, indent=2, allow_nan=False) + "\n"
    for output in (PROCESSED_RESULTS_OUTPUT, SITE_RESULTS_OUTPUT):
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json_payload)
    SITE_RESULTS_JS_OUTPUT.write_text(
        "window.NE_NY_DRAFT_PANEL_MODEL_RESULTS = "
        + json.dumps(results, separators=(",", ":"), allow_nan=False)
        + ";\n"
    )


if __name__ == "__main__":
    analysis_table = build_analysis_table()
    write_outputs(analysis_table, build_results(analysis_table))
