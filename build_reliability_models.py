"""Build simple ownership-reliability models for the reviewed 30-utility panel.

Reliability is modeled as a separate service-quality outcome. The results do not
claim that reliability causes electricity prices. Primary models exclude major event
days and retain both EIA-permitted reporting methods with one reporting-method
indicator. IEEE-only and major-event versions are stored as sensitivity checks.

Run: python3 build_reliability_models.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from build_price_models import (
    OWNERSHIP_TERMS,
    T_CRITICAL_95,
    cluster_robust_covariance,
)


PROJECT_ROOT = Path(__file__).resolve().parent
INPUT = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "reliability_coverage_audit_2013_2024.csv"
)
PROCESSED_OUTPUT = (
    PROJECT_ROOT / "data" / "processed" / "ownership_reliability_model_results.json"
)
SITE_JSON_OUTPUT = (
    PROJECT_ROOT / "site" / "data" / "ownership_reliability_model_results.json"
)
SITE_JS_OUTPUT = (
    PROJECT_ROOT / "site" / "data" / "ownership_reliability_model_results.js"
)

METRICS = {
    "saidi": {
        "label": "SAIDI",
        "unit": "minutes per customer",
        "without_major_events": "saidi_wo_major_event_days_minutes",
        "with_major_events": "saidi_w_major_event_days_minutes",
    },
    "saifi": {
        "label": "SAIFI",
        "unit": "interruptions per customer",
        "without_major_events": "saifi_wo_major_event_days_customers",
        "with_major_events": "saifi_w_major_event_days_customers",
    },
    "caidi": {
        "label": "CAIDI",
        "unit": "minutes per interruption",
        "without_major_events": "caidi_wo_major_event_days_minutes",
        "with_major_events": "caidi_w_major_event_days_minutes",
    },
}


def field_is_excluded(row: pd.Series, field: str) -> bool:
    excluded = row.get("analysis_excluded_fields")
    if pd.isna(excluded) or not str(excluded).strip():
        return False
    return field in str(excluded).split("|")


def model_frame(
    audit: pd.DataFrame,
    field: str,
    reporting_sample: str,
) -> pd.DataFrame:
    frame = audit.loc[audit[field].notna()].copy()
    frame = frame.loc[~frame.apply(field_is_excluded, axis=1, field=field)].copy()
    if reporting_sample == "ieee_only":
        frame = frame.loc[frame["reporting_standard"] == "ieee_standard"].copy()
    if frame["reporting_standard"].isna().any():
        raise ValueError(f"Usable {field} rows contain a missing reporting standard")
    return frame


def build_design_matrix(
    frame: pd.DataFrame,
    reporting_sample: str,
) -> tuple[np.ndarray, list[str]]:
    columns: list[np.ndarray] = [np.ones(len(frame), dtype=float)]
    names = ["intercept"]
    for ownership in OWNERSHIP_TERMS:
        columns.append((frame["ownership"] == ownership).to_numpy(dtype=float))
        names.append(f"ownership_{ownership}")

    if reporting_sample == "all_methods":
        columns.append(
            (frame["reporting_standard"] == "other_standard").to_numpy(dtype=float)
        )
        names.append("reporting_other_standard")

    for state in sorted(frame["state"].unique())[1:]:
        columns.append((frame["state"] == state).to_numpy(dtype=float))
        names.append(f"state_{state}")
    for year in sorted(frame["year"].unique())[1:]:
        columns.append((frame["year"] == year).to_numpy(dtype=float))
        names.append(f"year_{year}")
    return np.column_stack(columns), names


def fit_model(
    audit: pd.DataFrame,
    metric: str,
    event_scope: str,
    reporting_sample: str,
) -> dict[str, object]:
    config = METRICS[metric]
    field = str(config[event_scope])
    frame = model_frame(audit, field, reporting_sample)
    design, names = build_design_matrix(frame, reporting_sample)
    outcome = frame[field].to_numpy(dtype=float)
    rank = int(np.linalg.matrix_rank(design))
    if rank != design.shape[1]:
        raise ValueError(
            f"Rank-deficient reliability model {metric} {event_scope} "
            f"{reporting_sample}: {rank}/{design.shape[1]}"
        )

    coefficients = np.linalg.lstsq(design, outcome, rcond=None)[0]
    residuals = outcome - design @ coefficients
    covariance = cluster_robust_covariance(
        design, residuals, frame["panel_id"].to_numpy()
    )
    standard_errors = np.sqrt(np.diag(covariance))
    cluster_count = int(frame["panel_id"].nunique())
    degrees_of_freedom = cluster_count - 1
    if degrees_of_freedom not in T_CRITICAL_95:
        raise ValueError(
            f"Missing t critical value for {degrees_of_freedom} reliability df"
        )
    critical_value = T_CRITICAL_95[degrees_of_freedom]
    total_sum_squares = float(np.sum((outcome - outcome.mean()) ** 2))
    residual_sum_squares = float(residuals @ residuals)

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
                "estimate": estimate,
                "unit": config["unit"],
                "standard_error": standard_error,
                "confidence_95_low": confidence_low,
                "confidence_95_high": confidence_high,
                "confidence_interval_excludes_zero": bool(
                    confidence_low > 0 or confidence_high < 0
                ),
            }
        )

    return {
        "metric": metric,
        "metric_label": config["label"],
        "unit": config["unit"],
        "event_scope": event_scope,
        "reporting_sample": reporting_sample,
        "outcome_field": field,
        "observation_count": int(len(frame)),
        "utility_cluster_count": cluster_count,
        "reporting_method_counts": {
            str(key): int(value)
            for key, value in frame["reporting_standard"].value_counts().items()
        },
        "parameter_count": int(design.shape[1]),
        "design_rank": rank,
        "r_squared": float(1 - residual_sum_squares / total_sum_squares),
        "ownership_results": ownership_results,
    }


def build_results() -> dict[str, object]:
    audit = pd.read_csv(INPUT)
    if len(audit) != 360:
        raise ValueError(f"Expected 360 reviewed utility-years, found {len(audit)}")
    models = []
    for metric in METRICS:
        for event_scope in ("without_major_events", "with_major_events"):
            for reporting_sample in ("all_methods", "ieee_only"):
                models.append(
                    fit_model(audit, metric, event_scope, reporting_sample)
                )
    return {
        "title": "Ownership and utility-reported reliability",
        "purpose": "Secondary service-quality comparison; not a model of price causation",
        "source_data": str(INPUT.relative_to(PROJECT_ROOT)),
        "model": "Unweighted OLS with ownership, state, year, and reporting-method indicators",
        "primary_specification": {
            "event_scope": "without_major_events",
            "reporting_sample": "all_methods",
        },
        "reference_ownership": "DOM",
        "uncertainty": "95% CR1 confidence intervals clustered by utility, using a t critical value with clusters minus one degrees of freedom",
        "interpretation_limit": (
            "Associational, not causal; weather, geography, infrastructure, and "
            "reporting definitions remain possible explanations"
        ),
        "caidi_note": "CAIDI is derived from SAIDI divided by SAIFI and is not an independent reported outcome",
        "models": models,
    }


def write_results(results: dict[str, object]) -> None:
    payload = json.dumps(results, indent=2, allow_nan=False) + "\n"
    for output in (PROCESSED_OUTPUT, SITE_JSON_OUTPUT):
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload)
    SITE_JS_OUTPUT.write_text(
        "window.NE_NY_OWNERSHIP_RELIABILITY_MODEL_RESULTS = "
        + json.dumps(results, separators=(",", ":"), allow_nan=False)
        + ";\n"
    )


if __name__ == "__main__":
    write_results(build_results())
