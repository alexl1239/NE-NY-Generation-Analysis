"""Build Phase 6 ownership-event and potential-control research tables.

Phase 6 does not estimate an ownership effect or choose controls based on
prices. It gives every usable event-sector row a fixed pre/post window and
evaluates all 42 roster utilities against transparent, outcome-independent
control-pool rules.

Run: python3 scripts/build_research_design_inputs.py
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EVENT_WINDOWS_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "ownership_event_window_review_2001_2024.csv"
)
EVENTS_FILE = PROJECT_ROOT / "data" / "manual" / "ownership_events.csv"
OWNERSHIP_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "utility_ownership_history_2001_2024.csv"
)
PRICE_FILE = (
    PROJECT_ROOT / "data" / "processed" / "utility_price_history_2001_2024.csv"
)
EVENT_OUTPUT = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "ownership_research_design_events_2001_2024.csv"
)
CONTROL_OUTPUT = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "ownership_research_design_control_pool_2001_2024.csv"
)

YEAR_START = 2001
YEAR_END = 2024
PRIMARY_YEARS_EACH_SIDE = 4
CUSTOMER_BASE_FLOORS = {
    "residential": 100,
    "commercial": 100,
    "industrial": 5,
}
REVIEWED_DATE = "2026-11-16"
SECTORS = ("residential", "commercial", "industrial")

EVENT_FIELDS = [
    "event_id",
    "transaction_id",
    "treated_panel_id",
    "treated_utility_id_eia",
    "treated_utility",
    "treated_state",
    "treated_market",
    "customer_class",
    "closing_date",
    "year_end_treatment_year",
    "first_full_treatment_year",
    "old_ownership_class",
    "new_ownership_class",
    "phase5_readiness_status",
    "phase5_analysis_role",
    "phase6_window_role",
    "selected_years_each_side",
    "selected_pre_start_year",
    "selected_pre_end_year",
    "selected_post_start_year",
    "selected_post_end_year",
    "selected_pre_years",
    "selected_post_years",
    "selected_outcome_years",
    "required_treated_price_observations",
    "treated_customer_base_floor_customers",
    "treated_min_bundled_customers_selected_years",
    "treated_pre_mean_bundled_customers",
    "treated_customer_base_screen_status",
    "transaction_affected_panel_ids",
    "candidate_controls_evaluated",
    "eligible_control_count",
    "tier_1_same_state_count",
    "tier_2_same_market_count",
    "tier_3_cross_market_count",
    "eligible_control_panel_ids",
    "control_pool_rule",
    "customer_base_screen_rule",
    "review_status",
    "reviewed_date",
    "notes",
]

CONTROL_FIELDS = [
    "event_id",
    "transaction_id",
    "treated_panel_id",
    "treated_utility",
    "treated_state",
    "treated_market",
    "treated_old_ownership_class",
    "treated_new_ownership_class",
    "customer_class",
    "phase6_window_role",
    "closing_date",
    "year_end_treatment_year",
    "first_full_treatment_year",
    "selected_years_each_side",
    "selected_pre_years",
    "selected_post_years",
    "candidate_panel_id",
    "candidate_utility_id_eia",
    "candidate_utility",
    "candidate_state",
    "candidate_market",
    "same_state_as_treated",
    "same_market_as_treated",
    "affected_by_same_transaction",
    "candidate_baseline_ownership_class",
    "candidate_ownership_classes_in_span",
    "ownership_class_constant_through_span",
    "ownership_class_matches_treated_old_class",
    "candidate_parent_owners_in_span",
    "parent_owner_constant_through_span",
    "other_reviewed_event_in_span",
    "other_event_ids_in_span",
    "price_complete_for_selected_years",
    "missing_price_years",
    "candidate_identity_bases_in_span",
    "identity_basis_constant_through_span",
    "candidate_territory_statuses_in_span",
    "territory_basis_constant_through_span",
    "candidate_customer_base_floor_customers",
    "candidate_min_bundled_customers_selected_years",
    "candidate_pre_mean_bundled_customers",
    "treated_pre_mean_bundled_customers",
    "candidate_to_treated_pre_customer_ratio",
    "candidate_customer_base_screen_status",
    "control_pool_eligible",
    "control_pool_tier",
    "eligibility_reasons",
    "control_pool_rule",
    "customer_base_screen_rule",
    "review_status",
    "reviewed_date",
    "notes",
]

CONTROL_POOL_RULE = (
    "The candidate is not affected by the same transaction; remains in the "
    "treated utility's old ownership class; has no reviewed ownership, parent, "
    "identity, or territory event during the full span; has one stable parent, "
    "identity basis, and territory basis; and has a published price in every "
    "selected pre- and post-event year for the same customer class; and stays "
    "above the extreme-thinness customer floor."
)
CUSTOMER_BASE_RULE = (
    "Require more than 100 bundled customers in every selected residential or "
    "commercial year and more than 5 in every selected industrial year. This "
    "is an extreme-thinness screen, not a statistical-significance threshold."
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as source:
        return list(csv.DictReader(source))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {path}")


def bool_text(value: bool) -> str:
    return str(value).lower()


def pipe(values: list[object] | tuple[object, ...] | set[object]) -> str:
    return "|".join(str(value) for value in values)


def market_for_state(state: str) -> str:
    return "NYISO" if state == "NY" else "ISO-NE"


def numeric(value: str) -> float | None:
    return None if value == "" else float(value)


def rounded(value: float, digits: int = 3) -> float:
    return round(value, digits)


def selected_window(row: dict[str, str]) -> tuple[str, int]:
    status = row["readiness_status"]
    if status == "ready_4plus_each_side":
        return "primary_4_year_window", PRIMARY_YEARS_EACH_SIDE
    if status == "limited_2_to_3_one_side":
        years = int(row["max_balanced_window_years_each_side"])
        return f"sensitivity_{years}_year_window", years
    return "excluded_insufficient_price_window", 0


def prepare_inputs() -> tuple[
    list[dict[str, str]],
    list[dict[str, str]],
    dict[tuple[str, int], dict[str, str]],
    dict[tuple[str, int, str], dict[str, str]],
    list[str],
    dict[str, set[str]],
]:
    event_windows = read_csv(EVENT_WINDOWS_FILE)
    events = read_csv(EVENTS_FILE)
    ownership = read_csv(OWNERSHIP_FILE)
    prices = read_csv(PRICE_FILE)

    if len(event_windows) != 27:
        raise ValueError(f"Expected 27 Phase 5 event-sector rows; found {len(event_windows)}")
    if len(ownership) != 42 * 24:
        raise ValueError(f"Expected 1,008 ownership rows; found {len(ownership)}")
    if len(prices) != 42 * 24 * 3:
        raise ValueError(f"Expected 3,024 price rows; found {len(prices)}")

    ownership_lookup = {
        (row["panel_id"], int(row["year"])): row for row in ownership
    }
    price_lookup = {
        (row["panel_id"], int(row["year"]), row["customer_class"]): row
        for row in prices
    }
    if len(ownership_lookup) != len(ownership):
        raise ValueError("Duplicate annual ownership keys found")
    if len(price_lookup) != len(prices):
        raise ValueError("Duplicate annual price keys found")

    panels = sorted({row["panel_id"] for row in ownership})
    if len(panels) != 42:
        raise ValueError(f"Expected 42 panel utilities; found {len(panels)}")

    transaction_panels: dict[str, set[str]] = defaultdict(set)
    for event in events:
        transaction_panels[event["transaction_id"]].add(event["panel_id"])

    return (
        event_windows,
        events,
        ownership_lookup,
        price_lookup,
        panels,
        transaction_panels,
    )


def candidate_control_row(
    event: dict[str, str],
    window_role: str,
    selected_years: int,
    candidate_panel_id: str,
    transaction_panels: dict[str, set[str]],
    ownership_lookup: dict[tuple[str, int], dict[str, str]],
    price_lookup: dict[tuple[str, int, str], dict[str, str]],
    treated_pre_mean_customers: float,
) -> dict[str, object]:
    event_year = int(event["year_end_treatment_year"])
    first_full_year = int(event["first_full_treatment_year"])
    pre_years = list(range(event_year - selected_years, event_year))
    post_years = list(range(first_full_year, first_full_year + selected_years))
    outcome_years = pre_years + post_years
    span_years = list(range(pre_years[0], post_years[-1] + 1))

    ownership_rows = [
        ownership_lookup[(candidate_panel_id, year)] for year in span_years
    ]
    price_rows = [
        price_lookup[(candidate_panel_id, year, event["customer_class"])]
        for year in outcome_years
    ]
    pre_price_rows = [
        price_lookup[(candidate_panel_id, year, event["customer_class"])]
        for year in pre_years
    ]
    current = ownership_lookup[(candidate_panel_id, YEAR_END)]

    ownership_classes = sorted({row["ownership_class"] for row in ownership_rows})
    parent_owners = sorted(
        {row["ultimate_parent_or_owner"] for row in ownership_rows}
    )
    identity_bases = sorted(
        {row["identity_reporting_basis"] for row in ownership_rows}
    )
    territory_statuses = sorted(
        {row["territory_comparability_status"] for row in ownership_rows}
    )
    event_ids = sorted(
        {
            event_id
            for row in ownership_rows
            for event_id in row["event_ids"].split("|")
            if event_id
        }
    )
    missing_price_years = [
        year
        for year, row in zip(outcome_years, price_rows)
        if row["average_price_cents_kwh"] == ""
    ]

    ownership_constant = len(ownership_classes) == 1
    baseline_class = ownership_lookup[
        (candidate_panel_id, event_year - 1)
    ]["ownership_class"]
    class_matches = (
        ownership_constant and baseline_class == event["old_ownership_class"]
    )
    parent_constant = len(parent_owners) == 1
    identity_constant = len(identity_bases) == 1
    territory_constant = len(territory_statuses) == 1
    affected = candidate_panel_id in transaction_panels[event["transaction_id"]]
    price_complete = not missing_price_years

    reasons: list[str] = []
    if affected:
        reasons.append("affected_by_same_transaction")
    if not ownership_constant:
        reasons.append("ownership_class_changes_in_window")
    elif not class_matches:
        reasons.append("different_baseline_ownership_class")
    if event_ids:
        reasons.append("reviewed_event_in_window")
    if not parent_constant:
        reasons.append("parent_owner_changes_in_window")
    if not price_complete:
        reasons.append("price_gap_in_selected_years")
    if not identity_constant:
        reasons.append("identity_basis_changes_in_window")
    if not territory_constant:
        reasons.append("territory_basis_changes_in_window")

    customer_counts = [numeric(row["bundled_customers"]) for row in price_rows]
    complete_customer_counts = all(value is not None for value in customer_counts)
    min_customers = (
        min(value for value in customer_counts if value is not None)
        if complete_customer_counts
        else ""
    )
    pre_customer_counts = [
        numeric(row["bundled_customers"]) for row in pre_price_rows
    ]
    pre_mean_customers = (
        mean(value for value in pre_customer_counts if value is not None)
        if all(value is not None for value in pre_customer_counts)
        else None
    )
    customer_ratio = (
        pre_mean_customers / treated_pre_mean_customers
        if pre_mean_customers is not None and treated_pre_mean_customers > 0
        else None
    )
    customer_floor = CUSTOMER_BASE_FLOORS[event["customer_class"]]
    customer_base_passes = (
        min_customers != "" and float(min_customers) > customer_floor
    )
    if not complete_customer_counts:
        customer_base_status = "not_evaluable_price_gap"
    elif customer_base_passes:
        customer_base_status = "passes"
    else:
        customer_base_status = "fails_extremely_thin"
        reasons.append("extremely_thin_customer_base")

    eligible = not reasons
    candidate_market = market_for_state(current["state"])
    treated_market = market_for_state(event["state"])
    same_state = current["state"] == event["state"]
    same_market = candidate_market == treated_market
    if not eligible:
        tier = "not_eligible"
    elif same_state:
        tier = "tier_1_same_state"
    elif same_market:
        tier = "tier_2_same_market"
    else:
        tier = "tier_3_cross_market"

    return {
        "event_id": event["event_id"],
        "transaction_id": event["transaction_id"],
        "treated_panel_id": event["panel_id"],
        "treated_utility": event["display_name"],
        "treated_state": event["state"],
        "treated_market": treated_market,
        "treated_old_ownership_class": event["old_ownership_class"],
        "treated_new_ownership_class": event["new_ownership_class"],
        "customer_class": event["customer_class"],
        "phase6_window_role": window_role,
        "closing_date": event["closing_date"],
        "year_end_treatment_year": event_year,
        "first_full_treatment_year": first_full_year,
        "selected_years_each_side": selected_years,
        "selected_pre_years": pipe(pre_years),
        "selected_post_years": pipe(post_years),
        "candidate_panel_id": candidate_panel_id,
        "candidate_utility_id_eia": current["utility_id_eia"],
        "candidate_utility": current["display_name"],
        "candidate_state": current["state"],
        "candidate_market": candidate_market,
        "same_state_as_treated": bool_text(same_state),
        "same_market_as_treated": bool_text(same_market),
        "affected_by_same_transaction": bool_text(affected),
        "candidate_baseline_ownership_class": baseline_class,
        "candidate_ownership_classes_in_span": pipe(ownership_classes),
        "ownership_class_constant_through_span": bool_text(ownership_constant),
        "ownership_class_matches_treated_old_class": bool_text(class_matches),
        "candidate_parent_owners_in_span": pipe(parent_owners),
        "parent_owner_constant_through_span": bool_text(parent_constant),
        "other_reviewed_event_in_span": bool_text(bool(event_ids)),
        "other_event_ids_in_span": pipe(event_ids),
        "price_complete_for_selected_years": bool_text(price_complete),
        "missing_price_years": pipe(missing_price_years),
        "candidate_identity_bases_in_span": pipe(identity_bases),
        "identity_basis_constant_through_span": bool_text(identity_constant),
        "candidate_territory_statuses_in_span": pipe(territory_statuses),
        "territory_basis_constant_through_span": bool_text(territory_constant),
        "candidate_customer_base_floor_customers": customer_floor,
        "candidate_min_bundled_customers_selected_years": (
            rounded(float(min_customers)) if min_customers != "" else ""
        ),
        "candidate_pre_mean_bundled_customers": (
            rounded(pre_mean_customers) if pre_mean_customers is not None else ""
        ),
        "treated_pre_mean_bundled_customers": rounded(
            treated_pre_mean_customers
        ),
        "candidate_to_treated_pre_customer_ratio": (
            rounded(customer_ratio, 6) if customer_ratio is not None else ""
        ),
        "candidate_customer_base_screen_status": customer_base_status,
        "control_pool_eligible": bool_text(eligible),
        "control_pool_tier": tier,
        "eligibility_reasons": pipe(reasons),
        "control_pool_rule": CONTROL_POOL_RULE,
        "customer_base_screen_rule": CUSTOMER_BASE_RULE,
        "review_status": "reviewed_phase_6",
        "reviewed_date": REVIEWED_DATE,
        "notes": (
            "Controls are screened without using price levels or price changes. "
            "Tier is geographic and does not select a final control group."
        ),
    }


def build_rows() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    (
        event_windows,
        _events,
        ownership_lookup,
        price_lookup,
        panels,
        transaction_panels,
    ) = prepare_inputs()

    event_rows: list[dict[str, object]] = []
    control_rows: list[dict[str, object]] = []

    for event in event_windows:
        window_role, selected_years = selected_window(event)
        event_year = int(event["year_end_treatment_year"])
        first_full_year = int(event["first_full_treatment_year"])
        affected_panels = sorted(transaction_panels[event["transaction_id"]])

        if selected_years:
            pre_years = list(range(event_year - selected_years, event_year))
            post_years = list(
                range(first_full_year, first_full_year + selected_years)
            )
            outcome_years = pre_years + post_years
            treated_prices = [
                price_lookup[(event["panel_id"], year, event["customer_class"])]
                for year in outcome_years
            ]
            if any(row["average_price_cents_kwh"] == "" for row in treated_prices):
                raise ValueError(
                    f"Selected treated window contains a price gap: "
                    f"{event['event_id']} {event['customer_class']}"
                )
            treated_customer_counts = [
                float(row["bundled_customers"]) for row in treated_prices
            ]
            treated_pre_customers = [
                float(
                    price_lookup[
                        (event["panel_id"], year, event["customer_class"])
                    ]["bundled_customers"]
                )
                for year in pre_years
            ]
            treated_pre_mean_customers = mean(treated_pre_customers)
            treated_min_customers: float | str = min(treated_customer_counts)
            treated_customer_floor = CUSTOMER_BASE_FLOORS[event["customer_class"]]
            treated_customer_base_passes = (
                treated_min_customers > treated_customer_floor
            )
            if treated_customer_base_passes:
                treated_customer_base_status = "passes"
            else:
                treated_customer_base_status = "fails_extremely_thin"
                window_role = "excluded_extremely_thin_customer_base"

            event_controls = (
                [
                    candidate_control_row(
                        event,
                        window_role,
                        selected_years,
                        panel_id,
                        transaction_panels,
                        ownership_lookup,
                        price_lookup,
                        treated_pre_mean_customers,
                    )
                    for panel_id in panels
                ]
                if treated_customer_base_passes
                else []
            )
            control_rows.extend(event_controls)
            eligible_controls = [
                row
                for row in event_controls
                if row["control_pool_eligible"] == "true"
            ]
            tiers = Counter(row["control_pool_tier"] for row in eligible_controls)
        else:
            pre_years = []
            post_years = []
            outcome_years = []
            treated_min_customers = ""
            treated_pre_mean_customers = 0.0
            treated_customer_floor = CUSTOMER_BASE_FLOORS[event["customer_class"]]
            treated_customer_base_status = "not_evaluated_insufficient_window"
            event_controls = []
            eligible_controls = []
            tiers = Counter()

        event_rows.append(
            {
                "event_id": event["event_id"],
                "transaction_id": event["transaction_id"],
                "treated_panel_id": event["panel_id"],
                "treated_utility_id_eia": event["utility_id_eia"],
                "treated_utility": event["display_name"],
                "treated_state": event["state"],
                "treated_market": market_for_state(event["state"]),
                "customer_class": event["customer_class"],
                "closing_date": event["closing_date"],
                "year_end_treatment_year": event_year,
                "first_full_treatment_year": first_full_year,
                "old_ownership_class": event["old_ownership_class"],
                "new_ownership_class": event["new_ownership_class"],
                "phase5_readiness_status": event["readiness_status"],
                "phase5_analysis_role": event["later_analysis_role"],
                "phase6_window_role": window_role,
                "selected_years_each_side": selected_years,
                "selected_pre_start_year": pre_years[0] if pre_years else "",
                "selected_pre_end_year": pre_years[-1] if pre_years else "",
                "selected_post_start_year": post_years[0] if post_years else "",
                "selected_post_end_year": post_years[-1] if post_years else "",
                "selected_pre_years": pipe(pre_years),
                "selected_post_years": pipe(post_years),
                "selected_outcome_years": pipe(outcome_years),
                "required_treated_price_observations": len(outcome_years),
                "treated_customer_base_floor_customers": treated_customer_floor,
                "treated_min_bundled_customers_selected_years": (
                    rounded(float(treated_min_customers))
                    if treated_min_customers != ""
                    else ""
                ),
                "treated_pre_mean_bundled_customers": (
                    rounded(treated_pre_mean_customers)
                    if selected_years
                    else ""
                ),
                "treated_customer_base_screen_status": (
                    treated_customer_base_status
                ),
                "transaction_affected_panel_ids": pipe(affected_panels),
                "candidate_controls_evaluated": len(event_controls),
                "eligible_control_count": len(eligible_controls),
                "tier_1_same_state_count": tiers["tier_1_same_state"],
                "tier_2_same_market_count": tiers["tier_2_same_market"],
                "tier_3_cross_market_count": tiers["tier_3_cross_market"],
                "eligible_control_panel_ids": pipe(
                    sorted(
                        str(row["candidate_panel_id"])
                        for row in eligible_controls
                    )
                ),
                "control_pool_rule": CONTROL_POOL_RULE,
                "customer_base_screen_rule": CUSTOMER_BASE_RULE,
                "review_status": "reviewed_phase_6",
                "reviewed_date": REVIEWED_DATE,
                "notes": (
                    "Primary rows use four years on each side. Limited rows "
                    "retain their shorter balanced window for sensitivity or "
                    "description only. Rows with an insufficient window or an "
                    "extremely thin treated customer base receive no control pool."
                ),
            }
        )

    return validate_and_sort(event_rows, control_rows)


def validate_and_sort(
    event_rows: list[dict[str, object]],
    control_rows: list[dict[str, object]],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    if len(event_rows) != 27:
        raise ValueError(f"Expected 27 event-sector rows; created {len(event_rows)}")
    role_counts = Counter(str(row["phase6_window_role"]) for row in event_rows)
    if role_counts != {
        "primary_4_year_window": 15,
        "sensitivity_2_year_window": 3,
        "excluded_insufficient_price_window": 7,
        "excluded_extremely_thin_customer_base": 2,
    }:
        raise ValueError(f"Unexpected Phase 6 role counts: {role_counts}")

    expected_control_rows = (15 + 3) * 42
    if len(control_rows) != expected_control_rows:
        raise ValueError(
            f"Expected {expected_control_rows} control evaluations; "
            f"created {len(control_rows)}"
        )
    control_keys = {
        (
            row["event_id"],
            row["customer_class"],
            row["candidate_panel_id"],
        )
        for row in control_rows
    }
    if len(control_keys) != len(control_rows):
        raise ValueError("Duplicate event-sector-control rows found")

    for row in control_rows:
        if row["control_pool_eligible"] != "true":
            continue
        required_true = (
            "ownership_class_constant_through_span",
            "ownership_class_matches_treated_old_class",
            "parent_owner_constant_through_span",
            "price_complete_for_selected_years",
            "identity_basis_constant_through_span",
            "territory_basis_constant_through_span",
        )
        if any(row[field] != "true" for field in required_true):
            raise ValueError("An eligible control fails a required stability rule")
        if row["affected_by_same_transaction"] != "false":
            raise ValueError("A treated transaction utility entered its control pool")
        if row["other_reviewed_event_in_span"] != "false":
            raise ValueError("A utility with another reviewed event entered the pool")
        if row["candidate_customer_base_screen_status"] != "passes":
            raise ValueError("An eligible control fails the customer-base screen")
        if row["eligibility_reasons"] != "":
            raise ValueError("An eligible control has an exclusion reason")

    event_rows = sorted(
        event_rows,
        key=lambda row: (
            int(row["year_end_treatment_year"]),
            str(row["transaction_id"]),
            str(row["treated_panel_id"]),
            SECTORS.index(str(row["customer_class"])),
        ),
    )
    control_rows = sorted(
        control_rows,
        key=lambda row: (
            int(row["year_end_treatment_year"]),
            str(row["transaction_id"]),
            str(row["treated_panel_id"]),
            SECTORS.index(str(row["customer_class"])),
            str(row["candidate_panel_id"]),
        ),
    )
    return event_rows, control_rows


def main() -> None:
    event_rows, control_rows = build_rows()
    write_csv(EVENT_OUTPUT, EVENT_FIELDS, event_rows)
    write_csv(CONTROL_OUTPUT, CONTROL_FIELDS, control_rows)


if __name__ == "__main__":
    main()
